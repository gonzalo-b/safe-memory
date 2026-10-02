# Chat Workflow readiness receipt — 2026-10-02

Result: setup verified locally and ready for the later formal Alpha V1 plan.
This reexecutes the approved 1Hit; it does not start that plan, create a Goal,
implement V1, or certify the preserved unfinished 0.2 changes.

- Tested product baseline: `6b94117538853ca21306827974ed3f85bb2dd36a`.
- Candidate branch: `codex/workflow-readiness`, isolated from the dirty main checkout.
- Product VERSION: `0.1.0`, unchanged. No release or CHANGELOG entry is implied.
- Plan SHA256: `6e1dc752d0d8292ea7b85053cdc6021710ba708db3bfa6b0e5c9dc6ce046d883`.
- Original inventory: [INVENTORY.md](INVENTORY.md). Test output: [GATES.md](GATES.md).
- This candidate changes only PROGRESS and workflow evidence. All code, config,
  skill, dependencies, permissions and product tests remain byte-identical to baseline.
- Delivery: local readiness is verified here. Exact-candidate status, PR and merge
  receipt will be recorded separately after actual delivery; see MindBase's
  `2026-10-02-chat-workflow-install.md` digest and the branch PR in GitHub.

| Criterion | Result | Evidence |
|---|---|---|
| A1 Paths/precedence | Verified | Git root and vault real paths checked; current approved Plan controls workflow; canon hash unchanged. |
| A2 Astra High | Verified | Current turn metadata: gpt-6-astra, effort high, cwd /Users/agent/apps/memory. App-server resolved defaults match. Read-only subagent explicitly launched Astra High. |
| A3 Skill | Verified | Two forced skills/list reads find exactly one enabled repo memory-workflow; actual integrator/subagent invocation; bundled quick_validate exit 0. |
| A4 Isolation | Verified | Baseline dirty paths inventoried and excluded; edits/tests in memory-workflow-readiness; original audit/canon preserved. |
| A5 Gates | Verified locally | Aggregate 76/0 and explicit contract 59/0, exit 0; 73 historical passing names preserved, three previously added date checks also pass. Final exact-SHA runs are delivery checks. |
| A6 Resume | Verified | Updated PROGRESS records scope, tested base, branch, protected work, commands, agents and next action; fresh-context probe reconstructed state and exposed stale old checkpoint before correction. |
| A7 Honest evidence | Verified | Probe refuses previous-SHA green checks plus pending current contract check: keep PR open, rerun exact HEAD/base. This is procedural behavior, not automatic enforcement. |
| A8 Idempotence | Verified | Config/skill/AGENTS/CLAUDE/WORKFLOW already match desired state; no changes, duplicates, plugin installation or scheduler creation. Two forced loads agree. |
| A9 Filing | Verified | Registered memory slug; mb status/land returned the paths below. Canon untouched. Closure digest follows actual delivery. |
| A10 Delivery | Local verified; remote recorded separately | GitHub identity gonzalo-b, private safe-memory, main at baseline, Actions disabled. Historical PRs #1/#2 merged; this rerun follows exact-SHA delivery. |

## Runtime proof

CLI/app-server 0.144.5. `codex app-server --strict-config` initializes successfully.
`config/read` twice resolves model gpt-6-astra and model_reasoning_effort high.
`skills/list` twice with forceReload finds the repo skill enabled, scope repo.
No model inference or new app task was started by these read-only RPC calls.
Current turn metadata also proves actual Astra High (not merely a saved default).
Current permissions: approval_policy never; sandbox danger-full-access.
No permissions changed. service_tier resolves null; no explicit speed override
is inferred from that value. Standard-speed recommendations from the later
research note are not silently promoted to approved installation requirements.
Official configuration/skill/App Server behavior was checked in the freshly
fetched OpenAI manual, including https://learn.chatgpt.com/docs/app-server.

Validation command:
`/Users/agent/apps/mindbase/.venv/bin/python /Users/agent/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/memory-workflow`
returned `Skill is valid!`, exit 0. Existing environment; no dependency installed.

## Ownership and resume probe

Prior Codex Memory task was idle. Legacy Memory Cody run state was
NEEDS_ATTENTION, pid null, empty lease_owner, lease_until 0, next_wake 0.
No session was stopped, restarted or resumed; no unrelated process was changed.
One bounded read-only Astra High subagent completed the skill/checkpoint/evidence
probe. It found the stale checkpoint, the remaining Cody roadmap rows and an
active superseded procedural note. Integrator corrected these findings.

## Strategic alignment and returned filing paths

- Updated active Master Brief via mb land:
  `/Users/agent/base/projects/memory/docs/Memory - Master Brief.md`.
- Previous complete Master Brief preserved via mb status cold:
  `/Users/agent/base/_archive/Memory - Master Brief.md`.
- Superseded Steps workflow archived via mb status superseded:
  `/Users/agent/base/projects/memory/old/Steps - Memory Workflow.md`.
- Master Brief changes are limited to development ownership/review references
  (D6/D9 and an explicit precedence note); product decisions remain unchanged.
- Plan and 1Hit remain the existing authoritative documents, without duplicate
  active copies. The existing Chat Workflow - Usage guide remains valid.
- New research note Harness De Desarrollo Y Workflow V1 is explicitly marked
  recommendation. Its unapproved configuration proposals are not installed.
- Native MindBase tooling controls filing/frontmatter and returned destinations.

## Limits and rollback

No product UI changed, so product browser QA is not claimed. A sustained
4–8-hour feature execution remains unmeasured. Native GitHub branch protection
is not claimed: delivery uses Codex in the active task, successful exact-SHA
statuses and ordinary merge; Actions remain disabled and no paid plan is added.
No automation, background watcher, Goal, new visible task or fallback model was
created. The next action is the formal V1 plan with GB, then an explicitly
requested Goal. Alpha V1 remains Apple Photos.

Rollback only this branch's owned PROGRESS/evidence diff. Restore strategic
workflow references from their archived originals through MindBase only if
needed; do not undo approved product decisions. Preserve later edits and move
superseded files to _archive rather than deleting. Never reset dirty product
files or truncate audit. [INVENTORY.md](INVENTORY.md) records original hashes.
