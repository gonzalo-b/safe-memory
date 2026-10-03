"""Pairing domain proofs using synthetic credentials and isolated private stores."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import secrets
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore, RuntimeErrorResult, REPO
from runtime.pairing import PairingService

PASSWORD = 'synthetic pairing password'

class PairingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='memory-pairing-')
        self.now = 1800000000
        self.store = RuntimeStore(Path(self.tmp.name)/'store', fixture=True, clock=lambda:self.now)
        self.owner = self.store.create_owner('alice', PASSWORD, 'Synthetic owner')
        self.auth = self.store.login('alice', PASSWORD, 'local')
        self.service = PairingService(self.store)

    def tearDown(self): self.tmp.cleanup()

    def start(self): return self.service.start(self.auth['token'], self.auth['csrf_token'])
    def claim(self, intent=None, credential=None, library='library-a', name='Synthetic iPhone'):
        intent = intent or self.start(); credential = credential or secrets.token_urlsafe(32)
        claim = self.service.claim(intent['secret'], name, library, credential)
        return intent, credential, claim
    def confirm(self, claim):
        return self.service.confirm(self.auth['token'], self.auth['csrf_token'], claim['claim_id'], claim['fingerprint'])
    def denied(self, call, status=403):
        with self.assertRaises(RuntimeErrorResult) as error: call()
        self.assertEqual(error.exception.status, status)
    def rows(self, table):
        with self.store._db() as db:return [dict(row) for row in db.execute('SELECT * FROM '+table)]

    def test_start_preview_claim_do_not_register_and_store_only_hashes(self):
        intent = self.start()
        self.assertEqual(intent['expires_at'], self.now+300)
        self.assertEqual(len(intent['secret']),43)
        self.assertEqual(self.service.preview(intent['secret'])['status'],'awaiting_claim')
        _, credential, claim = self.claim(intent)
        self.assertEqual(self.service.preview(intent['secret'])['status'],'awaiting_confirmation')
        self.assertEqual(self.rows('vaults'),[]);self.assertEqual(self.rows('connections'),[])
        self.assertEqual(self.rows('devices'),[])
        self.assertEqual(self.service.pending(self.auth['token'])['claims'],[{
            'claim_id':claim['claim_id'],'device_name':'Synthetic iPhone',
            'fingerprint':claim['fingerprint'],'expires_at':intent['expires_at']}])
        stored=str(self.rows('pairing_intents'))+str(self.rows('audit'))
        self.assertNotIn(intent['secret'],stored);self.assertNotIn(credential,stored)
        for value in ('Synthetic iPhone','library-a',claim['fingerprint']):self.assertNotIn(value,str(self.rows('audit')))

    def test_confirm_creates_restricted_binding_and_idempotent_retries(self):
        intent, credential, claim = self.claim()
        self.assertEqual(self.service.claim(intent['secret'],'Synthetic iPhone','library-a',credential),claim)
        binding=self.confirm(claim)
        self.assertEqual(self.confirm(claim),binding)
        self.assertEqual(len(self.rows('vaults')),1);self.assertEqual(len(self.rows('connections')),1)
        source=self.rows('connections')[0]
        self.assertEqual((source['permission'],source['status']),('restricted','awaiting_ingest'))
        self.assertEqual((source['include_hidden'],source['include_shared_library'],source['include_shared_albums']),(0,0,0))
        result=self.service.authenticate(binding['device_id'],credential)
        self.assertEqual(result['owner_id'],self.owner);self.assertFalse(result['data_access'])
        self.assertEqual(result['connection_id'],source['id'])
        self.assertEqual(self.service.pending(self.auth['token'])['claims'],[])
        self.assertNotIn(credential,str(self.rows('devices')))

    def test_client_claim_id_becomes_device_id_only_after_owner_confirmation(self):
        _,credential,claim=self.claim()
        self.denied(lambda:self.service.authenticate(claim['claim_id'],credential),401)
        binding=self.confirm(claim)
        self.assertEqual(binding['device_id'],claim['claim_id'])
        self.assertEqual(self.service.authenticate(claim['claim_id'],credential)['connection_id'],binding['connection_id'])

    def test_expired_unclaimed_and_pending_intents_deny_at_boundary(self):
        empty=self.start();pending,credential,claim=self.claim()
        self.now+=300
        self.denied(lambda:self.service.claim(empty['secret'],'Phone','library',credential))
        self.denied(lambda:self.confirm(claim))
        self.denied(lambda:self.service.preview(pending['secret']))
        self.assertEqual(self.service.pending(self.auth['token'])['claims'],[])
        self.assertEqual(self.rows('devices'),[])

    def test_single_use_secret_and_claim_payload_cannot_be_substituted(self):
        intent, credential, claim=self.claim()
        for name,library,key in [('Other','library-a',credential),('Synthetic iPhone','other',credential),('Synthetic iPhone','library-a',secrets.token_urlsafe(32))]:
            self.denied(lambda:self.service.claim(intent['secret'],name,library,key))
        self.denied(lambda:self.service.confirm(self.auth['token'],self.auth['csrf_token'],claim['claim_id'],'0'*64))
        self.assertEqual(self.rows('devices'),[])
        self.confirm(claim)
        self.denied(lambda:self.service.claim(intent['secret'],'Synthetic iPhone','library-a',credential))

    def test_owner_scope_and_csrf_cover_all_mutations_and_reads(self):
        _,credential,claim=self.claim();binding=self.confirm(claim)
        _,_,pending=self.claim(library='second')
        self.store.create_owner('bob',PASSWORD,'Other owner')
        other=self.store.login('bob',PASSWORD,'other')
        self.assertEqual(self.service.pending(other['token'])['claims'],[])
        self.assertEqual(self.service.devices(other['token'])['devices'],[])
        self.denied(lambda:self.service.confirm(other['token'],other['csrf_token'],pending['claim_id'],pending['fingerprint']))
        self.denied(lambda:self.service.revoke(other['token'],other['csrf_token'],binding['device_id']))
        for operation in [lambda:self.service.start(self.auth['token'],'bad'),lambda:self.service.confirm(self.auth['token'],'bad',pending['claim_id'],pending['fingerprint']),lambda:self.service.revoke(self.auth['token'],'bad',binding['device_id'])]:self.denied(operation)
        for operation in [lambda:self.service.start(self.owner,'bad'),lambda:self.service.pending(self.owner),lambda:self.service.devices(self.owner)]:self.denied(operation,401)
        self.assertFalse(self.service.authenticate(binding['device_id'],credential)['data_access'])

    def test_revocation_epoch_and_spoofed_credentials_fail_immediately(self):
        _,credential,claim=self.claim();binding=self.confirm(claim)
        for device,key in [(self.owner,credential),(binding['device_id'],self.auth['token']),(binding['device_id'],secrets.token_urlsafe(32))]:self.denied(lambda:self.service.authenticate(device,key),401)
        self.service.revoke(self.auth['token'],self.auth['csrf_token'],binding['device_id'])
        self.assertEqual(self.service.revoke(self.auth['token'],self.auth['csrf_token'],binding['device_id']),{'ok':True})
        self.denied(lambda:self.service.authenticate(binding['device_id'],credential),401)
        self.denied(lambda:self.confirm(claim))
        _,key,next_claim=self.claim();next_binding=self.confirm(next_claim)
        with self.store.transaction() as db:db.execute('UPDATE owners SET auth_epoch=auth_epoch+1 WHERE id=?',(self.owner,))
        self.denied(lambda:self.service.authenticate(next_binding['device_id'],key),401)

    def test_reconnect_reuses_library_connection_and_vault_without_reactivating_old_key(self):
        _,key,claim=self.claim();first=self.confirm(claim)
        self.service.revoke(self.auth['token'],self.auth['csrf_token'],first['device_id'])
        _,_,new_claim=self.claim();second=self.confirm(new_claim)
        self.assertEqual(first['connection_id'],second['connection_id']);self.assertEqual(first['vault_id'],second['vault_id'])
        self.assertNotEqual(first['device_id'],second['device_id'])
        _,_,other_claim=self.claim(library='different-library');third=self.confirm(other_claim)
        self.assertNotEqual(third['connection_id'],first['connection_id']);self.assertEqual(third['vault_id'],first['vault_id'])
        self.denied(lambda:self.service.authenticate(first['device_id'],key),401)
        self.assertEqual(len(self.rows('connections')),2);self.assertEqual(len(self.rows('vaults')),1)

    def test_credential_cannot_bind_multiple_claims_or_owners(self):
        _,key,claim=self.claim();self.confirm(claim)
        intent=self.start()
        self.denied(lambda:self.service.claim(intent['secret'],'Phone','second',key))
        self.store.create_owner('bob',PASSWORD,'Other owner');bob=self.store.login('bob',PASSWORD,'bob')
        intent=self.service.start(bob['token'],bob['csrf_token'])
        self.denied(lambda:self.service.claim(intent['secret'],'Phone','library-a',key))

    def test_concurrent_claims_have_exactly_one_winner_and_retry(self):
        intent=self.start();keys=[secrets.token_urlsafe(32) for _ in range(2)]
        def attempt(key):
            try:return self.service.claim(intent['secret'],'Phone','library-a',key)
            except RuntimeErrorResult:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(attempt,keys))
        self.assertEqual(sum(result is not None for result in results),1)
        winner=next(i for i,result in enumerate(results) if result is not None)
        self.assertEqual(attempt(keys[winner]),results[winner]);self.assertEqual(len(self.rows('pairing_intents')),1)

    def test_invalid_input_cannot_inject_display_controls_or_weak_tokens(self):
        intent=self.start();key=secrets.token_urlsafe(32)
        for name,library,credential in [('Phone\nAdmin','library',key),('Phone\u202eadmin','library',key),('', 'library',key),('Phone','',key),('Phone','library','short'),('Phone','library','a'*44)]:
            self.denied(lambda:self.service.claim(intent['secret'],name,library,credential),400)
        self.assertEqual(self.rows('devices'),[])

    def test_audit_failure_rolls_back_start_claim_confirm_and_revoke(self):
        intent=self.start();_,key,claim=self.claim();binding=self.confirm(claim)
        _,_,pending=self.claim(library='second')
        before={table:self.rows(table) for table in ('pairing_intents','devices','connections','vaults')}
        with self.store.transaction() as db:db.execute("CREATE TRIGGER fail_pairing_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        operations=[lambda:self.start(),lambda:self.service.claim(intent['secret'],'Phone','new',secrets.token_urlsafe(32)),lambda:self.confirm(pending),lambda:self.service.revoke(self.auth['token'],self.auth['csrf_token'],binding['device_id']),lambda:self.service.authenticate(binding['device_id'],key),lambda:self.service.pending(self.auth['token'])]
        for operation in operations:self.denied(operation,503)
        self.assertEqual(before,{table:self.rows(table) for table in before})

    def test_restore_revokes_active_devices_and_all_pending_pairing(self):
        _,key,claim=self.claim();binding=self.confirm(claim)
        intent,_,pending=self.claim(library='second')
        backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored');service=PairingService(restored)
        self.denied(lambda:service.authenticate(binding['device_id'],key),401)
        fresh=restored.login('alice',PASSWORD,'local')
        self.denied(lambda:service.confirm(fresh['token'],fresh['csrf_token'],pending['claim_id'],pending['fingerprint']))
        self.denied(lambda:service.preview(intent['secret']))
        self.assertEqual(restored.sources(fresh['token'])['sources'][0]['status'],'reauthorization_required')
        self.assertFalse(self.service.authenticate(binding['device_id'],key)['data_access'])

    def test_backup_restore_never_buffers_database_file(self):
        backup=Path(self.tmp.name)/'streamed-backup'
        with mock.patch.object(Path,'read_bytes',side_effect=AssertionError('whole-file buffer forbidden')):
            self.store.backup(backup)
            restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'streamed-restore')
        self.assertEqual(restored.root.name,'streamed-restore')

    def test_confirm_retry_after_expiry_and_restart_retains_only_live_binding(self):
        _,credential,claim=self.claim();binding=self.confirm(claim)
        self.now+=301
        second=PairingService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now))
        self.assertEqual(second.confirm(self.auth['token'],self.auth['csrf_token'],claim['claim_id'],claim['fingerprint']),binding)
        self.assertEqual(second.authenticate(binding['device_id'],credential)['device_id'],binding['device_id'])

    def test_concurrent_confirms_reuse_one_binding(self):
        _,_,claim=self.claim()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:self.confirm(claim),range(2)))
        self.assertEqual(results[0],results[1]);self.assertEqual(len(self.rows('devices')),1)
        self.assertEqual(len(self.rows('connections')),1);self.assertEqual(len(self.rows('vaults')),1)

    def test_failed_restore_of_v2_leaves_credentials_quarantined(self):
        _,key,claim=self.claim();binding=self.confirm(claim)
        with self.store.transaction() as db:db.execute("CREATE TRIGGER fail_restore_pairing BEFORE INSERT ON audit WHEN NEW.action='restore' BEGIN SELECT RAISE(ABORT,'full'); END")
        backup=Path(self.tmp.name)/'failed-backup';self.store.backup(backup)
        destination=Path(self.tmp.name)/'failed-restore'
        self.denied(lambda:RuntimeStore.restore(backup,destination),503)
        with self.assertRaises(ValueError):RuntimeStore(destination,fixture=True)
        self.assertTrue((destination/'restore.incomplete').exists())
        self.assertFalse(self.service.authenticate(binding['device_id'],key)['data_access'])

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-pairing-migration-');self.root=Path(self.tmp.name)/'store';self.root.mkdir()
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            db.executescript((REPO/'schema/runtime-v1.sql').read_text())
            db.execute('PRAGMA user_version=1');db.execute("INSERT INTO metadata VALUES('fixture','true')")
            db.execute("INSERT INTO owners VALUES('owner','alice','Synthetic','unused',1,1)")
    def tearDown(self):self.tmp.cleanup()
    def test_migration_has_audited_private_backup_and_preserves_v1_facts(self):
        store=RuntimeStore(self.root,fixture=True)
        with store._db() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],7)
            self.assertEqual(db.execute('SELECT id FROM owners').fetchone()[0],'owner')
            self.assertIsNone(db.execute('PRAGMA foreign_key_check').fetchone())
        backups=list((self.root/'migration-backups').glob('*/manifest.json'));self.assertEqual(len(backups),1)
        manifest=json.loads(backups[0].read_text());self.assertEqual(manifest['schema'],1)
        self.assertEqual(backups[0].stat().st_mode & 0o777,0o600)
        with sqlite3.connect(backups[0].parent/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertEqual(db.execute("SELECT count(*) FROM audit WHERE action='backup'").fetchone()[0],1)
        RuntimeStore(self.root,fixture=True)
        self.assertEqual(len(list((self.root/'migration-backups').glob('*/manifest.json'))),1)
    def test_failed_migration_rolls_back_and_audit_failure_prevents_backup(self):
        original=Path.read_text
        def broken(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            return value+'\nINVALID SQL;' if path.name=='runtime-v2.sql' else value
        with mock.patch.object(Path,'read_text',broken):
            with self.assertRaises(sqlite3.Error):RuntimeStore(self.root,fixture=True)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='devices'").fetchone())
            db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        before=list((self.root/'migration-backups').glob('*/manifest.json'))
        with self.assertRaises(RuntimeErrorResult):RuntimeStore(self.root,fixture=True)
        self.assertEqual(list((self.root/'migration-backups').glob('*/manifest.json')),before)
    def test_migration_audit_failure_rolls_back_entire_schema_change(self):
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            db.execute("CREATE TRIGGER fail_migration_audit BEFORE INSERT ON audit WHEN NEW.action='migration' BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(RuntimeErrorResult):RuntimeStore(self.root,fixture=True)
        with sqlite3.connect(self.root/'memory.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='devices'").fetchone())
            self.assertEqual(db.execute('SELECT id FROM owners').fetchone()[0],'owner')
        self.assertEqual(len(list((self.root/'migration-backups').glob('*/manifest.json'))),1)

    def test_v1_backup_can_restore_with_revocation_then_migration(self):
        from runtime.store import file_digest
        import shutil
        backup=Path(self.tmp.name)/'v1-backup';backup.mkdir()
        shutil.copyfile(self.root/'memory.sqlite3',backup/'memory.sqlite3')
        (backup/'manifest.json').write_text(json.dumps({'schema':1,'fixture':True,'sha256':file_digest(backup/'memory.sqlite3')}))
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'v1-restored')
        with restored._db() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],7)
            self.assertEqual(db.execute('SELECT auth_epoch FROM owners').fetchone()[0],2)
        self.assertTrue((restored.root/'restore.completed').exists())

    def test_fixture_mismatch_refuses_before_migration(self):
        with self.assertRaises(ValueError):RuntimeStore(self.root,fixture=False)
        self.assertFalse((self.root/'migration-backups').exists())

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    failed=len(result.failures)+len(result.errors)
    print(f'{result.testsRun-failed} passed, {failed} failed')
    raise SystemExit(bool(failed))
