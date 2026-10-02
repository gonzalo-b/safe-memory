---
title: "Runtime integrated-browser"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Implementation candidate `9f05ed59ecd1f952929aa0c90bfc0b184576a5eb`; synthetic only.

```text

> safe-memory-web@0.0.0 test:e2e
> playwright test

[WebServer] (node:64597) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
[WebServer] (Use `node --trace-warnings ...` to show where the warning was created)

Running 32 tests using 1 worker

(node:64621) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:64621) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ✓   1 [desktop-light] › tests/frontend.spec.ts:37:1 › cookie sign-in, explicit fixture state, local assets and real-data-shaped empty view (908ms)
  ✓   2 [desktop-light] › tests/frontend.spec.ts:51:1 › invalid login stays signed out with generic feedback (253ms)
  ✓   3 [desktop-light] › tests/frontend.spec.ts:60:1 › navigation loads sources/debug, escapes content and marks future screens unavailable (493ms)
  ✓   4 [desktop-light] › tests/frontend.spec.ts:68:1 › 401 clears private view and requires a fresh sign-in (347ms)
  ✓   5 [desktop-light] › tests/frontend.spec.ts:75:1 › failure and future endpoint are honest rather than healthy empty results (438ms)
  ✓   6 [desktop-light] › tests/frontend.spec.ts:85:1 › logout sends CSRF and browser history does not restore private data (461ms)
  ✓   7 [desktop-light] › tests/frontend.spec.ts:93:1 › theme persistence, keyboard access, narrow viewport and reduced motion (582ms)
  ✓   8 [desktop-light] › tests/frontend.spec.ts:107:1 › restored browser page never flashes a previous session snapshot (303ms)
(node:64681) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:64681) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ✓   9 [desktop-dark] › tests/frontend.spec.ts:37:1 › cookie sign-in, explicit fixture state, local assets and real-data-shaped empty view (406ms)
  ✓  10 [desktop-dark] › tests/frontend.spec.ts:51:1 › invalid login stays signed out with generic feedback (263ms)
  ✓  11 [desktop-dark] › tests/frontend.spec.ts:60:1 › navigation loads sources/debug, escapes content and marks future screens unavailable (493ms)
  ✓  12 [desktop-dark] › tests/frontend.spec.ts:68:1 › 401 clears private view and requires a fresh sign-in (345ms)
  ✓  13 [desktop-dark] › tests/frontend.spec.ts:75:1 › failure and future endpoint are honest rather than healthy empty results (413ms)
  ✓  14 [desktop-dark] › tests/frontend.spec.ts:85:1 › logout sends CSRF and browser history does not restore private data (522ms)
  ✓  15 [desktop-dark] › tests/frontend.spec.ts:93:1 › theme persistence, keyboard access, narrow viewport and reduced motion (632ms)
  ✓  16 [desktop-dark] › tests/frontend.spec.ts:107:1 › restored browser page never flashes a previous session snapshot (287ms)
(node:64729) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:64729) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ✓  17 [mobile-light] › tests/frontend.spec.ts:37:1 › cookie sign-in, explicit fixture state, local assets and real-data-shaped empty view (459ms)
  ✓  18 [mobile-light] › tests/frontend.spec.ts:51:1 › invalid login stays signed out with generic feedback (327ms)
  ✓  19 [mobile-light] › tests/frontend.spec.ts:60:1 › navigation loads sources/debug, escapes content and marks future screens unavailable (657ms)
  ✓  20 [mobile-light] › tests/frontend.spec.ts:68:1 › 401 clears private view and requires a fresh sign-in (360ms)
  ✓  21 [mobile-light] › tests/frontend.spec.ts:75:1 › failure and future endpoint are honest rather than healthy empty results (502ms)
  ✓  22 [mobile-light] › tests/frontend.spec.ts:85:1 › logout sends CSRF and browser history does not restore private data (564ms)
  ✓  23 [mobile-light] › tests/frontend.spec.ts:93:1 › theme persistence, keyboard access, narrow viewport and reduced motion (572ms)
  ✓  24 [mobile-light] › tests/frontend.spec.ts:107:1 › restored browser page never flashes a previous session snapshot (338ms)
(node:64759) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:64759) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
  ✓  25 [mobile-dark] › tests/frontend.spec.ts:37:1 › cookie sign-in, explicit fixture state, local assets and real-data-shaped empty view (436ms)
  ✓  26 [mobile-dark] › tests/frontend.spec.ts:51:1 › invalid login stays signed out with generic feedback (252ms)
  ✓  27 [mobile-dark] › tests/frontend.spec.ts:60:1 › navigation loads sources/debug, escapes content and marks future screens unavailable (579ms)
  ✓  28 [mobile-dark] › tests/frontend.spec.ts:68:1 › 401 clears private view and requires a fresh sign-in (375ms)
  ✓  29 [mobile-dark] › tests/frontend.spec.ts:75:1 › failure and future endpoint are honest rather than healthy empty results (471ms)
  ✓  30 [mobile-dark] › tests/frontend.spec.ts:85:1 › logout sends CSRF and browser history does not restore private data (542ms)
  ✓  31 [mobile-dark] › tests/frontend.spec.ts:93:1 › theme persistence, keyboard access, narrow viewport and reduced motion (545ms)
  ✓  32 [mobile-dark] › tests/frontend.spec.ts:107:1 › restored browser page never flashes a previous session snapshot (275ms)

  32 passed (19.0s)
```
