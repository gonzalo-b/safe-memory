---
title: "Theme-Red Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

```text
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:42] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -

Running 1 test using 1 worker

(node:44104) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:44104) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:50:43] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✘  1 [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override (30.2s)


  1) [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override ─────

    Test timeout of 30000ms exceeded.

    Error: locator.click: Test timeout of 30000ms exceeded.
    Call log:
      - waiting for getByRole('button', { name: 'Light theme' })


      22 | test('theme choice persists and system clears override',async({page})=>{
      23 |   await page.goto(fixture);
    > 24 |   await page.getByRole('button',{name:'Light theme'}).click();
         |                                                       ^
      25 |   await page.reload(); await expect(page.locator('html')).toHaveAttribute('data-theme','light');
      26 |   await page.getByRole('button',{name:'Dark theme'}).click();
      27 |   await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
        at /private/tmp/memory-v1-ui/e2e/shell.spec.js:24:55

    Error Context: ../memory-ui-test-results/shell-theme-choice-persists-and-system-clears-override-mobile-dark/error-context.md

    attachment #2: trace (application/zip) ─────────────────────────────────────────────────────────
    ../memory-ui-test-results/shell-theme-choice-persists-and-system-clears-override-mobile-dark/trace.zip
    Usage:

        npx playwright show-trace ../memory-ui-test-results/shell-theme-choice-persists-and-system-clears-override-mobile-dark/trace.zip

    ────────────────────────────────────────────────────────────────────────────────────────────────

  1 failed
    [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override ──────

```
