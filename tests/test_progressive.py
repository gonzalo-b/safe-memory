"""Frozen authorized scan pages; generated metadata only."""
import sqlite3
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_ingestion import IngestionTests
from runtime.progressive import ProgressiveService
from runtime.store import RuntimeStore, RuntimeErrorResult

class ProgressiveTests(unittest.TestCase):
    def asset(self,native='asset-a',revision='r1',**changes):
        changes.setdefault('capture_time','2027-01-01T23:30:00-03:00')
        return IngestionTests.asset(self,native,revision,**changes)
    rows=IngestionTests.rows
    tearDown=IngestionTests.tearDown
    def setUp(self):
        IngestionTests.setUp(self)
        self.scan=ProgressiveService(self.store)
    def start(self,key='scan-a',count=3,permission='full',hidden=False,shared_library=False,shared_albums=False):
        return self.scan.begin(self.device,self.credential,key,permission,count,hidden,shared_library,shared_albums)
    def page(self,run,assets,sequence=0,phase='recent',key=None):
        return self.scan.append(self.device,self.credential,run['run_id'],key or 'batch-'+str(sequence),sequence,'cursor-'+str(sequence),phase,assets)
    def finish(self,run):return self.scan.finish(self.device,self.credential,run['run_id'])
    def old(self,native='old'):
        return self.asset(native,capture_time='2020-01-01T12:00:00-03:00')
    def test_recent_then_backfill_visible_progress_replay_restart(self):
        r=self.start();p=self.page(r,[self.asset('recent')]);self.assertEqual(p['observed'],1)
        self.assertEqual(self.page(r,[self.asset('recent')]),p);self.assertEqual(len(self.rows()),1)
        self.scan=ProgressiveService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now))
        r2=self.start();self.assertEqual(r2['run_id'],r['run_id']);self.assertEqual(r2['next_sequence'],1)
        self.page(r,[self.old(),self.asset('unknown',capture_time=None,time_basis='unknown')],1,'backfill')
        done=self.finish(r);self.assertEqual(done['observed'],3);self.assertEqual(done['coverage'],'authorized_full_scan')
        self.assertEqual(done,self.finish(r));self.assertEqual(len(self.rows()),3)
        progress=self.scan.progress(self.auth['token'])['scans'][0]
        self.assertEqual((progress['observed'],progress['expected_count'],progress['missing_date']), (3,3,1))
    def test_library_and_overview_coverage_are_based_on_current_scan(self):
        self.assertEqual(self.service.assets(self.auth['token'])['coverage']['mode'],'selected_samples')
        r=self.start(count=1);self.page(r,[self.asset()])
        self.assertEqual(self.service.assets(self.auth['token'])['coverage']['mode'],'progressive')
        self.finish(r)
        self.assertEqual(self.store.overview(self.auth['token'])['coverage']['index_state'],'authorized_scan_indexed')
        self.service.permission(self.device,self.credential,'revoked')
        self.assertEqual(self.service.assets(self.auth['token'])['coverage']['mode'],'restricted_or_unknown')
    def test_current_order_index_tracks_revisions_and_does_not_bypass_policy(self):
        r=self.start(count=2)
        self.page(r,[self.asset('a')]);self.page(r,[self.old('b')],1,'backfill');self.finish(r)
        self.assertEqual([a['native_id'] for a in self.rows()],['a','b'])
        r2=self.start('next',2)
        self.page(r2,[self.asset('b',revision='new',source_modified='2027-01-10T00:00:00Z')])
        self.page(r2,[self.old('a') | {'source_revision':'hidden-new','hidden':True,'source_modified':'2027-01-10T00:00:00Z'}],1,'backfill');self.finish(r2)
        self.assertEqual([a['native_id'] for a in self.rows()],['b'])
        with self.store._db() as db:
            row=db.execute("SELECT x.capture_day FROM current_asset_index x JOIN assets a ON a.id=x.asset_id WHERE a.native_id='b'").fetchone()
            self.assertEqual(row['capture_day'],'2027-01-01')
    def test_count_missing_duplicate_and_time_order_fail_atomically(self):
        r=self.start()
        with self.assertRaises(RuntimeErrorResult):self.finish(r)
        self.page(r,[self.asset('a')])
        for values,phase in [([self.asset('a')],'recent'),([self.old('b'),self.asset('c')],'backfill'),([self.old('b')],'recent')]:
            with self.assertRaises(RuntimeErrorResult):self.page(r,values,1,phase)
        self.assertEqual(len(self.rows()),1)
        self.page(r,[self.old('b')],1,'backfill')
        with self.assertRaises(RuntimeErrorResult):self.page(r,[self.asset('c')],2,'recent')
    def test_scope_policy_and_device_revocation_override_replay_and_retry(self):
        r=self.start();self.page(r,[self.asset('a')])
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,False,False)
        for call in [lambda:self.start(),lambda:self.page(r,[self.asset('a')]),lambda:self.scan.retry(self.auth['token'],self.auth['csrf_token'],r['run_id'])]:
            with self.assertRaises(RuntimeErrorResult):call()
        progress=self.scan.progress(self.auth['token'])['scans'][0]
        self.assertEqual(progress['state'],'restricted');self.assertNotIn('observed',progress)
    def test_full_and_limited_reconcile_absence_only_at_complete(self):
        r=self.start(count=2);self.page(r,[self.asset('a'),self.asset('b')]);self.finish(r)
        r2=self.start('scan-b',1);self.assertEqual(len(self.rows()),2)
        self.page(r2,[self.asset('a')]);self.assertEqual(len(self.rows()),2);self.finish(r2)
        self.assertEqual([x['native_id'] for x in self.rows()],['a'])
        r3=self.start('scan-c',1,'limited');self.assertEqual(self.rows(),[])
        self.page(r3,[self.asset('b')]);self.assertEqual(self.finish(r3)['coverage'],'authorized_limited_scan')
        self.assertEqual([x['native_id'] for x in self.rows()],['b'])
    def test_empty_scan_is_known_zero_and_retains_restricted_history(self):
        r=self.start(count=1);self.page(r,[self.asset()]);self.finish(r)
        r2=self.start('empty',0);self.finish(r2);self.assertEqual(self.rows(),[])
        with sqlite3.connect(self.store.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM assets').fetchone()[0],1)
    def test_consent_never_changes_source_and_exclusions_count_once(self):
        with self.assertRaises(RuntimeErrorResult):self.start(hidden=True)
        r=self.start(count=2);p=self.page(r,[self.asset('h',hidden=True),self.asset('s',collection='shared_album')]);self.assertEqual((p['accepted'],p['excluded'],p['observed']),(0,2,2))
        self.assertEqual(self.page(r,[self.asset('h',hidden=True),self.asset('s',collection='shared_album')]),p)
        self.finish(r);self.assertEqual(self.rows(),[])
    def test_retry_waits_for_device_and_never_changes_authority(self):
        r=self.start();result=self.scan.retry(self.auth['token'],self.auth['csrf_token'],r['run_id'])
        self.assertEqual(result['state'],'waiting_for_device')
        self.assertTrue(self.scan.progress(self.auth['token'])['scans'][0]['retry_requested'])
        self.start();self.assertFalse(self.scan.progress(self.auth['token'])['scans'][0]['retry_requested'])
        with self.assertRaises(RuntimeErrorResult):self.scan.retry(self.auth['token'],'wrong',r['run_id'])
    def test_sample_route_cannot_bypass_scan_order_or_count(self):
        r=self.start()
        with self.assertRaises(RuntimeErrorResult):self.service.append(self.device,self.credential,r['run_id'],'bypass',0,'x',[self.asset()])
        with self.assertRaises(RuntimeErrorResult):self.service.finish(self.device,self.credential,r['run_id'])
    def test_failed_page_and_audit_leave_previous_checkpoint(self):
        r=self.start();self.page(r,[self.asset('a')])
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER reject_scan BEFORE INSERT ON scan_assets BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(sqlite3.Error):self.page(r,[self.asset('b')],1)
        self.assertEqual(len(self.rows()),1);self.assertEqual(self.start()['next_sequence'],1)
    def test_backup_restores_progress_but_never_authority(self):
        r=self.start();self.page(r,[self.asset('a')])
        backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored')
        with self.assertRaises(RuntimeErrorResult):ProgressiveService(restored).progress(self.auth['token'])
        auth=restored.login('owner','synthetic-only-password','restored')
        view=ProgressiveService(restored).progress(auth['token'])['scans'][0]
        self.assertEqual(view['state'],'restricted');self.assertNotIn('observed',view)
        with restored._db() as db:
            self.assertEqual(db.execute('SELECT observed FROM scan_runs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM scan_assets').fetchone()[0],1)
        with self.assertRaises(RuntimeErrorResult):ProgressiveService(restored).begin(self.device,self.credential,'scan-a','full',3,False,False,False)
    def test_failed_audit_rolls_back_page_and_retry(self):
        r=self.start();self.page(r,[self.asset('a')])
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER reject_writes BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(RuntimeErrorResult):self.page(r,[self.asset('b')],1)
        with self.assertRaises(RuntimeErrorResult):self.scan.retry(self.auth['token'],self.auth['csrf_token'],r['run_id'])
        with self.store._db() as db:
            self.assertEqual(db.execute('SELECT observed FROM scan_runs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT retry_requested FROM scan_runs').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM assets').fetchone()[0],1)
    def test_owner_filter_and_unauditable_progress(self):
        r=self.start(count=0)
        self.store.create_owner('other','synthetic-other-password','Other');other=self.store.login('other','synthetic-other-password','other')
        self.assertEqual(self.scan.progress(other['token'])['scans'],[])
        with self.assertRaises(RuntimeErrorResult):self.scan.retry(other['token'],other['csrf_token'],r['run_id'])
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER reject_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(RuntimeErrorResult):self.scan.progress(self.auth['token'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProgressiveTests))
    failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
