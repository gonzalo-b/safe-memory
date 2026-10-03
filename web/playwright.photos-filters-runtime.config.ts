import {defineConfig} from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({...base,testMatch:'**/photos-filters-runtime.spec.ts',outputDir:'runtime-test-results/photos-filters',reporter:[['list'],['json',{outputFile:'runtime-test-results/photos-filters-results.json'}]]});
