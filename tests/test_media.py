"""Private component transfer and disclosure against synthetic JPEG/MP4 fixtures."""
import hashlib
import base64
import json
import subprocess
from pathlib import Path
import sqlite3
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_ingestion import IngestionTests, PASSWORD
from runtime.media import MediaService
from runtime.store import RuntimeStore, RuntimeErrorResult

class MediaTests(unittest.TestCase):
    asset=IngestionTests.asset
    begin=IngestionTests.begin
    append=IngestionTests.append
    rows=IngestionTests.rows
    tearDown=IngestionTests.tearDown

    def setUp(self):
        IngestionTests.setUp(self)
        self.media=MediaService(self.store)
        self.jpeg=(Path(__file__).parents[1]/'fixtures/media/synthetic.jpg').read_bytes()
        self.mp4=(Path(__file__).parents[1]/'fixtures/media/synthetic.mp4').read_bytes()
        self.run=self.begin()
        self.asset_id=self.append(self.run,[self.asset()])['assets'][0]['asset_id']

    def start(self,data=None,role='still',mime='image/jpeg',key='upload-a',revision='r1'):
        data=self.jpeg if data is None else data
        return self.media.begin(self.device,self.credential,self.asset_id,revision,role,mime,len(data),hashlib.sha256(data).hexdigest(),key)

    def upload(self,data=None,**options):
        data=self.jpeg if data is None else data
        value=self.start(data,**options)
        self.media.chunk(self.device,self.credential,value['upload_id'],0,data)
        return self.media.complete(self.device,self.credential,value['upload_id'])

    def test_checkpoint_replay_restart_and_audited_range(self):
        upload=self.start();half=len(self.jpeg)//2
        first=self.media.chunk(self.device,self.credential,upload['upload_id'],0,self.jpeg[:half])
        self.assertEqual(first,self.media.chunk(self.device,self.credential,upload['upload_id'],0,self.jpeg[:half]))
        self.media=MediaService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now))
        self.assertEqual(self.start()['next_offset'],half)
        self.media.chunk(self.device,self.credential,upload['upload_id'],half,self.jpeg[half:])
        component=self.media.complete(self.device,self.credential,upload['upload_id'])
        self.assertEqual(component,self.media.complete(self.device,self.credential,upload['upload_id']))
        read=self.media.read(self.auth['token'],component['component_id'],3,11)
        self.assertEqual(read['content'],self.jpeg[3:14]);self.assertEqual(read['size'],len(self.jpeg))
        self.assertEqual(self.media.library(self.auth['token'],self.asset_id)['state'],'ready')

    def test_hidden_and_owner_policy_apply_to_each_component_read(self):
        c=self.upload();self.store.create_owner('other',PASSWORD,'Other')
        other=self.store.login('other',PASSWORD,'other')
        with self.assertRaises(RuntimeErrorResult):self.media.read(other['token'],c['component_id'])
        self.append(self.run,[self.asset(revision='hidden',hidden=True)],key='hidden',sequence=1)
        with self.assertRaises(RuntimeErrorResult):self.media.read(self.auth['token'],c['component_id'])
        with self.assertRaises(RuntimeErrorResult):self.media.library(self.auth['token'],self.asset_id)

    def test_device_revocation_and_revision_change_interrupt_transfer(self):
        u=self.start();self.append(self.run,[self.asset(revision='r2',source_modified='2026-10-03T00:00:00Z')],key='r2',sequence=1)
        with self.assertRaises(RuntimeErrorResult):self.media.chunk(self.device,self.credential,u['upload_id'],0,self.jpeg)
        u=self.start(key='new',revision='r2')
        self.pairing.revoke(self.auth['token'],self.auth['csrf_token'],self.device)
        with self.assertRaises(RuntimeErrorResult):self.media.chunk(self.device,self.credential,u['upload_id'],0,self.jpeg)

    def test_batch_conflicts_bounds_and_digest_failure_never_publish(self):
        u=self.start();self.media.chunk(self.device,self.credential,u['upload_id'],0,b'x'*len(self.jpeg))
        with self.assertRaises(RuntimeErrorResult):self.media.chunk(self.device,self.credential,u['upload_id'],0,self.jpeg)
        with self.assertRaises(RuntimeErrorResult):self.media.complete(self.device,self.credential,u['upload_id'])
        self.assertEqual(self.media.library(self.auth['token'],self.asset_id)['state'],'not_transferred')
        with self.assertRaises(RuntimeErrorResult):self.start(role='video',mime='video/mp4')
        with self.assertRaises(RuntimeErrorResult):self.media.chunk(self.device,self.credential,u['upload_id'],len(self.jpeg),b'x')

    def test_format_gate_rejects_mislabeled_or_truncated_media(self):
        for index,content in enumerate((b'<script>bad</script>',self.jpeg[:5],b'\xff\xd8not-a-jpeg\xff\xd9')):
            u=self.start(content,key='bad-'+str(index))
            self.media.chunk(self.device,self.credential,u['upload_id'],0,content)
            with self.assertRaises(RuntimeErrorResult):self.media.complete(self.device,self.credential,u['upload_id'])
        self.assertEqual(self.media.library(self.auth['token'],self.asset_id)['components'],[])

    def test_live_requires_still_and_motion_and_video_bytes_are_retained(self):
        self.append(self.run,[self.asset(revision='live',media_type='live',source_modified='2026-10-03T00:00:00Z')],key='live',sequence=1)
        self.upload(revision='live');self.assertEqual(self.media.library(self.auth['token'],self.asset_id)['state'],'partial')
        c=self.upload(self.mp4,role='motion',mime='video/mp4',key='motion',revision='live')
        self.assertEqual(self.media.library(self.auth['token'],self.asset_id)['state'],'ready')
        self.assertEqual(self.media.read(self.auth['token'],c['component_id'])['content'],self.mp4)

    def test_audit_failure_does_not_publish_or_disclose(self):
        c=self.upload();u=self.start(key='another')
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        with self.assertRaises(RuntimeErrorResult):self.media.read(self.auth['token'],c['component_id'])
        with self.assertRaises(RuntimeErrorResult):self.media.chunk(self.device,self.credential,u['upload_id'],0,self.jpeg)

    def test_private_path_symlink_and_budget_fail_closed(self):
        self.media.budget=1
        with self.assertRaises(RuntimeErrorResult):self.start()
        self.media.budget=1024*1024
        u=self.start();path=self.store.root/'media'/u['upload_id']
        target=Path(self.tmp.name)/'external';target.mkdir()
        path.rmdir();path.symlink_to(target,target_is_directory=True)
        with self.assertRaises((RuntimeErrorResult,ValueError)):self.media.chunk(self.device,self.credential,u['upload_id'],0,self.jpeg)
        self.assertEqual(list(target.iterdir()),[])

    def test_backup_restore_retains_media_but_never_revives_access(self):
        c=self.upload();backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored')
        auth=restored.login('owner',PASSWORD,'restored')
        media=MediaService(restored)
        with self.assertRaises(RuntimeErrorResult):media.read(auth['token'],c['component_id'])
        with sqlite3.connect(restored.path) as db:
            key=db.execute('SELECT storage_key FROM media_components').fetchone()[0]
        self.assertEqual((restored.root/key).read_bytes(),self.jpeg)

    def test_authorized_session_resource_refusal_is_audited_before_returning_error(self):
        with self.assertRaises(RuntimeErrorResult):self.media.read(self.auth['token'],'missing')
        with sqlite3.connect(self.store.path) as db:
            row=db.execute("SELECT action,outcome FROM audit WHERE owner_id=? ORDER BY sequence DESC LIMIT 1",(self.owner,)).fetchone()
        self.assertEqual(row,('media_read','denied'))

    def test_same_size_corruption_and_missing_backup_component_fail_closed(self):
        c=self.upload()
        with sqlite3.connect(self.store.path) as db:key=db.execute('SELECT storage_key FROM media_components').fetchone()[0]
        path=self.store.root/key;path.write_bytes(b'x'*len(self.jpeg))
        with self.assertRaises(RuntimeErrorResult):self.media.read(self.auth['token'],c['component_id'])
        with self.assertRaises(ValueError):self.store.backup(Path(self.tmp.name)/'bad-backup')

    def test_current_component_readiness_is_reflected_in_photos_and_counts(self):
        self.upload()
        self.assertEqual(self.rows()[0]['media_state'],'ready')
        self.assertEqual(self.store.overview(self.auth['token'])['counts']['media_ready'],1)
        self.assertEqual(self.store.sources(self.auth['token'])['sources'][0]['media_ready_count'],1)
        self.append(self.run,[self.asset(revision='next',source_modified='2026-10-03T00:00:00Z')],key='next',sequence=1)
        self.assertEqual(self.rows()[0]['media_state'],'not_transferred')
        self.assertEqual(self.store.overview(self.auth['token'])['counts']['media_ready'],0)

    def test_partial_file_and_precommit_crashes_resume_without_duplicate_chunks(self):
        script='''
import base64,json,os,sys
import runtime.media as module
from runtime.store import RuntimeStore
x=json.load(sys.stdin);s=RuntimeStore(x['root'],fixture=True,clock=lambda:x['now'])
if x['partial']:
 original=module.os.fdopen
 class Partial:
  def __init__(self,stream):self.stream=stream
  def __enter__(self):return self
  def __exit__(self,*args):self.stream.close()
  def write(self,data):
   self.stream.write(data[:len(data)//2]);self.stream.flush();os._exit(77)
 module.os.fdopen=lambda fd,mode:Partial(original(fd,mode)) if mode=='wb' else original(fd,mode)
else:
 original=s._audit
 def crash(db,owner,action,outcome,count=0):
  if action=='media_chunk':os._exit(78)
  return original(db,owner,action,outcome,count)
 s._audit=crash
module.MediaService(s).chunk(x['device'],x['credential'],x['upload'],0,base64.b64decode(x['content']))
'''
        for partial in (True,False):
            u=self.start(key='crash-'+str(partial))
            value={'root':str(self.store.root),'now':self.now,'device':self.device,'credential':self.credential,'upload':u['upload_id'],'content':base64.b64encode(self.jpeg).decode(),'partial':partial}
            result=subprocess.run([sys.executable,'-c',script],input=json.dumps(value),text=True,capture_output=True,cwd=Path(__file__).parents[1])
            self.assertEqual(result.returncode,77 if partial else 78,result.stderr)
            self.assertEqual(self.start(key='crash-'+str(partial))['next_offset'],0)
            self.media.chunk(self.device,self.credential,u['upload_id'],0,self.jpeg)
            self.assertEqual(self.start(key='crash-'+str(partial))['next_offset'],len(self.jpeg))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MediaTests))
    failed=len(result.failures)+len(result.errors)
    print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
