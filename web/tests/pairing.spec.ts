import { expect, test, type Page } from '@playwright/test';
const secret = 'synthetic-pairing-secret-visible-in-memory';
const fingerprint = '0123456789abcdef'.repeat(4);
const name = 'Synthetic iPhone';
async function pairingBackend(page: Page) {
  const state = { pending: false, confirmed: false, revoked: false, status: 200, expires: Math.floor(Date.now()/1000)+300,
    mutations: [] as { path: string; csrf: string; body: unknown }[] };
  await page.route('**/api/**', async route => {
    const req = route.request(), path = new URL(req.url()).pathname;
    if (req.method() === 'POST') state.mutations.push({ path, csrf: req.headers()['x-csrf-token'], body: req.postDataJSON() });
    if (path === '/api/session') return route.fulfill({ json: { owner: { id: 'owner', display_name: 'Synthetic owner' }, csrf_token: 'synthetic-csrf', fixture: true } });
    if (state.status !== 200) return route.fulfill({ status: state.status, json: { error: { message: 'SECRET_INTERNAL_TRACE' } } });
    if (path === '/api/pairing/start') return route.fulfill({ json: { pairing_id: 'intent', secret, expires_at: state.expires } });
    if (path === '/api/pairing/pending') return route.fulfill({ json: { claims: state.pending && !state.confirmed ? [{ claim_id: 'claim', device_name: name, fingerprint, expires_at: state.expires }] : [] } });
    if (path === '/api/pairing/confirm') { state.confirmed = true; return route.fulfill({ json: { device_id: 'claim', owner_id: 'owner', connection_id: 'connection', vault_id: 'vault' } }); }
    if (path === '/api/devices/revoke') { state.revoked = true; return route.fulfill({ json: { ok: true } }); }
    if (path === '/api/devices') return route.fulfill({ json: { devices: state.confirmed ? [{ device_id: 'claim', connection_id: 'connection', device_name: name, fingerprint, created_at: 1790942400, revoked_at: state.revoked ? 1790942500 : null }] : [] } });
    if (path === '/api/sources') return route.fulfill({ json: { fixture: true, sources: state.confirmed ? [{ id: 'connection', name: 'Apple Photos', permission: 'restricted', status: 'awaiting_ingest', last_success: null, index_count: 0, media_ready_count: 0 }] : [] } });
    return route.fulfill({ json: {} });
  });
  await page.goto('/sources');
  await expect(page.getByRole('heading', { name: 'No sources connected' })).toBeVisible();
  return state;
}
async function refreshPairing(page: Page) { await page.getByRole('button', { name: 'Refresh devices', exact: true }).click(); }

test('pairing secret is temporary, never stored or placed in URLs, and clears on navigation', async ({ page }) => {
  const state = await pairingBackend(page), urls: string[] = [];
  page.on('request', req => urls.push(req.url()));
  await page.getByRole('button', { name: 'Connect iPhone', exact: true }).click();
  await expect(page.getByText(secret, { exact: true })).toBeVisible();
  expect(state.mutations).toEqual([{ path: '/api/pairing/start', csrf: 'synthetic-csrf', body: {} }]);
  expect(await page.evaluate(() => [JSON.stringify(localStorage), JSON.stringify(sessionStorage)])).toEqual(['{}', '{}']);
  expect(urls.every(url => !url.includes(secret))).toBe(true);
  await page.goto('/settings'); await page.goto('/sources');
  await expect(page.getByRole('heading', { name: 'No sources connected' })).toBeVisible();
  await expect(page.getByText(secret, { exact: true })).toHaveCount(0);
});

test('full fingerprint comparison gates exact confirmation and refreshes actual source state', async ({ page }, info) => {
  const state = await pairingBackend(page); state.pending = true;
  await refreshPairing(page);
  await expect(page.getByText(fingerprint, { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Confirm device', exact: true })).toBeDisabled();
  const comparison = page.getByRole('checkbox', { name: 'I compared the full fingerprint and device name' });
  await comparison.focus(); await page.keyboard.press('Space');
  await expect(comparison).toHaveAttribute('aria-checked', 'true');
  await expect(page.getByRole('button', { name: 'Confirm device', exact: true })).toBeEnabled();
  await expect.poll(() => comparison.evaluate(element => {
    const nav = document.querySelector('.memory-mobile-nav')!;
    return getComputedStyle(nav).display === 'none' || element.getBoundingClientRect().bottom <= nav.getBoundingClientRect().top;
  })).toBe(true);
  await page.getByRole('button', { name: 'Confirm device', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath('pairing-review.png'), fullPage: true });
  await page.getByRole('button', { name: 'Confirm device', exact: true }).click();
  await expect(page.getByText('awaiting_ingest', { exact: true })).toBeVisible();
  await expect(page.getByText('restricted', { exact: true })).toBeVisible();
  expect(state.mutations).toEqual([{ path: '/api/pairing/confirm', csrf: 'synthetic-csrf', body: { claim_id: 'claim', fingerprint } }]);
  await expect(page.getByText('Device confirmed. Photos access is still restricted.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Confirm device', exact: true })).toHaveCount(0);
  await page.setViewportSize({ width: 320, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('revoke requires the selected device confirmation and reports real revoked state', async ({ page }) => {
  const state = await pairingBackend(page); state.confirmed = true; await refreshPairing(page);
  await page.getByRole('button', { name: 'Revoke device', exact: true }).click();
  await expect(page.getByRole('heading', { name: `Revoke ${name}?` })).toBeVisible();
  expect(state.mutations).toEqual([]);
  await page.getByRole('button', { name: 'Cancel revocation' }).click(); expect(state.mutations).toEqual([]);
  await page.getByRole('button', { name: 'Revoke device', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm revocation', exact: true }).click();
  await expect(page.getByText('Revoked', { exact: true })).toBeVisible();
  expect(state.mutations).toEqual([{ path: '/api/devices/revoke', csrf: 'synthetic-csrf', body: { device_id: 'claim' } }]);
  await expect(page.getByText('Device revoked.', { exact: true })).toBeVisible();
});

test('expired codes disappear and expired claims cannot be confirmed', async ({ page }) => {
  await page.clock.install();
  const state = await pairingBackend(page); state.expires = Math.floor(Date.now()/1000)+2; state.pending = true;
  await page.getByRole('button', { name: 'Connect iPhone', exact: true }).click();
  await expect(page.getByText(secret, { exact: true })).toBeVisible();
  await refreshPairing(page);
  await page.clock.fastForward(4000);
  await expect(page.getByText(secret, { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Confirm device', exact: true })).toBeDisabled();
  await expect(page.getByText('Expired', { exact: true })).toBeVisible();
});

test('pairing errors are generic and unauthorized responses clear secret and owner content', async ({ page }) => {
  const state = await pairingBackend(page);
  await page.getByRole('button', { name: 'Connect iPhone', exact: true }).click();
  await expect(page.getByText(secret, { exact: true })).toBeVisible();
  state.status = 503; await refreshPairing(page);
  await expect(page.getByRole('main').getByRole('alert')).toContainText('temporarily unavailable');
  await expect(page.getByText('SECRET_INTERNAL_TRACE')).toHaveCount(0);
  state.status = 401; await refreshPairing(page);
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
  await expect(page.getByText(secret, { exact: true })).toHaveCount(0);
});
