---
title: "Existing Host Deployment Delta"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Existing host deployment delta

This document describes the deployment and its current limits; the execution receipt is in `docs/evidence/host-deploy/EVIDENCE.md`. GB approved the Next/Python/private SQLite/existing-host delta. No new provider, paid capacity, source access or agent scheduler is involved.

## Verified host and remaining checks

Read-only inspection on2026-10-02 found21 existing PM2 processes and no Memory process. The user LaunchAgent runs `cloudflared tunnel run macserver`; that named tunnel has one active darwin_arm64 connector. Its user config has10 existing hostname rules and no `memory.lazyagent.ai` rule. The separate root manifest does not define this named tunnel. No process or tunnel config has been changed. Cloudflare dashboard in the task's own BrowserOS tab requires login; account cache/Worker/header settings remain unverified. The CLI connector read alone cannot establish those settings.

Before routing private data, verify that no matching Worker/transform rewrites client identity and that no matching cache rule ignores origin `no-store` on `/api/*`. Preserve all existing routes and process definitions. Do not upgrade shared cloudflared or restart unrelated services as part of this change.

## Durable release and account

Use a new isolated durable checkout of the exact merged, tested revision under `/Users/agent/apps/memory-releases/alpha-<sha>`. Never deploy from the original dirty checkout or `/private/tmp`. Keep prior releases for rollback. Create a dedicated virtual environment at `/Users/agent/Library/Application Support/Safe Memory/runtime/venv` from the verified Homebrew Python, install the pinned `requirements-runtime.txt`, and build web from the pinned lockfile. This environment must not depend on another application's packages.

The private data root is `/Users/agent/Library/Application Support/Safe Memory/alpha`; initialize without fixtures or automatic source import. Create private0700 parent/log directories and0600 log files before starting PM2. Owner provisioning remains an interactive local command, with a password entered twice privately, never copied into arguments, environment, chat or this file:

```sh
'/Users/agent/Library/Application Support/Safe Memory/runtime/venv/bin/python' -m runtime.cli --root '/Users/agent/Library/Application Support/Safe Memory/alpha' create-owner --username owner --name Owner
```

Run from the durable release. A provisioned owner still has no Photos permission or Grant. Device pairing, native Photos consent and selected import remain separate explicit actions.

## Processes and one new route

`deploy/ecosystem.config.cjs` defines only `safe-memory-api` and `safe-memory-web`, with loopback ports8766/8767, private log destinations, bounded restart policy and no credentials. It enables the explicit trusted Cloudflare identity mode only for the verified tunnel→Next→Python path. `MEMORY_RELEASE` and `MEMORY_PYTHON` can identify a reviewed immutable release/runtime; their defaults are the current release and dedicated environment.

After stopping only this task's synthetic loopback servers, start only these two PM2 entries and verify API health/session denial, process command lines and loopback listeners. Record the preexisting process IDs/statuses before and after; their configuration must remain identical. Persist PM2 state only after the new services are healthy and the existing app set is unchanged.

Prepare a private copy of the existing user cloudflared config, inserting exactly this rule before its final catch-all while preserving every existing line:

```yaml
  - hostname: memory.lazyagent.ai
    service: http://127.0.0.1:8767
```

Validate that proposed file with the installed cloudflared ingress validator, inspect the exact diff and check the Memory URL selects only the new rule. The empty application/login may be routed for the requested preview before account-level verification. Do not import personal data until the account cache/Worker settings are verified. Create the Memory DNS route against the existing named tunnel. Do not create another provider/tunnel or a wildcard. Keep the previous config as a private rollback copy. Apply the verified delta and reload only the named connector by its supported mechanism; account for any interruption to the other10 routes before choosing a restart. A route listed in a file does not establish reachability.

## Acceptance and rollback receipt

Verify HTTPS response, configured origin/Host, unauthenticated denial, Secure/HttpOnly/SameSite cookie behavior, no-store API/media responses through the actual edge, trusted client identity and owner login. Repeat the private UI journey on the actual hostname; record sanitized status/results, never session tokens or personal data. Then confirm native pairing against its fixed HTTPS origin from a signed authorized iPhone. No local fixture replaces that check.

For rollback, stop only the two Memory processes, preserve the live private root/audit, and select the prior compatible release/database pair. A database rollback uses verified backup into a new quarantined root with revoked sessions/devices and restricted Sources; never overwrite live audit with an old snapshot. Restore only the Memory route delta if needed, preserving unrelated rules. Report local, pushed, merged, deployed and accepted independently.

## Preparation receipt —2026-10-03

The dedicated Python environment now exists at the approved durable path above,
with uvicorn0.48.0/click8.5.0/h110.16.0 and working scrypt. Runtime, empty alpha,
logs and release-parent directories were created under umask077. No owner,
Source, PM2 process, DNS rule or tunnel ingress has been provisioned by that
preparation. A final release checkout/build is recorded with its exact SHA in
the integrated evidence when prepared.

Automatic approval review rejected opening the authenticated Cloudflare account
for read-only verification twice, even after the approved project delta was
cited. The current explicit account-access question must be answered before
retrying that action. This is separate from entering login/2FA if the account
subsequently requires it; credentials must stay in the user's local UI.

## Actual deployment — 2026-10-03

GB explicitly requested publication and deployment on this device. The new
Cloudflare browser request was accepted; the earlier automatic-review block
is superseded. BrowserOS currently needs account login for cache/Worker/header
rule inspection. That remains a prerequisite for personal-data import, not
for viewing the empty app login.

The named tunnel now has the one Memory ingress rule and DNS route. Its prior
configuration is preserved privately as `~/.cloudflared/config.before-memory-20261003.yml`.
Only that LaunchAgent was restarted to apply the rule; it reconnected with
four edge connections. All other ingress rules were preserved exactly.
Both Memory processes are online with the separate production root; the21
preexisting PM2 process IDs, statuses and configurations are unchanged. PM2
state was saved. HTTPS root200, health200 and unauthenticated session401 were
observed at the real hostname, with API `no-store` and Cloudflare `DYNAMIC`.
Public resolvers propagated before the local negative cache expired; normal
DNS and BrowserOS subsequently loaded the login successfully.

PM2 interpreted a Python executable path containing spaces as a shell command.
The corrected config uses `shell/server.py` as the script and the full Python
path as interpreter. It also enables `merge_logs` so PM2 uses the precreated
0600 log files. Changing an existing PM2 process did not replace its entrypoint;
only the two newly created Memory entries were recreated. Logs and data were
retained. Run `node deploy/verify-pm2.cjs /opt/homebrew/lib/node_modules/pm2`
before applying future config, and inspect actual PM2 command paths afterward.

Owner creation/login and signed iPhone installation are separate pending steps.
A code-signing identity exists on this host; device inventory currently reports
no connected devices. See `TRY-IT-ES.md` for the first owner test.
