---
title: "Progressive Native Preparation"
project: memory
type: task
status: active
created: 2026-10-02
source: codex-desktop
---

# Owned native checkpoint

Owner: connector_probe, `/private/tmp/memory-v1-probe`, branch
`codex/memory-v1-1-probe`. Current completed handoff is
`5bf3022eb89aa55369cf61ef6b491f52c22104f3` (code `4526aeb`): gate171/0,
contract67/0, native17/0 and unsigned build0. Root owns integration and shared
PROGRESS/MindBase documents; only connectors/ios and native-specific tests may
be edited here. No push, main merge, physical source access or real HTTP tests.

Authorized next slice: full/limited explicit progressive metadata scan, descending
recent/backfill pages <=100, bounded durable journal and replay, persistent
revocation, optional separately consented optimized copies per accepted page.
The frozen contract is `/private/tmp/memory-v1-progressive/docs/runtime/PROGRESSIVE.md`.
Checkpoint max2000 characters, expected_count0 valid, Source consent must match
owner flags, media_ready is Source-wide/nonnegative. Parent approved the design
concerns and directed implementation.

Design: retain a public PhotoKit persistent change token plus streaming ordered
ID/count fingerprint; expired/unverifiable token or changed snapshot requires a
fresh explicit scan. Limited token behavior remains device-unverified. Keep only
current raw page; compact prior receipts keep IDs, mappings, source revisions,
payload digest and media checkpoints. Do not buffer the whole raw library.
Reuse MediaCoordinator through a confirmed-page adapter, never equating a page
receipt with whole-index completion. Media capacity/unavailable failures must
leave metadata scanning able to continue, with explicit later copy retry.
Finite journals/staging retain prior files; no automatic deletion.

Implemented: ScanModels/Coordinator/Transport/Journal/PhotosReader/
PageCopies, shared sample/scan UI busy/pause/cancellation, three fixed scan routes,
compact page records and source snapshot checks. Initial missing-types RED is
`/private/tmp/memory-scan-red.log`; core replay/phase/zero/media-capacity/revocation
fixture and private journal fixture passed. Actual page adapter reused the
optimized uploader while the global scan stayed indexing; altered compact page
digest revoked before copy retry. SDK token reader and new UI both compiled
unsigned successfully (`/private/tmp/memory-probe-scan-ui-build.log`).

One ordering regression reproduced RED: known date after unknown was accepted
by page construction. Added descending/unknown-last checks before transmission,
including state carried between pages. GREEN is recorded in `/private/tmp/memory-scan-order-green.log`. The full native
suite passed 19/0, including scan transport and private journal fixtures. Final
candidate gate/build results are recorded in PROGRESSIVE-VERIFICATION.md.
Current limits are512MiB journal,64scan jobs,20000pages/scan,1000000reported items,
current raw page<=1MiB; no raw prior library retention or automatic file deletion.
Sample mode and every earlier named test remain. This is engineering preparation;
no signed distribution or physical-device acceptance is claimed.
