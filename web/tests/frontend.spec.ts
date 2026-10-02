import { expect, test, type Page } from '@playwright/test';
const session = { owner: { id: 'synthetic-owner', display_name: 'Synthetic owner' }, csrf_token: 'synthetic-csrf', fixture: true };
const overview = { vault: null, counts: { assets: 0, media_ready: 0, artifacts: 0, trips: 0 }, sources: [], coverage: { index_state: 'not_connected', media_state: 'not_connected', last_success: null }, fixture: true };
async function backend(page: Page) {
  const state = { signed: false, overviewStatus: 200, sourceStatus: 200, csrf: '', loginStatus: 200 };
  await page.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const headers = { 'cache-control': 'no-store' };
    if (path === '/api/auth/login') {
      if (state.loginStatus !== 200) return route.fulfill({ status: state.loginStatus, json: { error: { code: 'unauthorized' } }, headers });
      state.signed = true;
      return route.fulfill({ json: session, headers: { ...headers, 'set-cookie': 'synthetic_session=fixture; HttpOnly; SameSite=Strict; Path=/' } });
    }
    if (!state.signed) return route.fulfill({ status: 401, json: { error: { code: 'unauthorized' } }, headers });
    if (path === '/api/auth/logout') { state.csrf = route.request().headers()['x-csrf-token']; state.signed = false; return route.fulfill({ json: { ok: true }, headers }); }
    if (path === '/api/session') return route.fulfill({ json: session, headers });
    if (path === '/api/overview') return route.fulfill({ status: state.overviewStatus, json: state.overviewStatus === 200 ? overview : { error: { code: 'unavailable', message: '/private/raw-data' } }, headers });
    if (path === '/api/sources') return route.fulfill({ status: state.sourceStatus, json: state.sourceStatus === 200 ? { sources: [], fixture: true } : { error: { code: 'not_implemented' } }, headers });
    if (path === '/api/debug') return route.fulfill({ json: { version: 'test-build', environment: 'synthetic', health: { storage: 'ok', audit: 'ok' }, operations: [], audit: [{ id: 'fixture-event', action: '<img src=x onerror=alert(1)>', outcome: 'allowed', created_at: 1790942400 }], fixture: true }, headers });
    return route.fulfill({ status: 501, json: { error: { code: 'not_implemented' } }, headers });
  });
  return state;
}
async function login(page: Page) {
  await page.goto('/');
  await page.getByRole('textbox', { name: 'Username' }).fill('synthetic');
  await page.getByLabel('Password', { exact: true }).fill('fixture-only-password');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
  await expect(page.getByText('Indexed assets', { exact: true })).toBeVisible();
}
async function navigate(page: Page, name: string) {
  let link = page.getByRole('link', { name, exact: true }).filter({ visible: true });
  if (!await link.count()) { await page.getByRole('link', { name: 'More', exact: true }).filter({ visible: true }).click(); link = page.getByRole('link', { name, exact: true }).filter({ visible: true }); }
  await link.first().click();
}
test('cookie sign-in, explicit fixture state, local assets and real-data-shaped empty view', async ({ page }, info) => {
  const errors: string[] = [], external: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:8767/')) external.push(request.url()); });
  await backend(page); await login(page);
  await expect(page.getByRole('navigation', { name: 'Primary navigation', exact: true }).filter({ visible: true })).toHaveCount(1);
  await expect(page.getByText('Synthetic fixture data.', { exact: false })).toBeVisible();
  expect((await page.context().cookies()).find(cookie => cookie.name === 'synthetic_session')?.httpOnly).toBe(true);
  await page.evaluate(() => document.fonts.ready);
  expect(await page.evaluate(() => document.fonts.check('16px Inter'))).toBe(true);
  expect(errors).toEqual([]); expect(external).toEqual([]);
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([]);
  await page.screenshot({ path: info.outputPath('overview.png'), fullPage: true });
});
test('invalid login stays signed out with generic feedback', async ({ page }) => {
  const state = await backend(page); state.loginStatus = 401;
  await page.goto('/'); await page.getByRole('textbox', { name: 'Username' }).fill('synthetic');
  await page.getByLabel('Password', { exact: true }).fill('wrong');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('main').getByRole('alert')).toHaveText('The username or password was not accepted.');
  await expect(page.getByLabel('Password', { exact: true })).toHaveValue('');
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toHaveCount(0);
});
test('navigation loads sources/debug, escapes content and marks future screens unavailable', async ({ page }) => {
  await backend(page); await login(page);
  await navigate(page, 'Sources'); await expect(page.getByRole('heading', { name: 'No sources connected' })).toBeVisible();
  await navigate(page, 'Debug'); await expect(page.getByText('test-build', { exact: true })).toBeVisible();
  await expect(page.getByText('<img src=x onerror=alert(1)>', { exact: true })).toBeVisible();
  expect(await page.locator('img').count()).toBe(0);
  await navigate(page, 'Artifacts'); await expect(page.getByRole('heading', { name: 'Not implemented in this build' })).toBeVisible();
});
test('401 clears private view and requires a fresh sign-in', async ({ page }) => {
  const state = await backend(page); await login(page); state.overviewStatus = 401;
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
  await expect(page.getByText('Indexed assets', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('main').getByRole('alert')).toContainText('Your session has ended');
});
test('failure and future endpoint are honest rather than healthy empty results', async ({ page }) => {
  const state = await backend(page); await login(page); state.overviewStatus = 503;
  await page.getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(page.getByRole('main').getByRole('alert')).toContainText('temporarily unavailable');
  await expect(page.getByText('Indexed assets', { exact: true })).toHaveCount(0);
  await expect(page.getByText('/private/raw-data', { exact: true })).toHaveCount(0);
  state.sourceStatus = 501; await navigate(page, 'Sources');
  await expect(page.getByRole('main').getByRole('alert')).toHaveText('Not implemented in this build.');
  await expect(page.getByRole('heading', { name: 'No sources connected' })).toHaveCount(0);
});
test('logout sends CSRF and browser history does not restore private data', async ({ page }) => {
  const state = await backend(page); await login(page); await navigate(page, 'Sources');
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
  expect(state.csrf).toBe('synthetic-csrf');
  await page.goBack(); await expect(page.getByRole('heading', { name: 'Welcome to Memory' })).toBeVisible();
  await expect(page.getByText('Indexed assets', { exact: true })).toHaveCount(0);
});
test('theme persistence, keyboard access, narrow viewport and reduced motion', async ({ page }) => {
  await backend(page); await login(page);
  await page.getByRole('button', { name: 'Light theme' }).click(); await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await expect(page.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Dark theme' }).click(); await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.getByRole('button', { name: 'System theme' }).click(); await expect(page.locator('html')).not.toHaveAttribute('data-theme');
  await page.getByRole('link', { name: 'Skip to content' }).focus(); await page.keyboard.press('Enter');
  await expect(page.locator('#memory-content')).toBeFocused();
  await page.setViewportSize({ width: 320, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await navigate(page, 'Memory'); await expect(page.getByRole('heading', { name: 'Memory', exact: true })).toBeFocused();
});
test('restored browser page never flashes a previous session snapshot', async ({ page }) => {
  await backend(page); await login(page);
  await page.route('**/api/session', route => route.fulfill({ json: { ...session, owner: { id: 'second-synthetic-owner', display_name: 'Second synthetic owner' } } }));
  let release!: () => void;
  const hold = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/overview', async route => { await hold; await route.fulfill({ json: overview }); });
  await page.evaluate(() => {
    const observed: string[] = [];
    Object.assign(window, { sessionFlashes: observed });
    new MutationObserver(() => {
      const text = document.querySelector('main')?.innerText || '';
      if (document.body.textContent?.includes('Second synthetic owner') && text.includes('Indexed assets')) observed.push('previous session snapshot');
    }).observe(document.body, { childList: true, subtree: true });
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
  });
  await expect(page.getByRole('status').filter({ hasText: 'Loading overview' })).toBeVisible();
  expect(await page.evaluate(() => (window as unknown as { sessionFlashes: string[] }).sessionFlashes)).toEqual([]);
  release();
});
