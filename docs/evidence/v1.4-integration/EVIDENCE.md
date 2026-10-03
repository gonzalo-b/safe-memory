---
title: "Alpha V1 Through V1.4 Integration Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Integrated local candidate, external acceptance pending

The full goal is not complete. VERSION0.1.0/Unreleased remains. Plan SHA256
ac2046dca5af017e3277376dd4e49351abf7bab367ee1a35e50ad9a05f863820.
The approved stack is Next/React/TypeScript plus Python/SQLite. Original dirty
checkout and personal canon are untouched; work occurs in isolated checkouts.

Product candidate85606c50232f555f305d3da85edd3b1c5ff19f24 passed aggregate373/0,
contract67/0,220 browser cases across desktop/mobile and light/dark,12units,
production build,TypeScript and DS checks. Logs are attached. All76 original
baseline names remain, with only the explicitly approved six-tools→sm_block
mapping; see baseline-preservation.json. Aggregate includes combined recovery
of corrected trip, Gallery, optimized media and original bytes, with restored
sessions/devices/Sources quarantined. No tests were skipped to raise totals.

Actual production Next→Python suites, without HTTP mocks, passed on the same
product code: originals2,knowledge2,progressive2,GalleryJPEG2,Galleryprepare2
then real API restart and Galleryreopen2. Restart replacedPID61587 with68571,
using the SAME retained synthetic root /private/tmp/memory-live-fixture-artifacts.
Final JPEG/video/Live2 used the separately retained synthetic media root,
with current schema8 forward migration, and the same product code. Different
synthetic stores are not claimed to be one physical-device journey.

The first final playback run failed2/2 at0.02322s. HTTP delivered the entire
MP4. Independent dataURL playback outside React/HTTP reproduced3/3 failures;
only disabling the host physical audio sink allowed3/3 playback advancement.
The media-only Playwright launch now uses --disable-audio-output while retaining
unmuted controls, currentTime advancement and actual decoded-audio checks.
The unchanged app then passed2/2. Initial failure and discriminating diagnostics
remain in audio-host-diagnosis and both logs; no acoustic output is certified.

PR15 Gallery delivery7d58289d50f71317eb4e67f1b3cbf88366981143 had exact345/0
and67/0, same-code196UI/11units/build/types/DS, CLEAN/currentbase and successful
local statuses immediately before merge. It merged at2026-10-03T02:52:22Z as
b5fbd5726435b81525bc22e22e9b916cc971729c; full merged tree equals delivery.
Original integration2fc917a7cfb28ea7a74c083f324cbf5f9fd30e13 includes that main,
with product implementation identical to85606c5; only evidence/docs and the
media test launch configuration differ. Exact aggregate/contract are rerun
before focused original-request delivery; later evidence-only commits require
implementation equivalence as allowed by memory-workflow.

Remaining local follow-up: Photos period/place/trip/collection filters required
by F3-01 are being implemented in a separate focused slice. F2 final bounded
capacity measurement is recorded independently;300ms remains an unmet target
where observed. A final41-criterion ledger will include these follow-ups and
their final revision receipts.

External blockers: devicectl currently finds0 devices; no signed/trusted iPhone,
Photos consent or authorized30–100asset sample is available. Production owner
requires private interactive provisioning. Cloudflare dashboard read access
was rejected twice by automatic approval review; explicit account permission
is pending. No route, DNS, production PM2 or external settings were changed.
Prepared deployment instructions are in ../../runtime/DEPLOYMENT.md. Temporary
loopback fixtures are QA, not deployed or real-source acceptance. No V1.5+
publication, email, scheduler, map or remote agent integration is included.

Final bounded F2 run on2fc917a:100k facts,13.108s rebuild,156.64MiBpeak,238.49MiBstore,all six warm query p95≤281.14ms across12samples. Passes the predeclared600ms/30s/256MiB/384MiB local envelope. Earlier300ms misses remain in historical receipts. This run is not a real-device/network/concurrent-import SLA.
