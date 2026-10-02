---
title: "Optimized export probe verification"
project: memory
type: evidence
status: preparation
created: 2026-10-02
source: codex-desktop
---

# Optimized export preparation: synthetic and compile evidence

Based on probe branch revision `b88cb7be882213f3706c8634543e8b8483f0ff8c`.
This evidence describes local-only preparation, with no release/VERSION change.
No Photos library was opened, no device/simulator app ran, and no personal data
was used. Root integration and its own gates remain separate.

The pure export policy tests were authored before the implementation; their
first compile failed because ExportPolicy.swift did not exist. The completed
contract now exercises selected-ID membership, duplicate/empty/101-ID rejection,
100-ID acceptance, hidden/shared/unknown consent, explicit cloud opt-in,
2048-edge sizing, required Live cover+motion and atomic byte-budget rejection.

`/opt/homebrew/bin/python3 tests/test_ios_probe.py` passed 7/7 Python cases.
These include the existing read-only mutation/private-API/network guards and
three Foundation-only Swift executables with 14 named check groups. The Swift
compiler used `-swift-version 6 -warnings-as-errors`. Callback tests exercise
completion before continuation registration, cancellation before request ID,
resource-budget cancellation, and 200 concurrent completion/cancellation races.
The exporter source guard permits only exact selected-ID fetches and no
permission request. These guards do not replace device non-mutation proof.

`/opt/homebrew/bin/python3 tests/run_all.py`: **160 passed, 0 failed**, exit 0.
Log: `/private/tmp/memory-export-gate.log`.
The standalone contract log is `/private/tmp/memory-export-contract.log`.

The README direct-target command using installed Xcode beta 26.5 SDK compiled
all six native sources, including the new exporter, with `CODE_SIGNING_ALLOWED=NO`.
Result: **BUILD SUCCEEDED**, exit 0. Final build log:
`/private/tmp/memory-probe-export-build.log`.
No Swift concurrency warnings remain. Xcode reports only its normal App Intents
metadata-extraction warning because this target does not use App Intents.
`file` confirms an arm64 Mach-O; `codesign -dv` confirms it is not signed.
There was no platform installation, signing/account action, upload or source mutation.

The old scheme/destination problem does not block direct-target compile. There
is still no usable installed iOS Simulator runtime, and no physical-device
permission, iCloud download, codec/playback/audio, resource use or UI acceptance
is claimed. The current UI remains metadata-only. See README for precise API
limits and the Photos-managed cache/AVFoundation advisory-byte-limit caveats.

## Source fingerprints

SHA-256 values identify the tested source independently of later evidence or
integration commits. Temporary logs are local evidence and may be removed by
system cleanup.

- `connectors/ios/SafeMemoryProbe/ExportPolicy.swift`: `715615893914343bde897787e88a5bf6e150b6ddb69fc1a9323ed229ea5b75c9`
- `connectors/ios/SafeMemoryProbe/ExportRequestBridge.swift`: `6c64a3f0f38f037482c37a88abf26c4286dda2da247c09088771c59db08bb964`
- `connectors/ios/SafeMemoryProbe/OptimizedMediaExporter.swift`: `cd38e348fc22e91f544b79110c5d837613de20399bddb375e0cf66d92e2ebb4a`
- `connectors/ios/SafeMemoryProbe/PhotosReader.swift`: `79cef0afff0560800a850b7680bbb9292f6640fcbf929ef4eb6f0f84a64343d2`
- `connectors/ios/SafeMemoryProbe/ProbeManifest.swift`: `e7bf900a4c25cf2b178965cae4c58bead689ea18c4c98430bba06615489f2d1d`
- `connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj/project.pbxproj`: `9c7c8a19f8a0922b9d87a0100303c6a8a2b665e1e8384d24b78a0cab3c0f5d2e`
- `connectors/ios/SafeMemoryProbe/SafeMemoryProbeApp.swift`: `6dbd7609e2e00c779fb78c027a8cb00b1bb452a93373a4064100063c1366ccb9`
- `connectors/ios/tests/ExportBridgeTests.swift`: `86d0143c4f04a8c3e750ee2c3b1fbf1351e276117fb212500eb66bead8841269`
- `connectors/ios/tests/ExportPolicyTests.swift`: `1d5f2a693b4b5f59bba3c5b37cd7683b4220c9c2bde35b2b99b9a6fec0f0cd63`
- `connectors/ios/tests/ManifestTests.swift`: `6356ae4b54639e2c88c1faf972bd5ef130a213e680d99f36a741bcea7cadd1eb`
- `tests/test_ios_probe.py`: `e05ef627b39a28c22b4961a1ae75926a06429830dbeffe173d056b315e89bbf8`
