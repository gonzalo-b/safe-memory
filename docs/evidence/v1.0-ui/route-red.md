---
title: "Route-Red Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

```text
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:12] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -

Running 1 test using 1 worker

(node:42951) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:42951) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:47:13] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✘  1 [desktop-light] › e2e/shell.spec.js:30:1 › unrecognized routes stay local and render a safe not-found page (5.5s)


  1) [desktop-light] › e2e/shell.spec.js:30:1 › unrecognized routes stay local and render a safe not-found page 

    Error: expect(locator).toBeVisible() failed

    Locator: getByRole('heading', { name: 'Page not found' })
    Expected: visible
    Timeout: 5000ms
    Error: element(s) not found

    Call log:
      - Expect "toBeVisible" with timeout 5000ms
      - waiting for getByRole('heading', { name: 'Page not found' })


      32 |   await expect(page.getByRole('heading',{name:'Page not found'})).toBeVisible();
      33 |   await page.goto(fixture+'#constructor');
    > 34 |   await expect(page.getByRole('heading',{name:'Page not found'})).toBeVisible();
         |                                                                   ^
      35 |   expect(await page.locator('img').count()).toBe(0);
      36 | });
      37 | test('skip link is keyboard operable',async({page})=>{
        at /private/tmp/memory-v1-ui/e2e/shell.spec.js:34:67

    attachment #1: screenshot (image/png) ──────────────────────────────────────────────────────────
    ../memory-ui-test-results/shell-unrecognized-routes--b2cbc-ender-a-safe-not-found-page-desktop-light/test-failed-1.png
    ────────────────────────────────────────────────────────────────────────────────────────────────

    Error Context: ../memory-ui-test-results/shell-unrecognized-routes--b2cbc-ender-a-safe-not-found-page-desktop-light/error-context.md

  1 failed
    [desktop-light] › e2e/shell.spec.js:30:1 › unrecognized routes stay local and render a safe not-found page 

```
