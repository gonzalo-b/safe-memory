"""Conservative source guard; device non-mutation proof remains separate."""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "SafeMemoryProbe"
FORBIDDEN = re.compile(
    r"\b(?:performChanges|performChangesAndWait|PHAssetChangeRequest|"
    r"PHAssetCreationRequest|PHAssetCollectionChangeRequest|PHCollectionListChangeRequest|"
    r"PHAssetResourceUploadJobChangeRequest|NSSelectorFromString|NSClassFromString|"
    r"class_getMethodImplementation|method_exchangeImplementations|dlsym|"
    r"WKWebView)\b|value\s*\(\s*forKey|setValue\s*\(",
)
NETWORK = re.compile(r"\b(?:URLSession|URLRequest)\b")
PAIRING_NETWORK = {
    "PairingRequests.swift": {"URLRequest"},
    "PairingTransport.swift": {"URLRequest", "URLSession"},
    "NativeRequests.swift": {"URLRequest"},
}


def reject_unsafe_source(source, allowed_network=()):
    return bool(FORBIDDEN.search(source) or any(token not in allowed_network for token in NETWORK.findall(source)))


class ReadOnlyGuard(unittest.TestCase):
    def test_rejects_every_source_mutation_entrypoint(self):
        for token in ("performChanges", "performChangesAndWait", "PHAssetChangeRequest",
                      "PHAssetCreationRequest", "PHAssetCollectionChangeRequest",
                      "PHCollectionListChangeRequest", "PHAssetResourceUploadJobChangeRequest"):
            with self.subTest(token=token):
                self.assertTrue(reject_unsafe_source(token + "()"))

    def test_rejects_private_lookup_and_network_surface(self):
        for token in ("value(forKey: key)", "NSSelectorFromString", "dlsym", "URLSession", "URLRequest"):
            with self.subTest(token=token):
                self.assertTrue(reject_unsafe_source(token))

    def test_all_probe_sources_are_read_only(self):
        files = sorted(SOURCE.glob("*.swift"))
        self.assertGreaterEqual(len(files), 3)
        for path in files:
            with self.subTest(path=path.name):
                self.assertFalse(reject_unsafe_source(path.read_text(), PAIRING_NETWORK.get(path.name, ())))

    def test_pairing_network_scope_never_admits_photos_or_source_mutations(self):
        for name, allowed in PAIRING_NETWORK.items():
            self.assertTrue(reject_unsafe_source("PHAssetChangeRequest()", allowed))
            self.assertTrue(reject_unsafe_source("value(forKey: key)", allowed))
            self.assertNotRegex((SOURCE / name).read_text(), r"\b(?:PHAsset|PhotosReader|ProbeManifest|ExportComponent)\b|import Photos")


if __name__ == "__main__":
    unittest.main(verbosity=2)
