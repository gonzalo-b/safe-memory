"""Delivery safety tested against disposable local Git repositories, offline."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("mirror_main", Path(__file__).resolve().parents[1] / "scripts/mirror_main.py")
mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mirror)


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / "work"
        self.source = self.root / "source.git"
        self.target = self.root / "target.git"
        self.work.mkdir()
        for bare in (self.source, self.target):
            self.git("init", "--bare", str(bare))
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("remote", "add", "origin", mirror.SOURCE_URL)
        (self.work / "tracked").write_text("fixture\n")
        self.git("add", "tracked")
        self.git("commit", "-m", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.git("commit", "--allow-empty", "-m", "merged change")
        self.tip = self.git("rev-parse", "HEAD")
        self.git("push", str(self.source), "HEAD:refs/heads/main")
        self.calls = []
        self.target_reads = 0
        self.private = True
        self.race = False
        self.push_race = False

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.work, check=True, capture_output=True, text=True).stdout.strip()

    def runner(self, argv, *, cwd, env):
        self.calls.append((argv[:], env.copy()))
        if argv[0] == "gh":
            return json.dumps({"nameWithOwner": mirror.TARGET_REPO, "isPrivate": self.private})
        mapped = [str(self.source) if arg == "origin" and "ls-remote" in argv else str(self.target) if arg == mirror.TARGET_URL else arg for arg in argv]
        if "ls-remote" in argv and mirror.TARGET_URL in argv:
            self.target_reads += 1
            if self.race and self.target_reads == 2:
                self.git("push", str(self.target), f"{self.base}:refs/heads/main")
        if "push" in argv and self.push_race:
            self.git("checkout", "--detach", self.base)
            self.git("commit", "--allow-empty", "-m", "competing target update")
            self.competing_tip = self.git("rev-parse", "HEAD")
            self.git("push", str(self.target), "HEAD:refs/heads/main")
            self.git("checkout", "main")
        result = subprocess.run(mapped, cwd=cwd, env=env, capture_output=True, text=True)
        if result.returncode:
            raise mirror.DeliveryError("Git command refused")
        return result.stdout.strip()

    def deliver(self, **kwargs):
        return mirror.mirror_main(self.work, self.tip, run=self.runner, **kwargs)

    def target_tip(self):
        result = self.git("ls-remote", str(self.target), "refs/heads/main")
        return result.split()[0] if result else None

    def test_empty_target_receives_exact_merged_main_and_rerun_is_noop(self):
        self.assertEqual(self.deliver(), self.tip)
        self.assertEqual(self.target_tip(), self.tip)
        self.calls.clear()
        self.assertEqual(self.deliver(), self.tip)
        self.assertFalse(any("push" in argv for argv, _ in self.calls))

    def test_ancestor_target_fast_forwards_without_force(self):
        self.git("push", str(self.target), f"{self.base}:refs/heads/main")
        self.deliver()
        self.assertEqual(self.target_tip(), self.tip)
        pushes = [argv for argv, _ in self.calls if "push" in argv]
        self.assertEqual(len(pushes), 1)
        self.assertFalse(any("force" in arg or arg.startswith("+") for arg in pushes[0]))

    def test_divergent_target_is_preserved(self):
        self.git("checkout", "--detach", self.base)
        self.git("commit", "--allow-empty", "-m", "unrelated target change")
        divergent = self.git("rev-parse", "HEAD")
        self.git("push", str(self.target), "HEAD:refs/heads/main")
        self.git("checkout", "main")
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertEqual(self.target_tip(), divergent)

    def test_stale_expected_main_is_refused(self):
        self.git("commit", "--allow-empty", "-m", "new source change")
        self.git("push", str(self.source), "HEAD:refs/heads/main")
        self.git("checkout", "--detach", self.tip)
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertIsNone(self.target_tip())

    def test_dirty_tracked_checkout_is_refused(self):
        (self.work / "tracked").write_text("dirty\n")
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertIsNone(self.target_tip())

    def test_wrong_origin_is_refused(self):
        self.git("remote", "set-url", "origin", "https://github.com/other/memory.git")
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertIsNone(self.target_tip())

    def test_public_target_is_refused(self):
        self.private = False
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertIsNone(self.target_tip())

    def test_target_change_during_validation_is_refused(self):
        self.race = True
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertEqual(self.target_tip(), self.base)

    def test_target_only_removes_token_environment_and_uses_keyring(self):
        old = dict(os.environ)
        self.addCleanup(lambda: (os.environ.clear(), os.environ.update(old)))
        os.environ.update(GITHUB_TOKEN="fixture-source-token", GH_TOKEN="fixture-source-token")
        self.deliver()
        for argv, env in self.calls:
            if mirror.TARGET_URL in argv or argv[0] == "gh":
                self.assertNotIn("GH_TOKEN", env)
                self.assertNotIn("GITHUB_TOKEN", env)
                if argv[0] == "git":
                    self.assertIn("credential.helper=!gh auth git-credential", argv)
            else:
                self.assertEqual(env.get("GH_TOKEN"), "fixture-source-token")
        self.assertEqual(os.environ["GH_TOKEN"], "fixture-source-token")

    def test_competing_divergent_push_is_rejected_by_git(self):
        self.push_race = True
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertEqual(self.target_tip(), self.competing_tip)

    def test_unmerged_checkout_is_refused(self):
        self.git("commit", "--allow-empty", "-m", "local only")
        with self.assertRaises(mirror.DeliveryError):
            self.deliver()
        self.assertIsNone(self.target_tip())

    def test_dry_run_does_not_push(self):
        self.deliver(dry_run=True)
        self.assertIsNone(self.target_tip())
        self.assertFalse(any("push" in argv for argv, _ in self.calls))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MirrorTests))
    failures = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failures} passed, {failures} failed")
    sys.exit(not result.wasSuccessful())
