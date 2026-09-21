const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.join(__dirname, '..');
const VERSION = fs.readFileSync(path.join(REPO_ROOT, 'VERSION'), 'utf8').trim();

async function shot(page, testInfo, id) {
  const { width, height } = testInfo.project.use.viewport;
  const theme = testInfo.project.use.colorScheme;
  const dir = path.join(REPO_ROOT, 'docs', 'evidence', VERSION);
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${id}-${width}x${height}-${theme}.png`);
  await page.screenshot({ path: file });
  return file;
}

function consoleErrors(page) {
  const errors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (err) => {
    errors.push(String(err));
  });
  return errors;
}

module.exports = { shot, consoleErrors, VERSION, REPO_ROOT };
