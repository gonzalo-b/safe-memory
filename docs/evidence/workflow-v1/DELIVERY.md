# Automatic delivery without Pro

The active Codex agent owns merge after exact-SHA tests and QA. Main is the
default branch. No paid plan, native auto-merge or background watcher.

## Red before green

The first pre-merge gate on c145129 failed with 72 passed / 1 failed:
`Days: line spans two dates` expected August 21–22, while rolling fixtures on
September 21 correctly produced August 22–23. Merge was not attempted.

The test now fixes the fixture clock for its exact golden assertions and also
checks rolling dates across the next day, new year and leap-day boundary.
Production code and existing assertions/names remain unchanged.
