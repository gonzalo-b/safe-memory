import {defineConfig} from '@playwright/test';
import base from './playwright.runtime.config';
const phase=process.env.MEMORY_ARTIFACT_PHASE;
if(phase!=='prepare'&&phase!=='restart')throw new Error('Choose prepare or restart; Python must actually restart between these suites.');
export default defineConfig({...base,testMatch:`**/artifact-runtime-${phase}.spec.ts`,outputDir:`runtime-test-results/artifact-${phase}`,reporter:[['list'],['json',{outputFile:`runtime-test-results/artifact-${phase}-results.json`}]]});
