'use client';
import {useState,type FormEvent} from 'react';
import {Button} from '../vendor/memory-ds/react/core';
import type {Gallery} from '../lib/artifact-types';
import {Field} from './KnowledgeShared';
import {ArtifactSelection,type Selection} from './ArtifactSelection';
import {Notice} from './Screens';
export function ArtifactComposer({mode,gallery,onSave,onCancel,onFailure}:{mode:'create'|'edit'|'recompose';gallery:Gallery|null;onSave:(path:string,body:Record<string,unknown>)=>void;onCancel:()=>void;onFailure:(e:unknown)=>void}){
 const [title,setTitle]=useState(gallery?.title||''),[layout,setLayout]=useState<'grid'|'story'>(gallery?.layout||'grid');
 const [selection,setSelection]=useState<Selection>({mode:mode==='recompose'?'retained':'photos',ids:mode==='edit'?gallery!.members.map(m=>m.asset_id):[],trip:null});
 const [cover,setCover]=useState<string|null>(gallery?.cover_asset_id||null),[error,setError]=useState('');
 function update(value:Selection){setSelection(value);if(!value.ids.includes(cover||''))setCover(value.ids[0]||null);}
 function move(i:number,direction:number){const ids=[...selection.ids];[ids[i],ids[i+direction]]=[ids[i+direction],ids[i]];setSelection({...selection,ids});}
 function submit(e:FormEvent){e.preventDefault();setError('');if(selection.ids.length>200){setError('Choose at most200 members.');return;}if(selection.mode==='trip'&&!selection.trip){setError('Choose a current trip snapshot.');return;}
 if(mode==='edit'){const before=gallery!.members.map(m=>m.asset_id);onSave('/api/artifacts/'+gallery!.id+'/edit',{expected_revision:gallery!.revision,patch:{title,layout,cover_asset_id:cover,add_ids:selection.ids.filter(id=>!before.includes(id)),remove_ids:before.filter(id=>!selection.ids.includes(id)),order:selection.ids}});return;}
 const pick=selection.mode==='trip'?{trip_id:selection.trip!.id,expected_trip_revision:selection.trip!.revision}:selection.mode==='photos'?{asset_ids:selection.ids}:{};
 onSave(mode==='create'?'/api/artifacts':'/api/artifacts/'+gallery!.id+'/recompose',mode==='create'?{title,layout,...pick}:{expected_revision:gallery!.revision,...pick});}
 return <form className="m-card memory-stack" aria-label="Gallery composer" onSubmit={submit}><h2 className="m-title">{mode==='create'?'New private gallery':mode==='edit'?'Edit private gallery':'Recompose private gallery'}</h2>
 {mode!=='recompose'&&<><Field label="Gallery title" value={title} onChange={setTitle} required/><div className="memory-actions" role="group" aria-label="Gallery layout">{(['grid','story'] as const).map(v=><Button key={v} size="lg" aria-label={v==='grid'?'Grid layout':'Story layout'} aria-pressed={layout===v} onClick={()=>setLayout(v)}>{v==='grid'?'Grid':'Story'}</Button>)}</div></>}
 {mode==='recompose'&&<Notice>Recompose retains existing members, order and exclusions. It does not re-add removed assets. Use Edit gallery to explicitly include an excluded asset again.</Notice>}
 {mode==='edit'&&<><h3 className="m-title">Member order and cover</h3>{selection.ids.map((id,i)=><article key={id} className="m-card m-card--raised memory-stack"><p className="m-code memory-wrap">Member {i+1}: {id}{cover===id?' · Cover':''}</p><div className="memory-actions"><Button size="lg" aria-label={`Move member ${i+1} up`} disabled={!i} onClick={()=>move(i,-1)}>Move up</Button><Button size="lg" aria-label={`Move member ${i+1} down`} disabled={i===selection.ids.length-1} onClick={()=>move(i,1)}>Move down</Button><Button size="lg" aria-label={`Use member ${i+1} as cover`} onClick={()=>setCover(id)}>Use as cover</Button><Button size="lg" aria-label={`Remove member ${i+1}`} onClick={()=>update({...selection,ids:selection.ids.filter(v=>v!==id)})}>Remove</Button></div></article>)}</>}
 {mode==='edit'?<ArtifactSelection value={selection} onChange={update} onFailure={onFailure} photosOnly/>:<ArtifactSelection value={selection} onChange={update} onFailure={onFailure} retained={mode==='recompose'}/>}
 {error&&<Notice error>{error}</Notice>}<div className="memory-actions"><Button type="submit" size="lg" variant="primary">{mode==='create'?'Save gallery':mode==='edit'?'Save changes':'Run recompose'}</Button><Button size="lg" onClick={onCancel}>Cancel composition</Button></div>
 </form>;
}
