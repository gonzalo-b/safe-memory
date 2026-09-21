# Chat Workflow

GB approved this workflow in `~/base/projects/memory/docs/Plan - Chat Workflow.md`.
Its newer approved decisions replace older workflow instructions. The app lives
in this Git repository; strategic planning lives in that separate vault folder.

Invoke `$memory-workflow` for a feature, fix or resume. The project-local skill
is `.agents/skills/memory-workflow/SKILL.md`. Defaults in `.codex/config.toml`
are Astra High; explicit task selections can override them, so verify the
effective selection when starting work. No global settings were changed.

One integrator and up to two bounded subagents, all Astra High. Continue through
approved slices with checkpoints. Wait for quota; no fallback, paid API or
automatic credit purchase. Codex is Memory's executor; no Cody/Hermes context,
supervisor or periodic automation is required. A 4–8-hour run remains a goal
to measure on real feature work, not an installation claim.

Quality means passing behavioral/contract tests and inspecting the relevant UI
with the integrated browser before GB's test. BrowserOS and Playwright are
available fallbacks. A separate reviewer is optional, never a merge gate.

## Delivery

Repository: `https://github.com/gonzalo-b/safe-memory`, private.
Default branch: `master`, preserving the existing repository's branch name.
Gate commands: `python3 tests/run_all.py`, `python3 tests/test_stub.py`.
Use `EVIDENCE.md` for receipts and criterion mapping. Product releases retain
the repo's VERSION/CHANGELOG rules. This harness installation does not release
the unfinished 0.2 feature or absorb its uncommitted changes.

Installation is checking the available GitHub protection capabilities. Until
the receipt records a resolved delivery mode, leave PRs open; do not claim native
protected auto-merge. GitHub Actions is disabled to avoid unapproved hosted
runner charges. Local test results can be reported as commit statuses for the
exact tested SHA; they are not GitHub-hosted CI runs.

## Rollback

Use the installation inventory and Git diff to revert only harness-owned paths.
Preserve later edits and move superseded new files to `_archive/`; do not reset
the repository or rewrite audit data. No scheduled job or global configuration
needs undoing. Remote creation and published history are separate side effects;
never delete the repository as an implicit rollback.
