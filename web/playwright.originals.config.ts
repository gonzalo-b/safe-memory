import config from './playwright.config';
export default {...config,testMatch:['**/originals.spec.ts'],outputDir:'original-test-results',reporter:[['list']]};
