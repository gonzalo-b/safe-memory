const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: '.',
  outputDir: 'test-results',
  workers: 1,
  fullyParallel: false,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  use: { screenshot: 'off', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop-light', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'light' } },
    { name: 'desktop-dark',  use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' } },
    { name: 'mobile-light',  use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true } },
    { name: 'mobile-dark',   use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'dark', isMobile: true, hasTouch: true } },
  ],
});
