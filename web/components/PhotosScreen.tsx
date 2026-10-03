'use client';
import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { Badge, Button, ModuleTile } from '../vendor/memory-ds/react/core';
import { ApiError, photosQuery, request } from '../lib/api';
import type { PhotoFilters, PhotoMetadata, Photos } from '../lib/types';
import type { KnowledgePage, Trip } from '../lib/knowledge-types';
import { Notice } from './Screens';
import { MediaViewer } from './MediaViewer';
import { EvidencePanel } from './KnowledgeShared';
const PAGE_SIZE = 24;
const emptyFilters: PhotoFilters = {type:'',day:'',from_day:'',to_day:'',place:'',trip_id:'',collection:''};
const collections = [['','All collections'],['personal','Personal'],['shared_library','Shared Library'],['shared_album','Shared Albums'],['unknown','Unknown collection']] as const;
const kinds = [['', 'All', 'All media types'], ['photo', 'Photos', 'Photos only'], ['video', 'Videos', 'Videos only'], ['live', 'Live', 'Live Photos only']] as const;
const labels = { photo: 'Photo record', video: 'Video record', live: 'Live Photo record' };
function RecordCard({ item, open, inspect }: { item: PhotoMetadata; open: () => void; inspect: () => void }) {
  const knownDay = item.time_basis === 'capture_offset' && !!item.capture_day;
  const collection = { personal: 'Personal', shared_library: 'Shared Library', shared_album: 'Shared Album', unknown: 'Unknown collection' }[item.collection];
  const presence = { owner: 'Owner presence reported by source', third_party: 'Third-party provenance', unknown: 'Owner presence unknown' }[item.owner_presence];
  return <article className="m-card memory-stack" aria-label={`${labels[item.media_type]} ${item.native_id}`}>
    <div className="m-card__head"><ModuleTile module="photo" /><h2 className="m-card__title">{labels[item.media_type]}</h2></div>
    <div><p className="m-meta">Capture local day</p><p className="m-title m-num">{knownDay ? item.capture_day : 'Unknown local day'}</p></div>
    <dl className="m-kv"><dt>{item.time_basis === 'instant_only' ? 'Capture instant' : 'Capture timestamp'}</dt><dd className="m-num">{item.capture_time ? <time dateTime={item.capture_time}>{item.capture_time}</time> : 'Unknown capture time'}</dd>
      <dt>Source place</dt><dd className="memory-wrap">{item.location?.place || 'Unknown'}</dd>
      <dt>Coordinates</dt><dd className="m-num">{item.location?.lat != null && item.location?.lon != null ? `${item.location.lat}, ${item.location.lon}` : 'Unavailable'}</dd>
      <dt>Explicit geography</dt><dd className="memory-wrap">{[item.geography?.city, item.geography?.country || item.geography?.country_code].filter(Boolean).join(', ') || 'Unknown'}</dd>
      <dt>Collection</dt><dd>{collection}</dd><dt>Presence</dt><dd>{presence}</dd><dt>Source record</dt><dd>{item.native_id}</dd></dl>
    <p className="m-help">Place and geography are reported by the source. Coordinates do not establish a city or owner presence.</p>
    <div className="memory-actions"><Badge>{item.media_state === 'ready' ? 'Media ready' : item.media_state === 'partial' ? 'Media partially transferred' : 'Media not transferred'}</Badge>{Boolean(item.hidden) && <Badge>Hidden</Badge>}</div>
    {item.media_state === 'not_transferred' && <p className="m-help">Metadata only. No photo, video or Live Photo component is available to open.</p>}
    <div className="memory-actions"><Button variant="tonal" size="lg" onClick={open}>Open media</Button>{item.evidence && <Button size="lg" onClick={inspect}>Inspect evidence</Button>}</div>
    {!item.evidence && <p className="m-help">Evidence awaiting Knowledge rebuild.</p>}
  </article>;
}
export function PhotosScreen({ onUnauthorized }: { onUnauthorized: (message?: string) => void }) {
  const [selected, setSelected] = useState<PhotoMetadata | null>(null);
  const [evidence, setEvidence] = useState<string | null>(null);
  const [draft, setDraft] = useState<PhotoFilters>(emptyFilters);
  const [query, setQuery] = useState({ ...emptyFilters, offset: 0, revision: 0 });
  const [tripChoices, setTripChoices] = useState<KnowledgePage<Trip> | null>(null);
  const [tripTitle, setTripTitle] = useState('');
  const [tripOpen, setTripOpen] = useState(false);
  const [tripBusy, setTripBusy] = useState(false);
  const [tripError, setTripError] = useState('');
  const tripRequest = useRef<AbortController | null>(null);
  const photoRequest = useRef<AbortController | null>(null);
  useEffect(() => () => tripRequest.current?.abort(), []);
  function clearTrips() { tripRequest.current?.abort(); setTripChoices(null); setTripTitle(''); setTripOpen(false); setTripBusy(false); setTripError(''); }
  async function loadTrips(cursor?: string | null) {
    tripRequest.current?.abort(); const controller = new AbortController(); tripRequest.current = controller;
    photoRequest.current?.abort(); setLoading(false);
    setTripOpen(true); setTripBusy(true); setTripChoices(null); setTripError(''); setTripTitle('');
    setDraft(old => ({...old,trip_id:''})); setSelected(null); setEvidence(null); setData(null); setError('');
    try {
      const value = await request<KnowledgePage<Trip>>('/api/knowledge/trips', {signal:controller.signal,query:{limit:20,...(cursor?{cursor}:{})}});
      if (controller.signal.aborted) return;
      if (!Array.isArray(value.data) || value.data.some(trip => !/^[a-f0-9]{32}$/.test(trip.trip_id) || typeof trip.title !== 'string') || (value.next_cursor !== null && typeof value.next_cursor !== 'string')) throw new ApiError(502,'invalid_response','The server response could not be read. Try again.');
      setTripChoices(value);
    } catch(value) {
      if (controller.signal.aborted) return;
      if (value instanceof ApiError && value.status === 401) onUnauthorized('Your session has ended. Sign in again to continue.');
      else setTripError(value instanceof ApiError ? value.message : 'Could not load trip choices. Try again.');
    } finally { if (!controller.signal.aborted) setTripBusy(false); }
  }
  const [data, setData] = useState<PhotoMetadata[] | null>(null);
  const [coverage,setCoverage]=useState('restricted_or_unknown');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const results = useRef<HTMLDivElement>(null);
  const evidenceFailed = useCallback(() => {
    setEvidence(null); setSelected(null); setData(null);
    setError('Evidence could not be verified. Refresh metadata to check current access.');
  }, []);
  useEffect(() => {
    const controller = new AbortController(); photoRequest.current=controller; setLoading(true); setData(null); setError('');
    void request<Photos>('/api/photos', { signal: controller.signal, query: photosQuery(query, query.offset) }).then(value => {
      if (!controller.signal.aborted) {
        if (!Array.isArray(value.assets)) throw new ApiError(502, 'invalid_response', 'The server response could not be read. Try again.');
        setData(value.assets);setCoverage(value.coverage?.mode || 'restricted_or_unknown');
      }
    }).catch(value => {
      if (controller.signal.aborted) return;
      if (value instanceof ApiError && value.status === 401) onUnauthorized('Your session has ended. Sign in again to continue.');
      else { clearTrips(); setDraft(old => ({...old,trip_id:''})); setError(value instanceof ApiError ? value.message : 'This request did not finish. Try again.'); }
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [query, onUnauthorized]);
  function update(next: typeof query) { setEvidence(null); setSelected(null); setData(null); setError(''); setLoading(true); setQuery(next); }
  function apply(event: FormEvent) {
    event.preventDefault();
    try { photosQuery(draft,0); } catch(value) { setSelected(null); setEvidence(null); setData(null); setError(value instanceof Error ? value.message : 'Check the filters.'); return; }
    tripRequest.current?.abort(); setTripChoices(null); setTripOpen(false); setTripBusy(false); setTripError('');
    update({...draft,offset:0,revision:query.revision+1});
  }
  function page(offset: number) { update({ ...query, offset }); results.current?.focus(); results.current?.scrollIntoView({ block: 'start' }); }
  const visible = data?.slice(0, PAGE_SIZE);
  return <>
    {selected && <MediaViewer item={selected} onClose={() => setSelected(null)} onUnauthorized={onUnauthorized} />}
    {evidence && <EvidencePanel id={evidence} onClose={() => setEvidence(null)} onUnauthorized={onUnauthorized} onFailure={evidenceFailed} />}
    <section className="m-card memory-stack"><div><h2 className="m-title">{coverage==='selected_samples'?'Selected samples only':'Authorized Photos metadata'}</h2><p className="m-body memory-copy memory-spaced">{coverage==='selected_samples'?'These metadata records come from selected, authorized samples. They do not establish coverage of your whole Photos library.':'Only currently authorized metadata is shown. Sources reports each scan’s scope and progress; this page does not imply whole-library or media completion.'}</p></div>
      <form className="memory-stack" onSubmit={apply} aria-label="Filter metadata">
        <div className="m-field"><span className="m-label">Media type</span><div className="m-seg memory-type-filter" role="group" aria-label="Media type">{kinds.map(([value, label, accessible]) => <button type="button" className="m-seg__item" key={value} aria-label={accessible} aria-pressed={draft.type === value} onClick={() => setDraft(old=>({...old,type:value}))}>{label}</button>)}</div></div>
        <label className="m-field"><span className="m-label">Capture local day</span><input className="m-input m-input--touch memory-day" aria-label="Capture local day" type="date" min="0001-01-01" max="9999-12-31" value={draft.day} onChange={event => setDraft(old=>({...old,day:event.target.value,from_day:'',to_day:''}))} /><span className="m-help">Only a known capture-local day matches this filter. An instant alone does not establish the local day.</span></label>
        <div className="memory-grid">
          <label className="m-field"><span className="m-label">Capture from day</span><input className="m-input m-input--touch memory-day" aria-label="Capture from day" type="date" min="0001-01-01" max="9999-12-31" value={draft.from_day} onChange={event=>setDraft(old=>({...old,from_day:event.target.value,day:''}))}/></label>
          <label className="m-field"><span className="m-label">Capture through day</span><input className="m-input m-input--touch memory-day" aria-label="Capture through day" type="date" min="0001-01-01" max="9999-12-31" value={draft.to_day} onChange={event=>setDraft(old=>({...old,to_day:event.target.value,day:''}))}/></label>
        </div>
        <p className="m-help">Period endpoints are inclusive, using known capture-local days. Choosing a period clears the single day, and choosing a single day clears the period.</p>
        <label className="m-field"><span className="m-label">Source place filter</span><input className="m-input m-input--touch" aria-label="Source place filter" type="text" value={draft.place} onChange={event=>setDraft(old=>({...old,place:event.target.value}))}/><span className="m-help">Matches only explicit source place, country or city text. Unknown places are not inferred from coordinates.</span></label>
        <div className="m-field"><span className="m-label">Collection</span><div className="memory-actions" role="group" aria-label="Collection filter">{collections.map(([value,label])=><Button key={value} size="lg" variant={draft.collection===value?'tonal':'neutral'} aria-label={'Filter '+label} aria-pressed={draft.collection===value} onClick={()=>setDraft(old=>({...old,collection:value}))}>{label}</Button>)}</div><span className="m-help">A filter only narrows current access. Shared categories still require their separate Source consent.</span></div>
        <div className="memory-stack"><p className="m-label">Trip filter</p>{tripTitle?<p className="m-body memory-wrap">{tripTitle}</p>:<p className="m-help">No trip selected.</p>}<div className="memory-actions"><Button size="lg" aria-expanded={tripOpen} aria-controls="photo-trip-choices" onClick={()=>void loadTrips()}>Choose trip filter</Button>{draft.trip_id&&<Button size="lg" variant="ghost" onClick={()=>{clearTrips();setDraft(old=>({...old,trip_id:''}));}}>Clear trip filter</Button>}</div>
          {tripOpen&&<div id="photo-trip-choices" className="memory-stack" aria-label="Current trip choices" aria-busy={tripBusy}>
            {tripBusy?<p role="status" className="m-help">Loading current trips…</p>:tripError?<Notice error>{tripError}</Notice>:tripChoices?.data.length?tripChoices.data.map(trip=><Button className="memory-comparison memory-wrap" key={trip.trip_id} size="lg" aria-label={'Filter trip '+trip.title} onClick={()=>{setDraft(old=>({...old,trip_id:trip.trip_id}));setTripTitle(trip.title);setTripChoices(null);setTripOpen(false);}}>{trip.title}</Button>):<p className="m-help">No currently authorized trips on this page.</p>}
            <div className="memory-actions"><Button size="lg" disabled={tripBusy} onClick={()=>void loadTrips()}>Refresh trip choices</Button>{tripChoices?.next_cursor&&<Button size="lg" onClick={()=>void loadTrips(tripChoices.next_cursor)}>Next trip choices</Button>}<Button size="lg" variant="ghost" onClick={()=>{clearTrips();}}>Close trip choices</Button></div>
          </div>}
        </div>
        <div className="memory-actions"><Button type="submit" variant="primary" size="lg">Apply filters</Button><Button variant="ghost" size="lg" onClick={() => { clearTrips(); setDraft(emptyFilters); update({ ...emptyFilters, offset: 0, revision: query.revision + 1 }); }}>Clear filters</Button><Button icon="refresh" size="lg" disabled={loading} onClick={() => update({ ...query, revision: query.revision + 1 })}>Refresh metadata</Button></div>
      </form>
    </section>
    <div ref={results} tabIndex={-1} className="memory-stack memory-results" aria-label="Metadata results" aria-busy={loading}>
      {loading ? <p className="m-body" role="status">Loading metadata…</p> : error ? <Notice error>{error}</Notice> : visible?.length ? <>
        <p className="m-help m-num" role="status">Showing records {query.offset + 1}–{query.offset + visible.length} from the current authorized result.</p>
        <div className="memory-grid">{visible.map(item => <RecordCard key={item.id} item={item} open={() => { setEvidence(null); setSelected(item); }} inspect={() => { setSelected(null); setEvidence(item.id); }} />)}</div>
      </> : data===null ? <p className="m-help">Apply filters to load current photos.</p> : <section className="m-card"><div className="m-empty"><ModuleTile module="photo" /><h2 className="m-empty__title">No matching metadata</h2><p className="m-empty__desc">No authorized records match this page and its applied filters. This does not mean your Photos library is empty.</p></div></section>}
      {!loading && !error && data && <nav className="memory-actions" aria-label="Metadata pages"><Button size="lg" disabled={query.offset === 0} onClick={() => page(Math.max(0, query.offset - PAGE_SIZE))}>Previous page</Button><Button size="lg" disabled={data.length <= PAGE_SIZE} onClick={() => page(query.offset + PAGE_SIZE)}>Next page</Button></nav>}
    </div>
  </>;
}
