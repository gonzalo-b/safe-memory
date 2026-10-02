'use client';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { Badge, Button } from '../vendor/memory-ds/react/core';
import { ApiError, mediaPath, request, verifyMedia } from '../lib/api';
import type { MediaManifest, PhotoMetadata } from '../lib/types';
import { Notice } from './Screens';
function validManifest(value: MediaManifest, item: PhotoMetadata): boolean {
  const roles: Record<string, string> = item.media_type === 'photo' ? { still: 'image/jpeg' } : item.media_type === 'video' ? { video: 'video/mp4' } : { still: 'image/jpeg', motion: 'video/mp4' };
  if (!value || value.asset_id !== item.id || !Array.isArray(value.components)) return false;
  if (!value.components.every(component => component && /^[a-f0-9]{32}$/.test(component.component_id) && Object.hasOwn(roles, component.role) && roles[component.role] === component.mime && Number.isSafeInteger(component.size) && component.size > 0)) return false;
  if (new Set(value.components.map(component => component.role)).size !== value.components.length) return false;
  return value.state === 'not_transferred' ? value.components.length === 0 : value.state === 'ready' ? value.components.length === Object.keys(roles).length : value.state === 'partial' && value.components.length > 0 && value.components.length < Object.keys(roles).length;
}
export function MediaViewer({ item, onClose, onUnauthorized }: { item: PhotoMetadata; onClose: () => void; onUnauthorized: (message?: string) => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const controller = useRef<AbortController | null>(null);
  const [manifest, setManifest] = useState<MediaManifest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const title = useId(), description = useId();
  const kind = item.media_type === 'live' ? 'Live Photo' : item.media_type === 'video' ? 'Video' : 'Photo';
  const failure = useCallback((value: unknown, signal: AbortSignal) => {
    if (signal.aborted) return;
    setManifest(null);
    if (value instanceof ApiError && value.status === 401) onUnauthorized('Your session has ended. Sign in again to continue.');
    else setError(value instanceof ApiError ? value.message : 'This request did not finish. Try again.');
  }, [onUnauthorized]);
  const load = useCallback(async () => {
    controller.current?.abort(); const current = new AbortController(); controller.current = current;
    setManifest(null); setError(''); setLoading(true);
    try {
      const value = await request<MediaManifest>(`/api/photos/${item.id}/media`, { signal: current.signal });
      if (!validManifest(value, item)) throw new ApiError(502, 'invalid_response', 'The server response could not be read. Try again.');
      if (!current.signal.aborted) setManifest(value);
    } catch (value) { failure(value, current.signal); }
    finally { if (!current.signal.aborted) setLoading(false); }
  }, [item, failure]);
  useEffect(() => {
    const element = dialog.current, opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    element?.showModal();
    return () => { element?.close(); if (opener?.isConnected) opener.focus(); };
  }, []);
  useEffect(() => { void load(); return () => controller.current?.abort(); }, [load]);
  useEffect(() => {
    const videos = Array.from(dialog.current?.querySelectorAll('video') || []);
    return () => { for (const video of videos) { video.pause(); video.removeAttribute('src'); video.removeAttribute('poster'); video.load(); } };
  }, [manifest]);
  async function mediaFailed(componentId: string) {
    const current = controller.current; if (!current || current.signal.aborted) return;
    setManifest(null); setError(''); setLoading(true);
    try {
      await verifyMedia(componentId, current.signal);
      if (!current.signal.aborted) setError('This browser could not display this media. Refresh to try again.');
    } catch (value) { failure(value, current.signal); }
    finally { if (!current.signal.aborted) setLoading(false); }
  }
  const still = manifest?.components.find(component => component.role === 'still');
  const video = manifest?.components.find(component => component.role === 'video' || component.role === 'motion');
  return <dialog ref={dialog} className="m-dialog memory-viewer" aria-labelledby={title} aria-describedby={description} onCancel={event => { event.preventDefault(); onClose(); }}>
    <div className="m-dialog__body memory-stack">
      <div className="memory-viewer-head"><h2 id={title} className="m-dialog__title">{kind} viewer</h2><Button variant="ghost" size="lg" onClick={onClose}>Close viewer</Button></div>
      <p id={description} className="m-help memory-wrap">{item.native_id}</p>
      {loading ? <p role="status" className="m-body">Loading private media…</p> : error ? <Notice error>{error}</Notice> : manifest && <>
        <div><Badge>{manifest.state === 'ready' ? 'Media ready' : manifest.state === 'partial' ? 'Media partially transferred' : 'Media not transferred'}</Badge></div>
        {video ? <video className="memory-media" controls playsInline preload="metadata" aria-label={`${kind} playback: ${item.native_id}`} src={mediaPath(video.component_id)} poster={still ? mediaPath(still.component_id) : undefined} onError={() => void mediaFailed(video.component_id)}>Your browser cannot play this media.</video>
          : still ? <img className="memory-media" src={mediaPath(still.component_id)} alt={`${kind}: ${item.native_id}`} onError={() => void mediaFailed(still.component_id)} /> : <p className="m-body">No media components are available.</p>}
        {item.media_type === 'live' && !video && <p className="m-help">No motion component was transferred. Motion and sound are unavailable.</p>}
        {item.media_type === 'live' && video && !still && <p className="m-help">The still component is unavailable. Only the transferred motion component can play.</p>}
        {video && <p className="m-help">Use the player controls to start playback and adjust sound. Sound is available only if the transferred component contains an audio track.</p>}
      </>}
    </div>
    <div className="m-dialog__foot"><Button size="lg" disabled={loading} onClick={() => void load()}>Refresh media</Button></div>
  </dialog>;
}
