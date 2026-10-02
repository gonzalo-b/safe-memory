"""Indexed owner knowledge with current-policy projection and retained corrections.

No network, model, source writes or answer cache. Stored facts are not permission.
"""
from __future__ import annotations
import base64
import calendar
import datetime as dt
import hashlib
import hmac
import html
import json
import math
import re
from dataclasses import asdict
from blocks.capabilities import _date, _month_day, Capabilities, LEAP_POLICIES
from blocks.trips import TripPolicy, _coordinates, _distance
from runtime.ingestion import VISIBLE, canonical
from runtime.pairing import PairingService, _text
from runtime.store import RuntimeErrorResult, digest, identifier

DEFINITION='indexed-photos-1'
FIELDS={'id','capture_time','location','geography','media_type','owner_presence','people'}
CAPABILITIES=('travel.where_on_date','travel.where_in_range','travel.where_in_year','travel.countries_visited','travel.cities_visited','photos.statistics','photos.on_this_day','travel.occasion_history','photos.records')

def invalid():raise RuntimeErrorResult(400,'invalid_input')
def date(value):
    try:return _date(value).isoformat()
    except (ValueError,TypeError):invalid()
def text(value,maximum=200):return value if _text(value,maximum) else None

def scope_value(value):
    if value is None:value={}
    if not isinstance(value,dict) or set(value)-{'connection_ids','start','end','fields'}:invalid()
    result=dict(value)
    if 'fields' in result:
        fields=result['fields']
        if not isinstance(fields,list) or any(not isinstance(x,str) or x not in FIELDS for x in fields):invalid()
        result['fields']=sorted(set(fields))
    else:result['fields']=sorted(FIELDS)
    if 'connection_ids' in result:
        ids=result['connection_ids']
        if not isinstance(ids,list) or len(ids)>100 or any(not isinstance(x,str) or not re.fullmatch('[a-f0-9]{32}',x) for x in ids):invalid()
        result['connection_ids']=sorted(set(ids))
    for field in ('start','end'):
        if field in result:result[field]=date(result[field])
    if result.get('start') and result.get('end') and result['start']>=result['end']:invalid()
    return result

class KnowledgeService:
    def __init__(self,store):self.store=store;self.pairing=PairingService(store)
    def _write(self,token,csrf,action,operation):
        return self.pairing._run(action,lambda db,owner:(operation(db,owner),owner['id']),token=token,csrf=csrf,owner_required=True,mutate=True)
    def _request(self,db,owner,key,payload):
        if not text(key,128):invalid()
        hashed=digest(canonical(payload));old=db.execute('SELECT * FROM knowledge_requests WHERE owner_id=? AND request_key=?',(owner['id'],key)).fetchone()
        if old and old['digest']!=hashed:raise RuntimeErrorResult(409,'request_conflict')
        return hashed,json.loads(old['result_json']) if old else None
    def _receipt(self,db,owner,key,hashed,result):db.execute('INSERT INTO knowledge_requests VALUES(?,?,?,?)',(owner['id'],key,hashed,canonical(result)))
    def _generation(self,db,owner):return db.execute('SELECT * FROM knowledge_generations WHERE owner_id=? AND current=1',(owner['id'],)).fetchone()
    def _source_where(self,scope,alias='a'):
        clauses=[];params=[]
        if 'connection_ids' in scope:
            clauses.append(alias+'.connection_id IN ('+','.join('?' for _ in scope['connection_ids'])+')');params.extend(scope['connection_ids'])
        for field,operator in [('start','>='),('end','<')]:
            if field in scope:clauses.append('r.capture_day'+operator+'?');params.append(scope[field])
        return ''.join(' AND '+clause for clause in clauses),params
    def _project(self,db,owner,scope):
        generation=self._generation(db,owner);fields=set(scope['fields']);extra,args=self._source_where(scope)
        columns=['f.asset_id AS _asset_id','f.revision AS _revision','f.signature AS _signature','a.connection_id AS _connection_id']
        for group,names in {'capture_time':['capture_time','capture_day','month_day','capture_instant'],'location':['lat','lon','place'],'geography':['country_code','country','city_id','city'],'media_type':['media_type'],'owner_presence':['owner_presence'],'people':['people_json']}.items():
            columns += [('f.'+name if group in fields else 'NULL')+' AS '+name for name in names]
        sql='WITH p AS (SELECT '+','.join(columns)+''' FROM knowledge_facts f
        JOIN assets a ON a.id=f.asset_id AND a.current_revision=f.revision
        JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
        WHERE f.generation_id=? AND a.owner_id=? AND '''+VISIBLE+extra.replace('r.capture_day','f.capture_day')+') '
        return sql,[generation['id'] if generation else '',owner['id'],*args],generation
    def _coverage(self,db,owner,scope,base,args,generation):
        # One live-policy scan for exact coverage, rather than independent scans
        # for indexed and unindexed counts. No generation count is authorization.
        fields=set(scope['fields']);day='f.capture_day' if 'capture_time' in fields else 'NULL'
        located='(f.lat IS NOT NULL OR f.place IS NOT NULL)' if 'location' in fields else '0'
        extra,source_args=self._source_where(scope)
        dated='start' in scope or 'end' in scope
        revision_join=' JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision ' if dated else ' '
        row=db.execute('SELECT count(f.asset_id) AS indexed_records,coalesce(sum(f.asset_id IS NOT NULL AND '+day+' IS NULL),0) AS unknown_time_records,coalesce(sum(f.asset_id IS NOT NULL AND '+located+'),0) AS located_records,min('+day+') AS first_observed_day,max('+day+') AS last_observed_day,coalesce(sum(f.asset_id IS NULL),0) AS unindexed_current_records FROM assets a JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id'+revision_join+'LEFT JOIN knowledge_facts f ON f.asset_id=a.id AND f.revision=a.current_revision AND f.generation_id=? WHERE a.owner_id=? AND '+VISIBLE+extra,[generation['id'] if generation else '',owner['id'],*source_args]).fetchone()
        return {'scope':'current_authorized_sample','whole_library':False,**dict(row),'excluded_records':None,'excluded_basis':'not_disclosed'}
    def _state(self,db,owner):
        sources=[tuple(row) for row in db.execute('SELECT id,policy_revision,permission FROM connections WHERE owner_id=? ORDER BY id',(owner['id'],))]
        latest=db.execute('SELECT max(last_observation),count(*) FROM assets WHERE owner_id=?',(owner['id'],)).fetchone()
        trips=db.execute('SELECT coalesce(sum(revision),0) FROM knowledge_trips WHERE owner_id=?',(owner['id'],)).fetchone()[0]
        areas=db.execute('SELECT coalesce(sum(revision),0) FROM knowledge_areas WHERE owner_id=?',(owner['id'],)).fetchone()[0]
        return [sources,tuple(latest),trips,areas]
    def _page(self,db,owner,token,generation,scope,query,limit,cursor):
        if type(limit) is not int or not 1<=limit<=200:invalid()
        key=digest(canonical([owner['id'],generation['id'] if generation else None,scope,query,limit,self._state(db,owner)]));offset=0
        if cursor is not None:
            try:
                body,signature=cursor.split('.')
                if not hmac.compare_digest(signature,hmac.new(token.encode(),body.encode(),'sha256').hexdigest()):raise ValueError()
                value=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
                if value['key']!=key:raise RuntimeErrorResult(409,'stale_cursor')
                offset=value['offset']
                if type(offset) is not int or not 0<=offset<=1000000:raise ValueError()
            except (ValueError,TypeError,KeyError,AttributeError):invalid()
        def following(more):
            if not more:return None
            body=base64.urlsafe_b64encode(canonical({'key':key,'offset':offset+limit}).encode()).decode().rstrip('=')
            return body+'.'+hmac.new(token.encode(),body.encode(),'sha256').hexdigest()
        return offset,following
    def _fact(self,row,fields):
        value={'capture_time':row['capture_time'],'capture_day':row['capture_day'],'time_basis':'source_offset_local_day' if row['capture_day'] else 'unknown_local_day','location':{k:row[k] for k in ('lat','lon','place') if row[k] is not None},'geography':{k:row[k] for k in ('country_code','country','city_id','city') if row[k] is not None},'media_type':row['media_type'],'owner_presence':row['owner_presence'] or 'unknown','continuous_presence':False}
        if 'id' in fields:value['evidence']={'asset_id':row['_asset_id'],'revision':row['_revision'],'connection_id':row['_connection_id']}
        if 'people' in fields:value['people']=json.loads(row['people_json'] or '[]')
        return value
    def _envelope(self,cap,generation,coverage,data,status=None,next_cursor=None):
        if status is None:status='no_evidence' if not data else 'partial' if coverage['unknown_time_records'] or coverage['unindexed_current_records'] else 'ok'
        rendered=self._markdown(data)
        return {'capability':cap,'definition_version':DEFINITION,'generation':generation['id'] if generation else None,'status':status,'data':data,'next_cursor':next_cursor,'time_basis':'source_offset_local_day_unknown_if_instant_only','counting_rule':'distinct_explicit_geography_ids_in_projected_media_not_owner_presence' if cap in ('travel.countries_visited','travel.cities_visited') else 'calendar_occurrences_including_unknown_years' if cap=='travel.occasion_history' else 'one_current_authorized_asset_not_derivative_place_rows','coverage':coverage,'freshness':{'built_at':generation['built_at'] if generation else None,'stale':bool(coverage['unindexed_current_records']),'source_check':'unknown'},'markdown':'## '+cap+'\n\n'+rendered+'\n','limitations':['selected_sample_not_whole_library','observations_not_continuous_owner_presence']}
    def _markdown(self,data):
        def safe(value):
            value=html.escape(str(value if value is not None else 'unknown'))
            return re.sub(r'([\\`*_{}\[\]()#+.!|>~-])',r'\\\1',value).replace('\n',' ').replace('\r',' ')
        if isinstance(data,dict):return '\n'.join('- '+safe(key.replace('_',' '))+': '+safe(value) for key,value in data.items())
        if not data:return 'No admissible observations for this query.'
        lines=[]
        for row in data:
            if 'capture_day' in row:
                place=row.get('location',{}).get('place') or ', '.join(str(row.get('location',{}).get(key,'unknown')) for key in ('lat','lon'))
                evidence=row.get('evidence',{}).get('asset_id','unavailable')
                lines.append('- '+safe(row['capture_day'])+' — '+safe(place)+'; '+safe(row.get('media_type'))+'; evidence '+safe(evidence)+'. Owner presence: '+safe(row.get('owner_presence'))+'.')
            elif 'observation_count' in row:lines.append('- '+safe(row['date'])+': '+safe(row['status'])+' ('+str(row['observation_count'])+' observations).')
            else:lines.append('- '+safe(row.get('label') or row.get('country_code') or row.get('city_id'))+': '+str(row.get('records',0))+' observations; '+str(row.get('observed_days',0))+' observed local days.')
        return '\n'.join(lines)+'\n\nCoverage: current authorized sample; observations do not establish continuous owner presence.'
    def _normalized(self,row):
        raw=json.loads(row['raw_json']);raw=raw if isinstance(raw,dict) else {}
        location=raw.get('location');location=location if isinstance(location,dict) else {}
        point=_coordinates({'lat':location.get('latitude',location.get('lat')),'lon':location.get('longitude',location.get('lon'))})
        geo=raw.get('geography');geo=geo if isinstance(geo,dict) else {}
        people=[]
        if raw.get('people_provenance')=='source_imported' and isinstance(raw.get('people'),list):
            for value in raw['people']:
                if isinstance(value,dict) and text(value.get('source_id')) and text(value.get('name')):people.append({'source_id':value['source_id'],'name':value['name']})
                if len(people)>200:raise RuntimeErrorResult(413,'people_index_too_large')
        day=row['capture_day'] if row['time_basis']=='capture_offset' else None
        values=[row['asset_id'],row['revision'],row['capture_time'],day,day[5:] if day else None,row['capture_instant'],row['media_type'],point[0] if point else None,point[1] if point else None,text(location.get('place')),text(geo.get('country_code')),text(geo.get('country')),text(geo.get('city_id')),text(geo.get('city')),row['owner_presence'],canonical(people)]
        return values+[digest(canonical(values[2:]))]
    def rebuild(self,token,csrf,request_key,*,policy=None):
        def build(db,owner):
            settings={} if policy is None else policy
            if not isinstance(settings,dict) or set(settings)-{'max_gap_hours','max_leg_km','min_observations','habitual_min_days'}:invalid()
            try:trip_policy=TripPolicy(**{k:v for k,v in settings.items() if k!='habitual_min_days'})
            except (TypeError,ValueError):invalid()
            minimum=settings.get('habitual_min_days',14)
            if type(minimum) is not int or not 2<=minimum<=366:invalid()
            hashed,prior=self._request(db,owner,request_key,['rebuild',settings])
            if prior:return prior
            generation=identifier();now=int(self.store.clock())
            db.execute('INSERT INTO knowledge_generations VALUES(?,?,?,?,?,0)',(generation,owner['id'],DEFINITION,canonical({**asdict(trip_policy),'habitual_min_days':minimum}),now))
            for row in db.execute('''SELECT r.* FROM assets a JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id WHERE a.owner_id=? AND '''+VISIBLE+' ORDER BY a.id',(owner['id'],)):
                db.execute('INSERT INTO knowledge_facts VALUES('+','.join('?' for _ in range(18))+')',[generation,*self._normalized(row)])
            self._suggest(db,owner,generation,minimum)
            self._detect(db,owner,generation,trip_policy)
            db.execute('UPDATE knowledge_generations SET current=0 WHERE owner_id=? AND current=1',(owner['id'],));db.execute('UPDATE knowledge_generations SET current=1 WHERE id=?',(generation,))
            db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?)',(generation,owner['id'],'knowledge_rebuild','complete',now,now))
            result={'generation':generation,'definition_version':DEFINITION,'built_at':now};self._receipt(db,owner,request_key,hashed,result);return result
        return self._write(token,csrf,'knowledge_rebuild',build)
    def catalog(self,token,*,scope=None):
        def read(db,owner):
            sc=scope_value(scope);base,args,generation=self._project(db,owner,sc);coverage=self._coverage(db,owner,sc,base,args,generation)
            people=db.execute(base+"SELECT count(*) FROM p WHERE people_json IS NOT NULL AND people_json!='[]'",args).fetchone()[0]
            return {'capabilities':list(CAPABILITIES),'definition_version':DEFINITION,'generation':generation['id'] if generation else None,'coverage':coverage,'people':'source_metadata_available' if people else 'unavailable','status':'no_evidence' if not coverage['indexed_records'] else 'partial'}
        return self.store.read(token,'knowledge_read',read)
    def evidence(self,token,asset_id,*,scope=None):
        def read(db,owner):
            sc=scope_value(scope);base,args,_=self._project(db,owner,sc)
            if 'id' not in sc['fields'] or not isinstance(asset_id,str):raise RuntimeErrorResult(404,'not_found')
            row=db.execute(base+'SELECT * FROM p WHERE _asset_id=?',args+[asset_id]).fetchone()
            if row is None:raise RuntimeErrorResult(404,'not_found')
            return self._fact(row,sc['fields'])
        return self.store.read(token,'knowledge_evidence',read)
    def answer(self,token,capability,params=None,*,scope=None,limit=50,cursor=None):
        def read(db,owner):
            if capability not in CAPABILITIES or (params is not None and not isinstance(params,dict)):invalid()
            values=params or {};sc=scope_value(scope);base,args,generation=self._project(db,owner,sc);coverage=self._coverage(db,owner,sc,base,args,generation)
            offset,following=self._page(db,owner,token,generation,sc,[capability,values],limit,cursor)
            allowed={'start','end','country_code','city_id','media_type'}
            filters=[];bindings=[]
            if capability=='travel.where_on_date':allowed={'date'};filters=['capture_day=?'];bindings=[date(values.get('date'))]
            elif capability=='travel.where_in_year':
                allowed={'year'};year=values.get('year')
                if type(year) is not int or not 1<=year<=9999:invalid()
                filters=['capture_day>=?','capture_day<=?'];bindings=[f'{year:04d}-01-01',f'{year:04d}-12-31']
            elif capability=='photos.on_this_day':
                allowed={'month_day'}
                try:_month_day(values.get('month_day'))
                except (ValueError,TypeError):invalid()
                filters=['month_day=?'];bindings=[values['month_day']]
            elif capability=='travel.occasion_history':return self._occasion(db,owner,sc,base,args,generation,coverage,values,limit)
            else:
                for field,op in [('start','>='),('end','<')]:
                    if field in values:filters.append('capture_day'+op+'?');bindings.append(date(values[field]))
                if values.get('start') and values.get('end') and values['start']>=values['end']:invalid()
                for field in ('country_code','city_id','media_type'):
                    if field in values:
                        if not text(values[field]):invalid()
                        filters.append(field+'=?');bindings.append(values[field])
            if set(values)-allowed:invalid()
            if capability=='travel.where_in_range' and not {'start','end'}<=set(values):invalid()
            if capability.startswith('travel.where_'):filters.extend(['capture_day IS NOT NULL','(lat IS NOT NULL OR place IS NOT NULL)'])
            where=' WHERE '+' AND '.join(filters) if filters else ''
            if capability=='photos.statistics':
                row=db.execute(base+'''SELECT count(*) AS records,coalesce(sum(media_type='photo'),0) AS photos,coalesce(sum(media_type='video'),0) AS videos,coalesce(sum(media_type='live'),0) AS live_photos,coalesce(sum(media_type IS NULL),0) AS unknown_type,coalesce(sum(capture_day IS NULL),0) AS unknown_time, count(DISTINCT capture_day) AS observed_days FROM p'''+where,args+bindings).fetchone();data=dict(row)
                return self._envelope(capability,generation,coverage,data,'no_evidence' if not data['records'] else 'partial' if data['unknown_time'] or data['unknown_type'] else 'ok')
            if capability in ('travel.countries_visited','travel.cities_visited'):
                country=capability=='travel.countries_visited';key='country_code' if country else 'city_id';label='country' if country else 'city'
                rows=db.execute(base+f'SELECT {key},min({label}) AS label,count(*) AS records,count(DISTINCT capture_day) AS observed_days,min(capture_day) AS first_observed_day,max(capture_day) AS last_observed_day FROM p'+where+(' AND ' if where else ' WHERE ')+key+' IS NOT NULL GROUP BY '+key+' ORDER BY '+key+' LIMIT ? OFFSET ?',args+bindings+[limit+1,offset]).fetchall()
                data=[{**dict(row),'evidence_query':{'capability':'photos.records','params':{**values,key:row[key]}}} for row in rows[:limit]]
            else:
                rows=db.execute(base+'SELECT * FROM p'+where+' ORDER BY capture_day IS NULL,capture_day,_asset_id LIMIT ? OFFSET ?',args+bindings+[limit+1,offset]).fetchall();data=[self._fact(row,sc['fields']) for row in rows[:limit]]
            return self._envelope(capability,generation,coverage,data,next_cursor=following(len(rows)>limit))
        return self.store.read(token,'knowledge_read',read)
    def _occasion(self,db,owner,scope,base,args,generation,coverage,values,limit):
        if set(values)-{'month_day','count','as_of','leap_day_policy'}:invalid()
        try:template=Capabilities([]).occasion_history(values.get('month_day'),values.get('count'),values.get('as_of'),leap_day_policy=values.get('leap_day_policy','leap_years_only'))
        except (ValueError,TypeError):invalid()
        data=[];remaining=limit
        for occurrence in template['data']:
            day=occurrence['date'];count=db.execute(base+'SELECT count(*) FROM p WHERE capture_day=? AND (lat IS NOT NULL OR place IS NOT NULL)',args+[day]).fetchone()[0]
            rows=db.execute(base+'SELECT * FROM p WHERE capture_day=? AND (lat IS NOT NULL OR place IS NOT NULL) ORDER BY _asset_id LIMIT ?',args+[day,remaining]).fetchall();remaining-=len(rows)
            data.append({'date':day,'status':'observed' if count else 'unknown','observation_count':count,'observations':[self._fact(row,scope['fields']) for row in rows],'evidence_query':{'capability':'travel.where_on_date','params':{'date':day}},'has_more':count>len(rows)})
        result=self._envelope('travel.occasion_history',generation,coverage,data,'needs_input' if template['status']=='needs_input' else 'partial' if any(row['status']=='unknown' for row in data) else 'ok');result['leap_day_policy']=values.get('leap_day_policy','leap_years_only')
        if template.get('required_input'):result['required_input']=template['required_input']
        return result
    def _area_admitted(self,db,owner,area,generation=None):
        if generation is None:
            current=self._generation(db,owner);generation=current['id'] if current else ''
        total=db.execute('SELECT count(*) FROM knowledge_area_members WHERE area_id=? AND area_revision=?',(area['id'],area['revision'])).fetchone()[0]
        valid=db.execute('''SELECT count(*) FROM knowledge_area_members m JOIN knowledge_facts f ON f.asset_id=m.asset_id AND f.signature=m.evidence_signature
          JOIN assets a ON a.id=f.asset_id AND a.current_revision=f.revision JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
          WHERE m.area_id=? AND m.area_revision=? AND f.generation_id=? AND a.owner_id=? AND '''+VISIBLE,(area['id'],area['revision'],generation,owner['id'])).fetchone()[0]
        return total==valid
    def _areas(self,db,owner,generation=None):
        for row in db.execute('SELECT a.*,r.label,r.lat,r.lon,r.radius_km,r.start,r.end,r.confirmed FROM knowledge_areas a JOIN knowledge_area_revisions r ON r.area_id=a.id AND r.revision=a.revision WHERE a.owner_id=? ORDER BY a.id',(owner['id'],)):
            if self._area_admitted(db,owner,row,generation):yield dict(row)
    def habitual_areas(self,token,*,limit=50,cursor=None):
        def read(db,owner):
            generation=self._generation(db,owner);offset,following=self._page(db,owner,token,generation,{},['areas'],limit,cursor)
            # Filter before pagination; only small typed area rows are traversed.
            values=[];seen=0
            for area in self._areas(db,owner):
                if seen>=offset:
                    values.append({k:v for k,v in area.items() if k not in {'owner_id','suggestion_key'}})
                    if len(values)>limit:break
                seen+=1
            return {'data':values[:limit],'next_cursor':following(len(values)>limit),'definition_version':DEFINITION}
        return self.store.read(token,'knowledge_area',read)
    def put_habitual_area(self,token,csrf,request_key,area,*,area_id=None,expected_revision=None):
        def write(db,owner):
            if area_id is not None and not isinstance(area_id,str):invalid()
            if not isinstance(area,dict) or set(area)-{'label','lat','lon','radius_km','start','end','confirmed','evidence_ids'}:invalid()
            point=_coordinates(area);start=date(area.get('start'));end=date(area.get('end'));radius=area.get('radius_km')
            if not text(area.get('label')) or point is None or type(area.get('confirmed')) is not bool or isinstance(radius,bool) or not isinstance(radius,(int,float)) or not math.isfinite(radius) or not 0<radius<=1000 or start>=end:invalid()
            hashed,prior=self._request(db,owner,request_key,['area',area_id,expected_revision,area])
            if prior:
                old=db.execute('SELECT * FROM knowledge_areas WHERE id=? AND owner_id=?',(prior['area_id'],owner['id'])).fetchone()
                return prior if old and self._area_admitted(db,owner,old) else {'area_id':None,'status':'unavailable'}
            old=None
            if area_id is not None:
                old=db.execute('SELECT * FROM knowledge_areas WHERE id=? AND owner_id=?',(area_id,owner['id'])).fetchone()
                if old is None:raise RuntimeErrorResult(404,'not_found')
                if type(expected_revision) is not int or old['revision']!=expected_revision:raise RuntimeErrorResult(409,'revision_conflict')
                if not self._area_admitted(db,owner,old):raise RuntimeErrorResult(404,'not_found')
            elif expected_revision is not None:invalid()
            ids=area.get('evidence_ids')
            if ids is not None:self._evidence_ids(db,owner,ids)
            identity=area_id or identifier();revision=old['revision']+1 if old else 1
            if not old:db.execute('INSERT INTO knowledge_areas VALUES(?,?,?,NULL)',(identity,owner['id'],revision))
            else:db.execute('UPDATE knowledge_areas SET revision=? WHERE id=?',(revision,identity))
            db.execute('INSERT INTO knowledge_area_revisions VALUES(?,?,?,?,?,?,?,?,?,?)',(identity,revision,area['label'],*point,radius,start,end,int(area['confirmed']),int(self.store.clock())))
            if ids is not None:self._copy_members(db,owner,'area',identity,revision,ids=ids)
            elif old:self._copy_members(db,owner,'area',identity,revision,previous=(identity,old['revision']))
            result={'area_id':identity,'revision':revision};self._receipt(db,owner,request_key,hashed,result);return result
        return self._write(token,csrf,'knowledge_area',write)
    def _suggest(self,db,owner,generation,minimum):
        groups=db.execute('''SELECT round(lat,1) AS lat,round(lon,1) AS lon,substr(capture_day,1,4) AS year,min(capture_day) AS start,max(capture_day) AS last
          FROM knowledge_facts WHERE generation_id=? AND capture_day IS NOT NULL AND lat IS NOT NULL AND owner_presence!='third_party'
          GROUP BY round(lat,1),round(lon,1),substr(capture_day,1,4) HAVING count(DISTINCT capture_day)>=?''',(generation,minimum))
        for group in groups:
            key=canonical([group['lat'],group['lon'],group['year']]);old=db.execute('SELECT a.*,r.confirmed FROM knowledge_areas a JOIN knowledge_area_revisions r ON r.area_id=a.id AND r.revision=a.revision WHERE a.owner_id=? AND a.suggestion_key=?',(owner['id'],key)).fetchone()
            if old and old['confirmed']:continue
            last=_date(group['last'])
            if last==dt.date.max:continue
            identity=old['id'] if old else identifier();revision=old['revision']+1 if old else 1
            if old:db.execute('UPDATE knowledge_areas SET revision=? WHERE id=?',(revision,identity))
            else:db.execute('INSERT INTO knowledge_areas VALUES(?,?,?,?)',(identity,owner['id'],revision,key))
            db.execute('INSERT INTO knowledge_area_revisions VALUES(?,?,?,?,?,?,?,?,?,?)',(identity,revision,'Suggested area ('+group['year']+')',group['lat'],group['lon'],15,group['start'],(last+dt.timedelta(days=1)).isoformat(),0,int(self.store.clock())))
            db.execute('''INSERT INTO knowledge_area_members SELECT ?,?,asset_id,revision,signature FROM knowledge_facts WHERE generation_id=? AND round(lat,1)=? AND round(lon,1)=? AND substr(capture_day,1,4)=? AND owner_presence!='third_party' ''',(identity,revision,generation,group['lat'],group['lon'],group['year']))
    def _detect(self,db,owner,generation,policy):
        areas=[area for area in self._areas(db,owner,generation) if area['confirmed']]
        db.execute('CREATE TEMP TABLE candidate_staging(group_id INTEGER,asset_id TEXT PRIMARY KEY)')
        db.execute('CREATE INDEX candidate_staging_group ON candidate_staging(group_id,asset_id)')
        group=0;previous=None
        query='''SELECT f.* FROM knowledge_facts f WHERE f.generation_id=? AND f.capture_day IS NOT NULL AND f.lat IS NOT NULL AND f.owner_presence!='third_party'
          AND NOT EXISTS(SELECT 1 FROM knowledge_trip_members m JOIN knowledge_trips t ON t.id=m.trip_id AND t.revision=m.trip_revision WHERE m.asset_id=f.asset_id AND t.owner_id=? AND t.state!='inferred') ORDER BY f.capture_instant,f.asset_id'''
        for row in db.execute(query,(generation,owner['id'])):
            point=(row['lat'],row['lon']);day=row['capture_day']
            if any(area['start']<=day<area['end'] and _distance(point,(area['lat'],area['lon']))<=area['radius_km'] for area in areas):group+=1;previous=None;continue
            if previous and ((row['capture_instant']-previous['capture_instant'])/3600>policy.max_gap_hours or _distance(point,(previous['lat'],previous['lon']))>policy.max_leg_km):group+=1
            db.execute('INSERT INTO candidate_staging VALUES(?,?)',(group,row['asset_id']));previous=row
        for grouped in db.execute('SELECT group_id FROM candidate_staging GROUP BY group_id HAVING count(*)>=? ORDER BY group_id',(policy.min_observations,)):
            number=grouped[0];hasher=hashlib.sha256(canonical([DEFINITION,asdict(policy)]).encode())
            for value in db.execute('SELECT asset_id FROM candidate_staging WHERE group_id=? ORDER BY asset_id',(number,)):hasher.update(value[0].encode())
            candidate='candidate-'+hasher.hexdigest()
            old=db.execute('''SELECT t.id,t.revision,count(*) AS overlap FROM knowledge_trips t JOIN knowledge_trip_members m ON m.trip_id=t.id AND m.trip_revision=t.revision
              JOIN candidate_staging s ON s.asset_id=m.asset_id WHERE t.owner_id=? AND t.state='inferred' AND s.group_id=?
              AND NOT EXISTS(SELECT 1 FROM knowledge_candidates c WHERE c.generation_id=? AND c.trip_id=t.id) GROUP BY t.id ORDER BY overlap DESC,t.id LIMIT 1''',(owner['id'],number,generation)).fetchone()
            identity=old['id'] if old else identifier();revision=old['revision']+1 if old else 1
            if old:db.execute('UPDATE knowledge_trips SET revision=? WHERE id=?',(revision,identity))
            else:db.execute('INSERT INTO knowledge_trips VALUES(?,?,?,?)',(identity,owner['id'],'inferred',revision))
            db.execute('INSERT INTO knowledge_trip_revisions VALUES(?,?,NULL,NULL,NULL,?,?)',(identity,revision,'inferred',int(self.store.clock())))
            db.execute('INSERT INTO knowledge_trip_members SELECT ?,?,f.asset_id,f.revision,f.signature FROM candidate_staging s JOIN knowledge_facts f ON f.asset_id=s.asset_id AND f.generation_id=? WHERE s.group_id=?',(identity,revision,generation,number))
            db.execute('INSERT INTO knowledge_candidates VALUES(?,?,?)',(generation,candidate,identity))
        db.execute('DROP TABLE candidate_staging')
    def _evidence_ids(self,db,owner,ids):
        if not isinstance(ids,list) or len(ids)>200 or any(not isinstance(x,str) for x in ids) or len(set(ids))!=len(ids):invalid()
        base,args,_=self._project(db,owner,scope_value(None))
        if db.execute(base+'SELECT count(*) FROM p WHERE _asset_id IN ('+','.join('?' for _ in ids)+')',args+ids).fetchone()[0]!=len(ids):raise RuntimeErrorResult(404,'not_found')
    def _copy_members(self,db,owner,kind,identity,revision,*,ids=None,previous=None):
        base,args,_=self._project(db,owner,scope_value(None));table='knowledge_'+kind+'_members'
        if ids is not None:where='_asset_id IN ('+','.join('?' for _ in ids)+')';bindings=ids
        else:where='_asset_id IN (SELECT asset_id FROM '+table+' WHERE '+kind+'_id=? AND '+kind+'_revision=?)';bindings=list(previous)
        db.execute(base+'INSERT INTO '+table+' SELECT ?,?,_asset_id,_revision,_signature FROM p WHERE '+where,args+[identity,revision,*bindings])
    def _trip_query(self,db,owner,scope,*,active=True):
        base,args,generation=self._project(db,owner,scope)
        if set(scope['fields'])!=FIELDS:return base+'SELECT t.* FROM knowledge_trips t WHERE 0',args,generation
        condition="t.state IN ('inferred','confirmed','manual') AND " if active else ''
        condition+="(t.state!='inferred' OR EXISTS(SELECT 1 FROM knowledge_candidates c WHERE c.trip_id=t.id AND c.generation_id=?))"
        condition+=' AND NOT EXISTS(SELECT 1 FROM knowledge_trip_members m WHERE m.trip_id=t.id AND m.trip_revision=t.revision AND NOT EXISTS(SELECT 1 FROM p WHERE p._asset_id=m.asset_id AND p._signature=m.evidence_signature))'
        if set(scope)-{'fields'}:condition+=' AND EXISTS(SELECT 1 FROM knowledge_trip_members m WHERE m.trip_id=t.id AND m.trip_revision=t.revision)'
        return base+'SELECT t.* FROM knowledge_trips t WHERE t.owner_id=? AND '+condition,args+[owner['id'],generation['id'] if generation else ''],generation
    def _trip_allowed(self,db,owner,identity,scope):
        if not isinstance(identity,str):raise RuntimeErrorResult(404,'not_found')
        sql,args,_=self._trip_query(db,owner,scope,active=False);return db.execute(sql+' AND t.id=?',args+[identity]).fetchone()
    def _trip_data(self,db,owner,row,scope,limit=0,offset=0):
        base,args,_=self._project(db,owner,scope);where=' WHERE _asset_id IN (SELECT asset_id FROM knowledge_trip_members WHERE trip_id=? AND trip_revision=?)';bindings=args+[row['id'],row['revision']]
        info=db.execute(base+'SELECT count(*) AS evidence_count,min(capture_day) AS observed_start,max(capture_day) AS observed_end,count(DISTINCT capture_day) AS observed_day_count,coalesce(sum(capture_day IS NULL),0) AS unknown_time_records,coalesce(min(owner_presence=\'owner\'),0) AS owner_confirmed FROM p'+where,bindings).fetchone()
        saved=db.execute('SELECT * FROM knowledge_trip_revisions WHERE trip_id=? AND revision=?',(row['id'],row['revision'])).fetchone()
        dates=[x[0] for x in db.execute(base+'SELECT DISTINCT capture_day FROM p'+where+' AND capture_day IS NOT NULL ORDER BY capture_day LIMIT 201',bindings)]
        gaps=[]
        for left,right in zip(dates,dates[1:]):
            if (_date(right)-_date(left)).days>1:gaps.append({'start':(_date(left)+dt.timedelta(days=1)).isoformat(),'end':(_date(right)-dt.timedelta(days=1)).isoformat(),'status':'unknown'})
        facts=db.execute(base+'SELECT * FROM p'+where+' ORDER BY capture_day IS NULL,capture_day,_asset_id LIMIT ? OFFSET ?',bindings+[limit+1 if limit else 0,offset]).fetchall()
        edges=[]
        for edge in db.execute('SELECT parent_id,child_id,action FROM knowledge_trip_lineage WHERE parent_id=? OR child_id=? ORDER BY parent_id,child_id LIMIT 201',(row['id'],row['id'])):
            other=edge['child_id'] if edge['parent_id']==row['id'] else edge['parent_id']
            if self._trip_allowed(db,owner,other,scope):edges.append(dict(edge))
        return {'trip_id':row['id'],'revision':row['revision'],'state':row['state'],'title':saved['title'] or ('Inferred trip' if row['state']=='inferred' else 'Owner trip'),'start':saved['start'] or info['observed_start'],'end':saved['end'] or info['observed_end'],'boundary_basis':'owner_asserted_dates' if saved['start'] else 'observed_local_dates_not_departure_or_return','kind':'same_day_candidate' if info['observed_start']==info['observed_end'] and info['observed_start'] else 'overnight_candidate' if info['observed_start'] else 'manual_unknown_evidence','observed_start':info['observed_start'],'observed_end':info['observed_end'],'observed_day_count':info['observed_day_count'],'unknown_time_records':info['unknown_time_records'],'observed_dates':dates[:200],'observed_dates_has_more':len(dates)>200,'gaps':gaps[:199],'gaps_complete':len(dates)<=200,'continuous_presence':False,'owner_presence_confirmed':bool(info['evidence_count'] and info['owner_confirmed']),'evidence_count':info['evidence_count'],'evidence':[self._fact(fact,scope['fields']) for fact in facts[:limit]],'has_more_evidence':info['evidence_count']>offset+limit,'lineage':edges[:200],'definition_version':DEFINITION}
    def trips(self,token,*,scope=None,limit=50,cursor=None):
        def read(db,owner):
            sc=scope_value(scope);sql,args,generation=self._trip_query(db,owner,sc);offset,following=self._page(db,owner,token,generation,sc,['trips'],limit,cursor)
            rows=db.execute(sql+' ORDER BY t.id LIMIT ? OFFSET ?',args+[limit+1,offset]).fetchall()
            return {'data':[self._trip_data(db,owner,row,sc) for row in rows[:limit]],'next_cursor':following(len(rows)>limit),'generation':generation['id'] if generation else None,'definition_version':DEFINITION}
        return self.store.read(token,'knowledge_trip',read)
    def trip(self,token,trip_id,*,scope=None,limit=50,cursor=None):
        def read(db,owner):
            sc=scope_value(scope);row=self._trip_allowed(db,owner,trip_id,sc)
            if row is None:raise RuntimeErrorResult(404,'not_found')
            generation=self._generation(db,owner);offset,following=self._page(db,owner,token,generation,sc,['trip',trip_id,row['revision']],limit,cursor)
            result=self._trip_data(db,owner,row,sc,limit,offset);result['next_cursor']=following(result.pop('has_more_evidence'));result['generation']=generation['id'] if generation else None;return result
        return self.store.read(token,'knowledge_trip',read)
    def _mutable_trip(self,db,owner,identity,expected):
        if not isinstance(identity,str):invalid()
        row=db.execute('SELECT * FROM knowledge_trips WHERE id=? AND owner_id=?',(identity,owner['id'])).fetchone()
        if row is None:raise RuntimeErrorResult(404,'not_found')
        if type(expected) is not int or expected!=row['revision']:raise RuntimeErrorResult(409,'revision_conflict')
        if row['state'] not in {'inferred','confirmed','manual'}:raise RuntimeErrorResult(409,'superseded_trip')
        base,args,generation=self._project(db,owner,scope_value(None))
        if row['state']=='inferred' and not db.execute('SELECT 1 FROM knowledge_candidates WHERE generation_id=? AND trip_id=?',(generation['id'] if generation else '',identity)).fetchone():raise RuntimeErrorResult(404,'not_found')
        total=db.execute('SELECT count(*) FROM knowledge_trip_members WHERE trip_id=? AND trip_revision=?',(identity,expected)).fetchone()[0]
        visible=db.execute(base+'SELECT count(*) FROM p JOIN knowledge_trip_members m ON m.asset_id=p._asset_id WHERE m.trip_id=? AND m.trip_revision=?',args+[identity,expected]).fetchone()[0]
        if visible!=total:raise RuntimeErrorResult(404,'not_found')
        return row
    def _save_trip(self,db,owner,*,old=None,title=None,start=None,end=None,state='confirmed',origin='owner'):
        identity=old['id'] if old else identifier();revision=old['revision']+1 if old else 1
        if old:db.execute('UPDATE knowledge_trips SET state=?,revision=? WHERE id=?',(state,revision,identity))
        else:db.execute('INSERT INTO knowledge_trips VALUES(?,?,?,?)',(identity,owner['id'],state,revision))
        db.execute('INSERT INTO knowledge_trip_revisions VALUES(?,?,?,?,?,?,?)',(identity,revision,title,start,end,origin,int(self.store.clock())))
        return identity,revision
    def _safe_receipt(self,db,owner,result):
        ids=[];revisions={}
        for identity in result['trip_ids']:
            row=self._trip_allowed(db,owner,identity,scope_value(None))
            if row is not None:ids.append(identity);revisions[identity]=row['revision']
        return {'operation_id':result['operation_id'],'trip_ids':ids,'revisions':revisions,'status':'applied'}
    def correct_trip(self,token,csrf,request_key,action,*,trip_id=None,expected_revision=None,payload=None):
        def write(db,owner):
            if not isinstance(action,str) or action not in {'manual','rename','dates','confirm','dismiss','merge','split'} or (payload is not None and not isinstance(payload,dict)):invalid()
            values=payload or {};hashed,prior=self._request(db,owner,request_key,['trip',action,trip_id,expected_revision,values])
            if prior:return self._safe_receipt(db,owner,prior)
            result_ids=[];parents=[]
            if action=='manual':
                if trip_id is not None or expected_revision is not None or set(values)-{'title','start','end','evidence_ids'} or not text(values.get('title')):invalid()
                start=date(values.get('start'));end=date(values.get('end'))
                if start>end:invalid()
                ids=values.get('evidence_ids',[]);self._evidence_ids(db,owner,ids)
                identity,revision=self._save_trip(db,owner,title=values['title'],start=start,end=end,state='manual',origin='manual')
                self._copy_members(db,owner,'trip',identity,revision,ids=ids);result_ids=[identity]
            elif action=='merge':
                ids=values.get('trip_ids');expected=values.get('expected_revisions')
                if trip_id is not None or expected_revision is not None or set(values)-{'trip_ids','expected_revisions','title'} or not isinstance(ids,list) or not 2<=len(ids)<=20 or any(not isinstance(x,str) for x in ids) or len(set(ids))!=len(ids) or not isinstance(expected,dict) or set(expected)!=set(ids):invalid()
                if 'title' in values and not text(values['title']):invalid()
                parents=[self._mutable_trip(db,owner,identity,expected[identity]) for identity in ids]
                identity,revision=self._save_trip(db,owner,title=values.get('title'),origin='merge');result_ids=[identity]
                base,args,_=self._project(db,owner,scope_value(None))
                db.execute(base+'''INSERT INTO knowledge_trip_members SELECT ?,?,_asset_id,_revision,_signature FROM p WHERE _asset_id IN
                  (SELECT m.asset_id FROM knowledge_trip_members m JOIN knowledge_trips t ON t.id=m.trip_id AND t.revision=m.trip_revision WHERE t.id IN ('''+','.join('?' for _ in ids)+'))',args+[identity,revision,*ids])
                for parent in parents:db.execute("UPDATE knowledge_trips SET state='merged' WHERE id=?",(parent['id'],));db.execute('INSERT INTO knowledge_trip_lineage VALUES(?,?,?,?)',(parent['id'],identity,'merge',int(self.store.clock())))
            else:
                row=self._mutable_trip(db,owner,trip_id,expected_revision);saved=db.execute('SELECT * FROM knowledge_trip_revisions WHERE trip_id=? AND revision=?',(trip_id,row['revision'])).fetchone()
                trusted=self._trip_allowed(db,owner,trip_id,scope_value(None)) is not None
                title=saved['title'] if trusted else None;start=saved['start'] if trusted else None;end=saved['end'] if trusted else None
                if action=='split':
                    if set(values)-{'date','titles'}:invalid()
                    cut=date(values.get('date'));titles=values.get('titles',[None,None])
                    if not isinstance(titles,list) or len(titles)!=2 or ('titles' in values and any(not text(x) for x in titles)):invalid()
                    base,args,_=self._project(db,owner,scope_value(None));selection=' WHERE _asset_id IN (SELECT asset_id FROM knowledge_trip_members WHERE trip_id=? AND trip_revision=?)';bindings=args+[trip_id,row['revision']]
                    counts=db.execute(base+'SELECT count(*) AS total,coalesce(sum(capture_day IS NULL),0) AS missing,coalesce(sum(capture_day<?),0) AS before,coalesce(sum(capture_day>=?),0) AS after FROM p'+selection,args+[cut,cut,trip_id,row['revision']]).fetchone()
                    if counts['missing'] or (counts['total'] and (not counts['before'] or not counts['after'])):raise RuntimeErrorResult(409,'split_requires_known_evidence_on_both_sides')
                    manual=not counts['total']
                    if manual and (not start or not end or not start<cut<=end):raise RuntimeErrorResult(409,'split_requires_known_boundaries')
                    for index,op in enumerate(('<','>=')):
                        child,revision=self._save_trip(db,owner,title=titles[index],start=(start if index==0 else cut) if manual else None,end=((_date(cut)-dt.timedelta(days=1)).isoformat() if index==0 else end) if manual else None,state='manual' if manual else 'confirmed',origin='split')
                        db.execute(base+'INSERT INTO knowledge_trip_members SELECT ?,?,_asset_id,_revision,_signature FROM p'+selection+' AND capture_day'+op+'?',args+[child,revision,trip_id,row['revision'],cut])
                        result_ids.append(child);db.execute('INSERT INTO knowledge_trip_lineage VALUES(?,?,?,?)',(trip_id,child,'split',int(self.store.clock())))
                    db.execute("UPDATE knowledge_trips SET state='split' WHERE id=?",(trip_id,))
                else:
                    allowed={'title'} if action=='rename' else {'start','end'} if action=='dates' else set()
                    if set(values)!=allowed:invalid()
                    if action=='rename':
                        if not text(values['title']):invalid()
                        title=values['title']
                    if action=='dates':
                        start=date(values['start']);end=date(values['end'])
                        if start>end:invalid()
                    identity,revision=self._save_trip(db,owner,old=row,title=title,start=start,end=end,state='dismissed' if action=='dismiss' else 'manual' if row['state']=='manual' else 'confirmed',origin=action)
                    self._copy_members(db,owner,'trip',identity,revision,previous=(trip_id,row['revision']));result_ids=[identity]
            operation=identifier();now=int(self.store.clock());db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?)',(operation,owner['id'],'knowledge_correction','complete',now,now))
            result={'operation_id':operation,'trip_ids':result_ids};self._receipt(db,owner,request_key,hashed,result);return self._safe_receipt(db,owner,result)
        return self._write(token,csrf,'knowledge_correction',write)
