/** Actual local Next/Python JPEG + H.264/AAC fixture playback; no personal media. */
import { expect, test } from '@playwright/test';
const username = process.env.MEMORY_TEST_USERNAME, password = process.env.MEMORY_TEST_PASSWORD;
if (!username || !password) throw new Error('Set synthetic MEMORY_TEST_USERNAME and MEMORY_TEST_PASSWORD.');

test('real private JPEG, video audio, Live partial and current-policy revocation', async ({ page }, info) => {
  await page.goto('/sources');
  await page.getByRole('textbox', { name: 'Username' }).fill(username);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Sources', exact: true })).toBeVisible();
  const session = await (await page.request.get('/api/session')).json(); expect(session.fixture).toBe(true);
  const sources = await (await page.request.get('/api/sources')).json(); expect(sources.sources).toHaveLength(1);
  const source = sources.sources[0];
  const headers = { Origin: 'http://127.0.0.1:8767', 'X-CSRF-Token': session.csrf_token };
  // Each repeat explicitly reauthorizes this synthetic category, then leaves it off.
  const hiddenChoice = page.getByRole('checkbox', { name: 'Include Hidden', exact: true });
  if (await hiddenChoice.getAttribute('aria-checked') !== 'true') {
    await hiddenChoice.click(); await page.getByRole('button', { name: 'Save source policy', exact: true }).click();
    await expect(hiddenChoice).toHaveAttribute('aria-checked', 'true');
  }
  await page.goto('/photos');
  const open = async (name: string) => page.getByRole('article').filter({ has: page.getByText(name, { exact: true }) }).getByRole('button', { name: 'Open media', exact: true }).click();
  const close = async () => page.getByRole('button', { name: 'Close viewer', exact: true }).click();
  await open('synthetic-photo');
  const image = page.locator('dialog img');
  await expect.poll(() => image.evaluate((element: HTMLImageElement) => [element.naturalWidth, element.naturalHeight])).toEqual([96,64]);
  const componentPath = await image.getAttribute('src'); expect(componentPath).toMatch(/^\/api\/media\/[a-f0-9]{32}$/);
  const head = await page.request.head(componentPath!); expect(head.status()).toBe(200); expect(head.headers()['cache-control']).toBe('no-store'); expect(head.headers()['x-content-type-options']).toBe('nosniff');
  const range = await page.request.get(componentPath!, { headers: { Range: 'bytes=0-31' } }); expect(range.status()).toBe(206); expect((await range.body()).length).toBe(32);
  await page.screenshot({ path: info.outputPath('real-private-photo.png'), fullPage: true, animations: 'disabled' }); await close();
  for (const name of ['synthetic-video', 'synthetic-live']) {
    await open(name); const video = page.locator('dialog video');
    await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.readyState)).toBeGreaterThanOrEqual(2);
    expect(await video.evaluate((element: HTMLVideoElement) => ({ paused: element.paused, muted: element.muted, autoplay: element.autoplay, controls: element.controls }))).toEqual({ paused: true, muted: false, autoplay: false, controls: true });
    if (name === 'synthetic-live') await expect(video).toHaveAttribute('poster', /^\/api\/media\/[a-f0-9]{32}$/);
    await video.evaluate((element: HTMLVideoElement) => element.play());
    await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime)).toBeGreaterThan(0.1);
    await expect.poll(() => video.evaluate((element: HTMLVideoElement & { webkitAudioDecodedByteCount?: number }) => element.webkitAudioDecodedByteCount || 0)).toBeGreaterThan(0);
    await page.screenshot({ path: info.outputPath(`${name}-playback.png`), fullPage: true, animations: 'disabled' }); await close();
  }
  await open('synthetic-partial'); await expect(page.locator('dialog img')).toBeVisible(); await expect(page.locator('dialog video')).toHaveCount(0);
  await expect(page.getByText('No motion component was transferred. Motion and sound are unavailable.', { exact: true })).toBeVisible(); await close();
  await open('synthetic-missing'); await expect(page.getByText('No media components are available.', { exact: true })).toBeVisible(); await expect(page.locator('dialog img,dialog video')).toHaveCount(0); await close();
  await open('synthetic-hidden'); await expect(page.locator('dialog img')).toBeVisible();
  const hiddenPath = await page.locator('dialog img').getAttribute('src');
  // Simulate explicit policy revocation in another owner view while this frame is open.
  const revoked = await page.request.post('/api/sources/policy', { headers, data: { connection_id: source.id, include_hidden: false, include_shared_library: Boolean(source.include_shared_library), include_shared_albums: Boolean(source.include_shared_albums) } }); expect(revoked.status()).toBe(200);
  await page.getByRole('button', { name: 'Refresh media', exact: true }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('unavailable'); await expect(page.locator('dialog img,dialog video')).toHaveCount(0);
  expect((await page.request.get(hiddenPath!)).status()).toBe(404);
  await close(); await page.getByRole('button', { name: 'Refresh metadata', exact: true }).click();
  await expect(page.getByText('synthetic-hidden', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
  expect((await page.request.get(componentPath!)).status()).toBe(401);
});
