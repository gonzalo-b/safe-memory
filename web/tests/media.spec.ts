import { readFileSync } from 'node:fs';
import { expect, test, type Page } from '@playwright/test';
const assetId = 'a'.repeat(32), stillId = 'b'.repeat(32), motionId = 'c'.repeat(32);
const jpeg = readFileSync(new URL('./fixtures/synthetic.jpg', import.meta.url));
const mp4 = readFileSync(new URL('./fixtures/synthetic.mp4', import.meta.url));
async function backend(page: Page, kind = 'photo') {
  const state = { manifestStatus: 200, bytesStatus: 200, manifest: { asset_id: assetId, state: 'ready', components: [{ component_id: stillId, role: 'still', mime: 'image/jpeg', size: jpeg.length }] }, reads: [] as string[], heads: 0 };
  await page.route('**/api/**', async route => {
    const req = route.request(), url = new URL(req.url());
    if (url.pathname === '/api/session') return route.fulfill({ json: { owner: { id: 'synthetic-owner', display_name: 'Synthetic owner' }, csrf_token: 'synthetic-csrf', fixture: true } });
    if (url.pathname === '/api/photos') return route.fulfill({ json: { fixture: true, assets: [{ id: assetId, native_id: 'Synthetic private record', hidden: 0, collection: 'personal', media_type: kind, capture_time: null, capture_day: null, time_basis: 'unknown', owner_presence: 'unknown', media_state: state.manifest.state }] } });
    if (url.pathname === `/api/photos/${assetId}/media`) return route.fulfill({ status: state.manifestStatus, json: state.manifestStatus === 200 ? state.manifest : { error: { message: 'PRIVATE_TRACE' } } });
    if (url.pathname.startsWith('/api/media/')) {
      state.reads.push(req.url()); if (req.method() === 'HEAD') state.heads++;
      if (state.bytesStatus !== 200) return route.fulfill({ status: state.bytesStatus, body: '' });
      const isVideo = url.pathname.endsWith(motionId), bytes = isVideo ? mp4 : jpeg;
      const headers = { 'Content-Type': isVideo ? 'video/mp4' : 'image/jpeg', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Accept-Ranges': 'bytes' };
      const range = req.headers().range?.match(/^bytes=(\d+)-(\d*)$/);
      if (range && req.method() !== 'HEAD') { const start = Number(range[1]), end = range[2] ? Number(range[2]) : bytes.length - 1; return route.fulfill({ status: 206, headers: { ...headers, 'Content-Range': `bytes ${start}-${end}/${bytes.length}` }, body: bytes.subarray(start, end + 1) }); }
      return route.fulfill({ headers, body: req.method() === 'HEAD' ? '' : bytes });
    }
    return route.fulfill({ status: 501, json: {} });
  });
  return state;
}
test('private photo decodes in a modal, traps focus and returns focus on Escape', async ({ page }, info) => {
  const state = await backend(page); await page.goto('/photos');
  const open = page.getByRole('button', { name: 'Open media', exact: true }); await open.click();
  const dialog = page.getByRole('dialog', { name: 'Photo viewer' }); await expect(dialog).toBeVisible();
  const image = dialog.getByRole('img', { name: 'Photo: Synthetic private record' });
  await expect.poll(() => image.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBeGreaterThan(0);
  expect(state.reads.every(url => new URL(url).pathname === `/api/media/${stillId}` && !new URL(url).search)).toBe(true);
  await page.keyboard.press('Tab'); expect(await page.evaluate(() => !!document.activeElement?.closest('dialog'))).toBe(true);
  await page.setViewportSize({ width: 320, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath('photo-viewer-320.png'), fullPage: true, animations: 'disabled' });
  await page.keyboard.press('Escape'); await expect(dialog).toHaveCount(0); await expect(open).toBeFocused();
  await expect(page.locator('img,video')).toHaveCount(0);
});
test('video and Live motion play only on explicit action with audio preserved', async ({ page }, info) => {
  const state = await backend(page, 'live'); state.manifest.components.push({ component_id: motionId, role: 'motion', mime: 'video/mp4', size: mp4.length });
  await page.goto('/photos'); await page.getByRole('button', { name: 'Open media', exact: true }).click();
  const video = page.locator('dialog video');
  await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.readyState)).toBeGreaterThanOrEqual(2);
  expect(await video.evaluate((element: HTMLVideoElement) => ({ paused: element.paused, muted: element.muted, autoplay: element.autoplay, controls: element.controls, poster: element.getAttribute('poster') }))).toEqual({ paused: true, muted: false, autoplay: false, controls: true, poster: `/api/media/${stillId}` });
  await video.evaluate((element: HTMLVideoElement) => element.play());
  await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime)).toBeGreaterThan(0.1);
  await expect.poll(() => video.evaluate((element: HTMLVideoElement & { webkitAudioDecodedByteCount?: number }) => element.webkitAudioDecodedByteCount || 0)).toBeGreaterThan(0);
  await page.screenshot({ path: info.outputPath('live-motion-viewer.png'), fullPage: true, animations: 'disabled' });
  await page.getByRole('button', { name: 'Close viewer', exact: true }).click(); await expect(video).toHaveCount(0);
});
test('partial Live Photo has an honest still-only state and unavailable media stays empty', async ({ page }) => {
  const state = await backend(page, 'live'); state.manifest.state = 'partial'; await page.goto('/photos');
  await page.getByRole('button', { name: 'Open media', exact: true }).click();
  await expect(page.getByText('No motion component was transferred. Motion and sound are unavailable.', { exact: true })).toBeVisible();
  await expect(page.locator('dialog img')).toBeVisible(); await expect(page.locator('video')).toHaveCount(0);
  state.manifest = { asset_id: assetId, state: 'not_transferred', components: [] };
  await page.getByRole('button', { name: 'Refresh media', exact: true }).click();
  await expect(page.getByText('No media components are available.', { exact: true })).toBeVisible();
  await expect(page.locator('img,video')).toHaveCount(0);
});
test('refresh denial removes prior media and401 removes the whole private session', async ({ page }) => {
  const state = await backend(page); await page.goto('/photos'); await page.getByRole('button', { name: 'Open media', exact: true }).click();
  await expect(page.locator('dialog img')).toBeVisible(); state.manifestStatus = 403;
  await page.getByRole('button', { name: 'Refresh media', exact: true }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('not permitted');
  await expect(page.locator('img,video')).toHaveCount(0); await expect(page.getByText('PRIVATE_TRACE')).toHaveCount(0);
  state.manifestStatus = 401; await page.getByRole('button', { name: 'Refresh media', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible(); await expect(page.locator('dialog,img,video')).toHaveCount(0);
});
test('a byte response401 is checked after decode failure and clears private media', async ({ page }) => {
  const state = await backend(page); state.bytesStatus = 401; await page.goto('/photos');
  await page.getByRole('button', { name: 'Open media', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible(); expect(state.heads).toBeGreaterThan(0);
  await expect(page.locator('dialog,img,video')).toHaveCount(0);
});
test('untrusted media component IDs never become a URL', async ({ page }) => {
  const state = await backend(page); state.manifest.components[0].component_id = 'https://example.invalid/private.jpg';
  await page.goto('/photos'); await page.getByRole('button', { name: 'Open media', exact: true }).click();
  await expect(page.getByRole('dialog').getByRole('alert')).toContainText('could not be read');
  expect(state.reads).toEqual([]); await expect(page.locator('img,video')).toHaveCount(0);
});
