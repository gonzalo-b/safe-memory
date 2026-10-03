"""Bounded owner original requests and explicit paired-device byte transfer."""
import base64,re
from runtime.originals import OriginalService
from runtime.media import MAX_CHUNK
from runtime.store import RuntimeErrorResult
from shell.media_http import MediaResponse

ORIGINAL_NATIVE={'/api/device/originals/'+name for name in ('pending','begin','chunk','complete','fail')}
class OriginalHTTP:
    def __init__(self,store):self.store=store;self.service=OriginalService(store)
    def native(self,path,data,credential,query):
        if query:raise RuntimeErrorResult(400,'invalid_query')
        routes={'pending':(self.service.pending,()),'begin':(self.service.begin,('request_id','resources')),'complete':(self.service.complete,('upload_id',)),'fail':(self.service.fail,('request_id','reason'))}
        action=path.rsplit('/',1)[-1]
        if action=='chunk':
            if set(data)!={'device_id','upload_id','offset','data'}:raise RuntimeErrorResult(400,'invalid_input')
            encoded=data['data']
            if not isinstance(encoded,str) or not encoded or len(encoded)>((MAX_CHUNK+2)//3)*4:raise RuntimeErrorResult(400,'invalid_chunk')
            try:content=base64.b64decode(encoded,validate=True)
            except (ValueError,TypeError):raise RuntimeErrorResult(400,'invalid_chunk')
            if base64.b64encode(content).decode()!=encoded:raise RuntimeErrorResult(400,'invalid_chunk')
            return self.service.chunk(data['device_id'],credential,data['upload_id'],data['offset'],content)
        fn,names=routes[action]
        if set(data)!={'device_id',*names}:raise RuntimeErrorResult(400,'invalid_input')
        return fn(data['device_id'],credential,*(data[n] for n in names))
    def owner(self,token,method,path,data,query,csrf,range_value):
        if query:raise RuntimeErrorResult(400,'invalid_query')
        asset=re.fullmatch('/api/photos/([a-f0-9]{32})/originals',path)
        retry=re.fullmatch('/api/originals/([a-f0-9]{32})/retry',path)
        component=re.fullmatch('/api/originals/components/([a-f0-9]{32})',path)
        if asset and method=='GET':return self.service.status(token,asset[1])
        if component and method in {'GET','HEAD'}:return MediaResponse(self.service,token,component[1],range_value,method=='HEAD',attachment=True)
        if method=='POST' and (asset or retry):
            if set(data)!={'request_key'}:raise RuntimeErrorResult(400,'invalid_input')
            return (self.service.request if asset else self.service.retry)(token,csrf,(asset or retry)[1],data['request_key'])
        self.store.session(token)
        raise RuntimeErrorResult(405 if asset or retry or component else 404,'method_not_allowed' if asset or retry or component else 'not_found')
