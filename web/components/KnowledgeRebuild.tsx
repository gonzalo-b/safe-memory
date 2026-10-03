'use client';
import { useCallback,useEffect,useState } from 'react';
import { Button } from '../vendor/memory-ds/react/core';
import type { Session } from '../lib/types';
import type { KnowledgeCatalog } from '../lib/knowledge-types';
import { CoverageView,OperationStatus,useMutationKey,usePrivateRequest,type OwnerProps } from './KnowledgeShared';
import { Notice } from './Screens';
export function KnowledgeRebuild({session,onUnauthorized}:{session:Session}&OwnerProps){
  const {run,busy,error}=usePrivateRequest(onUnauthorized),keys=useMutationKey();const [catalog,setCatalog]=useState<KnowledgeCatalog|null>(null),[message,setMessage]=useState('');
  const load=useCallback(()=>{setCatalog(null);void run<KnowledgeCatalog>('/api/knowledge/catalog',{},value=>{if(typeof value.coverage?.indexed_records!=='number')throw new Error('Invalid catalog');setCatalog(value);});},[run]);
  useEffect(()=>load(),[load]);
  function rebuild(){const body={};setCatalog(null);setMessage('');void run<{generation:string}>('/api/knowledge/rebuild',{method:'POST',csrf:session.csrf_token,body:{request_key:keys.forBody(body)}},value=>{if(typeof value.generation!=='string'||!value.generation)throw new Error('Invalid rebuild receipt');keys.reset();setMessage('Photos knowledge rebuilt.');load();});}
  return <section className="m-card memory-stack" aria-label="Photos knowledge"><h2 className="m-title">Photos knowledge</h2><p className="m-body memory-copy">Rebuild the deterministic Photos index, Travel Log outcomes and inferred candidates from currently authorized imported metadata. A failed build preserves the previous generation. This does not scan your device.</p><OperationStatus busy={busy} error={error}>Checking Photos knowledge…</OperationStatus>{message&&<Notice>{message}</Notice>}{catalog&&<><CoverageView coverage={catalog.coverage}/><dl className="m-kv"><dt>Generation</dt><dd className="m-code">{catalog.generation||'Not built'}</dd><dt>Definition</dt><dd>{catalog.definition_version}</dd></dl></>}
    <div className="memory-actions"><Button variant="primary" size="lg" disabled={busy} onClick={rebuild}>Rebuild Photos knowledge</Button><Button size="lg" disabled={busy} onClick={load}>Refresh knowledge status</Button></div>
  </section>;
}
