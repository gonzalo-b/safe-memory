---
title: "Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# iOS metadata probe preparation evidence

## Current integrated status

Latest combined candidate: [HANDOFF.md](HANDOFF.md), 153 aggregate / 67 contract /
32 synthetic browser checks passing. G-02 material approval and device acceptance
remain pending; goal is blocked without reducing scope.


Direct target compilation now **passes**, exit 0 at `956ce8e`: see
[TARGET-BUILD.md](TARGET-BUILD.md). Scheme-based destination discovery still
exits 70 and reports iOS 26.5 platform unavailable. No simulator runtime or physical device is
available. See [integrated revalidation](INTEGRATED.md) for both failures,
integrated 150/0 aggregate and 67/0 contract results, and limits.
[PR #7](https://github.com/gonzalo-b/safe-memory/pull/7) is open in draft.
Its code/tests are verified locally; native UI/device and deployment are not. Direct compilation does not resolve
those missing acceptance checks.

The section below is historical evidence at the named earlier revision, retained
verbatim. Its build PASS does not override the current failed revalidation.

## Historical preparation receipt

Date: 2026-10-02. Status: implemented, verified synthetic, unsigned build.
This is P4 preparation only. V1.1 is **not** accepted or released.

Implementation revision: `71522a1351307657a8abe369c841898f254b6152`.
Implementation subtree `connectors/ios`:
`7bdf6b043f629e49ac7a5682996f95592210d9cc`.
Base: `86e71a15bf2bc376b0c517c91797fc9c9bce9189`.
Branch: `codex/memory-v1-1-probe`; isolated checkout:
`/private/tmp/memory-v1-probe`. No original-checkout or strategic-document edits.

## Verified criteria

| Criterion | Evidence | Result |
| --- | --- | --- |
| Native iOS target compiles unsigned for arm64 / iOS 18 minimum | [Build](build.md) | PASS |
| Stable synthetic manifest encode/decode and explicit unknown capture offset | [Manifest](manifest.md) | PASS, four named checks |
| Restricted unknown collection provenance and bounded-sample label | [Manifest](manifest.md) | PASS, synthetic only |
| Source mutation/private lookup/network regression guard | [Guard](read-only.md) | PASS, three named tests |
| Existing aggregate baseline remains passing | [Gate](gate.md) | PASS, 76 checks |
| Existing transport contract remains passing | [Contract](contract.md) | PASS, 59 checks |

All verification above was rerun against the committed implementation revision.
Evidence files are appended separately; the implementation subtree stays fixed.
Named test outputs are retained, not merely the totals.

## Commands

```sh
xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj \
  -scheme SafeMemoryProbe -sdk iphoneos -configuration Debug \
  -derivedDataPath /private/tmp/memory-probe-build CODE_SIGNING_ALLOWED=NO build
python3 tests/run_all.py
python3 tests/test_stub.py
python3 connectors/ios/tests/test_read_only.py
xcrun swiftc -module-cache-path /private/tmp/memory-probe-module-cache \
  connectors/ios/SafeMemoryProbe/ProbeManifest.swift \
  connectors/ios/tests/ManifestTests.swift -o /private/tmp/memory-probe-manifest-tests
/private/tmp/memory-probe-manifest-tests
```

Observed results: build succeeded; all gates/tests passed. The synthetic Swift
test intentionally failed first because `ProbeManifest.swift` did not exist:
`error opening input file .../ProbeManifest.swift (No such file or directory)`.
The implementation then passed. An initial build warning about interface
orientations was fixed by declaring supported iPhone/iPad orientations.

## Tooling and limits

- `xcode-select -p`: `/Applications/Xcode-beta.app/Contents/Developer`.
- `xcodebuild -version`: Xcode 26.5, build 17F5012f; iOS 26.5 SDK.
- Apple frameworks only; no package/tool installation, upload, pairing, account
  login, endpoint, persistence migration, paid service or signing changes.
- The build host emitted CoreSimulator service/XPC diagnostics. They did not
  prevent the unsigned physical-device target compile. No simulator runtime
  success is claimed. An AppIntents metadata warning is expected because this
  probe does not depend on AppIntents.
- Earlier `devicectl list devices` timed out initializing CoreDeviceService.
  This does not establish whether an iPhone is available or connected.
- No app execution, real Photos permission request, real media/metadata read,
  UI QA, install, performance measurement or source before/after check occurred.
- No production runtime/distribution approval, device acceptance, full-library
  coverage, Hidden/shared capability, cloud transfer, stable reconnect identity,
  retry/recovery, media playback or V1.1 acceptance is implied.
- VERSION is unchanged. No push, PR, merge or deployment was performed.

The probe has a separate sample-consent control, uses bounded newest-first
PhotoKit fetches, and serializes metadata/resource descriptors only in memory.
Diagnostics expose counts and fixed status strings. The project README records
source limitations and the concrete owner-assisted installation steps.

Next integration work requires the pending native runtime/auth/schema/host
decisions, then a signed probe on an authorized iPhone. Personal data must never
be added to this evidence directory.

Follow-up: [Simulator UI QA prerequisite](SIMULATOR-QA.md) records a successful
read-only inspection showing no installed Simulator runtime/devices. Native UI
QA could not run; no runtime was downloaded or installed.
