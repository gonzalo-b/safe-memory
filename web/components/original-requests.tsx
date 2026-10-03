'use client';
import {useEffect,useRef,useState} from 'react';
import {Badge,Button} from '../vendor/memory-ds/react/core';
import {ApiError,request} from '../lib/api';
import {originalPath,originalRequest,validOriginalStatus,type OriginalStatus,type OriginalRequest,type OriginalResource} from '../lib/originals';
import type {Session} from '../lib/types';
import {Notice} from './Screens';
const labels={waiting_for_device:'Waiting for iPhone',transferring:'Transferring original',failed:'Original transfer failed',ready:'Original ready'};
const reasons:Record<string,string>={icloud_unavailable:'The original could not be retrieved from iCloud.',capacity:'A transfer or storage limit was reached.',source_unavailable:'The original was unavailable in Photos.',permission_changed:'Photos access changed.',revision_changed:'The source item changed.',unsupported_resource:'The original resource could not be verified.'};
export function OriginalRequests({assetId,onUnauthorized,onFailure}:{assetId:string;onUnauthorized:(message?:string)=>void;onFailure?:()=>void}){
 const [status,setStatus]=useState<OriginalStatus|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const active=useRef<AbortController|null>(null),pending=useRef<{identity:string;action:'status'|'retry';key:string}|null>(null);
 useEffect(()=>()=>active.current?.abort(),[]);
 useEffect(()=>{active.current?.abort();setStatus(null);setError('');setBusy(false);pending.current=null;},[assetId]);
 function begin(){active.current?.abort();const c=new AbortController();active.current=c;setStatus(null);setError('');setBusy(true);return c;}
 function fail(value:unknown,c:AbortController){if(c.signal.aborted)return;setStatus(null);if(value instanceof ApiError&&value.status===401)onUnauthorized('Your session has ended. Sign in again.');else {setError(value instanceof ApiError?value.message:'The response could not be read.');if(value instanceof ApiError&&[403,404].includes(value.status))onFailure?.();}}
 async function refresh(){const c=begin();try{const result=await originalRequest<OriginalStatus>(assetId,'status',{signal:c.signal});if(!validOriginalStatus(result,assetId))throw new ApiError(502,'invalid_response','The response could not be read.');if(!c.signal.aborted){pending.current=null;setStatus(result);}}catch(value){fail(value,c);}finally{if(!c.signal.aborted)setBusy(false);}}
 async function mutate(identity:string,action:'status'|'retry'){
  if(pending.current?.identity!==identity||pending.current.action!==action)pending.current={identity,action,key:crypto.randomUUID()};
  const mutation=pending.current,c=begin();try{
   const session=await request<Session>('/api/session',{signal:c.signal});
   const result=await originalRequest<OriginalRequest>(identity,action,{method:'POST',csrf:session.csrf_token,key:mutation.key,signal:c.signal});
   if(!validOriginalStatus({request:result},assetId))throw new ApiError(502,'invalid_response','The response could not be read.');
   if(!c.signal.aborted){pending.current=null;setStatus({request:result});}
  }catch(value){fail(value,c);}finally{if(!c.signal.aborted)setBusy(false);}
 }
 async function download(resource:OriginalResource){if(!resource.component_id)return;const saved=status,c=begin();try{
  await originalRequest<void>(resource.component_id,'download',{method:'HEAD',signal:c.signal});if(c.signal.aborted)return;
  const link=document.createElement('a');link.href=originalPath(resource.component_id,'download');link.download=resource.original_filename;link.rel='noreferrer';link.click();setStatus(saved);
 }catch(value){fail(value,c);}finally{if(!c.signal.aborted)setBusy(false);}}
 const current=status?.request;
 return <section className="m-card memory-stack" aria-label="Original resources"><h3 className="m-card__title">Original resources</h3>
  <p className="m-help">Request exact source files separately from playback copies. Open the iPhone connector to check and send requests; iCloud retrieval requires your explicit choice there. Files over the transfer limit remain unavailable.</p>
  {busy&&<p role="status">Checking private original…</p>}{error&&<Notice error>{error}</Notice>}
  {current&&<><div><Badge>{labels[current.state]}</Badge></div><p className="m-code memory-wrap">Request {current.request_id}</p>
   {current.state==='waiting_for_device'&&<p className="m-body">The request is saved. This does not indicate that your iPhone is online.</p>}
   {current.state==='transferring'&&<p className="m-body">All original components must finish before download is available.</p>}
   {current.state==='failed'&&<><p className="m-help">{reasons[current.error_code||'']||'The connector reported a transfer failure.'}</p><Button size="lg" disabled={busy} onClick={()=>void mutate(current.request_id,'retry')}>Retry original request</Button></>}
   {current.state==='ready'&&<ul className="memory-stack">{current.resources.map(resource=><li key={resource.ordinal} className="memory-stack"><span className="m-body memory-wrap">{resource.original_filename}</span><span className="m-help">{resource.resource_type} · {(resource.size/1048576).toFixed(2)} MiB</span><Button size="lg" disabled={busy} onClick={()=>void download(resource)}>Download {resource.original_filename}</Button></li>)}</ul>}
  </>}
  {status?.request===null&&<><p className="m-help">No original has been requested for this revision.</p><Button size="lg" disabled={busy} onClick={()=>void mutate(assetId,'status')}>Request original</Button></>}
  {pending.current&&error&&<Button size="lg" disabled={busy} onClick={()=>void mutate(pending.current!.identity,pending.current!.action)}>Retry same request</Button>}
  <Button variant="ghost" size="lg" disabled={busy} onClick={()=>void refresh()}>Refresh original status</Button>
 </section>;
}
