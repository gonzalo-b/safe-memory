"""Schema6→7 preserves previous rows and fails closed on interrupted migration."""
import json
from pathlib import Path
import sqlite3,sys,tempfile,unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore,REPO
class ArtifactMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-artifact-migration-');self.root=Path(self.tmp.name)/'store';self.root.mkdir()
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            db.executescript('\n'.join((REPO/f'schema/runtime-v{i}.sql').read_text() for i in range(1,7)))
            db.execute('PRAGMA user_version=6');db.execute("INSERT INTO metadata VALUES('fixture','true')");db.execute("INSERT INTO owners VALUES('owner','owner','Synthetic','unused',1,1)")
    def tearDown(self):self.tmp.cleanup()
    def test_v6_upgrade_preserves_owner_and_verified_prechange_backup(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],8);self.assertEqual(db.execute('SELECT id FROM owners').fetchone()[0],'owner')
            self.assertEqual(db.execute('SELECT count(*) FROM artifacts').fetchone()[0],0);self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())
        manifests=list((self.root/'migration-backups').glob('*/manifest.json'));self.assertEqual(len(manifests),1);self.assertEqual(json.loads(manifests[0].read_text())['schema'],6)
    def test_failed_artifact_migration_rolls_back_and_retains_progressive_tables(self):
        read=Path.read_text
        def fail(path,*a,**kw):return read(path,*a,**kw)+('\nINVALID SQL;' if path.name=='runtime-v7.sql' else '')
        with mock.patch.object(Path,'read_text',fail):
            with self.assertRaises(sqlite3.Error):RuntimeStore(self.root,fixture=True)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],6);self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='artifacts'").fetchone())
            self.assertIsNotNone(db.execute("SELECT name FROM sqlite_master WHERE name='scan_runs'").fetchone())
    def test_incomplete_artifact_schema_refuses_startup(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:db.execute('ALTER TABLE artifact_members DROP COLUMN origin');db.execute('ALTER TABLE artifact_members DROP COLUMN position')
        with self.assertRaises(ValueError):RuntimeStore(self.root,fixture=True)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactMigrationTests));failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
