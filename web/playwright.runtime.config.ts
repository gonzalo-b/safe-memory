import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: '**/runtime.spec.ts', outputDir: 'runtime-test-results', workers: 1,
  reporter: [['list'], ['json', { outputFile: 'runtime-test-results/results.json' }]],
  use: { baseURL: 'http://127.0.0.1:8767', trace: 'retain-on-failure' },
  projects: [
    { name: 'runtime-desktop', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' } },
    { name: 'runtime-mobile', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true } },
  ],
});
