---
title: "Runtime integrated-unit"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

Implementation candidate `9f05ed59ecd1f952929aa0c90bfc0b184576a5eb`; synthetic only.

```text

> safe-memory-web@0.0.0 test
> node --experimental-strip-types --test tests/*.test.ts

✔ private reads use same-origin cookies and disable caching (33.168167ms)
✔ mutations carry JSON and only explicit in-memory CSRF (0.536ms)
✔ missing mutation CSRF and external URLs fail before any request (0.358583ms)
✔ 401 and 501 remain failures and do not disclose server details (0.272167ms)
✔ network and malformed JSON fail explicitly instead of empty healthy data (0.31175ms)
✔ complete shipped CSS, Inter and icons match verified local UI assets (4.260416ms)
ℹ tests 6
ℹ suites 0
ℹ pass 6
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 467.204375
```
