---
title: "Runtime Operations"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Runtime operations

The approved stack is Next/React/TypeScript presentation plus Python ASGI/SQLite. This is an unreleased integrated runtime through private Galleries/original requests; no real iPhone transfer or release acceptance is implied. Legacy stdio fixtures remain separate.

## Supported interpreter and installation

This host has two Python installations: Xcode's /usr/bin/python3 lacks hashlib.scrypt; use /opt/homebrew/bin/python3 (verified 3.14.6) to create a dedicated environment. Runtime initialization refuses a Python without scrypt. Do not substitute a weaker password function or alter other services.

```sh
/opt/homebrew/bin/python3 -m venv /private/tmp/memory-runtime-venv
/private/tmp/memory-runtime-venv/bin/python -m pip install -r requirements-runtime.txt
```

The temporary environment is for development verification. Deployment uses a durable versioned release/environment, not a temporary directory. Only shell/server.py imports Uvicorn; core packages import no network client.

## Owner setup and process

Data root must be outside repositories and the document vault. The approved production root is `/Users/agent/Library/Application Support/Safe Memory/alpha`. It is never automatically seeded. Fixture roots are separate and persist their fixture flag; reopening with the other mode fails.

```sh
/path/to/venv/bin/python -m runtime.cli --root '/Users/agent/Library/Application Support/Safe Memory/alpha' create-owner --username owner --name Owner
/path/to/venv/bin/python shell/server.py --root '/Users/agent/Library/Application Support/Safe Memory/alpha' --origin https://memory.lazyagent.ai
```

Password is entered privately in the local terminal twice, never in an argument, environment variable, chat, log or repository. Provisioning is not exposed as a public HTTP endpoint. The CLI does not authorize source access.

API binds loopback8766. Next binds loopback8767 and forwards /api; existing HTTPS tunnel targets Next. The frontend must not duplicate domain policy or cache private API responses. Uvicorn disables access logs and untrusted forwarded headers, caps concurrent requests, and never binds publicly. A temporary local fixture can add --development --fixture and origin http://127.0.0.1:8767. Development refuses remote HTTP origins.

## Request bounds and trusted edge

HTTP JSON bodies are limited to 64 KiB (2 MiB for metadata append,6 MiB for base64 media/original chunks) and a total 15-second deadline, including stalled or slowly arriving chunks. A timeout or oversized body closes the connection so unread bytes cannot retain a transport slot. Login limits persist across restart: five failed account/client attempts and twenty total client attempts per fifteen minutes. Successful sign-in resets that account/client failure counter.

For the verified Cloudflare Tunnel → loopback Next → loopback Python deployment, add `--trusted-edge cloudflare`. It accepts a single valid `CF-Connecting-IP` only from the immediate loopback peer; absent/invalid identity refuses login. Ordinary `X-Forwarded-For` is never trusted. Without this explicit setting, limiter identity is the socket peer. Before enabling, verify the tunnel route and Next header propagation, prevent direct public access to either port, and confirm no same-zone Worker rewrites the header. [Cloudflare documents the edge header and Worker exceptions](https://developers.cloudflare.com/fundamentals/reference/http-headers/). This configuration is prepared, not evidence that a production route has been deployed.

## Backup and restore

```sh
/path/to/venv/bin/python -m runtime.cli --root /private/runtime backup /private/new-backup
/path/to/venv/bin/python -m runtime.cli --root /private/new-restored restore /private/new-backup
```

Each destination must be new, private, outside repositories/vault and not symlinked. Backup requires a committed audit before copying, uses SQLite online backup, and records a checksum manifest. This foundation contains metadata only; later media storage must extend the manifest before claiming full-media recovery.

Restore never overwrites the live root. A durable incomplete marker is placed before historical bytes arrive. Access stays quarantined until integrity/foreign-key checks and session revocation, owner auth epoch increment, source restriction and restore audit all commit. The marker is retained as a completion receipt. A failed restore remains quarantined; retain it and use a new destination after correcting the failure. Old live root and audit remain untouched. Reauthenticate and explicitly reauthorize each source. Do not point deployment at a restore merely because a DB file exists.

## Validation

Run the aggregate Python gate and explicit contract with the supported interpreter. tests/test_runtime.py covers restart/session/ownership/audit/recovery; tests/test_runtime_http.py drives actual ASGI requests. Browser evidence must distinguish mocked UI, real-runtime synthetic, authorized export and real device. No fixture result establishes device acceptance.
