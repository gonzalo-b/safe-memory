"""Actual ASGI boundary with synthetic owner stores, including negative requests."""
import asyncio
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore
from shell.app import MemoryApp

PASSWORD='synthetic correct horse battery'
class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-http-')
        self.store=RuntimeStore(Path(self.tmp.name)/'store',fixture=True)
        self.owner=self.store.create_owner('alice',PASSWORD,'Alice')
        self.app=MemoryApp(self.store,origin='http://127.0.0.1:8767',development=True)

    def tearDown(self):self.tmp.cleanup()

    def request(self,path,method='GET',body=None,headers=None,app=None,client='127.0.0.1'):
        data=json.dumps(body).encode() if body is not None else b''
        active=app or self.app
        items=[(b'host',urlsplit(active.origin).netloc.encode())]
        if method!='GET':items.extend([(b'origin',active.origin.encode()),(b'content-type',b'application/json')])
        items.extend((k.encode(),v.encode()) for k,v in (headers or []))
        sent=[]
        async def receive():return {'type':'http.request','body':data,'more_body':False}
        async def send(message):sent.append(message)
        scope={'type':'http','method':method,'path':path,'query_string':b'','headers':items,'client':(client,123),'scheme':'http'}
        asyncio.run((app or self.app)(scope,receive,send))
        start=next(m for m in sent if m['type']=='http.response.start')
        raw=b''.join(m.get('body',b'') for m in sent if m['type']=='http.response.body')
        return start['status'],dict((k.decode(),v.decode()) for k,v in start['headers']),json.loads(raw)

    def login(self):
        status,headers,body=self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD})
        self.assertEqual(status,200)
        return headers['set-cookie'].split(';')[0],body['csrf_token']

    def test_no_session_denied_and_public_health_has_no_owner_information(self):
        self.assertEqual(self.request('/api/overview')[0],401)
        self.assertEqual(self.request('/api/debug')[0],401)
        self.assertEqual(self.request('/api/health')[2],{'status':'ok'})

    def test_login_cookie_and_no_store_headers(self):
        status,headers,body=self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD})
        self.assertEqual(status,200)
        self.assertIn('HttpOnly',headers['set-cookie']);self.assertIn('SameSite=Strict',headers['set-cookie'])
        self.assertEqual(headers['cache-control'],'no-store')
        self.assertNotIn('token',body)

    def test_authenticated_read_and_logout_csrf(self):
        cookie,csrf=self.login()
        self.assertEqual(self.request('/api/overview',headers=[('cookie',cookie)])[0],200)
        self.assertEqual(self.request('/api/auth/logout','POST',{},[('cookie',cookie)])[0],403)
        self.assertEqual(self.request('/api/auth/logout','POST',{},[('cookie',cookie),('x-csrf-token',csrf)])[0],200)
        self.assertEqual(self.request('/api/session',headers=[('cookie',cookie)])[0],401)

    def test_spoofed_owner_header_cannot_select_other_owner(self):
        other=self.store.create_owner('bob',PASSWORD,'Bob')
        self.store.connect_source(other,'library-b','B private')
        cookie,_=self.login()
        response=self.request('/api/overview',headers=[('cookie',cookie),('x-owner-id',other)])[2]
        self.assertEqual(response['sources'],[])
        self.assertNotIn('B private',json.dumps(response))

    def test_origin_and_host_duplicate_rejected(self):
        self.assertEqual(self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD},[('origin','https://evil.test')])[0],400)
        self.assertEqual(self.request('/api/session',headers=[('host','evil.test')])[0],400)
        self.assertEqual(self.request('/api/session',headers=[('origin','https://evil.test')])[0],403)

    def test_unknown_and_future_routes_require_auth(self):
        self.assertEqual(self.request('/api/photos')[0],401)
        cookie,_=self.login()
        self.assertEqual(self.request('/api/photos',headers=[('cookie',cookie)])[0],501)
        self.assertEqual(self.request('/api/not-a-route',headers=[('cookie',cookie)])[0],404)

    def test_public_deployment_requires_https_and_secure_cookie(self):
        with self.assertRaises(ValueError):MemoryApp(self.store,origin='http://memory.example.test',development=False)
        with self.assertRaises(ValueError):MemoryApp(self.store,origin='http://memory.example.test',development=True)
        secure=MemoryApp(self.store,origin='https://memory.example.test')
        self.assertTrue(secure.secure)
        self.assertTrue(secure.cookie_name.startswith('__Host-'))
        status,headers,_=self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD},app=secure)
        self.assertEqual(status,200)
        self.assertIn('; Secure',headers['set-cookie'])
        self.assertIn('__Host-memory=',headers['set-cookie'])
        self.assertIn('strict-transport-security',headers)

    def test_input_size_and_extra_identity_fields_rejected(self):
        self.assertEqual(self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD,'owner_id':self.owner})[0],400)
        self.assertEqual(self.request('/api/auth/login','POST',{'username':'alice','password':'x'*70000})[0],413)

    def test_audit_failure_has_no_sensitive_details(self):
        cookie,_=self.login()
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER fail BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'secret path'); END")
        status,_,body=self.request('/api/overview',headers=[('cookie',cookie)])
        self.assertEqual(status,503)
        self.assertNotIn('secret path',json.dumps(body));self.assertNotIn(str(self.store.root),json.dumps(body))

    def test_edge_clients_have_independent_login_limits(self):
        app=MemoryApp(self.store,origin='https://memory.example.test',trusted_edge='cloudflare')
        for i in range(20):
            self.assertEqual(self.request('/api/auth/login','POST',{'username':f'absent{i}','password':'wrong'},[('cf-connecting-ip','192.0.2.1')],app=app)[0],401)
        self.assertEqual(self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD},[('cf-connecting-ip','192.0.2.1')],app=app)[0],429)
        self.assertEqual(self.request('/api/auth/login','POST',{'username':'alice','password':PASSWORD},[('cf-connecting-ip','192.0.2.2')],app=app)[0],200)

    def test_edge_identity_requires_explicit_trust_and_loopback_peer(self):
        app=MemoryApp(self.store,origin='https://memory.example.test',trusted_edge='cloudflare')
        data={'username':'alice','password':PASSWORD}
        for headers,client in [([], '127.0.0.1'),([('x-forwarded-for','192.0.2.1')],'127.0.0.1'),([('cf-connecting-ip','invalid')],'127.0.0.1'),([('cf-connecting-ip','192.0.2.1')],'192.0.2.2')]:
            with patch.object(self.store,'login') as login:
                self.assertEqual(self.request('/api/auth/login','POST',data,headers,app=app,client=client)[0],403)
                login.assert_not_called()
        with patch.object(self.store,'login',return_value={'token':'test'}) as login:
            self.request('/api/auth/login','POST',data,[('cf-connecting-ip','192.0.2.1'),('x-forwarded-for','192.0.2.2')])
            self.assertEqual(login.call_args.args[2],'127.0.0.1')

    def test_total_body_deadline_bounds_stall_and_drip_without_auth(self):
        async def scenario(drip):
            app=MemoryApp(self.store,origin=self.app.origin,development=True)
            app.body_timeout=0.025
            sent=[]
            async def receive():
                await asyncio.sleep(0.01 if drip else 2)
                return {'type':'http.request','body':b' ', 'more_body':True}
            async def send(message):sent.append(message)
            scope={'type':'http','method':'POST','path':'/api/auth/login','headers':[(b'host',b'127.0.0.1:8767'),(b'origin',self.app.origin.encode())]}
            with patch.object(self.store,'login') as login:
                await asyncio.wait_for(app(scope,receive,send),0.2)
                login.assert_not_called()
            self.assertEqual(sent[0]['status'],408)
        for drip in (False,True):asyncio.run(scenario(drip))
        self.assertEqual(self.request('/api/health')[0],200)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HTTPTests))
    failed=len(result.failures)+len(result.errors)
    print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
