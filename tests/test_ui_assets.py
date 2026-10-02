"""Offline UI boundary checks; no browser or dependency installation required."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class AssetTests(unittest.TestCase):
    def test_css_references_only_local_assets(self):
        for path in (ROOT / 'ui').rglob('*.css'):
            text = path.read_text()
            for url in re.findall(r'url\(([^)]+)\)', text):
                value = url.strip(' \"\'')
                self.assertFalse(re.match(r'(?:[a-z]+:|//)', value), (path, value))
                self.assertTrue((path.parent / value).resolve().is_file(), (path, value))
            self.assertNotIn('@import', text)

    def test_product_css_variables_exist_in_design_system(self):
        design = (ROOT / 'ui/memory-ds/memory.css').read_text()
        declared = set(re.findall(r'(--m-[\w-]+)\s*:', design))
        used = set(re.findall(r'var\((--m-[\w-]+)', (ROOT / 'ui/shell.css').read_text()))
        self.assertEqual(used - declared, set())

    def test_local_font_is_valid_nonempty_woff2(self):
        font = (ROOT / 'ui/fonts/Inter-variable.woff2').read_bytes()
        self.assertEqual(font[:4], b'wOF2')
        self.assertEqual(int.from_bytes(font[8:12], 'big'), len(font))
        self.assertGreater(len(font), 1000)

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AssetTests))
    failed = len(result.failures) + len(result.errors)
    print(f'{result.testsRun - failed} passed, {failed} failed')
    raise SystemExit(bool(failed))
