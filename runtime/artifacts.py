"""Private deterministic Gallery revisions. Persisted membership is never authority."""
from __future__ import annotations
import json
import re
from runtime.ingestion import VISIBLE
from runtime.knowledge import KnowledgeService, scope_value
from runtime.pairing import PairingService, _text
from runtime.store import RuntimeErrorResult, digest, identifier

DEFINITION='private-gallery-v1'
MAX_MEMBERS=200
MAX_EXCLUSIONS=1000
MAX_ARTIFACTS=200
MAX_REVISIONS=1000


def invalid():raise RuntimeErrorResult(400,'invalid_input')
def identity(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{32}',value)
def ids(value):
    if not isinstance(value,list) or len(value)>MAX_MEMBERS or any(not identity(x) for x in value) or len(set(value))!=len(value):invalid()
    return value

class ArtifactService:
    def __init__(self,store):self.store=store;self.pairing=PairingService(store);self.knowledge=KnowledgeService(store)

    def _asset(self,db,owner,asset_id):
        if not identity(asset_id):return None
        return db.execute('''SELECT a.id,a.current_revision,a.connection_id,a.hidden,r.media_type,r.capture_time,r.time_basis,
          m.media_state FROM assets a JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
          JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision
          LEFT JOIN asset_media_status m ON m.asset_id=a.id WHERE a.id=? AND a.owner_id=? AND '''+VISIBLE,(asset_id,owner['id'])).fetchone()

    def _allowed(self,db,owner,artifact_id):
        if not identity(artifact_id):return None
        row=db.execute('SELECT * FROM artifacts WHERE id=? AND owner_id=?',(artifact_id,owner['id'])).fetchone()
        if row is None:return None
        # Fail closed for the complete persisted output, including its private title.
        for member in db.execute("SELECT asset_id FROM artifact_members WHERE artifact_id=? AND revision=? AND intent='included'",(artifact_id,row['revision'])):
            if self._asset(db,owner,member['asset_id']) is None:return None
        return row

    def _required(self,db,owner,artifact_id):
        row=self._allowed(db,owner,artifact_id)
        if row is None:raise RuntimeErrorResult(404,'not_found')
        return row

    def _saved(self,db,row):
        revision=dict(db.execute('SELECT * FROM artifact_revisions WHERE artifact_id=? AND revision=?',(row['id'],row['revision'])).fetchone())
        members={r['asset_id']:dict(r) for r in db.execute('SELECT * FROM artifact_members WHERE artifact_id=? AND revision=? ORDER BY position,asset_id',(row['id'],row['revision']))}
        return revision,members

    def _data(self,db,owner,row,*,summary=False):
        revision,members=self._saved(db,row);included=[];excluded=[]
        for member in members.values():
            asset=self._asset(db,owner,member['asset_id'])
            if member['intent']=='excluded':
                if asset is not None:excluded.append(member['asset_id'])
                continue
            if asset is None:raise RuntimeErrorResult(404,'not_found')
            included.append({'asset_id':asset['id'],'revision':asset['current_revision'],'selected_revision':member['selected_revision'],
                             'connection_id':asset['connection_id'],'media_type':asset['media_type'],'capture_time':asset['capture_time'],
                             'time_basis':asset['time_basis'],'media_state':asset['media_state'] or 'not_transferred','origin':member['origin']})
        result={'id':row['id'],'type':'gallery','revision':row['revision'],'title':revision['title'],'layout':revision['layout'],
                'cover_asset_id':revision['cover_asset_id'],'member_count':len(included),'created_at':row['created_at'],'updated_at':row['updated_at'],'private':True}
        if not summary:
            trip=self.knowledge._trip_allowed(db,owner,revision['trip_id'],scope_value(None)) if revision['trip_id'] else None
            if trip is not None and trip['state'] not in ('inferred','confirmed','manual'):trip=None
            # A changed/superseded trip cannot expose its old title or historical evidence.
            valid=trip is not None and trip['revision']==revision['trip_revision']
            result.update(members=included,excluded_ids=excluded,definition_version=revision['definition_version'],
                          lineage={'origin':revision['origin'],'trip_id':revision['trip_id'] if valid else None,
                                   'trip_revision':revision['trip_revision'] if valid else None,'generation':revision['generation_id']})
        return result

    def get(self,token,artifact_id):return self.store.read(token,'artifact_read',lambda db,owner:self._data(db,owner,self._required(db,owner,artifact_id)))

    def _visible_rows(self,db,owner):
        return [row for row in db.execute('SELECT * FROM artifacts WHERE owner_id=? ORDER BY created_at,id',(owner['id'],)) if self._allowed(db,owner,row['id'])]

    def list(self,token,*,limit=50,cursor=None):
        def read(db,owner):
            if type(limit) is not int or not 1<=limit<=50 or cursor is not None and not identity(cursor):invalid()
            rows=self._visible_rows(db,owner)
            if cursor is not None:
                positions=[i for i,row in enumerate(rows) if row['id']==cursor]
                if not positions:raise RuntimeErrorResult(409,'stale_cursor')
                rows=rows[positions[0]+1:]
            page=rows[:limit]
            return {'artifacts':[self._data(db,owner,row,summary=True) for row in page],
                    'next_cursor':page[-1]['id'] if len(rows)>limit else None,'fixture':self.store.fixture}
        return self.store.read(token,'artifact_read',read)

    def _selection(self,db,owner,asset_ids,trip_id,expected_trip_revision,*,automatic=False):
        generation=self.knowledge._generation(db,owner)
        lineage={'trip_id':None,'trip_revision':None,'generation_id':generation['id'] if generation else None}
        if trip_id is not None:
            if asset_ids is not None or not identity(trip_id) or type(expected_trip_revision) is not int:invalid()
            trip=self.knowledge._trip_allowed(db,owner,trip_id,scope_value(None))
            if trip is None or trip['state'] not in ('inferred','confirmed','manual'):raise RuntimeErrorResult(404,'not_found')
            if trip['revision']!=expected_trip_revision:raise RuntimeErrorResult(409,'revision_conflict')
            # Whole trip checked by knowledge projection before resolving any membership.
            selected=[r['asset_id'] for r in db.execute('SELECT asset_id FROM knowledge_trip_members WHERE trip_id=? AND trip_revision=? ORDER BY asset_id LIMIT 202',(trip_id,trip['revision']))]
            if len(selected)>MAX_MEMBERS:raise RuntimeErrorResult(413,'selection_capacity')
            lineage.update(trip_id=trip_id,trip_revision=trip['revision']);automatic=True
        else:
            if expected_trip_revision is not None:invalid()
            selected=ids(asset_ids if asset_ids is not None else [])
        members={}
        for asset_id in selected:
            asset=self._asset(db,owner,asset_id)
            if asset is None:raise RuntimeErrorResult(404,'not_found')
            if automatic and asset['hidden']:continue
            members[asset_id]={'asset_id':asset_id,'selected_revision':asset['current_revision'],'intent':'included','position':len(members),'origin':'trip' if trip_id else 'selection'}
        return members,lineage

    def _mutation(self,token,csrf,key,action,body,operation):
        def mutate(db,owner):
            if not _text(key,200):invalid()
            try:fingerprint=digest(json.dumps([action,body],sort_keys=True,separators=(',',':'),allow_nan=False))
            except (TypeError,ValueError):invalid()
            receipt=db.execute('SELECT * FROM artifact_requests WHERE owner_id=? AND request_key=?',(owner['id'],key)).fetchone()
            if receipt:
                if receipt['digest']!=fingerprint:raise RuntimeErrorResult(409,'request_conflict')
                self._required(db,owner,receipt['artifact_id'])
                return {k:receipt[k] for k in ('artifact_id','revision','operation_id')},owner['id']
            artifact_id,revision=operation(db,owner)
            op=identifier();now=int(self.store.clock())
            db.execute('INSERT INTO operations VALUES(?,?,?,?,?,?)',(op,owner['id'],action,'complete',now,now))
            db.execute('INSERT INTO artifact_requests VALUES(?,?,?,?,?,?)',(owner['id'],key,fingerprint,artifact_id,revision,op))
            return {'artifact_id':artifact_id,'revision':revision,'operation_id':op},owner['id']
        return self.pairing._run(action,mutate,token=token,csrf=csrf,owner_required=True,mutate=True)

    def _save(self,db,owner,row,values,members):
        included=[v for v in members.values() if v['intent']=='included'];excluded=[v for v in members.values() if v['intent']=='excluded']
        if len(included)>MAX_MEMBERS or len(excluded)>MAX_EXCLUSIONS:raise RuntimeErrorResult(413,'selection_capacity')
        if not _text(values['title'],200) or values['layout'] not in ('grid','story'):invalid()
        if values['cover_asset_id'] is not None and values['cover_asset_id'] not in [x['asset_id'] for x in included]:invalid()
        revision=row['revision']+1 if row else 1;artifact_id=row['id'] if row else identifier();now=int(self.store.clock())
        if revision>MAX_REVISIONS:raise RuntimeErrorResult(409,'revision_capacity')
        if row:db.execute('UPDATE artifacts SET revision=?,updated_at=? WHERE id=?',(revision,now,artifact_id))
        else:
            if db.execute('SELECT count(*) FROM artifacts WHERE owner_id=?',(owner['id'],)).fetchone()[0]>=MAX_ARTIFACTS:raise RuntimeErrorResult(409,'artifact_capacity')
            db.execute('INSERT INTO artifacts VALUES(?,?,?,?,?,?)',(artifact_id,owner['id'],'gallery',revision,now,now))
        db.execute('INSERT INTO artifact_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)',(artifact_id,revision,values['title'],values['layout'],values['cover_asset_id'],DEFINITION,values.get('trip_id'),values.get('trip_revision'),values.get('generation_id'),values['origin'],now))
        for position,member in enumerate(included+excluded):
            db.execute('INSERT INTO artifact_members VALUES(?,?,?,?,?,?,?)',(artifact_id,revision,member['asset_id'],member['selected_revision'],member['intent'],position,member['origin']))
        return artifact_id,revision

    def create(self,token,csrf,request_key,*,title,asset_ids=None,layout='grid',trip_id=None,expected_trip_revision=None):
        body=dict(title=title,asset_ids=asset_ids,layout=layout,trip_id=trip_id,expected_trip_revision=expected_trip_revision)
        def create(db,owner):
            members,lineage=self._selection(db,owner,asset_ids,trip_id,expected_trip_revision)
            values=dict(title=title,layout=layout,cover_asset_id=next(iter(members),None),origin='owner_trip' if trip_id else 'owner_selection',**lineage)
            return self._save(db,owner,None,values,members)
        return self._mutation(token,csrf,request_key,'artifact_create',body,create)

    def _editable(self,db,owner,artifact_id,expected_revision):
        row=self._required(db,owner,artifact_id)
        if type(expected_revision) is not int or row['revision']!=expected_revision:raise RuntimeErrorResult(409,'revision_conflict')
        values,members=self._saved(db,row);return row,values,members

    def edit(self,token,csrf,request_key,artifact_id,expected_revision,patch):
        def edit(db,owner):
            row,values,members=self._editable(db,owner,artifact_id,expected_revision)
            if not isinstance(patch,dict) or not patch or set(patch)-{'title','layout','cover_asset_id','add_ids','remove_ids','order'}:invalid()
            add=ids(patch.get('add_ids',[]));remove=ids(patch.get('remove_ids',[]))
            if set(add)&set(remove):invalid()
            for asset_id in remove:
                if asset_id not in members or members[asset_id]['intent']!='included':invalid()
                members[asset_id]['intent']='excluded';members[asset_id]['origin']='owner_exclusion'
            for asset_id in add:
                asset=self._asset(db,owner,asset_id)
                if asset is None:raise RuntimeErrorResult(404,'not_found')
                if asset_id not in members or members[asset_id]['intent']=='excluded':
                    members[asset_id]={'asset_id':asset_id,'selected_revision':asset['current_revision'],'intent':'included','position':len(members),'origin':'owner_inclusion'}
            if 'order' in patch:
                order=ids(patch['order']);active={k for k,v in members.items() if v['intent']=='included'}
                if set(order)!=active:invalid()
                members={key:members[key] for key in order+list(k for k in members if k not in active)}
            for name in ('title','layout','cover_asset_id'):
                if name in patch:values[name]=patch[name]
            if 'cover_asset_id' not in patch and values['cover_asset_id'] in remove:
                values['cover_asset_id']=next((k for k,v in members.items() if v['intent']=='included'),None)
            values['origin']='owner_edit';return self._save(db,owner,row,values,members)
        return self._mutation(token,csrf,request_key,'artifact_edit',dict(artifact_id=artifact_id,expected_revision=expected_revision,patch=patch),edit)

    def recompose(self,token,csrf,request_key,artifact_id,expected_revision,*,asset_ids=None,trip_id=None,expected_trip_revision=None):
        def compose(db,owner):
            row,values,members=self._editable(db,owner,artifact_id,expected_revision)
            if asset_ids is not None or trip_id is not None:
                additions,lineage=self._selection(db,owner,asset_ids,trip_id,expected_trip_revision,automatic=True)
                for key,member in additions.items():
                    if key not in members:members[key]=member
                values.update(lineage)
            elif expected_trip_revision is not None:invalid()
            values['origin']='owner_recompose';return self._save(db,owner,row,values,members)
        return self._mutation(token,csrf,request_key,'artifact_recompose',dict(artifact_id=artifact_id,expected_revision=expected_revision,asset_ids=asset_ids,trip_id=trip_id,expected_trip_revision=expected_trip_revision),compose)

    def debug(self,token,artifact_id):
        def read(db,owner):
            row=self._required(db,owner,artifact_id)
            operations=[dict(r) for r in db.execute('''SELECT o.id,o.action,o.status,o.created_at,o.completed_at,r.revision FROM artifact_requests r
              JOIN operations o ON o.id=r.operation_id WHERE r.owner_id=? AND r.artifact_id=? ORDER BY r.revision DESC LIMIT 20''',(owner['id'],artifact_id))]
            return {'artifact_id':artifact_id,'revision':row['revision'],'definition_version':DEFINITION,'operations':operations,
                    'bounds':{'members':MAX_MEMBERS,'exclusions':MAX_EXCLUSIONS,'revisions':MAX_REVISIONS}}
        return self.store.read(token,'artifact_debug',read)
