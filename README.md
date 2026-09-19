# memory

**Codename `memory`. Full name: Safe Memory.** The folder, the slug
and the server identity are `memory`; the product is still called Safe Memory
everywhere it is written out for a human.

GB's life, in a vault he owns. What he bought, watched, listened to and where
he was — normalised into one event shape, held locally and encrypted, read only
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

Roadmap (`Safe Memory - Strategy V2.md`, landed in the vault under
`projects/memory/docs/`): SM-1 vault + MercadoLibre, SM-2 YouTube, SM-3
Apple Photos, SM-4 Amazon and Gmail receipts, SM-5 health and food.

No dependencies. No network client. Nothing here deletes.
