---
title: "Readme"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Safe Memory iOS selected metadata import and local export probe

Engineering preparation only. This is not accepted V1.1, an approved production
mobile runtime, or a distribution route. Minimum iOS 18
is a reversible probe choice. The product remains the existing web product.

The single native target uses Apple frameworks and no package dependencies.
It requests Photos authorization, reports the exact authorization category,
and can inspect at most 50 recent photo/video metadata records locally after
separate sample consent. Hidden items and Shared Albums are excluded from that
local diagnostic. A different explicit import action selects 1–100 IDs as
described below. Resource descriptors include Live Photo component
roles without retrieving media bytes. No Photos mutation API is used.

The metadata UI serializes its probe manifest only in memory, then releases it.
Only sanitized status and sample count reach its diagnostics; this action stores
no media. The reusable exporter described below is not wired to that UI.
Neither local metadata inspection nor local export uploads Photos. Selected
metadata import has separate selection, consent and retry controls. Pairing is a
separate explicit action described below. `unpaired-local-probe` remains a
metadata-sample marker, not an owner/device/source identity. Pairing does not
silently relabel or send that local diagnostic sample. No release VERSION change is
appropriate.

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
  the eventual production connector. Full-library paging/backfill and media
  delivery are not enabled; the selected-import server contract needs integration
  and actual device verification.

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

The test runner compiles nine Swift executables with synthetic data, Foundation
and CryptoKit, including strict Swift 6 concurrency checks. Installed Xcode tools
are required; missing tools fail explicitly. It never loads Photos, accesses
Keychain or requests permission. All transport fixtures intercept every URL via
URLProtocol; no real endpoint request occurs. The source guard rejects known
Photos mutation and private lookup APIs. Networking APIs are permitted only in
three reviewed request/transport files, where direct Photos adapter types are
forbidden.
The metadata/export files retain their no-network guard. These are regression
guards, not proofs against arbitrary obfuscation. Product aggregate/contract
gates also apply.

## Optional owner-confirmed pairing

This implements the approved technical delta's iOS-to-Memory pairing, with the
server contract in `runtime/pairing.py`. No endpoint availability, deployment,
signed app, device UI or Keychain runtime acceptance is implied by a build.
The only destination is `https://memory.lazyagent.ai`; it cannot be configured
from user input. Pairing uses these two POST requests:

| Endpoint | Request | Accepted response |
| --- | --- | --- |
| `/api/device/claim` | JSON `secret`, `device_name`, `library_id`, `credential`; no Authorization header | `claim_id`, full `fingerprint`, Unix-seconds `expires_at` |
| `/api/device/status` | JSON `device_id`; `Authorization: Bearer <credential>` | matching `device_id`, `owner_id`, `connection_id`, `vault_id`, `data_access: false` |

Once the owner web route is available, create a pairing code there. In the app,
acknowledge the installation/library alias, enter the code and explicitly press
Connect. The app generates a Memory-only 256-bit random credential using Apple's
secure random generator, encodes canonical unpadded base64url (43 characters),
and saves it in Keychain **before** the claim request. This is not an Apple
password or an owner web-session credential. The pairing code stays transient
in memory, is cleared from the input on submission/backgrounding, and is never
persisted or logged. Memory zeroization is not claimed for Swift strings.

The app shows the complete lowercase SHA-256 of the canonical credential's UTF-8
bytes. The returned fingerprint must match that locally computed value. Compare
all 64 characters with the pending device in the authenticated web account and
confirm there. A claim receipt is not a confirmed device; only the explicit
Check status button requests binding verification. Before confirmation, 401 is
an honest unconfirmed/unavailable authorization state. The claim ID is treated
as device ID only when the authenticated binding returns that exact ID and
`data_access: false`. The owner ID is response information, never caller-supplied
identity. A newly paired Source starts restricted/awaiting_ingest. No Photos payload,
manifest, media bytes or local source identifier reaches these endpoints.

Opening pairing or reloading its local state sends no request and creates no key.
There is no GET/preview handler, deep-link claiming, automatic confirmation,
background polling or application retry loop. A failed claim can be retried by
explicitly entering the **same** still-pending code; the durable device label,
alias and credential remain unchanged. If confirmation/expiry occurred before
the app retained a claim receipt, explicit recovery/relink is needed and is not
implemented. Credentials are never silently rotated to resolve ambiguity.

Keychain uses WhenUnlockedThisDeviceOnly, synchronization disabled, and a
noninteractive authentication context. Only a nonsecret installation UUID goes
in app preferences. If that sandbox marker and Keychain disagree (including a
key surviving reinstall), the app refuses to reuse or overwrite the identity.
Installation and library aliases are durable random local labels, not verified
Apple library IDs. A changed or previously connected but unrecognized library
needs an explicit new/relink flow before future ingestion; no filename heuristic
or automatic duplicate-library claim is implemented. These constraints still
need physical-device validation.

Every request has an isolated ephemeral session, no cookie jar, credential
storage or cache, exact origin/path/body/header validation, and normal system
TLS certificate verification. Redirects and client/password authentication
challenges are rejected, even to the same host. Bodies are bounded to 8 KiB,
including streamed responses with no Content-Length. Request/resource timeouts
are 15/20 seconds and task cancellation is supported. Errors displayed in the
UI are fixed sanitized messages; raw responses and native error descriptions
are never logged. Pairing cannot call the metadata reader or exporter.

## Explicit selected metadata import

This uses the frozen `runtime/ingestion.py` and `shell/app.py` contract reviewed
in the integrator checkout. Root still integrates that server and this branch;
no endpoint or device acceptance is claimed here. Media export remains local
and separate until its delivery API is integrated.

The Apple PhotosPicker chooses 1–100 item IDs. The app never calls
`loadTransferable` and never downloads the selected media. Import fetches only
those exact IDs under current full/limited PhotoKit permission. A picker item
without a local identifier, an unavailable selected ID or a limited-out asset
is refused, not guessed or silently replaced. Picker selection does not expand
the app's PhotoKit permission. The original recent-50 local diagnostic stays
independent and is never used as an implicit import selection.

The import consent names dates, available locations, filenames and resource
descriptions. Hidden remains opt-in. This adapter cannot establish personal vs
shared provenance, so **both** possible Shared Library and Shared Albums must
be explicitly allowed on the native side. Both owner-controlled server Source
flags must also allow unknown provenance; native consent never changes those
flags. Server exclusions are reported as exclusions, not accepted or complete
media. `collection` and `owner_presence` remain `unknown`.

PHAsset Date becomes `capture_time` with `time_basis: instant_only`. Missing date
is JSON null with `unknown` time basis. UTC serialization does not invent an
original offset/local capture day. `source_revision` is SHA-256 of the sorted,
ASCII-escaped canonical **full wrapper excluding source_revision**, including
metadata, Hidden/collection, source modification and missing-value reasons.
Unchanged wrappers produce the same revision; edits/restrictions change it even
when modification time is absent or unchanged. Resources have deterministic
descriptor order. The local probe metadata format is preserved as raw metadata;
its diagnostic disclosure marker is not interpreted as a server Grant.

Every new explicit sample first clears previous server scope with authenticated
`POST /api/device/permission`, including when full permission stays full. It
then performs `/api/device/ingest/begin` → `/append` → `/finish` with the existing
Keychain credential. Begin uses `phase: recent`; rows are newest-known-instant
first, unknown dates last. Coverage is always `bounded_authorized_sample`.
There is one bounded sequence-zero batch, not a whole-library cursor. Accepted
IDs/counts, exclusions, run identity, sequence and final `media_ready: 0` must
match before completion is displayed.

A private checkpoint freezes payload, consent, device/library binding, request
key and batch key before the first ingest request. Explicit Resume revalidates
the same selection and replays the identical batch to obtain its original
receipt, even if begin already reports sequence one. Lost begin/append/finish
responses therefore do not require a fresh key or duplicate import. The saved
sample count and its retained consent are shown separately from a new picker
selection. Credentials and pairing secrets are never in these files.

Checkpoint files live only under app Application Support/SafeMemoryProbe/
MetadataImport, with UUID filenames, private modes, complete iOS file protection
and backup exclusion. Atomic replacement synchronizes the file and containing
directory before a request can continue. Payload is written before the current
job pointer; older jobs are retained. Limits: 64 retained jobs, 64 MiB retained
checkpoint storage, 1 MiB append request (below the server's 2 MiB cap), 64 KiB
other metadata requests and 256 KiB responses. Corrupt wrappers, symlinks and
identity mismatches fail closed. Storage exhaustion requires a later explicit
retention decision; nothing is automatically deleted.

Selection/consent changes, app activation and PhotoKit change notifications
recheck the saved selected scope. Permission, membership or wrapper changes
persist `revocationPending` first and call the permission endpoint to clear old
server scope. Concurrent callbacks share one in-flight revocation. Late import
responses cannot replace pending/revoked state. No automatic re-import occurs.
Security-only revocation retries can run when the app reopens; they send no
source payload. While offline or suspended the server cannot learn changes
immediately: the UI says restriction is pending and blocks further import until
acknowledged. The owner can separately restrict the Source in Memory web.

Synthetic state-machine/file/URLProtocol tests and unsigned compilation do not
verify physical Photos permission transitions, UI behavior, filesystem durability
on iPhone, remote endpoint integration or real import/non-mutation. Those remain
explicit device/end-to-end acceptance work.

## Reusable local optimized exporter

`OptimizedMediaExporter.shared.export(selectedIDs:manifest:consent:)` is a
local-only, asynchronous API. It accepts 1–100 unique IDs already present in a
private manifest of at most 100 assets. Only those IDs are refetched. It never
enumerates additional assets, requests broader permission or mutates Photos.
The caller must separately record explicit consent for precisely that selection.
Metadata selection does not authorize media export. A separate explicit media
consent and delivery checkpoint are still required before exposing that action.

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
No paid membership or account change is presumed. Signed distribution and
physical-device acceptance remain outside this probe. The approved pairing
destination/contract is implemented in code only; deployment and end-to-end
verification remain separate. Selected metadata import is implemented for
explicit bounded testing; media delivery and real ingest acceptance remain
pending.

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
