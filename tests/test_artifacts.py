"""Private Gallery composition, current access, durable edits and recovery."""
from pathlib import Path
import json, secrets, sqlite3, sys, tempfile, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.artifacts import ArtifactService
from runtime.store import RuntimeStore, RuntimeErrorResult
from runtime.pairing import PairingService
from runtime.ingestion import IngestionService
from runtime.knowledge import KnowledgeService

class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='memory-artifact-');self.now=1800000000
        self.store=RuntimeStore(Path(self.tmp.name)/'store',fixture=True,clock=lambda:self.now)
        self.owner=self.store.create_owner('owner','synthetic-artifact-password','Fixture owner')
        self.auth=self.store.login('owner','synthetic-artifact-password','local');self.token=self.auth['token'];self.csrf=self.auth['csrf_token']
        p=PairingService(self.store);i=p.start(self.token,self.csrf);self.credential=secrets.token_urlsafe(32)
        c=p.claim(i['secret'],'Fixture phone','fixture-library',self.credential);b=p.confirm(self.token,self.csrf,c['claim_id'],c['fingerprint'])
        self.device=b['device_id'];self.connection=b['connection_id'];self.ingest=IngestionService(self.store);self.service=ArtifactService(self.store);self.runs=0
        self.import_rows(self.asset('a'),self.asset('b'),self.asset('c'))
        with self.store._db() as db:self.ids={r['native_id']:r['id'] for r in db.execute('SELECT id,native_id FROM assets')}
    def tearDown(self):self.tmp.cleanup()
    def asset(self,native,**changes):
        a=dict(native_id=native,source_revision='r1',media_type='photo',hidden=False,collection='personal',capture_time='2024-03-01T12:00:00+09:00',time_basis='capture_offset',owner_presence='unknown',source_modified='2026-10-02T00:00:00Z',metadata={'geography':{'country_code':'JP','city_id':'tokyo','city':'Tokyo'},'location':{'latitude':35,'longitude':139}});a.update(changes);return a
    def import_rows(self,*rows):
        self.runs+=1;r=self.ingest.begin(self.device,self.credential,str(self.runs),'full','recent',[x['native_id'] for x in rows]);self.ingest.append(self.device,self.credential,r['run_id'],'page',0,'checkpoint',list(rows));self.ingest.finish(self.device,self.credential,r['run_id'])
    def create(self,key='create',names=('a','b'),**kw):return self.service.create(self.token,self.csrf,key,title='My gallery',asset_ids=[self.ids[x] for x in names],**kw)
    def get(self,receipt):return self.service.get(self.token,receipt['artifact_id'])
    def edit(self,r,key,patch):return self.service.edit(self.token,self.csrf,key,r['artifact_id'],r['revision'],patch)
    def test_save_restart_reopen_and_immutable_source(self):
        with self.store._db() as db:before=[tuple(r) for r in db.execute('SELECT * FROM asset_revisions')]
        r=self.create();v=self.edit(r,'edit',{'title':'Private <script>text</script>','layout':'story','cover_asset_id':self.ids['b'],'order':[self.ids['b'],self.ids['a']]})
        self.service=ArtifactService(RuntimeStore(self.store.root,fixture=True,clock=lambda:self.now));data=self.get(v)
        self.assertEqual((data['id'],data['revision'],data['layout'],data['title']),(r['artifact_id'],2,'story','Private <script>text</script>'))
        self.assertEqual([x['asset_id'] for x in data['members']],[self.ids['b'],self.ids['a']]);self.assertEqual(data['cover_asset_id'],self.ids['b'])
        self.assertEqual(self.service.list(self.token)['artifacts'][0]['id'],r['artifact_id'])
        with self.store._db() as db:self.assertEqual(before,[tuple(x) for x in db.execute('SELECT * FROM asset_revisions')]);self.assertEqual(db.execute('SELECT count(*) FROM artifact_revisions').fetchone()[0],2)
    def test_remove_recompose_keeps_exclusion_and_manual_add(self):
        r=self.create();r=self.edit(r,'remove',{'remove_ids':[self.ids['a']],'add_ids':[self.ids['c']]})
        r=self.service.recompose(self.token,self.csrf,'compose',r['artifact_id'],r['revision'],asset_ids=[self.ids['a'],self.ids['b']])
        d=self.get(r);self.assertEqual({x['asset_id'] for x in d['members']},{self.ids['b'],self.ids['c']});self.assertEqual(d['excluded_ids'],[self.ids['a']])
        r=self.edit(r,'reinclude',{'add_ids':[self.ids['a']]});self.assertEqual(self.get(r)['excluded_ids'],[])
        with self.store._db() as db:self.assertEqual(db.execute("SELECT count(*) FROM artifact_members WHERE intent='excluded'").fetchone()[0],2)
    def test_idempotent_retry_and_optimistic_conflict(self):
        r=self.create();self.assertEqual(r,self.create());new=self.edit(r,'rename',{'title':'Changed'})
        self.assertEqual(new,self.edit(r,'rename',{'title':'Changed'}))
        with self.assertRaises(RuntimeErrorResult):self.create(names=('c',))
        with self.assertRaises(RuntimeErrorResult):self.edit(r,'stale',{'title':'Lost update'})
        self.assertEqual(self.get(new)['title'],'Changed')
    def test_restrictions_hide_title_list_lineage_and_retry_receipt(self):
        r=self.create();self.ingest.permission(self.device,self.credential,'revoked')
        self.assertEqual(self.service.list(self.token)['artifacts'],[])
        for fn in [lambda:self.get(r),lambda:self.create(),lambda:self.service.debug(self.token,r['artifact_id'])]:
            with self.assertRaises(RuntimeErrorResult) as result:fn()
            self.assertEqual(result.exception.status,404);self.assertNotIn('My gallery',str(result.exception))
    def test_hidden_and_excluded_id_projection_apply_before_disclosure(self):
        r=self.create();r=self.edit(r,'remove',{'remove_ids':[self.ids['a']]})
        self.ingest.configure(self.token,self.csrf,self.connection,True,False,False)
        self.import_rows(self.asset('a',source_revision='r2',hidden=True,source_modified='2026-10-03T00:00:00Z'))
        self.ingest.configure(self.token,self.csrf,self.connection,False,False,False)
        self.assertEqual(self.get(r)['excluded_ids'],[])
        with self.assertRaises(RuntimeErrorResult):self.service.create(self.token,self.csrf,'hidden',title='Hidden',asset_ids=[self.ids['a']])
    def test_explicit_hidden_selection_permitted_but_recompose_defaults_exclude_hidden(self):
        self.ingest.configure(self.token,self.csrf,self.connection,True,False,False);self.import_rows(self.asset('c',source_revision='r2',hidden=True,source_modified='2026-10-03T00:00:00Z'))
        r=self.create(names=('a',));r=self.service.recompose(self.token,self.csrf,'auto',r['artifact_id'],r['revision'],asset_ids=[self.ids['b'],self.ids['c']])
        self.assertEqual({x['asset_id'] for x in self.get(r)['members']},{self.ids['a'],self.ids['b']})
        r=self.edit(r,'explicit',{'add_ids':[self.ids['c']]});self.assertEqual(len(self.get(r)['members']),3)
    def test_reimport_resolves_current_media_identity_without_stale_evidence(self):
        r=self.create(names=('a',));self.import_rows(self.asset('a',source_revision='r2',media_type='video'))
        d=self.get(r);self.assertEqual((d['members'][0]['revision'],d['members'][0]['selected_revision'],d['members'][0]['media_type']),(2,1,'video'))
        self.assertNotIn('storage_key',json.dumps(d));self.assertNotIn('raw_json',json.dumps(d))
    def test_trip_snapshot_composition_has_generation_and_safe_lineage(self):
        k=KnowledgeService(self.store);k.rebuild(self.token,self.csrf,'build');trip=k.trips(self.token)['data'][0]
        r=self.service.create(self.token,self.csrf,'trip',title='Trip gallery',trip_id=trip['trip_id'],expected_trip_revision=trip['revision'])
        d=self.get(r);self.assertEqual(len(d['members']),3);self.assertEqual(d['lineage']['trip_id'],trip['trip_id']);self.assertTrue(d['lineage']['generation'])
        with self.assertRaises(RuntimeErrorResult):self.service.create(self.token,self.csrf,'stale-trip',title='X',trip_id=trip['trip_id'],expected_trip_revision=99)
        k.correct_trip(self.token,self.csrf,'dismiss','dismiss',trip_id=trip['trip_id'],expected_revision=trip['revision'])
        self.assertIsNone(self.get(r)['lineage']['trip_id'])
    def test_owner_csrf_and_all_ids_checked(self):
        r=self.create();self.store.create_owner('other','synthetic-artifact-password','Other');other=self.store.login('other','synthetic-artifact-password','other')
        self.assertEqual(self.service.list(other['token'])['artifacts'],[])
        for fn in [lambda:self.service.get(other['token'],r['artifact_id']),lambda:self.service.edit(self.token,'bad','bad',r['artifact_id'],1,{'title':'X'}),lambda:self.service.create(other['token'],other['csrf_token'],'create',title='X',asset_ids=[self.ids['a']]),lambda:self.service.get('no-session',r['artifact_id'])]:
            with self.assertRaises(RuntimeErrorResult):fn()
    def test_audit_and_mid_save_failure_keep_last_coherent_revision(self):
        r=self.create()
        with self.store._db() as db:db.execute("CREATE TRIGGER fail_member BEFORE INSERT ON artifact_members BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(sqlite3.Error):self.edit(r,'fail',{'title':'Not saved'})
        self.assertEqual(self.get(r)['revision'],1)
        with self.store._db() as db:db.execute('DROP TRIGGER fail_member');db.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT,'disk'); END")
        with self.assertRaises(RuntimeErrorResult):self.edit(r,'audit',{'title':'Not saved'})
        with self.assertRaises(RuntimeErrorResult):self.get(r)
        with self.store._db() as db:self.assertEqual(db.execute('SELECT revision FROM artifacts').fetchone()[0],1);self.assertEqual(db.execute('SELECT count(*) FROM artifact_requests').fetchone()[0],1)
    def test_backup_restore_retains_edits_without_resurrecting_access(self):
        r=self.create();r=self.edit(r,'remove',{'remove_ids':[self.ids['a']]});backup=Path(self.tmp.name)/'backup';self.store.backup(backup)
        restored=RuntimeStore.restore(backup,Path(self.tmp.name)/'restored');svc=ArtifactService(restored)
        with self.assertRaises(RuntimeErrorResult):svc.get(self.token,r['artifact_id'])
        fresh=restored.login('owner','synthetic-artifact-password','new');self.assertEqual(svc.list(fresh['token'])['artifacts'],[])
        with restored._db() as db:self.assertEqual(db.execute('SELECT revision FROM artifacts').fetchone()[0],2);self.assertEqual(db.execute("SELECT count(*) FROM artifact_members WHERE revision=2 AND intent='excluded'").fetchone()[0],1)
    def test_recompose_operation_debug_and_empty_gallery_are_real(self):
        r=self.create(names=());self.assertEqual(self.get(r)['members'],[])
        r=self.service.recompose(self.token,self.csrf,'rerun',r['artifact_id'],1)
        d=self.service.debug(self.token,r['artifact_id']);self.assertEqual(d['revision'],2);self.assertEqual(d['operations'][0]['status'],'complete');self.assertEqual(d['definition_version'],'private-gallery-v1')
    def test_inputs_and_order_cannot_smuggle_invalid_members_or_markup_settings(self):
        r=self.create()
        for patch in [{'html':'<script>x</script>'},{'layout':'javascript:evil'},{'order':[self.ids['a']]},{'cover_asset_id':self.ids['c']},{'add_ids':[self.ids['a']]*2},{'remove_ids':[self.ids['a']],'add_ids':[self.ids['a']]},{'title':''}]:
            with self.assertRaises(RuntimeErrorResult):self.edit(r,secrets.token_hex(8),patch)
        self.assertEqual(self.get(r)['revision'],1)
    def test_list_pagination_no_restricted_count_and_overview_current_count(self):
        a=self.create('a');b=self.create('b',names=('c',));page=self.service.list(self.token,limit=1);self.assertEqual(len(page['artifacts']),1)
        following=self.service.list(self.token,limit=1,cursor=page['next_cursor']);self.assertEqual(len(following['artifacts']),1);self.assertNotEqual(page['artifacts'][0]['id'],following['artifacts'][0]['id']);self.assertIsNone(following['next_cursor'])
        self.assertEqual(self.store.overview(self.token)['counts']['artifacts'],2)
        self.ingest.permission(self.device,self.credential,'revoked');self.assertEqual(self.store.overview(self.token)['counts']['artifacts'],0)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactTests));failed=len(result.failures)+len(result.errors);print(f'{result.testsRun-failed} passed, {failed} failed');raise SystemExit(bool(failed))
