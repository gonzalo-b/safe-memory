'use client';
import { useCallback,useEffect,useRef,useState,type FormEvent } from 'react';
import Link from 'next/link';
import { Badge,Button,ModuleTile } from '../vendor/memory-ds/react/core';
import type { Session } from '../lib/types';
import type { KnowledgeAnswer,KnowledgeCatalog,KnowledgeFact } from '../lib/knowledge-types';
import { CoverageView,DateField,EvidencePanel,FactCard,Field,OperationStatus,Pages,usePrivateRequest,type OwnerProps } from './KnowledgeShared';
import { Notice } from './Screens';
const capabilities=[['travel.where_on_date','Where on a date'],['travel.where_in_range','Where in a range'],['travel.where_in_year','Where in a year'],['travel.countries_visited','Countries'],['travel.cities_visited','Cities'],['photos.statistics','Photo statistics'],['photos.on_this_day','On this day'],['travel.occasion_history','Occasion history'],['photos.records','Indexed evidence']] as const;
export function BlocksScreen({session,onUnauthorized}:{session:Session}&OwnerProps){
  const catalogRequest=usePrivateRequest(onUnauthorized),answerRequest=usePrivateRequest(onUnauthorized);
  const [catalog,setCatalog]=useState<KnowledgeCatalog|null>(null),[answer,setAnswer]=useState<KnowledgeAnswer|null>(null),[evidence,setEvidence]=useState<string|null>(null);
  const [cap,setCap]=useState<string>('travel.where_on_date'),[day,setDay]=useState(''),[start,setStart]=useState(''),[end,setEnd]=useState(''),[year,setYear]=useState(''),[monthDay,setMonthDay]=useState(''),[asOf,setAsOf]=useState(''),[count,setCount]=useState('3');
  const [cursor,setCursor]=useState<string|null>(null);const applied=useRef<{capability:string;params:Record<string,unknown>}|null>(null),resultHeading=useRef<HTMLHeadingElement>(null);
  const clearEvidenceParent=useCallback(()=>{setAnswer(null);setCatalog(null);},[]);
  const loadCatalog=catalogRequest.run;
  useEffect(()=>{setCatalog(null);void loadCatalog<KnowledgeCatalog>('/api/knowledge/catalog',{},value=>{if(!Array.isArray(value.capabilities)||typeof value.coverage?.indexed_records!=='number')throw new Error('Invalid catalog');setCatalog(value);});},[loadCatalog]);
  function changeCap(value:string){answerRequest.clear();setAnswer(null);setEvidence(null);setCursor(null);setCap(value);applied.current=null;}
  function execute(nextCursor:string|null=null,fresh=false){
    let query=applied.current;
    if(fresh||!query){
      let params:Record<string,unknown>={};
      if(cap==='travel.where_on_date')params={date:day};
      else if(cap==='travel.where_in_year')params={year:Number(year)};
      else if(cap==='photos.on_this_day')params={month_day:monthDay};
      else if(cap==='travel.occasion_history')params={month_day:monthDay||null,count:Number(count),as_of:asOf,leap_day_policy:'leap_years_only'};
      else params={...(start?{start}:{}),...(end?{end}:{})};
      query={capability:cap,params};applied.current=query;
    }
    setAnswer(null);setEvidence(null);setCursor(nextCursor);
    void answerRequest.run<KnowledgeAnswer>('/api/knowledge/answer',{method:'POST',csrf:session.csrf_token,body:{...query,limit:20,...(nextCursor?{cursor:nextCursor}:{})}},value=>{
      if(!value||typeof value.status!=='string'||typeof value.coverage?.indexed_records!=='number'||(!Array.isArray(value.data)&&(typeof value.data!=='object'||value.data===null)))throw new Error('Invalid answer');setAnswer(value);resultHeading.current?.focus();
    });
  }
  function submit(event:FormEvent){event.preventDefault();execute(null,true);}
  const period=!['travel.where_on_date','travel.where_in_year','photos.on_this_day','travel.occasion_history'].includes(cap);
  const rows=answer&&Array.isArray(answer.data)?answer.data:[];
  return <>
    <section className="m-card memory-stack"><div className="m-card__head"><ModuleTile module="photo"/><h2 className="m-card__title">Photos knowledge</h2><Badge>Deterministic</Badge></div>
      <p className="m-body memory-copy">Travel Log and photo statistics use currently authorized indexed evidence. Unknown dates and gaps remain unknown.</p>
      <OperationStatus busy={catalogRequest.busy} error={catalogRequest.error}>Loading knowledge availability…</OperationStatus>
      {catalog&&<><CoverageView coverage={catalog.coverage}/><p className="m-help">{catalog.people==='unavailable'?'People is unavailable in current source metadata.':'Source-provided People metadata is available on permitted evidence.'}</p><p className="m-help">Definition {catalog.definition_version}</p></>}
      <Link className="m-btn m-btn--neutral m-btn--lg" href="/debug" prefetch={false}>Open rebuild controls</Link>
    </section>
    <section className="m-card memory-stack"><h2 className="m-title">Capabilities</h2>
      <div className="memory-capabilities" role="group" aria-label="Capability">{capabilities.map(([id,label])=><button type="button" className="m-chip" key={id} aria-pressed={cap===id} onClick={()=>changeCap(id)}>{label}</button>)}</div>
      <form className="memory-stack memory-knowledge-form" aria-label="Knowledge query" onSubmit={submit}>
        {cap==='travel.where_on_date'&&<DateField label="Local date" value={day} onChange={setDay} required/>}
        {cap==='travel.where_in_year'&&<Field label="Year" type="number" value={year} onChange={setYear} min="1" max="9999" step="1" required/>}
        {period&&<div className="memory-grid"><DateField label="Period start" value={start} onChange={setStart} required={cap==='travel.where_in_range'}/><DateField label="Period end" value={end} onChange={setEnd} required={cap==='travel.where_in_range'} help="Exclusive: observations on this date are outside the range."/></div>}
        {(cap==='photos.on_this_day'||cap==='travel.occasion_history')&&<Field label="Month and day" value={monthDay} onChange={setMonthDay} required={cap==='photos.on_this_day'} help="MM-DD. February 29 matches leap years exactly."/>}
        {cap==='travel.occasion_history'&&<><Field label="Occurrences" type="number" min="1" max="100" step="1" value={count} onChange={setCount} required/><DateField label="As of local date" value={asOf} onChange={setAsOf} required/><p className="m-help">N means calendar occurrences, including years with no evidence. The date is your explicit reference, not a guessed birthday or system date.</p></>}
        <div><Button type="submit" variant="primary" size="lg" disabled={answerRequest.busy}>Run query</Button></div>
      </form>
    </section>
    <section className="memory-stack memory-results" aria-label="Knowledge results" aria-busy={answerRequest.busy}>
      <h2 className="m-title" tabIndex={-1} ref={resultHeading}>Query results</h2><OperationStatus busy={answerRequest.busy} error={answerRequest.error}>Running query…</OperationStatus>
      {answer&&<><div className="m-card memory-stack"><Badge>{answer.status==='no_evidence'?'No evidence':answer.status==='partial'?'Partial evidence':answer.status==='needs_input'?'Needs input':'Current result'}</Badge><CoverageView coverage={answer.coverage}/>
        <p className="m-help">{answer.freshness.stale?'Some current evidence awaits a rebuild.':'The indexed revision is current for these authorized records.'} Source checking remains {answer.freshness.source_check}.</p><p className="m-help">Counting: {answer.counting_rule.replaceAll('_',' ')}.</p>
        {answer.status==='no_evidence'&&<><p className="m-body">No admissible evidence for this query.</p><p className="m-help">A zero here does not mean your whole library has no records.</p></>}
        {answer.status==='needs_input'&&<Notice>Choose a month and day to answer this occasion.</Notice>}
        {!Array.isArray(answer.data)&&<dl className="m-kv m-num">{Object.entries(answer.data).map(([key,value])=><div className="memory-kv-row" key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{String(value)}</dd></div>)}</dl>}
      </div>
      {rows.map((row,index)=>{
        if('capture_day'in row)return <FactCard key={index} fact={row as unknown as KnowledgeFact} inspect={setEvidence}/>;
        if('observation_count'in row)return <article className="m-card memory-stack" key={index}><h3 className="m-title m-num">{String(row.date)}</h3><Badge>{row.status==='unknown'?'Unknown occurrence':'Observed occurrence'}</Badge><p className="m-body m-num">{String(row.observation_count)} observations</p>{(row.observations as KnowledgeFact[]||[]).map((fact,index)=><FactCard key={index} fact={fact} inspect={setEvidence}/>)}{Boolean(row.has_more)&&<p className="m-help">More evidence exists for this date. Query that local date to page through it.</p>}</article>;
        const evidenceQuery=row.evidence_query as {capability:string;params:Record<string,unknown>}|undefined;
        return <article className="m-card memory-stack" key={index}><h3 className="m-title">{String(row.label||row.country_code||row.city_id||'Explicit geography')}</h3><p className="m-body m-num">{String(row.records)} observations · {String(row.observed_days)} observed local days</p><p className="m-help">Explicit source geography is not proof that you visited.</p>{evidenceQuery&&<div><Button size="lg" onClick={()=>{applied.current=evidenceQuery;execute();}}>Show supporting evidence</Button></div>}</article>;
      })}
      <Pages label="result" next={answer.next_cursor} onNext={()=>execute(answer.next_cursor)} onFirst={()=>execute()} busy={answerRequest.busy} first={cursor===null}/></>}
    </section>
    {evidence&&<EvidencePanel id={evidence} onClose={()=>setEvidence(null)} onUnauthorized={onUnauthorized} onFailure={clearEvidenceParent}/>}
  </>;
}
