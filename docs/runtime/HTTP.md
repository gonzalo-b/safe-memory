---
title: "Alpha Runtime HTTP Contract"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Alpha runtime HTTP contract

Approved Next/React/TypeScript frontend and Python/SQLite backend. This new runtime is separate from the unchanged legacy fixture stdio/event/Grant schemas. One HTTPS origin; Next proxies /api to loopback Python. Python validates configured Host and Origin and derives owner identity only from its session. API responses use Cache-Control: no-store. No Next data cache for private responses; no public image optimizer path for protected media. Browser credentials remain cookies, not localStorage.

All errors are JSON `{ "error": { "code": "unauthorized", "message": "Sign in to continue." } }`. Stable HTTP meanings: 400 invalid, 401 no/expired session, 403 denied/CSRF, 404 missing or inaccessible object, 409 conflict, 413 too large, 429 throttled, 503 audit/storage unavailable. Response shape never exposes tracebacks, local paths, tokens or source payloads in errors. 501 means a known future feature is not yet available; frontend must display that honestly, never simulate success.

## Foundation contract (frozen for parallel implementation)

- `GET /api/health`: public minimal liveness `{status:"ok"}`; no account or storage detail.
- `POST /api/auth/login`, JSON `{username,password}`: `{owner:{id,display_name}, csrf_token, fixture}` plus HttpOnly session cookie; HTTPS Secure in deployment. Origin must match. Invalid credentials generic401; bounded login attempts429.
- `GET /api/session`: same JSON owner/csrf/fixture for valid session; otherwise401. CSRF token is kept in UI memory only.
- `POST /api/auth/logout`, empty JSON: `{ok:true}` and expired session cookie. Requires Origin and `X-CSRF-Token`.
- `GET /api/overview`: `{vault:null|{id,domain}, counts:{assets,media_ready,artifacts,trips}, sources:[], coverage:{index_state,media_state,last_success}, fixture}`. Zero counts mean actual empty authorized runtime. No repository fixture fallback.
- `GET /api/sources`: `{sources:[],fixture}`; each later item has id, name, permission, status, last_success, index_count and media_ready_count.
- `GET /api/debug`: `{version,environment,health:{storage,audit},operations:[],audit:[],fixture}`. Only authenticated owner’s safe operation/audit IDs, action, outcome and timestamps; no query text, raw data, secrets or paths. Empty history is honest.

The signed-in frontend routes are Overview, Sources, Memory, Blocks, Trips, Artifacts, Access history, Debug, Settings. Future endpoints are not fabricated for this F0 component task. Screen content for unavailable capability must explicitly say unavailable, with no fake records or successful actions. Theme is the only persistent browser preference. Real auth/session handling must work in the actual browser, including expired401. Existing synthetic shell tests are retained separately and are not product acceptance.

Owner provisioning is a local interactive CLI, never a public signup route. Store/auth implementation, two-owner negative tests, SQL migration, persistence and audit are integrator-owned. Frontend does not create tables or independent auth.
