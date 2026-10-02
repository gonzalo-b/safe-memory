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
- Completed: skill validator, actual discovery, effective Astra High, fresh-context
  probe, post-install tests with identical passing names, idempotence assessment,
  activation in original checkout and vault alignment.
- Evidence: docs/evidence/workflow-v1/EVIDENCE.md. PR #1 open in private GitHub.
- Delivery resolved: Codex-mediated merge to main, without Pro or native protection.
- PR #1 merged as d50f454 after 76 aggregate and 59 contract checks; tested
  source 5361256 has the same tree as the merge. See DELIVERY.md.
- Installation complete; unfinished 0.2 product work remains separate.

## Delivery resolution — 2026-09-21

GB requires automatic PR delivery without GitHub Pro. Use agent-mediated merge
after exact-SHA checks and QA, per docs/WORKFLOW.md. Target branch is now main;
old remote master retained. No native auto-merge, protection, scheduled watcher
or paid CI is claimed. PR #1 exercised this path successfully; main is now the local and remote default.


## Chat Workflow readiness — 2026-10-02

This checkpoint supersedes the historical installation status above; the 0.2
implementation history remains intact.

- Objective: rerun the approved 1Hit setup and leave Memory ready for a later
  formal Alpha V1 plan and Goal. Do not implement V1 or create that Goal now.
- Verified starting revision: `6b94117538853ca21306827974ed3f85bb2dd36a`, main.
- Verification branch: `codex/workflow-readiness`; isolated checkout:
  `/Users/agent/apps/memory-workflow-readiness`. Delivery commit is recorded
  by Git history and the linked receipt, rather than a self-referential hash.
- Protected original work: CONTRACT.md, graphify-out/graph.json,
  tests/test_stub.py, vault/mcp_stub.py, vault/store.py, .cody/ and
  graphify-out/cody-manifest.json. Original audit and personal canon are preserved.
- Runtime: effective Astra High confirmed for this turn; two app-server reads
  detect one enabled repo skill and Astra High defaults. Skill validator passes.
- Baseline: aggregate 76 passed / 0 failed; contract 59 passed / 0 failed.
  Final delivery must preserve these checks by name.
- Ownership: previous Codex task idle; legacy Cody Memory run NEEDS_ATTENTION,
  pid null, no lease, next_wake 0. No session or scheduler was changed.
- QA: one Astra High read-only subagent exercised skill invocation, resume and
  rejection of stale-SHA/pending evidence; it completed. No pending agents.
- Evidence: docs/evidence/workflow-v1/revalidation-2026-10-02/EVIDENCE.md.
- Next action: with GB, define the formal V1 plan, resolve its product criteria
  and explicitly start a Goal when requested. Alpha V1 is Apple Photos.
  Inspect the preserved 0.2 diff before deciding what to reuse. Nothing here
  certifies those uncommitted product changes or releases 0.2/V1.
- Operating limit: active Mac/app session, checkpoints, quota waits; no
  scheduler, paid fallback or certified 4–8-hour endurance run.


## Alpha V1.0–V1.4 sprint — 2026-10-02

- Goal active; complete every supplied G/F0/F1/F2/F3/F4/Q criterion, including real iPhone connector. No version accepted yet.
- Integrator Astra High confirmed from actual turn_context; two bounded internal Astra High agents: connector probe and pure capabilities, each in an isolated checkout. No visible new tasks or supervisor.
- Chosen base 86e71a15bf2bc376b0c517c91797fc9c9bce9189; branch codex/memory-v1-0-foundation; checkout /private/tmp/memory-v1-foundation. Original dirty 0.2 files preserved; no main reset/stash/clean.
- Baseline: 76 aggregate and 59 contract checks pass by name on clean isolated base. Privacy regression reproduced (4 failures) and fixed (8 passes). Evidence in docs/evidence/1.0.0/EVIDENCE.md; input hashes in INPUTS.md.
- Proposal landed through mb land: /Users/agent/base/projects/memory/docs/Alpha V1 Technical Delta.md. GB approval pending for actual runtime/auth/schema/deployment; independent bugfixes and synthetic work continue.
- Host macserver; Xcode now exists unlike historical digest. Physical device/signing, HTTPS Memory route, private runtime/storage restore and authorized sample are unverified. No personal data imported.
- Next: safe projected sm_block regression; adopt DS assets and real UI once runtime delta approved; integrate pure capabilities and unsigned probe from isolated subagents. Retain VERSION 0.1.0 until acceptance.

- Privacy prerequisite implementation committed as 465ee800a7e0725ed279edcd9afd676fb222540f; exact candidate gate 104/0 and contract 67/0, original named baseline preserved. Backend-only, no UI/deployment claim. Pending focused PR delivery; evidence-only receipt may follow.
- Pending original 0.2 transport/tests deliberately reused after review; unsafe Block implementation replaced. Existing Claude process points at original checkout, so original edits remain isolated and untouched.

- PR #4 merged at a9c2fcaa9de7460507742b9f37669a4bf42a5e38; exact HEAD a0237e8 checks were 104/0 and 67/0. Integrated implementation equals tested tree. No deployment/version acceptance.
- Independent fixture review found hidden timestamp ordering with IDs also redacted and inherited malformed-Grant fail-open. Corrective branch codex/memory-v1-0-policy-ties now contains RED→GREEN tests; next step exact-SHA verification/delivery. No finding is waived.
- CoreDevice read with proper host access completed: zero available devices. Unsigned native probe builds but device/signing/transfer still pending.

- PR #5 merged e6bf38650371e91a201801e3a88916be9dc382f8 with exact-SHA gate118/0 and contract67/0; merged core/test tree matches tested.
- Current knowledge prerequisite checkout /private/tmp/memory-v1-capabilities, branch codex/memory-v1-2-capabilities, integrated candidate 7e389d220d83c63b0b032adb71408d90566e3b60: gate147/0, contract67/0. Pure date/statistics/occasion/trip modules only; production indexed Blocks/corrections remain pending. Evidence docs/evidence/1.2.0/.
- Native probe branch codex/memory-v1-1-probe at 0f8c877 builds unsigned; no simulator runtime or available physical device, so native UI and real connector acceptance pending.
- G-02 material approval remains pending in Alpha V1 Technical Delta.md. No persistent store/auth/schema/HTTPS deployment applied. Goal remains all V1.0–V1.4, no accepted increment.


## Current handoff — Alpha preparation awaiting material decision

- Integrated main60580239ff93b6fa034fd1d459258e30acc05c99 contains PR4/5 privacy corrections and PR6 internal calculations;147 aggregate/67 transport checks pass. No product increment accepted, VERSION0.1.0.
- Working checkout /private/tmp/memory-v1-probe, branch codex/memory-v1-1-probe, integrated implementation fc6f3c19c10e1920d7a2f49c848994173d02cad4.150 aggregate/67 contract +4 synthetic Swift checks pass. Native draft remains unmerged.
- Latest native Xcode revalidation fails exit70: iOS26.5 platform not installed according to destination resolver, despite earlier sandbox build success and SDK headers. No simulator runtimes or physical devices available. Preserve both results; native UI/device not tested.
- Strategic active proposal: /Users/agent/base/projects/memory/docs/Alpha V1 Technical Delta.md. GB approval is pending; do not treat elapsed time or execution authorization as approval of the reserved material auth/schema/stack choice.
- Receipt: /Users/agent/base/projects/memory/docs/Alpha V1 Preparation Receipt.md. The archived Technical Delta (2) is superseded evidence, not another active decision.
- All F0–F4/Q criteria remain pending or partially proven by fixtures; required deployment, real connector, durable knowledge/corrections, multimedia and editable persistent Artifacts are not delivered.
- Next action after GB's decision: implement approved runtime/schema/auth in focused foundation worktree; validate Xcode platform and prepare concrete private upload destination before requesting device signing/trust/sample consent. No personal sample exists yet. No subagents remain running; no scheduler installed. Goal active, first waiting-for-material-decision handoff.

- Native draft published as https://github.com/gonzalo-b/safe-memory/pull/7 at 49829416a400de0bd940796e0f927862f5bc4296, with exact-SHA gate 150/0 and contract 67/0. Native-device status pending; no merge. Final receipt-only follow-up links historical evidence to current build blocker; implementation is unchanged. Resume from this branch/checkpoint and its final PR HEAD, not the original dirty checkout.

- Continuation verified direct target unsigned build at 956ce8e exits 0, fresh output, installed SDK, no configuration changes. Scheme destination discovery remains failed; no simulator/device/UI acceptance. See TARGET-BUILD.md. Native PR remains draft.

## Continuation — reusable presentation and native compile recovery

- Previous goal turn was progress: PR4–6 merged and native PR7 published. Material G-02 decision remains unanswered; this continuation did not adopt runtime/auth/schema/deployment changes.
- Owned UI worktree /private/tmp/memory-v1-ui, branch codex/memory-v1-0-ui-assets, based on main6058023. Reusable local DS assets, navigation and theme component; all data comes from a future authorized caller. Fixture is explicitly synthetic, no production UI acceptance.
- Browser harness reused installed Playwright 1.60.0 without package changes. 28 component cases + 4 pre-existing browser-launch checks pass across desktop/mobile light/dark. Aggregate 150/0 (147 existing + 3 local-asset checks), contract 67/0. DS guard passes. Exact delivery revisions recorded in docs/evidence/v1.0-ui/EVIDENCE.md.
- Integrated browser unavailable because host is locked; approved Playwright fallback used. Screenshots reviewed. Native select, undefined line-height token, inherited-property route and theme-island defects corrected with recorded regressions.
- Native PR7 now at 83627409e10c8a55ac249137baa6159c67ce8d30: direct target unsigned compile succeeds without installation/settings changes. Scheme discovery fails; device/UI/Photos consent still unavailable. PR remains draft.
- G-02 still pending; no Alpha version accepted/deployed. Next step is apply GB's material decision, then authorized F0 runtime integration and real connector prerequisites. This is second consecutive goal turn observing that pending decision, with concrete independent progress in both turns.
