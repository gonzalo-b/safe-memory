'use client';
import {useEffect,useState} from 'react';
import {Button} from '../vendor/memory-ds/react/core';
import type {Photos,PhotoMetadata} from '../lib/types';
import type {KnowledgePage,Trip} from '../lib/knowledge-types';
import {request} from '../lib/api';
import {DateField,Toggle} from './KnowledgeShared';
import {Notice} from './Screens';
export type Selection={mode:'photos'|'trip'|'retained';ids:string[];trip:{id:string;revision:number}|null};
export function ArtifactSelection({value,onChange,onFailure,retained=false,photosOnly=false}:{value:Selection;onChange:(v:Selection)=>void;onFailure:(e:unknown)=>void;retained?:boolean;photosOnly?:boolean}){
 const [photos,setPhotos]=useState<PhotoMetadata[]|null>(null),[trips,setTrips]=useState<KnowledgePage<Trip>|null>(null),[busy,setBusy]=useState(false),[offset,setOffset]=useState(0),[cursor,setCursor]=useState<string|null>(null),[day,setDay]=useState(''),[appliedDay,setAppliedDay]=useState('');
 useEffect(()=>{const c=new AbortController();setPhotos(null);setTrips(null);if(value.mode==='retained')return;setBusy(true);
 const fetch=value.mode==='photos'?request<Photos>('/api/photos',{signal:c.signal,query:{limit:13,offset,...(appliedDay?{day:appliedDay}:{})}}).then(v=>{if(!Array.isArray(v.assets))throw new Error('Invalid Photos');if(!c.signal.aborted)setPhotos(v.assets);}):request<KnowledgePage<Trip>>('/api/knowledge/trips',{signal:c.signal,query:{limit:12,...(cursor?{cursor}:{})}}).then(v=>{if(!Array.isArray(v.data))throw new Error('Invalid trips');if(!c.signal.aborted)setTrips(v);});
 void fetch.catch(e=>{if(!c.signal.aborted)onFailure(e);}).finally(()=>{if(!c.signal.aborted)setBusy(false);});return()=>c.abort();
 },[value.mode,offset,cursor,appliedDay,onFailure]);
 function mode(mode:Selection['mode']){if(mode===value.mode)return;setOffset(0);setCursor(null);onChange({mode,ids:[],trip:null});}
 return <section className="memory-stack" aria-label="Gallery selection"><h3 className="m-title">Choose evidence</h3><p className="m-help">Only currently authorized results are selectable. Up to200 members. No selection is stored in your browser.</p><div className="memory-actions">{retained&&<Button size="lg" aria-pressed={value.mode==='retained'} onClick={()=>mode('retained')}>Retained membership</Button>}<Button size="lg" aria-pressed={value.mode==='photos'} onClick={()=>mode('photos')}>Choose Photos</Button>{!photosOnly&&<Button size="lg" aria-pressed={value.mode==='trip'} onClick={()=>mode('trip')}>Trip snapshot</Button>}</div>
 {value.mode==='photos'&&<><div className="memory-actions"><DateField label="Selection local day" value={day} onChange={setDay}/><Button size="lg" onClick={()=>{setOffset(0);setAppliedDay(day);}}>Filter selection</Button></div><p className="m-help m-num">{value.ids.length} selected assets</p></>}
 {value.mode==='trip'&&<Notice>A trip is saved as a snapshot of its current revision. Hidden assets are omitted. Future imports do not add members automatically.</Notice>}
 {busy&&<p role="status">Loading authorized selection…</p>}
 {photos&&<><div className="memory-grid">{photos.slice(0,12).map(p=><article key={p.id} className="m-card m-card--raised memory-stack"><p className="m-body memory-wrap">{p.native_id}</p><p className="m-help m-num">{p.capture_day||'Unknown local day'} · {p.media_type}{p.hidden?' · Hidden':''}</p><Toggle label={'Select '+p.native_id} checked={value.ids.includes(p.id)} onChange={()=>onChange({...value,ids:value.ids.includes(p.id)?value.ids.filter(id=>id!==p.id):[...value.ids,p.id]})}/></article>)}</div>{!photos.length&&<p>No authorized Photos match this page.</p>}<nav className="memory-actions" aria-label="Selection pages"><Button size="lg" disabled={!offset} onClick={()=>setOffset(v=>Math.max(0,v-12))}>Previous selection page</Button><Button size="lg" disabled={photos.length<=12} onClick={()=>setOffset(v=>v+12)}>Next selection page</Button></nav></>}
 {trips&&<><div className="memory-stack" role="radiogroup" aria-label="Trip snapshot selection">{trips.data.map(t=><button key={t.trip_id} type="button" className="m-btn m-btn--neutral memory-comparison" role="radio" aria-checked={value.trip?.id===t.trip_id} onClick={()=>onChange({...value,trip:{id:t.trip_id,revision:t.revision}})}>{t.title}</button>)}</div>{!trips.data.length&&<p>No authorized trips on this page.</p>}<nav className="memory-actions" aria-label="Trip selection pages"><Button size="lg" disabled={!cursor} onClick={()=>setCursor(null)}>First trip selection page</Button><Button size="lg" disabled={!trips.next_cursor} onClick={()=>setCursor(trips.next_cursor)}>Next trip selection page</Button></nav></>}
 </section>;
}
