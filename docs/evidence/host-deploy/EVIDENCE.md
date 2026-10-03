---
title: "Existing Host Deployment Evidence"
project: memory
type: doc
status: active
created: 2026-10-03
source: codex-desktop
---

# Deployment and dual-main delivery

User authorized `lazyagent/memory`, automatic checked-PR main delivery to both
repositories, and `memory.lazyagent.ai` on the existing device on2026-10-03.
User also authorized their personal Photos library as a first persistent test
case; no Apple password, private Photos metadata or media was accessed.
Original goal attachment SHA256:
`ac2046dca5af017e3277376dd4e49351abf7bab367ee1a35e50ad9a05f863820`.

## Candidate and checks

Candidate: `b30e7add6ac9c92b643db20bbc1605af00d1032a`, based on merged main
`316620b792c89934c61c6cfdf35f1d0dc30e81cc`. Only operator tooling, deployment
configuration and documentation changed. Runtime, web, schema, connector,
vault and Block code are identical to the previously verified integrated tree.
An evidence-only follow-up records final results; no VERSION bump. Physical
Photos/iCloud and owner login acceptance remain incomplete.

- Helper12/0 tests use temporary local Git repositories, including empty target,
  non-fast-forward refusal, changed tip, stale source, private target and auth
  environment separation. RED began with missing implementation; a test-fixture
  refspec was corrected before GREEN. Agent system-Python gate lacked scrypt;
  configured Python3.14 aggregate395/0 and contract67/0 passed.
- Integrator exact-candidate `/opt/homebrew/bin/python3 tests/test_stub.py`:
  67/0, exit0. Exact-candidate aggregate395/0, exit0; log `/private/tmp/memory-deploy-gate.log`. All prior383 named tests remain;12 mirror tests were added.
- `node deploy/verify-pm2.cjs /opt/homebrew/lib/node_modules/pm2`: exit0.
  Installed PM2 parser regression first failed because it rewrote the executable
  path containing spaces into bash and discarded API arguments. Corrected
  interpreter/script separation passes. Actual old PM2 entries retained their
  old script during restart, so only the two newly created Memory entries were
  recreated. Earlier logs and all data are retained.
- `git diff --check`: exit0. No UI code changed; prior240UI/13unit plus actual
  media/filters/knowledge/artifact verification remains applicable by tree identity.

## Real host and HTTPS proof

- Existing release `alpha-c9428a6` serves the identical tested application code;
  deployment settings come from the corrected candidate. Dedicated Python venv,
  production data root `~/Library/Application Support/Safe Memory/alpha`, no
  fixture mode, no owners at last inspection. Private logs0600; parent0700.
- PM2 API/web online on127.0.0.1:8766/8767. Before/after snapshot confirms all21
  preexisting process IDs, PIDs, statuses, cwd, scripts and args unchanged.
  `pm2 save` exit0; `com.cloudflare.cloudflared` LaunchAgent running.
- Local HTTP six checks passed: health200, session/overview401, direct backend
  wrong Host403, Next-to-Python wrong Origin403 and missing edge identity403;
  API responses no-store. Next rewrites Host to the loopback backend, so direct
  backend Host rejection is not claimed as a Next arbitrary-Host rejection.
- Existing tunnel configuration preserved privately; exact delta adds one
  hostname rule before catchall. `cloudflared tunnel ingress validate` exit0,
  URL selects rule10. Existing routes unchanged. DNS CLI successfully created
  the CNAME on the existing macserver tunnel. Named LaunchAgent restart
  reconnected four edge connections; no shared software upgrade.
- Public DNS1.1.1.1 and8.8.8.8 resolved the new hostname. First local/browser
  lookup saw negative cache; later ordinary curl and BrowserOS loaded root200.
  BrowserOS showed Welcome to Memory, username/password and Sign in at the real
  HTTPS URL. API health200 and no-session401 have no-store/HSTS and Cloudflare
  DYNAMIC. HTTPS invalid-account login401 reaches credential verification,
  demonstrating a valid edge identity rather than invalid_edge_identity.
- Owner login, Secure cookie observation with an authenticated real owner,
  private Sources and full physical-device journey are NOT verified by these
  unauthenticated checks. Cloudflare account UI requires login for all matching
  cache/Worker/header rule inspection; complete before importing personal data.

## GitHub and limits

Initial target inspection with the source account could not see the repo.
The existing lazyagent keyring session, with token environment overrides removed
only in child commands, sees ADMIN/private/empty. Initial ordinary push created
its main at316620b; no force push, global login change or user data publication.
No Actions workflow was installed. The target's default Actions setting remains
enabled: automatic review rejected disabling it. User then asked about its
benefit; no permission to change that setting is assumed. Original repo retains
its existing Actions policy. Active-agent checks, merge and mirror require no
user merge click; this is not an inactive-task background watcher.

Physical inventory: no connected iPhone; one existing valid development signing
identity. Unsigned compile/synthetic tests do not establish install or Photos
sync. Native import is explicit/resumable, not verified continuous background
sync or an iCloud web login. First-run guide: `docs/runtime/TRY-IT-ES.md`.

Private raw operational receipts are retained under
`/private/tmp/memory-deploy-receipt/`; no credentials or personal source content
are included here. Merge/mirror SHAs and exact aggregate result follow below.

The existing `pm2.agent` LaunchAgent runs `pm2 resurrect` at login; saved Memory entries use that existing startup path.
