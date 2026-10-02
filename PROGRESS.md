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

## Continuation — reusable presentation and native compile recovery

- Previous goal turn was progress: PR4–6 merged and native PR7 published. Material G-02 decision remains unanswered; this continuation did not adopt runtime/auth/schema/deployment changes.
- Owned UI worktree /private/tmp/memory-v1-ui, branch codex/memory-v1-0-ui-assets, based on main6058023. Reusable local DS assets, navigation and theme component; all data comes from a future authorized caller. Fixture is explicitly synthetic, no production UI acceptance.
- Browser harness reused installed Playwright 1.60.0 without package changes. 28 component cases + 4 pre-existing browser-launch checks pass across desktop/mobile light/dark. Aggregate 150/0 (147 existing + 3 local-asset checks), contract 67/0. DS guard passes. Exact delivery revisions recorded in docs/evidence/v1.0-ui/EVIDENCE.md.
- Integrated browser unavailable because host is locked; approved Playwright fallback used. Screenshots reviewed. Native select, undefined line-height token, inherited-property route and theme-island defects corrected with recorded regressions.
- Native PR7 now at 83627409e10c8a55ac249137baa6159c67ce8d30: direct target unsigned compile succeeds without installation/settings changes. Scheme discovery fails; device/UI/Photos consent still unavailable. PR remains draft.
- G-02 still pending; no Alpha version accepted/deployed. Next step is apply GB's material decision, then authorized F0 runtime integration and real connector prerequisites. This is second consecutive goal turn observing that pending decision, with concrete independent progress in both turns.

## Resumed with approved runtime — 2026-10-02

- GB confirmed Next/React/TypeScript frontend, Python backend and “seguí con todo”. Revised Alpha V1 Technical Delta is active in MindBase; prior decision archived. Runtime/auth/SQLite/private destination/proposed existing deployment are authorized. Earlier material-decision block is resolved; V1.0–V1.4 goal continues, no release accepted.
- Integrator checkout /private/tmp/memory-v1-runtime, branch codex/memory-v1-0-runtime, base main1efbc5e3223c2b12007fd595c2992a1bb6a368f8. Own uncommitted runtime, shell adapter, SQL, tests and behavior docs. Original dirty checkout remains untouched. VERSION0.1.0.
- Persistent owner/session/auth/audit, private path validation, backup and quarantined restore implemented. Recovery review found destination-copy and session resurrection defects; three RED tests reproduced, then15/15 runtime tests passed. Successful-login limiter regression separately RED→GREEN; full gate pending newest fixes.
- HTTP review found shared proxy limiter identity and unbounded body receive. Explicit trusted edge configuration plus total deadline implemented with RED tests; green run underway. Production tunnel/header trust still needs deployment verification.
- Frontend agent owns /private/tmp/memory-v1-next web only; Next production build,5 API checks,28 mocked UI cases and2 actual Python integration cases passed. Local synthetic API8766 and Next8767 only, no personal data; latest backend fixes need integration rerun.
- Native PR7 draft b88cb7b has unsigned direct-target build proof; real device/signing/Photos consent unavailable. PR4–6 and8 merged prerequisites. No connector acceptance or server deployment claimed.
- Next: finish HTTP/recovery gate, integrate frontend commit, preserve exact-SHA evidence and focused PR. Continue pairing/ingestion, knowledge persistence, private media, Artifacts and deployment. External human steps remain device trust/signing/Photos consent and private owner provisioning, not architecture approval.

- Foundation backendfef6139:179/0 aggregate and67/0 contract, all76 original named baseline checks preserved. Frontend1411504 integrated as9f05ed5; production build/typecheck/DS pass, unit6/6, mocked browser32/32, actual restarted Python integration2/2. Evidence consolidated under docs/evidence/v1.0-runtime/. Pending exact-final-head receipt and PR delivery.
- Current synthetic API PID62374/session69834 on8766; integrated Next session86341 on8767. No production route. Local tunnel configs contain no Memory hostname/8767; edge Worker/header settings unverified.
- Two independent bounded slices now running: reference_mapping owns /private/tmp/memory-v1-pairing (core secure pairing/migration/tests, based9f05ed5); connector_probe owns native probe exporter (explicit selected-ID optimized copies, no source access during tests). Root remains only writer in runtime integration checkout. No release/version acceptance.

## F1 continuation after foundation merge — 2026-10-02

- PR9 merged e93f5864544d615300af03d111b0fb5d2aa94a1b; exacthead1cfc3c5 had179 aggregate/67 contract/32 UI/2 actual-runtime/6 unit passing. Merged tree equals candidate. Digest landed2026-10-02-foundation-runtime-next. No deployment or device acceptance.
- Integrator now /private/tmp/memory-v1-ingestion, branch codex/memory-v1-1-ingestion; pairingcorea53fc6d cherry-picked asba53f5d. Pairing agent proved201/0 +67/0 with22 new pairing/migration tests. Original dirty checkout preserved.
- Own uncommitted schema3 migration, metadata ingestion service and tests. First10 tests passed; boundary regressions exposed invalid enum types, offset normalization and completed-run replay; corrections applied and aggregate running. Scope is explicit1–100 selected IDs and bounded sample, not whole-library claim. Raw authorized payloads and immutable revisions retained, Hidden/shared/current permission checked before disclosure.
- Native exporter committed0fe86cc inprobe checkout: gate160/0 on its olderbase, native7/0, unsignedtargetbuild. Real PhotoKit/cache/video/device claims remain unverified. Native pairing HTTPS/Keychain client now in progress separately.
- Frontend pairing UI running in web agent checkout; owns8767 for mocked QA. Root Python8766 stillfoundationfixture, no pairingHTTPyet. Next rootstep: expose exact frozen pairing/device/ingest routes with adversarial transporttests, then switch isolatedsynthetic API and runactualweb/nativeprotocol integration. No ownerpersonaldata provisioned.

- Metadata/HTTP candidate now passes227/0 aggregate. Independent review reproduced old-revision Hidden reversal and limited-selection replay; five RED regressions now green through retained observation ordering and policy-revision fencing. Crash before/after checkpoint, audit failure, revoked receipt and quarantined restore are exercised. Schema3 prototype compatibility fails closed; old fixture /private/tmp/memory-live-fixture-f1 must not be reused after restart.
- Pairing frontend commits1cec0c5/a9fa768 ready for integration:52 mocked browser/6 unit/2 actual pairing cases passed on synthetic local runtime. Native code3500d5b plus evidence1206f28 ready, unsigned build and165/0 on its older base; no actual device, Keychain or Photos test. Native agent now implements explicit bounded sample import with durable retries. Read-only ingestion review recheck pending; no release accepted.
- Next: commit metadata protocol, integrate pairing UI, start a fresh synthetic fixture root and revalidate actual browser flow, then integrate native branch. Whole-library enumeration, private media, persistent Blocks/trips/Artifacts and production deployment remain required. VERSION remains0.1.0.
