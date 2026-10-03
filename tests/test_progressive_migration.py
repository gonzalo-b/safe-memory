"""Schema5 to6 retains known facts and rolls back interrupted scans migration."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore,REPO
class ScanMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-scan-migration-');self.root=Path(self.tmp.name)/'store';self.root.mkdir()
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            db.executescript('\n'.join((REPO/f'schema/runtime-v{i}.sql').read_text() for i in range(1,6)))
            db.execute('PRAGMA user_version=5');db.execute("INSERT INTO metadata VALUES('fixture','true')");db.execute("INSERT INTO owners VALUES('owner','owner','Synthetic','unused',1,1)")
    def tearDown(self):self.tmp.cleanup()
    def test_v5_upgrade_is_backed_up_and_preserves_existing_owner(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],7)
            self.assertEqual(db.execute('SELECT id FROM owners').fetchone()[0],'owner')
            self.assertEqual(db.execute('SELECT count(*) FROM scan_runs').fetchone()[0],0)
            self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())
        manifests=list((self.root/'migration-backups').glob('*/manifest.json'));self.assertEqual(len(manifests),1);self.assertEqual(json.loads(manifests[0].read_text())['schema'],5)
    def test_failed_scan_migration_keeps_knowledge_schema_and_no_partial_scan_tables(self):
        read=Path.read_text
        def invalid(path,*a,**kw):return read(path,*a,**kw)+('\nINVALID SQL;' if path.name=='runtime-v6.sql' else '')
        with mock.patch.object(Path,'read_text',invalid):
            with self.assertRaises(sqlite3.Error):RuntimeStore(self.root,fixture=True)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],5)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='scan_runs'").fetchone())
            self.assertIsNotNone(db.execute("SELECT name FROM sqlite_master WHERE name='knowledge_facts'").fetchone())
    def test_incomplete_scan_schema_fails_closed(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:db.execute('ALTER TABLE scan_runs DROP COLUMN observed')
        with self.assertRaises(ValueError):RuntimeStore(self.root,fixture=True)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ScanMigrationTests))
    failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
