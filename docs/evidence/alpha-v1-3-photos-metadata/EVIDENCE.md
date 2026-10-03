# Photos explicit location and evidence — fixture receipt

Tested implementation: `b1b6d2d127ee6c513a077378ab2e6e7be19d61d5`.
Isolated branch `codex/memory-v1-3-photo-evidence`, base
`07b5f0bf10563756a6d71d331fe167a27d45bd7b`. This evidence-only follow-up leaves
the tested implementation unchanged. F3-01 software projection/UI proof only;
real Photos, physical device, deployment and full F3 acceptance remain outside
this fixture receipt. The integrator owns the final combined gate and matrix.

## Behavior and proof

| Criterion | Observed proof |
| --- | --- |
| Explicit current location without guessed geography | `test_photos_location_is_explicit_current_and_evidence_requires_current_index`: raw source aliases, zero coordinates, explicit place/city, revised metadata, no raw leakage. |
| Current indexed evidence only | Same test verifies null before rebuild, exact revision after rebuild, null after revision change, new revision after rebuild and no rows after revocation. |
| Invalid source fields remain unknown | `test_photos_reject_malformed_location_and_do_not_infer_geography`: absent/malformed location, booleans, out-of-range/incomplete coordinates, huge integer, control/padded/overlong text, malformed geography. |
| Privacy, audit and pagination retained | All 27 ingestion and 5 actual ASGI ingestion/owner transport tests pass, including owner isolation, audit failure, scope/Hidden/shared restrictions and metadata non-disclosure. Existing 22 Knowledge tests also pass. |
| Photos place, evidence, missing/revoked/session behavior | All 36 metadata Playwright cases pass across 1440×900 and 390×844, light/dark; new cases check literal source text, zero coordinates, unknown city, unavailable evidence, focus return, refresh closure, 404 clearing and 401 sign-out. 320px horizontal-overflow assertion passes. |

All tests use synthetic private temporary stores or intercepted synthetic browser
responses. No personal library, external network API, geocoding or source mutation
was performed. Browser proof uses the actual built Next UI with deterministic
Playwright interception; it is not an actual native import or unmocked end-to-end
claim. Images were visually inspected at mobile dark 390px and 320px.

## Commands on the tested commit

| Command | Result / log |
| --- | --- |
| `/opt/homebrew/bin/python3 tests/test_ingestion.py` | Exit 0, 27/0 — [api.log](api.log) |
| `/opt/homebrew/bin/python3 tests/test_ingestion_http.py` | Exit 0, 5/0 — [http.log](http.log) |
| `/opt/homebrew/bin/python3 tests/test_knowledge.py` | Exit 0, 22/0 — [knowledge.log](knowledge.log) |
| `cd web; PATH=/opt/homebrew/bin:$PATH MEMORY_TEST_PORT=8793 node node_modules/@playwright/test/cli.js test tests/metadata.spec.ts` | Exit 0, 36/36 — [browser.log](browser.log) |
| `cd web; PATH=/opt/homebrew/bin:$PATH npm run build` | Exit 0, normal Turbopack production build and TypeScript — [build.log](build.log) |
| `cd web; PATH=/opt/homebrew/bin:$PATH npm run check:ds` | Exit 0 — [design-system.log](design-system.log) |
| `git diff --check` | Exit 0 |

Runtime versions: Node 24.14.1, Python 3.14.6. Existing pinned dependencies were
copied locally without installation or dependency changes. A first symlink-based
Turbopack attempt failed because the link escaped its filesystem root; an
intermediate webpack build succeeded, then the final normal build above passed
using the local dependency copy. First sandboxed browser startup received EPERM
on the loopback listener; the same synthetic command ran with approved escalation.

## Recorded RED before GREEN

- New API regressions: two missing `location` KeyErrors before implementation —
  [api-red.log](api-red.log).
- Huge integer coordinate: reproduced OverflowError in existing coordinate
  validator, then Photos projection treats it as unavailable —
  [overflow-red.log](overflow-red.log). The separate existing Knowledge rebuild
  robustness issue was reported to the integrator, outside this slice's scope.
- New browser cases against the pre-change build: missing source place and missing
  Inspect evidence button, 2 failed — [browser-red.log](browser-red.log).

## Screenshots

- [Source location, desktop light](location-desktop-light.png)
- [Source location, 320px dark](location-320-dark.png)
- [Current evidence, mobile dark](evidence-mobile-dark.png)

No schema, native connector, MediaViewer, original request, shared strategic or
release-version files changed. No push or merge was performed by this subtask.
