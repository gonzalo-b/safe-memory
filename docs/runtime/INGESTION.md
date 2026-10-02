---
title: "Device Pairing and Metadata Ingestion"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Device pairing and metadata ingestion

This increment implements a bounded authorized sample of 1–100 selected native IDs. It does not yet establish whole-library coverage, progressive enumeration or media transfer. Legacy agent Grants remain separate; pairing grants no agent read permission. Device credentials can submit their bound Source only and cannot read owner data.

## Pairing

The signed-in owner starts `POST /api/pairing/start` with session/CSRF, receiving a five-minute secret. A device explicitly submits `POST /api/device/claim` with `secret`, `device_name`, durable installation `library_id` alias and a client-generated 256-bit base64url credential. Credentials and pairing secrets are hashed in SQLite. The full fingerprint is SHA-256 of the canonical 43-character credential's UTF-8 representation. The browser lists `GET /api/pairing/pending`; after comparing that fingerprint with the phone, the owner posts `claim_id` and `fingerprint` to `/api/pairing/confirm`. Confirmation returns device/owner/connection/Vault IDs. The claim ID becomes the device ID only after confirmation.

`GET /api/devices` lists this owner's devices. `POST /api/devices/revoke` with `device_id` immediately invalidates its credential. Native `POST /api/device/status` sends `device_id` and Bearer credential; successful binding still reports `data_access:false`. Reconnecting the same owner/library alias reuses its Source and Photos Vault, without creating a Grant. Installation aliases are not verified Apple library identities.

## Selected metadata protocol

Native endpoints accept no browser cookie as a substitute for a Bearer credential. Each transaction checks the device's owner epoch, revocation and Source binding. Native routes permit absent Origin; a supplied foreign Origin is refused. Browser policy changes require current session, matching Origin and CSRF.

1. `POST /api/device/ingest/begin`: `device_id`, `request_key`, `permission` (`full` or `limited`), `phase` (`recent` or `backfill`), `selected_ids`. The request key, selected IDs and permission are immutable for retries. The response gives `run_id`, `next_sequence`, state and `coverage:"bounded_authorized_sample"`.
2. `POST /api/device/ingest/append`: `device_id`, `run_id`, `batch_key`, zero-based `sequence`, opaque `checkpoint`, and 1–100 `assets`, bounded to 2 MiB. The asset wrappers below must belong to the selection. Receipt, revisions, audit and next checkpoint commit together. A repeated key must have identical content. A crash before commit writes nothing; a crash after commit returns the retained receipt on retry.
3. `POST /api/device/ingest/finish`: `device_id`, `run_id`; idempotently records sample completion, without claiming media availability. A Source lease expires after 15 minutes; begin with the same request can resume it unless a newer selection or policy change invalidated it.

Each asset has exactly `native_id`, `source_revision`, `media_type` (`photo`, `video`, `live`), `hidden` boolean, `collection` (`personal`, `shared_library`, `shared_album`, `unknown`), `capture_time` nullable ISO timestamp with offset, `time_basis` (`capture_offset`, `instant_only`, `unknown`), `owner_presence` (`owner`, `third_party`, `unknown`), nullable `source_modified`, and `metadata` object. Authorized raw metadata is retained canonically without dropping fields. A Date instant alone cannot establish the capture's local day: use `instant_only`. Missing capture time requires `unknown`. Do not infer ownership from library membership.

`source_revision` must remain stable for the identical wrapper and change when any source metadata/restriction changes. Reusing one revision with different contents is a conflict. Minimal identity, digest and restriction observations are retained even for initially excluded selected assets; their raw metadata is not retained. Immutable observation order includes restrictions even when their raw payload was excluded. A known older revision cannot replace the current observation; older source timestamps cannot relax a newer restriction. Removing a restriction requires a strictly newer known source modification time. Equal or absent times preserve the union of restrictions. An undated restriction permanently preserves uncertainty for that asset; later dated observations do not erase it. This deliberately conservative behavior may retain a restriction after an actual unhide; the owner can explicitly include that category, but automatic relaxation is not claimed. Clock uncertainty must not be used to invent chronology.

## Current policy and recovery

`POST /api/sources/policy` takes `connection_id` plus separate booleans `include_hidden`, `include_shared_library`, `include_shared_albums`. All default false. Unknown collection requires both shared opt-ins; it is never silently personal. Changes invalidate active runs and their cached receipts. `POST /api/device/permission` takes `device_id`, `permission` (`full`, `limited`, `denied`, `revoked`); every report invalidates the prior selection, including a repeat of `limited`. A fresh explicit selection is required. A new limited run clears previously authorized scope. Raw revisions already stored are retained under restriction.

`GET /api/photos` accepts unique optional `limit`, `offset`, `media_type`, `day`. Current owner and Source policy apply before matching, ordering and counts. Only known capture-local days match `day`. Responses contain metadata and `media_state:"not_transferred"`, not raw payloads or filesystem paths. Overview and Sources use the same visible predicate for counts.

Schema 3 migrates schema 1/2 transactionally after an audited backup and verifies old row counts/foreign keys. Restore retains metadata while revoking sessions/devices, restricting Sources and interrupting runs/leases. Incomplete prototype schema 3 layouts fail startup; synthetic development roots predating the final schema must be preserved and replaced with new isolated fixture roots. There is no automatic destructive repair.
