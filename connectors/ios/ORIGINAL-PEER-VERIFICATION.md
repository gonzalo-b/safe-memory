---
title: "Original Peer Cursor Recovery Verification"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Known upload advanced by an authorized peer

Tested candidate: `bf69752f8b949e5b34ad23c9b98adae92cdf5c15`, following originals
evidence `7091e83`. The integrator requested this bounded follow-up and owns the
combined aggregate gate. No push, merge, physical source access or real network
request occurred here.

The original client could resume an advanced manifest when binding a new upload,
but its known-upload guard admitted only the saved offset or one local chunk
beyond it. Reproduction: a 1 MiB chunk's response is lost, the local cursor stays
zero with a known upload ID, then another authorized device completes the
1 MiB + 3-byte resource. The correct server begin receipt returned invalidReceipt
indefinitely. RED: `/private/tmp/memory-original-known-peer-red.log`, exit 1.

The exact frozen manifest is validated before begin. A receipt may now advance
monotonically within that component's size. Exactly one local chunk ahead still
replays the identical chunk to recover a lost acknowledgement; other forward
advances adopt the server cursor. No re-export occurs. The regression verifies
the known upload can reach ready after peer completion, and that negative,
backward and out-of-range offsets fail before any additional chunk. Earlier
lost-chunk/completion, cloud choice, capacity, private file, Live completeness
and revocation groups remain in the same executable.

Exact-candidate verification:

- `/opt/homebrew/bin/python3 -m unittest tests.test_ios_probe.IOSContracts.test_original_replay_revocation_private_files_and_live_readiness`:
  **1 test passed**, exit 0; Swift 6 warnings-as-errors, **10 named groups**.
  `/private/tmp/memory-original-known-peer-candidate.log`.
- README direct unsigned iOS26.5 arm64 target build: **BUILD SUCCEEDED**, exit 0.
  `/private/tmp/memory-original-known-peer-build.log`.
- `git diff --check`: pass.
- Full aggregate was deliberately not duplicated for this bounded follow-up;
  the integrator will run it on the combined candidate. The earlier originals
  candidate's 176/0 gate is historical evidence, not a gate result at this SHA.

| Implementation path | Git object unchanged by evidence-only commit |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `66b148cce6c4bef334c34d313499c1d49dd8696d` |
| `connectors/ios/tests` | `28bf3b89ab46bd8b05b35faab7a47fab91ddc361` |
| `tests/test_ios_probe.py` | `8cd8c0237324d5044e7f3c7a210bbacb18f263df` |

The bounded read-only server review also reproduced cached-first-body delivery
after header-time revocation. The integrator fixed shared HTTP transport in
`c431b35`; that fix belongs to its checkout and proof, not this native commit.
Read amplification remains a reported server concern: an 8 MiB + 8-byte fixture
served as a one-byte Range hashed the full file twice. No throughput claim or
server hashing change is made here. All physical-device and PhotoKit acceptance
limits from ORIGINALS-VERIFICATION.md remain.
