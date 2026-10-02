---
title: "Pairing and Selected Metadata Evidence"
project: memory
type: doc
status: done
created: 2026-10-02
source: codex-desktop
---

# Pairing and selected metadata prerequisite

Tested implementation candidate: `cf100d00cc357309a883cbb4ce68a83bb36602c2`, based on main `e93f5864544d615300af03d111b0fb5d2aa94a1b`. A following documentation/evidence-only commit relocates frontend proof and records this receipt; implementation equivalence is checked before delivery. Input plan SHA256: `ac2046dca5af017e3277376dd4e49351abf7bab367ee1a35e50ad9a05f863820`.

This is implemented and verified with synthetic data locally. It is not accepted V1.1, a whole-library connector, a physical device result or a deployment. VERSION remains0.1.0; Changelog is Unreleased. The private owner runtime is independent of legacy agent Grants; pairing creates no Grant.

| Criteria | Proof now available | Outstanding acceptance |
|---|---|---|
| F0-03, F1-02 | Explicit expiring pairing, hashed credentials, full fingerprint confirmation, replay prevention, revocation/owner epoch, one owner Photos Vault/Source per alias, browser and ASGI negatives | Real iPhone installation, consent and reconnect |
| F1-03, F1-04 | 1–100 selected IDs, bounded-sample label, lease/checkpoint retry, duplicate receipts, crash before/after commit, no partial batch | Whole-library recent/backfill enumeration and measured device transfer |
| F1-06, F1-07 | Default separate Hidden/shared consents, current-policy reads/counts, restriction observations and clock uncertainty, revoked selection/receipt fencing | Device collection provenance plus media/Blocks/Artifact propagation |
| F1-08, F2-03 | Raw authorized metadata, immutable revisions, absent time/offset semantics, per-owner filtering before counts/matching, audited reads | Real source field completeness and persistent knowledge consumers |
| Q-03, Q-04 | Audited schema migration/backup, quarantined restore revoking devices/sessions, audit failure, HTTP limits | Media/edit recovery in later slices |
| Q-02 | Pairing UI desktop/mobile light/dark, narrow/focus/error/session cases, real Next→Python confirmation/revocation | Full media/editor and physical connector journey |

## Verification

- `/opt/homebrew/bin/python3 tests/run_all.py`: exit0, **231 passed/0 failed**, [gate](gate.log). All76 original baseline names preserved with the explicitly approved six-tools→sm_block mapping.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: exit0, **67/0**, [contract](contract.log).
- Metadata service: **25/0**, including atomic rollback/crash/restart, source scope, stale receipts, Hidden/shared retention, restore and invalid schema guard. [Latest targeted run](clock-green.log).
- `npm ci --ignore-scripts`, `npm run build`, `npm run typecheck`, `npm test` (**6/6**) and `npm run check:ds`: exit0. [Build](build.log), [typecheck](typecheck.log), [unit](unit.log), [DS](ds.log). Frontend implementation unchanged from integrated2a738ec to finalcf100d0.
- `npm run test:e2e`: exit0, **52/52**, [browser](browser.log), production Next with mocked APIs. All32 foundation cases retained,20 pairing cases added.
- Final candidate API restarted with a new synthetic schema3 root. `npm run test:runtime`: exit0, **2/2**, [actual empty runtime](final-real-empty.log). Then `npm run test:pairing-runtime`: exit0, **2/2**, [actual pairing](final-real-pairing.log). No HTTP mocks: Next→Python→SQLite. Synthetic native requests only; no Apple device, Keychain or Photos execution. Actual scope creates2 revoked fixture devices and one restricted Source, no assets.
- Integrator inspected actual [desktop](pairing-desktop.png) and [mobile](pairing-mobile.png) screenshots. Earlier integrated-browser availability check failed because the host was locked; the approved Playwright fallback was used. Screenshots alone are not authorization evidence.
- `git diff --check`: exit0. Exact delivery head checks are published only after their actual runs.

## Security corrections reproduced before fixes

1. Known-old revisions could reverse a later Hidden observation and limited runs could restore excluded IDs. [RED](privacy-red.log), [GREEN](privacy-green.log).
2. Initially excluded Hidden metadata discarded its restriction watermark; an older visible revision then appeared. [RED](first-hidden-red.log), [GREEN](first-hidden-green.log). Minimal restricted identity/digest is now retained without excluded raw metadata; empty current revisions do not contribute to counts.
3. Arrival order incorrectly relaxed restrictions when source times were equal or missing. [RED](clock-red.log), [GREEN](clock-green.log). Automatic relaxation now needs a strictly newer known source timestamp; an undated restriction retains uncertainty. This may conservatively retain a restriction after a real unhide. Explicit owner category inclusion remains possible.

Independent read-only replay after fixes: [original cases](review-final.log) and [ambiguous clocks](review-ambiguous.log), both exit0. All restriction variants stay invisible; the strictly newer-time control becomes visible as intended. No known blocking finding remains within this slice's tested scope.

## Honest limits and next work

No personal source payload, account credential or media entered the model or these artifacts. Historical synthetic prototype roots are preserved; startup rejects incomplete schema3 layouts. Device criteria, whole-library progress, optimized transfers, private playback/originals, persistent Blocks/trip corrections, Artifacts, existing-host HTTPS route and owner provisioning remain mandatory. UI still marks unavailable features honestly. Native exporter/pairing implementation is separate pending integration and does not change these acceptance claims.
