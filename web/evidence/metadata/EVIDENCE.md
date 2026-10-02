---
title: "Selected Metadata UI Evidence"
project: memory
type: doc
status: review
created: 2026-10-02
source: codex-desktop
---

# Selected metadata and Source consent UI

Implementation revision: `8c8dfa944f8385a148594ce4cb1187d0ffa82fc3`, based on `cf100d00cc357309a883cbb4ce68a83bb36602c2`. The evidence commit changes no runtime behavior. This folder is temporary agent-owned evidence under `web/`; the integrator may move it to the canonical release evidence directory.

## Outcome and limits

Memory now reads the actual `/api/photos` contract, with explicit media type and capture-local-day filters, 24-record pages plus a one-record lookahead, and distinct loading, empty, denied and error states. Capture timestamps retain the original offset. A timestamp instant or absent date never invents a local capture day. Presence is reported with its provenance; no location is inferred. Coverage describes selected authorized samples only, with no whole-library total. Records explicitly say media was not transferred; there are no fake thumbnails or players.

Sources reads integer or boolean consent flags separately for Hidden, Shared Library and Shared Albums. Only an explicit Save sends all three booleans and the connection ID with the in-memory CSRF token. Missing flags produce unavailable controls. Successful policy changes refresh current Sources; failed fresh reads do not reuse stale counts. Pairing and device endpoints failing independently cannot hide a successful Sources read. Existing secret lifetime, session clearing, navigation and DS assets are preserved.

This is partial F1/F3 presentation backed by the implemented bounded metadata protocol. It does not establish real iPhone operation, personal Photos acceptance, progressive enumeration, whole-library coverage, media transfer/playback, indexed capabilities, Blocks or Artifacts.

## Validation

At implementation revision `8c8dfa9`:

- `npm run build`: production build passed; Next 16.3.8 compiled and typechecked, dynamic catch-all route retained.
- `npm run typecheck`: passed.
- `npm run check:ds`: passed; complete local CSS/font/icon asset hashes remain covered by the existing asset test.
- `npm test`: 7/7. Six prior names preserved; one query-encoding/private-fetch regression added.
- `MEMORY_TEST_PORT=8769 npx playwright test`: 80/80, production Next build. The 52 previous browser tests remain by name; 28 new checks cover metadata/policy across desktop 1440×900 and mobile 390×844, both themes, with 320px overflow and visual checks. `mocked-results.json` and `preserved-test-names.json` retain the exact names.
- `/opt/homebrew/bin/python3 tests/run_all.py`: 231 passed, 0 failed.
- `/opt/homebrew/bin/python3 tests/test_stub.py`: 67 passed, 0 failed.

The initial query unit regression failed RED before query support (`api-red.log`). The metadata presentation test failed RED before its implementation (`ui-red.log`). The first expanded matrix exposed an old Sources navigation regression caused by coupling independent refresh endpoints; it was corrected before the final 80-test run. New policy and metadata scenarios cover explicit mutation, current flags, CSRF, empty/error/denied distinctions, stale-data clearing and unauthorized session loss.

The original 52 browser names are retained. The only baseline harness adjustment makes its allowed-origin assertion follow the configurable local test port. Product evolution is deliberate: `/photos` changes from honest unavailable to bounded metadata. Blocks, Trips and Artifacts remain unavailable.

## Actual Python integration, separate from mocks

`npm run test:metadata-runtime` passed 2/2 with actual Next 8767 → Python 8766 requests and no route mocks, against the final-schema synthetic fixture `/private/tmp/memory-live-fixture-f1-final`. The tested application and runtime test file are byte-identical to implementation revision 8c8dfa9; the run occurred just before that commit, while final screenshot-only changes to the mocked test and web documentation were being prepared. `runtime-results.json` and `runtime.log` preserve that timing rather than labeling it a post-commit run.

Each desktop/mobile run started a real pairing intent, submitted a synthetic native API claim, confirmed its full fingerprint, enabled Hidden through the UI, and ingested exactly three selected synthetic wrappers. It verified the preserved 23:30−03:00 capture-local day, an unknown-date third-party video, no raw metadata or media rendering, type/day filtering, and immediate Hidden exclusion after an explicit policy change. Cleanup revoked each synthetic device and verified credential denial. API clients are synthetic fixtures, not a real iPhone connector.

The fixture retains two additional Source/library aliases, six synthetic records (four visible under current policy; two Hidden restricted) and two added revoked devices. The preexisting Source and two revoked devices were not reset or deleted. Both library aliases are isolated from the preexisting fixture. Local Next QA was stopped after the run; ports 8767 and 8769 were released.

## Visual review

Reviewed `desktop-light-metadata.png`, `mobile-dark-metadata.png` (320px) and `desktop-light-source-policy.png`, plus the full four-theme/project matrix. Original timestamp text wraps inside a 320px card without horizontal overflow; local dates, unknown dates and media-unavailable state remain readable. Mobile bottom navigation keeps the existing keyboard focus/scroll padding fix. Other screenshots retain the corresponding light/dark and real-fixture views. Screenshots capture the app's actual scrolling container, not a reconstructed mockup.

The integrated browser was unavailable in this environment during the frontend work; the approved Playwright fallback supplied production-build browser proof. No new dependencies, remote fonts or paid services were introduced.
