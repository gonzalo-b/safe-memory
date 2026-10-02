---
title: "Reusable UI Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Reusable presentation component

Implementation/test candidate: `65828bc974567a16272ebce2a6ac69ddba674f46`, based on main `60580239ff93b6fa034fd1d459258e30acc05c99`. Final receipt-only commit follows; implementation equality is verified at delivery. No VERSION change or Alpha acceptance.

| Criterion | Current evidence | Limit |
| --- | --- | --- |
| F0-04 navigation / DS | Reusable sidebar, mobile More navigation, local Inter/icons, themes, history and keyboard focus implemented | Runtime, onboarding, account and data states still pending |
| Q-02 UI QA | 28 component cases on 1440×900 and 390×844 light/dark, System/override, 320px, 200% CSS zoom at desktop, reduced-motion environment, disabled storage, local resources; screenshots reviewed | Synthetic fixture, not app acceptance; CSS zoom is not a claim of native browser-zoom testing; no complete media/editor states |
| Q-04 checks | 150 aggregate/0 failed; 67 contract/0 failed; 32 browser/0 failed (28 component + 4 existing smoke); DS guard and diff check exit 0 | Does not certify the unfinished integrated runtime |

Exact-candidate commands:

```sh
python3 tests/run_all.py
python3 tests/test_stub.py
node scripts/check-ds.mjs ui/shell.js ui/shell.css ui/theme-bootstrap.js
NODE_PATH=/Users/agent/apps/memory/e2e/node_modules node /Users/agent/apps/memory/e2e/node_modules/@playwright/test/cli.js test -c e2e/playwright.config.js
git diff --check
```

Installed Playwright 1.60.0 reused read-only; no npm dependency installation. Initial sandbox server launch was denied; host-authorized loopback-only harness succeeded. Integrated browser could not unlock host; approved Playwright fallback used. Do not interpret a locked Mac as a device or Photos result.

Visual QA found the native select violated the DS and exposed a drawn border. It was replaced with named icon toggle buttons. Regression tests captured a missing mobile line-height token, inherited JavaScript property as route, missing DS theme controls, and accidental theme islands; RED logs are retained beside GREEN logs. Initial first-run test overlapped file creation and passed, so it is not presented as pre-implementation RED evidence. Independent bounded review found no additional blockers.

Original named Python checks remain untouched; the gate adds three offline asset checks. Source bytes/hashes are in ui/asset-provenance.json. Vendored CSS differs from the canonical source only at the remote font import, replaced with local Inter. Product CSS tokens are checked against the full DS; no truncated stylesheet was used. Font requests are local; no private data, network API, auth token or fake connected state exists in the component.

Screenshots: [desktop light](desktop-light.png), [desktop dark](desktop-dark.png), [mobile light](mobile-light.png), [mobile dark](mobile-dark.png). Each is visibly labelled synthetic. No screenshot is evidence of a deployed or authenticated product.

G-02 material approval remains pending. F0 runtime/persistence/auth and the real F1–F4/Q integrated path remain incomplete. Native PR7 independently recovered unsigned direct target compilation; UI/device proof is still pending. Goal remains active.

Execution-brief SHA-256: `ac2046dca5af017e3277376dd4e49351abf7bab367ee1a35e50ad9a05f863820`.
