---
title: "Frontend Foundation Verification"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Frontend foundation verification

Status: implemented and verified with synthetic data locally; no product release, real Photos ingestion or deployment acceptance claimed. The integrator records the eventual cherry-picked candidate/delivery SHAs in the root feature receipt.

- Approved frozen input: `docs/runtime/HTTP.md` from the runtime worktree, including Debug `created_at`/`completed_at` Unix seconds.
- Versions: Next 16.3.8, React 19.3.0, TypeScript 7.0.2, Node 24.14.1.
- Dataset: explicit synthetic owner and empty private SQLite runtime. No personal media or credentials used.
- Frontend origin: `http://127.0.0.1:8767`, Python API loopback `:8766`.

| Verification | Result | Receipt |
|---|---|---|
| API TDD | Failed before implementation, then passes | `api-red.log`; `unit.log` (6 pass) |
| Production build | exit 0, TypeScript included | `build.log` |
| Explicit typecheck | exit 0 | `typecheck.log` |
| Synthetic browser matrix | 32 pass at 1440×900 and 390×844, light/dark; includes 320px, keyboard/focus and reduced motion | `browser-mocked.log` |
| Final Debug fields and safe rendering | 4 affected browser cases pass after adding IDs/counts/completion times | `browser-debug-final.log` |
| Real Next → Python integration, no mocks | 2 pass, desktop/mobile: login, empty runtime, Sources, real Debug/audit, reload session, logout and subsequent401 | `browser-runtime.log` |
| Whole local assets | Copied CSS/font/icons compared byte-for-byte against verified `ui/`; no remote fonts | unit tests |
| Product DS guard | exit 0 | `ds.log` |
| Existing Python aggregate gate | 150 pass, 0 fail, exit 0 on frontend base | `python-gate.log` |

Visual QA found duplicate desktop and mobile navigation caused by stylesheet order. `css-order-red.log` records the failing regression before the selector-specificity fix. Final desktop screenshot shows only sidebar navigation; mobile shows only the floating bottom navigation. Mobile typography and two-column statistics follow the supplied DS. The first mocked run also found a test locator ambiguity with Next's own route-announcer alert; application error assertions now target the main region, retaining exact error-content assertions.

Screenshots: `overview-desktop-dark.png`, `overview-mobile-light.png` (mocked HTTP); `runtime-debug-desktop.png`, `runtime-debug-mobile.png` (actual Python fixture). All were visually inspected. The integrated-browser tool was attempted and returned “Browser is not available: iab”; permitted Playwright fallback supplied browser proof.

Limits: synthetic empty store only, no server restart test owned by this component, no deployment, no iPhone connector, no real media, no Block/Artifact persistence claim. Full integrated F0–F4 acceptance and final browser zoom/restore/permission matrix remain integrator-owned. Unavailable screens explicitly say so. Operational logs show safe synthetic identifiers, never query payloads or secrets.

A final browser-restoration review reproduced a transient previous-session snapshot after the cookie owner changed (`session-restore-red.log`). Session verification now discards the previous screen before accepting a new session. MutationObserver regressions pass in all four viewport/theme projects and cover the transient DOM disclosure, not only the eventual loading screen.

Committed text logs remove terminal color escapes and trailing whitespace; original raw outputs remain in `/private/tmp/memory-next-*.log`.
