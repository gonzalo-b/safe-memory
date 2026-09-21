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
Default branch: `main`. The previous remote `master` is retained as history.
Gate commands: `python3 tests/run_all.py`, `python3 tests/test_stub.py`.
Use `EVIDENCE.md` for receipts and criterion mapping. Product releases retain
the repo's VERSION/CHANGELOG rules. This harness installation does not release
the unfinished 0.2 feature or absorb its uncommitted changes.

The agent automatically completes each authorized PR to `main` after successful
checks and QA. No extra human merge approval, GitHub Pro, native auto-merge
feature, paid hosted CI, or new daemon is required. This is agent-mediated
merge during an active Codex task, not a background GitHub service. External
PRs are not monitored while Codex is inactive; scheduled automation remains deferred.

1. Fetch the current PR HEAD and `main`. Verify repository, target, ownership,
   private visibility, and that the candidate checkout has no tracked changes.
2. Ensure the current `main` is an ancestor of the PR HEAD. If it advanced,
   integrate it into the feature branch and rerun checks on that new candidate.
3. Run the aggregate and contract gates, plus relevant feature/UI QA. Record
   evidence and publish `memory/gate` and `memory/contract` statuses on the
   exact tested SHA. Any failed, missing, pending or skipped required result
   leaves the PR open. Include additional feature checks when relevant.
4. Re-read the PR HEAD, base SHA and statuses immediately before merge. Changes
   invalidate the old decision; return to verification. Use:
   `gh pr merge <number> --repo gonzalo-b/safe-memory --merge --match-head-commit <tested-sha>`.
   Do not use `--auto` (paid native feature) or `--admin` (bypass).
5. Confirm the returned merge commit and merged state. Fetch `main`, compare
   the merged implementation to the tested tree, and record the receipt. If
   integration differs, run checks on the actual merged tree and report any
   failure immediately; never claim untested integration is verified.

GitHub Actions remains disabled to avoid unapproved runner costs. Commit
statuses here report actual local runs, not GitHub-hosted CI. GitHub Free
private repositories do not enforce this policy against a direct push/manual
merge by another writer. Keep one integrator; this workflow is procedural
agent control, not equivalent to server-enforced branch protection.

## Rollback

Use the installation inventory and Git diff to revert only harness-owned paths.
Preserve later edits and move superseded new files to `_archive/`; do not reset
the repository or rewrite audit data. No scheduled job or global configuration
needs undoing. Remote creation and published history are separate side effects;
never delete the repository as an implicit rollback.
