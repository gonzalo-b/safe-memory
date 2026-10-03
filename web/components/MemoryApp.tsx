'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Badge, Button, ModuleTile } from '../vendor/memory-ds/react/core';
import { Icon } from '../vendor/memory-ds/react/Icon';
import type { IconName } from '../vendor/memory-ds/icon-names';
import { ApiError, request } from '../lib/api';
import type { Debug, Overview, Session, Sources } from '../lib/types';
import { DebugScreen, Notice, OverviewScreen, SettingsScreen, Unavailable } from './Screens';
import { PhotosScreen } from './PhotosScreen';
import { SourcesScreen } from './SourcesScreen';
import { ThemePicker } from './ThemePicker';
import { BlocksScreen } from './BlocksScreen';
import { TripsScreen } from './TripsScreen';
const routes: Record<string, { title: string; icon: IconName; description: string }> = {
  overview: { title: 'Overview', icon: 'home', description: 'Your private Photos memory, with a clear view of what is ready.' },
  sources: { title: 'Sources', icon: 'plug', description: 'The services that contribute to your memory.' },
  photos: { title: 'Memory', icon: 'grid', description: 'Photos, videos and the evidence behind your memories.' },
  blocks: { title: 'Blocks', icon: 'block', description: 'Knowledge built from your authorized evidence.' },
  trips: { title: 'Trips', icon: 'map-pin', description: 'Observed places and trips you can recognize.' },
  artifacts: { title: 'Artifacts', icon: 'layers', description: 'Your private saved results.' },
  audit: { title: 'Access history', icon: 'pulse', description: 'Safe access events from your current runtime.' },
  debug: { title: 'Debug', icon: 'terminal', description: 'Real system health and safe operational diagnostics.' },
  settings: { title: 'Settings', icon: 'settings', description: 'Your account, appearance and data boundaries.' },
  more: { title: 'More', icon: 'more-horizontal', description: 'The controls around your memory.' },
};
const primary = ['overview', 'sources', 'photos', 'artifacts'];
const secondary = ['blocks', 'trips', 'audit', 'debug', 'settings'];
const mobile = ['overview', 'photos', 'artifacts', 'more'];
const endpoint: Record<string, string> = { overview: '/api/overview', sources: '/api/sources', debug: '/api/debug', audit: '/api/debug' };
type ScreenData = Overview | Sources | Debug;
function failure(error: unknown) { return error instanceof ApiError ? error.message : 'This request did not finish. Try again.'; }
function validSession(value: Session): boolean {
  return !!value && typeof value.owner?.id === 'string' && typeof value.owner?.display_name === 'string' && typeof value.csrf_token === 'string' && !!value.csrf_token;
}
export function MemoryApp() {
  const pathname = usePathname();
  const route = pathname === '/' ? 'overview' : pathname.slice(1);
  const entry = Object.hasOwn(routes, route) ? routes[route] : null;
  const [session, setSession] = useState<Session | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionError, setSessionError] = useState('');
  const [busy, setBusy] = useState(false);
  const [screen, setScreen] = useState<{ route: string; data?: ScreenData; error?: string; loading: boolean }>({ route: '', loading: true });
  const [refresh, setRefresh] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const content = useRef<HTMLDivElement>(null);
  const scroll = useRef<HTMLDivElement>(null);
  const clearSession = useCallback((message = '') => {
    setSession(null); setScreen({ route: '', loading: false }); setSessionError(message);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const verify = async () => {
      // A restored page may now belong to another cookie session. Discard its
      // prior snapshot before verification can reveal a different owner.
      setScreen({ route: '', loading: true });
      setChecking(true);
      try {
        const value = await request<Session>('/api/session', { signal: controller.signal });
        if (!validSession(value)) throw new ApiError(502, 'invalid_response', 'Your session could not be verified. Sign in again.');
        setSession(value); setSessionError('');
      } catch (error) {
        if (!controller.signal.aborted) clearSession(error instanceof ApiError && error.status === 401 ? '' : failure(error));
      } finally { if (!controller.signal.aborted) setChecking(false); }
    };
    void verify();
    const restored = (event: PageTransitionEvent) => { if (event.persisted) void verify(); };
    window.addEventListener('pageshow', restored);
    return () => { controller.abort(); window.removeEventListener('pageshow', restored); };
  }, [clearSession]);
  useEffect(() => {
    if (!session) return;
    const controller = new AbortController();
    setScreen({ route, loading: !!endpoint[route] });
    if (endpoint[route]) {
      void request<ScreenData>(endpoint[route], { signal: controller.signal }).then(data => {
        if (!controller.signal.aborted) setScreen({ route, data, loading: false });
      }).catch(error => {
        if (controller.signal.aborted) return;
        if (error instanceof ApiError && error.status === 401) clearSession('Your session has ended. Sign in again to continue.');
        else setScreen({ route, error: failure(error), loading: false });
      });
    }
    return () => controller.abort();
  }, [route, session, refresh, clearSession]);
  useEffect(() => {
    if (session && !checking) { heading.current?.focus(); if (scroll.current) scroll.current.scrollTop = 0; }
    document.title = `${session ? entry?.title || 'Page not found' : 'Sign in'} · Memory`;
  }, [route, session, checking, entry?.title]);
  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const values = new FormData(form);
    setBusy(true); setSessionError('');
    try {
      const value = await request<Session>('/api/auth/login', { method: 'POST', body: { username: values.get('username'), password: values.get('password') } });
      if (!validSession(value)) throw new ApiError(502, 'invalid_response', 'Your session could not be verified. Try again.');
      form.reset(); setSession(value);
    } catch (error) {
      setSessionError(error instanceof ApiError && error.status === 401 ? 'The username or password was not accepted.' : failure(error));
      const password = form.elements.namedItem('password'); if (password instanceof HTMLInputElement) { password.value = ''; password.focus(); }
    } finally { setBusy(false); }
  }
  async function logout() {
    if (!session) return;
    setBusy(true); setSessionError('');
    try { await request('/api/auth/logout', { method: 'POST', csrf: session.csrf_token, body: {} }); clearSession(); }
    catch (error) {
      if (error instanceof ApiError && error.status === 401) clearSession();
      else setSessionError(failure(error));
    } finally { setBusy(false); }
  }
  if (checking) return <main className="memory-auth"><div className="memory-auth-card"><ModuleTile icon="vault" accent /><p role="status" className="m-body memory-spaced">Checking your session…</p></div></main>;
  if (!session) return <main className="memory-auth"><div className="memory-auth-theme"><ThemePicker /></div><section className="memory-auth-card">
    <ModuleTile icon="vault" accent size="lg" /><p className="m-meta memory-spaced">Private Photos memory</p>
    <h1 className="m-page memory-spaced">Welcome to Memory</h1><p className="m-body memory-copy">Sign in to open your private sources and saved memories.</p>
    <form className="memory-stack memory-spaced" onSubmit={login} aria-label="Sign in">
      <label className="m-field"><span className="m-label">Username</span><input className="m-input m-input--touch" name="username" autoComplete="username" required maxLength={254} disabled={busy} /></label>
      <label className="m-field"><span className="m-label">Password</span><input className="m-input m-input--touch" name="password" type="password" autoComplete="current-password" required maxLength={1024} disabled={busy} /></label>
      {sessionError && <Notice error>{sessionError}</Notice>}
      <Button type="submit" variant="primary" size="cta" block loading={busy}>Sign in</Button>
    </form><p className="m-help memory-spaced">Memory reads your sources. It never writes to them.</p>
  </section></main>;
  const activeMobile = mobile.includes(route) ? route : 'more';
  function nav(id: string, className: string, active: string) {
    return <Link key={id} prefetch={false} href={`/${id}`} className={className} aria-label={routes[id].title} aria-current={id === active ? 'page' : undefined}>
      <Icon name={routes[id].icon} /><span className={className === 'm-navitem' ? 'm-navitem__label' : undefined}>{routes[id].title}</span>
    </Link>;
  }
  const current = screen.route === route ? screen : { route, loading: true };
  return <><a href="#memory-content" className="memory-skip m-btn m-btn--primary" onClick={event => { event.preventDefault(); content.current?.focus(); }}>Skip to content</a>
    <div className="m-shell"><aside className="m-sidebar m-shell__sidebar"><div className="m-sidebar__brand"><ModuleTile icon="vault" accent size="sm" />Memory</div>
      <nav aria-label="Primary navigation">{primary.map(id => nav(id, 'm-navitem', route))}<div className="m-sidebar__section">Photos Vault</div>{secondary.map(id => nav(id, 'm-navitem', route))}</nav>
      <div className="m-sidebar__spacer" /><div className="memory-account"><div className="m-ui">{session.owner.display_name}</div><p className="m-help">Private account</p>{session.fixture && <Badge tone="warn">Synthetic fixture</Badge>}</div>
    </aside><main className="m-shell__main"><div className="m-wash m-wash--sm" aria-hidden="true" />
      <header className="m-topbar"><span className="m-topbar__title memory-desktop-title">Memory</span><div className="m-topbar__end"><ThemePicker /><Button onClick={logout} loading={busy} variant="ghost" size="lg">Sign out</Button></div></header>
      <div className="m-shell__body memory-scroll" ref={scroll}><div id="memory-content" tabIndex={-1} className="m-shell__content memory-stack" ref={content}>
        <div><div className="m-pagehead"><h1 ref={heading} tabIndex={-1} className="m-page memory-heading">{entry?.title || 'Page not found'}</h1>{endpoint[route] && <div className="m-pagehead__actions"><Button icon="refresh" onClick={() => setRefresh(value => value + 1)} disabled={current.loading} size="lg">Refresh</Button></div>}</div><p className="m-body memory-copy">{entry?.description || 'Choose a destination from navigation.'}</p></div>
        {session.fixture && <Notice>Synthetic fixture data. This is not a personal Photos library.</Notice>}
        {sessionError && <Notice error>{sessionError}</Notice>}
        {current.loading && endpoint[route] ? <p className="m-body" role="status">Loading {entry?.title.toLowerCase()}…</p> : current.error ? <Notice error>{current.error}</Notice> : <>
          {route === 'overview' && current.data && <OverviewScreen data={current.data as Overview} />}
          {route === 'sources' && current.data && <SourcesScreen data={current.data as Sources} session={session} onUnauthorized={clearSession} />}
          {(route === 'debug' || route === 'audit') && current.data && <DebugScreen data={current.data as Debug} session={session} onUnauthorized={clearSession} auditOnly={route === 'audit'} />}
          {route === 'settings' && <SettingsScreen session={session} />}
          {route === 'photos' && <PhotosScreen onUnauthorized={clearSession} />}
          {route === 'blocks' && <BlocksScreen session={session} onUnauthorized={clearSession} />}
          {route === 'trips' && <TripsScreen session={session} onUnauthorized={clearSession} />}
          {route === 'artifacts' && <Unavailable subject={entry!.title} />}
          {route === 'more' && <nav className="memory-more" aria-label="More destinations">{['sources', ...secondary].map(id => nav(id, 'm-navitem', route))}</nav>}
          {!entry && <Notice>This page is unavailable. Your private data has not been loaded for this route.</Notice>}
        </>}
      </div></div>
    </main></div><nav className="m-bottomnav m-bottomnav--fixed memory-mobile-nav" aria-label="Primary navigation">{mobile.map(id => nav(id, 'm-bottomnav__item', activeMobile))}</nav>
  </>;
}
