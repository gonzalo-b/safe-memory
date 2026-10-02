---
title: "Private Artifact Contract"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Persistent private Galleries

The V1.4 compositor saves a private Gallery from an explicit authorized asset selection or a currently authorized trip snapshot. It needs no agent, plugin runtime or source write. It stores references, safe text and allowlisted grid/story layout settings, never arbitrary HTML, public URLs or copied private bytes. The web renderer must use React text nodes and the existing authenticated media viewer. No publication, email, map, scheduling or automatic sync additions are included.

Schema7 adds owner-owned stable Artifact identities, immutable composition revisions, ordered included/excluded membership and immutable idempotency receipts. Owner mutation, optimistic expected_revision, operation record and audit commit are atomic. Failed audit/save leaves the last revision coherent. Migration backs up schema6 first, preserves prior rows and validates foreign keys. Normal backup includes all Artifact revisions; restore revokes sessions/devices and restricts Sources before exposing any retained content.

## Service surface for the HTTP/UI adapter

All calls use an owner session. Mutations require the same session's CSRF token; the adapter must check same Origin, exact fields and bounded JSON before dispatch. No caller-supplied owner ID is accepted.

- `list(token, limit=50, cursor=None)` returns currently allowed summaries and next_cursor. Limit1–50. Cursor is the previous visible Artifact ID; owner binding and visibility re-evaluate on every page. If it no longer belongs to the visible list the cursor is stale (409). No total or restricted-output count is returned.
- `get(token, artifact_id)` returns ID, revision, title, layout, optional cover, ordered members, currently authorized exclusions and safe lineage.
- `create(token, csrf, request_key, *, title, asset_ids=None, layout='grid', trip_id=None, expected_trip_revision=None)` saves revision1. Selection is either explicit asset_ids or trip_id plus exact current trip revision, never both. Empty manual galleries are valid. Trip selection is all or capacity-refused, never silently truncated. Trip-based composition excludes Hidden even when the Source currently permits it. Explicit manual selection may include Hidden only under current Source consent.
- `edit(token, csrf, request_key, artifact_id, expected_revision, patch)` accepts only title, layout, cover_asset_id, add_ids, remove_ids and order. Order contains every active ID exactly once. Removing writes durable exclusion intent. Explicit addition can clear that current exclusion; historical revisions remain. The cover must belong to active membership; removing its asset chooses the next member.
- `recompose(token, csrf, request_key, artifact_id, expected_revision, *, asset_ids=None, trip_id=None, expected_trip_revision=None)` performs an actual local composition and records a new coherent revision/operation. With no selection it rerenders the retained membership. An explicit new selection adds candidates while preserving all existing members/manual additions and all exclusions. It never silently removes prior members or re-adds exclusions. Automatically proposed Hidden candidates are omitted; explicit re-inclusion uses edit.
- `debug(token, artifact_id)` gives the current revision/definition and20 retained safe operation receipts. Recompose is its only local rerun action; arbitrary shell/SQL/HTML is unsupported.

Create/edit/recompose return `{artifact_id, revision, operation_id}`. Same owner request_key plus byte-equivalent canonical request replays the receipt without another save; changed request conflicts. A replay rechecks the Artifact's current authority before returning even its ID. A stale expected_revision conflicts unless it is the exact already-committed request replay. UI must keep the same key across network retry and refresh current state after409.

## Disclosure and evidence

Every included member must remain authorized under current Source permission, scope and category policy. If any is restricted, the complete saved output, its title, list item, Debug and replay receipt are unavailable. Membership is not an access grant. Excluded IDs are retained internally but are only listed if currently authorized. Empty owner-authored Galleries carry no source dependency.

Members resolve stable asset ID to the current authorized revision at read time, with selected_revision retained as provenance. Current media availability is reported independently; metadata alone does not imply an optimized copy exists. The API carries asset/evidence IDs, never storage keys/raw payloads or public media URLs. Existing media endpoints independently reauthorize each read/stream chunk.

Trip lineage is a snapshot reference, not a live recipe. Its link is disclosed only if the current trip remains authorized, active and at that same trip revision; otherwise it is null. It does not emit historical trip titles/boundaries. A new generation alone cannot widen Artifact membership; the owner must explicitly recompose. The generation identifier is retained for provenance. User-authored title/layout/order remain until edited.

## Bounds and status

At most200 included assets and1000 retained current exclusions per Gallery,200 Galleries per owner and1000 revisions per Gallery. These are honest Alpha bounds; capacity refusal preserves data. Titles1–200 characters, request keys1–200, layout grid/story, exact32hex identifiers. No files are deleted to free capacity. A Gallery with more desired photos can be split into explicit selections. Future unbounded libraries require a measured design, not a claim that these bounds cover all usage.

Backend implementation and synthetic behavioral tests are in progress. HTTP/UI integration, actual restart/browser proof, authorized real sample and deployment are separate pending acceptance gates. VERSION remains0.1.0.
