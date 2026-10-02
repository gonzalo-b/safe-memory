"""Run the native probe source boundary checks in the standard Python gate."""
import importlib.util
import sys
import unittest
from pathlib import Path
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('probe_source_guard', root / 'connectors/ios/tests/test_read_only.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
failed = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
passed = result.testsRun - failed - len(result.skipped) - len(result.expectedFailures)
print(f'\n{passed} passed, {failed} failed')
sys.exit(0 if result.wasSuccessful() and not result.skipped and not result.expectedFailures else 1)
