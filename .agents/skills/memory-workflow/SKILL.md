---
name: memory-workflow
description: "Develop, resume, and validate Safe Memory features using the approved Memory workflow, including its planning folder, fixtures, browser QA, checkpoints, and GitHub delivery. Use for Memory project work, not unrelated repositories."
---

# Memory Workflow

## Start and authority

Resolve the current Git root; a worktree is a valid app checkout. Read its
`CLAUDE.md`, `AGENTS.md`, and current `PROGRESS.md`. Read `CONTRACT.md` when
changing observable behavior. Strategic files live at
`~/base/projects/memory/docs/`; load `Plan - Chat Workflow.md` and only the
feature's approved inputs. Do not load Cody/Hermes documentation routinely.

GB's newer explicit approved planning decisions override older workflow
instructions in their scope. The personal `.context/canon.md` is read-only;
new approved decisions do not require editing that file to take effect.
Do not infer new product decisions or change Safe Memory's promises.

Inspect branch, HEAD, diff, worktrees, and task ownership before editing.
Keep unrelated work intact. One writer per checkout; one integrator owns shared
planning edits. Use a `codex/` branch and isolated worktree when needed, selecting
the starting revision deliberately rather than silently omitting pending work.

## Execute

Define the observable outcome, scope, numbered acceptance criteria, tests and
evidence. Continue through dependent slices of that agreed feature without
asking whether to continue. Ask only unresolved material decisions. Use
[templates](references/templates.md) for a brief, checkpoint or delivery.

Use Astra High. Delegate bounded independent work, including simple tasks,
when it saves time or main-context volume; at most two subagents alongside the
integrator. Subagents also use Astra High. A separate reviewer is optional,
never a mandatory gate. Do not create a visible new app task for every subtask.

Follow the repo's TDD rules and preserve previously passing tests by name.
Work on code and synthetic fixtures, not personal source libraries or secrets.
Use CodeGraph first if `.codegraph/` exists; otherwise use the existing local
Graphify workflow. Never run paid graph extraction or labeling.

## Quality before GB's test

Run `python3 tests/run_all.py` and `python3 tests/test_stub.py`, plus tests
relevant to the change. For UI, use the integrated ChatGPT/Codex browser first
to exercise the real app. Check relevant success, empty, loading, error,
permission and viewport states. BrowserOS and Playwright remain fallbacks;
use Playwright where repeatable automation is needed and the primary browser
does not cover it. Backend changes need behavioral/contract tests, not an
artificial browser exercise. A screenshot alone cannot prove authorization.

Fix blocking defects and rerun affected checks. Preserve observed failures in
the evidence; do not weaken tests or waive failures because attempts ran out.
Do not impose independent review approval or a fixed number of review rounds.

## Continuity and quota

Keep the checkpoint in `PROGRESS.md` at each milestone and before compaction:
objective, pending criteria, branch/HEAD, uncommitted and unrelated work,
commands/results, agents, blockers, decisions, next action. Wait for running
tools inside the active execution. Distinguish waiting for a tool, a decision,
or quota from failure and cancellation. Never restart cancelled work.

At quota exhaustion, preserve state when possible and wait. No model fallback,
paid API, automatic top-up, or extra agents to evade limits. Resume when the
runtime permits; without a scheduled wake, do not promise automatic recovery
after a session ends. The 4–8-hour target is an operating goal, not a guarantee.
No heartbeat, watchdog or external supervisor is installed by this workflow.

## Evidence and delivery

Use `docs/evidence/<version>/EVIDENCE.md` for criterion-to-proof mapping,
commands, exit codes, logs, QA results, plan hash and tested revision. Capture
images retain their native format and are linked in Markdown. Missing,
stale or wrong-revision evidence means the criterion is not verified.
An evidence-only commit may follow the tested candidate: record both revisions
and verify that the relevant implementation tree is unchanged.

Update behavior docs and VERSION/CHANGELOG for product releases. Harness-only
installation uses `docs/evidence/workflow-v1/` without claiming a product release.
Commit only owned paths using `Safe Memory V{MAJOR.MINOR} - {Title}`.
Push only synthetic fixtures/code and intended documentation to the private
`gonzalo-b/safe-memory` and `lazyagent/memory` repositories. After each checked
PR merge, fast-forward the merged `main` to both and verify equal remote SHAs
using `scripts/mirror_main.py --expected-main <merged-sha>`. No force push.
Check remote visibility and actual delivery
policy in `docs/WORKFLOW.md` before integrating. Automatically merge authorized
PRs to `main` after its exact-SHA checks and QA; do not wait for GB to click merge.
Use ordinary CLI merge with `--match-head-commit`, not native `--auto` or an
admin bypass. This runs while the agent is active; it is not a background watcher. Use the current PR HEAD and
base, successful required checks and completed QA, with no known blocking
defects. Reverify integration if the base changes. No reviewer approval is
required; missing or skipped checks are not success.

Report local verification, push and merge separately using actual receipts.
Land strategic documents through MindBase and finish with `mb digest memory`
(resolve the installed CLI, including `~/apps/mindbase/bin/mb`). MindBase is
development filing, never a Safe Memory runtime dependency. Preserve pending
filing honestly if unavailable.
