---
title: "Native selected metadata import verification"
project: memory
type: evidence
status: preparation
created: 2026-10-02
source: codex-desktop
---

# Explicit selected metadata import: local verification

Tested code candidate: `1a2264bae38ab5c6c93391aa4621f465d6f12aeb`, based on
`1206f2878881f66078c68865b921a337453bba3b`. An evidence-only commit follows.
This is code preparation for the approved native connector, not F1 device
acceptance or a product release. No push, merge, deployment, signing, device
installation, personal Photos access or actual endpoint request occurred.

## Criterion-to-proof mapping

| Criterion | Implemented behavior and synthetic proof |
| --- | --- |
| Explicit bounded selection | Separate PhotosPicker UI accepts 1–100 IDs and requires explicit metadata consent. Only IDs are read from picker items; no `loadTransferable`. Selected PhotoKit reads use only `fetchAssets(withLocalIdentifiers:)`. Empty, duplicate, missing and over-limit IDs fail. Source guard forbids mutation/private APIs and broader permission requests in the selected reader. |
| Honest metadata | Every currently captured `ProbeAsset` field remains in `metadata`. Creation Date becomes an instant with `time_basis: instant_only`; absent dates are null/unknown. Collection and owner presence remain unknown. No source timezone, personal-library identity or owner presence is inferred. |
| Stable full revision | SHA-256 covers canonical sorted-key ASCII JSON of the complete wire wrapper excluding only `source_revision`, with explicit nulls. Resource descriptors are sorted deterministically. Synthetic tests reconstruct the wrapper independently and verify stability, non-ASCII escaping and changes to favorite/Hidden metadata. |
| Source policy | Both possible Shared Library and Shared Album native consents are required because collection is unknown; Hidden consent is separate. Server policy remains independently authoritative. A permission request clears previous server selection before every new sample, including full→full. |
| Retry after interruption | Frozen selection, revisions, job/batch keys and stage are persisted before ingestion. A lost append response is reproduced after the fake server commits. A new coordinator resumes with the same keys and identical bytes: two append requests, one commit. Append is replayed even when begin reports sequence one, recovering accepted/excluded counts. |
| Revocation and races | Denied permission, unavailable selected ID or changed metadata invalidate the saved selection. Pending restriction is persisted before sending. Offline failures block resume without pretending the server is restricted. Concurrent callbacks share one in-flight revocation; late import responses cannot overwrite pending/revoked state. |
| Durable private checkpoint | Synthetic on-disk restart preserves the exact wrapper and stage. Jobs are app-owned, mode 0600 under mode 0700 storage, with iOS complete protection and backup exclusion. Atomic writes are file- and directory-synchronized. Corrupt revisions and symlink pointers fail closed. Pairing credentials are never saved in checkpoints. |
| Bounded HTTPS | Four exact POST routes use the existing isolated ephemeral transport, fixed HTTPS origin, bearer header only, no cookies, redirects, URL credentials, alternate ports or unexpected headers. Append cap 1 MiB, other requests 64 KiB, response cap 256 KiB. URLProtocol tests intercept every request and verify metadata authorization, redirect refusal and response bound. |
| Explicit UI lifecycle | Import, resume and clear actions are separate. Saved sample count and retained consents require their own resume acknowledgement. Selection changes revoke prior scope; active scene and PhotoKit observer revalidate existing checkpoints only. These UI/lifecycle paths compile but have not been exercised on a device. |

## RED → GREEN evidence

- Initial import tests failed because the new contract types did not exist:
  `/private/tmp/memory-import-red.log`.
- Concurrent invalidations initially issued two permission requests and left a
  late response failure. The regression failed in
  `/private/tmp/memory-import-revoke-red.log`; coalescing the in-flight request
  passed in `/private/tmp/memory-import-revoke-green.log` and the final gate.
- Invalid empty selection initially contacted authentication before rejection.
  `/private/tmp/memory-import-input-red.log` captures that failing assertion.
  Input/consent validation now precedes server calls and checkpoint changes;
  the same assertion passes in the final workflow test.

## Exact-candidate commands and results

- `/opt/homebrew/bin/python3 tests/run_all.py`: **169 passed, 0 failed**, exit 0.
  `/private/tmp/memory-import-candidate-gate.log`.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: **67 passed, 0 failed**, exit 0.
  `/private/tmp/memory-import-candidate-contract.log`.
- Native runner included in that gate: **15 passed, 0 failed**. Nine Swift
  executables contain 39 named check groups and compile with Swift 6 and
  warnings-as-errors. All seven earlier native contract test names and four
  read-only guard tests remain; four native tests were added. Standalone
  precommit result: `/private/tmp/memory-import-final2-tests.log`.
- Unsigned arm64 target: **BUILD SUCCEEDED**, exit 0. Exact-candidate log:
  `/private/tmp/memory-probe-import-candidate-build.log`; source compilation log:
  `/private/tmp/memory-probe-import-build.log`. No Swift warnings. The earlier
  full build has the normal skipped App Intents metadata warning.
- `file` reports an arm64 Mach-O; `codesign -dv` exits 1 with the expected
  `code object is not signed at all`. `git diff --check` passes.
- Host-authorized `xcrun simctl list runtimes` exits 0 with only
  `== Runtimes ==`: no installed runtimes. Log:
  `/private/tmp/memory-import-simulator-runtimes.log`. A preceding sandbox-only
  attempt failed to connect to CoreSimulator and was not treated as an inventory.

Build command (uses installed SDK only):

```sh
xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj \
  -target SafeMemoryProbe -sdk iphoneos26.5 -arch arm64 -configuration Debug \
  CODE_SIGNING_ALLOWED=NO \
  OBJROOT=/private/tmp/memory-probe-import-build/obj \
  SYMROOT=/private/tmp/memory-probe-import-build/products \
  SHARED_PRECOMPS_DIR=/private/tmp/memory-probe-import-build/precompiled \
  CLANG_MODULE_CACHE_PATH=/private/tmp/memory-probe-import-build/modules build
```

Implementation identities across the evidence-only commit:

| Path | Git object |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `3349c1c4a83bb6a6a3d4d1c67e9d56f96338a103` |
| `connectors/ios/tests` | `b86a7f66c4d1ce0c7d97f3c4adcaabb6acefbbcd` |
| `tests/test_ios_probe.py` | `cf4bf5f5b60cb390efd616bd2e7a0b387dce5e7b` |

Temporary logs can expire with host cleanup. Tests use synthetic rows,
in-memory services, fixture-only temporary files and catch-all URLProtocol;
they never access Photos, Keychain or the real service.

## Integration and remaining acceptance

Root owns integration with the frozen Python begin/append/finish API and shared
evidence/release documents. Current main was deliberately not merged here.
The integrated revision must rerun gates and build before delivery. No endpoint
reachability, TLS/Cloudflare operation, pairing-to-ingest round trip, PhotoKit
permission lifecycle, iOS filesystem protection, UI layout or physical-device
acceptance is asserted by these host tests. No simulator runtime was installed.

The selected sample is not full-library coverage or a backfill cursor. Offline,
terminated or background apps cannot promise immediate server revocation; UI
states this and offers explicit retry/web restriction. Source policy remains
server-enforced. Maximum retained local checkpoints: 64 jobs / 64 MiB; old jobs
are retained. Storage exhaustion refuses a new job rather than deleting evidence.

Only metadata is transferred by this implementation. Optimized media export is
still a separate local API with separate consent; there is no media upload UI or
device playback proof. Future media delivery must preserve accepted asset-ID
mapping (available by replaying the frozen append) and recheck the full current
revision and source policy before sending any component.
