---
title: "Browser Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

```text
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:45] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -

Running 32 tests using 1 worker

(node:45761) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:45761) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:46] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:46] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:46] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:46] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:46] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   1 [desktop-light] › e2e/shell.spec.js:3:1 › local assets load without external requests or errors (497ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   2 [desktop-light] › e2e/shell.spec.js:14:1 › navigation and history move focus and expose current page (200ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /e2e/fixtures/shell.html HTTP/1.1" 304 -
  ✓   3 [desktop-light] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override (270ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   4 [desktop-light] › e2e/shell.spec.js:35:1 › unrecognized routes stay local and render a safe not-found page (100ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   5 [desktop-light] › e2e/shell.spec.js:42:1 › skip link is keyboard operable (111ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:47] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   6 [desktop-light] › e2e/shell.spec.js:48:1 › 320px and zoom keep content accessible (141ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   7 [desktop-light] › e2e/shell.spec.js:56:1 › storage unavailable and reduced motion do not break navigation (126ms)
  ✓   8 [desktop-light] › e2e/smoke.spec.js:3:1 › the browser driver launches (70ms)
(node:45785) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:45785) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓   9 [desktop-dark] › e2e/shell.spec.js:3:1 › local assets load without external requests or errors (185ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:48] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  10 [desktop-dark] › e2e/shell.spec.js:14:1 › navigation and history move focus and expose current page (192ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /e2e/fixtures/shell.html HTTP/1.1" 304 -
  ✓  11 [desktop-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override (249ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  12 [desktop-dark] › e2e/shell.spec.js:35:1 › unrecognized routes stay local and render a safe not-found page (94ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  13 [desktop-dark] › e2e/shell.spec.js:42:1 › skip link is keyboard operable (95ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  14 [desktop-dark] › e2e/shell.spec.js:48:1 › 320px and zoom keep content accessible (126ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:49] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  15 [desktop-dark] › e2e/shell.spec.js:56:1 › storage unavailable and reduced motion do not break navigation (127ms)
  ✓  16 [desktop-dark] › e2e/smoke.spec.js:3:1 › the browser driver launches (60ms)
(node:45800) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:45800) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  17 [mobile-light] › e2e/shell.spec.js:3:1 › local assets load without external requests or errors (162ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  18 [mobile-light] › e2e/shell.spec.js:14:1 › navigation and history move focus and expose current page (181ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:50] "GET /e2e/fixtures/shell.html HTTP/1.1" 304 -
  ✓  19 [mobile-light] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override (272ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  20 [mobile-light] › e2e/shell.spec.js:35:1 › unrecognized routes stay local and render a safe not-found page (98ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  21 [mobile-light] › e2e/shell.spec.js:42:1 › skip link is keyboard operable (97ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  22 [mobile-light] › e2e/shell.spec.js:48:1 › 320px and zoom keep content accessible (137ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:51] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  23 [mobile-light] › e2e/shell.spec.js:56:1 › storage unavailable and reduced motion do not break navigation (126ms)
  ✓  24 [mobile-light] › e2e/smoke.spec.js:3:1 › the browser driver launches (67ms)
(node:45813) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:45813) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  25 [mobile-dark] › e2e/shell.spec.js:3:1 › local assets load without external requests or errors (193ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  26 [mobile-dark] › e2e/shell.spec.js:14:1 › navigation and history move focus and expose current page (198ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /e2e/fixtures/shell.html HTTP/1.1" 304 -
  ✓  27 [mobile-dark] › e2e/shell.spec.js:22:1 › theme choice persists and system clears override (273ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:52] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  28 [mobile-dark] › e2e/shell.spec.js:35:1 › unrecognized routes stay local and render a safe not-found page (190ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  29 [mobile-dark] › e2e/shell.spec.js:42:1 › skip link is keyboard operable (110ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  30 [mobile-dark] › e2e/shell.spec.js:48:1 › 320px and zoom keep content accessible (130ms)
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /e2e/fixtures/shell.html HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/shell.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/memory-ds/memory.css HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/theme-bootstrap.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/shell.js HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/memory-ds/sprite.svg HTTP/1.1" 200 -
[WebServer] 127.0.0.1 - - [02/Oct/2026 16:55:53] "GET /ui/fonts/Inter-variable.woff2 HTTP/1.1" 200 -
  ✓  31 [mobile-dark] › e2e/shell.spec.js:56:1 › storage unavailable and reduced motion do not break navigation (144ms)
  ✓  32 [mobile-dark] › e2e/smoke.spec.js:3:1 › the browser driver launches (76ms)

  32 passed (7.9s)

```
