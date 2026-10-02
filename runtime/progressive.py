"""Bounded pages of a frozen authorized Photos enumeration. No Source writes."""
from __future__ import annotations
import datetime as dt
import json
from runtime.ingestion import IngestionService, VISIBLE, LEASE_SECONDS, canonical, choice, instant
from runtime.pairing import _text
from runtime.store import RuntimeErrorResult, digest, identifier

class ProgressiveService:
    def __init__(self,store):self.store=store;self.ingest=IngestionService(store)

    def _scan(self,db,source,run_id,allow_complete=True):
        run=self.ingest._active(db,source,run_id,allow_complete=allow_complete)
        scan=db.execute('SELECT * FROM scan_runs WHERE run_id=?',(run_id,)).fetchone()
        if scan is None:raise RuntimeErrorResult(400,'scan_required')
        return run,scan

    def _receipt(self,run,scan):
        return {'run_id':run['id'],'next_sequence':run['next_sequence'],'state':run['state'],
                'coverage':run['coverage'],'recent_after':scan['recent_after'],'observed':scan['observed'],
                'expected_count':scan['expected_count'],'checkpoint':run['checkpoint']}

    def begin(self,device_id,credential,request_key,permission,expected_count,include_hidden,include_shared_library,include_shared_albums):
        def start(db,source):
            flags=(include_hidden,include_shared_library,include_shared_albums)
            if (not _text(request_key,128) or not choice(permission,{'full','limited'}) or type(expected_count) is not int
                or not 0<=expected_count<=1000000 or any(type(flag) is not bool for flag in flags)):
                raise RuntimeErrorResult(400,'invalid_scan')
            if flags!=tuple(bool(source[k]) for k in ('include_hidden','include_shared_library','include_shared_albums')):
                raise RuntimeErrorResult(403,'source_consent_mismatch')
            now=int(self.store.clock());hashed=digest(canonical([permission,expected_count,*flags]))
            previous=db.execute('SELECT * FROM ingest_runs WHERE connection_id=? AND request_key=?',(source['id'],request_key)).fetchone()
            if previous:
                scan=db.execute('SELECT * FROM scan_runs WHERE run_id=?',(previous['id'],)).fetchone()
                if previous['request_digest']!=hashed or previous['device_id']!=device_id or scan is None:raise RuntimeErrorResult(409,'replay_conflict')
                if previous['policy_revision']!=source['policy_revision'] or source['permission']!=permission:raise RuntimeErrorResult(403,'selection_revoked')
                if previous['state']=='complete':return self._receipt(previous,scan)
            run_id=previous['id'] if previous else identifier()
            lease=db.execute('SELECT * FROM ingest_leases WHERE connection_id=?',(source['id'],)).fetchone()
            if lease and lease['run_id']!=run_id and lease['expires_at']>now:raise RuntimeErrorResult(409,'ingest_busy')
            if lease and lease['run_id']!=run_id:
                db.execute("UPDATE ingest_runs SET state='interrupted' WHERE id=? AND state='active'",(lease['run_id'],))
                db.execute("UPDATE operations SET status='interrupted' WHERE id=?",(lease['run_id'],))
            if previous:
                db.execute("UPDATE ingest_runs SET state='active' WHERE id=?",(run_id,))
                db.execute("UPDATE operations SET status='running' WHERE id=?",(run_id,))
                db.execute('UPDATE scan_runs SET retry_requested=0 WHERE run_id=?',(run_id,))
            else:
                coverage='authorized_'+permission+'_scan'
                db.execute('''INSERT INTO ingest_runs(id,owner_id,connection_id,device_id,request_key,request_digest,phase,permission,policy_revision,selected_json,coverage,state,created_at)
                  VALUES(?,?,?,?,?,?,'recent',?,?,'[]',?,'active',?)''',
                  (run_id,source['owner_id'],source['id'],device_id,request_key,hashed,permission,source['policy_revision']+1,coverage,now))
                boundary=dt.datetime.fromtimestamp(now-90*86400,dt.timezone.utc).isoformat()
                db.execute('INSERT INTO scan_runs(run_id,expected_count,recent_after) VALUES(?,?,?)',(run_id,expected_count,boundary))
                db.execute("INSERT INTO operations(id,owner_id,action,status,created_at) VALUES(?,?,'ingest_scan','running',?)",(run_id,source['owner_id'],now))
                if permission=='limited' or source['permission']!=permission:
                    db.execute('UPDATE assets SET scope_authorized=0 WHERE connection_id=?',(source['id'],))
                db.execute("UPDATE connections SET permission=?,status='indexing',policy_revision=policy_revision+1 WHERE id=?",(permission,source['id']))
            db.execute('INSERT INTO ingest_leases VALUES(?,?,?) ON CONFLICT(connection_id) DO UPDATE SET run_id=excluded.run_id,expires_at=excluded.expires_at',(source['id'],run_id,now+LEASE_SECONDS))
            return self._receipt(db.execute('SELECT * FROM ingest_runs WHERE id=?',(run_id,)).fetchone(),db.execute('SELECT * FROM scan_runs WHERE run_id=?',(run_id,)).fetchone())
        return self.ingest._run('ingest_begin',device_id,credential,start)

    def append(self,device_id,credential,run_id,batch_key,sequence,checkpoint,phase,assets):
        def commit(db,source):
            run,scan=self._scan(db,source,run_id)
            if not choice(phase,{'recent','backfill'}) or not isinstance(assets,list) or not 1<=len(assets)<=100:
                raise RuntimeErrorResult(400,'invalid_batch')
            # Bind phase into the same immutable receipt digest without changing raw metadata.
            if not isinstance(checkpoint,str) or len(checkpoint)>2000:raise RuntimeErrorResult(400,'invalid_checkpoint')
            bound=phase+':'+checkpoint
            prior=db.execute('SELECT receipt_json FROM ingest_batches WHERE run_id=? AND batch_key=?',(run_id,batch_key)).fetchone() if isinstance(batch_key,str) else None
            if prior:
                return self.ingest._append(db,source,run_id,batch_key,sequence,bound,assets,authorized_scan=True)
            if run['state']!='active' or scan['observed']+len(assets)>scan['expected_count']:
                raise RuntimeErrorResult(409,'scan_count_conflict')
            if scan['phase']=='backfill' and phase=='recent':raise RuntimeErrorResult(409,'scan_order_conflict')
            last=scan['last_instant'];unknown=bool(scan['unknown_started']);missing=scan['missing_date'];first=scan['first_capture'];end=scan['last_capture']
            boundary=instant(scan['recent_after']);seen=set()
            for value in assets:
                captured,_=self.ingest._validate(value);native=value['native_id']
                if native in seen or db.execute('SELECT 1 FROM scan_assets WHERE run_id=? AND native_id=?',(run_id,native)).fetchone():
                    raise RuntimeErrorResult(409,'duplicate_scan_asset')
                seen.add(native)
                if captured is None:
                    if phase!='backfill':raise RuntimeErrorResult(409,'scan_order_conflict')
                    unknown=True;missing+=1
                else:
                    if unknown or (last is not None and captured>last) or ((captured>=boundary)!=(phase=='recent')):
                        raise RuntimeErrorResult(409,'scan_order_conflict')
                    last=captured;first=first or value['capture_time'];end=value['capture_time']
            receipt=self.ingest._append(db,source,run_id,batch_key,sequence,bound,assets,authorized_scan=True)
            for native in seen:
                asset=db.execute('SELECT id FROM assets WHERE connection_id=? AND native_id=?',(source['id'],native)).fetchone()
                db.execute('INSERT INTO scan_assets VALUES(?,?,?)',(run_id,native,asset['id']))
            observed=scan['observed']+len(assets)
            db.execute('''UPDATE scan_runs SET observed=?,accepted=accepted+?,excluded=excluded+?,last_instant=?,unknown_started=?,phase=?,first_capture=?,last_capture=?,missing_date=? WHERE run_id=?''',
                       (observed,receipt['accepted'],receipt['excluded'],last,int(unknown),phase,first,end,missing,run_id))
            receipt.update(observed=observed,expected_count=scan['expected_count'],phase=phase)
            db.execute('UPDATE ingest_batches SET receipt_json=? WHERE run_id=? AND batch_key=?',(canonical(receipt),run_id,batch_key))
            db.execute('UPDATE ingest_runs SET phase=?,checkpoint=? WHERE id=?',(phase,checkpoint,run_id))
            return receipt
        return self.ingest._run('ingest_batch',device_id,credential,commit)

    def finish(self,device_id,credential,run_id):
        def complete(db,source):
            run,scan=self._scan(db,source,run_id)
            if scan['observed']!=scan['expected_count']:raise RuntimeErrorResult(409,'scan_incomplete')
            if run['state']!='complete':
                now=int(self.store.clock())
                db.execute('''UPDATE assets SET scope_authorized=0 WHERE connection_id=? AND NOT EXISTS
                  (SELECT 1 FROM scan_assets s WHERE s.run_id=? AND s.asset_id=assets.id)''',(source['id'],run_id))
                db.execute("UPDATE ingest_runs SET state='complete',completed_at=? WHERE id=?",(now,run_id))
                db.execute('UPDATE ingest_leases SET expires_at=0 WHERE connection_id=?',(source['id'],))
                db.execute("UPDATE operations SET status='complete',completed_at=? WHERE id=?",(now,run_id))
                db.execute("UPDATE connections SET status='scan_indexed',last_success=? WHERE id=?",(dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),source['id']))
                db.execute('UPDATE scan_runs SET retry_requested=0 WHERE run_id=?',(run_id,))
            ready=db.execute('''SELECT count(*) FROM assets a JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
               JOIN asset_media_status m ON m.asset_id=a.id WHERE c.id=? AND m.media_state='ready' AND '''+VISIBLE,(source['id'],)).fetchone()[0]
            return {'run_id':run_id,'state':'complete','coverage':run['coverage'],'observed':scan['observed'],'expected_count':scan['expected_count'],'media_ready':ready}
        return self.ingest._run('ingest_finish',device_id,credential,complete)

    def progress(self,token):
        def read(db,owner):
            result=[]
            rows=db.execute('''SELECT i.*,s.*,c.policy_revision AS current_policy,c.permission AS current_permission
              FROM ingest_runs i JOIN scan_runs s ON s.run_id=i.id JOIN connections c ON c.id=i.connection_id
              WHERE i.owner_id=? ORDER BY i.created_at DESC,i.id DESC LIMIT 50''',(owner['id'],))
            for row in rows:
                item={'run_id':row['id'],'connection_id':row['connection_id'],'state':'restricted'}
                if row['policy_revision']==row['current_policy'] and row['current_permission'] in {'full','limited'}:
                    item.update({key:row[key] for key in ('state','coverage','phase','observed','expected_count','accepted','excluded','first_capture','last_capture','missing_date','created_at','completed_at')})
                    item['retry_requested']=bool(row['retry_requested'])
                result.append(item)
            return {'scans':result}
        return self.store.read(token,'ingest_progress',read)

    def retry(self,token,csrf,run_id):
        def request(db,owner):
            if not isinstance(run_id,str):raise RuntimeErrorResult(400,'invalid_input')
            run=db.execute('''SELECT i.*,c.policy_revision AS current_policy,c.permission AS current_permission FROM ingest_runs i
               JOIN scan_runs s ON s.run_id=i.id JOIN connections c ON c.id=i.connection_id WHERE i.id=? AND i.owner_id=?''',(run_id,owner['id'])).fetchone()
            if run is None:raise RuntimeErrorResult(404,'not_found')
            if run['policy_revision']!=run['current_policy'] or run['current_permission'] not in {'full','limited'}:raise RuntimeErrorResult(403,'selection_revoked')
            if run['state']=='complete':return {'run_id':run_id,'state':'complete'},owner['id']
            db.execute('UPDATE scan_runs SET retry_requested=1 WHERE run_id=?',(run_id,))
            db.execute("UPDATE operations SET status='waiting_for_device' WHERE id=?",(run_id,))
            return {'run_id':run_id,'state':'waiting_for_device'},owner['id']
        return self.ingest.pairing._run('ingest_retry',request,token=token,csrf=csrf,owner_required=True,mutate=True)
