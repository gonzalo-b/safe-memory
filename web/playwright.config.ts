import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: ['**/frontend.spec.ts', '**/pairing.spec.ts'], outputDir: 'test-results', workers: 1,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  webServer: { command: 'npm run start', url: 'http://127.0.0.1:8767', reuseExistingServer: false },
  use: { baseURL: 'http://127.0.0.1:8767', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop-light', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'light' } },
    { name: 'desktop-dark', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' } },
    { name: 'mobile-light', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true } },
    { name: 'mobile-dark', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'dark', isMobile: true, hasTouch: true } },
  ],
});
