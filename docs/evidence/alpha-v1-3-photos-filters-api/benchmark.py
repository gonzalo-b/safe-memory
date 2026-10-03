import json,math,statistics,sys,time,resource
from pathlib import Path
repo=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo))
sys.path.insert(0,str(repo/'tests'))
from test_knowledge_benchmark import seed
from test_knowledge import KnowledgeTests
for count in (10000,100000):
 case=KnowledgeTests();case.setUp()
 try:
  seed(case,count)
  with case.store._db() as db:
   db.execute('UPDATE assets SET current_revision=current_revision')
   metadata_bytes=len(db.execute('SELECT raw_json FROM asset_revisions LIMIT 1').fetchone()[0].encode())
  queries={
   'audited_session':lambda:case.store.session(case.token),
   'photos_baseline':lambda:case.ingest.assets(case.token,limit=25),
   'place_all_match_first_page':lambda:case.ingest.assets(case.token,place='TOKYO',limit=25),
   'place_no_match_full_scan':lambda:case.ingest.assets(case.token,place='NO SUCH SYNTHETIC PLACE',limit=25),
   'place_last_page':lambda:case.ingest.assets(case.token,place='TOKYO',limit=25,offset=count-25),
  }
  timings={}
  for name,query in queries.items():
   before=time.perf_counter();result=query();cold=(time.perf_counter()-before)*1000
   samples=[]
   for i in range(7):
    before=time.perf_counter();query();samples.append((time.perf_counter()-before)*1000)
   timings[name]={'cold_ms':round(cold,2),'warm_p50_ms':round(statistics.median(samples),2),'warm_p95_ms':round(sorted(samples)[math.ceil(len(samples)*.95)-1],2),'warm_max_ms':round(max(samples),2),'returned':len(result.get('assets',[])) if name!='audited_session' else None}
  print(json.dumps({'fixture':True,'count':count,'platform':sys.platform,'warm_rounds':7,'queries':timings,'peak_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,2),'metadata_bytes_per_row':metadata_bytes,'scope':'existing synthetic benchmark seed; index trigger refreshed; no rebuild or media; not device/ingest throughput'}),flush=True)
 finally:case.tearDown()
