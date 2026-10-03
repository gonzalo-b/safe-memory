import { defineConfig } from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({
  ...base, testMatch: '**/media-runtime.spec.ts', outputDir: 'runtime-test-results/media',
  // This headless host's physical audio sink stalls Chromium's playback clock.
  // Keep the element unmuted and assert decoded audio; acoustic output is not QA.
  use: { ...base.use, launchOptions: { args: ['--disable-audio-output'] } },
  reporter: [['list'], ['json', { outputFile: 'runtime-test-results/media-results.json' }]],
});
