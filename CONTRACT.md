# Safe Memory — the contract

Version **0.1.0** (SM-0, the contract stage). Status: **stub**. Every row this
server returns today comes from `fixtures/` and is stamped `fixture: true`.
Nothing in this repository has ever read GB's real accounts.

This file is the whole agreement between Safe Memory and everything that asks
it questions. MindBase's client (`daemons/providers/safe_memory.py`) is written
against this file and nothing else; when SM-1 replaces the fixture loaders with
an encrypted store, this file does not change.

---

## 1. The boundary

**Safe Memory answers what happened in GB's life.** What he bought, what he
watched, what he listened to, where he was, how he slept.

**MindBase answers what he is building and what is next.** Ideas, plans,
projects, threads.

Neither stores the other's half. They cross-reference by id: a MindBase idea
may cite an event, and an event may carry `project_ref`. That field is written
by MindBase, never inferred here.

The practical consequence for a caller: asking Safe Memory for an idea returns
nothing, and it is not a bug. Ask MindBase.

---

## 2. Transport

MCP over **stdio**: newline-delimited JSON-RPC 2.0 on stdin and stdout, one
JSON object per line, the transport `claude mcp add`, `codex mcp add` and
MindBase's own client already speak.

Three methods are implemented. Anything else answers JSON-RPC `-32601`.

| Method | Behaviour |
|---|---|
| `initialize` | Returns `protocolVersion`, `serverInfo`, and `instructions`. **Records the calling agent** from `params.clientInfo.name`. |
| `tools/list` | The six tools of §4, each with a JSON Schema for its arguments. |
| `tools/call` | Runs one tool. `params.name`, `params.arguments`. |

An unknown tool name answers `-32602`. A **refusal is a result, not a transport
error**: a well-formed question the agent may not ask comes back as a normal
`tools/call` result with `isError: true` and a `structuredContent` body
carrying `denied: true` and a `reason`, so an agent can say out loud why it has
no answer.

Every `tools/call` result carries both shapes: `content[0].text` is the JSON as
text for clients that only read text, and `structuredContent` is the same
object parsed, for clients that do better.

**Not in SM-0:** the HTTP transport. §C2 of the MindBase V6 Plan puts the real
server under PM2 as `safe-memory-mcp` behind the tunnel path `/sm`; that is
SM-1's work and it adds a transport beside this one rather than replacing it.
Nothing in this repository listens on a port today.

---

## 3. Identity and grants

**The calling agent is taken from the MCP client identity, never from a tool
argument.** An agent that could name itself in a call could name itself into a
wider grant. `SAFE_MEMORY_AGENT` in the server's environment is the only other
source, and it exists for a one-shot shell call.

A client that never sent `initialize` has no identity, and an agent with no
identity reads nothing.

A **grant** (`schema/grant.json`) says what one agent may read:

```json
{"agent": "siri", "kinds": ["purchase", "watch", "listen"], "window_days": 7,
 "expires": null, "fields_redacted": ["amount", "currency"]}
```

- **There is no implicit grant.** An agent GB has not named reads nothing.
- `kinds` is intersected with what the call asked for. An empty intersection is
  a refusal that names the kinds.
- `window_days` is a floor on `ts`, counted back from the read and rounded down
  to local midnight. A call asking for more is **not** an error: it is silently
  clipped, and the clip is in the audit line.
- `expires` in the past means the grant is gone. Revocation by GB is the only
  other end.
- `fields_redacted` are removed before the agent sees the row. `location` is the
  one special case: redacting it keeps `place` and drops the coordinates,
  because a town is an answer and a point is a tracker.

Shipped defaults (`fixtures/grants.json`): `lazy` reads every kind for 90 days;
`siri` reads purchases and media for 7 days with amounts stripped, because a
Siri answer is spoken in a room that may have other people in it.

**Every read is one append-only audit line**, refusals included, at
`audit/reads.jsonl` (override with `SAFE_MEMORY_AUDIT`). The line carries the
timestamp, agent, tool, the arguments that were not null, whether it was
allowed, how many rows came back, and the reason when it was not.

---

## 4. The six tools

All read-only. All grant-checked. All audited.

| Tool | Arguments | Answers |
|---|---|---|
| `sm_search` | `query` (required), `kinds[]`, `since`, `until`, `limit` | Free text across every kind the agent may read |
| `sm_timeline` | `date` (required), `limit` | One local day: purchases, media, places |
| `sm_purchases` | `query`, `since`, `until`, `source`, `limit` | What did we order, what do I own |
| `sm_media` | `query`, `since`, `until`, `kind` (`video`\|`music`), `limit` | What did I watch or listen to |
| `sm_photos` | `query`, `place`, `since`, `until`, `limit` | Where was I, when — **metadata only** |
| `sm_grants` | — | What **this** agent may read, and until when |

`sm_media` maps `kind: video` to the `watch` event kind and `kind: music` to
`listen`; omitting it spans both. `sm_photos` spans `photo` and `place`. No
tool ever returns an image, an audio file, or a raw export: `media_ref` is a
provider-native identifier and `raw_ref` points into an encrypted file that
never leaves the machine.

`sm_grants` reports the caller's own grant and no one else's. The roster is
GB's, not a readable resource.

A successful call returns:

```json
{"events": [ ... ], "count": 3, "agent": "lazy", "stub": true}
```

`stub: true` is present for as long as this server answers from fixtures. SM-1
drops it, and a client that wants to know whether it is talking to real data
should read it rather than guess.

---

## 5. The event

One shape for every source (`schema/event.json`, `additionalProperties:
false`). Required: `id`, `kind`, `source`, `ts`, `title`.

```json
{
  "id": "ev-20260903-x9k2",
  "kind": "purchase",
  "source": "mercadolibre",
  "ts": "2026-09-02T18:40:00-03:00",
  "title": "Cafetera Oster",
  "entities": ["Oster", "cocina"],
  "amount": 18999900, "currency": "ARS",
  "location": {"lat": null, "lon": null, "place": null},
  "media_ref": null,
  "raw_ref": "connectors/mercadolibre/raw/2026-09-02.json#order-123",
  "project_ref": null
}
```

- `kind` is a **closed** vocabulary: `purchase`, `watch`, `listen`, `photo`,
  `place`, `health`. A grant is written in these words, so adding one is a
  contract change.
- `ts` is local, with its offset, and is never UTC-normalised. "What did I buy
  yesterday" is a local-day question.
- `amount` is an **integer in minor units** (ARS centavos, USD cents) with
  `currency` beside it. Money is never a float here.
- `raw_ref` is how a claim is audited back to the export that produced it.
- `fixture: true` marks a stub row. The real store never sets it.

---

## 6. Fixtures (SM-0 only)

`fixtures/events.jsonl` is thirteen events across all six kinds and five
sources. A fixture row may carry `day_offset` + `time` instead of `ts`, and the
store resolves them against the local clock at load. It has to: "what did we
buy yesterday" is the question this stub exists to answer, and a frozen
timestamp stops answering it the day after it is written. The resolved row is
stamped `fixture: true` so nothing downstream can mistake it for a recording.

`day_offset` and `time` are **fixture-only** keys. They are not in
`schema/event.json` and the real store will never see one.

---

## 7. What SM-1 changes, and what it does not

Changes: the two loaders in `vault/store.py` (`load_events`, `load_grants`)
read an SQLCipher database instead of `fixtures/`; the `stub: true` key
disappears; an HTTP transport is added beside stdio; `connectors/` appears with
the first importer.

Does not change: the six tool names and their arguments, the event shape, the
grant shape, the identity rule, the window-clip rule, the redaction rule, the
audit line. **Every rule about what an agent may see already lives in
`vault/store.py`, not in the transport**, precisely so it survives the storage
swap untouched.

A client written against this file today keeps working.

---

## 8. Repository

```
CONTRACT.md            this file
VERSION                0.1.0
schema/event.json      the event shape
schema/grant.json      the grant shape
vault/store.py         grant check, window clip, redaction, audit, query
vault/mcp_stub.py      stdio JSON-RPC, the six tools
fixtures/              events.jsonl, grants.json
tests/test_stub.py     the contract, asserted over the real transport
```

Standard library only, no dependencies, no network client anywhere —
`tests/test_stub.py` greps for one on every run. Nothing here deletes.

Run the tests: `python3 tests/test_stub.py` (exit 0 is pass).

This repository has **no git remote**. Creating `gonzalo-b/safe-memory` on
GitHub is GB's step (MindBase V6 1Hit §11 Q2); until then it is a local
repository and says so.
