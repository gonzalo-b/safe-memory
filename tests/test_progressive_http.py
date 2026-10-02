"""Actual ASGI scan transport identity, size and ownership boundaries."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_progressive import ProgressiveTests
from tests.test_media_http import MediaHTTPTests
from shell.app import MemoryApp

class ProgressiveHTTPTests(unittest.TestCase):
    setUpBase=ProgressiveTests.setUp;asset=ProgressiveTests.asset;tearDown=ProgressiveTests.tearDown
    request=MediaHTTPTests.request
    def setUp(self):
        self.setUpBase();self.app=MemoryApp(self.store,origin='http://127.0.0.1:8767',development=True)
    def native(self,path,data,bearer=True):
        return self.request('/api/device/scan/'+path,{'device_id':self.device,**data},method='POST',owner=False,bearer=self.credential if bearer else None)
    def descriptor(self,count=1):
        return {'request_key':'http','permission':'full','expected_count':count,'include_hidden':False,'include_shared_library':False,'include_shared_albums':False}
    def test_native_bounded_scan_and_private_owner_progress(self):
        self.assertEqual(self.native('begin',self.descriptor(),False)[0],401)
        status,_,body=self.native('begin',self.descriptor());self.assertEqual(status,200);r=json.loads(body)
        status,_,body=self.native('append',{'run_id':r['run_id'],'batch_key':'page','sequence':0,'checkpoint':'c','phase':'recent','assets':[self.asset()]})
        self.assertEqual(status,200);self.assertEqual(json.loads(body)['observed'],1)
        self.assertEqual(self.native('finish',{'run_id':r['run_id']})[0],200)
        self.assertEqual(self.request('/api/ingestion/progress',owner=False,bearer=self.credential)[0],401)
        status,headers,body=self.request('/api/ingestion/progress');self.assertEqual(status,200);self.assertEqual(headers['cache-control'],'no-store');self.assertEqual(len(json.loads(body)['scans']),1)
    def test_exact_fields_and_sample_finish_cannot_finish_scan(self):
        self.assertEqual(self.native('begin',{**self.descriptor(),'unapproved':True})[0],400)
        _,_,body=self.native('begin',self.descriptor(0));run=json.loads(body)['run_id']
        self.assertEqual(self.request('/api/device/ingest/finish',{'device_id':self.device,'run_id':run},method='POST',owner=False,bearer=self.credential)[0],400)
        self.assertEqual(self.request('/api/ingestion/retry',{'run_id':run},method='POST')[0],403)
    def test_batch_above_64k_uses_bounded_metadata_budget(self):
        _,_,body=self.native('begin',self.descriptor());run=json.loads(body)['run_id']
        row=self.asset(metadata={'syntheticPadding':'x'*100000})
        self.assertEqual(self.native('append',{'run_id':run,'batch_key':'large','sequence':0,'checkpoint':'c','phase':'recent','assets':[row]})[0],200)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProgressiveHTTPTests))
    failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
