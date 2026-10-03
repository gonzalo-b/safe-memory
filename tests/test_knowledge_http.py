"""Owner knowledge transport over real ASGI/runtime, with synthetic evidence."""
from pathlib import Path
import asyncio,json,sys,unittest
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_knowledge import KnowledgeTests
from shell.app import MemoryApp

class KnowledgeHTTPTests(unittest.TestCase):
    def setUp(self):
        self.case=KnowledgeTests();self.case.setUp()
        self.case.import_rows(self.case.asset('a'),self.case.asset('b',capture_time='2024-03-01T12:00:00+09:00'))
        self.app=MemoryApp(self.case.store,origin='http://127.0.0.1:8767',development=True)
    def tearDown(self):self.case.tearDown()
    def request(self,path,body=None,*,method='GET',token=None,csrf=None,origin='http://127.0.0.1:8767'):
        headers=[(b'host',b'127.0.0.1:8767'),(b'content-type',b'application/json')]
        if token is None:token=self.case.token
        headers.append((b'cookie',('memory_dev='+token).encode()))
        if origin:headers.append((b'origin',origin.encode()))
        if csrf is None:csrf=self.case.csrf
        if csrf:headers.append((b'x-csrf-token',csrf.encode()))
        sent=[];url=urlsplit(path)
        async def receive():return {'type':'http.request','body':json.dumps(body or {}).encode(),'more_body':False}
        async def send(message):sent.append(message)
        asyncio.run(self.app({'type':'http','method':method,'path':url.path,'query_string':url.query.encode(),'headers':headers,'client':('127.0.0.1',1)},receive,send))
        return sent[0]['status'],dict((k.decode(),v.decode()) for k,v in sent[0]['headers']),json.loads(sent[1]['body'])
    def rebuild(self):
        result=self.request('/api/knowledge/rebuild',{'request_key':'build'},method='POST');self.assertEqual(result[0],200);return result[2]
    def test_rebuild_catalog_answer_and_paged_current_evidence(self):
        self.rebuild();catalog=self.request('/api/knowledge/catalog');self.assertEqual(catalog[0],200);self.assertIn('photos.statistics',catalog[2]['capabilities'])
        body={'capability':'photos.records','limit':1}
        page=self.request('/api/knowledge/answer',body,method='POST');self.assertEqual(page[0],200);self.assertEqual(page[1]['cache-control'],'no-store')
        row=page[2]['data'][0];self.assertEqual(self.request('/api/knowledge/evidence/'+row['evidence']['asset_id'])[0],200)
        nextpage=self.request('/api/knowledge/answer',dict(body,cursor=page[2]['next_cursor']),method='POST');self.assertEqual(len(nextpage[2]['data']),1)
        scoped=self.request('/api/knowledge/answer',{'capability':'photos.records','scope':{'fields':['media_type']}},method='POST')
        self.assertNotIn('evidence',scoped[2]['data'][0])
    def test_owner_origin_and_mutation_csrf_are_required_but_answer_is_read_only(self):
        self.assertEqual(self.request('/api/knowledge/catalog',token='')[0],401)
        self.assertEqual(self.request('/api/knowledge/rebuild',{'request_key':'x'},method='POST',csrf='wrong')[0],403)
        self.assertEqual(self.request('/api/knowledge/rebuild',{'request_key':'x'},method='POST',origin='https://evil.test')[0],403)
        self.rebuild()
        # Read-only answer checks Origin/session/audit, not the mutation CSRF token.
        self.assertEqual(self.request('/api/knowledge/answer',{'capability':'photos.statistics'},method='POST',csrf='')[0],200)
        self.assertEqual(self.request('/api/knowledge/answer',{'capability':'photos.statistics'},method='POST',origin=None)[0],403)
    def test_exact_payload_and_query_allowlists_prevent_identity_or_method_substitution(self):
        self.assertEqual(self.request('/api/knowledge/rebuild',{'request_key':'x','owner_id':'other'},method='POST')[0],400)
        self.assertEqual(self.request('/api/knowledge/answer',{'capability':'photos.statistics','raw':True},method='POST')[0],400)
        for path in ['/api/knowledge/trips?limit=2&limit=3','/api/knowledge/areas?owner_id=other','/api/knowledge/catalog?limit=1']:
            self.assertEqual(self.request(path)[0],400)
        self.assertEqual(self.request('/api/knowledge/rebuild')[0],405)
    def test_trip_and_area_mutations_persist_and_recheck_policy(self):
        self.rebuild();trip=self.request('/api/knowledge/trips?limit=1')[2]['data'][0];identity=trip['trip_id']
        body={'request_key':'rename','action':'rename','trip_id':identity,'expected_revision':trip['revision'],'payload':{'title':'Synthetic journey'}}
        self.assertEqual(self.request('/api/knowledge/trips/correct',body,method='POST',csrf='wrong')[0],403)
        self.assertEqual(self.request('/api/knowledge/trips/correct',body,method='POST')[0],200)
        self.assertEqual(self.request('/api/knowledge/trips/'+identity)[2]['title'],'Synthetic journey')
        area={'label':'Past area','lat':35,'lon':139,'radius_km':10,'start':'2020-01-01','end':'2021-01-01','confirmed':True}
        self.assertEqual(self.request('/api/knowledge/areas',{'request_key':'area','area':area},method='POST')[0],200)
        self.assertEqual(self.request('/api/knowledge/areas')[2]['data'][0]['label'],'Past area')
        self.case.ingest.permission(self.case.device,self.case.credential,'revoked')
        self.assertEqual(self.request('/api/knowledge/trips/'+identity)[0],404)
        self.assertEqual(self.request('/api/knowledge/trips')[2]['data'],[])
        self.assertEqual(self.request('/api/knowledge/trips/correct',body,method='POST')[2]['trip_ids'],[])
    def test_audit_failure_and_other_owner_never_disclose_cached_facts(self):
        self.rebuild();trip=self.request('/api/knowledge/trips')[2]['data'][0]
        self.case.store.create_owner('other','synthetic-knowledge-password','Other');other=self.case.store.login('other','synthetic-knowledge-password','other')['token']
        self.assertEqual(self.request('/api/knowledge/trips/'+trip['trip_id'],token=other)[0],404)
        with self.case.store._db() as db:db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'disk'); END")
        status,_,body=self.request('/api/knowledge/answer',{'capability':'photos.records'},method='POST')
        self.assertEqual(status,503);self.assertNotIn('capture_time',json.dumps(body))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(KnowledgeHTTPTests));failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');sys.exit(bool(failed))
