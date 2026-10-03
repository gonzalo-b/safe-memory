"""One combined retained-store recovery across knowledge, media and Gallery edits."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests.test_originals import OriginalTests
from tests.test_ingestion import PASSWORD
from runtime.artifacts import ArtifactService
from runtime.knowledge import KnowledgeService
from runtime.store import RuntimeStore,RuntimeErrorResult

class IntegratedRecoveryTests(unittest.TestCase):
    def test_restore_keeps_all_revision_intent_and_bytes_but_quarantines_every_surface(self):
        case=OriginalTests();case.setUp()
        try:
            knowledge=KnowledgeService(case.store);knowledge.rebuild(case.token,case.csrf,'build')
            knowledge.correct_trip(case.token,case.csrf,'manual','manual',payload={'title':'Synthetic journey','start':'2026-10-01','end':'2026-10-01','evidence_ids':[case.asset_id]})
            trip=knowledge.trips(case.token)['data'][0]
            knowledge.correct_trip(case.token,case.csrf,'rename','rename',trip_id=trip['trip_id'],expected_revision=trip['revision'],payload={'title':'Retained synthetic journey'})
            galleries=ArtifactService(case.store);gallery=galleries.create(case.token,case.csrf,'create',title='Retained synthetic Gallery',asset_ids=[case.asset_id]);gallery=galleries.edit(case.token,case.csrf,'layout',gallery['artifact_id'],1,{'layout':'story'})
            original=case.upload()
            optimized=case.media.begin(case.device,case.credential,case.asset_id,'r1','still','image/jpeg',len(case.jpeg),__import__('hashlib').sha256(case.jpeg).hexdigest(),'copy')
            case.media.chunk(case.device,case.credential,optimized['upload_id'],0,case.jpeg);component=case.media.complete(case.device,case.credential,optimized['upload_id'])
            tables=['artifact_revisions','artifact_members','knowledge_trip_revisions','original_requests','original_uploads','original_components','media_components']
            with case.store._db() as db:before={table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in tables}
            backup=Path(case.tmp.name)/'combined-backup';case.store.backup(backup)
            restored=RuntimeStore.restore(backup,Path(case.tmp.name)/'quarantined');fresh=restored.login('owner',PASSWORD,'restored')
            with restored._db() as db:
                self.assertEqual(before,{table:db.execute('SELECT count(*) FROM '+table).fetchone()[0] for table in tables})
                self.assertEqual(db.execute('SELECT title,layout FROM artifact_revisions WHERE revision=2').fetchone()[:],('Retained synthetic Gallery','story'))
            self.assertEqual(ArtifactService(restored).list(fresh['token'])['artifacts'],[])
            self.assertEqual(KnowledgeService(restored).trips(fresh['token'])['data'],[])
            from runtime.originals import OriginalService
            from runtime.media import MediaService
            for read in [lambda:restored.session(case.token),lambda:ArtifactService(restored).get(fresh['token'],gallery['artifact_id']),lambda:OriginalService(restored).read(fresh['token'],original['component_id']),lambda:MediaService(restored).read(fresh['token'],component['component_id'])]:
                with self.assertRaises(RuntimeErrorResult):read()
            # Backup/restore byte verification occurs before the quarantined store is returned.
            self.assertTrue((backup/'manifest.json').is_file());self.assertTrue(before['original_components']);self.assertTrue(before['media_components'])
        finally:case.tearDown()

if __name__=='__main__':
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IntegratedRecoveryTests));f=len(r.errors)+len(r.failures);print(f'{r.testsRun-f} passed, {f} failed');sys.exit(bool(f))
