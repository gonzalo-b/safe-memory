# contract verification

Implementation revision: `71522a1351307657a8abe369c841898f254b6152`.

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
