"""Resumable metadata ingestion and current-policy disclosure using synthetic assets."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import subprocess
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore, RuntimeErrorResult
from runtime.pairing import PairingService
from runtime.ingestion import IngestionService

PASSWORD='synthetic-only-password'
class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-ingestion-')
        self.now=1800000000
        self.store=RuntimeStore(Path(self.tmp.name)/'store',fixture=True,clock=lambda:self.now)
        self.owner=self.store.create_owner('owner',PASSWORD,'Synthetic owner')
        self.auth=self.store.login('owner',PASSWORD,'local')
        self.pairing=PairingService(self.store)
        import secrets
        intent=self.pairing.start(self.auth['token'],self.auth['csrf_token'])
        self.credential=secrets.token_urlsafe(32)
        claim=self.pairing.claim(intent['secret'],'Synthetic iPhone','library-a',self.credential)
        binding=self.pairing.confirm(self.auth['token'],self.auth['csrf_token'],claim['claim_id'],claim['fingerprint'])
        self.device=claim['claim_id'];self.connection=binding['connection_id']
        self.service=IngestionService(self.store)

    def tearDown(self):self.tmp.cleanup()

    def asset(self,native='asset-a',revision='r1',**changes):
        value={'native_id':native,'source_revision':revision,'media_type':'photo','hidden':False,'collection':'personal',
               'capture_time':'2026-10-01T23:30:00-03:00','time_basis':'capture_offset','owner_presence':'unknown',
               'source_modified':'2026-10-02T12:00:00Z','metadata':{'nativeField':'preserved','location':None}}
        value.update(changes);return value

    def begin(self,key='run-a',ids=None,permission='full',phase='recent'):
        return self.service.begin(self.device,self.credential,key,permission,phase,ids or ['asset-a'])

    def append(self,run,assets,key='batch-a',sequence=0):
        return self.service.append(self.device,self.credential,run['run_id'],key,sequence,'checkpoint-'+key,assets)

    def rows(self):return self.service.assets(self.auth['token'])['assets']

    def test_replay_and_restart_preserve_identity_raw_and_atomic_checkpoint(self):
        run=self.begin();receipt=self.append(run,[self.asset()]);replay=self.append(run,[self.asset()])
        self.assertEqual(receipt,replay)
        self.assertEqual(len(self.rows()),1)
        other=IngestionService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now))
        resumed=other.begin(self.device,self.credential,'run-a','full','recent',['asset-a'])
        self.assertEqual(resumed['run_id'],run['run_id']);self.assertEqual(resumed['next_sequence'],1)
        with sqlite3.connect(self.store.path) as db:
            raw=db.execute('SELECT raw_json FROM asset_revisions').fetchone()[0]
            self.assertEqual(json.loads(raw),self.asset()['metadata'])
        with self.assertRaises(RuntimeErrorResult) as error:self.append(run,[self.asset(metadata={'changed':True})])
        self.assertEqual(error.exception.status,409)

    def test_batch_failure_rolls_back_assets_receipt_and_checkpoint(self):
        run=self.begin()
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER fail_batch BEFORE INSERT ON ingest_batches BEGIN SELECT RAISE(ABORT,'disk full'); END")
        with self.assertRaises(sqlite3.Error):self.append(run,[self.asset()])
        self.assertEqual(self.rows(),[])
        with sqlite3.connect(self.store.path) as db:
            self.assertEqual(db.execute('SELECT next_sequence FROM ingest_runs').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM asset_revisions').fetchone()[0],0)

    def test_hidden_transition_restricts_existing_data_but_retains_revisions(self):
        run=self.begin();self.append(run,[self.asset()])
        self.append(run,[self.asset(revision='r2',hidden=True)],key='batch-b',sequence=1)
        self.assertEqual(self.rows(),[])
        with sqlite3.connect(self.store.path) as db:self.assertGreaterEqual(db.execute('SELECT count(*) FROM asset_revisions').fetchone()[0],1)
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,False,False)
        self.assertEqual(len(self.rows()),1)
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,False,False,False)
        self.assertEqual(self.rows(),[])

    def test_new_hidden_and_shared_assets_excluded_without_separate_consent(self):
        run=self.begin(ids=['h','s','a','u'])
        result=self.append(run,[self.asset('h',hidden=True),self.asset('s',collection='shared_library'),self.asset('a',collection='shared_album'),self.asset('u',collection='unknown')])
        self.assertEqual(result['accepted'],0);self.assertEqual(result['excluded'],4);self.assertEqual(self.rows(),[])
        with sqlite3.connect(self.store.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM asset_revisions').fetchone()[0],0)

    def test_collection_consent_is_independent_and_third_party_remains_unknown_presence(self):
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,False,True,False)
        run=self.begin(ids=['s','a']);self.append(run,[self.asset('s',collection='shared_library',owner_presence='third_party'),self.asset('a',collection='shared_album')])
        rows=self.rows();self.assertEqual(len(rows),1);self.assertEqual(rows[0]['owner_presence'],'third_party')
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,False,False,True)
        self.assertEqual(self.rows(),[])

    def test_limited_scope_and_permission_revocation_apply_before_disclosure(self):
        run=self.begin(ids=['asset-a','asset-b']);self.append(run,[self.asset(),self.asset('asset-b')]);self.service.finish(self.device,self.credential,run['run_id'])
        run=self.begin('run-b',['asset-a'],'limited');self.assertEqual(self.rows(),[])
        self.append(run,[self.asset()]);self.assertEqual(len(self.rows()),1)
        self.service.permission(self.device,self.credential,'revoked')
        self.assertEqual(self.rows(),[])
        with self.assertRaises(RuntimeErrorResult):self.append(run,[self.asset()],key='next',sequence=1)

    def test_sequence_lease_selection_and_input_limits(self):
        run=self.begin()
        for assets,key,sequence in [([self.asset('not-selected')],'bad',0),([self.asset()],'out-of-order',2),([self.asset()]*101,'large',0)]:
            with self.assertRaises(RuntimeErrorResult):self.append(run,assets,key,sequence)
        with self.assertRaises(RuntimeErrorResult):self.begin('another-run')
        self.now+=901
        with self.assertRaises(RuntimeErrorResult):self.append(run,[self.asset()])
        resumed=self.begin();self.assertEqual(resumed['run_id'],run['run_id'])
        self.append(resumed,[self.asset()])

    def test_owner_isolation_csrf_and_audit_failure(self):
        run=self.begin();self.append(run,[self.asset()])
        self.store.create_owner('other',PASSWORD,'Other')
        other=self.store.login('other',PASSWORD,'other')
        self.assertEqual(self.service.assets(other['token'])['assets'],[])
        with self.assertRaises(RuntimeErrorResult):self.service.configure(other['token'],other['csrf_token'],self.connection,True,True,True)
        with self.assertRaises(RuntimeErrorResult):self.service.configure(self.auth['token'],'wrong',self.connection,True,True,True)
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(RuntimeErrorResult):self.rows()
        with self.assertRaises(RuntimeErrorResult):self.append(run,[self.asset(revision='r2')],key='next',sequence=1)

    def test_capture_offset_unknowns_and_old_revision_do_not_invent_facts(self):
        run=self.begin(ids=['asset-a','instant','missing'])
        self.append(run,[self.asset(),self.asset('instant',capture_time='2026-10-02T01:30:00Z',time_basis='instant_only'),self.asset('missing',capture_time=None,time_basis='unknown')])
        self.append(run,[self.asset(revision='older',capture_time='2025-01-01T00:00:00Z',source_modified='2025-01-01T00:00:00Z')],key='older',sequence=1)
        rows={r['native_id']:r for r in self.rows()}
        self.assertEqual(rows['asset-a']['capture_day'],'2026-10-01')
        self.assertIsNone(rows['instant']['capture_day']);self.assertIsNone(rows['missing']['capture_day'])
        self.assertEqual(rows['asset-a']['capture_time'],'2026-10-01T23:30:00-03:00')

    def test_index_completion_does_not_claim_media_ready_or_whole_library(self):
        run=self.begin();self.append(run,[self.asset(media_type='live')])
        result=self.service.finish(self.device,self.credential,run['run_id'])
        self.assertEqual(result['coverage'],'bounded_authorized_sample')
        self.assertEqual(result['media_ready'],0)
        self.assertEqual(self.rows()[0]['media_state'],'not_transferred')

    def test_malformed_enums_and_normalized_invalid_offsets_are_rejected(self):
        run=self.begin()
        for field in ('media_type','collection','time_basis','owner_presence'):
            with self.subTest(field=field):
                with self.assertRaises(RuntimeErrorResult) as error:self.append(run,[self.asset(**{field:[]})])
                self.assertEqual(error.exception.status,400)
        for value in ('2026-10-01T23:30:00+03:99','20261001T233000+0300'):
            with self.assertRaises(RuntimeErrorResult):self.append(run,[self.asset(capture_time=value)])
        self.assertEqual(self.rows(),[])

    def test_completed_batch_replay_is_idempotent_and_stale_selected_asset_stays_visible(self):
        run=self.begin();receipt=self.append(run,[self.asset()]);self.service.finish(self.device,self.credential,run['run_id'])
        self.assertEqual(self.append(run,[self.asset()]),receipt)
        limited=self.begin('limited',['asset-a'],'limited')
        self.append(limited,[self.asset(revision='older',source_modified='2025-01-01T00:00:00Z')])
        self.assertEqual(len(self.rows()),1)

    def test_crash_before_and_after_commit_preserves_checkpoint_boundary(self):
        run=self.begin()
        script='''
import json,os,sys
from runtime.store import RuntimeStore
from runtime.ingestion import IngestionService
x=json.load(sys.stdin);s=RuntimeStore(x['root'],fixture=True,clock=lambda:x['now'])
if x['before']:
 original=s._audit
 def crash(db,owner,action,outcome,count=0):
  if action=='ingest_batch':os._exit(73)
  return original(db,owner,action,outcome,count)
 s._audit=crash
IngestionService(s).append(x['device'],x['credential'],x['run'],'batch-a',0,'checkpoint-batch-a',[x['asset']])
os._exit(74)
'''
        for before,count,sequence in [(True,0,0),(False,1,1)]:
            payload={'root':str(self.store.root),'now':self.now,'device':self.device,'credential':self.credential,'run':run['run_id'],'asset':self.asset(),'before':before}
            result=subprocess.run([sys.executable,'-c',script],input=json.dumps(payload),text=True,capture_output=True,cwd=Path(__file__).resolve().parents[1])
            self.assertEqual(result.returncode,73 if before else 74,result.stderr)
            self.assertEqual(len(self.rows()),count)
            self.assertEqual(self.begin()['next_sequence'],sequence)
        self.assertEqual(self.append(run,[self.asset()])['accepted'],1)
        self.assertEqual(len(self.rows()),1)

    def test_revoked_source_cannot_replay_completed_run_status(self):
        run=self.begin();self.append(run,[self.asset()]);self.service.finish(self.device,self.credential,run['run_id'])
        self.service.permission(self.device,self.credential,'revoked')
        with self.assertRaises(RuntimeErrorResult) as error:self.begin()
        self.assertEqual(error.exception.status,403)

    def test_restore_preserves_metadata_but_revokes_device_and_source_visibility(self):
        run=self.begin();self.append(run,[self.asset()]);backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored')
        service=IngestionService(restored)
        with self.assertRaises(RuntimeErrorResult):service.append(self.device,self.credential,run['run_id'],'next',1,'next',[self.asset()])
        auth=restored.login('owner',PASSWORD,'restored')
        self.assertEqual(service.assets(auth['token'])['assets'],[])
        with sqlite3.connect(restored.path) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM asset_revisions').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT state FROM ingest_runs').fetchone()[0],'interrupted')

    def test_old_revision_cannot_reverse_excluded_hidden_observation(self):
        run=self.begin();old=self.asset();self.append(run,[old])
        self.append(run,[self.asset(revision='hidden',hidden=True)],key='hidden',sequence=1)
        self.assertEqual(self.rows(),[])
        self.append(run,[old],key='old-replay',sequence=2)
        self.assertEqual(self.rows(),[])

    def test_known_revision_cannot_rewind_unknown_timestamp_or_admitted_hidden(self):
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,False,False)
        run=self.begin();old=self.asset(source_modified=None,capture_time='2025-01-01T00:00:00Z');self.append(run,[old])
        self.append(run,[self.asset(revision='newer',source_modified=None,hidden=True)],key='newer',sequence=1)
        self.append(run,[old],key='old',sequence=2)
        self.assertTrue(self.rows()[0]['hidden'])
        self.assertEqual(self.rows()[0]['capture_time'],'2026-10-01T23:30:00-03:00')
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,False,False,False)
        fresh=self.begin('fresh');self.append(fresh,[old])
        self.assertEqual(self.rows(),[])

    def test_old_limited_run_and_receipt_cannot_restore_newly_excluded_ids(self):
        old=self.begin('old',['asset-a','asset-b'],'limited');values=[self.asset(),self.asset('asset-b')]
        self.append(old,values);self.service.finish(self.device,self.credential,old['run_id'])
        fresh=self.begin('fresh',['asset-a'],'limited');self.append(fresh,[self.asset()]);self.service.finish(self.device,self.credential,fresh['run_id'])
        for action in (lambda:self.begin('old',['asset-a','asset-b'],'limited'),lambda:self.append(old,values),lambda:self.append(old,[self.asset('asset-b')],key='resurrect',sequence=1)):
            with self.assertRaises(RuntimeErrorResult):action()
        self.assertEqual([r['native_id'] for r in self.rows()],['asset-a'])

    def test_repeated_limited_report_invalidates_selection_and_pending_run(self):
        run=self.begin(permission='limited');self.append(run,[self.asset()]);self.assertEqual(len(self.rows()),1)
        self.service.permission(self.device,self.credential,'limited')
        self.assertEqual(self.rows(),[])
        with self.assertRaises(RuntimeErrorResult):self.begin(permission='limited')

    def test_policy_change_stops_old_run_but_allows_fresh_explicit_selection(self):
        run=self.begin();self.append(run,[self.asset()])
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,False,False)
        with self.assertRaises(RuntimeErrorResult):self.append(run,[self.asset(revision='new')],key='new',sequence=1)
        fresh=self.begin('fresh');self.assertNotEqual(fresh['run_id'],run['run_id'])

    def test_incomplete_declared_schema_refuses_startup(self):
        with sqlite3.connect(self.store.path) as db:db.execute('ALTER TABLE asset_observations RENAME TO archived_observations')
        with self.assertRaises(ValueError):RuntimeStore(self.store.root,fixture=True)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IngestionTests))
    failed=len(result.failures)+len(result.errors)
    print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
