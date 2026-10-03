// Exercise the installed PM2 parser before applying a deployment configuration.
// Usage: node deploy/verify-pm2.cjs /path/to/installed/pm2
const assert = require('node:assert/strict');
const path = require('node:path');
if (!process.argv[2]) throw new Error('Pass the installed PM2 module directory');
const Common = require(path.join(path.resolve(process.argv[2]), 'lib', 'Common.js'));
const config = require('./ecosystem.config.cjs');
const expected = structuredClone(config.apps);
const apps = Common.verifyConfs(config.apps);
assert(Array.isArray(apps), 'PM2 must accept the configuration');
for (const original of expected) {
  const app = apps.find(item => item.name === original.name);
  assert(app, 'PM2 must retain each Memory process');
  assert.equal(app.script, original.script, 'PM2 must not rewrite the entrypoint into a shell');
  assert.deepEqual(app.args, original.args, 'PM2 must retain all runtime boundaries');
  assert.equal(app.exec_interpreter, original.interpreter, 'Interpreter path must survive normalization');
  assert.equal(app.merge_logs, true, 'Use the precreated private log paths');
  assert.equal(app.out_file, original.out_file);
  assert.equal(app.error_file, original.error_file);
}
console.log('PASS: installed PM2 preserves both entrypoints, arguments, interpreters and private log paths');
