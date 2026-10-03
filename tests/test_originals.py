"""Explicit original requests against synthetic opaque resource bytes only."""
import hashlib,json,sqlite3,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_media import MediaTests
from tests.test_ingestion import PASSWORD
from runtime.originals import OriginalService
from runtime.media import MediaService,media_path
from runtime.store import RuntimeStore,RuntimeErrorResult

class OriginalTests(unittest.TestCase):
    asset=MediaTests.asset;begin=MediaTests.begin;append=MediaTests.append;rows=MediaTests.rows;tearDown=MediaTests.tearDown
    def setUp(self):
        MediaTests.setUp(self);self.original=OriginalService(self.store);self.token=self.auth['token'];self.csrf=self.auth['csrf_token'];self.data=b'synthetic-original-resource\0full exact bytes'
    def request(self,key='request'):return self.original.request(self.token,self.csrf,self.asset_id,key)
    def manifest(self,data=None,kind='photo',filename='original.heic',uti='public.heic'):
        data=self.data if data is None else data
        return {'resource_type':kind,'original_filename':filename,'uniform_type_identifier':uti,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    def start(self,r=None,manifest=None):
        r=self.request() if r is None else r
        return self.original.begin(self.device,self.credential,r['request_id'],manifest or [self.manifest()])
    def upload(self,r=None):
        started=self.start(r);u=started['resources'][0]['upload_id'];self.original.chunk(self.device,self.credential,u,0,self.data);return self.original.complete(self.device,self.credential,u)
    def test_owner_request_waits_offline_is_idempotent_and_does_not_download(self):
        self.assertIsNone(self.original.status(self.token,self.asset_id)['request'])
        r=self.request();self.assertEqual(r['state'],'waiting_for_device');self.assertEqual(r,self.request())
        self.assertEqual(self.request('another')['request_id'],r['request_id'])
        self.assertEqual(self.original.pending(self.device,self.credential)['requests'][0]['request_id'],r['request_id'])
        with self.store._db() as db:self.assertEqual(db.execute('SELECT count(*) FROM original_uploads').fetchone()[0],0);self.assertEqual(db.execute('SELECT count(*) FROM original_requests').fetchone()[0],1)
    def test_exact_resource_staging_checkpoint_restart_and_final_hash(self):
        r=self.request();s=self.start(r);u=s['resources'][0]['upload_id'];half=len(self.data)//2
        first=self.original.chunk(self.device,self.credential,u,0,self.data[:half]);self.assertEqual(first,self.original.chunk(self.device,self.credential,u,0,self.data[:half]))
        self.original=OriginalService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now))
        self.assertEqual(self.start(r)['resources'][0]['next_offset'],half)
        self.original.chunk(self.device,self.credential,u,half,self.data[half:]);done=self.original.complete(self.device,self.credential,u)
        self.assertEqual(done,self.original.complete(self.device,self.credential,u));self.assertEqual(done['state'],'ready')
        read=self.original.read(self.token,done['component_id'],3,7);self.assertEqual(read['content'],self.data[3:10]);self.assertEqual(read['mime'],'application/octet-stream');self.assertEqual(read['filename'],'original.heic')
        self.assertEqual(self.original.pending(self.device,self.credential)['requests'],[])
        self.assertEqual(self.media.library(self.token,self.asset_id)['state'],'not_transferred')
    def test_failed_retry_retains_chunks_and_requires_explicit_owner_retry(self):
        r=self.request();s=self.start(r);u=s['resources'][0]['upload_id'];self.original.chunk(self.device,self.credential,u,0,self.data[:8])
        self.original.fail(self.device,self.credential,r['request_id'],'icloud_unavailable')
        self.assertEqual(self.original.status(self.token,self.asset_id)['request']['state'],'failed');self.assertEqual(self.original.pending(self.device,self.credential)['requests'],[])
        with self.assertRaises(RuntimeErrorResult):self.start(r)
        retry=self.original.retry(self.token,self.csrf,r['request_id'],'retry');self.assertEqual(retry['state'],'waiting_for_device');self.assertEqual(retry,self.original.retry(self.token,self.csrf,r['request_id'],'retry'))
        self.assertEqual(self.start(r)['resources'][0]['next_offset'],8)
    def test_live_requires_photo_and_motion_and_retains_ancillary_audio(self):
        self.append(self.run,[self.asset(revision='live',media_type='live',source_modified='2026-10-03T00:00:00Z')],key='live',sequence=1)
        r=self.request()
        with self.assertRaises(RuntimeErrorResult):self.start(r)
        resources=[self.manifest(),self.manifest(b'motion','paired_video','live.mov','com.apple.quicktime-movie'),self.manifest(b'audio','audio','audio.m4a','public.mpeg-4-audio')]
        s=self.start(r,resources)
        for i,data in enumerate([self.data,b'motion',b'audio']):
            u=s['resources'][i]['upload_id'];self.original.chunk(self.device,self.credential,u,0,data);done=self.original.complete(self.device,self.credential,u)
            self.assertEqual(done['state'],'ready' if i==2 else 'transferring')
            if i<2:
                with self.assertRaises(RuntimeErrorResult):self.original.read(self.token,done['component_id'])
        self.assertEqual(len(self.original.status(self.token,self.asset_id)['request']['resources']),3)
    def test_missing_original_and_changed_manifest_never_substitute_optimized_bytes(self):
        r=self.request();self.start(r)
        for resources in [[],[self.manifest(kind='video')],[self.manifest(filename='../escape')],[self.manifest(uti='<html>')],[self.manifest(),self.manifest()]]:
            with self.assertRaises(RuntimeErrorResult):self.start(r,resources) if resources else self.original.begin(self.device,self.credential,r['request_id'],resources)
        with self.assertRaises(RuntimeErrorResult):self.start(r,[self.manifest(b'changed')])
        self.assertEqual(self.original.status(self.token,self.asset_id)['request']['state'],'transferring')
    def test_revocation_revision_hidden_owner_and_replay_are_checked_now(self):
        done=self.upload();self.store.create_owner('other',PASSWORD,'Other');other=self.store.login('other',PASSWORD,'other')
        with self.assertRaises(RuntimeErrorResult):self.original.read(other['token'],done['component_id'])
        self.append(self.run,[self.asset(revision='hidden',hidden=True,source_modified='2026-10-03T00:00:00Z')],key='hidden',sequence=1)
        for call in [lambda:self.request(),lambda:self.original.status(self.token,self.asset_id),lambda:self.original.read(self.token,done['component_id'])]:
            with self.assertRaises(RuntimeErrorResult):call()
        self.assertEqual(self.original.pending(self.device,self.credential)['requests'],[])
    def test_changed_visible_revision_stales_request_and_new_request_is_separate(self):
        old=self.request();self.start(old);self.append(self.run,[self.asset(revision='r2',source_modified='2026-10-03T00:00:00Z')],key='r2',sequence=1)
        self.assertIsNone(self.original.status(self.token,self.asset_id)['request'])
        with self.assertRaises(RuntimeErrorResult):self.start(old)
        with self.assertRaises(RuntimeErrorResult):self.request()
        new=self.request('new');self.assertNotEqual(new['request_id'],old['request_id'])
    def test_integrity_failure_cannot_publish_and_changed_chunk_conflicts(self):
        s=self.start();u=s['resources'][0]['upload_id'];self.original.chunk(self.device,self.credential,u,0,b'x'*len(self.data))
        with self.assertRaises(RuntimeErrorResult):self.original.chunk(self.device,self.credential,u,0,self.data)
        with self.assertRaises(RuntimeErrorResult):self.original.complete(self.device,self.credential,u)
        self.assertEqual(self.original.status(self.token,self.asset_id)['request']['state'],'transferring')
        with self.store._db() as db:self.assertEqual(db.execute('SELECT count(*) FROM original_components').fetchone()[0],0)
    def test_audit_failure_rolls_back_receipt_and_file_retry_survives(self):
        s=self.start();u=s['resources'][0]['upload_id']
        with self.store._db() as db:db.execute("CREATE TRIGGER fail_original_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(RuntimeErrorResult):self.original.chunk(self.device,self.credential,u,0,self.data)
        with self.store._db() as db:self.assertEqual(db.execute('SELECT next_offset FROM original_uploads').fetchone()[0],0);db.execute('DROP TRIGGER fail_original_audit')
        self.original.chunk(self.device,self.credential,u,0,self.data);done=self.original.complete(self.device,self.credential,u);self.assertEqual(self.original.read(self.token,done['component_id'])['content'],self.data)
    def test_retention_backup_restore_quarantine_and_missing_file_failure(self):
        done=self.upload();backup=Path(self.tmp.name)/'original-backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored');fresh=restored.login('owner',PASSWORD,'new');svc=OriginalService(restored)
        with self.assertRaises(RuntimeErrorResult):svc.read(fresh['token'],done['component_id'])
        manifest=json.loads((backup/'manifest.json').read_text());self.assertTrue(manifest['media'])
        with restored._db() as db:self.assertEqual(db.execute('SELECT count(*) FROM original_components').fetchone()[0],1)
        with self.store._db() as db:key=db.execute('SELECT storage_key FROM original_components').fetchone()[0]
        media_path(self.store.root,key).rename(media_path(self.store.root,key).with_name('retained-moved'))
        with self.assertRaises((ValueError,OSError)):self.store.backup(Path(self.tmp.name)/'broken-backup')
    def test_capacity_csrf_and_device_revocation_do_not_weaken_existing_media(self):
        with self.assertRaises(RuntimeErrorResult):self.original.request(self.token,'bad',self.asset_id,'bad')
        r=self.request();self.original.media.budget=1
        with self.assertRaises(RuntimeErrorResult):self.start(r)
        self.original.media.budget=1024**3;self.start(r);self.pairing.revoke(self.token,self.csrf,self.device)
        with self.assertRaises(RuntimeErrorResult):self.original.pending(self.device,self.credential)
    def test_original_reservation_also_bounds_later_optimized_upload(self):
        self.start();self.media.budget=2*len(self.data)+len(self.jpeg)
        with self.assertRaises(RuntimeErrorResult):self.media.begin(self.device,self.credential,self.asset_id,'r1','still','image/jpeg',len(self.jpeg),hashlib.sha256(self.jpeg).hexdigest(),'optimized')

    def test_file_permissions_symlinks_and_safe_manifest_fields(self):
        done=self.upload();result=self.original.status(self.token,self.asset_id);self.assertNotIn('storage_key',str(result));self.assertNotIn('raw_json',str(result))
        with self.store._db() as db:key=db.execute('SELECT storage_key FROM original_components').fetchone()[0]
        p=media_path(self.store.root,key);self.assertEqual(p.stat().st_mode&0o777,0o600);saved=p.with_name('retained-original');p.rename(saved);p.symlink_to(saved)
        with self.assertRaises((ValueError,OSError,RuntimeErrorResult)):self.original.read(self.token,done['component_id'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OriginalTests));failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
