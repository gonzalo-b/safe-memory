---
title: "Theme-Island-Red Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

```text
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:58] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -

Running 1 test using 1 worker

(node:44826) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:44826) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:52:59] "GET /e2e/fixtures/shell.html HTTP/1.1" 304 -
  ✘  1 [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override (563ms)


  1) [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override ─────

    Error: expect(received).toBe(expected) // Object.is equality

    Expected: true
    Received: false

      27 |     const foreground=getComputedStyle(document.documentElement).getPropertyValue('--m-fg');
      28 |     return [...group.children].every(button=>getComputedStyle(button).getPropertyValue('--m-fg')===foreground);
    > 29 |   })).toBe(true);
         |       ^
      30 |   await page.getByRole('button',{name:'Dark theme'}).click();
      31 |   await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
      32 |   await page.getByRole('button',{name:'System theme'}).click();
        at /private/tmp/memory-v1-ui/e2e/shell.spec.js:29:7

    Error Context: ../memory-ui-test-results/shell-theme-choice-persists-and-system-clears-override-mobile-dark/error-context.md

    attachment #2: trace (application/zip) ─────────────────────────────────────────────────────────
    ../memory-ui-test-results/shell-theme-choice-persists-and-system-clears-override-mobile-dark/trace.zip
    Usage:

        npx playwright show-trace ../memory-ui-test-results/shell-theme-choice-persists-and-system-clears-override-mobile-dark/trace.zip

    ────────────────────────────────────────────────────────────────────────────────────────────────

  1 failed
    [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override ──────

```
