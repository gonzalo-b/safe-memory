# Policy hardening gate

Tested SHA `bd68035ff11750529791723dbb6752ed9b9f6698`; command `python3 tests/run_all.py`; exit 0. Synthetic only. Baseline named checks preserved with authorized tools-list expansion.

```text

### tests/test_block_policy.py ###
  ok   Block respects narrow grant window
  ok   Block redacts before rendering
  ok   Block read produces exactly one audit receipt
  ok   Block never serves stale broad Markdown bytes
  ok   policy change takes effect without Block rebuild
  ok   expired Block grant fails closed
  ok   required Block field redaction denies independently of record presence 2
  ok   required Block field redaction denies independently of record presence 0

8 passed, 0 failed

### tests/test_blocks.py ###
== the Travel Log Block ==
  ok   first two lines exact
  ok   records: 3 with the shipped fixtures
  ok   one ## Bariloche, Rio Negro heading
  ok   three record rows in ts order carrying the three ids
  ok   Days: line spans two dates
  ok   fixture date span rolls correctly at (2026, 9, 21)
  ok   fixture date span rolls correctly at (2027, 1, 1)
  ok   fixture date span rolls correctly at (2028, 3, 30)
  ok   2 photos, 1 place
  ok   two consecutive compute() calls are byte-identical
  ok   compute([]) equals the empty text in §3.3
  ok   write() to a temp path produces a file equal to compute() of the store's events
  ok   the committed blocks/travel-log.md starts with the generated header line
  ok   the committed blocks/travel-log.md contains records: 3 and the Bariloche heading
  ok   blocks/travel_log.py imports no network client and shells out to nothing
  ok   blocks/travel_log.py deletes nothing
  ok   blocks/travel_log.py opens exactly one path for writing, named out_path

17 passed, 0 failed

### tests/test_grant_validation.py ###
  ok   malformed Grant expires='invalid' denies and audits
  ok   malformed Grant expires='2026-10-03junk' denies and audits
  ok   malformed Grant expires=999999 denies and audits
  ok   malformed Grant expires='2026-10-03T12:00:00+00:99' denies and audits
  ok   malformed Grant window_days='invalid' denies and audits
  ok   malformed Grant window_days=-1 denies and audits
  ok   malformed Grant window_days=True denies and audits
  ok   malformed Grant fields_redacted='title' denies and audits
  ok   malformed Grant fields_redacted=[False] denies and audits
  ok   malformed Grant kinds='photo' denies and audits
  ok   malformed Grant kinds=['photo', 'typo'] denies and audits
  ok   malformed Grant cannot authorize a Block
  ok   valid minimal Grant still reads

13 passed, 0 failed

### tests/test_policy_projection.py ###
  ok   redacted title cannot influence matching
  ok   redacted entities cannot influence matching
  ok   redacted source cannot influence matching
  ok   redacted source cannot influence source filter
  ok   visible place remains searchable
  ok   projection does not mutate source Record
  ok   legacy location redaction preserves place and removes coordinates
  ok   policy denial is audited
  ok   redacted timestamp cannot influence date filter
  ok   redacted timestamp cannot influence since filter
  ok   redacted timestamp cannot influence until filter
  ok   redacted timestamp cannot rank results before limit
  ok   hidden timestamps and IDs cannot break visible rank ties

13 passed, 0 failed

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
  ok   tools/list answers the six contract tools and sm_block
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

== sm_block: a Grant-checked, audited Block read ==
  ok   sm_block travel-log returns the Block markdown for lazy
  ok   sm_block is refused for siri and names the kinds
  ok   sm_block is refused for an agent with no grant
  ok   sm_block is refused for a client that never identified itself
  ok   an unknown block is a refusal, not a transport error
  ok   a Block that is not computed answers missing: true and no markdown
  ok   every sm_block read, granted or refused, is one audit line with via: mcp
  ok   a Block read that cannot be audited does not happen

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

67 passed, 0 failed

TOTAL: 118 passed, 0 failed
```
