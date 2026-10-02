---
title: "Memory Web Foundation"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Memory web foundation

Next.js App Router, React and TypeScript frontend for the Python runtime contract in `docs/runtime/HTTP.md`. It implements sign-in/session restoration, CSRF logout, Overview, Sources, safe Debug/access events, selected Photos metadata and private media viewing, separate Source collection consents, appearance and honest unavailable feature screens. Python owns identity, authorization, audit and persistence. This package does not provision owners or copy the store into browser storage.

From `web/`, on Node 24:

```sh
npm ci
npm run build
npm run typecheck
npm test
npm run check:ds
npm run start
```

Next listens only on `127.0.0.1:8767`. `/api/*` rewrites to Python at `127.0.0.1:8766`; run the Python service separately, configured for the browser origin. Production serves the existing HTTPS origin through its approved reverse proxy. Starting this package locally is not deployment evidence. Development uses `npm run dev` on the same loopback port. Telemetry is disabled in both scripts.

The browser stores only `m-theme`. Session credentials are HttpOnly cookies controlled by Python; CSRF lives only in component memory. All API requests use same-origin credentials, `cache: no-store`, and refuse redirects. An expired session clears displayed private data. Errors never echo unknown backend response bodies. Imported text is React text, never raw HTML. No remote font loading, image optimizer route for private media, public signup, fake login or client store exists.

## Device pairing in Sources

Sources uses the Python pairing contract: start an intent with session/CSRF, show its one-time code in component memory, manually refresh pending requests, compare the complete device name and fingerprint, and explicitly confirm that exact claim. The full fingerprint is sent unchanged. Opening Sources never starts or confirms pairing. Codes disappear on expiry, reload, navigation or session loss; no code or credential enters URLs, browser storage or logs. The browser does not receive the device credential.

Registered devices are loaded from Python. Revoke selects a specific device and requires an explicit second action. Confirmation and revocation refresh Sources, pending requests and devices from the API. Registered means a device binding exists; Photos remains restricted/awaiting_ingest, with no inferred import success or implicit permission. Lists refresh manually while Sources is open, and pending requests are aborted when the screen unmounts. Failed requests remain visible failures; a 401 clears the session and all displayed pairing state.

## Selected Photos metadata

Memory reads `GET /api/photos` using server-side media-type and capture-local-day filters. It preserves each original capture timestamp; missing local-day evidence remains unknown even when a capture instant exists. Twenty-four records are shown per page, with one lookahead record determining whether Next is available. Pagination does not claim a whole-library total. Loading and denied/error states clear previously shown records, and a 401 clears the owner session. Metadata cards contain no thumbnail, raw metadata, location inference or inferred owner presence. Open media checks current access and availability before displaying transferred components.

Coverage is explicitly a selected, authorized sample. Empty results describe only the current authorized query. Sources reads the API's separate Hidden, Shared Library and Shared Albums flags; each choice remains independent and is submitted only by Save source policy with the current CSRF token. Missing policy fields disable the controls rather than inventing defaults. A successful write refreshes Sources from Python; failed refreshes do not reuse prior counts. Pairing and device refresh failures cannot hide a separate successful Source read.

## Private media viewer

Open media reads the current authenticated `/api/photos/{asset_id}/media` manifest. Its exact asset and component IDs, roles, MIME types, sizes and ready/partial/not-transferred state are checked before a component can become a URL. Component paths are constructed as same-origin `/api/media/{component_id}`; no server-provided URL, public path, image optimizer, blob cache or browser storage is used. The Python endpoint owns authorization, audit, no-store responses and byte ranges.

A native modal dialog uses DS surfaces, makes the background inert, closes with Escape or Close viewer, and returns focus to the opener. A transferred still uses an image element. Video and Live Photo motion use native controls with audio unchanged and no autoplay or automatic muting; a Live still is its poster. Partial and missing components remain explicit, including unavailable motion/sound when only the still exists. No original-copy request UI is offered.

Refresh clears the prior frame before rechecking its manifest. Media decode/stream errors also remove content immediately and perform a private HEAD check so a 401 clears the owner session; other failures remain honest errors. Closing, navigating away and changing filters unmount the viewer and stop its video. Already displayed bytes cannot be remotely erased; refresh and new requests enforce current policy, with the backend rechecking ongoing reads.

## Design system

`public/` reuses the complete verified `ui/` stylesheet, Inter font and icon asset. `vendor/memory-ds/` preserves the supplied React Button, Badge, ModuleTile and Icon/Sprite wrappers with their dependencies. File hashes are in `asset-provenance.json`. Product CSS contains only layouts/tokens and is scanned by the existing guard. Local-asset tests compare the complete copied CSS and binary assets, not merely a suffix. No monospaced surface or new font dependency was introduced.

## Validation

`npm run test:e2e` starts the **production build** on loopback and runs synthetic HTTP-response mocks at desktop/mobile in both themes. It proves rendering, cookie handling in the browser, CSRF construction, error/401 transitions, safe text, keyboard/focus and local assets. It does not prove backend authentication, authorization or persistence.

`npm run test:runtime` runs separately against an already running Next and Python pair, with an explicitly provisioned synthetic account supplied through `MEMORY_TEST_USERNAME` and `MEMORY_TEST_PASSWORD`. It uses no request mocks and checks actual session cookies, API rewrite, empty runtime, diagnostics, reload and logout denial. It must never use a personal Photos account or dataset. Outputs go to ignored `runtime-test-results/`.

`npm run test:pairing-runtime` then exercises actual owner start, a synthetic native client claim through the API, full fingerprint confirmation, status and revocation. Run the empty-runtime suite first on a fresh synthetic store: pairing persists a Source, Vault and device history. The pairing suite retains those records and revokes its synthetic devices. It must not reset or delete the runtime. Neither API traffic nor responsive browser emulation proves an actual iPhone connector.

`npm run test:metadata-runtime` exercises an already running Next/Python pair using the synthetic account. It creates isolated synthetic library aliases, confirms their devices, admits three explicitly selected metadata records each, verifies original capture dates/unknown dates and server-side filtering, then changes Hidden consent through the UI and confirms immediate exclusion. Devices are revoked in cleanup; Sources and their synthetic metadata are retained. The fixture may already contain Sources or assets; do not run the empty-runtime suite afterward. No personal library or real iPhone is involved.

The mocked suite accepts `MEMORY_TEST_PORT` for an isolated production server (default 8767); actual-runtime suites use the API's configured origin on 8767.

`npm run test:media-runtime` targets the isolated synthetic media fixture described in the media evidence. It verifies 96×64 JPEG decode, H.264/AAC video and Live motion progress/audio decoding, no autoplay, partial/missing states, authenticated HEAD/Range, Hidden-policy denial after refresh and logout denial. It leaves Hidden disabled and retains all fixture records. This is a synthetic browser proof, not audible speaker QA or a real device acceptance test.

None of these suites claims a connected iPhone, deployment, whole-library coverage, original-copy retrieval, durable Block generations or Artifact editing. Those features remain visibly unavailable until their implementation is integrated.

## Dependency verification

Pinned versions were checked against the official npm registry on 2 October 2026: Next 16.3.8, React/React DOM 19.3.0 and TypeScript 7.0.2. Node 24.14.1 satisfies Next's declared Node >=20.9 requirement; matching Node 24 type definitions are pinned. Playwright 1.60.0 matches the existing browser harness. Installation reported no known audit vulnerabilities. The lockfile is committed; installed packages/build/test outputs are ignored.

Official references: [Next installation](https://nextjs.org/docs/app/getting-started/installation), [React versions](https://react.dev/versions). Registry metadata and the successful production build establish the exact installed compatible versions.
