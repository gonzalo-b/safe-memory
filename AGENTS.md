# AGENTS.md

Read `CLAUDE.md` first. It is repo law. This file exists so a Codex or any
other agent finds the same law under the name it looks for; where the two
differ, `CLAUDE.md` wins.

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
