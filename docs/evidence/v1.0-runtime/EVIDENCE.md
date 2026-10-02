---
title: "Private Runtime Foundation Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Private runtime foundation

Unreleased component of F0, not Alpha acceptance. VERSION remains0.1.0. Plan SHA256 `ac2046dca5af017e3277376dd4e49351abf7bab367ee1a35e50ad9a05f863820`. Backend candidate `fef61393a4a957fbcf04ffdc5743a92eb90dd04c`, based on merged main `1efbc5e3223c2b12007fd595c2992a1bb6a368f8`. All data synthetic, temporary and separate from any personal store.

| Criteria | Current evidence | Limit |
|---|---|---|
| G-02 | GB approved Next/Python and prepared SQLite/auth/private destination delta. Private-path/recovery tests pass. | No Memory tunnel route configured or production owner provisioned yet. |
| F0-01 | Real ASGI auth, secure cookie, CSRF, Origin/Host boundaries, owner spoof denial; Next integration pending final frontend candidate. | Loopback synthetic verification, not private HTTPS deployment. |
| F0-02 | Session/store reopen, expiry, explicit persisted fixture flag. | Foundation metadata only. |
| F0-03 | Internal source creation/replay enforces unique owner/domain Vault and owner isolation. | Device pairing action still pending. |
| F0-05 | Owner-scoped safe audit/operation fields; diagnostics require committed audit. | Ingest operations do not exist yet. |
| F0-06, Q-03 | Audited backup; destination refusal before copy; corrupt-backup refusal; failed restore quarantine; successful restore revokes historical sessions and restricts Sources. | Media/Artifact recovery belongs to subsequent slices. |
| F2-03, Q-04 | Previous named baseline preserved and stdlib/no-network core guard extended to runtime. | Full current product generation/policy integration still pending. |

## Commands and results

- `/opt/homebrew/bin/python3 tests/run_all.py`, exit0 on backend candidate: **179 passed,0 failed**. [Full named log](backend-gate.md). All76 original baseline names preserved with only the previously authorized six-tools→sm_block name mapping.
- `/opt/homebrew/bin/python3 tests/test_stub.py`, exit0: **67 passed,0 failed**. [Contract log](contract.md). Executed before the final runtime-only guard addition; legacy implementation unchanged. Combined final candidate will rerun the contract.
- `/opt/homebrew/bin/python3 tests/test_runtime_http.py`, exit0:12/12. [HTTP green](http-green.md). Includes20 failed attempts from one trusted-edge client followed by an unaffected second client, denied spoofed/missing edge identity, stalled and dripped body deadline, and subsequent healthy request.
- Targeted HTTP regressions before fix, exit1:3 errors (missing explicit edge configuration and unbounded receive timeout), [RED](http-red.md). Independent review reran all3 after fix, exit0.
- Recovery iteration [green15/15](recovery-green.md) predates successful-login and domain-guard additions; aggregate candidate above is authoritative. Backup destination/audit failure and failed-restore session resurrection were reproduced before correction.
- Six valid logins incorrectly exhausted the failure limiter: [RED](login-red.md), exit1. Successful login resets the account/client failure counter; current aggregate includes the regression.
- `git diff --check`, exit0 before candidate commit. Build dependencies installed into isolated temporary venv from exact pins; Python3.14.6 supports the required scrypt implementation. No weakening for the alternate Xcode Python.

## Review and deployment boundaries

Two discovered HTTP defects fixed: proxy peer collapse and indefinite request-body reception. Trusted Cloudflare edge configuration is explicit and off by default; JSON body deadline15s and maximum64KiB. Production must verify edge→tunnel→loopback Next→loopback Python and edge header behavior. Local configuration inspection found no `memory.lazyagent.ai`/8767 route in either existing cloudflared configuration. Worker/transform settings remain unverified. Nothing was reconfigured by that review.

No personal Photos payload, credentials, user media or source read occurred. Real iPhone/signing/consent, ingestion, durable Blocks/trip corrections, private media playback, Artifacts and deployment remain mandatory outstanding work. These fixtures do not satisfy device criteria. No release or goal completion claim.

## Integrated Next/Python candidate

Frontend1411504 was cherry-picked as `9f05ed59ecd1f952929aa0c90bfc0b184576a5eb`; Python runtime implementation is identical to backendfef6139. Only evidence relocation/frontmatter and behavior documentation follow this candidate. Final PR head must pass exact-SHA checks before merge.

- `npm ci --ignore-scripts`, production `npm run build`, `npm run typecheck`, `npm test` (6/6), `npm run check:ds`: exit0. [Build](integrated-build.md), [unit/assets](integrated-unit.md).
- `npm run test:e2e`:32/32, exit0, production Next build, mocked API, desktop/mobile light/dark; keyboard/focus,320px, theme and reduced-motion cases. [Integrated browser log](integrated-browser.md).
- `npm run start`, then synthetic credentials with `npm run test:runtime`:2/2, exit0. Actual restarted Python store/API plus production Next, no HTTP mocks. Real login/cookie, Overview, Sources, safe Debug, reload and logout denial. [Integrated runtime browser log](integrated-runtime-browser.md).
- `/opt/homebrew/bin/python3 tests/test_stub.py`:67/67, exit0 on integrated implementation. [Log](integrated-contract.md).
- Integrator inspected desktop dark and mobile light screenshots in [frontend evidence](frontend/EVIDENCE.md). Supplied DS assets are preserved byte-for-byte; no remote font requests. Previous integrated-browser attempt reported unavailable; permitted Playwright fallback used.

F0-04 and F0-05 now have verified local synthetic UI/runtime evidence. F0-01 remains pending real HTTPS deployment and owner provisioning. Q-02 is partial: full personal-media/editor flow and200% zoom remain later integrated checks. Frontend browser restoration regression is RED→GREEN and detects transient previous-session DOM disclosure. No future screen simulates successful functionality.
