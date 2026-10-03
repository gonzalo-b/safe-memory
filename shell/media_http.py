"""Authenticated streaming; every later chunk checks current policy again."""
import asyncio
import re
from runtime.media import MAX_CHUNK
from runtime.store import RuntimeErrorResult

class MediaResponse:
    def __init__(self,service,token,component_id,range_value=None,head=False):
        self.service=service;self.token=token;self.component_id=component_id;self.head=head
        info=service.read(token,component_id,0,1);self.size=info['size'];self.mime=info['mime']
        self.start=0;self.end=self.size-1;self.status=200
        if range_value is not None and not head:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_value)
            if not match or not any(match.groups()):raise RuntimeErrorResult(416,'invalid_range')
            first,last=match.groups()
            if not first:
                suffix=int(last)
                if suffix<1:raise RuntimeErrorResult(416,'invalid_range')
                self.start=max(0,self.size-suffix)
            else:
                self.start=int(first);self.end=min(int(last),self.size-1) if last else self.size-1
            if self.start>self.end or self.start>=self.size:raise RuntimeErrorResult(416,'invalid_range')
            self.status=206

    async def send(self,send,secure):
        headers=[(b'content-type',self.mime.encode()),(b'content-length',str(self.end-self.start+1).encode()),
                 (b'cache-control',b'no-store'),(b'accept-ranges',b'bytes'),(b'x-content-type-options',b'nosniff'),
                 (b'referrer-policy',b'no-referrer'),(b'cross-origin-resource-policy',b'same-origin'),
                 (b'content-security-policy',b"default-src 'none'; frame-ancestors 'none'")]
        if self.status==206:headers.append((b'content-range',f'bytes {self.start}-{self.end}/{self.size}'.encode()))
        if secure:headers.append((b'strict-transport-security',b'max-age=31536000'))
        async with asyncio.timeout(30):
            await send({'type':'http.response.start','status':self.status,'headers':headers})
            if self.head:
                await send({'type':'http.response.body','body':b''});return
            offset=self.start;part=None
            while offset<=self.end:
                if part is None:
                    part=await asyncio.to_thread(self.service.read,self.token,self.component_id,offset,min(MAX_CHUNK,self.end-offset+1))
                content=part['content'];offset+=len(content)
                await send({'type':'http.response.body','body':content,'more_body':offset<=self.end})
                part=None
        # A later denial propagates after headers and closes the incomplete response.
        # It never appends an error payload to otherwise private media bytes.
