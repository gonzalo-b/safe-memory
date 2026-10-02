---
title: "Readme"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Safe Memory iOS metadata probe

Engineering preparation only. This is not V1.1, an ingestion connector, an
approved production mobile runtime, or a distribution route. Minimum iOS 18
is a reversible probe choice. The product remains the existing web product.

The single native target uses Apple frameworks and no package dependencies.
It requests Photos authorization, reports the exact authorization category,
and reads at most 50 recent photo/video metadata records after separate sample
consent. A strict maximum of 100 is enforced by the adapter. Hidden items and
Shared Albums are excluded. Resource descriptors include Live Photo component
roles without retrieving media bytes. No Photos mutation API is used.

The local probe manifest is serialized only in memory, then released. Only
sanitized status and sample count reach the UI. Nothing is stored, uploaded,
logged, shared or imported into Safe Memory. There is no pairing, credential,
original request or endpoint configuration. `unpaired-local-probe` is a marker,
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
  -scheme SafeMemoryProbe -sdk iphoneos -configuration Debug \
  -derivedDataPath /private/tmp/memory-probe-build CODE_SIGNING_ALLOWED=NO build
python3 connectors/ios/tests/test_read_only.py
xcrun swiftc -module-cache-path /private/tmp/memory-probe-module-cache \
  connectors/ios/SafeMemoryProbe/ProbeManifest.swift \
  connectors/ios/tests/ManifestTests.swift -o /private/tmp/memory-probe-manifest-tests
/private/tmp/memory-probe-manifest-tests
```

The Swift executable uses synthetic data and Foundation only. It never loads
Photos or requests permission. The Python guard rejects known Photos mutation,
private lookup and network entrypoints; it is a regression guard, not a proof
against arbitrary obfuscation. Product aggregate/contract gates also apply.

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
