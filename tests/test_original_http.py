"""Exact-byte original transport and private attachment streaming."""
import asyncio,base64,json,sys,unittest
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_originals import OriginalTests
from shell.app import MemoryApp
from runtime.store import RuntimeErrorResult

class OriginalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.case=OriginalTests();self.case.setUp();self.app=MemoryApp(self.case.store,origin='http://127.0.0.1:8767',development=True)
    def tearDown(self):self.case.tearDown()
    def request(self,path,body=None,*,method='GET',owner=True,bearer=None,csrf=None,origin='http://127.0.0.1:8767',range_value=None,on_send=None):
        headers=[(b'host',b'127.0.0.1:8767'),(b'content-type',b'application/json')]
        if owner:headers.append((b'cookie',('memory_dev='+self.case.token).encode()))
        if bearer:headers.append((b'authorization',('Bearer '+bearer).encode()))
        if origin:headers.append((b'origin',origin.encode()))
        if csrf is None:csrf=self.case.csrf
        if csrf:headers.append((b'x-csrf-token',csrf.encode()))
        if range_value:headers.append((b'range',range_value.encode()))
        sent=[];url=urlsplit(path)
        async def receive():return {'type':'http.request','body':json.dumps(body or {}).encode(),'more_body':False}
        async def send(value):
            sent.append(value)
            if on_send:on_send(value)
        self.sent=sent
        asyncio.run(self.app({'type':'http','method':method,'path':url.path,'query_string':url.query.encode(),'headers':headers,'client':('127.0.0.1',1)},receive,send))
        return sent[0]['status'],dict((k.decode(),v.decode()) for k,v in sent[0]['headers']),b''.join(x.get('body',b'') for x in sent[1:])
    def native(self,action,**body):return self.request('/api/device/originals/'+action,dict(device_id=self.case.device,**body),method='POST',owner=False,bearer=self.case.credential,origin=None)
    def create(self):
        s,_,b=self.request('/api/photos/'+self.case.asset_id+'/originals',{'request_key':'http'},method='POST');self.assertEqual(s,200);return json.loads(b)
    def upload(self,data=None):
        data=self.case.data if data is None else data;r=self.create();s,_,b=self.native('begin',request_id=r['request_id'],resources=[self.case.manifest(data,filename='Viaje "日本".heic')]);self.assertEqual(s,200);u=json.loads(b)['resources'][0]['upload_id']
        for offset in range(0,len(data),4*1024*1024):self.assertEqual(self.native('chunk',upload_id=u,offset=offset,data=base64.b64encode(data[offset:offset+4*1024*1024]).decode())[0],200)
        s,_,b=self.native('complete',upload_id=u);self.assertEqual(s,200);return json.loads(b)
    def test_owner_wait_native_exact_upload_attachment_range_head(self):
        r=self.create();self.assertEqual(r['state'],'waiting_for_device');self.assertEqual(len(json.loads(self.native('pending')[2])['requests']),1)
        c=self.upload();path='/api/originals/components/'+c['component_id']
        s,h,b=self.request(path);self.assertEqual((s,b),(200,self.case.data));self.assertEqual(h['content-type'],'application/octet-stream');self.assertEqual(h['cache-control'],'no-store');self.assertTrue(h['content-disposition'].startswith("attachment; filename*=UTF-8''"));self.assertIn('%E6%97%A5%E6%9C%AC',h['content-disposition']);self.assertNotIn('"日本"',h['content-disposition'])
        s,h,b=self.request(path,range_value='bytes=2-8');self.assertEqual((s,b),(206,self.case.data[2:9]));self.assertEqual(h['content-range'],f'bytes 2-8/{len(self.case.data)}')
        self.assertEqual(self.request(path,method='HEAD')[2],b'');self.assertEqual(self.request(path,owner=False)[0],401);self.assertEqual(self.request(path,owner=False,bearer=self.case.credential)[0],401)
        self.assertEqual(self.request(path,range_value='bytes=0-1,3-4')[0],416)
    def test_origin_csrf_fields_query_bearer_and_canonical_base64(self):
        path='/api/photos/'+self.case.asset_id+'/originals'
        for kwargs in [{'csrf':'wrong'},{'origin':None},{'origin':'https://evil.test'}]:self.assertEqual(self.request(path,{'request_key':'x'},method='POST',**kwargs)[0],403)
        self.assertEqual(self.request(path+'?raw=true')[0],400)
        self.assertEqual(self.request(path,{'request_key':'x','owner_id':'other'},method='POST')[0],400)
        self.assertEqual(self.request('/api/device/originals/pending',{'device_id':self.case.device},method='POST',owner=True)[0],401)
        self.assertEqual(self.native('pending',raw=True)[0],400)
        r=self.create();s,_,b=self.native('begin',request_id=r['request_id'],resources=[self.case.manifest()]);self.assertEqual(s,200);u=json.loads(b)['resources'][0]['upload_id']
        for value in ['bad*base64','YR==','']:
            self.assertEqual(self.native('chunk',upload_id=u,offset=0,data=value)[0],400)
    def test_failure_retry_and_restricted_status_replay_download(self):
        r=self.create();self.assertEqual(self.native('fail',request_id=r['request_id'],reason='icloud_unavailable')[0],200)
        retry='/api/originals/'+r['request_id']+'/retry';self.assertEqual(self.request(retry,{'request_key':'retry'},method='POST')[0],200)
        c=self.upload();self.case.service.permission(self.case.device,self.case.credential,'revoked')
        self.assertEqual(self.request('/api/photos/'+self.case.asset_id+'/originals')[0],404)
        self.assertEqual(self.request('/api/originals/components/'+c['component_id'])[0],404)
        self.assertEqual(self.request(retry,{'request_key':'retry'},method='POST')[0],404)
    def test_revocation_at_response_headers_prevents_first_body(self):
        c=self.upload()
        def revoke(value):
            if value['type']=='http.response.start':self.case.service.permission(self.case.device,self.case.credential,'revoked')
        with self.assertRaises(RuntimeErrorResult):self.request('/api/originals/components/'+c['component_id'],on_send=revoke)
        self.assertFalse(any(x.get('body') for x in self.sent))
    def test_stream_rechecks_authority_after_first_chunk(self):
        data=b'x'*(4*1024*1024+8);c=self.upload(data)
        def revoke(value):
            if value['type']=='http.response.body' and value.get('body'):self.case.service.permission(self.case.device,self.case.credential,'revoked')
        with self.assertRaises(RuntimeErrorResult):self.request('/api/originals/components/'+c['component_id'],on_send=revoke)
        bodies=[x for x in self.sent if x['type']=='http.response.body'];self.assertEqual(len(bodies),1);self.assertTrue(bodies[0]['more_body']);self.assertEqual(len(bodies[0]['body']),4*1024*1024)

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OriginalHTTPTests));f=len(r.errors)+len(r.failures);print(f'{r.testsRun-f} passed, {f} failed');sys.exit(bool(f))
