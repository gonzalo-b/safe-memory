---
title: "Readme"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Safe Memory iOS metadata and local export probe

Engineering preparation only. This is not V1.1, an ingestion connector, an
approved production mobile runtime, or a distribution route. Minimum iOS 18
is a reversible probe choice. The product remains the existing web product.

The single native target uses Apple frameworks and no package dependencies.
It requests Photos authorization, reports the exact authorization category,
and reads at most 50 recent photo/video metadata records after separate sample
consent. A strict maximum of 100 is enforced by the adapter. Hidden items and
Shared Albums are excluded. Resource descriptors include Live Photo component
roles without retrieving media bytes. No Photos mutation API is used.

The current UI serializes its probe manifest only in memory, then releases it.
Only sanitized status and sample count reach the UI; this action stores no media.
The reusable exporter described below is not wired to that UI. Neither path
uploads, shares or imports anything into Safe Memory. There is no pairing,
credential or endpoint configuration. `unpaired-local-probe` is a marker,
not an owner/device/source identity. No release VERSION change is appropriate.

## Important limitations

- `PHAsset.creationDate` is an instant, not an original capture timezone. The
  manifest labels its ISO8601 UTC representation `creationInstant` and records
  an absent capture-offset reason. It does not map this to the Record contract.
- A local asset identifier is meaningful in its local Photos library. Cloud
  mappings, reconnect/reinstall identity and deduplication are not implemented.
- `.typeUserLibrary` does not establish personal versus iCloud Shared Library
  provenance. Every result is marked `collectionProvenance: unknown` and
  `disclosure: restricted_probe_only`. Choose limited permission for an exact
  owner-selected sample. Do not claim whole-library collection consent from it.
- Locked Hidden albums cannot be bulk enumerated merely by setting the hidden
  fetch flag. Inclusion and change detection remain unverified.
- `PHAssetResource` descriptions do not prove availability, component byte
  integrity, cloud downloads, Live motion/audio playback or optimized output.
  The exporter verifies output descriptors locally; device/playback evidence
  remains pending.
- PhotoKit exposes `.readWrite`, not a read-only authorization level. Source
  immutability here is enforced by using only read APIs and a source guard;
  device before/after proof is still required.
- No permission transitions, UI behavior, actual assets, performance, device
  install or non-mutation on a real library have been exercised by this build.
- This deliberately bounded preparation does not capture every field needed by
  the eventual production connector. The material ingestion schema is pending.

## Build and synthetic verification

Run from the repository root; derived output stays outside the checkout:

```sh
xcodebuild -project connectors/ios/SafeMemoryProbe/SafeMemoryProbe.xcodeproj \
  -target SafeMemoryProbe -sdk iphoneos26.5 -arch arm64 -configuration Debug \
  CODE_SIGNING_ALLOWED=NO OBJROOT=/private/tmp/memory-probe-build/obj \
  SYMROOT=/private/tmp/memory-probe-build/products \
  SHARED_PRECOMPS_DIR=/private/tmp/memory-probe-build/precompiled \
  CLANG_MODULE_CACHE_PATH=/private/tmp/memory-probe-build/modules build
python3 tests/test_ios_probe.py
```

The test runner compiles three Swift executables with synthetic data and
Foundation only, including strict Swift 6 concurrency checks. Installed Xcode
tools are required; missing tools fail explicitly. It never loads Photos or
requests permission. The Python guard rejects known Photos mutation,
private lookup and network entrypoints; it is a regression guard, not a proof
against arbitrary obfuscation. Product aggregate/contract gates also apply.

## Reusable local optimized exporter

`OptimizedMediaExporter.shared.export(selectedIDs:manifest:consent:)` is a
local-only, asynchronous API. It accepts 1–100 unique IDs already present in a
private manifest of at most 100 assets. Only those IDs are refetched. It never
enumerates additional assets, requests broader permission or mutates Photos.
The caller must separately record explicit consent for precisely that selection.
The existing screen has neither retained selection nor export consent, so no
export action is exposed there yet.

Hidden, Shared Album and possible Shared Library inclusion each default to false.
Unknown collection provenance is rejected unless the caller explicitly opts in
to possible Shared Library inclusion; it remains unknown, never relabelled
personal. Existing probe manifests always have unknown provenance. Full/limited
permission must match the manifest, and source type, hidden status, media type
and modification instant are checked again before and after export. Missing or
limited-out IDs are `unavailable`, never proof of deletion. A locked Hidden
album can still be inaccessible despite explicit consent.

Photo output is current-rendered JPEG, quality 0.85, with longest edge at most
2048 pixels and no upscaling. Video uses Apple's 1920×1080 export preset for
H.264/AAC MP4, preserves the current audio mix and verifies the returned video
codec, duration and presence of audio when the source has audio. Videos over
300 seconds are rejected before requesting media and checked again after load.
Live Photos require both a JPEG `cover` and MP4 `motion` component; audio remains
in the motion component. Edited Live Photos require a full-size paired motion
resource. Missing/incompatible motion never becomes a ready still-only Live
Photo. These separate components are not a reimportable Photos Live Photo pair.

iCloud downloading requires `allowICloud: true`; false is the default for every
Photos request. Cloud-only requests can return `cloudRequired`, and unknown
availability stays `unavailable`. Download errors with opt-in are not presented
as successful local availability. PhotoKit manages its own media cache and may
download originals to produce optimized output; this API cannot enforce a hard
network-byte or system-cache limit.

One job runs at a time, assets run sequentially, and each asset has a 90-second
cancellation deadline. Callback bridges handle synchronous completion and late
request IDs. Framework cancellation completion is cooperative, not a hard wall
clock guarantee. Limits are 64 MiB per returned component, 512 MiB retained app
staging, and 64 retained jobs. Live motion input is streamed with a strict byte
budget. AVFoundation's `fileLengthLimit` is advisory and can overshoot while
writing; the final output must pass the strict size check before it is ready.
No hard bound is claimed for Apple's transient codec memory or Photos cache.

Files use opaque UUID names under app Application Support/SafeMemoryProbe/Exports,
private directory/file permissions, complete device file protection and backup
exclusion. Failed and partial files remain private, count against the budget,
and are not returned as ready components; no automatic deletion policy is added.
Staging refuses symlinks in its app-owned path. Returned descriptors include
role, format, dimensions, duration, audio presence, byte count and SHA-256.
The manifest and descriptors are private and must not be logged. Future ingest
must revalidate consent/permission before sending retained files; this result
does not grant continuing permission or establish a server schema.

Results distinguish `ready`, `restricted`, `unavailable`, `cloudRequired`,
`unsupported`, `limitExceeded`, `cancelled`, `timedOut` and `failed`. Invalid
selection or a concurrent job is rejected before media reads. No export,
playback, audio fidelity, privacy transition or Photos immutability acceptance
on a physical device or simulator is claimed by compile/synthetic tests.

## Human device step, once authorized

1. Open `SafeMemoryProbe/SafeMemoryProbe.xcodeproj` in Xcode and choose the
   existing signing team. The owner handles Apple authentication; no credentials
   belong in chat, source, evidence or logs.
2. Connect/unlock/trust an authorized iPhone. Enable Developer Mode if required.
   Select that device and run the target. An unsigned build cannot be installed.
3. Choose limited Photos access and select only an approved bounded sample.
   Enable sample consent, then read it. Record sanitized permission/count/error
   observations, never raw manifests or personal metadata in repository evidence.
4. Exercise denied/revoked/limited/full permission states with explicit owner
   authorization. Never edit/delete/hide personal source assets to manufacture
   a test. Full permission does not change this probe into a complete import.

Local development signing is not the final iPhone-only distribution solution.
No paid membership or account change is presumed. Signed distribution, server
destination, pairing/auth, ingestion schema and media policy remain decisions
outside this probe.

## Official capability references

- [Read-only PhotoKit model objects](https://developer.apple.com/documentation/photokit/fetching-objects-and-requesting-changes)
- [Hidden asset limitations](https://developer.apple.com/documentation/photos/phasset/ishidden)
- [Local and cloud identifiers](https://developer.apple.com/documentation/photos/phcloudidentifier)
- [Resource network access](https://developer.apple.com/documentation/photos/phassetresourcerequestoptions/isnetworkaccessallowed)
- [Persistent change history](https://developer.apple.com/documentation/photos/phphotolibrary/fetchpersistentchanges(since:))

Reviewed against Xcode 26.5 SDK headers during preparation. Public API existence
does not establish device acceptance.

## Latest host revalidation

The earlier sandbox unsigned build succeeded, but final host-authorized build
failed with exit70: no eligible iOS destination; explicit generic iOS reports
that the iOS26.5 platform is not installed. SDK header/compiler availability
alone does not certify Xcode platform readiness. See
`docs/evidence/v1.1-probe/INTEGRATED.md`. Resolve the platform component and
rerun build/UI first. No platform download or device installation was performed.

### Direct target build recovery

The command in `docs/evidence/v1.1-probe/TARGET-BUILD.md` succeeds with the installed SDK by selecting `-target SafeMemoryProbe -sdk iphoneos26.5 -arch arm64`. Use that command for unsigned compile checks. The scheme/destination failure above remains relevant for run/UI tooling; native UI and device acceptance remain pending. No platform installation is needed merely to compile this target.
