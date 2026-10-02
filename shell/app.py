"""Small bounded ASGI adapter. Identity, audit and persistence live in runtime."""
import asyncio
import json
from ipaddress import ip_address
from http.cookies import SimpleCookie
import sqlite3
from urllib.parse import urlsplit,parse_qs
import re
import base64
from runtime.store import RuntimeErrorResult
from runtime.pairing import PairingService
from runtime.ingestion import IngestionService,MAX_BATCH
from runtime.media import MediaService,MAX_CHUNK
from shell.media_http import MediaResponse

MAX_BODY = 65536
NATIVE_ROUTES={'/api/device/claim','/api/device/status','/api/device/permission',
               '/api/device/ingest/begin','/api/device/ingest/append','/api/device/ingest/finish',
               '/api/device/media/begin','/api/device/media/chunk','/api/device/media/complete'}

class MemoryApp:
    def __init__(self, store, *, origin, development=False, trusted_edge=None):
        parsed=urlsplit(origin)
        if parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password or not parsed.hostname:
            raise ValueError('Origin must be an exact scheme and authority')
        if development:
            if parsed.scheme!='http' or parsed.hostname not in {'localhost','127.0.0.1','::1'}:
                raise ValueError('Development origin must be HTTP loopback')
        elif parsed.scheme!='https':raise ValueError('Private deployment requires HTTPS')
        if trusted_edge not in {None,'cloudflare'} or (trusted_edge and development):
            raise ValueError('Trusted edge requires a supported HTTPS deployment')
        self.trusted_edge=trusted_edge
        self.body_timeout=15
        self.store=store;self.origin=origin;self.secure=not development
        self.pairing=PairingService(store);self.ingestion=IngestionService(store)
        self.media=MediaService(store)
        self.cookie_name='__Host-memory' if self.secure else 'memory_dev'
        self.hosts={parsed.netloc,'127.0.0.1:8766','localhost:8766'}

    async def __call__(self,scope,receive,send):
        if scope['type']=='lifespan':
            while True:
                message=await receive()
                if message['type']=='lifespan.startup':await send({'type':'lifespan.startup.complete'})
                elif message['type']=='lifespan.shutdown':
                    await send({'type':'lifespan.shutdown.complete'});return
        if scope['type']!='http':return
        status=500;headers=[];payload=None
        try:
            header_list=scope.get('headers',[])
            if len(header_list)>100 or sum(len(k)+len(v) for k,v in header_list)>16384:raise RuntimeErrorResult(400,'invalid_headers')
            required_unique={b'host',b'origin',b'cookie',b'x-csrf-token',b'authorization',b'content-type',b'content-length',b'cf-connecting-ip',b'range'}
            for key in required_unique:
                if sum(k.lower()==key for k,_ in header_list)>1:raise RuntimeErrorResult(400,'invalid_headers')
            request_headers={k.decode('latin1').lower():v.decode('latin1') for k,v in header_list}
            if request_headers.get('host') not in self.hosts:
                await asyncio.to_thread(self.store.record_denial);raise RuntimeErrorResult(403,'invalid_host')
            origin=request_headers.get('origin')
            native=scope['path'] in NATIVE_ROUTES
            if (origin is not None and origin!=self.origin) or (scope['method'] not in {'GET','HEAD','OPTIONS'} and origin!=self.origin and not native):
                await asyncio.to_thread(self.store.record_denial);raise RuntimeErrorResult(403,'invalid_origin')
            if scope['method'] not in {'GET','POST'} and not (scope['method']=='HEAD' and re.fullmatch('/api/media/[a-f0-9]{32}',scope['path'])):raise RuntimeErrorResult(405,'method_not_allowed')
            body=bytearray()
            body_limit=MAX_BATCH if scope['path']=='/api/device/ingest/append' else MAX_BODY
            if scope['path']=='/api/device/media/chunk':body_limit=6*1024*1024
            try:
                async with asyncio.timeout(self.body_timeout):
                    while True:
                        part=await receive()
                        if part['type']=='http.disconnect':return
                        body.extend(part.get('body',b''))
                        if len(body)>body_limit:raise RuntimeErrorResult(413,'too_large')
                        if not part.get('more_body'):break
            except TimeoutError:raise RuntimeErrorResult(408,'request_timeout','The request took too long.')
            data={}
            if scope['method']=='POST':
                if request_headers.get('content-type','').split(';')[0].strip()!='application/json':raise RuntimeErrorResult(400,'invalid_content_type')
                def invalid_constant(value):raise ValueError('Invalid JSON constant')
                try:data=json.loads(body,parse_constant=invalid_constant) if body else {}
                except (ValueError,UnicodeError,RecursionError):raise RuntimeErrorResult(400,'invalid_json')
                if not isinstance(data,dict):raise RuntimeErrorResult(400,'invalid_json')
            status,payload,headers=await asyncio.to_thread(self.handle,scope,request_headers,data)
        except RuntimeErrorResult as error:
            status=error.status;payload={'error':{'code':error.code,'message':error.message}}
        except (sqlite3.Error,OSError):
            status=503;payload={'error':{'code':'storage_unavailable','message':'Storage is temporarily unavailable.'}}
        except Exception:
            status=500;payload={'error':{'code':'internal_error','message':'The operation could not be completed.'}}
        if isinstance(payload,MediaResponse):
            await payload.send(send,self.secure);return
        content=json.dumps(payload,separators=(',',':'),ensure_ascii=True).encode()
        headers.extend([(b'content-type',b'application/json; charset=utf-8'),(b'cache-control',b'no-store'),
                        (b'x-content-type-options',b'nosniff'),(b'referrer-policy',b'no-referrer'),
                        (b'content-security-policy',b"default-src 'none'; frame-ancestors 'none'"),
                        (b'content-length',str(len(content)).encode())])
        if self.secure:headers.append((b'strict-transport-security',b'max-age=31536000'))
        # An unread request body must not keep a transport slot alive after refusal.
        if status in {408,413}:headers.append((b'connection',b'close'))
        await send({'type':'http.response.start','status':status,'headers':headers})
        await send({'type':'http.response.body','body':b'' if scope['method']=='HEAD' else content})

    def _cookie(self,token,expires=False):
        value=f'{self.cookie_name}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={0 if expires else 86400}'
        if self.secure:value+='; Secure'
        return (b'set-cookie',value.encode())

    def handle(self,scope,headers,data):
        path=scope['path'];method=scope['method']
        def exact(*names):
            if set(data)!=set(names):raise RuntimeErrorResult(400,'invalid_input')
            return [data[name] for name in names]
        if path=='/api/health' and method=='GET':return 200,{'status':'ok'},[]
        if path=='/api/auth/login' and method=='POST':
            if set(data)!={'username','password'}:raise RuntimeErrorResult(400,'invalid_input')
            remote=(scope.get('client') or ('unknown',0))[0]
            if self.trusted_edge:
                # Opt-in only for the verified tunnel -> loopback Next -> Python path.
                # Neither public socket clients nor arbitrary X-Forwarded-For are trusted.
                try:
                    if not ip_address(remote).is_loopback:raise ValueError('Untrusted peer')
                    remote=str(ip_address(headers.get('cf-connecting-ip','')))
                except ValueError:raise RuntimeErrorResult(403,'invalid_edge_identity')
            auth=self.store.login(data['username'],data['password'],remote)
            token=auth.pop('token');return 200,auth,[self._cookie(token)]
        if path in NATIVE_ROUTES:
            if method!='POST':raise RuntimeErrorResult(405,'method_not_allowed')
            if path=='/api/device/claim':
                return 200,self.pairing.claim(*exact('secret','device_name','library_id','credential')),[]
            match=re.fullmatch(r'Bearer ([A-Za-z0-9_-]{43})',headers.get('authorization',''))
            if not match:raise RuntimeErrorResult(401,'unauthorized')
            credential=match.group(1)
            if path=='/api/device/media/chunk':
                device_id,upload_id,offset,encoded=exact('device_id','upload_id','offset','data_base64')
                if not isinstance(encoded,str) or len(encoded)>((MAX_CHUNK+2)//3)*4:raise RuntimeErrorResult(400,'invalid_chunk')
                try:content=base64.b64decode(encoded,validate=True)
                except (ValueError,TypeError):raise RuntimeErrorResult(400,'invalid_chunk')
                return 200,self.media.chunk(device_id,credential,upload_id,offset,content),[]
            routes={
                '/api/device/status':(self.pairing.authenticate,()),
                '/api/device/permission':(self.ingestion.permission,('permission',)),
                '/api/device/ingest/begin':(self.ingestion.begin,('request_key','permission','phase','selected_ids')),
                '/api/device/ingest/append':(self.ingestion.append,('run_id','batch_key','sequence','checkpoint','assets')),
                '/api/device/ingest/finish':(self.ingestion.finish,('run_id',)),
                '/api/device/media/begin':(self.media.begin,('asset_id','source_revision','role','mime','size','sha256','request_key')),
                '/api/device/media/complete':(self.media.complete,('upload_id',)),
            }
            action,names=routes[path];values=exact('device_id',*names)
            return 200,action(values[0],credential,*values[1:]),[]
        cookie=SimpleCookie()
        try:cookie.load(headers.get('cookie',''))
        except Exception:raise RuntimeErrorResult(400,'invalid_cookie')
        token=cookie[self.cookie_name].value if self.cookie_name in cookie else ''
        component=re.fullmatch('/api/media/([a-f0-9]{32})',path)
        if component and method in {'GET','HEAD'}:
            result=MediaResponse(self.media,token,component.group(1),headers.get('range'),method=='HEAD')
            return result.status,result,[]
        if method=='GET':
            media_list=re.fullmatch('/api/photos/([a-f0-9]{32})/media',path)
            if media_list:return 200,self.media.library(token,media_list.group(1)),[]
            actions={'/api/session':self.store.session,'/api/overview':self.store.overview,
                     '/api/sources':self.store.sources,'/api/debug':self.store.debug,
                     '/api/pairing/pending':self.pairing.pending,'/api/devices':self.pairing.devices}
            if path in actions:return 200,actions[path](token),[]
            if path=='/api/photos':
                try:
                    query=parse_qs(scope.get('query_string',b'').decode('ascii'),keep_blank_values=True,max_num_fields=4)
                    if set(query)-{'limit','offset','media_type','day'} or any(len(v)!=1 for v in query.values()):raise ValueError()
                    args={key:(int(value[0]) if key in {'limit','offset'} else value[0]) for key,value in query.items()}
                except (ValueError,UnicodeError):raise RuntimeErrorResult(400,'invalid_query')
                return 200,self.ingestion.assets(token,**args),[]
        if method=='POST':
            csrf=headers.get('x-csrf-token','')
            owner_actions={
                '/api/pairing/start':(self.pairing.start,()),
                '/api/pairing/confirm':(self.pairing.confirm,('claim_id','fingerprint')),
                '/api/devices/revoke':(self.pairing.revoke,('device_id',)),
                '/api/sources/policy':(self.ingestion.configure,('connection_id','include_hidden','include_shared_library','include_shared_albums')),
            }
            if path in owner_actions:
                action,names=owner_actions[path]
                return 200,action(token,csrf,*exact(*names)),[]
        if path=='/api/auth/logout' and method=='POST':
            if data:raise RuntimeErrorResult(400,'invalid_input')
            result=self.store.logout(token,headers.get('x-csrf-token',''))
            return 200,result,[self._cookie('',True)]
        # Unimplemented surfaces cannot reveal anything without authentication.
        self.store.session(token)
        if path in {'/api/photos','/api/blocks','/api/trips','/api/artifacts'}:
            raise RuntimeErrorResult(501,'not_available','This feature is not available yet.')
        raise RuntimeErrorResult(404,'not_found','This page is not available.')
