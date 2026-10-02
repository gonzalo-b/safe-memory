import { defineConfig } from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({
  ...base, testMatch: '**/pairing-runtime.spec.ts', outputDir: 'runtime-test-results/pairing',
  reporter: [['list'], ['json', { outputFile: 'runtime-test-results/pairing-results.json' }]],
});
