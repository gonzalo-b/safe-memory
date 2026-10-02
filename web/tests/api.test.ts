import assert from 'node:assert/strict';
import { test } from 'node:test';
import { ApiError, request } from '../lib/api.ts';

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
