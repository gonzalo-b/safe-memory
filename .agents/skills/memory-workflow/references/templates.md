# Memory task records

Use only the sections needed by the current task. Records are Markdown.

## Brief

- Outcome and scope:
- Approved strategic input and SHA256:
- Branch, starting revision and ownership:
- Acceptance criteria: ID, observable result, test command, proof path.
- Dependencies and decisions still needed:

## Checkpoint in PROGRESS.md

- Objective and status: running / waiting for tool / waiting for decision /
  waiting for quota / blocked / cancelled / verified local.
- Branch and HEAD:
- Completed and pending criteria:
- Owned uncommitted work and unrelated work:
- Commands, exit codes and evidence:
- Active agents and their bounded assignments:
- Decisions, blockers and next concrete action:

## EVIDENCE.md

- Task, approved plan path and SHA256:
- Tested source revision, base revision and delivery revision:
- If delivery adds only evidence, implementation-tree comparison:

| Criterion | Result | Proof / command | Revision |
|---|---|---|---|
| A1 | VERIFIED / FAILED / NOT VERIFIED | Actual observation | Tested SHA |

Record command, working directory, exit code and output in fenced text blocks.
List UI flows/states actually exercised, not a generic checklist marked done.
Retain failure and correction history. Name any untested criterion explicitly.

- QA result and remaining limitations:
- Previously passing test names preserved:
- Local verification, push URL, PR URL and merged SHA (each separately):
- Changed files and rollback instructions that preserve later edits:
- MindBase filing receipt:
