# Photos filters API — fixture receipt

Tested implementation `6d0dba686838ab06004c0807df615957c64dc081`, branch
`codex/memory-v1-photo-filters-api`, isolated base
`2fc917a7cfb28ea7a74c083f324cbf5f9fd30e13`. This evidence-only follow-up does not
change the tested runtime, HTTP, tests or technical contract.

Scope: optional read-only Photos date-range/place/trip/collection filters, owned
`runtime/ingestion.py`, `shell/app.py`, focused synthetic tests, and
`docs/runtime/PHOTOS-FILTERS.md`. No schema/auth/Knowledge-service changes, no
servers, private profiles, real Photos, source writes, push or merge. Root owns
UI integration, full gate, browser matrix and final acceptance.

## Exact-commit verification

All commands ran with `/opt/homebrew/bin/python3` (Python 3.14.6), exit 0:

| Command | Observed result |
| --- | --- |
| `tests/test_photos_filters.py` | 10/0 — [filters.log](filters.log) |
| `tests/test_ingestion.py` | 27/0 — [ingestion.log](ingestion.log) |
| `tests/test_ingestion_http.py` | 5/0 — [ingestion-http.log](ingestion-http.log) |
| `tests/test_knowledge.py` | 22/0 — [knowledge.log](knowledge.log) |
| `tests/test_runtime_http.py` | 12/0 — [runtime-http.log](runtime-http.log) |
| `git diff --check` | Exit 0 |

The 76 relevant tests preserve existing names and add coverage for inclusive
capture-local dates with unknown dates excluded; filtering before pagination;
Unicode literal place matching without SQL wildcards or inferred geography;
current raw revision without needing rebuild; collection/Hidden/shared/owner
restrictions; trip current membership, unindexed/signature changes, partial
restriction and superseded trips; strict HTTP query parsing; audit fail closed.

Place/trip inputs never enter audit rows. A focused assertion checks absence of
those values and the exact existing seven-column audit schema (`sequence`, `id`,
`owner_id`, `action`, `outcome`, `count`, `created_at`). Trip access reuses the
complete current Knowledge active-trip predicate within the same read transaction.
All member restrictions are checked before combining other filters, so a stale
trip does not produce a misleading partial result or disclose its membership.

## RED and corrections retained

- [red.log](red.log): the ten new test cases ran before implementation and failed
  on unsupported service filter arguments/HTTP query keys (unittest reported two
  failures and 22 errors, including subtests). The initial custom summary counted
  subtest errors as test cases and printed a negative passed count; the harness
  now counts distinct parent test IDs. No assertions were removed.
- [audit-assertion-failure.log](audit-assertion-failure.log): added audit-schema
  assertion initially omitted the existing `sequence` column. Corrected against
  `schema/runtime-v1.sql`; query-value non-disclosure checks were retained.
- Initial 100k place scans exceeded the 600ms comparison target: p95 604.85ms
  no-match and 652.67ms last-page. The safe optimization checks bounded string
  type/length and literal match before Unicode-category validation; every matched
  field must still pass full disclosure validation. No cache/index/schema added.

## Bounded synthetic performance

Used the existing `test_knowledge_benchmark.seed` with 10k and 100k rows, then
refreshed the existing current-index trigger because that seed primarily targets
Knowledge tables. No generation rebuild or media transfer. Every row has the
same 133-byte synthetic metadata wrapper. Seven warm rounds; p95 is the maximum
of those seven observations. Timings include owner authentication and audit.

| Query | 10k warm p95 | 100k warm p95 | 100k cold |
| --- | ---: | ---: | ---: |
| Audited session baseline | 1.32ms | 1.42ms | 1.30ms |
| Photos first page, no place filter | 2.05ms | 2.35ms | 1.93ms |
| Place matches all, first 25 | 2.18ms | 1.87ms | 1.87ms |
| Place matches none, full scan | 44.33ms | 392.72ms | 399.79ms |
| Place matches all, last 25 | 50.01ms | 543.97ms | 453.98ms |

Peak process RSS was 159.72MiB on macOS. This narrowly measured fixture falls
below 600ms after correction; it is not a universal latency guarantee. Place
search is still O(N) over current candidate metadata, and larger wrappers or
different host contention can take longer. No device/ingestion throughput claim.

Raw [final measurements](benchmark-exact.jsonl) and
[pre-optimization measurements](benchmark-before.jsonl) are retained. The older
measurement's metadata-byte field used Python repr length (146), not serialized
length; final telemetry measures actual stored bytes (133). Timing comparisons
used identical source metadata. [Reproduction script](benchmark.py) preserves the
measured algorithm; its import bootstrap accepts an optional checkout path:

```
/opt/homebrew/bin/python3 docs/evidence/alpha-v1-3-photos-filters-api/benchmark.py /absolute/checkout
```

Full gate and actual UI integration are deliberately left to the integrator to
avoid duplicate runs. This receipt does not establish real-device, deployment,
or whole F3-01 acceptance.
