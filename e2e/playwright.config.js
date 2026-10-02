const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: '.',
  outputDir: 'test-results',
  workers: 1,
  fullyParallel: false,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  webServer: { command: 'python3 -m http.server 8877 --bind 127.0.0.1 --directory ..', url: 'http://127.0.0.1:8877/e2e/fixtures/shell.html', reuseExistingServer: false },
  use: { baseURL: 'http://127.0.0.1:8877', screenshot: 'off', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop-light', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'light' } },
    { name: 'desktop-dark',  use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' } },
    { name: 'mobile-light',  use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true } },
    { name: 'mobile-dark',   use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'dark', isMobile: true, hasTouch: true } },
  ],
});
