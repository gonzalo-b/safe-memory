import Link from 'next/link';
import { Badge, ModuleTile } from '../vendor/memory-ds/react/core';
import type { Debug, Overview, SafeEvent, Session, Sources } from '../lib/types';
export function Notice({ children, error = false }: { children: React.ReactNode; error?: boolean }) {
  return <div className={`m-banner ${error ? 'm-banner--bad' : 'm-banner--neutral'}`} role={error ? 'alert' : 'status'}>{children}</div>;
}
export function Unavailable({ subject }: { subject: string }) {
  return <section className="m-card"><div className="m-empty"><ModuleTile icon="clock" />
    <h2 className="m-empty__title">Not implemented in this build</h2>
    <p className="m-empty__desc">{subject} will be available when its feature is ready. Your sources remain unchanged.</p>
  </div></section>;
}
function When({ value }: { value: string | number | null | undefined }) {
  if (value == null) return <>No successful update yet</>;
  const parsed = new Date(typeof value === 'number' ? value * 1000 : value);
  return <time dateTime={Number.isNaN(parsed.getTime()) ? undefined : parsed.toISOString()}>{Number.isNaN(parsed.getTime()) ? 'Time unavailable' : parsed.toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}</time>;
}
export function OverviewScreen({ data }: { data: Overview }) {
  return <>
    <div className="m-statgrid memory-statgrid">{[
      ['Records', data.counts.assets, 'Indexed assets'], ['Media ready', data.counts.media_ready, 'Optimized copies'],
      ['Trips', data.counts.trips, 'Saved trips'], ['Artifacts', data.counts.artifacts, 'Private saved results'],
    ].map(([label, value, help]) => <div className="m-card m-stat" key={label}>
      <span className="m-stat__label">{label}</span><div className="m-stat__row"><span className="m-stat__value m-num">{Number(value).toLocaleString('en-GB')}</span></div><span className="m-help">{help}</span>
    </div>)}</div>
    <div className="memory-grid">
      <section className="m-card"><div className="m-card__head"><ModuleTile module="photo" /><h2 className="m-card__title">Photos Vault</h2><Badge>{data.vault ? 'Created' : 'Not connected'}</Badge></div>
        <p className="m-body memory-copy">{data.vault ? 'Your connected sources contribute to one private Photos Vault.' : 'Your Photos Vault is created automatically when the first source connects.'}</p>
        <dl className="m-kv memory-spaced"><dt>Index</dt><dd>{data.coverage.index_state}</dd><dt>Media</dt><dd>{data.coverage.media_state}</dd><dt>Last success</dt><dd><When value={data.coverage.last_success} /></dd></dl>
        <Link prefetch={false} className="m-btn m-btn--tonal memory-spaced" href="/sources">View sources</Link>
      </section>
      <section className="m-card"><div className="m-card__head"><ModuleTile icon="shield-check" /><h2 className="m-card__title">Read-only sources</h2></div>
        <p className="m-body memory-copy">Memory reads your sources. It never writes to them.</p>
        <p className="m-help memory-spaced">Photos connection and import are not implemented in this build. These counts describe the current authorized runtime.</p>
      </section>
    </div>
  </>;
}
export function SourcesScreen({ data }: { data: Sources }) {
  return <>
    {data.sources.length ? <div className="memory-stack">{data.sources.map(source => <section className="m-card" key={source.id}>
      <div className="m-card__head"><ModuleTile module="photo" /><h2 className="m-card__title">{source.name}</h2><Badge>{source.status}</Badge></div>
      <dl className="m-kv"><dt>Permission</dt><dd>{source.permission}</dd><dt>Indexed</dt><dd className="m-num">{source.index_count}</dd><dt>Media ready</dt><dd className="m-num">{source.media_ready_count}</dd><dt>Last success</dt><dd><When value={source.last_success} /></dd></dl>
    </section>)}</div> : <section className="m-card"><div className="m-empty"><ModuleTile icon="plug" /><h2 className="m-empty__title">No sources connected</h2><p className="m-empty__desc">Apple Photos will be the first source for your Photos Vault. No library has been imported.</p></div></section>}
    <Unavailable subject="iPhone connection and progressive Photos import" />
  </>;
}
export function EventList({ items, empty }: { items: SafeEvent[]; empty: string }) {
  if (!items.length) return <p className="m-body memory-copy">{empty}</p>;
  return <ul className="memory-events">{items.map((item, index) => <li key={item.id || index} className="m-listrow">
    <div className="m-grow"><div className="m-listrow__title">{item.action || 'Operation'}</div><div className="m-listrow__sub"><When value={item.created_at} /></div><div className="m-help memory-event-id">{item.id}</div>{typeof item.count === 'number' && <div className="m-help m-num">{item.count} records</div>}{item.completed_at != null && <div className="m-help">Completed <When value={item.completed_at} /></div>}</div><Badge>{item.outcome || item.status || 'Recorded'}</Badge>
  </li>)}</ul>;
}
export function DebugScreen({ data, auditOnly = false }: { data: Debug; auditOnly?: boolean }) {
  if (auditOnly) return <section className="m-card"><EventList items={data.audit} empty="No access events are available in this response." /></section>;
  return <>
    <div className="memory-grid">
      <section className="m-card"><h2 className="m-title">System health</h2><dl className="m-kv memory-spaced"><dt>Storage</dt><dd>{data.health.storage}</dd><dt>Audit</dt><dd>{data.health.audit}</dd><dt>Version</dt><dd>{data.version}</dd><dt>Environment</dt><dd>{data.environment}</dd></dl></section>
      <section className="m-card"><h2 className="m-title">Operations</h2><div className="memory-spaced"><EventList items={data.operations} empty="No operations have been recorded." /></div></section>
    </div>
    <section className="m-card"><h2 className="m-title">Access events</h2><div className="memory-spaced"><EventList items={data.audit} empty="No access events are available in this response." /></div></section>
    <Unavailable subject="Record, Block, media and Artifact inspectors, import retry and selected rebuild controls" />
  </>;
}
export function SettingsScreen({ session }: { session: Session }) {
  return <div className="memory-grid"><section className="m-card"><h2 className="m-title">Your account</h2><p className="m-body memory-spaced">{session.owner.display_name}</p><p className="m-help memory-spaced">Your session protects this private Memory. Sign out from the account control when you finish.</p></section>
    <section className="m-card"><h2 className="m-title">Appearance</h2><p className="m-body memory-spaced">Use System, Light or Dark in the theme control above. Appearance is the only preference stored in this browser.</p></section>
    <section className="m-card"><h2 className="m-title">Data boundaries</h2><p className="m-body memory-spaced">Imported records and saved results belong to their owner. Source consent and access permissions remain separate.</p></section></div>;
}
