"""Persistent deterministic knowledge; synthetic data and current-policy boundaries."""
from pathlib import Path
import json, sqlite3, sys, tempfile, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore, RuntimeErrorResult
from runtime.knowledge import KnowledgeService
from runtime.ingestion import IngestionService
from runtime.pairing import PairingService
import secrets

class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-knowledge-');self.now=1800000000
        self.store=RuntimeStore(Path(self.tmp.name)/'store',fixture=True,clock=lambda:self.now)
        self.owner=self.store.create_owner('owner','synthetic-knowledge-password','Synthetic owner')
        self.auth=self.store.login('owner','synthetic-knowledge-password','local');self.token=self.auth['token'];self.csrf=self.auth['csrf_token']
        pair=PairingService(self.store);intent=pair.start(self.token,self.csrf);self.credential=secrets.token_urlsafe(32)
        claim=pair.claim(intent['secret'],'Synthetic phone','library',self.credential);binding=pair.confirm(self.token,self.csrf,claim['claim_id'],claim['fingerprint'])
        self.device=binding['device_id'];self.connection=binding['connection_id'];self.ingest=IngestionService(self.store);self.service=KnowledgeService(self.store);self.run_count=0
    def tearDown(self):self.tmp.cleanup()
    def asset(self,native='a',**changes):
        row=dict(native_id=native,source_revision='r1',media_type='photo',hidden=False,collection='personal',capture_time='2024-02-29T23:30:00-03:00',time_basis='capture_offset',owner_presence='unknown',source_modified='2026-10-02T00:00:00Z',metadata={'location':{'latitude':35.0,'longitude':139.0},'geography':{'country_code':'JP','country':'Japan','city_id':'tokyo','city':'Tokyo'}});row.update(changes);return row
    def import_rows(self,*rows):
        self.run_count+=1;r=self.ingest.begin(self.device,self.credential,str(self.run_count),'full','recent',[x['native_id'] for x in rows]);self.ingest.append(self.device,self.credential,r['run_id'],'batch',0,'checkpoint',list(rows));self.ingest.finish(self.device,self.credential,r['run_id']);return self.ingest.assets(self.token)['assets']
    def rebuild(self,key='build'):return self.service.rebuild(self.token,self.csrf,key)
    def answer(self,cap,params=None,**kwargs):return self.service.answer(self.token,cap,params,**kwargs)
    def test_generation_indexes_explicit_geography_preserves_offset_and_unknown_native_day(self):
        self.import_rows(self.asset(),self.asset('b',capture_time='2024-03-01T02:30:00Z',time_basis='instant_only'))
        generation=self.rebuild();result=self.answer('travel.where_on_date',{'date':'2024-02-29'})
        self.assertEqual(result['generation'],generation['generation']);self.assertEqual(len(result['data']),1)
        self.assertEqual(result['data'][0]['capture_time'],'2024-02-29T23:30:00-03:00')
        self.assertEqual(result['coverage']['unknown_time_records'],1)
        self.assertEqual(self.answer('travel.countries_visited')['data'][0]['country_code'],'JP')
        self.assertEqual(self.answer('photos.statistics')['data']['records'],2)
    def test_current_policy_revision_and_field_projection_precede_matching_and_counts(self):
        rows=self.import_rows(self.asset());self.rebuild();asset_id=rows[0]['id']
        scope={'fields':['id','media_type']}
        self.assertEqual(self.answer('travel.where_on_date',{'date':'2024-02-29'},scope=scope)['data'],[])
        self.assertEqual(self.answer('travel.countries_visited',scope=scope)['data'],[])
        self.ingest.configure(self.token,self.csrf,self.connection,True,False,False)
        self.import_rows(self.asset(source_revision='r2',hidden=True,source_modified='2026-10-03T00:00:00Z'))
        self.assertEqual(self.answer('photos.statistics')['data']['records'],0)
        self.assertEqual(self.answer('photos.statistics')['coverage']['unindexed_current_records'],1)
        self.rebuild('new');self.ingest.configure(self.token,self.csrf,self.connection,False,False,False)
        self.assertEqual(self.answer('photos.statistics')['status'],'no_evidence')
        with self.assertRaises(RuntimeErrorResult):self.service.evidence(self.token,asset_id)
    def test_occasion_exact_leap_days_keep_unknown_occurrences(self):
        self.import_rows(self.asset());self.rebuild()
        answer=self.answer('travel.occasion_history',{'month_day':'02-29','count':3,'as_of':'2026-10-02'})
        self.assertEqual([x['date'] for x in answer['data']],['2024-02-29','2020-02-29','2016-02-29'])
        self.assertEqual([x['status'] for x in answer['data']],['observed','unknown','unknown'])
        self.assertEqual(self.answer('travel.occasion_history',{'count':2,'as_of':'2026-10-02'})['status'],'needs_input')
    def test_failed_rebuild_preserves_generation_and_audit_failure_rolls_back(self):
        self.import_rows(self.asset());first=self.rebuild()
        with self.store._db() as db:db.execute("CREATE TRIGGER fail_fact BEFORE INSERT ON knowledge_facts BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(sqlite3.Error):self.rebuild('fail')
        self.assertEqual(self.answer('photos.statistics')['generation'],first['generation'])
        with self.store._db() as db:db.execute('DROP TRIGGER fail_fact');db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(RuntimeErrorResult):self.rebuild('audit-fail')
        with self.store._db() as db:self.assertEqual(db.execute('SELECT count(*) FROM knowledge_generations').fetchone()[0],1)

    def test_trip_corrections_identity_and_lineage_survive_rebuild_and_equivalent_reimport(self):
        rows=self.import_rows(self.asset('a'),self.asset('b',capture_time='2024-03-01T12:00:00+09:00'))
        self.rebuild();trip=self.service.trips(self.token)['data'][0]
        corrected=self.service.correct_trip(self.token,self.csrf,'rename','rename',trip_id=trip['trip_id'],expected_revision=trip['revision'],payload={'title':'Owner trip'})
        trip_id=corrected['trip_ids'][0];self.assertEqual(trip_id,trip['trip_id'])
        self.rebuild('again');self.assertEqual(self.service.trip(self.token,trip_id)['title'],'Owner trip')
        self.import_rows(self.asset('a',source_revision='r2'),self.asset('b',source_revision='r2',capture_time='2024-03-01T12:00:00+09:00'));self.rebuild('reimport')
        latest=self.service.trip(self.token,trip_id);self.assertEqual(latest['title'],'Owner trip')
        split=self.service.correct_trip(self.token,self.csrf,'split','split',trip_id=trip_id,expected_revision=latest['revision'],payload={'date':'2024-03-01'})
        self.assertEqual(len(split['trip_ids']),2)
        children=[self.service.trip(self.token,x) for x in split['trip_ids']]
        merged=self.service.correct_trip(self.token,self.csrf,'merge','merge',payload={'trip_ids':split['trip_ids'],'expected_revisions':{x['trip_id']:x['revision'] for x in children},'title':'Rejoined'})
        self.assertNotEqual(merged['trip_ids'][0],trip_id);self.assertEqual(self.service.trip(self.token,merged['trip_ids'][0])['title'],'Rejoined')
        self.rebuild('post-merge');self.assertEqual(len(self.service.trips(self.token)['data']),1)
    def test_restriction_never_leaks_corrected_title_boundaries_or_cached_receipt(self):
        self.import_rows(self.asset());self.rebuild();trip=self.service.trips(self.token)['data'][0]
        reply=self.service.correct_trip(self.token,self.csrf,'name','rename',trip_id=trip['trip_id'],expected_revision=trip['revision'],payload={'title':'Private Tokyo title'})
        self.ingest.permission(self.device,self.credential,'revoked')
        self.assertEqual(self.service.trips(self.token)['data'],[])
        with self.assertRaises(RuntimeErrorResult):self.service.trip(self.token,trip['trip_id'])
        replay=self.service.correct_trip(self.token,self.csrf,'name','rename',trip_id=trip['trip_id'],expected_revision=trip['revision'],payload={'title':'Private Tokyo title'})
        self.assertEqual(replay['trip_ids'],[]);self.assertNotIn('Tokyo',str(replay))
    def test_confirmed_historical_areas_exclude_commuting_but_not_older_residence(self):
        self.import_rows(self.asset('old',capture_time='2020-02-29T12:00:00+09:00'),self.asset('current',capture_time='2024-02-29T12:00:00+09:00'),self.asset('third',owner_presence='third_party'))
        self.service.put_habitual_area(self.token,self.csrf,'home',{'label':'Area','lat':35,'lon':139,'radius_km':10,'start':'2023-01-01','end':'2025-01-01','confirmed':True})
        self.rebuild();trips=self.service.trips(self.token)['data'];self.assertEqual(len(trips),1);self.assertEqual(trips[0]['observed_start'],'2020-02-29')
        self.assertFalse(trips[0]['owner_presence_confirmed']);self.assertFalse(trips[0]['continuous_presence'])
    def test_scope_pages_and_cursors_cannot_cross_policy_or_owner(self):
        self.import_rows(self.asset('a'),self.asset('b'));self.rebuild()
        page=self.answer('photos.records',limit=1);self.assertTrue(page['next_cursor'])
        with self.assertRaises(RuntimeErrorResult):self.answer('photos.records',scope={'fields':['media_type']},limit=1,cursor=page['next_cursor'])
        self.ingest.configure(self.token,self.csrf,self.connection,False,True,False)
        with self.assertRaises(RuntimeErrorResult):self.answer('photos.records',limit=1,cursor=page['next_cursor'])
        self.store.create_owner('other','synthetic-knowledge-password','Other');other=self.store.login('other','synthetic-knowledge-password','other')['token']
        self.assertEqual(self.service.answer(other,'photos.statistics')['status'],'no_evidence')
        with self.assertRaises(RuntimeErrorResult):self.service.evidence(other,page['data'][0]['evidence']['asset_id'])

    def test_native_instant_and_missing_geography_do_not_invent_local_day_country_or_people(self):
        self.import_rows(self.asset(metadata={'location':{'latitude':0,'longitude':0,'place':'Tokyo, Japan'},'unavailable':{'people':'not_exposed'}},time_basis='instant_only',capture_time='2024-02-29T12:00:00Z'))
        self.rebuild();self.assertEqual(self.answer('travel.countries_visited')['data'],[])
        self.assertEqual(self.answer('travel.where_on_date',{'date':'2024-02-29'})['data'],[])
        self.assertEqual(self.service.catalog(self.token)['people'],'unavailable');self.assertEqual(self.service.trips(self.token)['data'],[])
    def test_multicity_observations_keep_gaps_unknown_and_provenance_explicit(self):
        self.import_rows(self.asset('a',capture_time='2024-03-01T12:00:00+09:00'),self.asset('b',capture_time='2024-03-03T12:00:00+09:00',metadata={'location':{'lat':35.01,'lon':139.01,'place':'<script>unsafe</script>'},'geography':{'city_id':'second','city':'Second city','country_code':'JP'}}))
        self.rebuild();trip=self.service.trips(self.token)['data'][0]
        self.assertEqual(trip['kind'],'overnight_candidate');self.assertEqual(trip['observed_day_count'],2)
        self.assertEqual(trip['gaps'],[{'start':'2024-03-02','end':'2024-03-02','status':'unknown'}])
        self.assertEqual(len(self.answer('travel.cities_visited')['data']),2)
        self.assertNotIn('<script>',self.answer('photos.records')['markdown'])
    def test_inferred_habitual_suggestion_is_not_commuting_until_confirmed(self):
        self.import_rows(self.asset('a',capture_time='2024-03-01T12:00:00+09:00'),self.asset('b',capture_time='2024-03-02T12:00:00+09:00'))
        self.service.rebuild(self.token,self.csrf,'suggest',policy={'habitual_min_days':2})
        area=self.service.habitual_areas(self.token)['data'][0];self.assertFalse(area['confirmed']);self.assertEqual(len(self.service.trips(self.token)['data']),1)
        body={key:area[key] for key in ('label','lat','lon','radius_km','start','end')};body['confirmed']=True
        self.service.put_habitual_area(self.token,self.csrf,'confirm-area',body,area_id=area['id'],expected_revision=area['revision'])
        self.rebuild('exclude');self.assertEqual(self.service.trips(self.token)['data'],[])
        restarted=KnowledgeService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now));self.assertTrue(restarted.habitual_areas(self.token)['data'][0]['confirmed'])
    def test_manual_trip_dates_idempotency_concurrency_and_source_immutability(self):
        self.import_rows(self.asset());self.rebuild()
        with self.store._db() as db:before=[tuple(row) for row in db.execute('SELECT * FROM asset_revisions')]
        payload={'title':'Manual','start':'2024-01-01','end':'2024-01-10'}
        first=self.service.correct_trip(self.token,self.csrf,'manual','manual',payload=payload)
        self.assertEqual(first,self.service.correct_trip(self.token,self.csrf,'manual','manual',payload=payload))
        identity=first['trip_ids'][0]
        updated=self.service.correct_trip(self.token,self.csrf,'dates','dates',trip_id=identity,expected_revision=1,payload={'start':'2024-01-03','end':'2024-01-06'})
        with self.assertRaises(RuntimeErrorResult):self.service.correct_trip(self.token,self.csrf,'stale','rename',trip_id=identity,expected_revision=1,payload={'title':'stale'})
        with self.assertRaises(RuntimeErrorResult):self.service.correct_trip(self.token,self.csrf,'manual','manual',payload={**payload,'title':'changed'})
        restarted=KnowledgeService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now));self.assertEqual(restarted.trip(self.token,identity)['start'],'2024-01-03')
        split=restarted.correct_trip(self.token,self.csrf,'manual-split','split',trip_id=identity,expected_revision=2,payload={'date':'2024-01-05'});self.assertEqual(len(split['trip_ids']),2)
        with self.store._db() as db:self.assertEqual(before,[tuple(row) for row in db.execute('SELECT * FROM asset_revisions')])
    def test_semantically_changed_evidence_hides_cached_correction_until_explicit_reanchor(self):
        self.import_rows(self.asset());self.rebuild();trip=self.service.trips(self.token)['data'][0]
        self.service.correct_trip(self.token,self.csrf,'name','rename',trip_id=trip['trip_id'],expected_revision=1,payload={'title':'OLD_PRIVATE_LOCATION'})
        self.import_rows(self.asset(source_revision='r2',metadata={'location':{'lat':10,'lon':20},'geography':{'country_code':'ZZ'}}));self.rebuild('changed')
        self.assertEqual(self.service.trips(self.token)['data'],[])
        with self.assertRaises(RuntimeErrorResult):self.service.trip(self.token,trip['trip_id'])
        self.service.correct_trip(self.token,self.csrf,'reanchor','confirm',trip_id=trip['trip_id'],expected_revision=2)
        result=self.service.trip(self.token,trip['trip_id']);self.assertNotIn('OLD_PRIVATE_LOCATION',str(result));self.assertEqual(result['evidence'][0]['geography']['country_code'],'ZZ')
    def test_backup_restore_retains_corrections_without_resurrecting_source_access(self):
        self.import_rows(self.asset());self.rebuild();trip=self.service.trips(self.token)['data'][0]
        self.service.correct_trip(self.token,self.csrf,'name','rename',trip_id=trip['trip_id'],expected_revision=1,payload={'title':'Retained private trip'})
        backup=Path(self.tmp.name)/'backup';self.store.backup(backup);restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored');service=KnowledgeService(restored)
        with self.assertRaises(RuntimeErrorResult):service.trip(self.token,trip['trip_id'])
        auth=restored.login('owner','synthetic-knowledge-password','fresh');self.assertEqual(service.trips(auth['token'])['data'],[])
        with restored._db() as db:self.assertEqual(db.execute('SELECT title FROM knowledge_trip_revisions WHERE trip_id=? AND revision=2',(trip['trip_id'],)).fetchone()[0],'Retained private trip')
    def test_csrf_audit_failure_and_cross_owner_corrections_fail_closed(self):
        self.import_rows(self.asset());self.rebuild();trip=self.service.trips(self.token)['data'][0]
        with self.assertRaises(RuntimeErrorResult):self.service.correct_trip(self.token,'spoof','name','rename',trip_id=trip['trip_id'],expected_revision=1,payload={'title':'X'})
        self.store.create_owner('other','synthetic-knowledge-password','Other');other=self.store.login('other','synthetic-knowledge-password','other')
        with self.assertRaises(RuntimeErrorResult):self.service.correct_trip(other['token'],other['csrf_token'],'name','rename',trip_id=trip['trip_id'],expected_revision=1,payload={'title':'X'})
        with self.store._db() as db:db.execute("CREATE TRIGGER deny_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(RuntimeErrorResult):self.service.correct_trip(self.token,self.csrf,'fail','rename',trip_id=trip['trip_id'],expected_revision=1,payload={'title':'X'})
        with self.store._db() as db:self.assertEqual(db.execute('SELECT revision FROM knowledge_trips WHERE id=?',(trip['trip_id'],)).fetchone()[0],1)
        with self.assertRaises(RuntimeErrorResult):self.answer('photos.statistics')
    def test_window_and_id_redaction_apply_to_all_evidence_and_trip_dependencies(self):
        self.import_rows(self.asset('a'),self.asset('b',capture_time='2024-03-01T12:00:00+09:00'));self.rebuild()
        result=self.answer('photos.records',scope={'fields':['capture_time','location']})
        self.assertTrue(all('evidence' not in row for row in result['data']))
        window={'start':'2024-03-01','end':'2024-03-02'}
        self.assertEqual(self.answer('photos.statistics',scope=window)['data']['records'],1)
        self.assertEqual(self.service.trips(self.token,scope=window)['data'],[])
        self.assertEqual(self.answer('photos.statistics',scope={'connection_ids':[]})['status'],'no_evidence')

    def test_trip_summary_declares_remaining_evidence_and_dismissal_survives_rebuild(self):
        self.import_rows(self.asset('a'),self.asset('b'));self.rebuild()
        trip=self.service.trips(self.token)['data'][0];self.assertTrue(trip['has_more_evidence']);self.assertEqual(trip['evidence'],[])
        first=self.service.trip(self.token,trip['trip_id'],limit=1);self.assertIsNotNone(first['next_cursor'])
        second=self.service.trip(self.token,trip['trip_id'],limit=1,cursor=first['next_cursor']);self.assertIsNone(second['next_cursor'])
        self.assertNotEqual(first['evidence'][0]['evidence'],second['evidence'][0]['evidence'])
        self.service.correct_trip(self.token,self.csrf,'dismiss','dismiss',trip_id=trip['trip_id'],expected_revision=trip['revision'])
        self.rebuild('post-dismiss');self.assertEqual(self.service.trips(self.token)['data'],[])
    def test_invalid_area_identity_and_mutation_values_are_structured_refusals(self):
        area={'label':'Area','lat':35,'lon':139,'radius_km':10,'start':'2023-01-01','end':'2025-01-01','confirmed':True}
        with self.assertRaises(RuntimeErrorResult):self.service.put_habitual_area(self.token,self.csrf,'invalid',area,area_id=[])
        with self.assertRaises(RuntimeErrorResult):self.service.put_habitual_area(self.token,self.csrf,'invalid',dict(area,radius_km=float('nan')))
        with self.assertRaises(RuntimeErrorResult):self.service.rebuild(self.token,self.csrf,'invalid',policy={'max_gap_hours':float('inf')})

    def test_period_statistics_year_range_and_on_this_day_use_offset_local_dates(self):
        self.import_rows(self.asset('photo'),self.asset('video',media_type='video',capture_time='2024-03-01T00:30:00+14:00'),self.asset('live',media_type='live',capture_time='2020-02-29T12:00:00-03:00'))
        self.rebuild()
        self.assertEqual(len(self.answer('travel.where_in_year',{'year':2024})['data']),2)
        period={'start':'2024-02-29','end':'2024-03-01'}
        self.assertEqual(len(self.answer('travel.where_in_range',period)['data']),1)
        stats=self.answer('photos.statistics',period)['data'];self.assertEqual((stats['photos'],stats['videos'],stats['live_photos']),(1,0,0))
        self.assertEqual(len(self.answer('photos.on_this_day',{'month_day':'02-29'})['data']),2)
        with self.assertRaises(RuntimeErrorResult):self.answer('travel.where_in_range',{'start':'2024-02-29'})

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(KnowledgeTests));print(f'{result.testsRun-len(result.failures)-len(result.errors)} passed, {len(result.failures)+len(result.errors)} failed');sys.exit(not result.wasSuccessful())
