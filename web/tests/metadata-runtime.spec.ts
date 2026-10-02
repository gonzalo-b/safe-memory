/** Real Next -> Python selected metadata. Synthetic native API client; no iPhone or personal Photos. */
import { randomBytes } from 'node:crypto';
import { expect, test } from '@playwright/test';
const username = process.env.MEMORY_TEST_USERNAME;
const password = process.env.MEMORY_TEST_PASSWORD;
if (!username || !password) throw new Error('Set synthetic MEMORY_TEST_USERNAME and MEMORY_TEST_PASSWORD.');

test('real selected metadata preserves capture dates and honors explicit Hidden policy changes', async ({ page, request }, info) => {
  await page.goto('/sources');
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Sources', exact: true })).toBeVisible();
  const session = await (await page.request.get('/api/session')).json(); expect(session.fixture).toBe(true);
  const headers = { Origin: 'http://127.0.0.1:8767', 'X-CSRF-Token': session.csrf_token };
  const start = await page.request.post('/api/pairing/start', { headers, data: {} }); expect(start.status()).toBe(200);
  const credential = randomBytes(32).toString('base64url');
  const alias = `synthetic-metadata-ui-${info.project.name}-${randomBytes(6).toString('hex')}`;
  const claimResponse = await request.post('/api/device/claim', { data: { secret: (await start.json()).secret, credential, device_name: alias, library_id: alias } });
  expect(claimResponse.status()).toBe(200); const claim = await claimResponse.json();
  const confirm = await page.request.post('/api/pairing/confirm', { headers, data: { claim_id: claim.claim_id, fingerprint: claim.fingerprint } });
  expect(confirm.status()).toBe(200); const binding = await confirm.json();
  const nativeHeaders = { Authorization: `Bearer ${credential}` };
  try {
    await page.reload();
    const source = page.locator(`[data-source-id="${binding.connection_id}"]`);
    await expect(source.getByRole('checkbox', { name: 'Include Hidden' })).toHaveAttribute('aria-checked', 'false');
    await source.getByRole('checkbox', { name: 'Include Hidden' }).click();
    await source.getByRole('button', { name: 'Save source policy' }).click();
    await expect(page.getByText('Source policy saved.', { exact: true })).toBeVisible();
    await expect(source.getByRole('checkbox', { name: 'Include Hidden' })).toHaveAttribute('aria-checked', 'true');
    const day = info.project.name.includes('mobile') ? '2026-09-30' : '2026-09-29';
    const capture = `${day}T23:30:00-03:00`;
    const base = { source_revision: 'synthetic-revision-1', hidden: false, collection: 'personal', capture_time: capture, time_basis: 'capture_offset', owner_presence: 'unknown', source_modified: '2026-10-01T00:00:00Z', metadata: { synthetic_marker: 'RAW_PRIVATE_METADATA_NOT_IN_UI' } };
    const assets = [
      { ...base, native_id: `${alias}-photo`, media_type: 'photo' },
      { ...base, native_id: `${alias}-unknown`, media_type: 'video', capture_time: null, time_basis: 'unknown', owner_presence: 'third_party' },
      { ...base, native_id: `${alias}-hidden`, media_type: 'live', hidden: true },
    ];
    const begin = await request.post('/api/device/ingest/begin', { headers: nativeHeaders, data: { device_id: binding.device_id, request_key: alias, permission: 'full', phase: 'recent', selected_ids: assets.map(asset => asset.native_id) } });
    expect(begin.status()).toBe(200); const run = await begin.json();
    const append = await request.post('/api/device/ingest/append', { headers: nativeHeaders, data: { device_id: binding.device_id, run_id: run.run_id, batch_key: 'synthetic-batch', sequence: 0, checkpoint: 'synthetic-checkpoint', assets } });
    expect(append.status()).toBe(200);
    const finish = await request.post('/api/device/ingest/finish', { headers: nativeHeaders, data: { device_id: binding.device_id, run_id: run.run_id } }); expect(finish.status()).toBe(200);
    await page.goto('/photos');
    const photo = page.getByRole('article', { name: `Photo record ${alias}-photo`, exact: true });
    await expect(photo.getByText(capture, { exact: true })).toBeVisible();
    await expect(photo.getByText(day, { exact: true })).toBeVisible();
    const unknown = page.getByRole('article', { name: `Video record ${alias}-unknown`, exact: true });
    await expect(unknown.getByText('Unknown local day', { exact: true })).toBeVisible();
    await expect(unknown.getByText('Third-party provenance', { exact: true })).toBeVisible();
    await expect(page.getByText(`${alias}-hidden`, { exact: true })).toBeVisible();
    await expect(page.getByText('RAW_PRIVATE_METADATA_NOT_IN_UI', { exact: true })).toHaveCount(0);
    expect(await page.locator('img,video').count()).toBe(0);
    await page.getByRole('button', { name: 'Photos only', exact: true }).click();
    await page.getByLabel('Capture local day', { exact: true }).fill(day);
    await page.getByRole('button', { name: 'Apply filters' }).click();
    await expect(photo).toBeVisible(); await expect(unknown).toHaveCount(0);
    await page.screenshot({ path: info.outputPath('real-selected-metadata.png'), fullPage: true });
    await page.goto('/sources');
    await source.getByRole('checkbox', { name: 'Include Hidden' }).click();
    await source.getByRole('button', { name: 'Save source policy' }).click();
    await expect(page.getByText('Source policy saved.', { exact: true })).toBeVisible();
    await expect(source.getByRole('checkbox', { name: 'Include Hidden' })).toHaveAttribute('aria-checked', 'false');
    await page.goto('/photos'); await expect(photo).toBeVisible();
    await expect(page.getByText(`${alias}-hidden`, { exact: true })).toHaveCount(0);
    const current = await (await page.request.get('/api/photos?limit=200')).json();
    expect(current.assets.some((asset: { native_id: string }) => asset.native_id === `${alias}-hidden`)).toBe(false);
    await expect(unknown).toBeVisible();
  } finally {
    const revoked = await page.request.post('/api/devices/revoke', { headers, data: { device_id: binding.device_id } }); expect(revoked.status()).toBe(200);
    const denied = await request.post('/api/device/status', { headers: nativeHeaders, data: { device_id: binding.device_id } }); expect(denied.status()).toBe(401);
  }
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
});
