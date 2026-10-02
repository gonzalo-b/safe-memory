"""Behavioral runtime foundation checks; private temporary roots only."""
import json
import ast
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore, RuntimeErrorResult

PASSWORD = 'synthetic correct horse battery'

def check_domain_imports(root):
    banned={'socket','urllib','http','requests','httpx','subprocess','uvicorn'}
    approved={'blocks.capabilities','blocks.trips'}
    pending=list((root/'runtime').glob('*.py'));seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                assert node.level==0, (path,'relative import outside explicit allowlist')
                names=[node.module] if node.module else []
            else:names=[alias.name for alias in node.names] if isinstance(node,ast.Import) else []
            for name in names:
                package=name.split('.')[0]
                assert package not in banned, (path,package)
                if name in approved:
                    pending.append(root.joinpath(*name.split('.')).with_suffix('.py'))
                else:assert package in sys.stdlib_module_names or package=='runtime', (path,package)

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='memory-runtime-')
        self.root = Path(self.tmp.name) / 'store'
        self.now = 1800000000
        self.store = RuntimeStore(self.root, fixture=True, clock=lambda: self.now)
        self.owner = self.store.create_owner('alice', PASSWORD, 'Synthetic Alice')

    def tearDown(self):
        self.tmp.cleanup()

    def login(self):
        return self.store.login('alice', PASSWORD, 'loopback')

    def test_login_persists_only_verifier_and_hashed_session(self):
        auth = self.login()
        self.assertEqual(self.store.session(auth['token'])['owner']['id'], self.owner)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            rows = str(db.execute('SELECT * FROM owners').fetchall()) + str(db.execute('SELECT * FROM sessions').fetchall())
        self.assertNotIn(PASSWORD, rows)
        self.assertNotIn(auth['token'], rows)
        self.assertNotIn(auth['csrf_token'], rows)

    def test_session_survives_restart_and_expires(self):
        auth = self.login()
        second = RuntimeStore(self.root, fixture=True, clock=lambda: self.now)
        self.assertEqual(second.session(auth['token'])['owner']['id'], self.owner)
        self.now += 86401
        with self.assertRaises(RuntimeErrorResult) as result: second.session(auth['token'])
        self.assertEqual(result.exception.status, 401)

    def test_logout_revokes_and_token_spoof_denied(self):
        auth = self.login()
        self.store.logout(auth['token'], auth['csrf_token'])
        for token in (auth['token'], self.owner, 'bogus'):
            with self.assertRaises(RuntimeErrorResult) as result: self.store.session(token)
            self.assertEqual(result.exception.status, 401)

    def test_csrf_failure_keeps_session_and_denies_mutation(self):
        auth = self.login()
        with self.assertRaises(RuntimeErrorResult) as result: self.store.logout(auth['token'], 'wrong')
        self.assertEqual(result.exception.status, 403)
        self.assertEqual(self.store.session(auth['token'])['owner']['id'], self.owner)

    def test_login_throttle_survives_restart_and_errors_are_generic(self):
        errors=[]
        for username in ('alice','missing'):
            for _ in range(5):
                with self.assertRaises(RuntimeErrorResult) as result:self.store.login(username,'bad','remote')
                errors.append((result.exception.status,result.exception.code))
            second=RuntimeStore(self.root,fixture=True,clock=lambda:self.now)
            with self.assertRaises(RuntimeErrorResult) as result:second.login(username,PASSWORD,'remote')
            self.assertEqual(result.exception.status,429)
        self.assertEqual(set(errors),{(401,'invalid_credentials')})

    def test_successful_sign_in_does_not_exhaust_failed_login_limit(self):
        for _ in range(6):
            auth=self.login()
            self.assertEqual(self.store.session(auth['token'])['owner']['id'],self.owner)

    def test_vault_and_source_replay_are_unique_and_owner_scoped(self):
        other=self.store.create_owner('bob',PASSWORD,'Synthetic Bob')
        first=self.store.connect_source(self.owner,'library-a','iPhone')
        replay=self.store.connect_source(self.owner,'library-a','iPhone again')
        second=self.store.connect_source(other,'library-a','iPhone')
        self.assertEqual(first['id'],replay['id'])
        self.assertNotEqual(first['vault_id'],second['vault_id'])
        self.assertNotEqual(first['id'],second['id'])
        auth=self.login()
        overview=self.store.overview(auth['token'])
        self.assertEqual([s['id'] for s in overview['sources']],[first['id']])
        self.assertEqual(overview['counts'],{'assets':0,'media_ready':0,'artifacts':0,'trips':0})

    def test_fixture_mode_is_persisted_and_cannot_be_silently_changed(self):
        with self.assertRaises(ValueError):RuntimeStore(self.root,fixture=False)
        self.assertTrue(self.store.overview(self.login()['token'])['fixture'])

    def test_audit_is_append_only_and_content_free(self):
        auth=self.login();self.store.overview(auth['token']);self.store.debug(auth['token'])
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            rows=str(db.execute('SELECT * FROM audit').fetchall())
            for sql in ('DELETE FROM audit','UPDATE audit SET outcome="allowed"'):
                with self.assertRaises(sqlite3.IntegrityError):db.execute(sql)
        for secret in (PASSWORD,auth['token'],auth['csrf_token'],'Synthetic Alice','alice'):
            self.assertNotIn(secret,rows)

    def test_audit_failure_refuses_read(self):
        auth=self.login()
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(RuntimeErrorResult) as result:self.store.overview(auth['token'])
        self.assertEqual(result.exception.status,503)
        self.assertEqual(result.exception.code,'audit_unavailable')

    def test_backup_restore_preserves_facts_but_revokes_old_access(self):
        auth=self.login();source=self.store.connect_source(self.owner,'library-a','iPhone')
        backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored')
        with self.assertRaises(RuntimeErrorResult):restored.session(auth['token'])
        fresh=restored.login('alice',PASSWORD,'local')
        view=restored.overview(fresh['token'])
        self.assertEqual(view['sources'][0]['id'],source['id'])
        self.assertEqual(view['sources'][0]['permission'],'restricted')
        self.assertEqual(self.store.session(auth['token'])['owner']['id'],self.owner)
        with self.assertRaises(ValueError):RuntimeStore.restore(backup,self.root)

    def test_corrupt_backup_refused_without_touching_live_store(self):
        backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        with (backup/'memory.sqlite3').open('ab') as stream:stream.write(b'corrupt')
        with self.assertRaises(ValueError):RuntimeStore.restore(backup,Path(self.tmp.name)/'bad')
        self.assertEqual(self.store.session(self.login()['token'])['owner']['id'],self.owner)

    def test_backup_and_restore_reject_repo_and_symlink_destinations_before_writing(self):
        backup=Path(self.tmp.name)/'good-backup';self.store.backup(backup)
        fake_repo=Path(self.tmp.name)/'repo';fake_repo.mkdir()
        with mock.patch('runtime.store.REPO',fake_repo):
            for operation,target in [(lambda p:self.store.backup(p),fake_repo/'backup'),(lambda p:RuntimeStore.restore(backup,p),fake_repo/'restored')]:
                with self.assertRaises(ValueError):operation(target)
                self.assertFalse(target.exists())
        real=Path(self.tmp.name)/'real';real.mkdir()
        link=Path(self.tmp.name)/'link';link.symlink_to(real,target_is_directory=True)
        for operation,name in [(lambda p:self.store.backup(p),'backup'),(lambda p:RuntimeStore.restore(backup,p),'restored')]:
            with self.assertRaises(ValueError):operation(link/name)
            self.assertFalse((real/name).exists())

    def test_failed_restore_is_quarantined_before_old_sessions_can_be_used(self):
        auth=self.login()
        with sqlite3.connect(self.store.path) as db:
            db.execute("CREATE TRIGGER fail_restore BEFORE INSERT ON audit WHEN NEW.action='restore' BEGIN SELECT RAISE(ABORT,'disk full'); END")
        backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        destination=Path(self.tmp.name)/'restored'
        with self.assertRaises(RuntimeErrorResult):RuntimeStore.restore(backup,destination)
        with self.assertRaises(ValueError):RuntimeStore(destination,fixture=True)
        self.assertEqual(self.store.session(auth['token'])['owner']['id'],self.owner)

    def test_backup_requires_audit_before_any_copy(self):
        with sqlite3.connect(self.store.path) as db:
            db.execute("CREATE TRIGGER fail_backup BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        destination=Path(self.tmp.name)/'backup'
        with self.assertRaises(RuntimeErrorResult) as result:self.store.backup(destination)
        self.assertEqual(result.exception.code,'audit_unavailable')
        self.assertFalse(destination.exists())

    def test_files_private_and_symlink_database_refused(self):
        self.assertEqual(self.root.stat().st_mode & 0o777,0o700)
        self.assertEqual((self.root/'memory.sqlite3').stat().st_mode & 0o777,0o600)
        root=Path(self.tmp.name)/'linked';root.mkdir()
        (root/'memory.sqlite3').symlink_to(self.root/'memory.sqlite3')
        with self.assertRaises(ValueError):RuntimeStore(root,fixture=True)

    def test_domain_runtime_remains_stdlib_without_network_or_shell(self):
        check_domain_imports(Path(__file__).resolve().parents[1])

    def test_domain_guard_checks_only_approved_helpers_transitively(self):
        root=Path(self.tmp.name)/'guard';(root/'runtime').mkdir(parents=True);(root/'blocks').mkdir()
        (root/'runtime'/'safe.py').write_text('from blocks.trips import detect_trips\n')
        (root/'blocks'/'trips.py').write_text('from blocks.capabilities import parser\n')
        helper=root/'blocks'/'capabilities.py';helper.write_text('import datetime\n')
        check_domain_imports(root)
        helper.write_text('import socket\n')
        with self.assertRaises(AssertionError):check_domain_imports(root)
        helper.write_text('from blocks.unapproved import something\n')
        with self.assertRaises(AssertionError):check_domain_imports(root)
        helper.write_text('from . import unapproved\n')
        with self.assertRaises(AssertionError):check_domain_imports(root)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeTests))
    failed=len(result.failures)+len(result.errors)
    print(f'{result.testsRun-failed} passed, {failed} failed')
    raise SystemExit(bool(failed))
