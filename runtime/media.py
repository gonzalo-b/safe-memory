"""Bounded private optimized-component storage. No public paths or source writes."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import re
import shutil
from runtime.ingestion import IngestionService, VISIBLE, canonical, choice
from runtime.pairing import _text
from runtime.store import RuntimeErrorResult, digest, file_digest, identifier, private_destination

MAX_CHUNK=4*1024*1024
MAX_COMPONENT=64*1024*1024
MEDIA_BUDGET=1024*1024*1024
KEY=re.compile(r'media/[a-f0-9]{32}/(?:chunk-[0-9]{1,10}|complete)')
ROLES={'photo':{'still':'image/jpeg'},'video':{'video':'video/mp4'},'live':{'still':'image/jpeg','motion':'video/mp4'}}

def publish(staged,path):
    staged.rename(path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def media_path(root,key):
    if not isinstance(key,str) or not KEY.fullmatch(key):raise ValueError('Invalid private storage key')
    return private_destination(Path(root)/key)

def retained_files(db):
    return [dict(row) for row in db.execute('SELECT storage_key,size,sha256 FROM media_chunks UNION SELECT storage_key,size,sha256 FROM media_components')]

def copy_retained(source_root,destination_root,entries):
    for entry in entries:
        source=media_path(source_root,entry['storage_key']);target=media_path(destination_root,entry['storage_key'])
        if type(entry['size']) is not int or entry['size']<1 or source.stat().st_size!=entry['size']:
            raise ValueError('Media integrity failed')
        target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        source_fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(source_fd,'rb') as input_stream,os.fdopen(fd,'wb') as output:
            shutil.copyfileobj(input_stream,output,1024*1024);output.flush();os.fsync(output.fileno())
        if target.stat().st_size!=entry['size'] or file_digest(target)!=entry['sha256']:
            raise ValueError('Media integrity failed')

def validate_format(path,mime):
    """Bounded container validation; decoder compatibility is a separate browser/device proof."""
    size=path.stat().st_size
    with path.open('rb') as stream:
        if mime=='image/jpeg':
            if stream.read(2)!=b'\xff\xd8':raise RuntimeErrorResult(415,'invalid_media')
            dimensions=False;scan=False
            while stream.tell()<size:
                marker=stream.read(2)
                if len(marker)!=2 or marker[0]!=255:raise RuntimeErrorResult(415,'invalid_media')
                if marker==b'\xff\xd9':break
                raw=stream.read(2)
                if len(raw)!=2:raise RuntimeErrorResult(415,'invalid_media')
                length=int.from_bytes(raw,'big')
                if length<2 or stream.tell()+length-2>size:raise RuntimeErrorResult(415,'invalid_media')
                segment=stream.read(length-2)
                if marker[1] in {0xC0,0xC1,0xC2}:
                    if len(segment)<6:raise RuntimeErrorResult(415,'invalid_media')
                    height=int.from_bytes(segment[1:3],'big');width=int.from_bytes(segment[3:5],'big')
                    dimensions=0<width<=4096 and 0<height<=4096
                if marker==b'\xff\xda':scan=True;break
            stream.seek(-2,2)
            if not dimensions or not scan or stream.read()!=b'\xff\xd9':raise RuntimeErrorResult(415,'invalid_media')
        elif mime=='video/mp4':
            boxes=set();avc=False;offset=0
            while offset<size:
                stream.seek(offset);header=stream.read(8)
                if len(header)!=8:raise RuntimeErrorResult(415,'invalid_media')
                length=int.from_bytes(header[:4],'big');kind=header[4:];head=8
                if length==1:
                    extended=stream.read(8)
                    if len(extended)!=8:raise RuntimeErrorResult(415,'invalid_media')
                    length=int.from_bytes(extended,'big');head=16
                if length==0:length=size-offset
                if length<head or offset+length>size:raise RuntimeErrorResult(415,'invalid_media')
                boxes.add(kind)
                if kind==b'moov':
                    if length>8*1024*1024:raise RuntimeErrorResult(415,'invalid_media')
                    body=stream.read(length-head);avc=b'avc1' in body and b'avcC' in body
                offset+=length
            if not {b'ftyp',b'moov',b'mdat'}<=boxes or not avc:raise RuntimeErrorResult(415,'invalid_media')
        else:raise RuntimeErrorResult(415,'invalid_media')

class MediaService:
    def __init__(self,store):
        self.store=store;self.ingest=IngestionService(store);self.budget=MEDIA_BUDGET

    def _asset(self,db,owner_id,asset_id):
        if not isinstance(asset_id,str):raise RuntimeErrorResult(400,'invalid_input')
        row=db.execute('''SELECT a.*,r.source_revision,r.media_type FROM assets a
          JOIN connections c ON c.id=a.connection_id AND c.owner_id=a.owner_id
          JOIN asset_revisions r ON r.asset_id=a.id AND r.revision=a.current_revision
          WHERE a.id=? AND a.owner_id=? AND '''+VISIBLE,(asset_id,owner_id)).fetchone()
        if row is None:raise RuntimeErrorResult(404,'not_found')
        return row

    def _upload(self,db,source,upload_id):
        if not isinstance(upload_id,str):raise RuntimeErrorResult(400,'invalid_input')
        row=db.execute('SELECT * FROM media_uploads WHERE id=? AND device_id=? AND owner_id=?',(upload_id,source['device_id'],source['owner_id'])).fetchone()
        if row is None:raise RuntimeErrorResult(404,'not_found')
        asset=self._asset(db,source['owner_id'],row['asset_id'])
        if asset['connection_id']!=source['id'] or asset['current_revision']!=row['revision']:raise RuntimeErrorResult(403,'revision_restricted')
        return row

    def _capacity(self,additional):
        total=0;root=self.store.root/'media'
        if root.exists():
            private_destination(root)
            for directory,dirs,files in os.walk(root,followlinks=False):
                for name in dirs:
                    if (Path(directory)/name).is_symlink():raise ValueError('Private media contains a symlink')
                for name in files:
                    path=Path(directory)/name
                    if path.is_symlink():raise ValueError('Private media contains a symlink')
                    total+=path.stat().st_size
        if total+additional>self.budget or shutil.disk_usage(self.store.root).free<additional+1024*1024*1024:
            raise RuntimeErrorResult(507,'media_capacity')

    def _write(self,key,content):
        path=media_path(self.store.root,key)
        if path.exists():
            if path.stat().st_size!=len(content) or file_digest(path)!=hashlib.sha256(content).hexdigest():raise RuntimeErrorResult(409,'staged_conflict')
            return
        self._capacity(len(content))
        staged=path.parent/('staged-'+identifier())
        fd=os.open(staged,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
        publish(staged,path)

    def begin(self,device_id,credential,asset_id,source_revision,role,mime,size,sha256,request_key):
        def begin(db,source):
            if (not _text(request_key,128) or not _text(source_revision,256) or not choice(role,{'still','video','motion'})
                or not choice(mime,{'image/jpeg','video/mp4'}) or type(size) is not int or not 1<=size<=MAX_COMPONENT
                or not isinstance(sha256,str) or not re.fullmatch('[a-f0-9]{64}',sha256)):raise RuntimeErrorResult(400,'invalid_component')
            asset=self._asset(db,source['owner_id'],asset_id)
            if asset['connection_id']!=source['id'] or asset['source_revision']!=source_revision:raise RuntimeErrorResult(403,'revision_restricted')
            if ROLES[asset['media_type']].get(role)!=mime:raise RuntimeErrorResult(400,'invalid_component')
            request_hash=digest(canonical([asset_id,source_revision,role,mime,size,sha256]))
            old=db.execute('SELECT * FROM media_uploads WHERE device_id=? AND request_key=?',(device_id,request_key)).fetchone()
            if old:
                if old['request_digest']!=request_hash:raise RuntimeErrorResult(409,'replay_conflict')
                return {'upload_id':old['id'],'next_offset':old['next_offset'],'state':old['state']}
            reserved=db.execute('SELECT COALESCE(sum(size),0)*2 FROM media_uploads').fetchone()[0]
            if reserved+size*2>self.budget or db.execute('SELECT count(*) FROM media_uploads').fetchone()[0]>=256:raise RuntimeErrorResult(507,'media_capacity')
            self._capacity(size*2)
            upload_id=identifier();folder=media_path(self.store.root,'media/'+upload_id+'/complete').parent
            folder.mkdir(mode=0o700,parents=True);folder.parent.chmod(0o700)
            db.execute('''INSERT INTO media_uploads(id,owner_id,device_id,asset_id,revision,role,mime,size,sha256,request_key,request_digest,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(upload_id,source['owner_id'],device_id,asset_id,asset['current_revision'],role,mime,size,sha256,request_key,request_hash,int(self.store.clock())))
            return {'upload_id':upload_id,'next_offset':0,'state':'active'}
        return self.ingest._run('media_begin',device_id,credential,begin)

    def chunk(self,device_id,credential,upload_id,offset,content):
        def append(db,source):
            upload=self._upload(db,source,upload_id)
            if type(offset) is not int or offset<0 or not isinstance(content,bytes) or not 1<=len(content)<=MAX_CHUNK or offset+len(content)>upload['size']:
                raise RuntimeErrorResult(400,'invalid_chunk')
            hashed=hashlib.sha256(content).hexdigest()
            old=db.execute('SELECT * FROM media_chunks WHERE upload_id=? AND offset=?',(upload_id,offset)).fetchone()
            if old:
                if old['sha256']!=hashed or old['size']!=len(content):raise RuntimeErrorResult(409,'replay_conflict')
                return {'upload_id':upload_id,'next_offset':offset+len(content)}
            if upload['state']!='active' or upload['next_offset']!=offset:raise RuntimeErrorResult(409,'checkpoint_conflict')
            if db.execute('SELECT count(*) FROM media_chunks WHERE upload_id=?',(upload_id,)).fetchone()[0]>=1024:raise RuntimeErrorResult(413,'too_many_chunks')
            key='media/'+upload_id+'/chunk-'+str(offset);self._write(key,content)
            db.execute('INSERT INTO media_chunks VALUES(?,?,?,?,?)',(upload_id,offset,len(content),hashed,key))
            db.execute('UPDATE media_uploads SET next_offset=? WHERE id=?',(offset+len(content),upload_id))
            return {'upload_id':upload_id,'next_offset':offset+len(content)}
        return self.ingest._run('media_chunk',device_id,credential,append)

    def complete(self,device_id,credential,upload_id):
        def finish(db,source):
            upload=self._upload(db,source,upload_id)
            if upload['next_offset']!=upload['size']:raise RuntimeErrorResult(409,'incomplete_upload')
            existing=db.execute('SELECT * FROM media_components WHERE asset_id=? AND revision=? AND role=?',(upload['asset_id'],upload['revision'],upload['role'])).fetchone()
            if existing:
                if existing['sha256']!=upload['sha256'] or existing['size']!=upload['size']:raise RuntimeErrorResult(409,'component_conflict')
                component_id=existing['id']
            else:
                key='media/'+upload_id+'/complete';path=media_path(self.store.root,key)
                if not path.exists():
                    self._capacity(upload['size'])
                    staged=path.parent/('staged-'+identifier())
                    fd=os.open(staged,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                    with os.fdopen(fd,'wb') as output:
                        for chunk in db.execute('SELECT * FROM media_chunks WHERE upload_id=? ORDER BY offset',(upload_id,)):
                            source_path=media_path(self.store.root,chunk['storage_key'])
                            if source_path.stat().st_size!=chunk['size'] or file_digest(source_path)!=chunk['sha256']:raise RuntimeErrorResult(409,'chunk_integrity')
                            with source_path.open('rb') as stream:shutil.copyfileobj(stream,output,1024*1024)
                        output.flush();os.fsync(output.fileno())
                    publish(staged,path)
                if path.stat().st_size!=upload['size'] or file_digest(path)!=upload['sha256']:raise RuntimeErrorResult(409,'component_integrity')
                validate_format(path,upload['mime']);component_id=identifier()
                db.execute('INSERT INTO media_components VALUES(?,?,?,?,?,?,?,?,?)',(component_id,upload['asset_id'],upload['revision'],upload['role'],upload['mime'],upload['size'],upload['sha256'],key,int(self.store.clock())))
            db.execute("UPDATE media_uploads SET state='complete',component_id=? WHERE id=?",(component_id,upload_id))
            return {'component_id':component_id,'state':'ready','size':upload['size'],'mime':upload['mime']}
        return self.ingest._run('media_complete',device_id,credential,finish)

    def library(self,token,asset_id):
        def read(db,owner):
            asset=self._asset(db,owner['id'],asset_id)
            components=[dict(row) for row in db.execute('SELECT id AS component_id,role,mime,size FROM media_components WHERE asset_id=? AND revision=? ORDER BY role',(asset_id,asset['current_revision']))]
            ready=set(ROLES[asset['media_type']])<={c['role'] for c in components}
            return {'asset_id':asset_id,'state':'ready' if ready else 'partial' if components else 'not_transferred','components':components}
        return self.store.read(token,'media_library',read)

    def read(self,token,component_id,start=0,length=MAX_CHUNK):
        def read(db,owner):
            if not isinstance(component_id,str) or type(start) is not int or start<0 or type(length) is not int or not 1<=length<=MAX_CHUNK:raise RuntimeErrorResult(400,'invalid_range')
            row=db.execute('SELECT * FROM media_components WHERE id=?',(component_id,)).fetchone()
            if row is None:raise RuntimeErrorResult(404,'not_found')
            asset=self._asset(db,owner['id'],row['asset_id'])
            if row['revision']!=asset['current_revision']:raise RuntimeErrorResult(404,'not_found')
            if start>=row['size']:raise RuntimeErrorResult(416,'invalid_range')
            path=media_path(self.store.root,row['storage_key'])
            if path.stat().st_size!=row['size'] or file_digest(path)!=row['sha256']:raise RuntimeErrorResult(503,'component_integrity')
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
            with os.fdopen(fd,'rb') as stream:stream.seek(start);content=stream.read(min(length,row['size']-start))
            return {'component_id':component_id,'content':content,'mime':row['mime'],'size':row['size'],'offset':start}
        return self.store.read(token,'media_read',read)
