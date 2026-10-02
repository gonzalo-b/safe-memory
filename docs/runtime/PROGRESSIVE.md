---
title: "Progressive Photos Scan Contract"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Progressive authorized Photos scans

This additive contract extends, and does not relabel, bounded selected samples. A new explicit native action authorizes enumerating all assets currently exposed by the device's full or limited PhotoKit permission, with independent category consent. Full PhotoKit permission alone is not this action. Limited always means the OS-selected subset, never the whole personal library. Source writes remain prohibited. This draft contract is being implemented and is not a delivery receipt.

## Native API

Existing exact HTTPS origin and device Bearer apply. All fields are required unless stated otherwise; extra fields are rejected.

- `POST /api/device/scan/begin`: `device_id`, stable `request_key`, `permission` (`full` or `limited`), `expected_count` (integer0–1000000, from the frozen authorized fetch result), `include_hidden`, `include_shared_library`, `include_shared_albums` (booleans). Consent flags must match the owner's current Source flags; this request cannot change server policy. Returns `run_id`, `next_sequence`, `state`, `coverage` (`authorized_full_scan` or `authorized_limited_scan`), `recent_after` (UTC timestamp string), `observed`, `expected_count` and `checkpoint` (null initially). The server fixes `recent_after` to90 days before its start. Same-key retry retains that boundary and scope. No sampling claim becomes full coverage merely from a permission string.
- `POST /api/device/scan/append`: `device_id`, `run_id`, stable `batch_key`, integer `sequence`, opaque `checkpoint` (max2000characters), `phase` (`recent` or `backfill`), and1–100 unchanged metadata `assets`. Payload cap2MiB. Assets must be ordered by capture instant descending, unknown-date assets last; equal timestamps permit either ID order. Recent has known instants >=recent_after; backfill has older or unknown instants. Phase cannot return to recent. Each native ID occurs once in the frozen scan, including excluded observations. The receipt retains the usual accepted/excluded counts and native_id→asset_id mapping plus `observed`, `expected_count`, `phase`. Identical batch retries do not add counts; changed retries conflict. Every batch checks current policy and scope before a receipt can be returned.
- `POST /api/device/scan/finish`: `device_id`, `run_id`. Completes only when unique observed IDs equal expected_count;0 is valid. It then restricts previously imported IDs absent from this completed authorized enumeration. Returns `run_id`, `state:"complete"`, the exact scan `coverage`, `observed`, `expected_count` and current-policy `media_ready` (Source-wide, nonnegative; not necessarily equal to this scan's newly uploaded copies). Completion proves only this reported, frozen enumeration, not ongoing source synchronization.

Before initial scan or after any permission/selection callback, use existing permission reporting, which immediately clears prior scope and invalidates old runs. All local in-flight operations cancel on change; durable pending revocation is sent before resuming other work. A changed fetch result/order needs a new explicit scan rather than reusing the old count or checkpoint. Source restrictions discovered during sync apply immediately; unknown absence is only reconciled at complete enumeration. Metadata becomes useful per committed page; index completion never implies media completion.

Keep a private bounded journal: stable run and batch keys and the current page are durable before transmission. Retain accepted mappings and media checkpoints without buffering the entire raw library. Resume must validate the source snapshot, permission, consents and frozen metadata. Exports and chunk sends recheck revisions using the existing verified uploader. Optimized copies and iCloud downloads require explicit choices; original copies are not part of this scan. Unknown native collection provenance remains unknown and requires both shared category opt-ins under the existing conservative policy.

## Owner progress and retry

`GET /api/ingestion/progress` is owner-session-only and returns at most50 recent scans with Source ID, coverage/state/phase, unique observed/expected counts, accepted/excluded counts, known capture span, missing-date count, created/completed times and retry_requested flag. Current Source policy and run policy revision must match before scan-derived counts/spans are disclosed. Revoked/stale runs expose only a restricted status, not old coverage data. Media readiness remains a separate current-policy count.

`POST /api/ingestion/retry` requires owner session+CSRF and exactly `run_id`. For a current noncomplete scan it records a request to resume and reports `waiting_for_device`; it never grants permission or pretends the phone ran. Actual native resume acknowledges that request through begin. Source policy changes require a fresh explicit native selection/scan and cannot be bypassed by Debug retry.

Schema6 stores scan state and retained per-scan native identities for exact counting/reconciliation. Existing immutable revision, observation ordering, leases, audit and quarantined backup/restore remain authoritative. Capacity tests and final evidence will report the actual implemented bounds; no ETA or unknown-denominator percentage is fabricated.

## Indexed ordering and recovery

Schema6 also maintains a current metadata ordering index through SQLite triggers when an asset's current revision changes. It stores owner/revision/capture time/local day/type, never permission decisions. Photos listing joins the exact current asset revision and current VISIBLE policy on every read; owner/time, owner/type/time and owner/local-day/time indexes avoid sorting the entire library for a bounded page. An interrupted migration rolls back; prechange backups retain the prior schema. Early synthetic schema6 roots without these required structures fail startup and are preserved rather than silently reused.

Progress and retained scan identities survive backup/restore, but restored sessions/devices are revoked and Sources restricted. Retry records a wait for the device; it cannot revive authority. Count/phase/checkpoint/membership changes and their audit commit are one transaction. A failure leaves the prior page coherent. Source metadata remains immutable, including excluded restriction observations.

The server/frontend component is implemented; native enumeration and real device acceptance are separately pending. The benchmark script refuses existing roots and generates only synthetic records. Raw metadata and media bytes never enter project logs; benchmark output contains aggregate time/RSS/disk only. Final measured values and exact revisions belong in the evidence receipt.
