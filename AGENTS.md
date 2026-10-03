# AGENTS.md

Read `CLAUDE.md` first. It is repo law. This file exists so a Codex or any
other agent finds the same law under the name it looks for; where the two
differ, `CLAUDE.md` wins unless GB has explicitly approved a newer decision
in that scope. The approved Chat Workflow supersedes older Cody instructions.

## The five promises

- Read-Only Promise: Safe Memory reads Sources; every write path here targets
  our own store, our own audit log, or our own Blocks.
- Get all of it: capture every field a Source exposes, then decide what to show.
- Local first: it runs free on the user's device.
- Authorised paths: official APIs, official exports, files already on device.
- Default deny, fail closed: nothing is visible without a Grant, and a read
  that cannot be audited does not happen.

## Commands

```bash
python3 tests/run_all.py          # the gate. exit 0 is pass
python3 tests/test_stub.py        # the contract alone
python3 -m blocks.travel_log      # compute blocks/travel-log.md from the store
python3 shell/server.py           # the shell on http://127.0.0.1:8765, agent from SAFE_MEMORY_AGENT
python3 vault/mcp_stub.py         # the MCP server, on stdio
cd e2e && npx playwright test     # browser proof, writes docs/evidence/<VERSION>/
```

Commit format: `Safe Memory V{MAJOR.MINOR} - {Title}`.

## Done means

A slice is done when all four hold, not three:

1. The gate exits 0 and the named tests that passed before still pass by name.
2. Every acceptance criterion has an artifact in `docs/evidence/<version>/`,
   produced at the shipped revision.
3. `CHANGELOG.md` and the docs that describe the changed behaviour moved with it.
4. `VERSION` matches what the changelog says shipped.

Nothing is deleted; superseded files move to `_archive/`. No per-token
inference, no API key, no model run over user data.

## Chat Workflow

For Memory development, invoke `$memory-workflow` at
`.agents/skills/memory-workflow/SKILL.md`; see `docs/WORKFLOW.md`.
Use Astra High and delegate bounded independent subtasks when useful, with at
most two subagents and one integrator. Subagents also use Astra High.
Validate quality through tests and the integrated browser for UI; BrowserOS
and Playwright are fallbacks. Independent review is optional.
Wait for quota; no automatic model fallback, top-up or paid API.
New approved planning in `~/base/projects/memory/docs/` is authoritative for
its scope. Preserve the personal canon file. Keep checkpoints in PROGRESS and
Markdown evidence in EVIDENCE.md; do not load historical Cody docs routinely.
Harness-only installation does not bump product VERSION or claim 0.2 shipped.

## Dual repository delivery

GB approved `lazyagent/memory` as an additional private repository on 2026-10-03.
Every authorized PR is automatically merged after successful checks and its
merged `main` is fast-forwarded to both repositories. Verify matching remote
SHAs before reporting delivery complete. Follow `docs/WORKFLOW.md`; no force
push, bypassed checks or manual user merge step.
