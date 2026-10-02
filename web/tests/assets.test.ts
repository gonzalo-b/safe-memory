import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
test('complete shipped CSS, Inter and icons match verified local UI assets', () => {
  for (const path of ['memory-ds/memory.css', 'memory-ds/sprite.svg', 'fonts/Inter-variable.woff2']) {
    assert.deepEqual(readFileSync(new URL('../public/' + path, import.meta.url)), readFileSync(new URL('../../ui/' + path, import.meta.url)));
  }
  const css = readFileSync(new URL('../public/memory-ds/memory.css', import.meta.url), 'utf8');
  assert.equal(css.includes('fonts.googleapis.com'), false);
  assert.equal(css.includes("500&display=swap');"), false);
  assert.match(css, /:root\s*\{/);
});
