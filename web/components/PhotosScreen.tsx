'use client';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Badge, Button, ModuleTile } from '../vendor/memory-ds/react/core';
import { ApiError, request } from '../lib/api';
import type { PhotoMetadata, Photos } from '../lib/types';
import { Notice } from './Screens';
import { MediaViewer } from './MediaViewer';
const PAGE_SIZE = 24;
const kinds = [['', 'All', 'All media types'], ['photo', 'Photos', 'Photos only'], ['video', 'Videos', 'Videos only'], ['live', 'Live', 'Live Photos only']] as const;
const labels = { photo: 'Photo record', video: 'Video record', live: 'Live Photo record' };
function RecordCard({ item, open }: { item: PhotoMetadata; open: () => void }) {
  const knownDay = item.time_basis === 'capture_offset' && !!item.capture_day;
  const collection = { personal: 'Personal', shared_library: 'Shared Library', shared_album: 'Shared Album', unknown: 'Unknown collection' }[item.collection];
  const presence = { owner: 'Owner presence reported by source', third_party: 'Third-party provenance', unknown: 'Owner presence unknown' }[item.owner_presence];
  return <article className="m-card memory-stack" aria-label={`${labels[item.media_type]} ${item.native_id}`}>
    <div className="m-card__head"><ModuleTile module="photo" /><h2 className="m-card__title">{labels[item.media_type]}</h2></div>
    <div><p className="m-meta">Capture local day</p><p className="m-title m-num">{knownDay ? item.capture_day : 'Unknown local day'}</p></div>
    <dl className="m-kv"><dt>{item.time_basis === 'instant_only' ? 'Capture instant' : 'Capture timestamp'}</dt><dd className="m-num">{item.capture_time ? <time dateTime={item.capture_time}>{item.capture_time}</time> : 'Unknown capture time'}</dd>
      <dt>Collection</dt><dd>{collection}</dd><dt>Presence</dt><dd>{presence}</dd><dt>Source record</dt><dd>{item.native_id}</dd></dl>
    <div className="memory-actions"><Badge>{item.media_state === 'ready' ? 'Media ready' : item.media_state === 'partial' ? 'Media partially transferred' : 'Media not transferred'}</Badge>{Boolean(item.hidden) && <Badge>Hidden</Badge>}</div>
    {item.media_state === 'not_transferred' && <p className="m-help">Metadata only. No photo, video or Live Photo component is available to open.</p>}
    <div><Button variant="tonal" size="lg" onClick={open}>Open media</Button></div>
  </article>;
}
export function PhotosScreen({ onUnauthorized }: { onUnauthorized: (message?: string) => void }) {
  const [selected, setSelected] = useState<PhotoMetadata | null>(null);
  const [draftType, setDraftType] = useState('');
  const [draftDay, setDraftDay] = useState('');
  const [query, setQuery] = useState({ type: '', day: '', offset: 0, revision: 0 });
  const [data, setData] = useState<PhotoMetadata[] | null>(null);
  const [coverage,setCoverage]=useState('restricted_or_unknown');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const results = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setData(null); setError('');
    void request<Photos>('/api/photos', { signal: controller.signal, query: { limit: PAGE_SIZE + 1, offset: query.offset,
      ...(query.type ? { media_type: query.type } : {}), ...(query.day ? { day: query.day } : {}) } }).then(value => {
      if (!controller.signal.aborted) {
        if (!Array.isArray(value.assets)) throw new ApiError(502, 'invalid_response', 'The server response could not be read. Try again.');
        setData(value.assets);setCoverage(value.coverage?.mode || 'restricted_or_unknown');
      }
    }).catch(value => {
      if (controller.signal.aborted) return;
      if (value instanceof ApiError && value.status === 401) onUnauthorized('Your session has ended. Sign in again to continue.');
      else setError(value instanceof ApiError ? value.message : 'This request did not finish. Try again.');
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [query, onUnauthorized]);
  function update(next: typeof query) { setSelected(null); setData(null); setError(''); setLoading(true); setQuery(next); }
  function apply(event: FormEvent) { event.preventDefault(); update({ type: draftType, day: draftDay, offset: 0, revision: query.revision + 1 }); }
  function page(offset: number) { update({ ...query, offset }); results.current?.focus(); results.current?.scrollIntoView({ block: 'start' }); }
  const visible = data?.slice(0, PAGE_SIZE);
  return <>
    {selected && <MediaViewer item={selected} onClose={() => setSelected(null)} onUnauthorized={onUnauthorized} />}
    <section className="m-card memory-stack"><div><h2 className="m-title">{coverage==='selected_samples'?'Selected samples only':'Authorized Photos metadata'}</h2><p className="m-body memory-copy memory-spaced">{coverage==='selected_samples'?'These metadata records come from selected, authorized samples. They do not establish coverage of your whole Photos library.':'Only currently authorized metadata is shown. Sources reports each scan’s scope and progress; this page does not imply whole-library or media completion.'}</p></div>
      <form className="memory-stack" onSubmit={apply} aria-label="Filter metadata">
        <div className="m-field"><span className="m-label">Media type</span><div className="m-seg memory-type-filter" role="group" aria-label="Media type">{kinds.map(([value, label, accessible]) => <button type="button" className="m-seg__item" key={value} aria-label={accessible} aria-pressed={draftType === value} onClick={() => setDraftType(value)}>{label}</button>)}</div></div>
        <label className="m-field"><span className="m-label">Capture local day</span><input className="m-input m-input--touch memory-day" aria-label="Capture local day" type="date" min="0001-01-01" max="9999-12-31" value={draftDay} onChange={event => setDraftDay(event.target.value)} /><span className="m-help">Only a known capture-local day matches this filter. An instant alone does not establish the local day.</span></label>
        <div className="memory-actions"><Button type="submit" variant="primary" size="lg">Apply filters</Button><Button variant="ghost" size="lg" onClick={() => { setDraftType(''); setDraftDay(''); update({ type: '', day: '', offset: 0, revision: query.revision + 1 }); }}>Clear filters</Button><Button icon="refresh" size="lg" disabled={loading} onClick={() => update({ ...query, revision: query.revision + 1 })}>Refresh metadata</Button></div>
      </form>
    </section>
    <div ref={results} tabIndex={-1} className="memory-stack memory-results" aria-label="Metadata results" aria-busy={loading}>
      {loading ? <p className="m-body" role="status">Loading metadata…</p> : error ? <Notice error>{error}</Notice> : visible?.length ? <>
        <p className="m-help m-num" role="status">Showing records {query.offset + 1}–{query.offset + visible.length} from the current authorized result.</p>
        <div className="memory-grid">{visible.map(item => <RecordCard key={item.id} item={item} open={() => setSelected(item)} />)}</div>
      </> : <section className="m-card"><div className="m-empty"><ModuleTile module="photo" /><h2 className="m-empty__title">No matching metadata</h2><p className="m-empty__desc">No authorized records match this page and its applied filters. This does not mean your Photos library is empty.</p></div></section>}
      {!loading && !error && data && <nav className="memory-actions" aria-label="Metadata pages"><Button size="lg" disabled={query.offset === 0} onClick={() => page(Math.max(0, query.offset - PAGE_SIZE))}>Previous page</Button><Button size="lg" disabled={data.length <= PAGE_SIZE} onClick={() => page(query.offset + PAGE_SIZE)}>Next page</Button></nav>}
    </div>
  </>;
}
