"""Strict owner-only knowledge routes; runtime owns policy, audit and mutations.

POST answer is a read: exact Origin + owner session + audit are required by the
ASGI adapter/runtime. Its CSRF header is not verified. All mutations pass the
header to KnowledgeService, which verifies CSRF inside the write transaction.
"""
import re
from urllib.parse import parse_qs
from runtime.knowledge import KnowledgeService
from runtime.store import RuntimeErrorResult

class KnowledgeHTTP:
    def __init__(self,store):self.store=store;self.service=KnowledgeService(store)
    def handle(self,token,method,path,data,raw_query,csrf):
        if not path.startswith('/api/knowledge/'):return None
        def body(required,optional=()):
            if not set(required)<=set(data) or set(data)-set(required)-set(optional):raise RuntimeErrorResult(400,'invalid_input')
            return data
        def query(paged=False):
            try:
                values=parse_qs(raw_query.decode('ascii'),keep_blank_values=True,max_num_fields=2)
                if set(values)-({'limit','cursor'} if paged else set()) or any(len(v)!=1 for v in values.values()):raise ValueError()
                return {key:int(value[0]) if key=='limit' else value[0] for key,value in values.items()}
            except (ValueError,UnicodeError):raise RuntimeErrorResult(400,'invalid_query')
        if method=='GET':
            if path=='/api/knowledge/catalog':query();return self.service.catalog(token)
            if path=='/api/knowledge/trips':return self.service.trips(token,**query(True))
            if path=='/api/knowledge/areas':return self.service.habitual_areas(token,**query(True))
            match=re.fullmatch('/api/knowledge/(evidence|trips)/([a-f0-9]{32})',path)
            if match:
                if match[1]=='evidence':query();return self.service.evidence(token,match[2])
                return self.service.trip(token,match[2],**query(True))
        if method=='POST':
            query()
            if path=='/api/knowledge/answer':
                values=body(('capability',),('params','scope','limit','cursor'))
                return self.service.answer(token,**values)
            if path=='/api/knowledge/rebuild':
                return self.service.rebuild(token,csrf,**body(('request_key',),('policy',)))
            if path=='/api/knowledge/trips/correct':
                return self.service.correct_trip(token,csrf,**body(('request_key','action'),('trip_id','expected_revision','payload')))
            if path=='/api/knowledge/areas':
                return self.service.put_habitual_area(token,csrf,**body(('request_key','area'),('area_id','expected_revision')))
        self.store.session(token)
        raise RuntimeErrorResult(405 if path in {'/api/knowledge/catalog','/api/knowledge/answer','/api/knowledge/rebuild','/api/knowledge/trips','/api/knowledge/trips/correct','/api/knowledge/areas'} else 404,'method_not_allowed' if path in {'/api/knowledge/catalog','/api/knowledge/answer','/api/knowledge/rebuild','/api/knowledge/trips','/api/knowledge/trips/correct','/api/knowledge/areas'} else 'not_found')
