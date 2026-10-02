---
title: "Read Only"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# read-only verification

Implementation revision: `71522a1351307657a8abe369c841898f254b6152`.

```text
test_all_probe_sources_are_read_only (__main__.ReadOnlyGuard) ... ok
test_rejects_every_source_mutation_entrypoint (__main__.ReadOnlyGuard) ... ok
test_rejects_private_lookup_and_network_surface (__main__.ReadOnlyGuard) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.002s

OK

```
