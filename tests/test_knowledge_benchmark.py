"""Reproducible synthetic index benchmark; source ingestion throughput is separate.

Default is a bounded correctness test. Use --records 10000 or 100000 for timings.
The seed copies a valid synthetic wrapper in batches; no personal Photos access.
"""
from pathlib import Path
import datetime as dt
import json, math, resource, statistics, sys, time, unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_knowledge import KnowledgeTests


def seed(case, count):
    case.import_rows(case.asset('seed'))
    with case.store._db() as db:
        template=dict(db.execute('SELECT * FROM asset_revisions').fetchone())
        db.execute('BEGIN IMMEDIATE')
        for start in range(1,count,1000):
            assets=[];revisions=[]
            for index in range(start,min(count,start+1000)):
                identity=f'{index:032x}';day=dt.date(2000,1,1)+dt.timedelta(days=(index//20)*4)
                timestamp=day.isoformat()+'T12:00:00+09:00';instant=dt.datetime.fromisoformat(timestamp).timestamp()
                assets.append((identity,case.owner,case.connection,'synthetic-'+str(index),1,0,0,0,'personal',1,case.now,case.now))
                revisions.append((identity,1,'r1','synthetic',template['raw_json'],'video' if index%5==0 else 'photo',timestamp,'capture_offset',day.isoformat(),instant,None,'unknown',case.now))
            db.executemany('INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',assets)
            db.executemany('INSERT INTO asset_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',revisions)
        db.commit()


def benchmark(count, rounds=12):
    case=KnowledgeTests();case.setUp()
    try:
        seed(case,count)
        print(f"Seeded {count} records",file=sys.stderr,flush=True)
        baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        start=time.perf_counter();case.rebuild();rebuild=time.perf_counter()-start
        print(f"Rebuilt in {rebuild:.3f}s",file=sys.stderr,flush=True)
        queries={
            'day':lambda:case.answer('travel.where_on_date',{'date':'2000-01-05'}),
            'year':lambda:case.answer('travel.where_in_year',{'year':2000}),
            'countries':lambda:case.answer('travel.countries_visited'),
            'statistics':lambda:case.answer('photos.statistics'),
            'occasion':lambda:case.answer('travel.occasion_history',{'month_day':'02-29','count':10,'as_of':'2056-10-02'}),
            'trips_page':lambda:case.service.trips(case.token,limit=20),
        }
        timings={}
        # Audited session read separates general host/fsync latency from scans.
        queries={'audited_session':lambda:case.store.session(case.token),**queries}
        for name, query in queries.items():
            print('Query '+name,file=sys.stderr,flush=True)
            query();samples=[];cpu_samples=[]
            for _ in range(rounds):
                start=time.perf_counter();cpu_start=time.process_time();query();samples.append((time.perf_counter()-start)*1000);cpu_samples.append((time.process_time()-cpu_start)*1000)
            timings[name]={'p50_ms':round(statistics.median(samples),2),'p95_ms':round(sorted(samples)[math.ceil(len(samples)*.95)-1],2),'max_ms':round(max(samples),2),'cpu_p95_ms':round(sorted(cpu_samples)[math.ceil(len(cpu_samples)*.95)-1],2)}
        assert case.answer('photos.statistics')['data']['records']==count
        with case.store._db() as db:
            facts=db.execute('SELECT count(*) FROM knowledge_facts').fetchone()[0];db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            trips=db.execute('SELECT count(*) FROM knowledge_trips').fetchone()[0]
        # macOS reports bytes, Linux KiB. Record platform and normalize to MiB.
        unit=1 if sys.platform=='darwin' else 1024
        return {'records':count,'facts':facts,'inferred_trips':trips,'rebuild_seconds':round(rebuild,3),'baseline_peak_rss_mib':round(baseline*unit/2**20,2),'peak_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*unit/2**20,2),'store_mib':round(sum(p.stat().st_size for p in Path(case.tmp.name).rglob('*') if p.is_file())/2**20,2),'warm_rounds':rounds,'queries':timings,'platform':sys.platform,'coverage':'synthetic projected metadata; no ingestion or device throughput claim'}
    finally:case.tearDown()

class BenchmarkTests(unittest.TestCase):
    def test_batched_synthetic_seed_and_queries_preserve_exact_asset_count(self):
        result=benchmark(60,1);self.assertEqual(result['facts'],60);self.assertGreater(result['inferred_trips'],1)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--records':print(json.dumps(benchmark(int(sys.argv[2])),indent=2))
    else:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BenchmarkTests));print(f'{result.testsRun-len(result.failures)-len(result.errors)} passed, {len(result.failures)+len(result.errors)} failed');sys.exit(not result.wasSuccessful())
