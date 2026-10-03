import {defineConfig} from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({...base,testMatch:'**/artifact-media-runtime.spec.ts',outputDir:'runtime-test-results/artifact-media',reporter:[['list'],['json',{outputFile:'runtime-test-results/artifact-media-results.json'}]]});
