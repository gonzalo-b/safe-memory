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
    r"URLSession|WKWebView|URLRequest)\b|value\s*\(\s*forKey|setValue\s*\(",
)


def reject_unsafe_source(source):
    return bool(FORBIDDEN.search(source))


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
                self.assertFalse(reject_unsafe_source(path.read_text()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
