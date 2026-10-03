---
title: "Indexed Knowledge and Trip Corrections"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Owner knowledge service contract

`KnowledgeService(store)` is a stdlib-only direct service. HTTP/UI integration is separate. Every method receives the current owner session token; writes also require its CSRF token. Caller-supplied owner identity is never accepted. Scope only narrows owner policy and is not a Grant or remote-agent authorization. Legacy MCP remains separate.

## Frozen signatures

- `rebuild(token, csrf, request_key, *, policy=None)` builds a coherent Photos knowledge generation; policy optionally supplies `max_gap_hours`, `max_leg_km`, `min_observations` and `habitual_min_days`. Returns generation ID, definition and built timestamp. Idempotent keys are owner-scoped.
- `catalog(token, *, scope=None)` returns the allowlisted capabilities and safe coverage/freshness.
- `answer(token, capability, params=None, *, scope=None, limit=50, cursor=None)` returns a bounded result envelope.
- `evidence(token, asset_id, *, scope=None)` resolves only a currently authorized indexed revision.
- `trips(token, *, scope=None, limit=50, cursor=None)` and `trip(token, trip_id, *, scope=None, limit=50, cursor=None)` return current projected trips and paginated evidence.
- `habitual_areas(token, *, limit=50, cursor=None)` lists currently admissible inferred/confirmed historical areas.
- `put_habitual_area(token, csrf, request_key, area, *, area_id=None, expected_revision=None)` creates or revises an area. `area` has `label`, approximate `lat`, `lon`, positive `radius_km`, inclusive `start`, exclusive `end`, explicit boolean `confirmed`, optional `evidence_ids` (maximum 200). Editing requires the exact current revision.
- `correct_trip(token, csrf, request_key, action, *, trip_id=None, expected_revision=None, payload=None)` accepts only the actions below. Existing-trip writes require its exact current revision. Retries return IDs/current projected results, never a cached private title or evidence body.

Trip actions: `manual` has `title`, inclusive `start` and `end`, optional `evidence_ids` (maximum 200); `rename` has `title`; `dates` has inclusive `start` and `end`; `confirm` and `dismiss` have an empty payload. `merge` has `trip_ids` (2–20), `expected_revisions` mapping every selected ID to its exact revision, and optional `title`; it creates a new durable ID and retains all parents/lineage. `split` has `date` (first date of second child) and optional two-element `titles`; it partitions known-date evidence, creates two durable IDs and retains the parent. Unknown-date evidence requires correction before splitting. Source timestamps and Source metadata never change.

Capabilities: `travel.where_on_date` (`date`), `travel.where_in_range` (`start`, exclusive `end`), `travel.where_in_year` (`year`), `travel.countries_visited` / `travel.cities_visited` / `photos.statistics` (optional `start`, exclusive `end`), `photos.on_this_day` (`month_day`), `travel.occasion_history` (`month_day`, `count`, `as_of`, optional `leap_day_policy`). Missing occasion month/day returns needs_input. Exact leap-year-only February 29 is the reversible default. N means calendar occurrences including unknown years, not N matching observations. No system clock silently chooses an occasion.

Scope keys: optional `connection_ids` (up to 100 exact owner connections), inclusive `start`, exclusive `end`, and `fields` drawn from `id`, `capture_time`, `location`, `geography`, `media_type`, `owner_presence`, `people`. An empty list of fields or connections admits no corresponding disclosure. Dates absent/redacted remain unknown before matching/aggregation; location cannot supply geography by geocoding or text guessing. Page limit 1–200; signed cursors are session/generation/scope/query/policy-bound and stale cursors fail explicitly.

## Normalization and safety

Facts preserve the wrapper's original capture timestamp and only use `capture_day` when its basis is `capture_offset`. Native `PhotosReader` exposes an instant, not a reliable capture offset; it therefore produces unknown local-day facts. Its raw `location.latitude/longitude` are explicit coordinates, not proof of owner presence. Optional imported enrichment is `metadata.geography` with explicit country_code/country/city_id/city. No country is inferred from a place label. People is unavailable unless imported metadata explicitly identifies source-provided People with provenance; no recognition/tagging is introduced.

Each read rechecks owner, connection consent, limited selection and asset current revision before matching, aggregation, evidence or Markdown. Generation counts and cached trip boundaries are never authorization. There is no cross-query answer cache. Raw metadata is parsed one record at a time during rebuild, then queries use indexed typed facts. Old generations and corrections are retained; a failed rebuild cannot replace the published generation. Unknown chronology never becomes invented continuity.

This document freezes direct-service integration signatures; it does not claim shipped HTTP/UI, real-device evidence or complete F2 acceptance.

## Result shapes and pagination

`answer` returns `{capability, definition_version, generation, status, data, next_cursor, time_basis, counting_rule, coverage, freshness, markdown, limitations}`. `photos.records` is the supporting paginated fact query; optional filters are `start`, exclusive `end`, `country_code`, `city_id`, and `media_type`. Date/range/year and On This Day return fact pages. Country/city rows include a bounded aggregate plus an `evidence_query` resolving their complete evidence through `photos.records`. Occasion rows include each requested calendar occurrence, observed/unknown status, count, a bounded observation sample and an `evidence_query`; the page limit caps observations across all occurrences. Follow evidence queries for additional observations rather than treating the sample as complete.

A fact is `{capture_time, capture_day, time_basis, location, geography, media_type, owner_presence, continuous_presence:false, evidence?, people?}`. The optional evidence object is `{asset_id, revision, connection_id}` and appears only when `id` is permitted. Location and geography contain only explicit non-null projected fields. People is an array of `{source_id, name}` only when permitted and `metadata.people_provenance` is exactly `source_imported`; absent metadata produces an empty array and catalog availability `unavailable`. Native PhotosReader currently does not provide that People enrichment.

Statistics count one current authorized asset, separating photos, videos and Live Photos; derivatives do not become new Records. An empty admissible projection returns `no_evidence` with an observed count of zero, not a whole-library zero. Coverage includes indexed/current-unindexed records, unknown time, located records and first/last observed day; excluded totals are deliberately unavailable. Source checking is `unknown`; a knowledge rebuild is not a new device scan. A current revision absent from the generation contributes to stale/unindexed coverage and cannot resolve through evidence until rebuilt.

Trip list entries contain `{trip_id, revision, state, title, start, end, boundary_basis, kind, observed_start, observed_end, observed_day_count, unknown_time_records, observed_dates, observed_dates_has_more, gaps, gaps_complete, continuous_presence:false, owner_presence_confirmed, evidence_count, evidence:[], has_more_evidence, lineage, definition_version}`. Detail adds paginated fact evidence, `next_cursor` and `generation`. List envelopes contain `data`, `next_cursor`, `generation` and `definition_version`. Observed dates are capped at 200 and gaps at 199 ranges, with explicit incompleteness; they are not interpolated presence. Lineage contains `{parent_id, child_id, action}` only while both identities remain admissible. A correction receipt is `{operation_id, trip_ids, revisions, status:'applied'}`; replay rechecks visibility and may return no trip IDs after restriction.

`habitual_areas` returns `{data, next_cursor, definition_version}`. Each area has `id`, current `revision`, `label`, `lat`, `lon`, `radius_km`, inclusive `start`, exclusive `end`, and `confirmed` (SQLite boolean 0/1). Area writes return `{area_id, revision}`. Replays return an unavailable result if their source anchors no longer qualify.

## Detection, durable corrections and conservative disclosure

Definition `indexed-photos-1` uses distance/time policy `distance-time-1`: consecutive known local-date, located observations within 72 elapsed hours and 2,000 km form a candidate; minimum observations defaults to one. Rebuild overrides are recorded in the generation. UTC instants only order elapsed intervals; original timestamps and local-day semantics remain intact. Known third-party evidence is excluded. Unknown provenance stays unknown and never proves owner presence. Multiple cities may belong to one candidate; gaps remain unknown. A single-day candidate is not proof of a trip, and multiple dates do not prove an overnight stay.

Habitual suggestions group explicit coordinates rounded to 0.1 degrees within each observed calendar year, require 14 distinct observed days by default, and propose a 15 km radius limited to their observed historical interval. These configurable detection hypotheses need owner review; they are not inferred home/work truth. Multiple historical areas coexist. Only explicitly confirmed, currently admissible areas suppress commuting observations during their own interval. No current residence is applied to earlier years.

Candidate hashes include the definition, grouping configuration and sorted stable asset IDs. Durable owner trip IDs are separate: inferred candidates reconcile by greatest member overlap, with deterministic ID tie ordering. Existing corrected/manual/dismissed membership is excluded from automatic grouping; rebuild cannot overwrite owner corrections. Merge creates a new ID and preserves parents; split creates two IDs and preserves the parent. All revision snapshots, member anchors, request receipts and lineage are retained. Requests use exact owner-scoped idempotency keys and exact expected revisions; conflicting retries/revisions return 409. Source asset revisions are never updated by these operations.

Saved titles, dates, area centers and lineage depend on every evidence anchor. Each read checks the current source permission, category consent, limited selection and current indexed revision, plus the normalized evidence signature. Equivalent metadata reimport may change the source revision while retaining its semantic signature and durable correction. Changed/restricted evidence hides the entire dependent trip/area, including saved title and broad boundaries. This slice deliberately denies a trip whose dependencies cannot all be projected; it does not reveal a partial cached title or boundary. Narrow field scopes therefore cannot return trips, and narrow date/connection scopes must admit every anchor. Manual owner assertions without evidence are visible only in the unrestricted owner view, clearly distinguished from inferred observations.

When source evidence has changed but remains admissible and indexed, an explicit new correction can re-anchor a trip. Untrusted prior title/date overrides are cleared unless the new action supplies them. Restriction itself cannot be overridden with a correction. Restore retains corrections and generations but inherits source quarantine and session/device revocation; preserved rows do not resurrect access. Rebuild publishes its new generation only within the successful audit transaction; normalization, SQL or audit failure rolls back the whole generation and leaves the previous generation current. The caller receives the failure; only completed rebuilds have operation receipts in this slice.

## Validation scope

Direct service tests cover current-policy and revision filtering before matching/counting, redacted fields and evidence IDs, explicit geography and unknown native local day, exact leap occasions with unknown years, failure/audit rollback, manual and inferred corrections, optimistic concurrency, idempotency, merge/split lineage, semantic reimport, historical confirmed areas, third-party exclusion, dismissal persistence, session/CSRF/cross-owner denial, backup/restore quarantine and signed stale cursors. The runtime dependency guard permits only `blocks.capabilities` and `blocks.trips`, scans both transitively and rejects other internal helpers, relative-import bypasses and network/process dependencies.

`tests/test_knowledge_benchmark.py` is a reproducible synthetic benchmark. Its default run is a bounded correctness test; `--records 10000` and `--records 100000` measure a fresh generation and 12 warm runs of six query families. The seed inserts valid synthetic wrappers in batches to measure knowledge computation separately from ingestion/device throughput. Raw JSON is parsed one record at a time; typed SQLite staging and paging avoid a whole-library raw buffer. Peak RSS includes the prior scrypt login peak and is reported alongside that baseline. Retained generations increase disk on later rebuilds; the measured disk size is a fresh store with one generation.


Optimized precommit measurement on the shared macOS development host (2026-10-02); 12 warm samples per family. Numbers describe this synthetic distribution and do not establish a production SLA.

| Measure | 10,000 assets | 100,000 assets |
|---|---:|---:|
| Fresh rebuild | 0.536 s | 12.239 s |
| Inferred candidates | 501 | 4,999 |
| Prior scrypt peak RSS | 158.50 MiB | 158.72 MiB |
| Process peak RSS | 160.70 MiB | 158.72 MiB |
| Fresh store size | 20.37 MiB | 201.78 MiB |
| Date query p95 | 16.61 ms | 198.32 ms |
| Year query p95 | 14.87 ms | 123.13 ms |
| Countries p95 | 21.40 ms | 192.27 ms |
| Statistics p95 | 31.83 ms | 269.18 ms |
| Ten occasion dates p95 | 12.14 ms | 158.91 ms |
| Twenty-trip page p95 | 25.20 ms | 287.83 ms |

That precommit run met the 300 ms target for the six measured warm families, narrowly for trip pages. Earlier 100k measurements exceeded it: first completed p95 values ranged 324–1,018 ms, and a later shared-host run ranged 546–4,597 ms. The original grouping run was interrupted after more than three minutes without publishing a generation; a temporary `(group_id,asset_id)` index removed that scan. Final query changes combine exact live coverage into one scan and use indexed correlated anchor checks instead of materializing all facts for trips. No permission or answer cache was introduced. Historical generations, different data distributions, concurrent imports, cold storage and larger libraries remain unmeasured budgets; preserve these earlier results when interpreting the final run.


## Exact candidate receipt

Tested implementation: `720cf9a9b82b5eb2ac33a45303934494db3602e5`, following isolated schema commit `e48592e9456eed0f86537e8891fe43fc3f94f050`. The subsequent evidence commit changes this document only.

- `/opt/homebrew/bin/python3 tests/run_all.py`: **291 passed, 0 failed**, exit 0. Includes knowledge 19, knowledge migration 4, synthetic benchmark correctness 1 and domain/runtime 18; previously named suites remain present.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: **67 passed, 0 failed**, exit 0.
- `python3 -m py_compile runtime/knowledge.py tests/test_knowledge.py tests/test_knowledge_benchmark.py tests/test_runtime.py`: exit 0 with the configured Python interpreter.
- Exact-commit `tests/test_knowledge_benchmark.py --records 10000` and `--records 100000`: exit 0, counts exactly matched their indexed assets; 12 warm samples per query family.

| Exact-commit measure | 10,000 assets | 100,000 assets |
|---|---:|---:|
| Fresh rebuild | 0.523 s | 13.276 s |
| Prior scrypt peak RSS | 157.20 MiB | 156.97 MiB |
| Process peak RSS | 160.94 MiB | 156.97 MiB |
| Fresh store size | 20.37 MiB | 201.89 MiB |
| Date query p95 | 19.37 ms | 126.99 ms |
| Year query p95 | 21.67 ms | 205.73 ms |
| Countries p95 | 22.94 ms | **338.55 ms** |
| Statistics p95 | 25.37 ms | 207.46 ms |
| Ten occasion dates p95 | 12.91 ms | 186.86 ms |
| Twenty-trip page p95 | 30.37 ms | 298.12 ms |

The exact-commit country aggregate exceeded the 300 ms target despite passing in the preceding run. Performance acceptance is therefore not claimed across all families. Measurements use small synthetic metadata wrappers without media bytes; concurrent host activity is not isolated. These results do not establish real-library, cold-query, subsequent-generation or native-device performance.

Evidence handoff logs: `memory-knowledge-fullgate.log`, `memory-knowledge-contract.log`, `memory-knowledge-720cf9a-10000.{json,log}`, `memory-knowledge-720cf9a-100000.{json,log}` under the integrator's temporary evidence staging directory. Earlier RED logs retain the missing-service/method failures, schema guard regression, incorrect evidence-summary flag and malformed area identity regression. The import guard regression separately proves that a forbidden transitive import, an unapproved Blocks helper and a relative-import bypass are denied. The integrator files these logs with the overall candidate evidence; no release or device acceptance is implied by this backend receipt.

## Live query performance follow-up

Country/city and statistics answers now compute filtered aggregates and exact
scope coverage in one live-policy pass. Projection still precedes matching;
unindexed/current records and unknown dates remain explicit. A cursor's state
fingerprint is computed only when a cursor is supplied or another page exists.
Trip detail resolves membership before date sorting, avoiding a whole-generation
scan for each visible trip. No permission cache or schema change is introduced.

The original country p95338.55ms miss remains in the history. Follow-up100k
synthetic runs recorded country p95193.74/287.23ms and trips20.43ms after fixing
the query plan (prior393.42ms). A later concurrent-host run recorded day1087.85,
country499.73, statistics356.47 and trips39.37ms; it does not pass the300ms target.
All runs are retained; no best-of selection is a final acceptance receipt. The
benchmark now also records an audited session-read baseline and per-query CPU
p95, to distinguish host/audit I/O contention from calculation cost at final
integration. The current goal requires measured bounds and honest evidence;
these synthetic measurements are not a real-library or deployment SLA.

## Local Alpha capacity budget for final integration

Before the final candidate measurement, the integrator sets a bounded local QA
budget for one fresh100,000-record generation: rebuild at most30s, peak process
RSS at most256MiB, fresh store at most384MiB, and each of the six warm query
families p95 at most600ms across12 samples, with current authorization and audit
included. This is a subsecond interactive envelope for the current shared Mac,
not a new public SLA. The300ms engineering target remains visible and missed
runs above are not relabeled as passing it. Concurrent import, cold I/O, retained
multiple generations, edge/network and a real library remain separate pending
measurements. A failed final measurement remains a failed budget result; no
selection of a best run is allowed.

Final candidate2fc917a measured100,000 facts/4,999 trips: rebuild13.108s, peakRSS156.64MiB, freshstore238.49MiB. Warm p95ms: day200.40,year147.14,countries165.76,statistics281.14,occasion96.01,trips25.96; auditedsession2.39. It passes the declared600ms/30s/256MiB/384MiB local envelope and this run also meets300ms. Prior300ms misses are retained and no general guarantee follows from this run. JSON/log in ../evidence/v1.4-integration.
