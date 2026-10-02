---
title: "Native Probe Integrated Revalidation"
project: memory
type: doc
status: blocked
created: 2026-10-02
source: codex-desktop
---

# Integrated native probe revalidation

Candidate: `fc6f3c19c10e1920d7a2f49c848994173d02cad4`; base `main` at `60580239ff93b6fa034fd1d459258e30acc05c99`. Native subtree was `7bdf6b043f629e49ac7a5682996f95592210d9cc` before this evidence-only README update.

- Aggregate gate: 150 passed/0 failed, exit 0. Includes source guard (3 checks) plus integrated main (147 checks). Explicit contract 67/0, exit 0. Four synthetic Swift manifest checks pass.
- Earlier sandbox unsigned build succeeded at `71522a1`; its actual log remains preserved. However final host-authorized revalidation failed exit 70: Xcode cannot find an eligible iOS destination. Explicit generic/platform=iOS also fails, reporting iOS 26.5 platform is not installed. SDK headers/compiler presence alone is insufficient to certify a usable Xcode device build environment.
- Simulator inspection exited0 with zero runtimes/devices; CoreDevice inventory exited0 with zero available physical devices. No platform download, signing, install, Photos access or runtime permission test occurred.
- Native UI and current host build readiness remain blocked. Keep PR draft; no native-build/UI/device success status. Resolve Xcode platform availability and then rerun build/UI before device consent.
- Original no-destination and explicit-generic failures preserved below; do not supersede them with historical success. No acceptance criterion is waived.

```text
memory-probe-final-build.log
Command line invocation:
    /Applications/Xcode-beta.app/Contents/Developer/usr/bin/xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj -scheme SafeMemoryProbe -sdk iphoneos -configuration Debug -derivedDataPath /private/tmp/memory-probe-build CODE_SIGNING_ALLOWED=NO build

Build settings from command line:
    CODE_SIGNING_ALLOWED = NO
    SDKROOT = iphoneos26.5

2026-10-02 16:29:19.855 xcodebuild[37611:20941362] [MT] IDERunDestination: Supported platforms for the buildables in the current scheme is empty.
2026-10-02 16:29:19.874 xcodebuild[37611:20941362] Writing error result bundle to /var/folders/w4/l3zk637j5zl0m2__47q75x600000gn/T/ResultBundle_2026-02-10_16-29-0019.xcresult
xcodebuild: error: Found no destinations for the scheme 'SafeMemoryProbe' and action build.

memory-probe-final-generic-build.log
Command line invocation:
    /Applications/Xcode-beta.app/Contents/Developer/usr/bin/xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj -scheme SafeMemoryProbe -sdk iphoneos -destination generic/platform=iOS -configuration Debug -derivedDataPath /private/tmp/memory-probe-build CODE_SIGNING_ALLOWED=NO build

Build settings from command line:
    CODE_SIGNING_ALLOWED = NO
    SDKROOT = iphoneos26.5

2026-10-02 16:30:07.836 xcodebuild[38100:20943107] [MT] IDERunDestination: Supported platforms for the buildables in the current scheme is empty.
2026-10-02 16:30:07.846 xcodebuild[38100:20943107] Writing error result bundle to /var/folders/w4/l3zk637j5zl0m2__47q75x600000gn/T/ResultBundle_2026-02-10_16-30-0007.xcresult
xcodebuild: error: Unable to find a destination matching the provided destination specifier:
		{ generic:1, platform:iOS }

	Ineligible destinations for the "SafeMemoryProbe" scheme:
		{ platform:iOS, id:dvtdevice-DVTiPhonePlaceholder-iphoneos:placeholder, name:Any iOS Device, error:iOS 26.5 is not installed. Please download and install the platform from Xcode > Settings > Components. }

```
