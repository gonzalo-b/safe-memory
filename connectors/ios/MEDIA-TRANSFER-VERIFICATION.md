---
title: "Native optimized-copy transfer verification"
project: memory
type: evidence
status: preparation
created: 2026-10-02
source: codex-desktop
---

# Explicit optimized copies: local verification

Tested code candidate: `4ff885d5340f6b5e07336788526666ee974a356a`, directly after
selected-metadata handoff `3c2c5ac29ec64dff26a60175fade899eaff8582b`.
An evidence-only commit follows. Scope is native connector code, its README and
synthetic native tests. No main merge, push, deployment, device installation,
personal Photos access, Keychain operation or actual HTTP request occurred.
This is not F1 acceptance or a product release.

## Criterion-to-proof mapping

| Criterion | Behavior and evidence |
| --- | --- |
| Explicit accepted sample | Copy action is separate from pairing and metadata import. Only server-accepted IDs from the last complete sample enter the exporter. Receipt mapping is persisted, with duplicate native/asset IDs refused; an older checkpoint recovers it by exact append replay. Existing metadata workflow fixture verifies recovery without a new commit or permission clear. |
| Separate consent | UI requires explicit Send/Resume optimized copies. iCloud defaults off and the job preserves the recorded choice. Startup, observers and scene callbacks never start export/upload. Changed selection or permission uses the existing durable restriction flow. UI/lifecycle is compiled, not device-tested. |
| Stable revision | Full captured metadata wrapper is revalidated before and after export, and before/after every transfer step. A synthetic revision change during export produces no chunks and retains pending restriction. Bytes are never assigned to a different or silently refreshed revision. |
| Durable interruption/replay | A fake server commits a chunk then loses its response. A new coordinator reloads the serialized checkpoint, replays the same bytes/key/offset and completes with one export, three chunk requests for two unique chunks, and one completion. A separate lost completion fixture retries only completion, without new chunks or export. |
| Revocation during transfer | A fixture restricts the sample during a chunk request. Its late receipt cannot advance the saved offset or overwrite pending restriction; completion does not happen and explicit resume sends no further chunks. Previously completed retained files also cannot resume after local revocation. |
| Independent Live components | Still and motion have distinct request keys, offsets and component receipts. A still-only fixture records one component but zero ready Live items. A two-component fixture becomes ready only after both receipts and retains the motion audio descriptor. Actual audible playback remains unverified. |
| Private retained bytes | Synthetic on-disk checkpoint reopen preserves mapping, digest, key and offset. Opaque app-relative staging is opened without following file symlinks; directory symlinks, length/digest changes and out-of-range reads fail. File and directory synchronization precede retention of upload descriptors. Credentials never enter the checkpoint. |
| Bounded transport | Exact HTTPS origin and three additional POST routes only. Native chunks are 1 MiB decoded / at most 2 MiB JSON, below server limits. Fixture requests verify base64 round trip, bearer-only credentials, redirect refusal, alternate-port refusal, body bounds and explicit 507 capacity / 409 conflict failures. Existing cookie isolation, response limits and cancellation checks remain. |
| Honest incomplete state | Missing/cloud-required/incompatible/limited exports remain incomplete with sanitized reason counts. Resume reuses retained bytes; it does not silently rerun failed exports under new consent. A fresh sample/job requires a fresh explicit metadata confirmation. No originals workflow exists. |

## RED → GREEN and test receipts

The initial new workflow test failed with the not-yet-implemented media model
and coordinator (`/private/tmp/memory-media-native-red.log`: 12 pass / 4 fail).
The new core fixture then passed in `/private/tmp/memory-media-native-green.log`.
File-fixture compilation initially rejected throwing expressions inside assert
autoclosures; these were moved to explicit reads without changing assertions.
The preserved output is `/private/tmp/memory-media-files-tests.log`. The final
focused file, transport and workflow checks pass in
`/private/tmp/memory-media-focused-tests.log`. Final revision/mid-chunk checks
pass in `/private/tmp/memory-media-final-focused.log` and the candidate gate.

At the exact code candidate:

- `/opt/homebrew/bin/python3 tests/run_all.py`: **171 passed, 0 failed**, exit 0.
  `/private/tmp/memory-media-candidate-gate.log`.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: **67 passed, 0 failed**, exit 0.
  `/private/tmp/memory-media-candidate-contract.log`.
- Native runner inside the gate: **17 passed, 0 failed**. Eleven Swift
  executables contain 50 named check groups. They compile in Swift 6 with
  warnings-as-errors. All eleven earlier native test names and all four source
  guard tests remain; two native tests were added. Tests contain synthetic data
  only, using in-memory services, temporary fixture files and catch-all
  URLProtocol, never Photos/Keychain or a real endpoint.
- Unsigned direct-target build: **BUILD SUCCEEDED**, exit 0. Exact-candidate log:
  `/private/tmp/memory-probe-media-candidate-build.log`. Full source compilation
  logs: `/private/tmp/memory-probe-media-build.log` and
  `/private/tmp/memory-probe-media-final-build.log`. No Swift warnings; the full
  build only has the normal skipped App Intents metadata warning.
- Output is an arm64 Mach-O. `codesign -dv` returns the expected exit 1:
  `code object is not signed at all`. `git diff --check` passes.

Unsigned command uses only the installed SDK:

```sh
xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj \
  -target SafeMemoryProbe -sdk iphoneos26.5 -arch arm64 -configuration Debug \
  CODE_SIGNING_ALLOWED=NO \
  OBJROOT=/private/tmp/memory-probe-media-build/obj \
  SYMROOT=/private/tmp/memory-probe-media-build/products \
  SHARED_PRECOMPS_DIR=/private/tmp/memory-probe-media-build/precompiled \
  CLANG_MODULE_CACHE_PATH=/private/tmp/memory-probe-media-build/modules build
```

Implementation identities across the evidence-only commit:

| Path | Git object |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `bcff05220274c83c9e0a026a71c34809910e42a7` |
| `connectors/ios/tests` | `26cf8a5e96e7190e66759aaad1022eeb38ff064b` |
| `tests/test_ios_probe.py` | `555dd997e16339ea0b024c3378b499b82a5e2e19` |

Temporary logs can expire with host cleanup. Root owns integrated server,
frontend and native gate verification and shared release/evidence documents.

## Limits and remaining acceptance

No iOS Simulator runtime was installed at the host-authorized inventory recorded
in `IMPORT-VERIFICATION.md`; no runtime download or physical-device operation
was performed. Native UI, PhotoKit authorization changes, real iCloud retrieval,
optimized visual/audio quality, iPhone filesystem protection/durability and
endpoint/browser playback are not established by these host fixtures or build.
Server integration and device acceptance must run at their integrated revision.

Limits remain 64 MiB/component, local staging 512 MiB / 64 export jobs and
64 retained metadata checkpoints / 64 MiB. The server contract reserves space
for staged and completed copies under 1 GiB with 256 retained upload jobs.
Exhaustion explicitly stops work; no silent deletion/eviction occurs.
An interrupted pre-upload export can leave private files counted against the
staging budget; explicit resume may export again only when no descriptors were
retained. Once retained, the exact files and request keys are reused.

This is a bounded sample and revalidation protocol, not a whole-library sync or
atomic PhotoKit snapshot. Offline/background detection cannot promise immediate
server restriction. Local ready counts summarize prior server acknowledgements;
server current revision and Source policy remain authoritative on every actual
request. Already delivered bytes cannot be retroactively removed from a client.
