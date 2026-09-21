const { test, expect } = require('@playwright/test');

test('the browser driver launches', async ({ page }) => {
  await page.goto('data:text/html,<title>Safe Memory smoke</title><h1>ok</h1>');
  await expect(page).toHaveTitle('Safe Memory smoke');
  await expect(page.locator('h1')).toHaveText('ok');
});
