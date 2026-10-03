import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ApiError, mediaPath, request, verifyMedia } from '../lib/api.ts';

test('private reads use same-origin cookies and disable caching', async () => {
  const old = globalThis.fetch;
  globalThis.fetch = async (path, init) => {
    assert.equal(path, '/api/session'); assert.equal(init?.credentials, 'same-origin');
    assert.equal(init?.cache, 'no-store'); assert.equal(init?.redirect, 'error');
    return Response.json({ owner: { id: 'synthetic-owner' } });
  };
  try { assert.deepEqual(await request('/api/session'), { owner: { id: 'synthetic-owner' } }); }
  finally { globalThis.fetch = old; }
});
test('mutations carry JSON and only explicit in-memory CSRF', async () => {
  const old = globalThis.fetch;
  globalThis.fetch = async (_path, init) => {
    assert.equal(init?.method, 'POST');
    assert.equal(new Headers(init?.headers).get('X-CSRF-Token'), 'synthetic-csrf');
    assert.equal(new Headers(init?.headers).get('Content-Type'), 'application/json');
    assert.equal(init?.body, '{}');
    return Response.json({ ok: true });
  };
  try { await request('/api/auth/logout', { method: 'POST', csrf: 'synthetic-csrf', body: {} }); }
  finally { globalThis.fetch = old; }
});
test('missing mutation CSRF and external URLs fail before any request', async () => {
  const old = globalThis.fetch; let calls = 0;
  globalThis.fetch = async () => { calls++; return Response.json({}); };
  try {
    await assert.rejects(request('/api/auth/logout', { method: 'POST', body: {} }), /Session verification/);
    await assert.rejects(request('https://example.org/api/session'), /local API/);
    await assert.rejects(request('/api/../secret'), /local API/);
    assert.equal(calls, 0);
  } finally { globalThis.fetch = old; }
});
test('401 and 501 remain failures and do not disclose server details', async () => {
  const old = globalThis.fetch;
  try {
    for (const [status, code] of [[401, 'unauthorized'], [501, 'not_implemented']] as const) {
      globalThis.fetch = async () => Response.json({ error: { code, message: '/private/secret-password' } }, { status });
      await assert.rejects(request('/api/overview'), (error: unknown) => {
        assert.ok(error instanceof ApiError); assert.equal(error.status, status);
        assert.equal(error.message.includes('secret'), false); return true;
      });
    }
  } finally { globalThis.fetch = old; }
});
test('network and malformed JSON fail explicitly instead of empty healthy data', async () => {
  const old = globalThis.fetch;
  try {
    globalThis.fetch = async () => { throw new TypeError('private host path'); };
    await assert.rejects(request('/api/overview'), /Could not reach Memory/);
    globalThis.fetch = async () => new Response('not json', { headers: { 'content-type': 'text/html' } });
    await assert.rejects(request('/api/overview'), /response could not be read/);
  } finally { globalThis.fetch = old; }
});
test('metadata filter queries are encoded separately without weakening local path validation', async () => {
  const old = globalThis.fetch;
  globalThis.fetch = async (path, init) => {
    assert.equal(path, '/api/photos?limit=25&offset=24&media_type=video&day=2026-10-01');
    assert.equal(init?.cache, 'no-store'); return Response.json({ assets: [], fixture: true });
  };
  try { await request('/api/photos', { query: { limit: 25, offset: 24, media_type: 'video', day: '2026-10-01' } }); }
  finally { globalThis.fetch = old; }
});
test('media manifests allow only the exact local asset endpoint', async () => {
  const old = globalThis.fetch; let calls = 0;
  globalThis.fetch = async (path, init) => { calls++; assert.equal(path, '/api/photos/' + 'a'.repeat(32) + '/media'); assert.equal(init?.cache, 'no-store'); return Response.json({ components: [] }); };
  try {
    await request('/api/photos/' + 'a'.repeat(32) + '/media');
    for (const path of ['/api/photos/../media', '/api/photos/%2f/media', '/api/photos/abc/media', '//example.org/api/media', '/api/photos/' + 'a'.repeat(32) + '/media?secret=x']) await assert.rejects(request(path), /local API/);
    assert.equal(calls, 1);
  } finally { globalThis.fetch = old; }
});

test('media error probes use private HEAD and preserve authorization failures', async () => {
  const old = globalThis.fetch;
  globalThis.fetch = async (path, init) => {
    assert.equal(path, '/api/media/' + 'b'.repeat(32)); assert.equal(init?.method, 'HEAD');
    assert.equal(init?.credentials, 'same-origin'); assert.equal(init?.cache, 'no-store'); assert.equal(init?.redirect, 'error');
    return new Response(null, { status: 401 });
  };
  try {
    await assert.rejects(verifyMedia('b'.repeat(32), new AbortController().signal), (error: unknown) => error instanceof ApiError && error.status === 401);
    assert.throws(() => mediaPath('https://example.org/media.jpg'), /local media/);
  } finally { globalThis.fetch = old; }
});

test('knowledge detail paths accept only exact32hex owner endpoints', async () => {
  const old = globalThis.fetch; const paths: string[] = [];
  globalThis.fetch = async path => { paths.push(String(path)); return Response.json({}); };
  try {
    await request('/api/knowledge/evidence/' + 'a'.repeat(32));
    await request('/api/knowledge/trips/' + 'b'.repeat(32));
    for (const path of ['/api/knowledge/evidence/abc', '/api/knowledge/trips/' + 'a'.repeat(31), '/api/knowledge/evidence/%2f', '/api/knowledge/trips/' + 'a'.repeat(32) + '/raw', '/api/knowledge/evidence/' + 'a'.repeat(32) + '?owner=x']) await assert.rejects(request(path), /local API/);
    assert.equal(paths.length, 2);
  } finally { globalThis.fetch = old; }
});

test('artifact paths allow only exact private Gallery endpoints', async()=>{
 const old=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;return Response.json({});};
 try{for(const suffix of ['','/debug','/edit','/recompose'])await request('/api/artifacts/'+'a'.repeat(32)+suffix);
 for(const path of ['/api/artifacts/abc','/api/artifacts/'+'a'.repeat(31),'/api/artifacts/'+'a'.repeat(32)+'/raw','/api/artifacts/'+'a'.repeat(32)+'?owner=x'])await assert.rejects(request(path),/local API/);assert.equal(calls,4);
 }finally{globalThis.fetch=old;}
});

test('Photos filters encode literal source text and reject invalid scope values before requests', async () => {
  const { photosQuery } = await import('../lib/api.ts');
  const filters = { type: 'live', day: '', from_day: '2026-10-01', to_day: '2026-10-02', place: 'Córdoba & <coast>', trip_id: 'a'.repeat(32), collection: 'shared_album' };
  assert.deepEqual(photosQuery(filters,24), {limit:25,offset:24,media_type:'live',from_day:'2026-10-01',to_day:'2026-10-02',place:'Córdoba & <coast>',trip_id:'a'.repeat(32),collection:'shared_album'});
  for(const change of [{day:'2026-10-01'},{from_day:'2026-10-03'},{trip_id:'../../raw'},{collection:'all-owner'},{place:'secret\nquery'},{from_day:'2026-02-31'}]) assert.throws(()=>photosQuery({...filters,...change},0));
});
