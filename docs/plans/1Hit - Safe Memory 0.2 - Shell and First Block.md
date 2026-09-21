# 1Hit - Safe Memory 0.2 - Shell and First Block

> **Mode:** full-YOLO. Autonomous end to end.
> **Objective:** A local webapp reads the SM-0 store, renders one precomputed Block (the Travel Log), and shows nothing without a Grant, proven by screenshots and audit lines.
> **Depends on:** nothing. Base is `master` at `92615f7` (Safe Memory 0.1.0).
> **Host:** macserver (Apple M1), user `agent`, repo `/Users/agent/apps/memory`, tmux window `cody:memory-0.2`.
> **Publish:** commits land on `master`, the only branch. The repository has **no git remote** (verified 2026-09-20 with `git remote -v`, empty). Every push is a technical constraint logged as blocked, the release target is `local` and the report says `VERIFIED_LOCAL`. GB's rule of 2026-09-11 (ship to main) applies the moment a remote exists; see §11.
> **Compiled:** 2026-09-20 from a recon of the repo on that date.

## 0. Execution contract (read first)

1. **This file is the contract.** Everything that produced it was context.
   Execute what is written here; do not go looking for the original plan.
   `CLAUDE.md` is repo law and is read first, but it is never edited by this
   work: it says "Agents amend it only when GB says so", and GB has not.
2. **YOLO.** Ask nothing. On an ambiguous choice take the recommended option,
   log it under "Decisions I made" in the final report, continue. The only
   stop is a destructive, irreversible action on production data or
   infrastructure. There is none in this repo.
3. **Finish everything.** If an item blocks, complete all the rest and report
   exactly what is missing and why. Reducing scope on your own is not an
   option. These words are banned in code, commits and reports: "for now",
   "placeholder", "simplified version", "v1 of", "hardcoded for now", "will be
   wired later", "TODO later".
4. **Do not invent.** Verify every path, env var, script, endpoint and column
   before use. If something does not exist, say so; never simulate it with a
   realistic-looking placeholder.
5. **Repo law wins.** From `CLAUDE.md` and `CONTRACT.md`, the invariants this
   work can plausibly break:
   - **Default deny and fail closed.** Nothing is visible without a Grant. A
     read that cannot be audited does not happen: it is refused with
     `denied: true, unaudited: true`. Every rule about what an agent may see
     lives in `vault/store.py`, never in a transport, never in the shell.
   - **Read-Only Promise.** The only write paths are our own audit log
     (`audit/reads.jsonl`, append-only, never rewritten or trimmed) and our
     own Block files under `blocks/`.
   - **Identity is never a request argument.** The calling agent comes from
     the MCP `initialize` client identity or from `SAFE_MEMORY_AGENT` in the
     server's environment. A query string, cookie, header or form field never
     names the agent.
   - **Standard library only on the Python side.** No package, no network
     client, nothing that shells out, in `vault/`, `blocks/` or `shell/`.
     `tests/test_stub.py` greps for that and the grep is a feature; the new
     tests extend the grep to the new files.
   - **Refusals are results**, with `isError: true`, `denied: true` and a
     reason. Never a transport error.
   - **Money is an integer, time is local, `kind` is closed.** Nothing here
     adds a kind or touches `amount`.
   - **Nothing is deleted.** Superseded files move to `_archive/`.
   - **Done means all four hold:** the gate exits 0 and the named tests that
     passed before still pass by name; every acceptance criterion has an
     artifact in `docs/evidence/0.2.0/` produced at the shipped revision;
     `CHANGELOG.md` and the docs moved with the behaviour; `VERSION` matches
     the changelog.
   - Fleet law: secrets only through 1Password `op://` references at the
     secret-pull layer (`secrets-pull` writes `~/.config/secrets/agents.env`
     from `agents.env.tpl`; `~/.bashrc` mirrors `~/.zshenv` and sources it for
     every shell, agent and daemon; `session.sh open` inherits
     `CLAUDE_CODE_OAUTH_TOKEN` from the environment, never a runtime `op
     read`); never an `sk-` key in any file. This work needs no secret at all.
     Production PM2 processes untouched. Nothing deleted, only moved to
     `_archive/`. No polling of Claude Max by cron. Bounded shell commands on
     the M1, no broad `find` over `~`. Ops is the only status writer in
     MindBase. Finance paths are draft-only. Commit format
     `Safe Memory V{MAJOR.MINOR} - {Title}`. Changelog and docs move with
     every slice (SHIP rule). Max subscription only: no Anthropic API key, no
     per-token provider, no model run over user data.

   Where this file and repo law conflict, repo law wins, except these three
   explicit overrides, each with its reason:
   - **Playwright is added as a dev dependency**, in `e2e/` only, as a Node
     package. `CLAUDE.md` says a package needs a conversation first; GB had
     it in `Memory - Cody Setup.md` §2, slice S0, which names "Playwright as a
     dev dependency with one smoke test". Playwright is never imported by any
     Python file, `e2e/node_modules/` is gitignored, and the Python side
     stays standard library.
   - **One named test is renamed.** `tools/list answers exactly the six
     contract tools` in `tests/test_stub.py` becomes `tools/list answers the
     six contract tools and sm_block`, asserting the seven names in order.
     The input's S2 asks the stub to serve the Block, which is a seventh
     tool, and `CONTRACT.md` §4 moves with it in the same slice. Every other
     named test keeps its name and passes. The rename is recorded in
     `PROGRESS.md` and the final report.
   - **The shell listens on a port.** `CONTRACT.md` §2 says nothing in the
     repository listens on a port. The shell binds `127.0.0.1` only, serves
     a page and one JSON endpoint to the same machine, and is not the MCP HTTP
     transport (still SM-1's work). `CONTRACT.md` §2 gets one sentence saying
     exactly that.
6. **Evidence, not assertions.** Nothing is done until the command that proves
   it has run and its output is in the report. UI is proven in a browser by
   the Verifier, never by the slice's implementer.
7. **Retry budget.** Three attempts per failing gate. A gate still red after
   three attempts becomes a blocker: skip that slice without committing it,
   paste its output in `PROGRESS.md` and in the report, and finish every
   other slice, each committed on `master` as it passes. Never loosen a check
   to pass it.
8. **Run order.** §7 item 1 (clean start); §1 Step 0 (record
   `BASE=$(git rev-parse HEAD)` and the baseline counts in `PROGRESS.md`);
   §4 wave by wave: per slice §9.2, commit on `master` (slice is *built*);
   once every slice of the wave is either committed or logged as blocked in
   `PROGRESS.md`, the Verifier runs §9.2 and §9.3 on `master` (built slices
   become *done*); after the last wave §9.4; §9.5; §8; one final commit per
   §7 item 7; §12 report. Record every §10 criterion as you prove it with
   `bash ~/lazy/cody/lib/complete.sh record <run id> <criterion id> --outcome
   pass --artifact <path> --verifier <identity>` (the run id is in
   `.cody/seed-memory-0.2.md`). After §12 is written, run
   `bash ~/lazy/cody/lib/complete.sh request <run id>`; if that script is
   unavailable, run `touch .cody/done-memory-0.2`.

## 1. Current state (verify before trusting)

Diagnosis from recon on 2026-09-20. Everything below was read from the repo
that day.

| Fact | Expected | Verify with |
|---|---|---|
| Branch | `master`, no remote | `git branch --show-current; git remote -v` (second prints nothing) |
| Base commit | `92615f7 Safe Memory V0.1 - Graphify code graph, built local with no API key` | `git log --oneline -1` |
| Version source | `VERSION` = `0.1.0`; `CONTRACT.md` header says 0.1.0 | `cat VERSION` |
| Changelog | none exists | `ls CHANGELOG.md` fails |
| Baseline tests | `59 passed, 0 failed`, exit 0, in under 2 seconds | `python3 tests/test_stub.py; echo $?` |
| Python | 3.14.6 at `/opt/homebrew/bin/python3` | `python3 --version` |
| Node | v24.14.1, `npx` at `/opt/homebrew/bin/npx` | `node --version` |
| Playwright in repo | none: no `package.json`, no `e2e/`, no `playwright.config.*` | `ls package.json e2e playwright.config.* ` all fail |
| Playwright on machine | `@playwright/test` 1.60.0 installed under `~/apps/qualy/node_modules`; chromium builds 1223 and 1234 under `~/Library/Caches/ms-playwright` | `ls ~/Library/Caches/ms-playwright` |
| Working tree at start | `graphify-out/graph.json` modified, `graphify-out/cody-manifest.json` untracked. Both belong to the Cody flow's graph rebuild; do not revert, do not stage them in slice commits | `git status --short` |
| Fixtures | 13 events in `fixtures/events.jsonl`; 3 of them are `photo` or `place`, all with `location.place` = `Bariloche, Rio Negro`, ids `ev-fixture-0010`, `ev-fixture-0011`, `ev-fixture-0012`, day offsets 30, 29, 30 | `grep -c '"kind": "p' fixtures/events.jsonl` prints 6 (3 purchases plus 3 photo or place) |
| Grants | `lazy`: all six kinds, 90 days, nothing redacted. `siri`: purchase, watch, listen, 7 days, amount and currency redacted | `cat fixtures/grants.json` |
| Audit log | `audit/` is gitignored; `audit/reads.jsonl` has 9 lines | `wc -l audit/reads.jsonl` |
| Store read path | `vault/store.py`: `load_events`, `load_grants`, `grant_for`, `Denied`, `AuditFailed`, `_redact`, `audit`, `query`, `grants`. Env overrides `SAFE_MEMORY_FIXTURES`, `SAFE_MEMORY_AUDIT` | `grep -n '^def \|^class ' vault/store.py` |
| Stub | `vault/mcp_stub.py`: `TOOLS` (six), `Session.call_tool`, `Session.handle`, `_result`, `_error`, `serve`. Refusals built inline in `handle` | `grep -n '^def \|^class \|^TOOLS' vault/mcp_stub.py` |
| Graph | `graphify` at `~/.local/bin/graphify`; graph at `graphify-out/graph.json` | `which graphify` |
| Plan dir | `docs/plans/` holds this file; `docs/evidence/` does not exist yet | `ls docs` |
| Cody sentinel dir | `.cody/` exists, empty | `ls -a .cody` |

**Step 0 of your work is to re-run every row.** Reality wins; note every
difference in the final report. The suite never ends with fewer passing tests
than it started with, and every one of the 59 names keeps passing except the
one rename in §0 item 5.

## 2. Scope

### In
1. `AGENTS.md`, `CONTEXT.md`, `PROGRESS.md` at the repo root, written by this
   work, consistent with `CLAUDE.md` and never contradicting it.
2. Playwright as a Node dev dependency in `e2e/`, one smoke test that proves
   the browser launches, `docs/evidence/0.2.0/` created.
3. `blocks/` package: `blocks/travel_log.py` computes the Travel Log Block by
   code from the store's events and writes `blocks/travel-log.md`. No model,
   no inference, deterministic.
4. `vault/store.py` gains `block(agent, name, via)`: grant-checked on the
   Block's kinds, one audit line per read, fail closed. `vault/mcp_stub.py`
   gains the seventh tool `sm_block`. `CONTRACT.md` moves with it.
5. `shell/`: a local webapp on `127.0.0.1`, standard library only, one page
   route `/` that renders the Block, with loading, empty, denied and error
   states, light and dark, desktop and mobile.
6. Default deny proven end to end: a shell started without an agent shows
   nothing, leaks no data, and still writes an audit line. Same over MCP.
7. Tests for all of the above, self-exiting scripts in the repo's convention,
   one runner `tests/run_all.py`. Playwright specs write the evidence PNGs.
8. `CHANGELOG.md` created, `VERSION` to `0.2.0`, `README.md` and
   `CONTRACT.md` fixed per canon where touched, graph rebuilt.

### Out
- Any connector or real Source. Apple Photos is 0.3 (GB's roadmap).
- The other four Alpha V1 Blocks (Countries, Trips, Stats, On This Day): 0.4.
- Artifacts, Plugins, onboarding, a design system: 0.5 and 0.6.
- The MCP HTTP transport under PM2: SM-1, not this version.
- A GitHub remote: GB's gate (§11). Never create it from here.
- Editing `CLAUDE.md`: GB only.
- Per-agent Block computation (a Block clipped to the reader's window or
  redactions): a later version, see the decision in §3.4.
- A theme toggle in the UI: the shell follows the OS colour scheme only.
- `pytest`: never added. The repo's test convention is the self-exiting
  script, and the acceptance "test suite green above the 0.1.0 baseline" is
  met by `python3 tests/run_all.py`.

## 3. Specification

### 3.1 Root files (S0)

**`AGENTS.md`** (new, under 60 lines). Opens with: "Read `CLAUDE.md` first.
It is repo law. This file exists so a Codex or any other agent finds the same
law under the name it looks for; where the two differ, `CLAUDE.md` wins."
Then, verbatim in this order: the five promises as one line each (Read-Only,
Get all of it, Local first, Authorised paths, Default deny with fail closed);
the commands block:

```bash
python3 tests/run_all.py          # the gate. exit 0 is pass
python3 tests/test_stub.py        # the contract alone
python3 -m blocks.travel_log      # compute blocks/travel-log.md from the store
python3 shell/server.py           # the shell on http://127.0.0.1:8765, agent from SAFE_MEMORY_AGENT
python3 vault/mcp_stub.py         # the MCP server, on stdio
cd e2e && npx playwright test     # browser proof, writes docs/evidence/<VERSION>/
```

then the commit format `Safe Memory V{MAJOR.MINOR} - {Title}`, the "done
means all four hold" list from `CLAUDE.md`, "nothing is deleted, move to
`_archive/`", and "no per-token inference, no API key, no model over user
data".

**`CONTEXT.md`** (new). Title `# Safe Memory - Context`. One sentence: "The
vocabulary. One word replaces a sentence; a new concept earns a word here
before it earns an implementation." Then a table with exactly these rows, in
this order, definitions copied from `CLAUDE.md` where they exist there and
from GB's Domain Glossary otherwise:

| Word | Meaning |
|---|---|
| Source | One connected app's data. Apple Photos, YouTube Music, Whoop. Not a whole account |
| Connector | The integration that reads a Source under the user's authorisation |
| Connection | One authorised link to a Source account, library or selected scope |
| Module | A domain of memory and the unit of permission. Photos, Music, Shopping, Health, Meetings, Messages, Email |
| Vault | One domain collection of a person's data: Photos Vault, Health Vault. At most one per domain per person. Not the whole memory. The code directory `vault/` predates this word and holds the SM-0 store; it is not renamed |
| Record | One normalised thing that happened. One shape for every Source. In code this is the `event` of `schema/event.json` |
| Evidence | Records and explicit user corrections that support a claim |
| Block | A precomputed, agent-ready `.md` that answers a family of questions. Computed by code on every sync, never by a model. `blocks/travel-log.md` is the first |
| Capability | A named question Safe Memory can answer. MCP tools expose Capabilities |
| Grant | What one agent may read. Modules (today: kinds), once or standing, window, expiry, redactions |
| Plugin | A `.md` recipe the user's own agent runs over MCP |
| Artifact | What a Plugin produces and a person keeps or shares. Travel Map, Photo Gallery |
| Publication | A deliberately shared projection of an Artifact with its own access rules |
| Mission | A Beta onboarding task that earns points |
| Shell | The local webapp in `shell/`. Renders Blocks to the person on their own machine. Its agent identity comes from `SAFE_MEMORY_AGENT` at launch, never from a request |
| Audit line | One JSON line in `audit/reads.jsonl` per read, granted or refused. A read that cannot write one does not happen |

Close with the boundary sentence from `CLAUDE.md`: Safe Memory answers what
happened; MindBase answers what he is building; neither stores the other's
half.

**`PROGRESS.md`**. The Cody flow may have created it before the session with
a `## Definition of done` block; keep that block byte for byte and add the §6
content after it. If it does not exist, create it with §6 content only.

### 3.2 Playwright (S0)

`e2e/package.json`:

```json
{
  "name": "safe-memory-e2e",
  "private": true,
  "description": "Browser proof for the Safe Memory shell. Node only; never imported by Python.",
  "scripts": { "test": "playwright test" },
  "devDependencies": { "@playwright/test": "1.60.0" }
}
```

Install with `cd e2e && npm install` (creates `package-lock.json`, committed).
Then `npx playwright test smoke.spec.js`. If Playwright reports a missing
browser, run `npx playwright install chromium` once (network, seconds). If
that fails for lack of network, it is a §11 blocker.

`e2e/playwright.config.js` in S0:

```js
const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: '.',
  outputDir: 'test-results',
  workers: 1,
  fullyParallel: false,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  use: { screenshot: 'off', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop-light', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'light' } },
    { name: 'desktop-dark',  use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, colorScheme: 'dark' } },
    { name: 'mobile-light',  use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'light', isMobile: true, hasTouch: true } },
    { name: 'mobile-dark',   use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, colorScheme: 'dark', isMobile: true, hasTouch: true } },
  ],
});
```

`e2e/smoke.spec.js`: navigates to
`data:text/html,<title>Safe Memory smoke</title><h1>ok</h1>`, asserts the
title is `Safe Memory smoke` and `h1` text is `ok`. No server. Runs under
every project.

`e2e/helpers.js`: exports `shot(page, testInfo, id)` which saves
`../docs/evidence/<VERSION>/<id>-<w>x<h>-<theme>.png` where `<VERSION>` is
read from the repo's `VERSION` file, `<w>x<h>` from
`testInfo.project.use.viewport`, `<theme>` from `colorScheme`; and
`consoleErrors(page)` which returns an array collecting every `console`
message of type `error` and every `pageerror`.

`.gitignore` gains four lines: `e2e/node_modules/`, `e2e/test-results/`,
`e2e/playwright-report/`, `e2e/.tmp/`.

`docs/evidence/0.2.0/.gitkeep` is created so the directory exists at S0.

### 3.3 The Travel Log Block (S1)

`blocks/__init__.py` holds the registry and imports nothing from `vault`
(this is what keeps `vault.store` importing `blocks` free of a cycle):

```python
BLOCKS = {
    "travel-log": {"title": "Travel Log", "kinds": ("photo", "place"), "file": "travel-log.md"},
}
```

`blocks/travel_log.py` imports `vault.store` (after inserting the repo root
into `sys.path`, the same three lines `vault/mcp_stub.py` uses) and exposes:

- `compute(events: list[dict]) -> str`: pure, deterministic, no clock, no
  randomness, no model.
- `write(out_path: str) -> str`: `compute(store.load_events())`, writes the
  text to `out_path` (creating the directory), returns the text. The only
  `open(..., "w")` in the module names `out_path`.
- `main(argv)`: `python3 -m blocks.travel_log [--out PATH]`, default
  `blocks/travel-log.md`, prints `travel-log: <records> records -> <path>`.
  Events come from the store, so `SAFE_MEMORY_FIXTURES` selects the source.

Selection: events whose `kind` is `photo` or `place`. Group key: the exact
string `location.place`; events with no place go under the group
`Unplaced`. Groups ordered by their earliest `ts`, then by name. Rows inside a
group ordered by `ts` ascending, then by `id`. Date is `ts[:10]`, time is
`ts[11:16]`.

Exact output for the shipped fixtures (dates are relative to the day of the
run because the fixture rows carry `day_offset`; on 2026-09-20 they resolve to
2026-08-21 and 2026-08-22):

```markdown
<!-- generated by blocks/travel_log.py; never edit by hand -->
<!-- block: travel-log | records: 3 | kinds: photo, place -->
# Travel Log

Places your photos and check-ins put you, grouped by place and day. Computed by code from 3 records. Fixture data: none of it happened.

## Bariloche, Rio Negro

- Days: 2026-08-21 to 2026-08-22
- Records: 2 photos, 1 place
- 2026-08-21 12:00 place Bariloche (ev-fixture-0012)
- 2026-08-21 15:10 photo Cerro Catedral (ev-fixture-0010)
- 2026-08-22 10:02 photo Lago Nahuel Huapi (ev-fixture-0011)
```

Rules: the two comment lines are always the first two lines, in that form.
`records` is the count of selected events. Singulars: `1 photo`, `1 place`;
plurals with `s`. A group with one day prints `- Days: 2026-08-21`. When no
event is selected the file is:

```markdown
<!-- generated by blocks/travel_log.py; never edit by hand -->
<!-- block: travel-log | records: 0 | kinds: photo, place -->
# Travel Log

No trips in your records yet. Computed by code from 0 records.
```

The file ends with exactly one newline. `blocks/travel-log.md` is committed,
regenerated by `python3 -m blocks.travel_log` before every commit that ships
it, and never edited by hand; the first line says so.

### 3.4 The Block read path (S2)

`vault/store.py` gains, beside the existing loaders:

```python
BLOCKS_DIR = os.environ.get("SAFE_MEMORY_BLOCKS", os.path.join(HOME, "blocks"))

class BlockMissing(Exception):
    """The Block is registered but its file has not been computed."""

def block(agent: str, name: str, via: str = "mcp") -> dict: ...
```

`block()` is the one read path for Blocks. Order, and it never changes:

1. `name` not in `blocks.BLOCKS`: `audit(agent, "sm_block", {"name": name,
   "via": via}, False, 0, "unknown block")`, then `raise Denied(f"unknown
   block {name!r}")`.
2. `grant_for(agent)` is `None`: audit `False, 0, "no grant"`, then
   `raise Denied(f"agent {agent!r} has no grant")`.
3. Every kind in the Block's `kinds` must be in the grant's `kinds`.
   Otherwise audit `False, 0, "kinds not granted"`, then
   `raise Denied(f"agent {agent!r} may not read {sorted(missing_kinds)}")`.
4. Read `os.path.join(BLOCKS_DIR, spec["file"])`. On `OSError`: audit
   `True, 0, "block not computed"`, then `raise BlockMissing(f"block
   {name!r} is not computed; run python3 -m blocks.travel_log")`.
5. Parse `records: N` from the second line (regex `records: (\d+)`; missing
   means 0). Audit `True, N`. Return
   `{"block": name, "title": spec["title"], "kinds": [...], "records": N,
   "markdown": text, "agent": agent, "stub": True}`.

The audit line is written before any data is returned, so `AuditFailed`
raised inside `audit()` propagates and the caller never receives the
markdown. `via` is `"mcp"` from the stub and `"shell"` from the shell; it
appears inside `args` of the audit line, which is how GB tells the two
apart. Window and redaction do not apply to a Block read.

`Decision (YOLO): a Block read is governed by the grant's kinds and expiry
only - a Block is an aggregate computed on sync, not a row set; clipping it
per reader would make it per-agent, which GB's Block contract defers. GB
should confirm this one.`

`vault/mcp_stub.py`:

- `TOOLS` gains a seventh entry, after `sm_grants`:

  ```python
  {
      "name": "sm_block",
      "description": "One precomputed Block as markdown. Grant-checked on the Block's kinds, one audit line per read.",
      "inputSchema": {"type": "object",
                      "properties": {"name": {"type": "string", "enum": ["travel-log"]}},
                      "required": ["name"]},
  }
  ```
  The enum is `list(blocks.BLOCKS)` so it grows with the registry.
- `Session.call_tool`: `if name == "sm_block": return store.block(self.agent,
  str(args.get("name") or ""), via="mcp")`.
- Two module-level helpers, used by `handle` and by the shell:

  ```python
  def refusal_payload(exc: Exception, agent: str) -> dict:
      return {"denied": True, "reason": str(exc), "agent": agent, "events": [],
              "count": 0, "stub": True, "unaudited": isinstance(exc, store.AuditFailed)}

  def missing_payload(exc: Exception, agent: str, name: str) -> dict:
      return {"missing": True, "reason": str(exc), "agent": agent, "block": name, "stub": True}
  ```
  `handle` replaces its inline refusal dict with `refusal_payload` (same
  keys, same values, the existing tests keep passing) and adds
  `except store.BlockMissing as e:` returning a result with
  `structuredContent: missing_payload(...)`, `content[0].text` the same as
  JSON, `isError: True`. A missing Block is not a refusal, so it never carries
  `denied`.

`CONTRACT.md`, same slice: header version `0.2.0`; §2 one sentence: "0.2 adds
a local shell (`shell/server.py`) that binds `127.0.0.1` and serves one page
to the same machine; it is not the MCP HTTP transport, which is still SM-1."
§4 title becomes "The seven tools", the table gains the `sm_block` row
(`name` required, "One precomputed Block as markdown"), and a paragraph
states the five-step order above, the `via` key, and that a missing Block
answers `missing: true` with `isError: true`. §8 repository listing gains
`blocks/`, `shell/`, `e2e/`, `tests/run_all.py`, and its last paragraph
names the repo `gonzalo-b/safe-memory` (canon; the old `gonzalo-b/memory` is
stale).

### 3.5 The shell (S3)

`shell/server.py`, standard library only (`http.server`, `json`, `os`,
`sys`, `urllib.parse` is not needed: routes are exact strings). Listens on
`127.0.0.1` at `SAFE_MEMORY_SHELL_PORT` (default `8765`). Agent identity is
`os.environ.get("SAFE_MEMORY_AGENT", "")` read once at start. Startup prints
one line: `shell: http://127.0.0.1:<port> agent=<name or '(none)'>
blocks=<BLOCKS_DIR>`. `ThreadingHTTPServer`, `serve_forever`, exits 0 on
`KeyboardInterrupt`. Never opens a file for writing. Never shells out.
Every response carries `Cache-Control: no-store`.

Routes, exact:

| Method and path | Response |
|---|---|
| `GET /` | 200, `text/html; charset=utf-8`, the bytes of `shell/index.html` |
| `GET /shell.css` | 200, `text/css; charset=utf-8`, `shell/shell.css` |
| `GET /shell.js` | 200, `text/javascript; charset=utf-8`, `shell/shell.js` |
| `GET /api/block/travel-log` | JSON, see below |
| anything else | 404, `application/json`, `{"error": "not found"}` |

`/api/block/travel-log` calls `store.block(agent, "travel-log", via="shell")`:

| Outcome | Status | Body |
|---|---|---|
| success | 200 | the dict `block()` returns |
| `Denied` or `AuditFailed` | 200 | `mcp_stub.refusal_payload(exc, agent)` (a refusal is a result) |
| `BlockMissing` | 503 | `mcp_stub.missing_payload(exc, agent, "travel-log")` |

`shell/index.html`: `<title>Safe Memory</title>`, `<meta name="viewport"
content="width=device-width, initial-scale=1">`, links `shell.css`, loads
`shell.js` with `defer`. Body:

```html
<header>
  <h1 class="brand">Safe Memory</h1>
  <p class="sub">Shell 0.2 <span class="badge" id="agent">agent: …</span> <span class="badge">fixture data</span></p>
</header>
<main id="block" data-state="loading" aria-live="polite"></main>
<footer><p>Every read is audited. Nothing is shown without a Grant.</p></footer>
```

`shell/shell.js` (plain, no module, no library): on load, `render("loading")`
then `fetch("/api/block/travel-log")`. State machine on `main#block`
(`data-state` is the selector the tests use):

| State | When | Content (exact copy) |
|---|---|---|
| `loading` | before the fetch resolves | `<p class="status">Reading the Travel Log</p>` and a CSS spinner `<span class="spinner" aria-hidden="true"></span>` |
| `block` | 200 and `records > 0` | the markdown rendered (below) followed by `<p class="meta">Computed by code from N records. Read as <agent>, audited.</p>` |
| `empty` | 200 and `records === 0` | `<h2>Travel Log</h2><p class="status">No trips in your records yet.</p><p class="meta">A Block is computed by code on every sync. This one found 0 records.</p>` |
| `denied` | body has `denied: true` | `<h2>Nothing to show</h2><p class="status">Safe Memory shows nothing without a Grant.</p><p class="reason"><reason verbatim></p><p class="meta">This read was refused and audited.</p>`; when `unaudited` is true the last line is `This read was refused because it could not be audited.` |
| `error` | fetch threw, response not ok, or body has `missing: true` | `<h2>The Block could not be read</h2><p class="reason"><reason verbatim, or "The shell could not reach the store."></p><button id="retry" type="button">Retry</button>`; Retry runs the fetch again from `loading` |

The `#agent` badge shows `agent: <name>` from the response body's `agent`, or
`agent: none` when it is empty. The denied and error states put no field of
any Record in the DOM: the test asserts the page text never contains
`Bariloche`, `Catedral`, `Nahuel` or `ev-fixture`.

Markdown rendering, in `shell.js`, for the subset the Block uses and nothing
more: HTML-escape the whole text first; drop lines starting with `<!--`;
`# ` to `<h2>` (the page `<h1>` is the brand), `## ` to `<h3>`; consecutive
`- ` lines to one `<ul>` of `<li>`; other non-empty lines grouped by blank
lines into `<p>`; `**x**` to `<strong>x</strong>` inside any of them. No
`innerHTML` from unescaped input.

`shell/shell.css`: tokens on `:root`, dark via
`@media (prefers-color-scheme: dark)`. Light: background `#ffffff`, text
`#111111`, muted `#5f6368`, surface `#f4f4f5`, accent `#0f766e`. Dark:
background `#101214`, text `#f2f2f2`, muted `#a1a1aa`, surface `#1a1d21`,
accent `#2dd4bf`. Font stack `-apple-system, "SF Pro Text", "Helvetica
Neue", Arial, sans-serif`, base 16px, line height 1.5. `main` max-width
720px centred, padding 24px; at widths below 480px padding 16px, single
column. Badges are pills on the surface colour. The spinner is a 16px
circle border animation. Reason text in the denied and error states is
monospace on the surface colour. No image, no font download, no external
URL anywhere.

Mobile is 390x844; nothing scrolls horizontally at that width.

### 3.6 Default deny, proven (S4)

Three proofs, all three required:

1. Over the shell: a server started with `SAFE_MEMORY_AGENT` unset serves
   `denied: true`, reason `agent '' has no grant`, and the page is in state
   `denied` with no Record text. `audit/reads.jsonl` gains exactly one line
   with `"allowed": false`, `"agent": ""`, `"tool": "sm_block"`,
   `"reason": "no grant"` and `"args": {"name": "travel-log", "via": "shell"}`.
2. Over MCP: `sm_block` with no `initialize`, and with `initialize` as
   `stranger`, both answer `isError: true`, `denied: true`, `count: 0`, no
   `markdown` key, and each writes one audit line with `allowed: false`.
   `siri` (no `photo` or `place` in its grant) is refused with `may not read
   ['photo', 'place']`.
3. Fail closed: with `SAFE_MEMORY_AUDIT` pointing under a regular file, both
   the shell and the stub refuse the Block read with `unaudited: true`.

## 4. Work plan: slices and waves

Slices form a task graph. Every slice here depends on the previous one, so
the waves are serial; that is the shape of a tracer bullet and it is fine.
`PROGRESS.md` is shared by every slice and is exempt from file ownership.

### S0 - Foundation: root files, Playwright, evidence dir   (wave 0, blocked by: nothing)
- **Delivers:** `AGENTS.md`, `CONTEXT.md`, `PROGRESS.md` in place; the
  browser driver proven by a smoke test under four projects; the evidence
  dir exists; this plan committed.
- **Files owned:** `AGENTS.md`, `CONTEXT.md`, `PROGRESS.md`, `.gitignore`,
  `e2e/package.json`, `e2e/package-lock.json`, `e2e/playwright.config.js`,
  `e2e/smoke.spec.js`, `e2e/helpers.js`, `docs/evidence/0.2.0/.gitkeep`,
  `docs/plans/1Hit - Safe Memory 0.2 - Shell and First Block.md` (committed
  as is, never edited).
- **Read first:** `CLAUDE.md`, `CONTRACT.md`, §3.1, §3.2, §6.
- **Do:** write the three root files per §3.1; `cd e2e && npm install`;
  write the config, helpers and smoke spec per §3.2; extend `.gitignore`;
  create the evidence dir.
- **Verify:** `cd e2e && npx playwright test smoke.spec.js` prints `4 passed`
  and exits 0; `python3 tests/test_stub.py` still `59 passed, 0 failed`;
  `git status --short` shows no `e2e/node_modules`.
- **Built when:** all three verifies hold, committed as
  `Safe Memory V0.2 - Foundation: AGENTS, CONTEXT, PROGRESS and Playwright`.
- **Done when:** built, and the Verifier re-ran the smoke test on `master`.

### S1 - The Travel Log Block   (wave 1, blocked by: S0)
- **Delivers:** `python3 -m blocks.travel_log` writes `blocks/travel-log.md`
  exactly per §3.3; the file is committed; tests prove determinism and shape.
- **Files owned:** `blocks/__init__.py`, `blocks/travel_log.py`,
  `blocks/travel-log.md`, `tests/test_blocks.py`, `tests/run_all.py`.
- **Read first:** `vault/store.py` (`load_events`, `_resolve_fixture_row`),
  `fixtures/events.jsonl`, `tests/test_stub.py` (the `check` convention), §3.3.
- **Do:** write the registry and module per §3.3. `tests/run_all.py` runs
  every `tests/test_*.py` as a subprocess with `sys.executable`, streams
  their output, prints `TOTAL: N passed, M failed` and exits 1 if any failed.
  `tests/test_blocks.py` checks, each by name: first two lines exact;
  `records: 3` with the shipped fixtures; one `## Bariloche, Rio Negro`
  heading; three record rows in `ts` order carrying the three ids;
  `Days:` line spans two dates; `2 photos, 1 place`; two consecutive
  `compute()` calls are byte-identical; `compute([])` equals the empty text
  in §3.3; `write()` to a temp path produces a file equal to `compute()` of
  the store's events; the committed `blocks/travel-log.md` starts with the
  generated header line and contains `records: 3` and the Bariloche heading;
  `blocks/travel_log.py` imports no network client, shells out to nothing,
  deletes nothing, and opens exactly one path for writing, named `out_path`
  (reuse the regexes from `tests/test_stub.py` section 6).
- **Verify:** `python3 -m blocks.travel_log` prints `travel-log: 3 records
  -> blocks/travel-log.md`; `python3 tests/run_all.py` exits 0 with
  `TOTAL:` above 59 passed and 0 failed.
- **Built when:** verifies hold and `blocks/travel-log.md` is the output of
  that very run; committed as `Safe Memory V0.2 - Travel Log Block, computed
  by code`.
- **Done when:** built and the Verifier re-ran the gate on `master`.

### S2 - Serve the Block, grant-checked and audited   (wave 2, blocked by: S1)
- **Delivers:** `sm_block` over stdio JSON-RPC returns the Block for `lazy`,
  refuses `siri`, `stranger` and the unidentified client, answers
  `missing: true` when the file is absent, one audit line each.
- **Files owned:** `vault/store.py`, `vault/mcp_stub.py`,
  `tests/test_stub.py`, `CONTRACT.md`.
- **Read first:** `vault/store.py` whole, `vault/mcp_stub.py` whole,
  `tests/test_stub.py` sections 2, 4 and 5, §3.4.
- **Do:** per §3.4. In `tests/test_stub.py`: rename the one test per §0 item
  5 and assert the seven names; add, by name: `sm_block travel-log returns
  the Block markdown for lazy` (structuredContent has `block`, `records ==
  3`, `markdown` starting with the generated header); `sm_block is refused
  for siri and names the kinds`; `sm_block is refused for an agent with no
  grant`; `sm_block is refused for a client that never identified itself`;
  `an unknown block is a refusal, not a transport error`; `a Block that is
  not computed answers missing: true and no markdown` (run with
  `SAFE_MEMORY_BLOCKS` at an empty temp dir); `every sm_block read, granted
  or refused, is one audit line with via: mcp` (temp audit dir, count lines
  before and after four calls, expect exactly four, check `args.via`);
  `a Block read that cannot be audited does not happen` (same unwritable
  trick as section 5, expect `unaudited: true` and no `markdown`).
- **Verify:** `python3 tests/run_all.py` exits 0, every 0.1.0 name except
  the renamed one still listed as `ok`; `echo
  '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 vault/mcp_stub.py
  | grep -c sm_block` prints 1.
- **Built when:** verifies hold, `CONTRACT.md` updated per §3.4, committed
  as `Safe Memory V0.2 - sm_block: a Grant-checked, audited Block read`.
- **Done when:** built and the Verifier re-ran the gate on `master`.

### S3 - The shell   (wave 3, blocked by: S2)
- **Delivers:** `python3 shell/server.py` on `127.0.0.1:8765` renders the
  Block at `/`, with loading, empty, denied and error states, light and
  dark, 1440x900 and 390x844; Playwright flows F1 to F4 write their PNGs.
- **Files owned:** `shell/server.py`, `shell/index.html`, `shell/shell.js`,
  `shell/shell.css`, `tests/test_shell.py`, `e2e/playwright.config.js`
  (adds `webServer` and `globalSetup`), `e2e/global-setup.js`,
  `e2e/shell.spec.js`, `e2e/fixtures/empty/events.jsonl` (an empty file),
  `e2e/fixtures/empty/grants.json` (a copy of `fixtures/grants.json`).
- **Read first:** `vault/mcp_stub.py` (`refusal_payload`, `missing_payload`),
  `vault/store.py` (`block`), `e2e/helpers.js`, §3.5, §9.3.
- **Do:** per §3.5. `e2e/global-setup.js` runs, with `cwd` the repo root,
  `SAFE_MEMORY_FIXTURES=e2e/fixtures/empty python3 -m blocks.travel_log
  --out e2e/.tmp/empty/travel-log.md` and creates `e2e/.tmp/missing/`
  (both idempotent). `webServer` in the config becomes an array of four
  entries, each `command: 'python3 shell/server.py'`, `cwd: '..'`,
  `reuseExistingServer: false`, `timeout: 15000`, `url` on the port, and
  `env`:

  | Port | `SAFE_MEMORY_AGENT` | `SAFE_MEMORY_BLOCKS` | Proves |
  |---|---|---|---|
  | 8765 | `lazy` | unset (repo `blocks/`) | block, loading |
  | 8766 | unset | unset | denied (S4 uses it) |
  | 8767 | `lazy` | `e2e/.tmp/empty` | empty |
  | 8768 | `lazy` | `e2e/.tmp/missing` | error |

  `tests/test_shell.py` starts `shell/server.py` as a subprocess on a free
  port with a temp `SAFE_MEMORY_AUDIT` and checks, by name: `GET / is
  text/html with a main#block`; `the API returns the Block for lazy` (200,
  `block == "travel-log"`, `records == 3`, markdown starts with the header);
  `the API with no agent is a refusal, not data` (200, `denied`, body
  contains none of `Bariloche`, `Catedral`, `Nahuel`, `ev-fixture`);
  `the API for siri names the kinds it may not read`; `a missing Block is
  503 with missing: true`; `three reads are three audit lines with via:
  shell`; `an unwritable audit log refuses the read with unaudited: true`;
  `the shell binds 127.0.0.1 only` (startup line); `an unknown path is
  404 JSON`; `every response is Cache-Control: no-store`; `shell/server.py
  imports no network client and shells out to nothing`; `shell/server.py
  deletes nothing`; `shell/server.py opens nothing for writing`.
- **Verify:** `python3 tests/run_all.py` exits 0; `cd e2e && npx playwright
  test` prints `0 failed`; `ls docs/evidence/0.2.0/S3-*.png | wc -l`
  prints 16.
- **Built when:** verifies hold, committed as `Safe Memory V0.2 - The
  shell: one route, one Block, four states` (the PNGs are committed by the
  Verifier's run, see §9.3, not by the implementer).
- **Done when:** built and the Verifier's PNGs for F1 to F4 exist at their
  §9.3 paths, captured on `master`.

### S4 - Default deny, proven   (wave 4, blocked by: S3)
- **Delivers:** the three proofs of §3.6 as named tests and a browser flow
  with screenshots; audit line growth asserted from the real
  `audit/reads.jsonl`.
- **Files owned:** `tests/test_deny.py`, `e2e/deny.spec.js`.
- **Read first:** §3.6, `tests/test_shell.py`, `e2e/shell.spec.js`, §9.3 F5.
- **Do:** `tests/test_deny.py` checks, by name, over the real subprocesses
  with temp audit dirs: `the shell with no agent returns nothing and one
  refused audit line`; `the stub with no initialize returns nothing and one
  refused audit line`; `the stub as stranger returns nothing and one refused
  audit line`; `the refused audit line names no Record` (the line's JSON has
  no `markdown`, no `events` beyond the empty list, no `Bariloche`); `a
  granted Block read and a refused one are two lines, one allowed and one
  not`. `e2e/deny.spec.js` is F5 in §9.3.
- **Verify:** `python3 tests/run_all.py` exits 0; `cd e2e && npx playwright
  test deny.spec.js` prints `4 passed`; `ls docs/evidence/0.2.0/S4-F5-*.png
  | wc -l` prints 4.
- **Built when:** verifies hold, committed as `Safe Memory V0.2 - Default
  deny, proven`.
- **Done when:** built and the Verifier's F5 PNGs exist, captured on
  `master`, with the audit delta recorded in `PROGRESS.md`.

## 5. Agent orchestration

Assign by difficulty, not by length. Names as of September 2026; the roles
matrix for this project in `~/lazy/cody/roles.json` is: orchestrator fable,
builder sonnet, builder_lite haiku, verifier sonnet.

| Tier | Role in this 1Hit | Claude | OpenAI |
|---|---|---|---|
| **T1 judgment** | Orchestration, the §3.4 read-path review, final report | Fable 5.1 (the session), Opus 5 when the Fable pool is capped | gpt-6-astra |
| **T2 builder** | S1, S2, S3, S4 and both §9.4 reviewers | Sonnet 5 | gpt-5.6-terra |
| **Verifier** | Runs §9.2 and §9.3 after each wave on `master`, with only this file; never the implementer of the slice it verifies | Sonnet 5 | gpt-5.6-terra |
| **T3 mechanical** | S0's root files from §3.1, `.gitignore`, `CHANGELOG.md` and `README.md` edits in §8 | Haiku 4.5 | gpt-5.6-luna |
| **Explorer** | Read-only mapping when a builder needs a symbol found | Haiku 4.5, read-only tools | gpt-5.6-luna |

Rules:

- The orchestrator (T1) plans, dispatches, integrates and reviews. It does
  not implement slices itself.
- Every subagent gets this brief and nothing vaguer:

  ```
  Objective: {one sentence}
  Context pointers: docs/plans/1Hit - Safe Memory 0.2 - Shell and First Block.md §3.x, §4 Sx; commits; files to read first
  Files owned: {paths}. Touch nothing else. Never edit CLAUDE.md.
  Deliver: {code + tests | report under N words | screenshots at paths}
  Verify with: {command} expecting {output}
  Do not spawn further agents. Do not ask questions; pick the recommended
  option and note it in your report.
  ```
- Parallelize only across disjoint `Files owned`. Here every wave is one
  slice, so nothing runs in parallel except the two §9.4 reviewers.
- A subagent's "success" is a claim. The orchestrator re-runs the verify
  command and reads the diff before accepting it.
- Explorers, graders and the Verifier are read-only on code. Builders own
  their files. The Verifier's Playwright run writes only under
  `docs/evidence/0.2.0/` and `e2e/test-results/`.
- **No subagents in your harness:** you are every tier. Run one slice per
  context, and run the Verifier and both §9.4 reviewers in a cleared context
  that holds only this file and `master`.
- Cost rules: Max subscription only. No Anthropic API key, no per-token
  provider, no model run over user data at any point, including tests.

## 6. Long-run protocol

- **`PROGRESS.md`** at `/Users/agent/apps/memory/PROGRESS.md` is the task
  list and the resume point. It holds: `BASE`, baseline counts (`59 passed,
  0 failed`), each slice S0 to S4 with status (todo / doing / built / done /
  blocked), decisions taken, the one test rename, blockers with the failing
  output, and the audit line count before and after each Playwright run.
  Update it after every slice. Do not rely on the harness's todo tool. Keep
  the Cody flow's `## Definition of done` block intact if present.
- **Startup ritual on every start or restart:** read `PROGRESS.md`, then
  `git log --oneline -20`, then `git status --short`, then `python3
  tests/run_all.py` (or `python3 tests/test_stub.py` before S1 exists), then
  continue at the first unfinished slice. Every slice is idempotent: check
  state before creating.
- **One slice per context.** Clear or compact between slices. Before
  compacting, write the checkpoint into `PROGRESS.md`: objective,
  outstanding criteria, current revision, blockers, pending agents, test
  commands, changed assumptions (this is the checkpoint `CLAUDE.md` asks
  for).
- **Rate limits are pauses, not failures.** Checkpoint `PROGRESS.md`, wait,
  retry. Never exit because of a limit.
- **Stop conditions:** all §10 items green and every built slice committed on
  `master`; or a blocker that no fallback in §11 covers, documented in
  `PROGRESS.md` with what was attempted, with every other slice already
  committed per §0 item 7.

## 7. Git

1. On first start: `git status --short` shows only the two pre-existing
   `graphify-out/` entries from §1. Do not revert them, do not stage them
   until §8. On a restart, unpushed commits on `master` are expected;
   continue.
2. **Default: commit straight to `master`.** No feature branch, no PR. There
   is no remote, so no push happens; the report says `VERIFIED_LOCAL` and
   lists the push as blocked by the missing remote (§11). Never run `gh repo
   create`, never `git remote add`: creating the remote is GB's action.
3. One atomic commit per slice, staged by explicit paths, never `git add -A`.
   Message format: `Safe Memory V0.2 - {Title}` (from `git log`, the
   repo writes `Safe Memory V0.1 - ...`).
4. If a remote appears mid-run (GB ran `gh repo create` per §11), push every
   commit on `master` with `git push -u origin master`. If that push is
   rejected by branch protection, switch to a branch `0.2-shell-and-first-
   block`, note in `PROGRESS.md` and the report which commits are where, and
   open a PR per item 6.
5. A slice that fails its retry budget (§0 item 7) is never committed. Its
   failure is documented in `PROGRESS.md` and the report; every other slice
   still commits to `master`.
6. **Only when a branch/PR workflow is in force (item 4):** PR against
   `master`, title `0.2-Shell and First Block`, body: Summary and status;
   changes per slice with key files; Requirements addressed; Verification
   (commands, outputs, screenshots); Decisions taken; Pending. No PR template
   exists. Once §10 is green, merge it yourself unless required reviews make
   that impossible; then say so as a technical constraint.
7. If §9.4 review finds a defect after slices are committed, fix it in a new
   commit. Never rewrite history to hide a mistake; say what happened in the
   report. After §8's changelog, version, docs and graph edits, make one
   final commit `Safe Memory V0.2 - Shell and First Block shipped: changelog,
   VERSION 0.2.0, docs, graph`.
8. Never fake a push or a deploy. `VERIFIED_LOCAL` is the honest word.

## 8. Changelog, version, docs

- Create `CHANGELOG.md` (none exists, say so in the report) with
  `## v0.2.0 - <date shipped>` on top listing the five slices in one line
  each, then `## v0.1.0 - 2026-09-15` backfilled from the five 0.1 commits
  (`git log --oneline`, dates from `git log --format='%ad %s' --date=short`).
- Bump `VERSION` to `0.2.0`. `CONTRACT.md` header already says 0.2.0 from S2.
- Update `README.md`: the two commands block becomes the six lines from
  §3.1; the "Today this repository is SM-0" paragraph says 0.2 adds a Travel
  Log Block computed by code, a seventh tool `sm_block` and a local shell,
  still on fixtures; the roadmap paragraph is replaced by the table 0.2, 0.3
  Apple Photos connector, 0.4 the five Alpha V1 Blocks, 0.5 Artifacts, 0.6
  Onboarding, 1.0 Alpha V1 done (canon says Strategy V2's order is on Hold
  and the file is fixed when next touched; this is that touch). Keep "No
  dependencies. No network client. Nothing here deletes." and add "Playwright
  lives in `e2e/`, Node only, and is never imported by Python."
- Regenerate `blocks/travel-log.md` with `python3 -m blocks.travel_log` so
  the shipped file is from the shipped day.
- Rebuild the graph: `graphify update --no-label` (never `extract` or
  `label`). Stage `graphify-out/graph.json`. Leave
  `graphify-out/cody-manifest.json` untracked; it is the Cody flow's.
- Commit the evidence directory `docs/evidence/0.2.0/` (20 PNGs plus the
  Playwright JSON results copied as `docs/evidence/0.2.0/playwright-results.json`
  and the gate output as `docs/evidence/0.2.0/run_all.txt`).

## 9. Verification: everything you touch, you prove

### 9.1 Evidence law
Every "done" in this file resolves to a command, its exit code or output, and
an artifact path where relevant. Record what ran and what it returned, never
what you hoped happened. If something was not verified, the report says
"unverified", with the reason.

### 9.2 Automated gates (green before every commit)

```bash
python3 tests/run_all.py                       # exit 0, TOTAL: N passed, 0 failed, N > 59
python3 -m blocks.travel_log && git diff --quiet blocks/travel-log.md   # the committed Block is the computed Block
cd e2e && npx playwright test                  # 0 failed (from S3 on; smoke only before)
```

- Unit and contract, by name, at the seams named in §3: the S1, S2, S3 and
  S4 lists in §4. Every 0.1.0 test name keeps passing except the one rename.
- Integration: the stub over a real subprocess (`tests/test_stub.py`
  convention), the shell over a real HTTP subprocess (`tests/test_shell.py`),
  both with temp audit dirs.
- Red before green: write the failing test first, then the minimum to pass.
- A failing test gets fixed. It is never skipped, commented out or loosened.
- The no-network, no-delete and single-write-target greps from
  `tests/test_stub.py` section 6 are applied to `blocks/travel_log.py`
  (write target `out_path`) and `shell/server.py` (no write target at all).

### 9.3 Browser proof (mandatory for anything a user sees)
Driver: the repo's own Playwright project in `e2e/` (created in S0;
`@playwright/test` 1.60.0, chromium). BrowserOS neo is allowed for a human
look, never as evidence. Evidence dir: `docs/evidence/0.2.0/`, committed.
Run by the Verifier on `master` once every slice of the wave is either
committed or logged as blocked in `PROGRESS.md`, never by the slice's
implementer. The Verifier runs `cd e2e && npx playwright test` from a fresh
context; the specs themselves save the PNGs through `helpers.shot`, so the
paths below are produced by the run, not by hand. Before the run the Verifier
records `wc -l audit/reads.jsonl` in `PROGRESS.md`; after the run, again.

Every flow runs under the four projects, so each produces four PNGs:
`1440x900-light`, `1440x900-dark`, `390x844-light`, `390x844-dark`. Every
flow asserts `consoleErrors(page)` is empty at the end.

**F1 - The Block renders** (slice S3, `e2e/shell.spec.js`, port 8765)
- Steps: 1. `goto http://127.0.0.1:8765/`. 2. wait for
  `main#block[data-state="block"]`. 3. assert `main h2` text is `Travel Log`,
  `main h3` text is `Bariloche, Rio Negro`, `main li` count is 5, the page
  text contains `Cerro Catedral`, `Lago Nahuel Huapi`, `ev-fixture-0012`,
  and `#agent` text is `agent: lazy`. 4. assert `main .meta` text starts
  with `Computed by code from 3 records`. 5. no horizontal scroll:
  `document.documentElement.scrollWidth <= window.innerWidth`.
- Must hold: the Block from §3.3 is visible, with the record ids; zero
  console errors.
- Screenshots: `docs/evidence/0.2.0/S3-F1-{viewport}-{theme}.png`.

**F2 - Loading state** (slice S3, port 8765)
- Steps: 1. `page.route('**/api/block/travel-log', ...)` delaying
  `route.continue()` by 2500 ms. 2. `goto /`. 3. within 500 ms assert
  `main#block[data-state="loading"]` is visible and its text is `Reading the
  Travel Log`. 4. screenshot. 5. wait for state `block` (timeout 10 s).
- Must hold: the loading copy is shown before data arrives; the Block
  follows; zero console errors.
- Screenshots: `docs/evidence/0.2.0/S3-F2-{viewport}-{theme}.png`.

**F3 - Empty state** (slice S3, port 8767)
- Steps: 1. `goto http://127.0.0.1:8767/`. 2. wait for state `empty`.
  3. assert text `No trips in your records yet.` and `This one found 0
  records.`; assert no `li` in `main`.
- Must hold: an empty Block is a calm page, not an error; zero console
  errors.
- Screenshots: `docs/evidence/0.2.0/S3-F3-{viewport}-{theme}.png`.

**F4 - Error state and retry** (slice S3, port 8768)
- Steps: 1. `goto http://127.0.0.1:8768/`. 2. wait for state `error`.
  3. assert `main h2` is `The Block could not be read` and `main .reason`
  contains `not computed`. 4. screenshot. 5. click `#retry`; assert state
  passes through `loading` and settles on `error` again within 5 s.
- Must hold: a missing Block is an error state with the store's reason, and
  Retry re-reads; zero console errors (a 503 response logs no console error
  because the fetch resolves; a failed assertion here is a bug in the page).
- Screenshots: `docs/evidence/0.2.0/S3-F4-{viewport}-{theme}.png`.

**F5 - Default deny, no data leaked** (slice S4, `e2e/deny.spec.js`, port 8766)
- Steps: 1. read `audit/reads.jsonl` line count `before` with Node `fs`
  (0 if absent). 2. `goto http://127.0.0.1:8766/`. 3. wait for state
  `denied`. 4. assert `main h2` is `Nothing to show`, `main .reason` contains
  `has no grant`, `#agent` text is `agent: none`, and the full page text
  contains none of `Bariloche`, `Catedral`, `Nahuel`, `ev-fixture`. 5.
  `request.get('http://127.0.0.1:8766/api/block/travel-log')` and assert the
  JSON has `denied: true`, `count: 0` and no `markdown` key. 6. read the line
  count `after`; assert `after - before === 2` and that the last line parses
  to `allowed: false`, `agent: ""`, `tool: "sm_block"`, `args.via: "shell"`.
- Must hold: nothing from any Record reaches the DOM or the JSON; two reads,
  two refused audit lines; zero console errors.
- Screenshots: `docs/evidence/0.2.0/S4-F5-{viewport}-{theme}.png`.

Each flow is deterministic, agent-runnable and asserts the exact behaviour
from §3, not "page loads". No HITL is needed anywhere in this version.

### 9.4 Independent review (after the last wave, before §8)
Two T2 reviewers, fresh context, in parallel; neither sees the other's report:

- **Spec axis:** given `git diff $BASE..HEAD` and this file, report (a)
  requirements in §3 missing or partial, (b) behaviour in the diff nobody
  asked for, (c) requirements that look done but are wrong. Quote the §3
  sentence for each finding. Under 400 words.
- **Standards axis:** given the diff and repo law (`CLAUDE.md`,
  `CONTRACT.md`, §0 item 5), report violations of the invariants, especially:
  any place the agent identity could come from a request; any read path that
  returns data before its audit line; any write open outside the audit log
  and the Block file; any import outside the standard library in Python;
  any `innerHTML` of unescaped text in `shell.js`; any deletion. Flag only
  what affects correctness or the stated requirements.

Fix every finding, re-run §9.2 and §9.3, then proceed. The implementer of a
slice never reviews that slice.

### 9.5 Scope check
`git diff --stat $BASE..HEAD` (`BASE` read from `PROGRESS.md`) lists only
files owned by slices in §4, plus `PROGRESS.md`, `CHANGELOG.md`, `VERSION`,
`README.md`, `graphify-out/graph.json`, `.gitignore` and `docs/evidence/0.2.0/`.
`CLAUDE.md` never appears. Any other file is explained in the report or
reverted.

## 10. Acceptance criteria

### Feature criteria (each false at `BASE`, provable by command or artifact)
- [ ] The test suite is green above the 0.1.0 baseline: `python3 tests/run_all.py` exits 0 and prints `TOTAL: N passed, 0 failed` with N greater than 59, and every 0.1.0 test name except `tools/list answers exactly the six contract tools` still prints `ok` - proof: `docs/evidence/0.2.0/run_all.txt` (at `BASE` there is no `tests/run_all.py` and 59 is the count)
- [ ] `blocks/travel-log.md` exists, is generated, never hand-written - proof: `python3 -m blocks.travel_log && git diff --quiet blocks/travel-log.md && head -1 blocks/travel-log.md` prints `<!-- generated by blocks/travel_log.py; never edit by hand -->` and exits 0 (at `BASE` the file does not exist)
- [ ] `sm_block` returns the Block over MCP for `lazy` and refuses `siri`, `stranger` and an unidentified client - proof: `python3 tests/test_stub.py` lists the S2 names in §4 as `ok` (at `BASE` `sm_block` is `-32602 unknown tool`)
- [ ] The shell renders the Block at 1440x900 dark - proof: screenshot `docs/evidence/0.2.0/S3-F1-1440x900-dark.png` shows `Travel Log`, `Bariloche, Rio Negro` and three record rows in the dark palette (at `BASE` there is no `shell/`)
- [ ] The shell's loading, empty and error states exist in light and dark, desktop and mobile - proof: screenshots `docs/evidence/0.2.0/S3-F2-*.png`, `S3-F3-*.png`, `S3-F4-*.png`, four each, and `cd e2e && npx playwright test shell.spec.js` prints `0 failed`
- [ ] Default deny is proven with no data leaked - proof: screenshot `docs/evidence/0.2.0/S4-F5-1440x900-dark.png` shows `Nothing to show` and no place, title or id from any Record; `cd e2e && npx playwright test deny.spec.js` prints `4 passed`
- [ ] `audit/reads.jsonl` gains one line per read, granted or denied, from the shell and from MCP - proof: `python3 tests/test_deny.py` and `python3 tests/test_shell.py` list the audit names in §4 as `ok`; `PROGRESS.md` records the real `wc -l audit/reads.jsonl` before and after the Verifier's Playwright run with a delta equal to the number of reads the flows make

### Gates
- [ ] Passing tests at end >= 59, and by name: `python3 tests/run_all.py` exit 0 with every 0.1.0 name still `ok` apart from the single documented rename
- [ ] Playwright green: `cd e2e && npx playwright test` prints `0 failed`, 20 tests under four projects plus the smoke test
- [ ] `ls docs/evidence/0.2.0/*.png | wc -l` prints 20, one PNG per §9.3 flow, viewport and theme, captured by the Verifier on `master`
- [ ] Both §9.4 reviewers clear; §9.5 scope check clean, `CLAUDE.md` untouched: `git diff --stat $BASE..HEAD -- CLAUDE.md` prints nothing
- [ ] `VERSION` prints `0.2.0`, `CHANGELOG.md` opens with `## v0.2.0`, `CONTRACT.md` header says 0.2.0, `README.md` roadmap matches §8
- [ ] All built slices committed on `master`, `git status --short` shows only `graphify-out/cody-manifest.json`; `PROGRESS.md` final; report says `VERIFIED_LOCAL`

## 11. Known blockers and pending decisions

- **No git remote.** `git remote -v` prints nothing (2026-09-20). Meanwhile:
  commit every slice on `master`, log every push as blocked, report
  `VERIFIED_LOCAL`. Human action: GB runs `cd ~/apps/memory && gh repo create
  gonzalo-b/safe-memory --private --source=. --remote=origin --push` (Master
  Brief decision 9, `Memory - Cody Setup.md` §1.3), or tells Cody to. Never
  run it from this session. Not needed for 0.2; needed before 0.3.
- **Chromium download.** If `npx playwright test smoke.spec.js` reports a
  missing browser and `npx playwright install chromium` cannot reach the
  network, S0 is blocked and so is every browser proof. Meanwhile: finish
  S1 and S2 (no browser), commit them, mark S0, S3, S4 blocked in
  `PROGRESS.md` with the install output. Human action: GB restores network
  or runs the install on macserver. Today the cache holds chromium builds
  1223 and 1234, so this is unlikely.
- **Decision for GB to confirm (not a blocker):** a Block read is governed by
  the grant's kinds and expiry only; window and redactions are not applied
  to Blocks in 0.2 (§3.4). If GB wants per-reader Blocks, that is a 0.4
  change to `blocks/` and `store.block`.

## 12. Final report (format of delivery)

1. **Done** - by slice, in bullets.
2. **Evidence** - table: criterion | command | result | artifact. Then
   `git log --oneline $BASE..HEAD` on `master` and the word `VERIFIED_LOCAL`
   with the reason (no remote). Then `git diff --stat $BASE..HEAD` with
   `BASE` from `PROGRESS.md`. Then the audit line counts before and after
   the Verifier's run.
3. **Decisions I made** - each ambiguity resolved alone, with the criterion.
   Include the test rename and the Block read semantics from §3.4. Mark the
   ones a human should confirm.
4. **Unverified** - anything not proven, and why.
5. **Unresolved** - what is missing, why, and the concrete human action that
   unblocks it (the remote, per §11).
6. **Risks and rollback** - what can break locally and the exact revert:
   `git revert` of the listed commits in reverse order; nothing runs under
   PM2, nothing listens after the session ends, `audit/reads.jsonl` is
   append-only and is never touched by a rollback.
7. **Handoff** - what 0.3 (Apple Photos connector) should know: where the
   Block registry lives, how a Block is served, how the shell finds its
   agent, and which fixture assumptions (day offsets) shift daily.

Be literal. If something was not tested, say so. If a test is red, paste its
output.

## 13. Executor adapters (optional; the core never depends on these)

| Executor | Use |
|---|---|
| Claude Code, interactive (this run, `cody:memory-0.2`) | First message from the flow: read `.cody/seed-memory-0.2.md`, then this file, execute end to end. `/goal every §10 item holds, with evidence recorded in PROGRESS.md`. `/code-review` covers the standards axis. `/clear` between slices. Dispatch slices with the Agent tool, `model` per §5 tier; no worktrees needed since waves are serial. |
| Claude Code, headless | `claude -p --permission-mode bypassPermissions --max-turns 200`. Same run order. |
