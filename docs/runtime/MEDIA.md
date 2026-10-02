---
title: "Private Optimized Media Contract"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Private optimized media

This component extends selected metadata ingestion with private JPEG and H.264 MP4 copies. No source writes, public URLs or image-optimizer proxy exist. Physical iPhone export, whole-library media coverage and owner-requested originals remain separately unverified or unimplemented; this contract does not claim them.

## Native transfer

Every POST uses the confirmed device's Bearer credential. Its bound owner, Source, current permission/selection, Hidden/shared policy and exact current source revision are checked in the committing transaction, including retries.

- `/api/device/media/begin`: `device_id`, `asset_id` (from the metadata receipt), `source_revision`, `role`, `mime`, `size`, lowercase `sha256`, stable `request_key`. Returns `upload_id`, `next_offset`, `state`. A changed descriptor under the same request key conflicts.
- `/api/device/media/chunk`: `device_id`, `upload_id`, byte `offset`, strict `data_base64`. At most4 MiB decoded /6 MiB JSON, total15-second request-body deadline. Returns `upload_id`, `next_offset`. Offsets are sequential; identical retries return their retained checkpoint. Differing bytes at the same offset conflict.
- `/api/device/media/complete`: `device_id`, `upload_id`. Verifies all chunks, exact declared length/digest and bounded container structure before atomically publishing `component_id`, `state:"ready"`, `size`, `mime`. Current asset/revision/role has one immutable component; a different digest conflicts. One ready component does not imply a whole Live Photo is ready.

Photo requires `still`/`image/jpeg`; video requires `video`/`video/mp4`; Live requires both `still`/`image/jpeg` and `motion`/`video/mp4`. MP4 audio bytes are retained unmodified. The server does not synthesize missing motion/audio. Native export remains responsible for its documented JPEG/H.264/AAC compatibility and source provenance.

## Bounds, integrity and retained state

Initial limits are64 MiB per optimized component,1 GiB actual retained media and two-times-size reservation for chunk plus completed copy,256 retained upload jobs,1024 chunks per job and at least1 GiB free host space before writes. These are sample budgets, not whole-library capacity claims. Overflow returns an explicit failure; no silent deletion/eviction occurs. A retry after interrupted file writing creates a new private staged file; partial staging remains counted against disk budget. Publish uses file fsync, atomic rename and parent-directory fsync. DB checkpoint follows publication, so a crash before DB commit can reuse the verified immutable file.

Server-generated opaque storage keys remain inside the0700 private runtime root with0600 files. Parent/file symlinks and user paths are refused. Per-component length and SHA256 are checked again on reads; JPEG segment/dimension and MP4 box/H.264 configuration checks reject malformed containers. These bounded structural checks are not a full decoder or a claim that arbitrary producer formats play. Browser/device decode and playback proofs are recorded separately. SVG/HTML and unapproved content types are not accepted.

## Browser disclosure

`GET /api/photos/{asset_id}/media` returns `asset_id`, `state` (`not_transferred`, `partial`, `ready`) and components with only `component_id`, `role`, `mime`, `size`. The browser constructs `/api/media/{component_id}`; no filesystem path is returned. Metadata listing, Source counts and Overview calculate readiness from the current revision, after policy filtering.

`GET` and `HEAD /api/media/{component_id}` require the owner session, not a device bearer. Single `Range: bytes=start-end`, open-ended and suffix ranges are supported; malformed/multipart/unsatisfiable ranges are refused. Responses are no-store, nosniff and same-origin resource policy, with exact MIME/length/range. Files stream in chunks of at most4 MiB; each later chunk checks current authorization and commits an audit before disclosure. A restriction during streaming terminates the response before the next chunk. A30-second send deadline bounds stalled clients. Already delivered pixels cannot be retroactively removed from a client; the UI clears failed/restricted media when revalidation detects a change.

## Backup and restore

Schema4 adds uploads, immutable chunks/components and a current-revision readiness view. Migration remains audited and transactional. The SQLite snapshot determines the exact retained file manifest; only referenced immutable files are copied, with verified sizes/digests. A failed copy leaves an incomplete new backup, without overwriting the live store. Restore matches manifest entries to the snapshot, validates every file in a new quarantined root, then revokes sessions/devices, restricts Sources and interrupts active transfers before opening access. Uncommitted orphan staging remains in the original root and is not represented as successfully imported data.

Synthetic fixtures are a96×64 purple JPEG and a one-second96×64 H.264/AAC tone video generated with the host's existing FFmpeg solely for testing. FFmpeg/ffprobe are not runtime imports or production server dependencies. No personal photo or video is sent to a model.
