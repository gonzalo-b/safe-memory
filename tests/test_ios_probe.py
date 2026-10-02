"""Native probe policy checks use synthetic Foundation values, never Photos."""
from __future__ import annotations

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
IOS = ROOT / "connectors/ios"
SOURCE = IOS / "SafeMemoryProbe"
spec = importlib.util.spec_from_file_location("ios_read_only_guard", IOS / "tests/test_read_only.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
ReadOnlyGuard = guard.ReadOnlyGuard


class IOSContracts(unittest.TestCase):
    def swift(self, files, harness, expected):
        if "PairingTransport.swift" in files and "NativeRequests.swift" not in files:
            files = files + ["NativeRequests.swift"]
        self.assertIsNotNone(shutil.which("xcrun"), "These native contract checks require installed Xcode Swift tools")
        with tempfile.TemporaryDirectory(prefix="memory-synthetic-swift-") as directory:
            target = pathlib.Path(directory) / "contract"
            compile_result = subprocess.run([
                "xcrun", "swiftc", "-swift-version", "6", "-warnings-as-errors",
                "-module-cache-path", str(pathlib.Path(directory) / "modules"),
                *[str(SOURCE / name) for name in files], str(IOS / "tests" / harness),
                "-o", str(target),
            ], capture_output=True, text=True, timeout=90)
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout + compile_result.stderr)
            result = subprocess.run([str(target)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(sum(line.startswith("PASS") for line in result.stdout.splitlines()), expected)

    def test_manifest_serialization_and_unknown_offset(self):
        self.swift(["ProbeManifest.swift"], "ManifestTests.swift", 4)

    def test_export_scope_consent_roles_and_budget(self):
        self.swift(["ExportPolicy.swift"], "ExportPolicyTests.swift", 6)

    def test_callback_cancellation_races(self):
        self.swift(["ExportPolicy.swift", "ExportRequestBridge.swift"], "ExportBridgeTests.swift", 4)

    def test_pairing_request_contract(self):
        self.swift(["PairingRequests.swift"], "PairingTests.swift", 3)

    def test_pairing_bounded_transport_with_protocol_fixtures(self):
        self.swift(["ExportPolicy.swift", "ExportRequestBridge.swift", "PairingRequests.swift", "PairingTransport.swift"], "PairingTransportTests.swift", 7)

    def test_pairing_persistent_identity_and_confirmation_lifecycle(self):
        self.swift(["ExportPolicy.swift", "ExportRequestBridge.swift", "PairingRequests.swift", "PairingTransport.swift", "PairingIdentity.swift"], "PairingLifecycleTests.swift", 4)

    def test_import_revision_and_explicit_scope(self):
        self.swift(["ExportPolicy.swift", "ExportRequestBridge.swift", "PairingRequests.swift", "PairingTransport.swift", "PairingIdentity.swift", "ProbeManifest.swift", "ImportModels.swift"], "ImportModelTests.swift", 3)

    def test_import_replay_and_permission_invalidation(self):
        self.swift(["ExportPolicy.swift", "ExportRequestBridge.swift", "PairingRequests.swift", "PairingTransport.swift", "PairingIdentity.swift", "ProbeManifest.swift", "ImportModels.swift", "ImportCoordinator.swift", "ImportTransport.swift"], "ImportWorkflowTests.swift", 5)

    def test_private_import_checkpoint_restart_and_integrity(self):
        self.swift(["ExportPolicy.swift", "ExportRequestBridge.swift", "PairingRequests.swift", "PairingTransport.swift", "PairingIdentity.swift", "ProbeManifest.swift", "ImportModels.swift", "ImportCheckpointFiles.swift"], "ImportFilesTests.swift", 3)

    def test_exporter_cannot_enumerate_or_request_broader_permission(self):
        source = (SOURCE / "OptimizedMediaExporter.swift").read_text()
        self.assertNotIn("requestAuthorization", source)
        self.assertNotRegex(source, r"fetchAssets\s*\((?!withLocalIdentifiers:)")
        self.assertNotIn("fetchAssetCollections", source)

    def test_import_reader_uses_only_selected_ids_without_media_download(self):
        source = (SOURCE / "PhotosReader.swift").read_text().split("static func selected(", 1)[1].split("private static func describe", 1)[0]
        self.assertIn("fetchAssets(withLocalIdentifiers: ids", source)
        self.assertNotRegex(source, r"fetchAssets\s*\((?!withLocalIdentifiers:)")
        self.assertNotIn("requestAuthorization", source)
        view = (SOURCE / "ImportView.swift").read_text()
        self.assertNotIn("loadTransferable", view)
        self.assertNotIn("PhotosReader.snapshot", view)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed} passed, {failed} failed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
