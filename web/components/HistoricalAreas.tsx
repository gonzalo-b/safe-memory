'use client';
import { useCallback,useEffect,useState,type FormEvent } from 'react';
import Link from 'next/link';
import { Badge,Button } from '../vendor/memory-ds/react/core';
import type { Session } from '../lib/types';
import type { HistoricalArea,KnowledgePage } from '../lib/knowledge-types';
import { DateField,Field,OperationStatus,Pages,Toggle,useMutationKey,usePrivateRequest,type OwnerProps } from './KnowledgeShared';
import { Notice } from './Screens';
type Draft={id?:string;revision?:number;label:string;lat:string;lon:string;radius:string;start:string;end:string;confirmed:boolean};
export function HistoricalAreas({session,onUnauthorized}:{session:Session}&OwnerProps){
  const {run,busy,error}=usePrivateRequest(onUnauthorized);const keys=useMutationKey();
  const [data,setData]=useState<KnowledgePage<HistoricalArea>|null>(null),[draft,setDraft]=useState<Draft|null>(null),[cursor,setCursor]=useState<string|null>(null),[message,setMessage]=useState('');
  const load=useCallback((next:string|null=null)=>{setData(null);setDraft(null);setCursor(next);void run<KnowledgePage<HistoricalArea>>('/api/knowledge/areas',{query:{limit:20,...(next?{cursor:next}:{})}},value=>{if(!Array.isArray(value.data))throw new Error('Invalid areas');setData(value);});},[run]);
  useEffect(()=>load(),[load]);
  function edit(area?:HistoricalArea){setMessage('');setDraft(area?{id:area.id,revision:area.revision,label:area.label,lat:String(area.lat),lon:String(area.lon),radius:String(area.radius_km),start:area.start,end:area.end,confirmed:Boolean(area.confirmed)}:{label:'',lat:'',lon:'',radius:'15',start:'',end:'',confirmed:false});setData(null);}
  function update(key:keyof Draft,value:string|boolean){setDraft(old=>old?{...old,[key]:value}:old);}
  function save(event:FormEvent){
    event.preventDefault();if(!draft)return;
    const body={area:{label:draft.label,lat:Number(draft.lat),lon:Number(draft.lon),radius_km:Number(draft.radius),start:draft.start,end:draft.end,confirmed:draft.confirmed},...(draft.id?{area_id:draft.id,expected_revision:draft.revision}:{})};
    setDraft(null);setData(null);setMessage('');
    void run<{area_id:string;revision:number}>('/api/knowledge/areas',{method:'POST',csrf:session.csrf_token,body:{...body,request_key:keys.forBody(body)}},value=>{if(typeof value.area_id!=='string'||typeof value.revision!=='number')throw new Error('Invalid area receipt');keys.reset();setMessage('Historical area saved.');load();});
  }
  return <section className="memory-stack" aria-label="Historical habitual areas"><div className="m-card memory-stack"><h2 className="m-title">Historical areas</h2><p className="m-body memory-copy">Suggestions do not suppress trips until you explicitly confirm them. Each area applies only to its own historical interval; several areas may coexist.</p><div className="memory-actions"><Button variant="tonal" size="lg" onClick={()=>edit()} disabled={busy}>Add historical area</Button><Button size="lg" onClick={()=>load()} disabled={busy}>Refresh areas</Button></div></div>
    <OperationStatus busy={busy} error={error}>Refreshing historical areas…</OperationStatus>{message&&<Notice><div><p>{message}</p><p>Rebuild Photos knowledge to apply commuting exclusions. <Link href="/debug" prefetch={false}>Open Debug</Link></p></div></Notice>}
    {draft&&<form className="m-card memory-stack memory-knowledge-form" aria-label="Historical area" onSubmit={save}>
      <h3 className="m-title">{draft.id?'Review historical area':'New historical area'}</h3><Field label="Area label" value={draft.label} onChange={value=>update('label',value)} required/>
      <div className="memory-grid"><Field label="Latitude" type="number" min="-90" max="90" step="any" value={draft.lat} onChange={value=>update('lat',value)} required/><Field label="Longitude" type="number" min="-180" max="180" step="any" value={draft.lon} onChange={value=>update('lon',value)} required/></div>
      <Field label="Radius in kilometres" type="number" min="0.001" max="1000" step="any" value={draft.radius} onChange={value=>update('radius',value)} required/>
      <div className="memory-grid"><DateField label="Area start" value={draft.start} onChange={value=>update('start',value)} required/><DateField label="Area end" value={draft.end} onChange={value=>update('end',value)} required help="Exclusive end date for this historical area."/></div>
      <Toggle label="Use this confirmed historical area for commuting" checked={draft.confirmed} onChange={()=>update('confirmed',!draft.confirmed)}/>
      <div className="memory-actions"><Button type="submit" variant="primary" size="lg">Save historical area</Button><Button variant="ghost" size="lg" onClick={()=>load()}>Cancel area change</Button></div>
    </form>}
    {data?.data.length===0&&<p className="m-body">No currently admissible historical areas.</p>}
    {data?.data.map(area=><article className="m-card memory-stack" key={area.id}><div className="m-card__head"><h3 className="m-card__title memory-knowledge-title">{area.label}</h3><Badge>{area.confirmed?'Confirmed area':'Inferred suggestion'}</Badge></div><dl className="m-kv m-num"><dt>Coordinates</dt><dd>{area.lat}, {area.lon}</dd><dt>Radius</dt><dd>{area.radius_km} km</dd><dt>Historical interval</dt><dd>{area.start} to {area.end} (exclusive)</dd></dl><div><Button size="lg" aria-label={'Review area '+area.label} onClick={()=>edit(area)}>Review area</Button></div></article>)}
    {data&&<Pages label="area" next={data.next_cursor} onNext={()=>load(data.next_cursor)} onFirst={()=>load()} busy={busy} first={cursor===null}/>}
  </section>;
}
