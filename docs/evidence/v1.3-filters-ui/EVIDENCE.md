---
title: Photos period place trip and collection filters
project: memory
type: evidence
status: active
created: 2026-10-03
source: codex-desktop
---

# F3-01 bounded filter gap closure

Base2fc917a7cfb28ea7a74c083f324cbf5f9fd30e13; implementation669c0fd. Own checkout `/private/tmp/memory-v1-photo-filters-ui`, branch `codex/memory-v1-photo-filters-ui`. The production build and browser suite ran on the identical implementation tree immediately before that commit. An evidence-only commit follows. No backend/schema/viewer/original-resource paths were changed; no push, merge or release claim. Integrator owns full Python gate, combined matrix and actual API/browser proof.

Photos now submits explicit server filters for an inclusive known-capture-local-day period, literal source place/country/city text, current authorized trip ID and personal/shared-library/shared-album/unknown collection. The existing single-day/type controls remain. A single day clears the period and a period clears the single day. Invalid dates, reverse ranges, malformed trip IDs/control text and unknown enums fail before requesting. Unknown source days/places are never inferred. Filters only narrow current authority and never enable shared-category consent.

Photos requests retain limit25 (24 visible plus one lookahead), offset and every applied filter on pagination; no client-side filtering of the fetched page or whole-library total. Drafts stay in component memory. Apply and Clear remain explicit. Collection buttons expose aria-pressed plus the DS tonal selected state.

Trip choices load only on an explicit Choose/Refresh/Next action through the existing owner endpoint, limit20 plus cursor. No ambient refresh. Starting a trip request clears old titles/choices/results and aborts an older Photos read. Failures do not re-display cached choices;401 clears owner session. Photos failure clears prior results and selected trip title/choices. An empty choice page and a failed request are distinct. Long trip titles use the existing wrapping DS button. Current-policy authority stays on Python, including a well-formed but restricted/stale trip404.

## Commands and observed results

- New browser behaviors were RED3/3 on the baseline production build (`red-browser-retry.log`): missing period and trip controls. The added query validation unit was RED (`red-unit.log`). No existing test was renamed or skipped.
- Final production `npm run build`, `npm run typecheck`, `npm test`13/13, `npm run check:ds`, and `git diff --check` pass. See `final-*.log` and `diff-check.log`.
- `MEMORY_TEST_PORT=8771 ./node_modules/.bin/playwright test tests/metadata.spec.ts`: final52/52 across desktop1440×900/mobile390×844 and light/dark, including320px overflow, keyboard Enter, screenshots, server request/pagination, trip choice cursor,404/503/401 clearing, reversed dates, mutual single-day/range reset and stale in-flight Photos cancellation.36 preexisting cases remain;16 were added. Final receipt `final-browser.log`.
- First green attempt40pass/12fail was a harness selector ambiguity: both the product alert and Next route announcer have role=alert. Scope now targets main; no error/content expectation was removed. `browser-green.log` retained. A retry launched before its path typo was noticed was stopped (`browser-green-final.log`); `browser-verified.log` then passed52. Final styling/screenshot follow-up was rebuilt and retested52 on the exact final implementation.
- Environment setup attempts retained: an external node_modules symlink failed Turbopack root validation (`red-build.log`); copying the already installed locked dependencies into this checkout fixed it (`red-build-retry.log`). Initial sandbox bind8771 EPERM is in `red-browser.log`; authorized isolated browser execution used only8771. No dependency versions or package config changed.

The four attached320px screenshots are synthetic light/dark views of filter fields and trip choices. They were visually reviewed; no horizontal overflow. Playwright is the repeatable browser fallback already used for this UI matrix. No personal Photos, remote fonts/services or fixture deletion occurred. Parent-controlled8766/8767 were untouched.

This closes the frontend portion of the original goal line204. The backend agent owns filtering before pagination/current authorization; the integrator must pair these commits, run actual HTTP/UI checks and preserve receipt identity. Physical iPhone, owner sample, deployment and complete F0–F4 acceptance remain external and unclaimed. VERSION remains0.1.0.

## Pending-response validation follow-up

Root review identified an in-flight Photos read could survive local invalid-filter validation. The targeted regression failed1/1 before correction (`invalid-pending-red.log`): loading hid the validation error. Validation failure now aborts the current Photos read and trip-choice read, clears selections/choices/results, sets loading false and exposes the actionable error. A late response cannot restore those states. This is a narrowly scoped follow-up after669c0fd/1fa0c83; labels and HTTP contract are unchanged. Follow-up production build, TypeScript,13units and DS pass (`invalid-pending-*.log`). Final metadata matrix receipt records56 cases, retaining all previous names and adding the new race case across four projects. The integrator owns exact combined240-case matrix and actual runtime proof after integration.

Final implementation follow-up8073a28e2f3ee941a958e28167fcc24d850d18e8:56/56 passed. Its web tree matches the just-built/tested tree; this receipt-only commit does not change it. No test server remains from the completed port8771 Playwright run.
