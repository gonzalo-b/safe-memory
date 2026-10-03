#!/usr/bin/env python3
"""Mirror a verified, already merged source main; never merge a PR or force push.

Run from a clean checkout of the merged commit:
    python3 scripts/mirror_main.py --expected-main <full merged SHA> [--dry-run]

The active agent must complete exact-SHA checks and merge the source PR first.
This operator helper is not a watcher or a substitute for those checks.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

SOURCE_URL = "https://github.com/gonzalo-b/safe-memory.git"
SOURCE_URLS = {SOURCE_URL, SOURCE_URL.removesuffix(".git"), "git@github.com:gonzalo-b/safe-memory.git", "ssh://git@github.com/gonzalo-b/safe-memory.git"}
TARGET_REPO = "lazyagent/memory"
TARGET_URL = f"https://github.com/{TARGET_REPO}.git"
MAIN = "refs/heads/main"


class DeliveryError(RuntimeError):
    """Delivery was refused or could not be verified."""


def run_command(argv, *, cwd, env):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode:
        # Do not echo credential-helper or remote diagnostics into receipts.
        raise DeliveryError(f"{argv[0]} command failed (exit {result.returncode}); delivery is not verified")
    return result.stdout.strip()


def mirror_main(repo, expected_main, *, dry_run=False, run=run_command):
    """Return the verified source SHA, or refuse without rewriting either history."""
    if not re.fullmatch(r"[0-9a-f]{40}", expected_main):
        raise DeliveryError("--expected-main must be a full lowercase commit SHA")
    repo = Path(repo).resolve()
    source_env = dict(os.environ)
    target_env = {key: value for key, value in source_env.items() if key not in {"GH_TOKEN", "GITHUB_TOKEN"}}

    def git(*args, target=False):
        config = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"] if target else []
        return run(["git", *config, *args], cwd=repo, env=target_env if target else source_env)

    def tip(remote, *, target=False):
        output = git("ls-remote", "--heads", remote, MAIN, target=target)
        if not output:
            return None
        fields = output.split()
        if len(fields) != 2 or fields[1] != MAIN or not re.fullmatch(r"[0-9a-f]{40}", fields[0]):
            raise DeliveryError("Unexpected remote main response")
        return fields[0]

    if git("remote", "get-url", "--all", "origin") not in SOURCE_URLS:
        raise DeliveryError("origin must identify gonzalo-b/safe-memory with exactly one URL")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise DeliveryError("Tracked checkout changes must be committed before delivery")
    if git("rev-parse", "HEAD") != expected_main:
        raise DeliveryError("Checkout HEAD must equal the expected merged main")
    if tip("origin") != expected_main:
        raise DeliveryError("Source main changed or does not match the expected merged SHA")
    try:
        target_info = json.loads(run(["gh", "repo", "view", f"github.com/{TARGET_REPO}", "--json", "nameWithOwner,isPrivate"], cwd=repo, env=target_env))
    except (ValueError, TypeError) as error:
        raise DeliveryError("Cannot verify target repository identity and visibility") from error
    if not isinstance(target_info, dict) or target_info.get("nameWithOwner") != TARGET_REPO or target_info.get("isPrivate") is not True:
        raise DeliveryError("Target must be the private lazyagent/memory repository")
    previous = tip(TARGET_URL, target=True)
    if previous and previous != expected_main:
        git("fetch", "--no-tags", "--no-write-fetch-head", TARGET_URL, previous, target=True)
        try:
            git("merge-base", "--is-ancestor", previous, expected_main)
        except DeliveryError as error:
            raise DeliveryError("Target main is not an ancestor of source main; refusing to rewrite history") from error
    if tip("origin") != expected_main or tip(TARGET_URL, target=True) != previous:
        raise DeliveryError("Remote main changed during validation; rerun checks")
    if dry_run:
        return expected_main
    if previous != expected_main:
        # Ordinary push still rejects a competing divergent update after validation.
        git("push", TARGET_URL, f"{expected_main}:{MAIN}", target=True)
    if tip(TARGET_URL, target=True) != expected_main or tip("origin") != expected_main:
        raise DeliveryError("Remote main changed during delivery; delivery is not verified")
    return expected_main


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-main", required=True)
    parser.add_argument("--dry-run", action="store_true", help="validate without pushing (may fetch target commit objects)")
    args = parser.parse_args()
    try:
        sha = mirror_main(Path.cwd(), args.expected_main, dry_run=args.dry_run)
    except (DeliveryError, OSError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    print(f"{'Validated plan' if args.dry_run else 'Verified mirrored main'}: {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
