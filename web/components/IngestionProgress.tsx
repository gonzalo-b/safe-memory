'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Badge, Button } from '../vendor/memory-ds/react/core';
import { ApiError, request } from '../lib/api';
import type { Session } from '../lib/types';
import { Notice } from './Screens';

type Scan = {
  run_id: string; connection_id: string; state: string; coverage?: string; phase?: string;
  observed?: number; expected_count?: number; accepted?: number; excluded?: number;
  first_capture?: string | null; last_capture?: string | null; missing_date?: number;
  created_at?: number; completed_at?: number | null; retry_requested?: boolean;
};
export function IngestionProgress({ session, onUnauthorized }: { session: Session; onUnauthorized: (message?: string) => void }) {
  const [scans,setScans]=useState<Scan[] | null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[unavailable,setUnavailable]=useState(false),[message,setMessage]=useState('');
  const lifetime=useRef<AbortController | null>(null);
  const fail=useCallback((value: unknown,signal: AbortSignal)=>{
    if(signal.aborted)return;
    if(value instanceof ApiError && value.status===401)onUnauthorized('Your session has ended. Sign in again to continue.');
    else if(value instanceof ApiError && value.status===501)setUnavailable(true);
    else setError(value instanceof ApiError?value.message:'Import progress could not be read. Try again.');
  },[onUnauthorized]);
  const load=useCallback(async(signal:AbortSignal)=>{
    setBusy(true);setScans(null);setError('');setUnavailable(false);
    try {
      const result=await request<{scans:Scan[]}>('/api/ingestion/progress',{signal});
      if(!Array.isArray(result.scans))throw new Error('Invalid progress');
      if(!signal.aborted)setScans(result.scans);
    }catch(value){fail(value,signal);}finally{if(!signal.aborted)setBusy(false);}
  },[fail]);
  useEffect(()=>{const controller=new AbortController();lifetime.current=controller;void load(controller.signal);return()=>controller.abort();},[load]);
  async function retry(run_id:string){
    const controller=lifetime.current;if(!controller || controller.signal.aborted || busy)return;
    setBusy(true);setError('');setMessage('');
    try{
      const result=await request<{state:string}>('/api/ingestion/retry',{method:'POST',csrf:session.csrf_token,body:{run_id},signal:controller.signal});
      if(!controller.signal.aborted){
        setMessage(result.state==='complete'?'This scan is already complete.':'Resume requested. Open the iPhone connector to continue.');
        await load(controller.signal);
      }
    }catch(value){fail(value,controller.signal);}finally{if(!controller.signal.aborted)setBusy(false);}
  }
  return <section className="m-card memory-stack" aria-label="Import progress">
    <div className="m-card__head"><h2 className="m-card__title">Import progress</h2></div>
    <p className="m-help">Index progress does not mean media is ready. See each source’s separate media count.</p>
    {error&&<Notice error>{error}</Notice>}{message&&<Notice>{message}</Notice>}
    {unavailable&&<p className="m-help">Scan progress is not available in this runtime.</p>}
    {busy&&<p role="status" className="m-body">Refreshing import progress…</p>}
    {scans?.length===0&&<p className="m-body">No progressive scans have been started. Selected samples do not establish library coverage.</p>}
    {scans?.map(scan=><article className="m-card m-card--raised memory-stack" key={scan.run_id}>
      {scan.state==='restricted'?<p className="m-body">This scan is restricted. A fresh authorized scan is required.</p>:<>
        <div className="m-card__head"><h3 className="m-title">{scan.coverage==='authorized_full_scan'?'Authorized full-access scan':'Authorized limited selection'}</h3>
          <Badge>{scan.retry_requested?'Waiting for device':scan.state==='complete'?'Index complete':scan.state==='interrupted'?'Interrupted':'Indexing'}</Badge></div>
        <p className="m-body m-num">{scan.observed} of {scan.expected_count} observed</p>
        <dl className="m-kv"><dt>Phase</dt><dd>{scan.phase==='recent'?'Recent photos':'Older history'}</dd><dt>Accepted metadata</dt><dd>{scan.accepted}</dd><dt>Excluded observations</dt><dd>{scan.excluded}</dd><dt>Missing capture date</dt><dd>{scan.missing_date}</dd></dl>
        <p className="m-help memory-wrap">{scan.first_capture&&scan.last_capture?`Observed capture span: ${scan.last_capture} to ${scan.first_capture}`:'Capture span is unknown.'}</p>
        <p className="m-help">This is the connector’s frozen authorized enumeration. Photos may have changed since it started.</p>
        {scan.state!=='complete'&&<div><Button size="lg" variant="tonal" disabled={busy||scan.retry_requested} onClick={()=>void retry(scan.run_id)}>Request resume</Button></div>}
      </>}
    </article>)}
    <div><Button size="lg" disabled={busy} onClick={()=>lifetime.current&&void load(lifetime.current.signal)}>Refresh import progress</Button></div>
  </section>;
}
