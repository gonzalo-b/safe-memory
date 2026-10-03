import { defineConfig } from '@playwright/test';
const port = Number(process.env.MEMORY_TEST_PORT || 8767);
if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error('Invalid local test port.');
const baseURL = `http://127.0.0.1:${port}`;
export default defineConfig({
  testDir: './tests', testMatch: ['**/frontend.spec.ts', '**/pairing.spec.ts', '**/metadata.spec.ts', '**/media.spec.ts', '**/progressive.spec.ts', '**/knowledge.spec.ts', '**/artifacts.spec.ts', '**/integrated-accessibility.spec.ts'], outputDir: 'test-results', workers: 1,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  webServer: { command: `NEXT_TELEMETRY_DISABLED=1 npx next start --hostname 127.0.0.1 --port ${port}`, url: baseURL, reuseExistingServer: false },
  use: { baseURL, trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop-light', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'light' } },
    { name: 'desktop-dark', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' } },
    { name: 'mobile-light', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true } },
    { name: 'mobile-dark', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'dark', isMobile: true, hasTouch: true } },
  ],
});
