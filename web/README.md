# Memory web foundation

Next.js App Router, React and TypeScript frontend for the Python runtime contract in `docs/runtime/HTTP.md`. It implements sign-in/session restoration, CSRF logout, Overview, Sources, safe Debug/access events, appearance and honest unavailable feature screens. Python owns identity, authorization, audit and persistence. This package does not provision owners or copy the store into browser storage.

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

## Design system

`public/` reuses the complete verified `ui/` stylesheet, Inter font and icon asset. `vendor/memory-ds/` preserves the supplied React Button, Badge, ModuleTile and Icon/Sprite wrappers with their dependencies. File hashes are in `asset-provenance.json`. Product CSS contains only layouts/tokens and is scanned by the existing guard. Local-asset tests compare the complete copied CSS and binary assets, not merely a suffix. No monospaced surface or new font dependency was introduced.

## Validation

`npm run test:e2e` starts the **production build** on loopback and runs synthetic HTTP-response mocks at desktop/mobile in both themes. It proves rendering, cookie handling in the browser, CSRF construction, error/401 transitions, safe text, keyboard/focus and local assets. It does not prove backend authentication, authorization or persistence.

`npm run test:runtime` runs separately against an already running Next and Python pair, with an explicitly provisioned synthetic account supplied through `MEMORY_TEST_USERNAME` and `MEMORY_TEST_PASSWORD`. It uses no request mocks and checks actual session cookies, API rewrite, empty runtime, diagnostics, reload and logout denial. It must never use a personal Photos account or dataset. Outputs go to ignored `runtime-test-results/`.

Neither suite claims a connected iPhone, deployment, non-empty source data, media playback, durable Block generations or Artifact editing. Those features remain visibly unavailable until their implementation is integrated.

## Dependency verification

Pinned versions were checked against the official npm registry on 2 October 2026: Next 16.3.8, React/React DOM 19.3.0 and TypeScript 7.0.2. Node 24.14.1 satisfies Next's declared Node >=20.9 requirement; matching Node 24 type definitions are pinned. Playwright 1.60.0 matches the existing browser harness. Installation reported no known audit vulnerabilities. The lockfile is committed; installed packages/build/test outputs are ignored.

Official references: [Next installation](https://nextjs.org/docs/app/getting-started/installation), [React versions](https://react.dev/versions). Registry metadata and the successful production build establish the exact installed compatible versions.
