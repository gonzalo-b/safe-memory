---
title: "Native metadata replay after media delivery"
project: memory
type: evidence
status: preparation
created: 2026-10-02
source: codex-desktop
---

# Completed metadata replay with ready media

Tested candidate: `4526aeba0e327839b3cce6afa1f62fbc870e0384`, following
optimized-copy evidence `953e79dfaf09db0ff6800e84d47ccb22f189da04`.
An evidence-only commit follows. No push, merge, endpoint operation or personal
source access occurred.

Root integration review found that metadata finish validation still required
`media_ready == 0`. After optimized copies arrive, the backend reports current
Source-wide readiness, which can be positive and larger than this sample.
Replaying an already completed metadata run incorrectly returned invalidReceipt.

The regression fixture completes a one-item run, then reports media_ready=123
on a completed-run retry. It failed before the fix with invalidReceipt:
`/private/tmp/memory-media-ready-red.log`, exit 1. The same test passes after
requiring a nonnegative count rather than zero. A second assertion rejects -1.
Swift Int decoding already rejects values outside the platform's integer range;
there is no arbitrary sample-sized bound on a Source-wide count. Run identity,
coverage, completion state, pairing, permission, selection and revision checks
remain unchanged. GREEN: `/private/tmp/memory-media-ready-green.log`, exit 0.

Exact-candidate receipts:

- `/opt/homebrew/bin/python3 tests/run_all.py`: **171 passed, 0 failed**, exit 0.
  `/private/tmp/memory-ready-candidate-gate.log`.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: **67 passed, 0 failed**, exit 0.
  `/private/tmp/memory-ready-candidate-contract.log`.
- Native runner included: **17 passed, 0 failed**, eleven Swift executables,
  now 51 named groups; Swift 6 with warnings-as-errors. All prior test names
  remain. Data/services are synthetic; no Photos, Keychain or real requests.
- Same unsigned direct-target command and installed iOS26.5 SDK as documented
  in `MEDIA-TRANSFER-VERIFICATION.md`: **BUILD SUCCEEDED**, exit 0.
  `/private/tmp/memory-ready-candidate-build.log`. No Swift warnings.
- `git diff --check` passes.

Implementation identities across the evidence-only commit:

| Path | Git object |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `9639dd3881ebb298ce52b57f061f76cf138fd7b7` |
| `connectors/ios/tests` | `82d8730bf2ffe07e5d3414d396d72ead700e8d8b` |
| `tests/test_ios_probe.py` | `3b541da1dae527295e57caab08c3e7c30069707a` |

Temporary logs can expire with host cleanup. This fixes the integration finding
in the earlier uploader candidate; it adds no device, UI, playback, deployment
or whole-library acceptance claim. Those limits in the earlier evidence remain.
