import { defineConfig } from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({...base,testMatch:'**/knowledge-runtime.spec.ts',outputDir:'runtime-test-results/knowledge',reporter:[['list'],['json',{outputFile:'runtime-test-results/knowledge-results.json'}]]});
