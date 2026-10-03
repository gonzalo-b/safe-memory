---
title: "Private Gallery Backend Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Backend candidate, integration pending

Implementation e5d1994 committed during the full gate; merge27176392fffc36669441a54169addb21bf5f532d then incorporated main0b3caf6 with no implementation changes. All tested implementation files match that merged tree. The later evidence-only commit does not change product code. VERSION0.1.0; no V1.4 release or user acceptance is claimed.

[Aggregate](gate.log)330/0 and [explicit contract](contract.log)67/0 passed on the unchanged implementation. New [Artifact behavior](behavior.log)14/14 and [migration](migration.log)3/3 cover F4 persistence/restart, exact idempotency, stale revision conflict, ordered edits, cover selection, retained exclusions and explicit re-inclusion, deterministic recomposition preserving manual additions, current-policy denial of complete outputs/Debug/retry, filtered lineage, Hidden selection rules, current revision resolution, owner/CSRF isolation, failed-save/audit atomicity and restore quarantine. Stored source revisions compare identical before and after composition.

[Initial missing-module RED](red.log) precedes implementation. The [first implementation run](first-failure.log) failed14/14 because the receipt INSERT had seven placeholders for six columns; corrected before the14/14 rerun. No behavioral assertions were weakened. Temporary roots contain synthetic metadata only.

Commands: `/opt/homebrew/bin/python3 tests/test_artifacts.py`, `tests/test_artifacts_migration.py`, `tests/run_all.py`, `tests/test_stub.py`. [Behavior and service contract](../../runtime/ARTIFACTS.md). Schema7 forward migration stores a verified schema6 backup, rolls back invalid SQL and refuses an incomplete schema. Existing migration assertions now require latest7; their historical input fixtures and prior behavior remain unchanged.

This proof is backend-only. HTTP/UI safe rendering, browser composition/restart/reopen, authorized real media/sample, installed iPhone and deployed private host remain unverified. No fixture replaces those acceptance criteria. Existing optimized-media authorization is reused through current asset references, but Artifact-driven playback still needs the actual UI integration proof.

## Integrated private Gallery UI and restart proof

Integrated backend47691e2 passed345/0 aggregate and67/0 contract on currentmain2ee0e4f. Follow-up a8f4df6 changes only web evidence access: opening one permitted member now first revalidates the complete Gallery, since a different included member may have become restricted. RED→GREEN preserved. Final frontend identical to agentfe6ffa825c016be4ba8df14e0877c73c3e9d2e1d:188/188 browser cases,11/11 units, production build/TypeScript/DS. Canonical logs/screenshots in ui/.

Four new owner HTTP behavior tests cover exact route/body/query fields, session/Origin/CSRF, saved output/recompose, revision conflicts, audit failure and restriction. The pre-existing test_unknown_and_future_routes_require_auth initially expected unimplemented501 for Artifacts. Its name remains; it now asserts implemented owner200/empty, unauthenticated401 and a still-unimplemented route501. This updates the intentional contract without dropping a negative test. The initial combined failure is retained in ui/547947f-gate.log; corrected integrated gate345/0 is attached.

F4-01–05: actual Next→Python prepare2/2 desktop/mobile saved revision3, story layout, cover and one included/one excluded member after recomposition. Root stopped PythonPID48247 and startedPID51095 against the SAME /private/tmp/memory-live-fixture-artifacts. runtime/schema/shell tree was identical to c431b35 throughout; schema8 is a superset of this PR's schema7 and includes the independently developed original service. The actual restart2/2 reopened the same IDs/revisions/title/layout/cover/exclusion and then withdrew Hidden consent, verifying the complete output/evidence became unavailable. Two Sources, two revoked devices and saved Galleries remain retained; no fixture or source rows were deleted. No original API was needed for the Gallery test.

BrowserOS visual inspection opened the persisted story Gallery, cover, exclusion and Debug, then checked denial after restriction and signed out. All member media uses the previously tested private viewer; missing media is labeled metadata-only. These fixtures have no PhotoKit/personal images. The renderer is safe typed React text with grid/story arrangements; it introduces no publication, email, map, Plugin framework or automatic additions.

This closes local synthetic persistence/UI proof, not the authorized real-sample/device/deployed acceptance of F4/Q. Current evidence includes a runtime-schema8 superset; final all-slice acceptance must run against one integrated candidate and the real sample. VERSION remains0.1.0/Unreleased.
