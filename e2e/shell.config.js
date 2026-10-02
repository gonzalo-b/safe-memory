const base = require('./playwright.config');
module.exports = {...base, testMatch: 'shell.spec.js', reporter: [['list']]};
