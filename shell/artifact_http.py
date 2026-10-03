"""Exact owner-only Gallery transport; runtime owns access, writes and audit."""
import re
from urllib.parse import parse_qs
from runtime.artifacts import ArtifactService
from runtime.store import RuntimeErrorResult

class ArtifactHTTP:
    def __init__(self,store):self.store=store;self.service=ArtifactService(store)
    def handle(self,token,method,path,data,raw_query,csrf):
        def body(required,optional=()):
            if not set(required)<=set(data) or set(data)-set(required)-set(optional):raise RuntimeErrorResult(400,'invalid_input')
            return data
        try:
            values=parse_qs(raw_query.decode('ascii'),keep_blank_values=True,max_num_fields=2)
            allowed={'limit','cursor'} if path=='/api/artifacts' and method=='GET' else set()
            if set(values)-allowed or any(len(v)!=1 for v in values.values()):raise ValueError()
            query={key:int(value[0]) if key=='limit' else value[0] for key,value in values.items()}
        except (ValueError,UnicodeError):raise RuntimeErrorResult(400,'invalid_query')
        if path=='/api/artifacts':
            if method=='GET':return self.service.list(token,**query)
            if method=='POST':return self.service.create(token,csrf,**body(('request_key','title'),('asset_ids','layout','trip_id','expected_trip_revision')))
        match=re.fullmatch('/api/artifacts/([a-f0-9]{32})(?:/(edit|recompose|debug))?',path)
        if match:
            identity,action=match.groups()
            if method=='GET' and action is None:return self.service.get(token,identity)
            if method=='GET' and action=='debug':return self.service.debug(token,identity)
            if method=='POST' and action=='edit':return self.service.edit(token,csrf,artifact_id=identity,**body(('request_key','expected_revision','patch')))
            if method=='POST' and action=='recompose':return self.service.recompose(token,csrf,artifact_id=identity,**body(('request_key','expected_revision'),('asset_ids','trip_id','expected_trip_revision')))
        self.store.session(token)
        raise RuntimeErrorResult(405 if match or path=='/api/artifacts' else 404,'method_not_allowed' if match or path=='/api/artifacts' else 'not_found')
