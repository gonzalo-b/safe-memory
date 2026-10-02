---
title: "Sources pairing UI evidence"
project: memory
type: doc
status: verified-local
created: 2026-10-02
source: codex-desktop
---

# Sources pairing UI

Implementation: `1cec0c5b2df29fdd9422d165bf8a84195fe00b21`, based on merged main `e93f5864544d615300af03d111b0fb5d2aa94a1b`. The evidence-only follow-up does not change implementation. This receipt is temporarily under web/ under the subagent's ownership; the integrator will relocate it to canonical docs/evidence and run the integrated exact-SHA gate. No release, deployment, personal Photos import or physical device acceptance is claimed.

## Behavior and proof

| Criterion | Proof |
|---|---|
| Start only through explicit session/CSRF action; code is temporary component memory | Pairing browser test: no mutations before action; exact start body/CSRF; empty local/session storage; no URL disclosure; navigation discards code |
| Exact full fingerprint/device comparison before confirmation | Keyboard checkbox starts unchecked, Confirm disabled until comparison; payload contains exactly claim_id/fingerprint; full fingerprint remains readable on narrow screens |
| Register/revoke without inferring Photos access | Mock and actual Python integration show restricted/awaiting_ingest; actual native status returns data_access:false |
| Selected device requires explicit revocation | Inline named confirmation, cancel produces no mutation, exact selected device_id is sent; refreshed server status is Revoked |
| Expiry, error and authentication safety | Expired code disappears; expired claim disabled; generic503 never echoes server text;401 clears owner/code state |
| Existing presentation/session behavior preserved | All32 prior browser cases and all6 unit/asset cases retain their names and pass |
| Mobile keyboard focus remains visible | Visual review reproduced BottomNav overlap; focus-red.log fails rectangle check, scroll-padding fixes it; full final matrix includes this regression |

## Commands and results

All commands use web/ unless noted. Production build, not Next dev. Local Node24.14.1, pinned dependencies unchanged.

| Command | Result | Artifact |
|---|---|---|
| npm run build | exit0 | build.log |
| npm run typecheck | exit0 | typecheck.log |
| npm run check:ds | exit0 | ds.log |
| npm test |6 passed,0 failed | unit.log |
| npm run test:e2e |52 passed:32 existing +20 pairing; desktop1440×900/mobile390×844, both themes, additional320px check | browser.log |
| /opt/homebrew/bin/python3 tests/run_all.py (repo root) |179 passed,0 failed; this frontend checkout's backend baseline | gate.log |
| /opt/homebrew/bin/python3 tests/test_stub.py (repo root) |67 passed,0 failed | contract.log |
| npm run test:runtime |2 passed, no mocks, before any pairing | real-empty.log |
| npm run test:pairing-runtime |2 passed, no mocks, after baseline | real-pairing.log |

Real runtime: Next8767 from this checkout; Python8766 from the integrator's `/private/tmp/memory-v1-ingestion` candidate, schema3, explicitly synthetic store `/private/tmp/memory-live-fixture-f1`. Owner test credentials were supplied only to the test process; no personal account or Apple credentials. A synthetic native API client generates a fresh256-bit Memory credential in memory. The test starts pairing through UI, claims through actual `/api/device/claim`, verifies401 before confirmation, compares the full locally computed fingerprint, confirms through UI, verifies200/data_access:false, reloads, revokes through UI and verifies401 immediately. Both desktop and mobile pass. The store remains intact with one Source/Vault and two revoked synthetic device records. No metadata/media ingest was performed by this suite. Responsive browser emulation and native API traffic are not an actual iPhone connector.

## Observed failures retained

- First loopback browser attempt hit sandbox EPERM. Authorized retry successfully launched the harness; this was environment setup, not a product pass.
- `baseline-red.log`: new start-code behavior fails against unchanged F0 UI because Connect iPhone does not exist.
- `selector-failure.log`: first feature matrix48 pass/4 fail because a broad role=alert locator also matched Next's route announcer. Narrowing to main preserved the intended error assertion.
- `focus-red.log`: mobile keyboard comparison control was covered by BottomNav. `focus-green.log` and final52-case matrix prove the scroll-container fix.

## Visual evidence

Synthetic review state: [desktop light](mock-desktop-light.png), [desktop dark](mock-desktop-dark.png), [mobile light](mock-mobile-light.png), [mobile dark](mock-mobile-dark.png). Inspected light desktop and dark mobile with complete fingerprints, visible focus and unobstructed controls.

Actual Python, synthetic device revoked: [desktop](real-runtime-desktop.png), [mobile](real-runtime-mobile.png). No photograph, personal media or native-device screenshot.
