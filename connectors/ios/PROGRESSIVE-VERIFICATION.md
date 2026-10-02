---
title: "Native Progressive Scan Verification"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Progressive authorized scan preparation

Tested code candidate: `bdf5bfe7ce49e59a5576b7fd91de7190b42d3ccd`.
This evidence-only commit follows that candidate. The native checkout deliberately
remains on its owned branch; the integrator must recheck the combined revision.
No push, merge, signed installation, personal Photos read or real HTTP request
occurred here. This is engineering preparation, not a release or device acceptance.

## Criterion-to-proof mapping

| Criterion | Synthetic proof |
| --- | --- |
| Explicit full/limited indexing, recent before backfill, empty scope | `ScanWorkflowTests.swift`: replay phase order, empty authorized scan and known/unknown date ordering groups; UI compiled |
| Interrupted/restarted append uses identical durable key/payload | restart/replay group plus `ScanJournalTests.swift` restart/compact-page group |
| Permission/snapshot change cannot resume old scope | pending restriction persists offline and blocks replay; changed compact-page digest revokes before copy retry |
| Index completion separate from copies | actual `MediaCoordinator` page adapter runs while global scan remains indexing; capacity leaves metadata completion possible |
| Finite private journal, no silent cleanup | budget failure retains private state; symlink refused without touching external sentinel |
| Fixed HTTPS contract and bounded request/response | `PairingTransportTests.swift` synthetic scan begin/flags, auth, redirect and existing body/cookie/origin groups; URLProtocol intercepts all requests |
| PhotoKit API compatibility and source immutability guard | unsigned direct target build; all existing read-only/private API/network source guards pass |

The first fixture failed because progressive types were absent:
`/private/tmp/memory-scan-red.log`, exit 1. A later behavioral RED demonstrated
that page construction admitted a known date after an unknown date:
`/private/tmp/memory-scan-order-red.log`, exit 1. Descending/unknown-last checks
now run before sending, including the previous page's ordering state. The same
fixture passed in `/private/tmp/memory-scan-order-green.log`, exit 0.

Exact-candidate verification:

- `/opt/homebrew/bin/python3 tests/run_all.py`: **173 passed, 0 failed**, exit 0.
  `/private/tmp/memory-scan-candidate-gate.log`.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: **67 passed, 0 failed**, exit 0.
  `/private/tmp/memory-scan-candidate-contract.log`.
- Native suite within that gate: **19 passed, 0 failed**; thirteen Swift 6
  executables with warnings-as-errors and 62 named assertion groups. Every prior
  named native test remains. Standalone full run also passed in
  `/private/tmp/memory-scan-native-tests.log`.
- README direct-target command using installed iOS26.5 SDK, arm64,
  `CODE_SIGNING_ALLOWED=NO`, external build directories:
  **BUILD SUCCEEDED**, exit 0. `/private/tmp/memory-scan-candidate-build.log`.
  No Swift warnings; Xcode reports only skipped AppIntents metadata extraction
  because this app has no AppIntents dependency.
- `git diff --check`: pass.

Implementation objects preserved across the evidence-only commit:

| Path | Git object |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `41fe963bcfa4f71f828acca22d2095d870edde0e` |
| `connectors/ios/tests` | `d1fd2e618ded07842cbc361ada3d24eef5fd6076` |
| `tests/test_ios_probe.py` | `88a4edc85d5fad802dcdc64f719aafa63bbdc553` |

The public persistent-history token is securely archived, and ID/count hashing
streams instead of building a full raw metadata array. Any unverifiable/expired
token, permission change or changed ordering requires a fresh explicit scan.
Limited-token behavior, tie ordering across real PhotoKit fetches, actual Hidden
availability, device memory/performance, UI permission flows and physical full
coverage remain unverified. The host has no installed Simulator runtime; the
unsigned compile cannot establish those behaviors. No runtime was downloaded.

Current limits: 100 items/page, under 1 MiB metadata payload, 1,000,000 reported
items, 20,000 pages/scan, 64 retained scans and 512 MiB journal. Existing optimized
staging/server budgets still apply. Unsupported media kinds stop indexing
honestly; media capacity/unavailability does not falsely complete copies or stop
otherwise valid metadata indexing. Original-byte delivery is a separate next slice.

Temporary logs may expire with host cleanup. The committed fixtures and this
receipt preserve the tested commands, named behaviors and verification limits.
