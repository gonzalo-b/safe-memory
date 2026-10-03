"""Explicit owner requests for immutable original PhotoKit resource bytes."""
from __future__ import annotations
import hashlib
import os
import re
import shutil
import unicodedata
from runtime.ingestion import VISIBLE,canonical,choice
from runtime.media import MediaService,MAX_CHUNK,media_path,media_reserved,media_jobs,publish
from runtime.pairing import _text
from runtime.store import RuntimeErrorResult,digest,file_digest,identifier

MAX_REQUEST_BYTES=256*1024*1024
RESOURCE_TYPES={'photo','video','paired_video','alternate_photo','audio'}
FAILURES={'source_unavailable','permission_changed','revision_changed','icloud_unavailable','capacity','unsupported_resource'}

class OriginalService:
    def __init__(self,store):self.store=store;self.media=MediaService(store);self.ingest=self.media.ingest

    def _required(self,db,owner_id,request_id):
        if not isinstance(request_id,str):raise RuntimeErrorResult(400,'invalid_input')
        row=db.execute('SELECT * FROM original_requests WHERE id=? AND owner_id=?',(request_id,owner_id)).fetchone()
        if row is None:raise RuntimeErrorResult(404,'not_found')
        asset=self.media._asset(db,owner_id,row['asset_id'])
        if asset['current_revision']!=row['revision']:raise RuntimeErrorResult(404,'not_found')
        return row,asset

    def _device_request(self,db,source,request_id):
        row,asset=self._required(db,source['owner_id'],request_id)
        if asset['connection_id']!=source['id']:raise RuntimeErrorResult(404,'not_found')
        return row,asset

    def _data(self,db,row):
        resources=[dict(r) for r in db.execute('''SELECT ordinal,resource_type,original_filename,uniform_type_identifier,size,sha256,component_id
          FROM original_uploads WHERE request_id=? ORDER BY ordinal''',(row['id'],))]
        return {'request_id':row['id'],'asset_id':row['asset_id'],'revision':row['revision'],'state':row['state'],
                'error_code':row['error_code'],'resources':resources}

    def status(self,token,asset_id):
        def read(db,owner):
            asset=self.media._asset(db,owner['id'],asset_id)
            row=db.execute('SELECT * FROM original_requests WHERE owner_id=? AND asset_id=? AND revision=?',(owner['id'],asset_id,asset['current_revision'])).fetchone()
            return {'request':self._data(db,row) if row else None}
        return self.store.read(token,'original_status',read)

    def _owner(self,token,csrf,key,action,payload,resolve):
        def mutate(db,owner):
            if not _text(key,128):raise RuntimeErrorResult(400,'invalid_input')
            # Resolve/reauthorize even on retry, before consulting a retained receipt.
            request,body=resolve(db,owner,False)
            hashed=digest(canonical([action,payload,body]))
            receipt=db.execute('SELECT * FROM original_owner_receipts WHERE owner_id=? AND request_key=?',(owner['id'],key)).fetchone()
            if receipt:
                if receipt['digest']!=hashed:raise RuntimeErrorResult(409,'request_conflict')
                row,_=self._required(db,owner['id'],receipt['request_id']);return self._data(db,row),owner['id']
            row,_=resolve(db,owner,True)
            db.execute('INSERT INTO original_owner_receipts VALUES(?,?,?,?)',(owner['id'],key,hashed,row['id']))
            return self._data(db,row),owner['id']
        return self.ingest.pairing._run(action,mutate,token=token,csrf=csrf,owner_required=True,mutate=True)

    def request(self,token,csrf,asset_id,request_key):
        def resolve(db,owner,write):
            asset=self.media._asset(db,owner['id'],asset_id)
            row=db.execute('SELECT * FROM original_requests WHERE owner_id=? AND asset_id=? AND revision=?',(owner['id'],asset_id,asset['current_revision'])).fetchone()
            if row is None and write:
                if db.execute('SELECT count(*) FROM original_requests WHERE owner_id=?',(owner['id'],)).fetchone()[0]>=4096:raise RuntimeErrorResult(507,'request_capacity')
                identity=identifier();now=int(self.store.clock())
                db.execute("INSERT INTO original_requests VALUES(?,?,?,?,'waiting_for_device',NULL,NULL,?,?)",(identity,owner['id'],asset_id,asset['current_revision'],now,now))
                db.execute('INSERT INTO operations VALUES(?,?,?,?,?,NULL)',(identity,owner['id'],'original_request','waiting_for_device',now))
                row=db.execute('SELECT * FROM original_requests WHERE id=?',(identity,)).fetchone()
            return row,asset['current_revision']
        return self._owner(token,csrf,request_key,'original_request',asset_id,resolve)

    def retry(self,token,csrf,request_id,request_key):
        def resolve(db,owner,write):
            row,_=self._required(db,owner['id'],request_id)
            if write and row['state']=='failed':
                now=int(self.store.clock());db.execute("UPDATE original_requests SET state='waiting_for_device',error_code=NULL,updated_at=? WHERE id=?",(now,request_id))
                db.execute("UPDATE operations SET status='waiting_for_device',completed_at=NULL WHERE id=?",(request_id,))
                row=db.execute('SELECT * FROM original_requests WHERE id=?',(request_id,)).fetchone()
            return row,row['revision']
        return self._owner(token,csrf,request_key,'original_retry',request_id,resolve)

    def pending(self,device_id,credential):
        def read(db,source):
            requests=[dict(r) for r in db.execute('''SELECT r.id AS request_id,r.asset_id,a.native_id,v.source_revision,v.media_type,r.state
              FROM original_requests r JOIN assets a ON a.id=r.asset_id AND a.current_revision=r.revision
              JOIN asset_revisions v ON v.asset_id=a.id AND v.revision=a.current_revision
              JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
              WHERE r.owner_id=? AND c.id=? AND r.state IN ('waiting_for_device','transferring') AND '''+VISIBLE+'''
              ORDER BY r.created_at,r.id LIMIT 20''',(source['owner_id'],source['id']))]
            return {'requests':requests}
        return self.ingest._run('original_pending',device_id,credential,read)

    def _manifest(self,resources,media_type):
        if not isinstance(resources,list) or not 1<=len(resources)<=8:raise RuntimeErrorResult(400,'invalid_manifest')
        counts={kind:0 for kind in RESOURCE_TYPES};total=0;seen=set()
        for value in resources:
            if not isinstance(value,dict) or set(value)!={'resource_type','original_filename','uniform_type_identifier','size','sha256'}:raise RuntimeErrorResult(400,'invalid_manifest')
            name=value['original_filename'];uti=value['uniform_type_identifier'];size=value['size'];sha=value['sha256'];kind=value['resource_type']
            if (not choice(kind,RESOURCE_TYPES) or not isinstance(name,str) or not 1<=len(name)<=255 or name in ('.','..') or '/' in name or '\\' in name
                or any(unicodedata.category(c).startswith('C') for c in name) or not isinstance(uti,str) or not re.fullmatch('[A-Za-z0-9.-]{1,128}',uti)
                or type(size) is not int or not 1<=size<=MAX_REQUEST_BYTES or not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha)):
                raise RuntimeErrorResult(400,'invalid_manifest')
            hashed=digest(canonical(value))
            if hashed in seen:raise RuntimeErrorResult(400,'ambiguous_manifest')
            seen.add(hashed);counts[kind]+=1;total+=size
        if total>MAX_REQUEST_BYTES:raise RuntimeErrorResult(413,'original_capacity')
        expected={'photo':{'photo':1,'video':0,'paired_video':0},'video':{'photo':0,'video':1,'paired_video':0,'alternate_photo':0},'live':{'photo':1,'video':0,'paired_video':1}}[media_type]
        if any(counts[k]!=v for k,v in expected.items()):raise RuntimeErrorResult(400,'incomplete_manifest')
        return digest(canonical(resources)),total

    def _begin_data(self,db,row):
        resources=[dict(r) for r in db.execute('SELECT ordinal,id AS upload_id,next_offset,state FROM original_uploads WHERE request_id=? ORDER BY ordinal',(row['id'],))]
        return {'request_id':row['id'],'state':row['state'],'resources':resources}

    def begin(self,device_id,credential,request_id,resources):
        def begin(db,source):
            row,asset=self._device_request(db,source,request_id);hashed,total=self._manifest(resources,asset['media_type'])
            if row['state']=='failed':raise RuntimeErrorResult(409,'owner_retry_required')
            if row['manifest_digest']:
                if row['manifest_digest']!=hashed:raise RuntimeErrorResult(409,'manifest_conflict')
            else:
                count=media_jobs(db)
                if count+len(resources)>256 or media_reserved(db)+2*total>self.media.budget:raise RuntimeErrorResult(507,'media_capacity')
                self.media._capacity(2*total)
                for ordinal,value in enumerate(resources):
                    upload=identifier();folder=media_path(self.store.root,'media/'+upload+'/complete').parent;folder.mkdir(mode=0o700,parents=True);folder.parent.chmod(0o700)
                    db.execute('''INSERT INTO original_uploads(id,request_id,ordinal,resource_type,original_filename,uniform_type_identifier,size,sha256)
                    VALUES(?,?,?,?,?,?,?,?)''',(upload,request_id,ordinal,value['resource_type'],value['original_filename'],value['uniform_type_identifier'],value['size'],value['sha256']))
            if row['state']!='ready':
                db.execute("UPDATE original_requests SET manifest_digest=?,state='transferring',error_code=NULL,updated_at=? WHERE id=?",(hashed,int(self.store.clock()),request_id))
                db.execute("UPDATE operations SET status='transferring' WHERE id=?",(request_id,))
            return self._begin_data(db,db.execute('SELECT * FROM original_requests WHERE id=?',(request_id,)).fetchone())
        return self.ingest._run('original_begin',device_id,credential,begin)

    def _upload(self,db,source,upload_id):
        if not isinstance(upload_id,str):raise RuntimeErrorResult(400,'invalid_input')
        upload=db.execute('SELECT * FROM original_uploads WHERE id=?',(upload_id,)).fetchone()
        if upload is None:raise RuntimeErrorResult(404,'not_found')
        request,_=self._device_request(db,source,upload['request_id'])
        if request['state']=='failed':raise RuntimeErrorResult(409,'owner_retry_required')
        return upload,request

    def chunk(self,device_id,credential,upload_id,offset,content):
        def write(db,source):
            upload,request=self._upload(db,source,upload_id)
            if type(offset) is not int or offset<0 or not isinstance(content,bytes) or not 1<=len(content)<=MAX_CHUNK or offset+len(content)>upload['size']:raise RuntimeErrorResult(400,'invalid_chunk')
            hashed=hashlib.sha256(content).hexdigest();old=db.execute('SELECT * FROM original_chunks WHERE upload_id=? AND offset=?',(upload_id,offset)).fetchone()
            if old:
                if old['sha256']!=hashed or old['size']!=len(content):raise RuntimeErrorResult(409,'replay_conflict')
                return {'upload_id':upload_id,'next_offset':offset+len(content),'state':upload['state']}
            if request['state']!='transferring' or upload['state']!='active' or upload['next_offset']!=offset:raise RuntimeErrorResult(409,'checkpoint_conflict')
            if db.execute('SELECT count(*) FROM original_chunks WHERE upload_id=?',(upload_id,)).fetchone()[0]>=1024:raise RuntimeErrorResult(413,'too_many_chunks')
            key='media/'+upload_id+'/chunk-'+str(offset);self.media._write(key,content)
            db.execute('INSERT INTO original_chunks VALUES(?,?,?,?,?)',(upload_id,offset,len(content),hashed,key));db.execute('UPDATE original_uploads SET next_offset=? WHERE id=?',(offset+len(content),upload_id))
            return {'upload_id':upload_id,'next_offset':offset+len(content),'state':'active'}
        return self.ingest._run('original_chunk',device_id,credential,write)

    def complete(self,device_id,credential,upload_id):
        def finish(db,source):
            upload,request=self._upload(db,source,upload_id)
            if upload['next_offset']!=upload['size']:raise RuntimeErrorResult(409,'incomplete_upload')
            component=db.execute('SELECT * FROM original_components WHERE upload_id=?',(upload_id,)).fetchone()
            if component is None:
                if request['state']!='transferring':raise RuntimeErrorResult(409,'checkpoint_conflict')
                key='media/'+upload_id+'/complete';path=media_path(self.store.root,key)
                if not path.exists():
                    self.media._capacity(upload['size']);staged=path.parent/('staged-'+identifier());fd=os.open(staged,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as output:
                        for chunk in db.execute('SELECT * FROM original_chunks WHERE upload_id=? ORDER BY offset',(upload_id,)):
                            source_path=media_path(self.store.root,chunk['storage_key'])
                            if source_path.stat().st_size!=chunk['size'] or file_digest(source_path)!=chunk['sha256']:raise RuntimeErrorResult(409,'chunk_integrity')
                            with source_path.open('rb') as stream:shutil.copyfileobj(stream,output,1024*1024)
                        output.flush();os.fsync(output.fileno())
                    publish(staged,path)
                if path.stat().st_size!=upload['size'] or file_digest(path)!=upload['sha256']:raise RuntimeErrorResult(409,'component_integrity')
                component_id=identifier();db.execute('INSERT INTO original_components VALUES(?,?,?,?,?,?)',(component_id,upload_id,key,upload['size'],upload['sha256'],int(self.store.clock())))
            else:component_id=component['id']
            db.execute("UPDATE original_uploads SET state='complete',component_id=? WHERE id=?",(component_id,upload_id))
            ready=not db.execute("SELECT 1 FROM original_uploads WHERE request_id=? AND state!='complete'",(request['id'],)).fetchone()
            state='ready' if ready else 'transferring';now=int(self.store.clock())
            db.execute('UPDATE original_requests SET state=?,error_code=NULL,updated_at=? WHERE id=?',(state,now,request['id']))
            db.execute('UPDATE operations SET status=?,completed_at=? WHERE id=?',(state,now if ready else None,request['id']))
            return {'request_id':request['id'],'upload_id':upload_id,'component_id':component_id,'state':state}
        return self.ingest._run('original_complete',device_id,credential,finish)

    def fail(self,device_id,credential,request_id,reason):
        def fail(db,source):
            row,_=self._device_request(db,source,request_id)
            if not choice(reason,FAILURES):raise RuntimeErrorResult(400,'invalid_input')
            if row['state']=='ready':raise RuntimeErrorResult(409,'already_ready')
            now=int(self.store.clock());db.execute("UPDATE original_requests SET state='failed',error_code=?,updated_at=? WHERE id=?",(reason,now,request_id))
            db.execute("UPDATE operations SET status='failed',completed_at=? WHERE id=?",(now,request_id))
            return {'request_id':request_id,'state':'failed','error_code':reason}
        return self.ingest._run('original_fail',device_id,credential,fail)

    def read(self,token,component_id,start=0,length=MAX_CHUNK):
        def read(db,owner):
            if not isinstance(component_id,str) or type(start) is not int or start<0 or type(length) is not int or not 1<=length<=MAX_CHUNK:raise RuntimeErrorResult(400,'invalid_range')
            component=db.execute('''SELECT c.*,u.request_id,u.original_filename FROM original_components c JOIN original_uploads u ON u.id=c.upload_id WHERE c.id=?''',(component_id,)).fetchone()
            if component is None:raise RuntimeErrorResult(404,'not_found')
            request,_=self._required(db,owner['id'],component['request_id'])
            if request['state']!='ready':raise RuntimeErrorResult(409,'original_not_ready')
            if start>=component['size']:raise RuntimeErrorResult(416,'invalid_range')
            path=media_path(self.store.root,component['storage_key'])
            if path.stat().st_size!=component['size'] or file_digest(path)!=component['sha256']:raise RuntimeErrorResult(503,'component_integrity')
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
            with os.fdopen(fd,'rb') as stream:stream.seek(start);content=stream.read(min(length,component['size']-start))
            return {'component_id':component_id,'content':content,'mime':'application/octet-stream','filename':component['original_filename'],'size':component['size'],'offset':start}
        return self.store.read(token,'original_read',read)
