# Chat Workflow installation evidence

Status: DELIVERED. PR #1 merged to main by Codex after exact-SHA checks,
without Pro. The initial capability findings below are historical; completion
receipt and resolved delivery policy are in DELIVERY.md.
The original checkout's uncommitted product work is preserved, not certified.

- Tested candidate: `2f85ac474762b524966ec4e5b6a479ebe358a6fe`.
- Base: `de9dfe153e7adec461bc36474cebac505359fcf8`.
- Plan: `~/base/projects/memory/docs/Plan - Chat Workflow.md`.
- Plan SHA256: `0abf0445c3999e50eab5d6767c28f677af4e9b6dcf521d075e016e8675c3069f`.
- Isolated checkout: `/Users/agent/apps/memory-chat-workflow`.
- Activated checkout: `/Users/agent/apps/memory`.
- Product VERSION remains 0.1.0; unfinished 0.2 not released.
- PR: https://github.com/gonzalo-b/safe-memory/pull/1.

| Criterion | Result | Evidence |
|---|---|---|
| A1 Paths and precedence | VERIFIED | Skill/probe distinguish app, planning and newer approved GB decisions. |
| A2 Astra High | VERIFIED | RUNTIME.md: effective config; functional subagent launched explicitly on Astra High. Existing task overrides remain possible. |
| A3 Skill discovered and invoked | VERIFIED | app-server skills/list finds exactly one enabled repo skill; PROBE.md records actual invocation. |
| A4 Isolation | VERIFIED | INVENTORY.md hashes for seven pre-existing files plus canon unchanged; local fast-forward preserved dirty product paths. |
| A5 Gates | VERIFIED | Candidate aggregate 73 / contract 59, exit 0; all previous passing names identical. Logs below. |
| A6 Resume | VERIFIED | Fresh-context subagent reconstructed objective, revision, protected work and next action from checkpoint. |
| A7 Honest evidence | VERIFIED | Probe rejected older-revision proof and pending tests; no fabricated PASS or required reviewer. |
| A8 Idempotence | VERIFIED | RUNTIME.md: repeated forced reads and file comparison find desired state; no duplicate skill/job. |
| A9 Filing | VERIFIED | MindBase returned Chat Workflow - Usage.md and superseded Cody Setup path; final digest recorded at closure. |
| A10 Delivery | VERIFIED | PR #1 merged to main as d50f454 after 76 aggregate / 59 contract checks; merged tree equals tested HEAD. See DELIVERY.md. |

## Configuration and skill validation

`quick_validate.py .agents/skills/memory-workflow` using the existing MindBase
venv Python: exit 0, `Skill is valid!`. System and bundled Python lacked PyYAML;
no dependency was added to Safe Memory or globally. Local test runners use
standard-library Python. Codex login reported ChatGPT authentication.

## Source privacy inspection

Tracked history has no credential-pattern matches in the bounded private-key,
GitHub-token and API-key scan; this is not a comprehensive security audit.
Audit and raw data paths are ignored, not published. Source fixtures use
`ev-fixture-*` IDs; `fixture: true` is stamped by `_resolve_fixture_row` at
read time and tested by the contract, not stored directly on raw fixture rows.
An initial assumption that raw rows carry that flag was corrected before delivery.

## GitHub capability result

Private repo created under authenticated gonzalo-b. Base committed history
pushed to master. Actions explicitly disabled; no hosted runners or charges.
Branch protection PUT returned HTTP 403: "Upgrade to GitHub Pro or make this
repository public to enable this feature." Setting allow_auto_merge=true did
not enable it. No upgrade or visibility change attempted.

Actual local test results were published as `memory/gate` and `memory/contract`
commit statuses on the candidate SHA. These are not GitHub-hosted CI runs, and
without protection GitHub does not enforce them. No negative test can honestly
prove a protection that GitHub refused to provide. The independent behavioral
probe verifies procedural refusal of missing/wrong-revision evidence only.

## Baseline and candidate test output

### baseline-all

Exit 0. Command: `python3 tests/run_all.py`

```text

### tests/test_blocks.py ###
== the Travel Log Block ==
  ok   first two lines exact
  ok   records: 3 with the shipped fixtures
  ok   one ## Bariloche, Rio Negro heading
  ok   three record rows in ts order carrying the three ids
  ok   Days: line spans two dates
  ok   2 photos, 1 place
  ok   two consecutive compute() calls are byte-identical
  ok   compute([]) equals the empty text in §3.3
  ok   write() to a temp path produces a file equal to compute() of the store's events
  ok   the committed blocks/travel-log.md starts with the generated header line
  ok   the committed blocks/travel-log.md contains records: 3 and the Bariloche heading
  ok   blocks/travel_log.py imports no network client and shells out to nothing
  ok   blocks/travel_log.py deletes nothing
  ok   blocks/travel_log.py opens exactly one path for writing, named out_path

14 passed, 0 failed

### tests/test_stub.py ###
== schemas ==
  ok   event.json parses
  ok   event.json declares $schema and $id
  ok   event.json lists required fields
  ok   grant.json parses
  ok   grant.json declares $schema and $id
  ok   grant.json lists required fields
  ok   event schema closes additionalProperties
  ok   grant schema requires agent, kinds and window_days

== protocol ==
  ok   server exits 0 when stdin closes
  ok   initialize returns a protocolVersion
  ok   initialize names the server
  ok   initialize instructions say the rows are a stub
  ok   initialize instructions state the boundary rule
  ok   tools/list answers exactly the six contract tools
  ok   every tool declares an inputSchema
  ok   every tool declares a description
  ok   an unknown method is -32601
  ok   an unknown tool is -32602

== the six tools answer ==
  ok   sm_purchases returns events
  ok   sm_purchases returns only purchases
  ok   every row is stamped fixture: true
  ok   every row carries only schema'd fields
  ok   every kind is in the schema's enum
  ok   'what did we buy yesterday' has an answer today and every other day
  ok   a purchase carries an integer amount in minor units
  ok   sm_timeline is one local day only
  ok   sm_timeline crosses kinds
  ok   sm_media kind=music is listens only
  ok   sm_media with no kind spans watch and listen
  ok   sm_photos filters by place
  ok   sm_search finds a title
  ok   sm_search finds an entity
  ok   a search with no hits is an empty list, not an error

== grants are the whole point ==
  ok   sm_grants reports the calling agent's grant
  ok   the lazy grant is 90 days
  ok   the siri grant is narrower
  ok   the siri grant redacts amounts
  ok   sm_grants never reports another agent's grant
  ok   siri sees purchases
  ok   siri never sees an amount
  ok   the siri window clips the 40-day-old purchase
  ok   siri is refused a kind it was not granted
  ok   the refusal says why and returns nothing
  ok   an agent with no grant reads nothing
  ok   the no-grant refusal names the agent
  ok   a client that never identified itself reads nothing
  ok   an agent cannot widen its grant through a tool argument

== every read leaves a line ==
  ok   the audit log exists after a read
  ok   an allowed read is audited
  ok   a REFUSED read is audited too
  ok   every audit line carries a timestamp and a count
  ok   a read that cannot be audited does not happen
  ok   and the caller is told it was the audit, not the grant

== a memory vault that cannot phone out ==
  ok   vault/store.py imports no network client and shells out to nothing
  ok   vault/mcp_stub.py imports no network client and shells out to nothing
  ok   vault/store.py deletes nothing
  ok   vault/mcp_stub.py deletes nothing
  ok   vault/store.py opens nothing for writing except the audit log
  ok   vault/mcp_stub.py opens nothing for writing except the audit log

59 passed, 0 failed

TOTAL: 73 passed, 0 failed
```

### baseline-contract

Exit 0. Command: `python3 tests/test_stub.py`

```text
== schemas ==
  ok   event.json parses
  ok   event.json declares $schema and $id
  ok   event.json lists required fields
  ok   grant.json parses
  ok   grant.json declares $schema and $id
  ok   grant.json lists required fields
  ok   event schema closes additionalProperties
  ok   grant schema requires agent, kinds and window_days

== protocol ==
  ok   server exits 0 when stdin closes
  ok   initialize returns a protocolVersion
  ok   initialize names the server
  ok   initialize instructions say the rows are a stub
  ok   initialize instructions state the boundary rule
  ok   tools/list answers exactly the six contract tools
  ok   every tool declares an inputSchema
  ok   every tool declares a description
  ok   an unknown method is -32601
  ok   an unknown tool is -32602

== the six tools answer ==
  ok   sm_purchases returns events
  ok   sm_purchases returns only purchases
  ok   every row is stamped fixture: true
  ok   every row carries only schema'd fields
  ok   every kind is in the schema's enum
  ok   'what did we buy yesterday' has an answer today and every other day
  ok   a purchase carries an integer amount in minor units
  ok   sm_timeline is one local day only
  ok   sm_timeline crosses kinds
  ok   sm_media kind=music is listens only
  ok   sm_media with no kind spans watch and listen
  ok   sm_photos filters by place
  ok   sm_search finds a title
  ok   sm_search finds an entity
  ok   a search with no hits is an empty list, not an error

== grants are the whole point ==
  ok   sm_grants reports the calling agent's grant
  ok   the lazy grant is 90 days
  ok   the siri grant is narrower
  ok   the siri grant redacts amounts
  ok   sm_grants never reports another agent's grant
  ok   siri sees purchases
  ok   siri never sees an amount
  ok   the siri window clips the 40-day-old purchase
  ok   siri is refused a kind it was not granted
  ok   the refusal says why and returns nothing
  ok   an agent with no grant reads nothing
  ok   the no-grant refusal names the agent
  ok   a client that never identified itself reads nothing
  ok   an agent cannot widen its grant through a tool argument

== every read leaves a line ==
  ok   the audit log exists after a read
  ok   an allowed read is audited
  ok   a REFUSED read is audited too
  ok   every audit line carries a timestamp and a count
  ok   a read that cannot be audited does not happen
  ok   and the caller is told it was the audit, not the grant

== a memory vault that cannot phone out ==
  ok   vault/store.py imports no network client and shells out to nothing
  ok   vault/mcp_stub.py imports no network client and shells out to nothing
  ok   vault/store.py deletes nothing
  ok   vault/mcp_stub.py deletes nothing
  ok   vault/store.py opens nothing for writing except the audit log
  ok   vault/mcp_stub.py opens nothing for writing except the audit log

59 passed, 0 failed
```

### candidate-all

Exit 0. Command: `python3 tests/run_all.py`

```text

### tests/test_blocks.py ###
== the Travel Log Block ==
  ok   first two lines exact
  ok   records: 3 with the shipped fixtures
  ok   one ## Bariloche, Rio Negro heading
  ok   three record rows in ts order carrying the three ids
  ok   Days: line spans two dates
  ok   2 photos, 1 place
  ok   two consecutive compute() calls are byte-identical
  ok   compute([]) equals the empty text in §3.3
  ok   write() to a temp path produces a file equal to compute() of the store's events
  ok   the committed blocks/travel-log.md starts with the generated header line
  ok   the committed blocks/travel-log.md contains records: 3 and the Bariloche heading
  ok   blocks/travel_log.py imports no network client and shells out to nothing
  ok   blocks/travel_log.py deletes nothing
  ok   blocks/travel_log.py opens exactly one path for writing, named out_path

14 passed, 0 failed

### tests/test_stub.py ###
== schemas ==
  ok   event.json parses
  ok   event.json declares $schema and $id
  ok   event.json lists required fields
  ok   grant.json parses
  ok   grant.json declares $schema and $id
  ok   grant.json lists required fields
  ok   event schema closes additionalProperties
  ok   grant schema requires agent, kinds and window_days

== protocol ==
  ok   server exits 0 when stdin closes
  ok   initialize returns a protocolVersion
  ok   initialize names the server
  ok   initialize instructions say the rows are a stub
  ok   initialize instructions state the boundary rule
  ok   tools/list answers exactly the six contract tools
  ok   every tool declares an inputSchema
  ok   every tool declares a description
  ok   an unknown method is -32601
  ok   an unknown tool is -32602

== the six tools answer ==
  ok   sm_purchases returns events
  ok   sm_purchases returns only purchases
  ok   every row is stamped fixture: true
  ok   every row carries only schema'd fields
  ok   every kind is in the schema's enum
  ok   'what did we buy yesterday' has an answer today and every other day
  ok   a purchase carries an integer amount in minor units
  ok   sm_timeline is one local day only
  ok   sm_timeline crosses kinds
  ok   sm_media kind=music is listens only
  ok   sm_media with no kind spans watch and listen
  ok   sm_photos filters by place
  ok   sm_search finds a title
  ok   sm_search finds an entity
  ok   a search with no hits is an empty list, not an error

== grants are the whole point ==
  ok   sm_grants reports the calling agent's grant
  ok   the lazy grant is 90 days
  ok   the siri grant is narrower
  ok   the siri grant redacts amounts
  ok   sm_grants never reports another agent's grant
  ok   siri sees purchases
  ok   siri never sees an amount
  ok   the siri window clips the 40-day-old purchase
  ok   siri is refused a kind it was not granted
  ok   the refusal says why and returns nothing
  ok   an agent with no grant reads nothing
  ok   the no-grant refusal names the agent
  ok   a client that never identified itself reads nothing
  ok   an agent cannot widen its grant through a tool argument

== every read leaves a line ==
  ok   the audit log exists after a read
  ok   an allowed read is audited
  ok   a REFUSED read is audited too
  ok   every audit line carries a timestamp and a count
  ok   a read that cannot be audited does not happen
  ok   and the caller is told it was the audit, not the grant

== a memory vault that cannot phone out ==
  ok   vault/store.py imports no network client and shells out to nothing
  ok   vault/mcp_stub.py imports no network client and shells out to nothing
  ok   vault/store.py deletes nothing
  ok   vault/mcp_stub.py deletes nothing
  ok   vault/store.py opens nothing for writing except the audit log
  ok   vault/mcp_stub.py opens nothing for writing except the audit log

59 passed, 0 failed

TOTAL: 73 passed, 0 failed
```

### candidate-contract

Exit 0. Command: `python3 tests/test_stub.py`

```text
== schemas ==
  ok   event.json parses
  ok   event.json declares $schema and $id
  ok   event.json lists required fields
  ok   grant.json parses
  ok   grant.json declares $schema and $id
  ok   grant.json lists required fields
  ok   event schema closes additionalProperties
  ok   grant schema requires agent, kinds and window_days

== protocol ==
  ok   server exits 0 when stdin closes
  ok   initialize returns a protocolVersion
  ok   initialize names the server
  ok   initialize instructions say the rows are a stub
  ok   initialize instructions state the boundary rule
  ok   tools/list answers exactly the six contract tools
  ok   every tool declares an inputSchema
  ok   every tool declares a description
  ok   an unknown method is -32601
  ok   an unknown tool is -32602

== the six tools answer ==
  ok   sm_purchases returns events
  ok   sm_purchases returns only purchases
  ok   every row is stamped fixture: true
  ok   every row carries only schema'd fields
  ok   every kind is in the schema's enum
  ok   'what did we buy yesterday' has an answer today and every other day
  ok   a purchase carries an integer amount in minor units
  ok   sm_timeline is one local day only
  ok   sm_timeline crosses kinds
  ok   sm_media kind=music is listens only
  ok   sm_media with no kind spans watch and listen
  ok   sm_photos filters by place
  ok   sm_search finds a title
  ok   sm_search finds an entity
  ok   a search with no hits is an empty list, not an error

== grants are the whole point ==
  ok   sm_grants reports the calling agent's grant
  ok   the lazy grant is 90 days
  ok   the siri grant is narrower
  ok   the siri grant redacts amounts
  ok   sm_grants never reports another agent's grant
  ok   siri sees purchases
  ok   siri never sees an amount
  ok   the siri window clips the 40-day-old purchase
  ok   siri is refused a kind it was not granted
  ok   the refusal says why and returns nothing
  ok   an agent with no grant reads nothing
  ok   the no-grant refusal names the agent
  ok   a client that never identified itself reads nothing
  ok   an agent cannot widen its grant through a tool argument

== every read leaves a line ==
  ok   the audit log exists after a read
  ok   an allowed read is audited
  ok   a REFUSED read is audited too
  ok   every audit line carries a timestamp and a count
  ok   a read that cannot be audited does not happen
  ok   and the caller is told it was the audit, not the grant

== a memory vault that cannot phone out ==
  ok   vault/store.py imports no network client and shells out to nothing
  ok   vault/mcp_stub.py imports no network client and shells out to nothing
  ok   vault/store.py deletes nothing
  ok   vault/mcp_stub.py deletes nothing
  ok   vault/store.py opens nothing for writing except the audit log
  ok   vault/mcp_stub.py opens nothing for writing except the audit log

59 passed, 0 failed
```

## Limits and rollback

See INVENTORY.md, RUNTIME.md and PROBE.md. No product UI changed, so this
installation does not claim product browser acceptance or a 4–8-hour endurance
run. No daemon, scheduler, global model config or paid tool was installed.
Only Cody Memory's pending quota auto-continue was cancelled; its session
and edits remain. Other Cody projects were not modified.

Before reusing proof after a later commit, compare the implementation tree.
Evidence-only commits do not invalidate unchanged source; source changes require
new checks. Preserve original dirty product work when rolling back.
