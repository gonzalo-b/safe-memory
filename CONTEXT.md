# Safe Memory - Context

The vocabulary. One word replaces a sentence; a new concept earns a word here
before it earns an implementation.

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

Safe Memory answers what happened; MindBase answers what he is building;
neither stores the other's half.
