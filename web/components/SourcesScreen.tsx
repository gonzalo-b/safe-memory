'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Badge, Button, ModuleTile } from '../vendor/memory-ds/react/core';
import { Icon } from '../vendor/memory-ds/react/Icon';
import { ApiError, request } from '../lib/api';
import type { Device, PairingClaim, PairingIntent, Session, Sources } from '../lib/types';
import { Notice, SourcesList } from './Screens';

function ClaimCard({ claim, now, busy, confirm }: { claim: PairingClaim; now: number; busy: boolean; confirm: (claim: PairingClaim) => void }) {
  const [compared, setCompared] = useState(false);
  const expired = now >= claim.expires_at;
  return <article className="m-card m-card--raised memory-stack" aria-label={`Device request: ${claim.device_name}`}>
    <div><h3 className="m-title memory-wrap">{claim.device_name}</h3><p className="m-help memory-spaced">Compare every character below with the fingerprint shown by your iPhone connector.</p></div>
    <div><p className="m-label">Full fingerprint</p><p className="m-body m-num memory-fingerprint">{claim.fingerprint}</p></div>
    {expired ? <Badge tone="warn">Expired</Badge> : <p className="m-help m-num">Expires {new Date(claim.expires_at * 1000).toLocaleTimeString('en-GB')}</p>}
    <Button role="checkbox" aria-checked={compared} disabled={busy || expired} onClick={() => setCompared(value => !value)} className="memory-comparison" size="lg">
      <span className="m-check" aria-checked={compared} aria-hidden="true">{compared && <Icon name="check" />}</span>
      <span>I compared the full fingerprint and device name</span>
    </Button>
    <div><Button variant="tonal" size="lg" disabled={!compared || expired || busy} onClick={() => confirm(claim)}>Confirm device</Button></div>
  </article>;
}

export function SourcesScreen({ data, session, onUnauthorized }: { data: Sources; session: Session; onUnauthorized: (message?: string) => void }) {
  const [sources, setSources] = useState(data);
  const [intent, setIntent] = useState<PairingIntent | null>(null);
  const [claims, setClaims] = useState<PairingClaim[] | null>(null);
  const [devices, setDevices] = useState<Device[] | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [now, setNow] = useState(() => Math.floor(Date.now() / 1000));
  const lifetime = useRef<AbortController | null>(null);
  const failure = useCallback((value: unknown, signal: AbortSignal) => {
    if (signal.aborted) return;
    if (value instanceof ApiError && value.status === 401) onUnauthorized('Your session has ended. Sign in again to continue.');
    else setError(value instanceof ApiError ? value.message : 'This request did not finish. Try again.');
  }, [onUnauthorized]);
  const load = useCallback(async (signal: AbortSignal) => {
    setLoading(true); setError(''); setClaims(null); setDevices(null); setRevoking(null);
    try {
      const [pending, registered, current] = await Promise.all([
        request<{ claims: PairingClaim[] }>('/api/pairing/pending', { signal }),
        request<{ devices: Device[] }>('/api/devices', { signal }),
        request<Sources>('/api/sources', { signal }),
      ]);
      if (!signal.aborted) { setClaims(pending.claims); setDevices(registered.devices); setSources(current); }
    } catch (value) { failure(value, signal); }
    finally { if (!signal.aborted) setLoading(false); }
  }, [failure]);
  useEffect(() => {
    const controller = new AbortController(); lifetime.current = controller;
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);
  useEffect(() => {
    if (!intent && !claims?.length) return;
    const tick = () => {
      const current = Math.floor(Date.now() / 1000); setNow(current);
      setIntent(value => value && current >= value.expires_at ? null : value);
    };
    tick(); const timer = window.setInterval(tick, 1000);
    return () => window.clearInterval(timer);
  }, [intent?.pairing_id, claims]);
  async function mutate(action: 'start' | 'confirm' | 'revoke', body: unknown = {}) {
    const controller = lifetime.current;
    if (!controller || controller.signal.aborted || busy || loading) return;
    setBusy(action); setError(''); setMessage('');
    try {
      if (action === 'start') {
        const value = await request<PairingIntent>('/api/pairing/start', { method: 'POST', csrf: session.csrf_token, body: {}, signal: controller.signal });
        if (!controller.signal.aborted) { setNow(Math.floor(Date.now() / 1000)); setIntent(value); }
      } else {
        await request(action === 'confirm' ? '/api/pairing/confirm' : '/api/devices/revoke', { method: 'POST', csrf: session.csrf_token, body, signal: controller.signal });
        if (!controller.signal.aborted) {
          if (action === 'confirm') setIntent(null);
          setMessage(action === 'confirm' ? 'Device confirmed. Photos access is still restricted.' : 'Device revoked.');
          await load(controller.signal);
        }
      }
    } catch (value) { failure(value, controller.signal); }
    finally { if (!controller.signal.aborted) setBusy(''); }
  }
  const working = !!busy || loading;
  return <>
    <SourcesList data={sources} />
    <section className="m-card memory-stack" aria-labelledby="pairing-title">
      <div className="m-card__head"><ModuleTile icon="plug" /><h2 id="pairing-title" className="m-card__title">Connect your iPhone</h2></div>
      <p className="m-body memory-copy">Start here, then enter the pairing code in your iPhone connector. Return to compare the device name and full fingerprint before confirming.</p>
      <p className="m-help">Pairing identifies your device. Photos access remains restricted until you explicitly authorize a supported import.</p>
      <div className="memory-actions"><Button variant="primary" size="lg" onClick={() => void mutate('start')} disabled={working || !!intent} loading={busy === 'start'}>Connect iPhone</Button>
        <Button size="lg" onClick={() => lifetime.current && void load(lifetime.current.signal)} disabled={working}>Refresh devices</Button></div>
      {intent && now < intent.expires_at && <div className="m-card m-card--raised memory-stack" aria-label="Temporary pairing code">
        <h3 className="m-title">Pairing code</h3><p className="m-body m-num memory-fingerprint">{intent.secret}</p>
        <p className="m-help m-num">Expires {new Date(intent.expires_at * 1000).toLocaleTimeString('en-GB')}. This code disappears when you leave or refresh this page.</p>
        <p className="m-help">After entering it on your iPhone, select Refresh devices.</p>
      </div>}
      {loading && <p role="status" className="m-body">Loading device requests…</p>}
      {error && <Notice error>{error}</Notice>}
      {message && <Notice>{message}</Notice>}
      {claims && <div className="memory-stack"><h3 className="m-title">Pending confirmation</h3>
        {claims.length ? claims.map(claim => <ClaimCard key={`${claim.claim_id}:${claim.fingerprint}:${claim.device_name}`} claim={claim} now={now} busy={working} confirm={value => void mutate('confirm', { claim_id: value.claim_id, fingerprint: value.fingerprint })} />) : <p className="m-body memory-copy">No devices are waiting for confirmation.</p>}
      </div>}
    </section>
    <section className="m-card memory-stack" aria-labelledby="devices-title"><h2 id="devices-title" className="m-title">Your devices</h2>
      {devices ? devices.length ? devices.map(device => <article className="m-card m-card--raised memory-stack" key={device.device_id} aria-label={`Registered device: ${device.device_name}`}>
        <div className="m-card__head"><h3 className="m-title memory-wrap">{device.device_name}</h3><Badge>{device.revoked_at == null ? 'Registered' : 'Revoked'}</Badge></div>
        <div><p className="m-label">Full fingerprint</p><p className="m-body m-num memory-fingerprint">{device.fingerprint}</p></div>
        {device.revoked_at == null && (revoking === device.device_id ? <div className="memory-stack">
          <h4 className="m-title memory-wrap">Revoke {device.device_name}?</h4><p className="m-body memory-copy">This device will immediately lose its Memory connection. Your Photos library remains unchanged.</p>
          <div className="memory-actions"><Button variant="danger" size="lg" disabled={working} onClick={() => void mutate('revoke', { device_id: device.device_id })}>Confirm revocation</Button><Button variant="ghost" size="lg" disabled={working} onClick={() => setRevoking(null)}>Cancel revocation</Button></div>
        </div> : <div><Button variant="danger" size="lg" disabled={working} onClick={() => setRevoking(device.device_id)}>Revoke device</Button></div>)}
      </article>) : <p className="m-body memory-copy">No devices are registered.</p> : <p className="m-help">{loading ? 'Loading registered devices…' : 'Device information is unavailable. Refresh to try again.'}</p>}
    </section>
  </>;
}
