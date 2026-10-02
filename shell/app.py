"""Small bounded ASGI adapter. Identity, audit and persistence live in runtime."""
import asyncio
import json
from ipaddress import ip_address
from http.cookies import SimpleCookie
import sqlite3
from urllib.parse import urlsplit
from runtime.store import RuntimeErrorResult

MAX_BODY = 65536

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
            required_unique={b'host',b'origin',b'cookie',b'x-csrf-token',b'content-type',b'content-length',b'cf-connecting-ip'}
            for key in required_unique:
                if sum(k.lower()==key for k,_ in header_list)>1:raise RuntimeErrorResult(400,'invalid_headers')
            request_headers={k.decode('latin1').lower():v.decode('latin1') for k,v in header_list}
            if request_headers.get('host') not in self.hosts:
                await asyncio.to_thread(self.store.record_denial);raise RuntimeErrorResult(403,'invalid_host')
            origin=request_headers.get('origin')
            if (origin is not None and origin!=self.origin) or (scope['method'] not in {'GET','HEAD','OPTIONS'} and origin!=self.origin):
                await asyncio.to_thread(self.store.record_denial);raise RuntimeErrorResult(403,'invalid_origin')
            if scope['method'] not in {'GET','POST'}:raise RuntimeErrorResult(405,'method_not_allowed')
            body=bytearray()
            try:
                async with asyncio.timeout(self.body_timeout):
                    while True:
                        part=await receive()
                        if part['type']=='http.disconnect':return
                        body.extend(part.get('body',b''))
                        if len(body)>MAX_BODY:raise RuntimeErrorResult(413,'too_large')
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
        content=json.dumps(payload,separators=(',',':'),ensure_ascii=True).encode()
        headers.extend([(b'content-type',b'application/json; charset=utf-8'),(b'cache-control',b'no-store'),
                        (b'x-content-type-options',b'nosniff'),(b'referrer-policy',b'no-referrer'),
                        (b'content-security-policy',b"default-src 'none'; frame-ancestors 'none'"),
                        (b'content-length',str(len(content)).encode())])
        if self.secure:headers.append((b'strict-transport-security',b'max-age=31536000'))
        await send({'type':'http.response.start','status':status,'headers':headers})
        await send({'type':'http.response.body','body':content})

    def _cookie(self,token,expires=False):
        value=f'{self.cookie_name}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={0 if expires else 86400}'
        if self.secure:value+='; Secure'
        return (b'set-cookie',value.encode())

    def handle(self,scope,headers,data):
        path=scope['path'];method=scope['method']
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
        cookie=SimpleCookie()
        try:cookie.load(headers.get('cookie',''))
        except Exception:raise RuntimeErrorResult(400,'invalid_cookie')
        token=cookie[self.cookie_name].value if self.cookie_name in cookie else ''
        if method=='GET':
            actions={'/api/session':self.store.session,'/api/overview':self.store.overview,
                     '/api/sources':self.store.sources,'/api/debug':self.store.debug}
            if path in actions:return 200,actions[path](token),[]
        if path=='/api/auth/logout' and method=='POST':
            if data:raise RuntimeErrorResult(400,'invalid_input')
            result=self.store.logout(token,headers.get('x-csrf-token',''))
            return 200,result,[self._cookie('',True)]
        # Unimplemented surfaces cannot reveal anything without authentication.
        self.store.session(token)
        if path in {'/api/photos','/api/blocks','/api/trips','/api/artifacts'}:
            raise RuntimeErrorResult(501,'not_available','This feature is not available yet.')
        raise RuntimeErrorResult(404,'not_found','This page is not available.')
