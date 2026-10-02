"""Standalone schema5 migration; does not depend on unfinished knowledge service."""
from pathlib import Path
import json, sqlite3, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore, RuntimeErrorResult, REPO
class KnowledgeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-knowledge-migration-');self.root=Path(self.tmp.name)/'store';self.root.mkdir()
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            db.executescript('\n'.join((REPO/f'schema/runtime-v{i}.sql').read_text() for i in range(1,5)))
            db.execute('PRAGMA user_version=4');db.execute("INSERT INTO metadata VALUES('fixture','true')");db.execute("INSERT INTO owners VALUES('owner','owner','Synthetic','unused',1,1)")
    def tearDown(self):self.tmp.cleanup()
    def test_v4_upgrade_retains_rows_and_audited_prechange_backup(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],5)
            self.assertEqual(db.execute('SELECT id FROM owners').fetchone()[0],'owner');self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_facts').fetchone()[0],0)
        backups=list((self.root/'migration-backups').glob('*/manifest.json'));self.assertEqual(len(backups),1);self.assertEqual(json.loads(backups[0].read_text())['schema'],4)
        with sqlite3.connect(backups[0].parent/'memory.sqlite3') as db:self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action='backup'").fetchone()[0],1)
    def test_v5_migration_failure_keeps_v4_usable(self):
        original=Path.read_text
        def fail(path,*args,**kwargs):
            value=original(path,*args,**kwargs);return value+'\nINVALID SQL;' if path.name=='runtime-v5.sql' else value
        with mock.patch.object(Path,'read_text',fail):
            with self.assertRaises(sqlite3.Error):RuntimeStore(self.root,fixture=True)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],4);self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='knowledge_facts'").fetchone())
        RuntimeStore(self.root,fixture=True)
    def test_v5_migration_audit_failure_rolls_back_all_new_tables(self):
        with sqlite3.connect(self.root/'memory.sqlite3') as db:db.execute("CREATE TRIGGER deny_migration BEFORE INSERT ON audit WHEN NEW.action='migration' BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(RuntimeErrorResult):RuntimeStore(self.root,fixture=True)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],4);self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='knowledge_facts'").fetchone())
    def test_incomplete_fact_signature_schema_fails_closed(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:db.execute('ALTER TABLE knowledge_facts DROP COLUMN signature')
        with self.assertRaises(ValueError):RuntimeStore(self.root,fixture=True)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(KnowledgeMigrationTests));print(f'{result.testsRun-len(result.failures)-len(result.errors)} passed, {len(result.failures)+len(result.errors)} failed');sys.exit(not result.wasSuccessful())
