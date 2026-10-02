import { defineConfig } from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({...base,testMatch:'**/progressive-runtime.spec.ts',outputDir:'runtime-test-results/progressive',reporter:[['list'],['json',{outputFile:'runtime-test-results/progressive-results.json'}]]});
