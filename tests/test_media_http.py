"""Binary and upload API boundaries, including policy changes while streaming."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_media import MediaTests
from runtime.store import RuntimeErrorResult
from shell.app import MemoryApp

class MediaHTTPTests(unittest.TestCase):
    asset=MediaTests.asset;begin=MediaTests.begin;append=MediaTests.append;rows=MediaTests.rows
    start=MediaTests.start;upload=MediaTests.upload;tearDown=MediaTests.tearDown
    def setUp(self):
        MediaTests.setUp(self)
        self.app=MemoryApp(self.store,origin='http://127.0.0.1:8767',development=True)

    def request(self,path,body=None,*,method='GET',owner=True,bearer=None,range_value=None,on_send=None):
        headers=[(b'host',b'127.0.0.1:8767'),(b'content-type',b'application/json')]
        if owner:headers.append((b'cookie',('memory_dev='+self.auth['token']).encode()))
        if bearer:headers.append((b'authorization',('Bearer '+bearer).encode()))
        if range_value:headers.append((b'range',range_value.encode()))
        sent=[]
        async def receive():return {'type':'http.request','body':json.dumps(body or {}).encode(),'more_body':False}
        async def send(value):
            sent.append(value)
            if on_send:on_send(value)
        scope={'type':'http','method':method,'path':path,'query_string':b'','headers':headers,'client':('127.0.0.1',1)}
        self.sent=sent;asyncio.run(self.app(scope,receive,send))
        return sent[0]['status'],dict((k.decode(),v.decode()) for k,v in sent[0]['headers']),b''.join(v.get('body',b'') for v in sent[1:])

    def test_native_begin_chunk_complete_then_private_get_head_and_range(self):
        descriptor={'device_id':self.device,'asset_id':self.asset_id,'source_revision':'r1','role':'still','mime':'image/jpeg','size':len(self.jpeg),'sha256':hashlib.sha256(self.jpeg).hexdigest(),'request_key':'http'}
        status,_,body=self.request('/api/device/media/begin',descriptor,method='POST',owner=False,bearer=self.credential)
        self.assertEqual(status,200);upload=json.loads(body)['upload_id']
        status,_,_=self.request('/api/device/media/chunk',{'device_id':self.device,'upload_id':upload,'offset':0,'data_base64':base64.b64encode(self.jpeg).decode()},method='POST',owner=False,bearer=self.credential)
        self.assertEqual(status,200)
        status,_,body=self.request('/api/device/media/complete',{'device_id':self.device,'upload_id':upload},method='POST',owner=False,bearer=self.credential)
        self.assertEqual(status,200);path='/api/media/'+json.loads(body)['component_id']
        status,headers,body=self.request(path)
        self.assertEqual(status,200);self.assertEqual(body,self.jpeg);self.assertEqual(headers['content-type'],'image/jpeg')
        self.assertEqual(headers['cache-control'],'no-store');self.assertEqual(headers['x-content-type-options'],'nosniff')
        status,headers,body=self.request(path,range_value='bytes=3-9')
        self.assertEqual(status,206);self.assertEqual(body,self.jpeg[3:10]);self.assertEqual(headers['content-range'],f'bytes 3-9/{len(self.jpeg)}')
        status,headers,body=self.request(path,method='HEAD')
        self.assertEqual(status,200);self.assertEqual(body,b'');self.assertEqual(int(headers['content-length']),len(self.jpeg))
        self.assertEqual(self.request(path,owner=False)[0],401)
        self.assertEqual(self.request(path,owner=False,bearer=self.credential)[0],401)
        status,_,body=self.request(path,owner=False,method='HEAD')
        self.assertEqual(status,401);self.assertEqual(body,b'')

    def test_invalid_range_malformed_base64_and_component_hidden(self):
        c=self.upload();path='/api/media/'+c['component_id']
        for value in ('bytes=999999-','bytes=0-2,4-6','bytes=-0','bytes=5-1'):
            self.assertEqual(self.request(path,range_value=value)[0],416)
        status,_,_=self.request('/api/device/media/chunk',{'device_id':self.device,'upload_id':'x','offset':0,'data_base64':'not*base64'},method='POST',owner=False,bearer=self.credential)
        self.assertEqual(status,400)
        self.service.permission(self.device,self.credential,'revoked')
        self.assertEqual(self.request(path,range_value='bytes=0-2')[0],404)
        self.assertEqual(self.request('/api/photos/'+self.asset_id+'/media')[0],404)

    def test_revocation_after_headers_prevents_first_body(self):
        c=self.upload()
        def revoke(value):
            if value['type']=='http.response.start':self.service.permission(self.device,self.credential,'revoked')
        with self.assertRaises(RuntimeErrorResult):self.request('/api/media/'+c['component_id'],on_send=revoke)
        self.assertFalse(any(x.get('body') for x in self.sent))

    def test_policy_is_checked_again_before_later_stream_chunks(self):
        # Legal JPEG comment segments make a large fixture without a large decoded image.
        comment=b'\xff\xfe'+(65535).to_bytes(2,'big')+b'x'*65533
        data=self.jpeg[:2]+comment*65+self.jpeg[2:]
        upload=self.start(data);offset=0
        while offset<len(data):
            part=data[offset:offset+4*1024*1024]
            self.media.chunk(self.device,self.credential,upload['upload_id'],offset,part);offset+=len(part)
        c=self.media.complete(self.device,self.credential,upload['upload_id'])
        def revoke(value):
            if value['type']=='http.response.body' and value.get('body'):
                self.service.permission(self.device,self.credential,'revoked')
        with self.assertRaises(RuntimeErrorResult):self.request('/api/media/'+c['component_id'],on_send=revoke)
        bodies=[v for v in self.sent if v['type']=='http.response.body']
        self.assertEqual(len(bodies),1);self.assertTrue(bodies[0]['more_body']);self.assertLess(len(bodies[0]['body']),len(data))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MediaHTTPTests))
    failed=len(result.failures)+len(result.errors)
    print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
