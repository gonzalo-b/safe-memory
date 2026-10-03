"""Read-only Photos filters over synthetic current authorized metadata."""
import asyncio
import json
import sqlite3
import sys
import unittest
from pathlib import Path
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_ingestion import IngestionTests, PASSWORD
from runtime.knowledge import KnowledgeService
from runtime.store import RuntimeErrorResult
from shell.app import MemoryApp


class PhotosFilterTests(unittest.TestCase):
    setUp=IngestionTests.setUp
    tearDown=IngestionTests.tearDown
    asset=IngestionTests.asset
    begin=IngestionTests.begin
    append=IngestionTests.append

    def imported(self,*assets):
        run=self.begin(ids=[a['native_id'] for a in assets]);self.append(run,list(assets));return run

    def rows(self,**filters):return self.service.assets(self.auth['token'],**filters)['assets']
    def ids(self,**filters):return [row['native_id'] for row in self.rows(**filters)]
    def dated(self,native,day,**changes):return self.asset(native,capture_time=day+'T23:30:00-03:00',**changes)

    def trip(self,ids):
        knowledge=KnowledgeService(self.store)
        knowledge.rebuild(self.auth['token'],self.auth['csrf_token'],'build')
        by_native={r['native_id']:r['id'] for r in self.rows()}
        receipt=knowledge.correct_trip(self.auth['token'],self.auth['csrf_token'],'manual','manual',payload={
            'title':'Synthetic trip','start':'2026-10-01','end':'2026-10-03','evidence_ids':[by_native[i] for i in ids]})
        return knowledge,receipt['trip_ids'][0]

    def refused(self,status,**filters):
        with self.assertRaises(RuntimeErrorResult) as failure:self.rows(**filters)
        self.assertEqual(failure.exception.status,status)
        return failure.exception.code

    def request(self,query='',*,token=None):
        app=MemoryApp(self.store,origin='http://127.0.0.1:8767',development=True)
        headers=[(b'host',b'127.0.0.1:8767'),(b'cookie',('memory_dev='+str(token or self.auth['token'])).encode())]
        scope={'type':'http','method':'GET','path':'/api/photos','query_string':query.encode('ascii'),'headers':headers,'client':('127.0.0.1',123)}
        sent=[]
        async def receive():return {'type':'http.request','body':b'','more_body':False}
        async def send(message):sent.append(message)
        asyncio.run(app(scope,receive,send))
        return sent[0]['status'],dict(sent[0]['headers']),json.loads(sent[1]['body'])

    def test_inclusive_capture_local_range_precedes_pagination_and_excludes_unknown_days(self):
        self.imported(self.dated('before','2026-09-30'),self.dated('start','2026-10-01'),self.dated('end','2026-10-03',media_type='video'),self.dated('after','2026-10-04'),self.asset('instant',capture_time='2026-10-02T00:00:00Z',time_basis='instant_only'),self.asset('undated',capture_time=None,time_basis='unknown'))
        self.assertEqual(self.ids(from_day='2026-10-01',to_day='2026-10-03'),['end','start'])
        self.assertEqual(self.ids(from_day='2026-10-01',to_day='2026-10-03',limit=1,offset=1),['start'])
        self.assertEqual(self.ids(from_day='2026-10-03'),['after','end'])
        self.assertEqual(self.ids(to_day='2026-10-01'),['start','before'])
        self.assertEqual(self.ids(day='2026-10-03',media_type='video'),['end'])
        self.assertEqual(self.ids(from_day='2026-10-03',to_day='2026-10-03'),['end'])

    def test_place_matches_only_valid_explicit_fields_casefolded_literally_before_page(self):
        self.imported(self.dated('unmatched-newer','2026-10-05',metadata={'location':{'latitude':-23.55,'longitude':-46.63}}),
            self.dated('place','2026-10-04',metadata={'location':{'place':'São Paulo 100%_station'}}),
            self.dated('city','2026-10-03',metadata={'geography':{'city':'SÃO PAULO'}}),
            self.dated('bad','2026-10-02',metadata={'location':{'place':' São Paulo '},'geography':{'city':'São Paulo\n'},'private':'São Paulo'}),
            self.dated('country','2026-10-01',metadata={'geography':{'country_code':'BR','country':'Brasil','city_id':'sao-paulo'}}))
        self.assertEqual(self.ids(place='são paulo'),['place','city'])
        self.assertEqual(self.ids(place='SÃO PAULO',limit=1,offset=1),['city'])
        self.assertEqual(self.ids(place='%_'),['place'])
        self.assertEqual(self.ids(place='brasil'),['country'])
        self.assertEqual(self.ids(place='BR'),['country'])
        self.assertEqual(self.ids(place='sao-paulo'),['country'])
        self.assertEqual(self.ids(place="' OR 1=1 --"),[])

    def test_place_filter_uses_latest_raw_revision_without_requiring_rebuild(self):
        run=self.imported(self.asset(metadata={'location':{'place':'Old source place'}}))
        self.assertEqual(self.ids(place='old'),['asset-a'])
        self.append(run,[self.asset(revision='r2',metadata={'geography':{'city':'New source city'}})],key='new',sequence=1)
        self.assertEqual(self.ids(place='old'),[]);self.assertEqual(self.ids(place='new'),['asset-a'])
        self.assertIsNone(self.rows(place='new')[0]['evidence'])

    def test_collection_filters_never_bypass_current_shared_hidden_or_owner_policy(self):
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,True,True)
        collections=['personal','shared_library','shared_album','unknown']
        self.imported(*[self.asset(c,collection=c) for c in collections],self.asset('hidden',hidden=True))
        for c in collections:self.assertEqual(set(self.ids(collection=c)),{c,'hidden'} if c=='personal' else {c})
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,False,True,False)
        self.assertEqual(self.ids(collection='unknown'),[]);self.assertEqual(self.ids(collection='shared_album'),[])
        self.assertEqual(self.ids(collection='personal'),['personal']);self.assertEqual(self.ids(collection='shared_library'),['shared_library'])
        self.store.create_owner('other',PASSWORD,'Other');other=self.store.login('other',PASSWORD,'other')
        self.assertEqual(self.service.assets(other['token'],collection='shared_library')['assets'],[])

    def test_trip_membership_is_current_authorized_and_combines_filters_before_page(self):
        self.imported(self.dated('outside','2026-10-03',metadata={'location':{'place':'Target'}}),
            self.dated('a','2026-10-01',metadata={'location':{'place':'Target'}}),self.dated('b','2026-10-02',metadata={'location':{'place':'Target'}}))
        _,trip=self.trip(['a','b'])
        self.assertEqual(self.ids(trip_id=trip,place='target',collection='personal',from_day='2026-10-01',to_day='2026-10-03',limit=1,offset=1),['a'])
        self.assertEqual(self.ids(trip_id=trip,day='2026-10-02'),['b'])

    def test_trip_denies_all_members_if_any_member_is_stale_then_respects_rebuild_signature(self):
        run=self.imported(self.asset('a'),self.asset('b'))
        knowledge,trip=self.trip(['a','b'])
        # Equivalent source revision is unindexed until rebuilt; same normalized signature then permits it.
        self.append(run,[self.asset('b',revision='r2')],key='equivalent',sequence=1)
        self.assertEqual(self.refused(404,trip_id=trip,place='no match'),'not_found')
        knowledge.rebuild(self.auth['token'],self.auth['csrf_token'],'equivalent-rebuild')
        self.assertEqual(set(self.ids(trip_id=trip)),{'a','b'})
        self.append(run,[self.asset('b',revision='r3',metadata={'location':{'place':'Changed fact'}})],key='changed',sequence=2)
        knowledge.rebuild(self.auth['token'],self.auth['csrf_token'],'changed-rebuild')
        self.assertEqual(self.refused(404,trip_id=trip),'not_found')

    def test_trip_restriction_missing_owner_and_superseded_have_same_denial(self):
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,False,False)
        self.imported(self.asset('a'),self.asset('hidden',hidden=True))
        knowledge,trip=self.trip(['a','hidden'])
        self.assertEqual(self.refused(404,trip_id='0'*32),'not_found')
        self.store.create_owner('other',PASSWORD,'Other');other=self.store.login('other',PASSWORD,'other')
        with self.assertRaises(RuntimeErrorResult) as failure:self.service.assets(other['token'],trip_id=trip)
        self.assertEqual((failure.exception.status,failure.exception.code),(404,'not_found'))
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,False,False,False)
        self.assertEqual(self.refused(404,trip_id=trip,collection='personal'),'not_found')
        self.service.configure(self.auth['token'],self.auth['csrf_token'],self.connection,True,False,False)
        knowledge.correct_trip(self.auth['token'],self.auth['csrf_token'],'dismiss','dismiss',trip_id=trip,expected_revision=1)
        self.assertEqual(self.refused(404,trip_id=trip),'not_found')

    def test_invalid_filter_shapes_dates_ranges_and_identifiers_are_bounded(self):
        for filters in [{'from_day':'2026-02-30'},{'to_day':'2026-1-01'},{'from_day':True},{'day':'2026-10-01','from_day':'2026-10-01'},{'from_day':'2026-10-02','to_day':'2026-10-01'},{'place':''},{'place':' padded'},{'place':'x'*201},{'place':'control\n'},{'place':[]},{'trip_id':'A'*32},{'trip_id':'a'*31},{'trip_id':[]},{'collection':'shared'},{'collection':[]}]:
            with self.subTest(filters=filters):self.assertEqual(self.refused(400,**filters),'invalid_filter')

    def test_http_filters_are_accepted_and_reject_ambiguous_or_undecodable_query(self):
        self.imported(self.asset(metadata={'location':{'place':'São Paulo'}}))
        _,trip=self.trip(['asset-a'])
        query=urlencode({'limit':1,'offset':0,'media_type':'photo','from_day':'2026-10-01','to_day':'2026-10-01','place':'SÃO PAULO','trip_id':trip,'collection':'personal'})
        status,headers,body=self.request(query)
        self.assertEqual(status,200);self.assertEqual(headers[b'cache-control'],b'no-store')
        self.assertEqual([row['native_id'] for row in body['assets']],['asset-a']);self.assertEqual(set(body),{'assets','coverage','fixture'})
        for query in ['place=a&place=b','trip_id='+trip+'&trip_id='+trip,'place=%FF','unexpected=x','place=','day=2026-10-01&from_day=2026-10-01']:
            with self.subTest(query=query):self.assertEqual(self.request(query)[0],400)
        self.assertEqual(self.request('trip_id='+'0'*32)[0],404)
        self.assertEqual(self.request('place=Paulo',token='invalid')[0],401)

    def test_filter_disclosure_remains_audit_fail_closed(self):
        self.imported(self.asset(metadata={'location':{'place':'Private fixture'}}));_,trip=self.trip(['asset-a'])
        self.assertEqual(self.ids(place='Private',trip_id=trip),['asset-a'])
        with self.store._db() as db:
            audit=[dict(row) for row in db.execute('SELECT * FROM audit')]
        self.assertNotIn('Private',json.dumps(audit));self.assertNotIn(trip,json.dumps(audit))
        self.assertTrue(all(set(row)=={'sequence','id','owner_id','action','outcome','count','created_at'} for row in audit))
        with sqlite3.connect(self.store.path) as db:db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'full'); END")
        status,_,body=self.request(urlencode({'place':'Private','trip_id':trip}))
        self.assertEqual(status,503);self.assertNotIn('assets',body);self.assertNotIn('Private',json.dumps(body))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PhotosFilterTests))
    failed=len({getattr(case,'test_case',case).id() for case,_ in result.failures+result.errors})
    print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
