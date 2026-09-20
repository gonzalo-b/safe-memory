# CLAUDE.md — Safe Memory

Repo law. Every agent that opens this repository reads this file first. Written
by GB's desk on 2026-09-20. Agents amend it only when GB says so.

## What this is

**Safe Memory answers what happened in GB's life.** What he bought, watched,
listened to, where he was, how he slept. Normalised into one event shape, held
locally, read only through explicit per-agent Grants, every read audited.

**MindBase answers what he is building.** Ideas, plans, projects, threads.
Neither stores the other's half. Asking Safe Memory for an idea returns nothing
and that is correct behaviour, not a bug.

Codename and slug: `memory`. Product name written out for humans: Safe Memory.

**`CONTRACT.md` is the agreement.** It defines the transport, the six tools, the
event shape, the grant rules and the audit rule. When this file and `CONTRACT.md`
disagree about behaviour, `CONTRACT.md` wins and you fix this file. When they
disagree about *how to work here*, this file wins.

## Vocabulary

Use these words. They exist so one word replaces a sentence, in code, in commits
and in conversation. A new concept earns a word here before it earns an
implementation.

| Word | Meaning |
|---|---|
| **Source** | One connected app's data. Apple Photos, YouTube Music, Whoop. Not a whole account |
| **Module** | A domain of memory and the unit of permission. Photos, Music, Shopping, Health, Meetings, Messages, Email |
| **Record** | One normalised thing that happened. One shape for every Source. In code today this is the `event` of `schema/event.json` |
| **Block** | A precomputed, agent-ready `.md` that answers a family of questions. Travel Log, Top Tracks 2020. Computed by code on every sync, never by a model |
| **Grant** | What one agent may read. Modules, once or standing, window, expiry, redactions |
| **Plugin** | A `.md` recipe the user's own agent runs over MCP |
| **Artifact** | What a Plugin produces and a person keeps or shares. Travel Map, Photo Gallery |
| **Mission** | A Beta onboarding task that earns points |

`Record` and `event` are the same thing at two layers. The schema says `event`
because that is what shipped in SM-0. Say Record to a human, write `event` in
code, and do not rename the schema to chase the word.

## The five promises

These are the product. Code that breaks one of them is wrong even when it passes.

1. **Read-Only Promise.** Safe Memory reads Sources. Every write path in this
   repo targets our own store, our own audit log or our own Blocks.
2. **Get all of it.** Capture every field a Source exposes, then decide what to
   show. A field not captured at import is gone.
3. **Local first.** It runs free on the user's device. Cloud is an extra that
   earns its price.
4. **Authorised paths.** Official APIs, official exports, files already on the
   user's device.
5. **Default deny.** Nothing is visible without a Grant, and **a read that
   cannot be audited does not happen.** When the audit line cannot be written,
   the read is refused with `unaudited: true`. Fail closed, loudly.

Promise 5 is the one to reread before touching `vault/store.py`. Every rule about
what an agent may see lives there, not in the transport, so it survives the
SM-1 storage swap untouched. Keep it that way.

## Where things are

```
CONTRACT.md          the agreement. Read it before changing behaviour
CLAUDE.md            this file
schema/event.json    the Record shape. additionalProperties: false
schema/grant.json    the Grant shape
vault/store.py       grant check, window clip, redaction, audit, query
vault/mcp_stub.py    stdio JSON-RPC, the six tools
fixtures/            events.jsonl, grants.json. Every row is stamped fixture: true
audit/reads.jsonl    append-only. Never rewritten, never trimmed in code
tests/test_stub.py   the contract, asserted over the real transport
```

```bash
python3 tests/test_stub.py     # the gate. exit 0 is pass
python3 vault/mcp_stub.py      # the server, on stdio
```

**Standard library only.** No dependencies, no network client anywhere.
`tests/test_stub.py` greps for one on every run, and that grep is a feature. A
task that seems to need a package needs a conversation first.

## How work is done here

**Discover through the graph.** `graphify explain "<symbol>"` and
`graphify path "<A>" "<B>"` answer where something lives and what reaches it.
Read files for what the graph cannot answer. The graph is built with
`graphify update --no-label`, which needs no model and no API key. Never run
`graphify extract` or `graphify label`: their backend auto-detects a paid key.

**One feature per session.** Clear between slices. Before compacting, write the
checkpoint: objective, outstanding criteria, current revision, blockers, pending
agents, test commands, changed assumptions.

**Red before green.** Write the failing test, then the minimum that passes it. A
failing test gets fixed, never skipped, commented out or loosened. Every bug gets
a test that fails before the fix.

**Money is an integer.** `amount` is minor units with `currency` beside it. Never
a float, anywhere, for any reason.

**Time is local.** `ts` carries its offset and is never UTC-normalised. "What did
I buy yesterday" is a local-day question, and a frozen timestamp stops answering
it the day after it is written.

**`kind` is a closed vocabulary**: `purchase`, `watch`, `listen`, `photo`,
`place`, `health`. A Grant is written in these words, so adding one is a contract
change and goes to GB.

**Nothing is deleted.** Superseded files move to `_archive/`. This includes
fixtures, migrations and anything that looks obsolete.

**Refusals are results.** A question the agent may not ask comes back as a
normal result with `isError: true`, `denied: true` and a reason, so the agent can
say out loud why it has no answer. A refusal is never a transport error.

## Done means

A slice is done when all four hold. Not three.

1. `python3 tests/test_stub.py` exits 0, and the named tests that passed before
   still pass by name, not by count.
2. Every acceptance criterion in the slice has an artifact in
   `docs/evidence/<version>/`, and the artifact was produced at the revision
   being shipped.
3. `CHANGELOG.md` and the docs that describe the changed behaviour moved with it.
4. `VERSION` matches what the changelog says shipped.

**This repository has no git remote yet** and its release target is `local`.
Report `VERIFIED_LOCAL`. Never report a push that did not happen.

Commit format: `Safe Memory V{MAJOR.MINOR} - {Title}`.

## Already decided

Do not reopen these. They live in `~/base/projects/memory/.context/canon.md`,
which is GB's file and the faster correction path if one of them is wrong.

- **Alpha V1 is Apple Photos.** `CONTRACT.md` and `README.md` still carry the
  older Strategy V2 order that put MercadoLibre first. Strategy V2 is on Hold.
  Fix those two files when you next touch them.
- **The GitHub repo is `gonzalo-b/safe-memory`**, private until Beta. The name
  `gonzalo-b/memory` in `CONTRACT.md` §8 is stale.
- SM-0 code is kept and evolved, not replaced. `project_ref` becomes `links[]`.
- Blocks by code, Plugins in the user's own agent. No server-side inference on
  user data, ever.

## Pointers

Reach for these when the branch you are on needs them, not otherwise.

| When | Read |
|---|---|
| Changing behaviour an agent can observe | `CONTRACT.md` |
| Scope, versions, what Alpha V1 must prove | `~/base/projects/memory/docs/Memory - Master Brief.md` |
| How a version is dispatched, watched and shipped | `~/base/projects/memory/docs/Memory - Cody Setup.md` |
| Which model does what, and how to change it | `~/lazy/cody/roles.json`, or ask Cody in plain language |
| Why a decision was made | `~/base/projects/memory/.context/canon.md` |
