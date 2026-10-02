"""Synthetic-only bounded scan benchmark. Refuses an existing destination."""
import argparse
import datetime as dt
import json
from pathlib import Path
import resource
import secrets
import statistics
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore
from runtime.pairing import PairingService
from runtime.progressive import ProgressiveService
from runtime.ingestion import IngestionService

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--count',type=int,choices=[10000,100000],required=True);args=parser.parse_args()
    if Path(args.root).exists():raise SystemExit('Use a new private synthetic destination; prior data is retained.')
    store=RuntimeStore(args.root,fixture=True);store.create_owner('benchmark','synthetic-benchmark-password','Synthetic benchmark')
    auth=store.login('benchmark','synthetic-benchmark-password','synthetic');pairing=PairingService(store)
    intent=pairing.start(auth['token'],auth['csrf_token']);credential=secrets.token_urlsafe(32)
    claim=pairing.claim(intent['secret'],'Synthetic benchmark','synthetic-progressive-benchmark',credential)
    pairing.confirm(auth['token'],auth['csrf_token'],claim['claim_id'],claim['fingerprint']);device=claim['claim_id']
    service=ProgressiveService(store);run=service.begin(device,credential,'synthetic-scan','full',args.count,False,False,False)
    baseline=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;start=time.perf_counter();pages=[]
    for offset in range(0,args.count,100):
        phase='recent' if offset<args.count//2 else 'backfill';rows=[]
        for index in range(offset,min(offset+100,args.count)):
            stamp=dt.datetime.now(dt.timezone.utc)-dt.timedelta(days=1 if phase=='recent' else 3650,seconds=index)
            captured=stamp.isoformat(timespec='seconds');unknown=index==args.count-1
            rows.append({'native_id':f'synthetic-{index:06d}','source_revision':'synthetic-r1','media_type':'photo','hidden':False,'collection':'personal','capture_time':None if unknown else captured,'time_basis':'unknown' if unknown else 'capture_offset','owner_presence':'unknown','source_modified':captured,'metadata':{'fixture':True,'location':None,'nativeField':'synthetic'}})
        before=time.perf_counter();service.append(device,credential,run['run_id'],f'page-{offset}',offset//100,str(offset+len(rows)),phase,rows);pages.append(time.perf_counter()-before)
    finished=service.finish(device,credential,run['run_id']);elapsed=time.perf_counter()-start
    ingest=IngestionService(store);queries=[]
    for i in range(25):
        before=time.perf_counter();result=ingest.assets(auth['token'],limit=25,offset=100 if i else 0);queries.append(time.perf_counter()-before)
        assert len(result['assets'])==25
    with store._db() as db:actual=db.execute('SELECT count(*) FROM assets').fetchone()[0]
    assert actual==args.count and finished['observed']==args.count
    scale=1024*1024 if sys.platform=='darwin' else 1024
    print(json.dumps({'fixture':True,'count':args.count,'seconds':round(elapsed,3),'page_p95_ms':round(sorted(pages)[int(.95*(len(pages)-1))]*1000,3),'photos_cold_ms':round(queries[0]*1000,3),'photos_warm_p95_ms':round(sorted(queries[1:])[int(.95*(len(queries)-2))]*1000,3),'peak_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/scale,2),'baseline_peak_rss_mib':round(baseline/scale,2),'retained_bytes':sum(p.stat().st_size for p in store.root.rglob('*') if p.is_file()),'media_transferred':0},indent=2))
if __name__=='__main__':main()
