import {defineConfig} from '@playwright/test';
import base from './playwright.runtime.config';
export default defineConfig({...base,testMatch:'**/original-runtime.spec.ts',outputDir:'runtime-test-results/originals',reporter:[['list']]});
