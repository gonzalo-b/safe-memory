import { defineConfig } from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({
  ...base, testMatch: '**/media-runtime.spec.ts', outputDir: 'runtime-test-results/media',
  reporter: [['list'], ['json', { outputFile: 'runtime-test-results/media-results.json' }]],
});
