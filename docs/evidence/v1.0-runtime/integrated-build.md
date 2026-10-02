---
title: "Runtime integrated-build"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Implementation candidate `9f05ed59ecd1f952929aa0c90bfc0b184576a5eb`; synthetic only.

```text

> safe-memory-web@0.0.0 build
> NEXT_TELEMETRY_DISABLED=1 next build

▲ Next.js 16.3.8 (Turbopack)
✓ Running next.config.ts took 1745ms

  Creating an optimized production build ...
✓ Compiled successfully in 2.7s
  Running TypeScript ...
  Finished TypeScript in 1346ms ...
  Collecting page data using 4 workers ...
  Generating static pages using 4 workers (0/2) ...
✓ Generating static pages using 4 workers (2/2) in 295ms
  Finalizing page optimization ...

Route (app)
┌ ○ /_not-found
└ ƒ /[[...path]]


○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand

```
