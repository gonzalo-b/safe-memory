import { defineConfig } from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({
  ...base, testMatch: '**/metadata-runtime.spec.ts', outputDir: 'runtime-test-results/metadata',
  reporter: [['list'], ['json', { outputFile: 'runtime-test-results/metadata-results.json' }]],
});
