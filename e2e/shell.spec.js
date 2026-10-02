const { test, expect } = require('@playwright/test');
const fixture = '/e2e/fixtures/shell.html';
test('local assets load without external requests or errors', async ({page}, testInfo) => {
  const errors=[], external=[];
  page.on('pageerror', e=>errors.push(e.message));
  page.on('request', r=>{if(!r.url().startsWith('http://127.0.0.1:8877/'))external.push(r.url());});
  await page.goto(fixture);
  await expect(page.getByRole('heading', {name:'Overview',exact:true})).toBeVisible();
  await page.evaluate(()=>document.fonts.ready);
  expect(await page.evaluate(()=>document.fonts.check('16px Inter'))).toBe(true);
  expect(external).toEqual([]); expect(errors).toEqual([]);
  await page.screenshot({path:testInfo.outputPath('shell.png'),fullPage:true});
});
test('navigation and history move focus and expose current page',async({page})=>{
  await page.goto(fixture);
  await page.getByRole('link',{name:'Memory',exact:true}).filter({visible:true}).click();
  await expect(page.getByRole('heading',{name:'Memory',exact:true})).toBeFocused();
  await expect(page.locator('a[href="#photos"][aria-current="page"]').filter({visible:true})).toHaveCount(1);
  await page.goBack();
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
});
test('theme choice persists and system clears override',async({page})=>{
  await page.goto(fixture);
  await page.getByRole('button',{name:'Light theme'}).click();
  await page.reload(); await expect(page.locator('html')).toHaveAttribute('data-theme','light');
  expect(await page.getByRole('group',{name:'Color theme'}).evaluate(group=>{
    const foreground=getComputedStyle(document.documentElement).getPropertyValue('--m-fg');
    return [...group.children].every(button=>getComputedStyle(button).getPropertyValue('--m-fg')===foreground);
  })).toBe(true);
  await page.getByRole('button',{name:'Dark theme'}).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
  await page.getByRole('button',{name:'System theme'}).click();
  await expect(page.locator('html')).not.toHaveAttribute('data-theme');
});
test('unrecognized routes stay local and render a safe not-found page',async({page})=>{
  await page.goto(fixture+'#%3Cimg%20src=x%20onerror=alert(1)%3E');
  await expect(page.getByRole('heading',{name:'Page not found'})).toBeVisible();
  await page.goto(fixture+'#constructor');
  await expect(page.getByRole('heading',{name:'Page not found'})).toBeVisible();
  expect(await page.locator('img').count()).toBe(0);
});
test('skip link is keyboard operable',async({page})=>{
  await page.goto(fixture); await page.keyboard.press('Tab');
  await expect(page.getByRole('link',{name:'Skip to content'})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#memory-content')).toBeFocused();
});
test('320px and zoom keep content accessible',async({page})=>{
  await page.setViewportSize({width:320,height:844}); await page.goto(fixture);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.setViewportSize({width:1440,height:900});
  await page.locator('body').evaluate(el=>el.style.zoom='2');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await expect(page.getByRole('group',{name:'Color theme'})).toBeVisible();
});
test('storage unavailable and reduced motion do not break navigation',async({page})=>{
  await page.addInitScript(()=>{Storage.prototype.getItem=()=>{throw Error('disabled')};Storage.prototype.setItem=()=>{throw Error('disabled')};Storage.prototype.removeItem=()=>{throw Error('disabled')};});
  await page.emulateMedia({reducedMotion:'reduce'}); await page.goto(fixture);
  await page.getByRole('button',{name:'Dark theme'}).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
  await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
});
