import { expect, test, type Page } from '@playwright/test';
const session = { owner: { id: 'synthetic-owner', display_name: 'Synthetic owner' }, csrf_token: 'synthetic-csrf', fixture: true };
function asset(index: number, changes = {}) { return { id: `id-${index}`, native_id: `native-${index}`, hidden: 0, collection: 'personal', media_type: 'photo', capture_time: '2026-10-01T23:30:00-03:00', time_basis: 'capture_offset', capture_day: '2026-10-01', owner_presence: 'unknown', media_state: 'not_transferred', ...changes }; }
async function backend(page: Page) {
  const state = { status: 200, mutationStatus: 200, assets: [asset(0), asset(1, { capture_time: null, time_basis: 'unknown', capture_day: null }), asset(2, { media_type: 'video', capture_time: '2026-10-02T02:30:00Z', time_basis: 'instant_only', capture_day: null, owner_presence: 'third_party' })], queries: [] as string[], posts: [] as { csrf: string; body: unknown }[], flags: [0, 1, 0], hold: null as Promise<void> | null };
  await page.route('**/api/**', async route => {
    const req = route.request(), url = new URL(req.url());
    if (url.pathname === '/api/session') return route.fulfill({ json: session });
    if (url.pathname === '/api/photos') {
      state.queries.push(url.search); if (state.hold) await state.hold;
      if (state.status !== 200) return route.fulfill({ status: state.status, json: { error: { message: 'PRIVATE_BACKEND_TRACE' } } });
      let rows = state.assets;
      if (url.searchParams.has('media_type')) rows = rows.filter(row => row.media_type === url.searchParams.get('media_type'));
      if (url.searchParams.has('day')) rows = rows.filter(row => row.capture_day === url.searchParams.get('day'));
      const start = Number(url.searchParams.get('offset') || 0), limit = Number(url.searchParams.get('limit') || 50);
      return route.fulfill({ json: { coverage: {mode:'selected_samples'}, fixture: true, assets: rows.slice(start, start + limit) } });
    }
    if (url.pathname === '/api/sources/policy') {
      const body = req.postDataJSON(); state.posts.push({ csrf: req.headers()['x-csrf-token'], body });
      if (state.mutationStatus !== 200) return route.fulfill({ status: state.mutationStatus, json: { error: { message: 'PRIVATE_BACKEND_TRACE' } } });
      state.flags = [body.include_hidden, body.include_shared_library, body.include_shared_albums].map(Number);
      return route.fulfill({ json: { ok: true } });
    }
    if (url.pathname === '/api/sources') return route.fulfill({ json: { fixture: true, sources: [{ id: 'connection-a', name: 'Apple Photos', status: 'sample_indexed', permission: 'limited', index_count: 3, media_ready_count: 0, last_success: null, include_hidden: state.flags[0], include_shared_library: state.flags[1], include_shared_albums: state.flags[2] }] } });
    if (url.pathname === '/api/pairing/pending') return route.fulfill({ json: { claims: [] } });
    if (url.pathname === '/api/devices') return route.fulfill({ json: { devices: [] } });
    return route.fulfill({ status: 501, json: {} });
  });
  return state;
}
test('metadata shows original capture basis, unknown local days and unavailable media honestly', async ({ page }, info) => {
  await backend(page); await page.goto('/photos');
  await expect(page.getByText('native-0', { exact: true })).toBeVisible();
  await expect(page.getByText('2026-10-01T23:30:00-03:00', { exact: true })).toBeVisible();
  await expect(page.getByText('Unknown local day', { exact: true })).toHaveCount(2);
  await expect(page.getByText('Media not transferred', { exact: true })).toHaveCount(3);
  await expect(page.getByText('Selected samples only', { exact: true })).toBeVisible();
  expect(await page.locator('img,video').count()).toBe(0);
  await page.getByRole('article', { name: 'Photo record native-0', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath('metadata-records.png'), fullPage: true });
  await page.setViewportSize({ width: 320, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Apply filters' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath('metadata.png'), fullPage: true });
  await page.getByRole('article', { name: 'Photo record native-0', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath('metadata-records-320.png'), fullPage: true });
});
test('type and local-day filters request authorized server matching and reset pagination', async ({ page }) => {
  const state = await backend(page); await page.goto('/photos'); await expect(page.getByText('native-0', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Photos only', exact: true }).click();
  await page.getByLabel('Capture local day', { exact: true }).fill('2026-10-01');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect.poll(() => state.queries.at(-1)).toBe('?limit=25&offset=0&media_type=photo&day=2026-10-01');
  await expect(page.getByText('native-1', { exact: true })).toHaveCount(0);
  await expect(page.getByText('native-0', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Clear filters' }).click();
  await expect(page.getByText('native-2', { exact: true })).toBeVisible();
  expect(state.queries.at(-1)).toBe('?limit=25&offset=0');
});
test('pagination uses bounded lookahead without claiming a whole-library total', async ({ page }) => {
  const state = await backend(page); state.assets = Array.from({ length: 25 }, (_, index) => asset(index));
  await page.goto('/photos'); await expect(page.getByText('native-0', { exact: true })).toBeVisible();
  await expect(page.getByText('native-24', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.getByText('native-24', { exact: true })).toBeVisible();
  await expect(page.getByText('native-0', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Next page' })).toBeDisabled();
  expect(state.queries.at(-1)).toBe('?limit=25&offset=24');
  await page.getByRole('button', { name: 'Previous page' }).click();
  await expect(page.getByText('native-0', { exact: true })).toBeVisible();
});
test('refresh removes stale metadata while loading, distinguishes denied and clears session on401', async ({ page }) => {
  const state = await backend(page); await page.goto('/photos'); await expect(page.getByText('native-0', { exact: true })).toBeVisible();
  let release!: () => void; state.hold = new Promise<void>(resolve => { release = resolve; });
  await page.getByRole('button', { name: 'Refresh metadata' }).click();
  await expect(page.getByText('Loading metadata…', { exact: true })).toBeVisible();
  await expect(page.getByText('native-0', { exact: true })).toHaveCount(0);
  state.status = 403; release(); state.hold = null;
  await expect(page.getByRole('main').getByRole('alert')).toContainText('not permitted');
  await expect(page.getByRole('heading', { name: 'No matching metadata' })).toHaveCount(0);
  await expect(page.getByText('PRIVATE_BACKEND_TRACE')).toHaveCount(0);
  state.status = 401; await page.getByRole('button', { name: 'Refresh metadata' }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
});
test('source consents read integer flags and save independent booleans only on explicit action', async ({ page }, info) => {
  const state = await backend(page); await page.goto('/sources');
  await expect(page.getByRole('checkbox', { name: 'Include Shared Library' })).toHaveAttribute('aria-checked', 'true');
  await expect(page.getByRole('checkbox', { name: 'Include Hidden' })).toHaveAttribute('aria-checked', 'false');
  await page.getByRole('checkbox', { name: 'Include Hidden' }).click();
  await page.getByRole('checkbox', { name: 'Include Shared Albums' }).click();
  expect(state.posts).toEqual([]);
  await page.getByRole('button', { name: 'Save source policy' }).click();
  await expect(page.getByText('Source policy saved.', { exact: true })).toBeVisible();
  expect(state.posts).toEqual([{ csrf: 'synthetic-csrf', body: { connection_id: 'connection-a', include_hidden: true, include_shared_library: true, include_shared_albums: true } }]);
  await expect(page.getByRole('checkbox', { name: 'Include Hidden' })).toHaveAttribute('aria-checked', 'true');
  await page.getByRole('checkbox', { name: 'Include Shared Albums' }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath('source-policy.png'), fullPage: true });
});
test('failed source policy save never reports success and401 clears the private screen', async ({ page }) => {
  const state = await backend(page); await page.goto('/sources');
  await page.getByRole('checkbox', { name: 'Include Hidden' }).click(); state.mutationStatus = 503;
  await page.getByRole('button', { name: 'Save source policy' }).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('temporarily unavailable');
  await expect(page.getByText('Source policy saved.')).toHaveCount(0); expect(state.flags).toEqual([0,1,0]);
  state.mutationStatus = 401; await page.getByRole('button', { name: 'Save source policy' }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
});

test('empty authorized results do not imply an empty Photos library', async ({ page }) => {
  const state = await backend(page); state.assets = []; await page.goto('/photos');
  await expect(page.getByRole('heading', { name: 'No matching metadata' })).toBeVisible();
  await expect(page.getByText('No authorized records match this page and its applied filters. This does not mean your Photos library is empty.', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Next page' })).toBeDisabled();
  await expect(page.getByRole('main').getByRole('alert')).toHaveCount(0);
});

test('photos show source place and coordinates without inventing geography and inspect current evidence', async ({ page }, info) => {
  const state = await backend(page), id = 'a'.repeat(32);
  state.assets = [asset(0, { id, location: {lat:0,lon:0,place:'<Source place>'}, geography:{city:'Explicit city'}, evidence:{asset_id:id,revision:1} }),asset(1,{location:{lat:12,lon:34},geography:{},evidence:null})];
  let evidenceReads = 0;
  await page.route('**/api/knowledge/evidence/*', route => { evidenceReads++; return route.fulfill({json:{capture_time:null,capture_day:null,media_type:'photo',owner_presence:'unknown',location:{lat:0,lon:0,place:'<Source place>'},geography:{city:'Explicit city'},evidence:{asset_id:id,revision:1,connection_id:'b'.repeat(32)}}}); });
  await page.goto('/photos');
  const first=page.getByRole('article',{name:'Photo record native-0',exact:true}),second=page.getByRole('article',{name:'Photo record native-1',exact:true});
  await expect(first.getByText('<Source place>',{exact:true})).toBeVisible();
  await expect(first.getByText('0, 0',{exact:true})).toBeVisible();
  await expect(first.getByText('Explicit city',{exact:true})).toBeVisible();
  await expect(second.getByText('Unknown',{exact:true})).toHaveCount(2);
  await expect(second.getByText('Evidence awaiting Knowledge rebuild.',{exact:true})).toBeVisible();
  await expect(second.getByRole('button',{name:'Inspect evidence'})).toHaveCount(0);
  expect(evidenceReads).toBe(0);
  await first.scrollIntoViewIfNeeded();
  await page.screenshot({path:info.outputPath('photos-source-location.png'),fullPage:true});
  await first.getByRole('button',{name:'Inspect evidence'}).click();
  const panel=page.getByRole('region',{name:'Evidence details'});
  await expect(panel.getByText(`${id} · revision 1`,{exact:true})).toBeVisible();
  await page.screenshot({path:info.outputPath('photos-place-evidence.png'),fullPage:true});
  await page.getByRole('button',{name:'Close evidence'}).click();
  await expect(first.getByRole('button',{name:'Inspect evidence'})).toBeFocused();
  await first.getByRole('button',{name:'Inspect evidence'}).click();
  await expect(panel).toBeVisible();
  await page.getByRole('button',{name:'Refresh metadata'}).click();
  await expect(panel).toHaveCount(0);
  await page.setViewportSize({width:320,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await first.scrollIntoViewIfNeeded();
  await page.screenshot({path:info.outputPath('photos-source-location-320.png'),fullPage:true});
});

test('evidence denial clears stale photo metadata and session expiry clears private UI', async ({ page }) => {
  const state=await backend(page),id='a'.repeat(32);
  state.assets=[asset(0,{id,location:{place:'Private source place'},geography:{},evidence:{asset_id:id,revision:1}})];
  let status=404;
  await page.route('**/api/knowledge/evidence/*',route=>route.fulfill({status,json:{error:{message:'PRIVATE_BACKEND_TRACE'}}}));
  await page.goto('/photos');
  await page.getByRole('button',{name:'Inspect evidence'}).click();
  await expect(page.getByRole('main').getByRole('alert')).toBeVisible();
  await expect(page.getByText('Private source place',{exact:true})).toHaveCount(0);
  await expect(page.getByText('native-0',{exact:true})).toHaveCount(0);
  await expect(page.getByText('PRIVATE_BACKEND_TRACE')).toHaveCount(0);
  status=401;
  await page.getByRole('button',{name:'Refresh metadata'}).click();
  await page.getByRole('button',{name:'Inspect evidence'}).click();
  await expect(page.getByRole('heading',{name:'Welcome to Memory'})).toBeVisible();
});
