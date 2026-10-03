"""Gallery owner routes exercise the actual private runtime, not HTTP mocks."""
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_artifacts import ArtifactTests
from test_knowledge_http import KnowledgeHTTPTests
from shell.app import MemoryApp

class ArtifactHTTPTests(unittest.TestCase):
    request=KnowledgeHTTPTests.request
    def setUp(self):
        self.case=ArtifactTests();self.case.setUp();self.app=MemoryApp(self.case.store,origin='http://127.0.0.1:8767',development=True)
    def tearDown(self):self.case.tearDown()
    def create(self):
        response=self.request('/api/artifacts',{'request_key':'create','title':'Private <script>text</script>','asset_ids':list(self.case.ids.values())},method='POST')
        self.assertEqual(response[0],200);return response[2]
    def test_create_edit_reopen_debug_and_exclusion_preserving_recompose(self):
        receipt=self.create();path='/api/artifacts/'+receipt['artifact_id'];a=self.case.ids['a']
        self.assertEqual(self.request('/api/artifacts')[2]['artifacts'][0]['id'],receipt['artifact_id'])
        edit={'request_key':'remove','expected_revision':1,'patch':{'remove_ids':[a],'title':'Edited'}}
        self.assertEqual(self.request(path+'/edit',edit,method='POST')[2]['revision'],2)
        self.assertEqual(self.request(path+'/edit',edit,method='POST')[2]['revision'],2)
        self.assertEqual(self.request(path+'/recompose',{'request_key':'rerun','expected_revision':2,'asset_ids':[a]},method='POST')[2]['revision'],3)
        self.app=MemoryApp(self.case.store,origin='http://127.0.0.1:8767',development=True)
        status,headers,saved=self.request(path);self.assertEqual(status,200);self.assertEqual(headers['cache-control'],'no-store')
        self.assertEqual(saved['title'],'Edited');self.assertEqual(saved['excluded_ids'],[a]);self.assertEqual(len(saved['members']),2)
        self.assertEqual(self.request(path+'/debug')[0],200)
    def test_identity_origin_csrf_strict_fields_and_methods(self):
        self.assertEqual(self.request('/api/artifacts',token='')[0],401)
        body={'request_key':'create','title':'Gallery','asset_ids':[]}
        for kwargs in [{'csrf':'wrong'},{'origin':'https://evil.test'},{'origin':None}]:
            self.assertEqual(self.request('/api/artifacts',body,method='POST',**kwargs)[0],403)
        self.assertEqual(self.request('/api/artifacts',dict(body,owner_id='other'),method='POST')[0],400)
        for path in ['/api/artifacts?limit=1&limit=2','/api/artifacts?owner_id=other','/api/artifacts?limit=0']:
            self.assertEqual(self.request(path)[0],400)
        r=self.create();path='/api/artifacts/'+r['artifact_id']
        self.assertEqual(self.request(path,{},method='POST')[0],405)
        self.assertEqual(self.request(path+'?limit=1')[0],400)
        self.assertEqual(self.request(path+'/edit')[0],405)
    def test_concurrent_edit_audit_and_current_source_refusal(self):
        r=self.create();path='/api/artifacts/'+r['artifact_id'];body={'request_key':'edit','expected_revision':1,'patch':{'title':'New'}}
        self.assertEqual(self.request(path+'/edit',body,method='POST')[0],200)
        self.assertEqual(self.request(path+'/edit',dict(body,request_key='stale'),method='POST')[0],409)
        self.case.ingest.permission(self.case.device,self.case.credential,'revoked')
        self.assertEqual(self.request('/api/artifacts')[2]['artifacts'],[])
        for endpoint in [path,path+'/debug']:
            denied=self.request(endpoint);self.assertEqual(denied[0],404);self.assertNotIn('New',str(denied[2]))
        self.assertEqual(self.request(path+'/edit',body,method='POST')[0],404)
        with self.case.store._db() as db:db.execute("CREATE TRIGGER no_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'disk'); END")
        self.assertEqual(self.request('/api/artifacts')[0],503)
    def test_other_owner_and_paged_list_have_no_cross_owner_output(self):
        r=self.create();self.case.store.create_owner('other','synthetic-artifact-password','Other');other=self.case.store.login('other','synthetic-artifact-password','other')
        self.assertEqual(self.request('/api/artifacts',token=other['token'])[2]['artifacts'],[])
        self.assertEqual(self.request('/api/artifacts/'+r['artifact_id'],token=other['token'])[0],404)
        self.case.service.create(self.case.token,self.case.csrf,'second',title='Second',asset_ids=[])
        first=self.request('/api/artifacts?limit=1')[2];self.assertEqual(len(first['artifacts']),1);self.assertTrue(first['next_cursor'])
        second=self.request('/api/artifacts?limit=1&cursor='+first['next_cursor'])[2];self.assertEqual(len(second['artifacts']),1);self.assertNotEqual(first['artifacts'][0]['id'],second['artifacts'][0]['id'])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactHTTPTests));failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');sys.exit(bool(failed))
