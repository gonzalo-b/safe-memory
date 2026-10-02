"""Browser/device transport separation over the actual ASGI application."""
import asyncio,json,secrets,sqlite3,tempfile,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore
from shell.app import MemoryApp
PASSWORD='synthetic-only-password'
class DeviceHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-device-http-')
        self.store=RuntimeStore(Path(self.tmp.name)/'store',fixture=True)
        self.store.create_owner('owner',PASSWORD,'Synthetic')
        self.app=MemoryApp(self.store,origin='http://127.0.0.1:8767',development=True)
        status,headers,body=self.request('/api/auth/login',{'username':'owner','password':PASSWORD})
        self.assertEqual(status,200);self.cookie=headers['set-cookie'].split(';')[0];self.csrf=body['csrf_token']
        self.credential=secrets.token_urlsafe(32)
    def tearDown(self):self.tmp.cleanup()
    def request(self,path,body=None,*,native=False,owner=False,method='POST',bearer=None,origin=None,csrf=None):
        headers=[(b'host',b'127.0.0.1:8767'),(b'content-type',b'application/json')]
        if not native or origin:headers.append((b'origin',(origin or self.app.origin).encode()))
        if owner:headers.extend([(b'cookie',self.cookie.encode()),(b'x-csrf-token',(self.csrf if csrf is None else csrf).encode())])
        if bearer:headers.append((b'authorization',('Bearer '+bearer).encode()))
        data=json.dumps(body or {}).encode();sent=[]
        async def receive():return {'type':'http.request','body':data,'more_body':False}
        async def send(message):sent.append(message)
        scope={'type':'http','method':method,'path':path,'query_string':b'','headers':headers,'client':('127.0.0.1',123)}
        asyncio.run(self.app(scope,receive,send))
        return sent[0]['status'],dict((k.decode(),v.decode()) for k,v in sent[0]['headers']),json.loads(sent[1]['body'])
    def claim(self):
        status,_,intent=self.request('/api/pairing/start',{},owner=True);self.assertEqual(status,200)
        status,_,claim=self.request('/api/device/claim',{'secret':intent['secret'],'device_name':'Fixture iPhone','library_id':'library-a','credential':self.credential},native=True)
        self.assertEqual(status,200);return claim
    def confirmed(self):
        claim=self.claim()
        result=self.request('/api/pairing/confirm',{'claim_id':claim['claim_id'],'fingerprint':claim['fingerprint']},owner=True)
        self.assertEqual(result[0],200);return claim['claim_id']
    def test_owner_starts_and_confirms_native_claim_without_implicit_data_access(self):
        claim=self.claim()
        self.assertEqual(self.request('/api/device/status',{'device_id':claim['claim_id']},native=True,bearer=self.credential)[0],401)
        pending=self.request('/api/pairing/pending',owner=True,method='GET')
        self.assertEqual(pending[2]['claims'][0]['claim_id'],claim['claim_id'])
        self.assertEqual(self.request('/api/pairing/confirm',{'claim_id':claim['claim_id'],'fingerprint':claim['fingerprint']},owner=True)[0],200)
        status,headers,binding=self.request('/api/device/status',{'device_id':claim['claim_id']},native=True,bearer=self.credential)
        self.assertEqual(status,200);self.assertFalse(binding['data_access']);self.assertEqual(headers['cache-control'],'no-store')
        self.assertEqual(self.request('/api/sources',owner=True,method='GET')[2]['sources'][0]['permission'],'restricted')
    def test_native_origin_exception_does_not_bypass_browser_csrf_or_session(self):
        self.assertEqual(self.request('/api/pairing/start',{},native=True,owner=True)[0],403)
        self.assertEqual(self.request('/api/pairing/start',{},owner=True,csrf='wrong')[0],403)
        device=self.confirmed()
        self.assertEqual(self.request('/api/device/status',{'device_id':device},native=True,bearer=self.credential,origin='https://evil.test')[0],403)
        self.assertEqual(self.request('/api/photos',native=True,method='GET',bearer=self.credential)[0],401)
        self.assertEqual(self.request('/api/device/status',{'device_id':device},native=True,owner=True)[0],401)
    def test_actual_metadata_batch_is_private_replayable_and_indexed_in_overview(self):
        device=self.confirmed()
        status,_,run=self.request('/api/device/ingest/begin',{'device_id':device,'request_key':'run','permission':'full','phase':'recent','selected_ids':['a']},native=True,bearer=self.credential)
        self.assertEqual(status,200)
        asset={'native_id':'a','source_revision':'one','media_type':'photo','hidden':False,'collection':'personal','capture_time':None,'time_basis':'unknown','owner_presence':'unknown','source_modified':None,'metadata':{'large_allowed_field':'x'*70000}}
        body={'device_id':device,'run_id':run['run_id'],'batch_key':'batch','sequence':0,'checkpoint':'one','assets':[asset]}
        first=self.request('/api/device/ingest/append',body,native=True,bearer=self.credential)
        self.assertEqual(first[0],200);self.assertEqual(first[2],self.request('/api/device/ingest/append',body,native=True,bearer=self.credential)[2])
        photos=self.request('/api/photos',owner=True,method='GET');self.assertEqual(len(photos[2]['assets']),1)
        self.assertNotIn('large_allowed_field',json.dumps(photos[2]))
        overview=self.request('/api/overview',owner=True,method='GET');self.assertEqual(overview[2]['counts']['assets'],1)
        self.assertEqual(overview[2]['counts']['media_ready'],0)
    def test_revocation_immediately_denies_native_access(self):
        device=self.confirmed()
        self.assertEqual(self.request('/api/devices/revoke',{'device_id':device},owner=True)[0],200)
        self.assertEqual(self.request('/api/device/status',{'device_id':device},native=True,bearer=self.credential)[0],401)
    def test_audit_failure_does_not_disclose_pairing_secret_or_create_intent(self):
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER fail BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        status,_,body=self.request('/api/pairing/start',{},owner=True)
        self.assertEqual(status,503);self.assertNotIn('secret',json.dumps(body))
        with sqlite3.connect(self.store.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM pairing_intents').fetchone()[0],0)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DeviceHTTPTests))
    failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
