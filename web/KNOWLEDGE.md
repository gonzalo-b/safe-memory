# Owner knowledge interface

F2 HTTP and frontend slice; direct-service behavior is defined in `../docs/runtime/KNOWLEDGE.md`. This interface does not claim real-device acceptance or introduce agent Grants.

## HTTP contract

All routes require the current owner cookie. Responses use `no-store`; current source policy, current indexed revision and audit are checked by `KnowledgeService`. Device credentials do not authorize these routes. Caller-supplied owner IDs and additional body/query fields are rejected.

- `GET /api/knowledge/catalog` returns the catalog, availability and projected coverage.
- `POST /api/knowledge/answer` accepts exactly required `capability`, optional `params`, `scope`, `limit`, `cursor`. This is read-only: the server verifies exact Origin, owner session and audit. It **does not verify the mutation CSRF token**. The frontend sends the token because its common POST helper requires it; that header alone is not server enforcement.
- `GET /api/knowledge/evidence/{asset_id}` resolves a currently admissible fact. IDs are exactly 32 lowercase hex characters.
- `GET /api/knowledge/trips` and `GET /api/knowledge/trips/{trip_id}` accept only `limit` and `cursor` query parameters, once each.
- `GET /api/knowledge/areas` accepts only `limit` and `cursor`.
- `POST /api/knowledge/rebuild` accepts required `request_key`, optional `policy`.
- `POST /api/knowledge/trips/correct` accepts required `request_key`, `action`, optional `trip_id`, `expected_revision`, `payload`.
- `POST /api/knowledge/areas` accepts required `request_key`, `area`, optional `area_id`, `expected_revision`.

The last three mutations verify CSRF transactionally in the domain service, in addition to the adapter's Origin and owner checks. Mutation idempotency keys stay in live component memory; retries of the same unsuccessful payload reuse the key. They are reset after an acknowledged receipt. No private answer, evidence, correction draft or credential is placed in browser storage or URLs.

## Screens

Blocks offers the nine allowlisted query families, including paged indexed evidence. The user supplies local dates/year, explicit month/day and an as-of date for occasion history. Exact February 29 uses leap years only; unknown occurrences remain visible. Coverage distinguishes unknown dates, indexed assets and current assets awaiting rebuild. People is displayed only when source-provided metadata exists. Results are rendered from typed fields with React text escaping; the server's Markdown is never inserted as HTML.

Trips shows current candidate summaries, bounded evidence, observed dates/gaps, saved revision and retained lineage. Manual, rename, dates, confirm, dismiss, merge and split forms submit explicit owner corrections with current revisions. Manual trips are clearly owner assertions without source evidence. Historical areas support multiple dated intervals, explicit coordinates/radius and review of inferred suggestions; commuting suppression requires explicit confirmation and a subsequent rebuild.

Debug can rebuild the coherent Photos knowledge generation and then reload the actual catalog. Failure never reports a successful generation. Requests clear stale private views before loading and on failure;401 clears the owner session. Unmount/route changes abort requests. Evidence inspection uses only exact same-origin ID paths. Existing logout, BFCache clearing, themes, navigation and media behavior remain in the shared shell.

## Development evidence staging

Base `a298df3a14cba6757eb6c9c0416d0a2b09e5c65d`, isolated branch `codex/memory-v1-2-knowledge-ui`. Backend/service commits were cherry-picked as `c6903b7` and evidence as `294f648`; runtime/store/schema are owned by the integrator and unchanged in this UI slice.

- New HTTP tests: RED 5/5 before routes; GREEN 5/5 after implementation.
- New API path guard unit: RED rejects malformed knowledge paths before the fix; exact 32-hex evidence/trip paths now have a separate allowlist.
- New browser tests: RED 7/7 on the baseline production build (desktop-dark), before component wiring. First sandbox run could not bind localhost8769; the authorized run outside the sandbox captured the actual behavior failures.
- TypeScript, unit 10/10 and DS guard passed before the first browser GREEN attempt.
- Full mock matrix passed 148/148 across desktop/mobile and light/dark; baseline 120 tests retained by name. Actual Python integration is pending. No browser tests have been renamed or skipped; existing unavailable Artifacts behavior remains covered under its original test name.

Temporary logs are `/private/tmp/memory-knowledge-http-{red,green}.log`, `memory-knowledge-ui-{red,unit-red,unit-green,typecheck,ds,build}.log`. The integrator files final exact-revision evidence separately from this implementation note.

The first browser GREEN attempt identified help text incorrectly joining accessible field names; Field now gives the input its visible name and a separate aria-describedby reference. Selector ambiguities were narrowed to the fact heading/main alert, without removing assertions. Screenshot review at320px also corrected a success notice whose flex children squeezed the message into columns; the notice now has one readable content block.

A further privacy regression was reproduced RED: an evidence inspector403 hid the inspector's fact but left its parent answer visible. Inspector failure now clears parent answer/coverage or trip detail. The final new-feature matrix passes32/32 after that fix; the prior complete matrix passed148/148 with all120 existing cases retained. Backend full gate318/0 and explicit contract67/0 also pass. Production build, TypeScript, unit10/10 and DS guard pass. Actual runtime tests are prepared in `tests/knowledge-runtime.spec.ts` and require the explicitly synthetic credentials plus the local Python API; they create only synthetic metadata and revoke their test device/Hidden consent at completion.
