---
title: "Owner Requested Originals Protocol"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Private original resource requests

This shared bounded protocol is frozen for implementation; it is not a delivery receipt. An owner explicitly requests the current asset revision. It records waiting_for_device immediately; it never claims the phone is online. Optimized copies and their readiness are separate. No original is downloaded just because a library scan ran.

Native registration is a frozen manifest of exact original PhotoKit resource bytes, never a transcode. Resource type, original filename and public uniform type identifier retain provenance; response downloads are application/octet-stream attachments with safe encoded filenames, no inline rendering. The backend validates manifest shape, bounds, hashes and current revision authority, not decoder support for every HEIC/RAW/MOV format. Unknown resource semantics refuse rather than label a derivative original.

## Routes, exact JSON fields

All owner routes require session; POST requires same Origin and CSRF. Native routes require exact configured HTTPS origin plus paired device Bearer. Every device operation rechecks current Source authority and asset revision, including retries and every chunk.

- Owner `GET /api/photos/{asset_id}/originals`: returns `{request:null}` or current revision's request with request_id, asset_id, revision, state, error_code, and resource descriptors. No older or unauthorized revision is disclosed.
- Owner `POST /api/photos/{asset_id}/originals`: `{request_key}`. Creates or returns the single retained request for this owner/asset/revision, initially waiting_for_device. Exact key retries are idempotent; a changed key payload conflicts. A new key cannot silently create duplicate original downloads for that revision.
- Owner `POST /api/originals/{request_id}/retry`: `{request_key}`. Failed requests return to waiting_for_device while retaining manifest/chunks. Ready stays ready. It never renews revoked authority.
- Native `POST /api/device/originals/pending`: `{device_id}`. Returns `{requests:[…]}` with at most20 waiting/transferring requests for the paired Source and currently authorized asset revisions. Each includes request_id, asset_id, native_id, source_revision, media_type, state. Failed/ready/stale/restricted requests are not pending.
- Native `POST /api/device/originals/begin`: `{device_id,request_id,resources}`. Array1–8, each exactly `{resource_type,original_filename,uniform_type_identifier,size,sha256}`. Index in the array is the stable ordinal. Frozen manifest equality makes lost-ACK replay idempotent; changed manifest conflicts. Returns `{request_id,state,resources:[{ordinal,upload_id,next_offset,state}]}`, with the same count/order as the frozen manifest. Resource state is active or complete; parent state is transferring or ready. Size/hash are not repeated in this receipt. A failed parent requires owner retry first.
- Native `POST /api/device/originals/chunk`: `{device_id,upload_id,offset,data}`. data is canonical base64, decoded1–4MiB. Contiguous offset, exact-byte replay, private atomic filesystem publish and transactional receipt. Returns `{upload_id,next_offset,state}`; state is the upload state active or complete.
- Native `POST /api/device/originals/complete`: `{device_id,upload_id}`. Verifies complete size/hash and publishes immutable original component; parent is ready only when all registered components are complete. Returns request_id,upload_id,component_id,state (parent ready or transferring). Replays reauthorize first.
- Native `POST /api/device/originals/fail`: `{device_id,request_id,reason}`. Reasons: source_unavailable, permission_changed, revision_changed, icloud_unavailable, capacity, unsupported_resource. Retains all prior bytes/checkpoints and records failed; current authorization must still permit the request. Network outage itself leaves the last committed state intact, not a fabricated server-side failure.
- Owner `GET|HEAD /api/originals/components/{component_id}`: only ready, current-authorized original. Authenticated Range/no-store/nosniff/CORP and per-stream-chunk reauthorization reuse private transport rules. Content-Disposition attachment only. Revocation, logout and revision changes immediately deny. No URL token is authority.

## Manifest and capacity

Frozen resource_type vocabulary: photo, video, paired_video, alternate_photo, audio. Photo requires exactly one photo plus optional alternate_photo resources; video exactly one video; Live exactly one photo plus one paired_video, with optional alternate_photo. Every explicitly exposed ancillary audio resource is also included for any of these media types. The native implementation must verify public PhotoKit semantics and reject an ambiguous/missing required resource. Deterministic ordering and exact original bytes are frozen before begin. Current metadata wrapper, permission and resource inventory are verified before/after export and before each send, with pending revocation first.

Resource filenames1–255 characters, no slash/backslash or controls; UTI1–128 ASCII letters/digits/dot/dash; SHA256 lowercase64hex. Total request256MiB maximum, each resource positive, at most8 resources; chunk4MiB. At most256 combined optimized/original upload jobs and4096 retained requests per owner. Combined actual optimized/original retained storage retains the1GiB sample budget and1GiB free-space reserve. No automatic deletion/eviction. Capacity reports failed/waiting honestly and leaves optimized playback unaffected. iCloud retrieval retains the connector's explicit allow-download choice; a server request does not flip it.

Original rows/chunks/components are separate from optimized tables, so they cannot make optimized readiness appear complete. Backup retains all immutable original files; pre-original-schema migration backups tolerate absent tables. Restore revokes sessions/devices and Source scope. Multiple paired devices for the same current Source may resume the exact frozen bytes after revalidation; no secret/device-origin ownership is inferred from a native ID.

No implementation or real PhotoKit/host acceptance is claimed by this contract. The native public-SDK inventory review confirmed original photo/video/pairedVideo/alternatePhoto/audio resources and no public byte size; exact streams must be staged and measured before begin. All resources retain their descriptor inventory in metadata; no Photos access was needed for this contract review.

Backend schema8 and the service are implemented against synthetic opaque bytes; transport, native and actual-format proof remain pending. Download descriptors expose no storage keys. Original reservation also reduces optimized-upload capacity, and vice versa, without changing optimized readiness.
