---
title: "Native Original Resource Verification"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Owner-requested exact original preparation

Implementation: `58044ff8e885c17d0b5fda5b40e86c536b474368`.
Final tested candidate: `43898717bf5f1e6d0fd5f040e7e0be3036410a72`, which clarifies
that a failed local attempt does not prove the server received its failure report.
This evidence-only commit follows; implementation objects below are unchanged.
The integrator must recheck the combined runtime/frontend/native revision.
No push, merge, physical Photos read, real endpoint request, signing, installation
or release acceptance occurred in this owned native checkout.

## Criterion-to-proof mapping

| Criterion | Committed synthetic proof |
| --- | --- |
| Faithful resource selection without rendered substitutes | `OriginalPolicyTests.swift`: original photo/video/Live roles, alternate photo/RAW and audio, deterministic order, missing/ambiguous/proxy/unknown refusal |
| Bounded exact manifest and safe source descriptors | same harness: filenames/Unicode category/UTI validation, total-size and resource-count bounds |
| Original requests cannot grant themselves local source scope | `ScanWorkflowTests.swift`: accepted scan/sample mapping, native/server ID match and full current revision; rejected forged mapping or changed metadata |
| Interrupted transfer/restart replays exact retained bytes | `OriginalWorkflowTests.swift`: actual private files reopened after lost chunk and completion acknowledgements, unchanged hash/manifest, no re-export |
| Live completion needs all original components | same harness: independent still/motion completion, missing motion failed before any chunk, parent-ready acknowledgement required |
| Changed source/permission blocks retry before further chunks | same harness: durable pending revocation while offline, explicit retry blocked, then revoked after security operation succeeds |
| iCloud choice cannot silently change | same harness: disabled cloud failure, owner retry required by pending state, new explicit consent creates a fresh unstaged job while retaining prior attempt |
| Advanced immutable server offsets are recoverable | same harness: exact manifest already advanced by an authorized peer, bounded begin offsets and repeated completion |
| Storage/server capacity preserves honest failure | same harness: server capacity records failed/capacity while retaining staged manifest; private budget and symlink checks preserve external sentinel |
| Exact HTTPS/Bearer and bounded request/response | `PairingTransportTests.swift`: original `data` field, 1 MiB decoded chunk, 2 MiB request cap, redirect rejection, inherited cookie/header/origin/response guards |
| Public SDK compatibility and source immutability | direct unsigned iOS target build plus all previous mutation/private lookup/network guards; targeted original exporter has no enumeration, permission request or transcode |

RED/GREEN history:

- Initial missing original policy type: `/private/tmp/memory-original-policy-red.log`,
  exit 1; implemented policy passed `/private/tmp/memory-original-policy-green.log`.
- Advanced server offsets initially returned invalidReceipt:
  `/private/tmp/memory-original-peer-red.log`, exit 1. A newly bound upload now
  accepts a bounded offset only after validating the identical frozen manifest;
  known local uploads still replay their saved chunk. GREEN:
  `/private/tmp/memory-original-peer-green.log`, exit 0.
- Server507 initially escaped as a transport error without recording the intended
  original failure state: `/private/tmp/memory-original-capacity-red.log`, exit 1.
  GREEN `/private/tmp/memory-original-capacity-green.log`, exit 0, verifies retained
  manifest/files and a bounded capacity failure report.
- Additional scope and owner/cloud retry fixtures passed in
  `/private/tmp/memory-original-scope-tests.log` and
  `/private/tmp/memory-original-cloud-green.log`.

Exact final candidate receipts:

- `/opt/homebrew/bin/python3 tests/run_all.py`: **176 passed, 0 failed**, exit 0.
  `/private/tmp/memory-original-final-gate.log`.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: **67 passed, 0 failed**, exit 0.
  `/private/tmp/memory-original-final-contract.log`.
- Native runner within that gate: **22 passed, 0 failed**; fifteen Swift 6
  executables with warnings-as-errors and **78 named groups**. Every previously
  passing native test name remains. Harnesses use only synthetic records, files
  and services; transport fixtures intercept every request with URLProtocol.
  No Photos or Keychain runtime APIs are executed in the harnesses.
- README direct-target command, installed iOS26.5 SDK, arm64, Debug,
  `CODE_SIGNING_ALLOWED=NO`, external build directories:
  **BUILD SUCCEEDED**, exit 0. `/private/tmp/memory-original-final-build.log`.
  No Swift warnings. Xcode only reports skipped AppIntents metadata extraction
  because this target has no AppIntents dependency.
- `git diff --check`: pass; owned checkout clean before this evidence commit.

The earlier implementation candidate also passed gate176/0, contract67/0 and
unsigned build0, recorded under `/private/tmp/memory-original-candidate-*.log`.
The final string clarification was revalidated at its own exact SHA above.

| Implementation path | Git object unchanged by evidence |
| --- | --- |
| `connectors/ios/SafeMemoryProbe` | `273d39a9f341f74b977cbf8fb17d2b415e9fc238` |
| `connectors/ios/tests` | `5123ad01834597f38bb37de0f8afcc9e959dc9de` |
| `tests/test_ios_probe.py` | `39ca42798bf28c49b6727caf824b0625a1925f51` |

Reviewed public installed SDK interfaces: `PHAssetResource.h`, `PhotosTypes.h`
and `PHAssetResourceManager.h` under the Xcode-beta iPhoneOS26.5 SDK Photos
framework. Original filenames, resource type, public UTI and descriptor dimensions
are available; byte size is measured from the stream, not private KVC. iOS18
continues to use public uniformTypeIdentifier; contentType requires iOS26.

Physical exact-byte fidelity, actual RAW/Live/audio resource availability, iCloud
downloads, changed Photos behavior, UI interactions and large-file/device timing
remain unverified. No Simulator runtime is installed, so no native UI proof is
claimed. Per-request bounds are 256 MiB and 8 resources; native storage is 512 MiB,
64 jobs and 64 resource-file attempts/job with 4 MiB checkpoint reserve. Each
resource request has a cancellable 300-second deadline. No originals are pulled
automatically during indexing, foreground inspection or request-list retrieval.

Temporary logs may expire with host cleanup. Committed fixtures and this receipt
preserve the tested behaviors and practical verification limits.
