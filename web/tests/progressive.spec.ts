import { expect, test, type Page } from '@playwright/test';
async function backend(page: Page) {
  const state = { status: 200, retryStatus: 200, retry: false, posts: [] as unknown[], restricted: false };
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/session') return route.fulfill({ json: { owner: { id: 'owner', display_name: 'Fixture' }, csrf_token: 'synthetic-csrf', fixture: true } });
    if (path === '/api/photos') return route.fulfill({json:{assets:[],coverage:{mode:'progressive'},fixture:true}});
    if (path === '/api/sources') return route.fulfill({ json: { sources: [], fixture: true } });
    if (path === '/api/pairing/pending') return route.fulfill({ json: { claims: [] } });
    if (path === '/api/devices') return route.fulfill({ json: { devices: [] } });
    if (path === '/api/debug') return route.fulfill({ json: { health: {storage: 'ok', audit: 'ok'}, version: '0.1.0', environment: 'fixture', operations: [], audit: [], fixture: true } });
    if (path === '/api/ingestion/retry') { state.posts.push({ csrf: route.request().headers()['x-csrf-token'], body: route.request().postDataJSON() }); if (state.retryStatus !== 200) return route.fulfill({ status: state.retryStatus, json: {} }); state.retry = true; return route.fulfill({json: {run_id: 'scan-a', state: 'waiting_for_device'}}); }
    if (path === '/api/ingestion/progress') return route.fulfill({ status: state.status, json: { scans: state.restricted ? [{run_id: 'scan-a', connection_id: 'source', state: 'restricted'}] : [{run_id: 'scan-a', connection_id: 'source', state: 'active', coverage: 'authorized_limited_scan', phase: 'backfill', observed: 2, expected_count: 5, accepted: 1, excluded: 1, first_capture: '2026-10-01T12:00:00-03:00', last_capture: '2020-01-01T12:00:00-03:00', missing_date: 0, created_at: 1790985600, completed_at: null, retry_requested: state.retry}] } });
    return route.fulfill({status: 501,json: {}});
  }); return state;
}
test('scan progress keeps limited scope, dates and media completion distinct', async ({page},info) => {
  await backend(page); await page.goto('/sources');
  const panel=page.getByRole('region',{name:'Import progress'});
  await expect(panel.getByText('Authorized limited selection', {exact:true})).toBeVisible();
  await expect(panel.getByText('2 of 5 observed', {exact:true})).toBeVisible();
  await expect(panel.getByText('Older history', {exact:true})).toBeVisible();
  await expect(panel.getByText('Index progress does not mean media is ready. See each source’s separate media count.')).toBeVisible();
  await page.setViewportSize({width:320,height:844}); await panel.scrollIntoViewIfNeeded();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath('progress.png'),fullPage:true});
});
test('Debug retry is explicit, CSRF protected and honestly waits for device', async ({page}) => {
  const state=await backend(page); await page.goto('/debug');
  const panel=page.getByRole('region',{name:'Import progress'});
  await panel.getByRole('button',{name:'Request resume',exact:true}).click();
  await expect(panel.getByText('Resume requested. Open the iPhone connector to continue.',{exact:true})).toBeVisible();
  expect(state.posts).toEqual([{csrf:'synthetic-csrf',body:{run_id:'scan-a'}}]);
  await expect(panel.getByText('Waiting for device',{exact:true})).toBeVisible();
  state.restricted=true; await panel.getByRole('button',{name:'Refresh import progress'}).click();
  await expect(panel.getByText('This scan is restricted. A fresh authorized scan is required.',{exact:true})).toBeVisible();
  await expect(panel.getByText('2 of 5 observed',{exact:true})).toHaveCount(0);await expect(panel.getByRole('button',{name:'Request resume'})).toHaveCount(0);
});
test('failed progress clears old values and401 clears owner content', async ({page})=>{
  const state=await backend(page);await page.goto('/sources');
  const panel=page.getByRole('region',{name:'Import progress'});await expect(panel.getByText('2 of 5 observed')).toBeVisible();
  state.status=503;await panel.getByRole('button',{name:'Refresh import progress'}).click();
  await expect(panel.getByRole('alert')).toContainText('temporarily unavailable');await expect(panel.getByText('2 of 5 observed')).toHaveCount(0);
  state.status=401;await panel.getByRole('button',{name:'Refresh import progress'}).click();await expect(page.getByRole('heading',{name:'Welcome to Memory'})).toBeVisible();
});

test('Photos labels progressive results without a selected-sample or complete-library claim',async({page})=>{
  await backend(page);await page.goto('/photos');
  await expect(page.getByRole('heading',{name:'Authorized Photos metadata',exact:true})).toBeVisible();
  await expect(page.getByText('Selected samples only',{exact:true})).toHaveCount(0);
  await expect(page.getByText('Only currently authorized metadata is shown. Sources reports each scan’s scope and progress; this page does not imply whole-library or media completion.')).toBeVisible();
});
