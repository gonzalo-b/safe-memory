"""Bounded metadata imports. Source identity and policy are checked in each transaction."""
from __future__ import annotations
import datetime as dt
import hmac
import json
import re
from runtime.pairing import PairingService, _secret, _text
from runtime.store import RuntimeErrorResult, digest, identifier

MAX_BATCH=2*1024*1024
LEASE_SECONDS=900

def choice(value,allowed):return isinstance(value,str) and value in allowed

def canonical(value):
    try:return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    except (ValueError,TypeError,RecursionError):raise RuntimeErrorResult(400,'invalid_input')

def instant(value):
    if value is None:return None
    if (not isinstance(value,str) or len(value)>64 or value.endswith('-00:00') or not re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',value)):
        raise RuntimeErrorResult(400,'invalid_time')
    if not value.endswith('Z') and (int(value[-5:-3])>23 or int(value[-2:])>59):
        raise RuntimeErrorResult(400,'invalid_time')
    try:
        result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:raise ValueError()
        return result.timestamp()
    except (ValueError,OverflowError):raise RuntimeErrorResult(400,'invalid_time')

def eligible(connection,hidden,collection):
    if hidden and not connection['include_hidden']:return False
    return {'personal':True,'shared_library':bool(connection['include_shared_library']),
            'shared_album':bool(connection['include_shared_albums']),
            'unknown':bool(connection['include_shared_library'] and connection['include_shared_albums'])}.get(collection,False)

def restrictive_collection(left,right):
    if left==right or right=='personal':return left
    if left=='personal':return right
    return 'unknown'

VISIBLE="""c.permission IN ('full','limited') AND a.scope_authorized=1 AND a.current_revision IS NOT NULL
 AND (a.hidden=0 OR c.include_hidden=1)
 AND (a.collection='personal' OR (a.collection='shared_library' AND c.include_shared_library=1)
 OR (a.collection='shared_album' AND c.include_shared_albums=1)
 OR (a.collection='unknown' AND c.include_shared_library=1 AND c.include_shared_albums=1))"""

class IngestionService:
    def __init__(self,store):self.store=store;self.pairing=PairingService(store)

    def _device(self,db,device_id,credential):
        if not isinstance(device_id,str) or not _secret(credential):raise RuntimeErrorResult(401,'unauthorized')
        row=db.execute('''SELECT c.*,d.id AS device_id,d.credential_hash FROM devices d
          JOIN owners o ON o.id=d.owner_id JOIN connections c ON c.id=d.connection_id AND c.owner_id=d.owner_id
          WHERE d.id=? AND d.revoked_at IS NULL AND d.auth_epoch=o.auth_epoch''',(device_id,)).fetchone()
        if row is None or not hmac.compare_digest(row['credential_hash'],digest(credential)):
            raise RuntimeErrorResult(401,'unauthorized')
        return row

    def _run(self,action,device_id,credential,operation):
        def perform(db,_):
            source=self._device(db,device_id,credential)
            return operation(db,source),source['owner_id']
        return self.pairing._run(action,perform)

    def _invalidate(self,db,connection_id,clear_scope=False):
        if clear_scope:db.execute('UPDATE assets SET scope_authorized=0 WHERE connection_id=?',(connection_id,))
        db.execute("UPDATE operations SET status='interrupted' WHERE id IN (SELECT id FROM ingest_runs WHERE connection_id=? AND state='active')",(connection_id,))
        db.execute("UPDATE ingest_runs SET state='interrupted' WHERE connection_id=? AND state='active'",(connection_id,))
        db.execute('UPDATE ingest_leases SET expires_at=0 WHERE connection_id=?',(connection_id,))

    def configure(self,token,csrf,connection_id,include_hidden,include_shared_library,include_shared_albums):
        def change(db,owner):
            if any(type(v) is not bool for v in (include_hidden,include_shared_library,include_shared_albums)):
                raise RuntimeErrorResult(400,'invalid_input')
            if not isinstance(connection_id,str) or not db.execute('SELECT id FROM connections WHERE id=? AND owner_id=?',(connection_id,owner['id'])).fetchone():
                raise RuntimeErrorResult(404,'not_found')
            db.execute('UPDATE connections SET include_hidden=?,include_shared_library=?,include_shared_albums=?,policy_revision=policy_revision+1 WHERE id=?',
                       (include_hidden,include_shared_library,include_shared_albums,connection_id))
            self._invalidate(db,connection_id)
            return {'ok':True},owner['id']
        return self.pairing._run('source_policy',change,token=token,csrf=csrf,owner_required=True,mutate=True)

    def begin(self,device_id,credential,request_key,permission,phase,selected_ids):
        def start(db,source):
            if (not _text(request_key,128) or not choice(permission,{'full','limited'}) or not choice(phase,{'recent','backfill'})
                or not isinstance(selected_ids,list) or not 1<=len(selected_ids)<=100
                or any(not _text(value,256) for value in selected_ids) or len(set(selected_ids))!=len(selected_ids)):
                raise RuntimeErrorResult(400,'invalid_input')
            now=int(self.store.clock());request_hash=digest(canonical([permission,phase,sorted(selected_ids)]))
            previous=db.execute('SELECT * FROM ingest_runs WHERE connection_id=? AND request_key=?',(source['id'],request_key)).fetchone()
            if previous and (previous['request_digest']!=request_hash or previous['device_id']!=device_id):raise RuntimeErrorResult(409,'replay_conflict')
            if previous and previous['policy_revision']!=source['policy_revision']:raise RuntimeErrorResult(403,'selection_revoked')
            run_id=previous['id'] if previous else identifier()
            lease=db.execute('SELECT * FROM ingest_leases WHERE connection_id=?',(source['id'],)).fetchone()
            if lease and lease['run_id']!=run_id and lease['expires_at']>now:raise RuntimeErrorResult(409,'ingest_busy')
            if previous and source['permission'] not in {'full','limited'}:raise RuntimeErrorResult(403,'source_reauthorization_required')
            if previous and previous['state']=='complete':return {'run_id':run_id,'next_sequence':previous['next_sequence'],'state':'complete','coverage':previous['coverage']}
            if lease and lease['run_id']!=run_id:
                db.execute("UPDATE ingest_runs SET state='interrupted' WHERE id=? AND state='active'",(lease['run_id'],))
                db.execute("UPDATE operations SET status='interrupted' WHERE id=?",(lease['run_id'],))
            if not previous:
                db.execute('''INSERT INTO ingest_runs(id,owner_id,connection_id,device_id,request_key,request_digest,phase,permission,policy_revision,selected_json,coverage,state,created_at)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?,'active',?)''',
                           (run_id,source['owner_id'],source['id'],device_id,request_key,request_hash,phase,permission,source['policy_revision']+1,canonical(selected_ids),'bounded_authorized_sample',now))
                db.execute("INSERT INTO operations(id,owner_id,action,status,created_at) VALUES(?,?,?,'running',?)",(run_id,source['owner_id'],'ingest_'+phase,now))
                if permission=='limited' or source['permission']!=permission:
                    db.execute('UPDATE assets SET scope_authorized=0 WHERE connection_id=?',(source['id'],))
                db.execute("UPDATE connections SET permission=?,status='indexing',policy_revision=policy_revision+1 WHERE id=?",(permission,source['id']))
            else:
                db.execute("UPDATE ingest_runs SET state='active' WHERE id=?",(run_id,))
                db.execute("UPDATE operations SET status='running' WHERE id=?",(run_id,))
            db.execute('INSERT INTO ingest_leases VALUES(?,?,?) ON CONFLICT(connection_id) DO UPDATE SET run_id=excluded.run_id,expires_at=excluded.expires_at',(source['id'],run_id,now+LEASE_SECONDS))
            return {'run_id':run_id,'next_sequence':previous['next_sequence'] if previous else 0,'state':'active','coverage':'bounded_authorized_sample'}
        return self._run('ingest_begin',device_id,credential,start)

    def _active(self,db,source,run_id,allow_complete=False):
        if not isinstance(run_id,str):raise RuntimeErrorResult(400,'invalid_input')
        row=db.execute('SELECT * FROM ingest_runs WHERE id=? AND connection_id=? AND device_id=?',(run_id,source['id'],source['device_id'])).fetchone()
        if row is None:raise RuntimeErrorResult(404,'not_found')
        if row['policy_revision']!=source['policy_revision']:raise RuntimeErrorResult(403,'selection_revoked')
        if source['permission'] not in {'full','limited'}:raise RuntimeErrorResult(403,'source_restricted')
        if allow_complete and row['state']=='complete':return row
        lease=db.execute('SELECT * FROM ingest_leases WHERE connection_id=?',(source['id'],)).fetchone()
        if row['state']!='active' or not lease or lease['run_id']!=run_id or lease['expires_at']<=int(self.store.clock()):
            raise RuntimeErrorResult(409,'lease_expired')
        return row

    def _validate(self,value):
        required={'native_id','source_revision','media_type','hidden','collection','capture_time','time_basis','owner_presence','source_modified','metadata'}
        if (not isinstance(value,dict) or set(value)!=required or not _text(value['native_id'],256)
            or not _text(value['source_revision'],256) or not choice(value['media_type'],{'photo','video','live'})
            or type(value['hidden']) is not bool or not choice(value['collection'],{'personal','shared_library','shared_album','unknown'})
            or not choice(value['time_basis'],{'capture_offset','instant_only','unknown'})
            or not choice(value['owner_presence'],{'owner','third_party','unknown'}) or not isinstance(value['metadata'],dict)):
            raise RuntimeErrorResult(400,'invalid_asset')
        captured=instant(value['capture_time']);modified=instant(value['source_modified'])
        if (captured is None)!=(value['time_basis']=='unknown'):raise RuntimeErrorResult(400,'invalid_time_basis')
        return captured,modified

    def append(self,device_id,credential,run_id,batch_key,sequence,checkpoint,assets):
        def commit(db,source):
            return self._append(db,source,run_id,batch_key,sequence,checkpoint,assets)
        return self._run('ingest_batch',device_id,credential,commit)

    def _append(self,db,source,run_id,batch_key,sequence,checkpoint,assets,*,authorized_scan=False):
        run=self._active(db,source,run_id,allow_complete=True)
        if not authorized_scan and run['coverage']!='bounded_authorized_sample':raise RuntimeErrorResult(400,'scan_endpoint_required')
        if (not _text(batch_key,128) or type(sequence) is not int or sequence<0 or not isinstance(checkpoint,str) or len(checkpoint)>2048
            or not isinstance(assets,list) or not 1<=len(assets)<=100):raise RuntimeErrorResult(400,'invalid_batch')
        payload=canonical([sequence,checkpoint,assets])
        if len(payload.encode())>MAX_BATCH:raise RuntimeErrorResult(413,'too_large')
        payload_hash=digest(payload)
        prior=db.execute('SELECT * FROM ingest_batches WHERE run_id=? AND batch_key=?',(run_id,batch_key)).fetchone()
        if prior:
            if prior['payload_digest']!=payload_hash:raise RuntimeErrorResult(409,'replay_conflict')
            return json.loads(prior['receipt_json'])
        if run['state']!='active':raise RuntimeErrorResult(409,'run_complete')
        if sequence!=run['next_sequence']:raise RuntimeErrorResult(409,'checkpoint_conflict')
        selected=set(json.loads(run['selected_json']));seen=set();admitted=[];excluded=0;now=int(self.store.clock())
        for value in assets:
            captured,modified=self._validate(value);native=value['native_id']
            if (not authorized_scan and native not in selected) or native in seen:raise RuntimeErrorResult(400,'outside_selected_scope')
            seen.add(native)
            existing=db.execute('SELECT * FROM assets WHERE connection_id=? AND native_id=?',(source['id'],native)).fetchone()
            permitted=eligible(source,value['hidden'],value['collection'])
            asset_id=existing['id'] if existing else identifier();asset_hash=digest(canonical(value))
            if not existing:
                db.execute('''INSERT INTO assets(id,owner_id,connection_id,native_id,hidden,collection,scope_authorized,first_seen,last_seen)
                              VALUES(?,?,?,?,?,?,1,?,?)''',(asset_id,source['owner_id'],source['id'],native,value['hidden'],value['collection'],now,now))
            observation=db.execute('SELECT * FROM asset_observations WHERE asset_id=? AND source_revision=?',(asset_id,value['source_revision'])).fetchone()
            if observation and observation['payload_digest']!=asset_hash:raise RuntimeErrorResult(409,'source_revision_conflict')
            observed=db.execute('SELECT max(source_modified) FROM asset_observations WHERE asset_id=?',(asset_id,)).fetchone()[0]
            stale=modified is not None and observed is not None and modified<observed
            ordinal=observation['sequence'] if observation else db.execute('INSERT INTO asset_observations(asset_id,source_revision,payload_digest,source_modified) VALUES(?,?,?,?)',
                (asset_id,value['source_revision'],asset_hash,modified)).lastrowid
            last=existing['last_observation'] if existing else 0
            uncertain=bool(existing and existing['restriction_uncertain']) or (modified is None and (value['hidden'] or value['collection']!='personal'))
            if uncertain:db.execute('UPDATE assets SET restriction_uncertain=1 WHERE id=?',(asset_id,))
            if ordinal>last and not stale:
                hidden,collection=value['hidden'],value['collection']
                can_relax=not uncertain and modified is not None and observed is not None and modified>observed
                if existing and not can_relax:
                    hidden=existing['hidden'] or hidden
                    collection=restrictive_collection(existing['collection'],collection)
                db.execute('UPDATE assets SET hidden=?,collection=?,last_observation=?,last_seen=? WHERE id=?',(hidden,collection,ordinal,now,asset_id))
            elif not observation and stale and existing and (value['hidden'] or value['collection']!='personal'):
                # A newly detected restriction is retained even when source clocks disagree.
                collection=restrictive_collection(existing['collection'],value['collection'])
                db.execute('UPDATE assets SET hidden=?,collection=?,last_observation=?,last_seen=? WHERE id=?',
                           (existing['hidden'] or value['hidden'],collection,ordinal,now,asset_id))
            if not permitted:excluded+=1;continue
            previous=db.execute('SELECT * FROM asset_revisions WHERE asset_id=? AND source_revision=?',(asset_id,value['source_revision'])).fetchone()
            if previous and previous['payload_digest']!=asset_hash:raise RuntimeErrorResult(409,'source_revision_conflict')
            revision=previous['revision'] if previous else db.execute('SELECT COALESCE(max(revision),0)+1 FROM asset_revisions WHERE asset_id=?',(asset_id,)).fetchone()[0]
            if not previous:
                db.execute('INSERT INTO asset_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (asset_id,revision,value['source_revision'],asset_hash,canonical(value['metadata']),value['media_type'],value['capture_time'],value['time_basis'],
                            value['capture_time'][:10] if value['time_basis']=='capture_offset' else None,captured,modified,value['owner_presence'],now))
            if ordinal>=last and not stale:db.execute('UPDATE assets SET current_revision=? WHERE id=?',(revision,asset_id))
            db.execute('UPDATE assets SET scope_authorized=1,last_seen=? WHERE id=?',(now,asset_id))
            admitted.append({'native_id':native,'asset_id':asset_id})
        receipt={'run_id':run_id,'sequence':sequence,'next_sequence':sequence+1,'accepted':len(admitted),'excluded':excluded,'assets':admitted}
        db.execute('INSERT INTO ingest_batches VALUES(?,?,?,?,?,?)',(run_id,batch_key,sequence,payload_hash,canonical(receipt),now))
        db.execute('UPDATE ingest_runs SET next_sequence=?,checkpoint=? WHERE id=?',(sequence+1,checkpoint,run_id))
        db.execute('UPDATE ingest_leases SET expires_at=? WHERE connection_id=?',(now+LEASE_SECONDS,source['id']))
        db.execute('UPDATE connections SET index_count=(SELECT count(*) FROM assets WHERE connection_id=?) WHERE id=?',(source['id'],source['id']))
        return receipt
    def finish(self,device_id,credential,run_id):
        def complete(db,source):
            run=self._active(db,source,run_id,allow_complete=True);now=int(self.store.clock())
            if run['coverage']!='bounded_authorized_sample':raise RuntimeErrorResult(400,'scan_endpoint_required')
            if run['state']!='complete':
                db.execute("UPDATE ingest_runs SET state='complete',completed_at=? WHERE id=?",(now,run_id))
                db.execute('UPDATE ingest_leases SET expires_at=0 WHERE connection_id=?',(source['id'],))
                db.execute("UPDATE operations SET status='complete',completed_at=? WHERE id=?",(now,run_id))
                db.execute("UPDATE connections SET status='sample_indexed',last_success=? WHERE id=?",(dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),source['id']))
            ready=db.execute('SELECT count(*) FROM assets a JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id JOIN asset_media_status m ON m.asset_id=a.id WHERE c.id=? AND m.media_state=\'ready\' AND '+VISIBLE,(source['id'],)).fetchone()[0]
            return {'run_id':run_id,'state':'complete','coverage':run['coverage'],'media_ready':ready}
        return self._run('ingest_finish',device_id,credential,complete)

    def permission(self,device_id,credential,permission):
        def update(db,source):
            if not choice(permission,{'full','limited','denied','revoked'}):raise RuntimeErrorResult(400,'invalid_permission')
            # Positive changes also require a new explicit selection before revealing retained assets.
            self._invalidate(db,source['id'],clear_scope=True)
            db.execute("UPDATE connections SET permission=?,status='selection_required',policy_revision=policy_revision+1 WHERE id=?",(permission,source['id']))
            return {'ok':True}
        return self._run('source_permission',device_id,credential,update)

    def assets(self,token,*,limit=50,offset=0,media_type=None,day=None):
        def read(db,owner):
            if type(limit) is not int or not 1<=limit<=200 or type(offset) is not int or not 0<=offset<=1000000:raise RuntimeErrorResult(400,'invalid_page')
            if media_type is not None and not choice(media_type,{'photo','video','live'}):raise RuntimeErrorResult(400,'invalid_filter')
            if day is not None:
                try:
                    if not isinstance(day,str) or dt.date.fromisoformat(day).isoformat()!=day:raise ValueError()
                except ValueError:raise RuntimeErrorResult(400,'invalid_filter')
            query='''SELECT a.id,a.native_id,a.hidden,a.collection,r.media_type,r.capture_time,r.time_basis,r.capture_day,r.owner_presence,r.raw_json,
              (SELECT f.revision FROM knowledge_facts f JOIN knowledge_generations g ON g.id=f.generation_id
               WHERE g.owner_id=a.owner_id AND g.current=1 AND f.asset_id=a.id AND f.revision=a.current_revision) AS evidence_revision,
              (SELECT media_state FROM asset_media_status m WHERE m.asset_id=a.id) AS media_state FROM current_asset_index x JOIN assets a ON a.id=x.asset_id AND a.owner_id=x.owner_id AND a.current_revision=x.revision JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
              JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision WHERE x.owner_id=? AND '''+VISIBLE
            args=[owner['id']]
            if media_type is not None:query+=' AND x.media_type=?';args.append(media_type)
            if day is not None:query+=' AND x.capture_day=?';args.append(day)
            query+=' ORDER BY x.capture_instant DESC,x.asset_id LIMIT ? OFFSET ?';args.extend([limit,offset])
            scans=db.execute('''SELECT i.id FROM ingest_runs i JOIN scan_runs s ON s.run_id=i.id
              JOIN connections c ON c.id=i.connection_id WHERE i.owner_id=? AND i.policy_revision=c.policy_revision
              AND c.permission IN ('full','limited') LIMIT 1''',(owner['id'],)).fetchone()
            restricted=db.execute("SELECT 1 FROM connections WHERE owner_id=? AND permission IN ('revoked','denied') LIMIT 1",(owner['id'],)).fetchone()
            mode='progressive' if scans else 'restricted_or_unknown' if restricted else 'selected_samples'
            # Bounded current-revision metadata only. Reuse the knowledge coordinate
            # validator; never infer geography from coordinates or return raw JSON.
            from blocks.trips import _coordinates
            rows=[]
            for row in db.execute(query,args):
                item=dict(row);raw=json.loads(item.pop('raw_json'))
                location=raw.get('location');location=location if isinstance(location,dict) else {}
                try:point=_coordinates({'lat':location.get('latitude',location.get('lat')),'lon':location.get('longitude',location.get('lon'))})
                except OverflowError:point=None
                item['location']={'lat':point[0],'lon':point[1]} if point else {}
                if _text(location.get('place'),200):item['location']['place']=location['place']
                geography=raw.get('geography');geography=geography if isinstance(geography,dict) else {}
                item['geography']={key:geography[key] for key in ('country_code','country','city_id','city') if _text(geography.get(key),200)}
                revision=item.pop('evidence_revision')
                item['evidence']={'asset_id':item['id'],'revision':revision} if revision is not None else None
                rows.append(item)
            return {'assets':rows,'coverage':{'mode':mode},'fixture':self.store.fixture}
        return self.store.read(token,'assets',read)
