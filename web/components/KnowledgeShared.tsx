'use client';
import { useCallback,useEffect,useId,useRef,useState,type ReactNode } from 'react';
import { Badge,Button } from '../vendor/memory-ds/react/core';
import { ApiError,request } from '../lib/api';
import type { Coverage,KnowledgeFact } from '../lib/knowledge-types';
import { Notice } from './Screens';
export type OwnerProps={onUnauthorized:(message?:string)=>void};
export function usePrivateRequest(onUnauthorized:OwnerProps['onUnauthorized']){
  const active=useRef<AbortController|null>(null);const [busy,setBusy]=useState(false),[error,setError]=useState('');
  useEffect(()=>()=>active.current?.abort(),[]);
  const clear=useCallback(()=>{active.current?.abort();setBusy(false);setError('');},[]);
  const run=useCallback(async<T,>(path:string,options:Parameters<typeof request>[1],accept:(value:T)=>void)=>{
    active.current?.abort();const controller=new AbortController();active.current=controller;setBusy(true);setError('');
    try {const value=await request<T>(path,{...options,signal:controller.signal});if(!controller.signal.aborted)accept(value);}
    catch(value){if(controller.signal.aborted)return;if(value instanceof ApiError&&value.status===401)onUnauthorized('Your session has ended. Sign in again to continue.');else setError(value instanceof ApiError?value.message:'The response could not be read. Refresh and try again.');}
    finally{if(!controller.signal.aborted)setBusy(false);}
  },[onUnauthorized]);
  return {busy,error,run,clear};
}
export function useMutationKey(){
  const pending=useRef<{body:string;key:string}|null>(null);
  return {forBody:(body:unknown)=>{const serialized=JSON.stringify(body);if(pending.current?.body!==serialized)pending.current={body:serialized,key:crypto.randomUUID()};return pending.current.key;},reset:()=>{pending.current=null;}};
}
export function Field({label,value,onChange,type='text',required=false,min,max,step,help}:{label:string;value:string;onChange:(value:string)=>void;type?:string;required?:boolean;min?:string;max?:string;step?:string;help?:string}){
  const helpId=useId();
  return <label className="m-field"><span className="m-label">{label}</span><input className="m-input m-input--touch memory-knowledge-input" aria-label={label} aria-describedby={help?helpId:undefined} type={type} value={value} onChange={event=>onChange(event.target.value)} required={required} min={min} max={max} step={step} maxLength={200}/>{help&&<span id={helpId} className="m-help">{help}</span>}</label>;
}
export function DateField(props:{label:string;value:string;onChange:(value:string)=>void;required?:boolean;help?:string}){return <Field {...props} type="date" min="0001-01-01" max="9999-12-31"/>;}
export function CoverageView({coverage}:{coverage:Coverage}){
  return <div className="memory-stack"><p className="m-help">Current authorized sample. Whole-library coverage is not established by these answers.</p><dl className="m-kv m-num"><dt>Indexed records</dt><dd>{coverage.indexed_records.toLocaleString()}</dd><dt>Current records awaiting rebuild</dt><dd>{coverage.unindexed_current_records.toLocaleString()}</dd><dt>Unknown local day</dt><dd>{coverage.unknown_time_records.toLocaleString()}</dd><dt>Located observations</dt><dd>{coverage.located_records.toLocaleString()}</dd></dl></div>;
}
export function FactCard({fact,inspect}:{fact:KnowledgeFact;inspect?:(id:string)=>void}){
  return <article className="m-card m-card--raised memory-stack">
    <div className="m-card__head"><h3 className="m-card__title m-num">{fact.capture_day||'Unknown local day'}</h3><Badge>{fact.media_type||'Unknown media type'}</Badge></div>
    {fact.location?.place&&<p className="m-body memory-wrap">{fact.location.place}</p>}
    <dl className="m-kv"><dt>Capture timestamp</dt><dd className="m-num">{fact.capture_time||'Unknown capture time'}</dd><dt>Coordinates</dt><dd className="m-num">{fact.location?.lat!=null&&fact.location?.lon!=null?`${fact.location.lat}, ${fact.location.lon}`:'Unavailable'}</dd><dt>Explicit geography</dt><dd>{[fact.geography?.city,fact.geography?.country||fact.geography?.country_code].filter(Boolean).join(', ')||'Unavailable'}</dd></dl>
    <p className="m-help">{fact.owner_presence==='owner'?'Owner presence reported by source':fact.owner_presence==='third_party'?'Third-party provenance':'Owner presence unknown'}</p>
    <p className="m-help">An observation does not establish continuous presence.</p>
    {!!fact.people?.length&&<p className="m-body">Source People: {fact.people.map(person=>person.name).join(', ')}</p>}
    {fact.evidence&&<><p className="m-code memory-wrap">{fact.evidence.asset_id} · revision {fact.evidence.revision}</p>{inspect&&<div><Button size="lg" onClick={()=>inspect(fact.evidence!.asset_id)}>Inspect evidence</Button></div>}</>}
  </article>;
}
export function EvidencePanel({id,onClose,onUnauthorized,onFailure}:{id:string;onClose:()=>void;onFailure:()=>void}&OwnerProps){
  const {run,busy,error}=usePrivateRequest(onUnauthorized);const [fact,setFact]=useState<KnowledgeFact|null>(null);const heading=useRef<HTMLHeadingElement>(null);
  useEffect(()=>{if(error)onFailure();},[error,onFailure]);
  useEffect(()=>{const previous=document.activeElement;setFact(null);void run<KnowledgeFact>('/api/knowledge/evidence/'+id,{},value=>{if(!value.location||!value.geography)throw new Error('Invalid fact');setFact(value);});heading.current?.focus();return()=>{if(previous instanceof HTMLElement&&document.contains(previous))previous.focus();};},[id,run]);
  return <section className="m-card memory-stack" aria-label="Evidence details"><div className="m-card__head"><h2 tabIndex={-1} ref={heading} className="m-card__title">Evidence details</h2><Button size="lg" variant="ghost" onClick={onClose}>Close evidence</Button></div>{busy&&<p role="status">Checking current evidence…</p>}{error&&<Notice error>{error}</Notice>}{fact&&<FactCard fact={fact}/>}</section>;
}
export function Pages({next,onNext,onFirst,busy,first,label}:{next:string|null|undefined;onNext:()=>void;onFirst:()=>void;busy:boolean;first:boolean;label:string}){
  return <nav className="memory-actions" aria-label={label+' pages'}><Button size="lg" disabled={busy||first} onClick={onFirst}>First {label} page</Button><Button size="lg" disabled={busy||!next} onClick={onNext}>Next {label} page</Button></nav>;
}
export function Toggle({label,checked,onChange}:{label:string;checked:boolean;onChange:()=>void}){
  return <button className="m-btn m-btn--neutral memory-comparison" type="button" role="checkbox" aria-checked={checked} onClick={onChange}><span className="m-check" aria-hidden="true">{checked?'✓':''}</span>{label}</button>;
}
export function OperationStatus({busy,error,children}:{busy:boolean;error:string;children:ReactNode}){return <>{busy&&<p className="m-body" role="status">{children}</p>}{error&&<Notice error>{error}</Notice>}</>;}
