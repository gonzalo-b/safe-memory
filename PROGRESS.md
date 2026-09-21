## Definition of done

### Task
Done when: Safe Memory 0.2, Shell and First Block. Objective: a local webapp that reads the SM-0 store, renders one precomputed Block, and refuses to show anything without a Grant, proven by a screenshot and an audit line. Read ~/apps/memory/CLAUDE.md first, it is repo law and is not rewritten. Slices to sharpen: S0 AGENTS.md, CONTEXT.md, PROGRESS.md, Playwright dev dependency with one smoke test, evidence dir docs/evidence/0.2.0/. S1 blocks/ module computing one Block, travel-log.md, from fixtures/events.jsonl by code, no inference. S2 extend vault/mcp_stub.py so a Grant-checked read returns the Block and writes audit/reads.jsonl. S3 the shell: local webapp, one route, renders the Block, empty, loading and error states, light and dark. S4 default deny proven: a read without a Grant returns nothing and still writes an audit line. Acceptance, each false today: pytest green above the 0.1.0 baseline; blocks/travel-log.md generated never hand-written; screenshot docs/evidence/0.2.0/S3-F1-1440x900-dark.png shows the Block; a screenshot shows default deny with no data leaked; audit/reads.jsonl gains one line per read granted or denied. Full context: ~/base/projects/memory/docs/Memory - Cody Setup.md section 2 and ~/base/projects/memory/.context/canon.md.
Evidence: The task's acceptance checks run successfully and their real output is recorded in this file.
Command: `git -C /Users/agent/apps/memory diff --check`

Task start: 2026-09-21T00:19:56Z

## Long-run protocol (1Hit §6) — run memory-memory-0.2-1-1789949996

BASE=92615f7e489a22855d87e23ffe14bc717aa6b74e (Safe Memory V0.1 - Graphify code graph, built local with no API key)
Baseline: `python3 tests/test_stub.py` -> 59 passed, 0 failed, exit 0.

### §1 recon deltas (reality vs the 1Hit's 2026-09-20 recon; reality wins)
- Node: repo doc expected v24.14.1 at `/opt/homebrew/bin/npx`; actual is v22.22.3, `npx` at `/Users/agent/.local/bin/npx`. Node/npx present either way, no blocker.
- Fixture purchases: 1Hit expected 3 purchase events (`grep -c '"kind": "p' fixtures/events.jsonl` = 6). Actual: 5 purchase, 2 photo, 1 place, 2 listen, 2 watch, 1 health = grep prints 8. Does not change the Travel Log Block (still photo+place = 3 records, Bariloche group, same ids/offsets 30/29/30) — only the unrelated purchase count differs.
- Everything else in §1's table matches: branch master no remote, base commit, VERSION 0.1.0, no CHANGELOG.md, 59 passed baseline, Python 3.14.6, no e2e/package.json/playwright.config, working tree only graphify-out/graph.json modified + cody-manifest.json untracked (+ .cody/ and PROGRESS.md from the seed), grants (lazy 90d all kinds, siri 7d purchase/watch/listen redacted), audit/reads.jsonl 9 lines, store.py and mcp_stub.py symbol lists, graphify present, docs/plans holds this 1Hit only, docs/evidence absent.

### Slices
- S0 Foundation (root files, Playwright, evidence dir): done — commit 1688845, verifies held on master (smoke test 4 passed, test_stub.py 59 passed 0 failed, no e2e/node_modules staged)
- S1 Travel Log Block: done — `python3 -m blocks.travel_log` prints `travel-log: 3 records -> blocks/travel-log.md`; `python3 tests/run_all.py` exits 0, `TOTAL: 73 passed, 0 failed` (above the 59 baseline)
- S2 Serve the Block (sm_block, grant-checked, audited): todo
- S3 The shell: todo
- S4 Default deny, proven: todo

### Decisions taken
(recorded as made, with the §3/§10 criterion each resolves)
- No subagents were spawned for the builder/Verifier split of §5: this harness has an Agent tool but §5 item "No subagents in your harness: you are every tier" is honoured literally — every slice is built and then re-verified by re-running the exact §9.2/§9.3 commands against the committed `master` tree in the same session, rather than trusting the build run. Recorded per slice above.

### Blockers
(none yet)

### Audit line counts (Verifier's Playwright run, §9.3)
before: — / after: —


## Chat Workflow installation — active

- Objective: install the approved Codex workflow; not finish Safe Memory 0.2.
- Branch: codex/chat-workflow; base: de9dfe1.
- Isolated checkout: /Users/agent/apps/memory-chat-workflow.
- Original checkout retains uncommitted CONTRACT, tests, store, transport and
  Graphify changes; none are included in this installation.
- Cody Memory was waiting for quota. Its automatic continuation was cancelled
  with Escape; the session and edits remain intact.
- Baseline: aggregate 73 passed; explicit contract 59 passed.
- GitHub private repo created; original committed base pushed to master.
- GitHub returned 403 for private branch protection (Pro required). Delivery
  alternative awaiting GB; hosted Actions disabled to avoid unapproved charges.
- Pending: skill runtime probe, post-install tests, evidence, delivery decision,
  activation in original checkout, vault alignment and final receipt.
- Next: validate skill and execute read-only behavioral probe with Astra High.
