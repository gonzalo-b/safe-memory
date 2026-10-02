# memory

**Codename `memory`. Full name: Safe Memory.** The folder, the slug
and the server identity are `memory`; the product is still called Safe Memory
everywhere it is written out for a human.

GB's life, in a vault he owns. What he bought, watched, listened to and where
he was — normalised into one event shape, protected by explicit access policy, read only
through explicit per-agent grants, every read audited.

**Today this repository is SM-0: the contract stage.** It holds the agreement
and a server that answers it from fixtures. It has never read a real account.
`CONTRACT.md` is the document to read; everything else implements it.

```
python3 tests/test_stub.py     # the contract, asserted. exit 0 is pass.
python3 vault/mcp_stub.py      # the server, on stdio
```

The boundary: Safe Memory answers what happened in GB's life; MindBase answers
what he is building. Neither stores the other's half.

Alpha V1 is Apple Photos. The active sprint covers V1.0 foundation, V1.1 iPhone
ingestion, V1.2 Blocks/trips, V1.3 private media and V1.4 private Artifacts.
Later V1.5–V1.10 remain separate. Nothing here yet certifies deployed Alpha or
a real iPhone import. See `PROGRESS.md` and `docs/evidence/1.0.0/EVIDENCE.md`.

The fixture candidate adds `sm_block` for Travel Log. It applies current Grant
scope before rendering rather than serving broad generated Markdown. Field
redactions also precede search, filters and ranking.

Core: standard library only, no network client, no Source writes or deletion.
Private repository: `gonzalo-b/safe-memory`; delivery in `docs/WORKFLOW.md`.

Reusable navigation/theme presentation is in `ui/`; `ui/README.md` documents the synthetic browser fixture. It makes no server, authentication or Photos connection claim.
