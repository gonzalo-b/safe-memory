---
title: "Photos Location And Evidence"
project: memory
type: doc
status: active
created: 2026-10-02
source: codex-desktop
---

# Photos location and evidence

The authenticated, audited `GET /api/photos` projection includes three additive
fields for each currently authorized asset:

- `location`: optional `lat`, `lon`, and `place` keys. Both coordinates must be
  finite, valid numbers; native `latitude`/`longitude` aliases are accepted.
- `geography`: optional explicit `country_code`, `country`, `city_id`, and
  `city` keys. No geocoding or owner-presence inference occurs.
- `evidence`: `{asset_id, revision}` only when the active owner Knowledge
  generation contains that exact current revision; otherwise `null`.

Place and geography strings use the existing Knowledge text validation: at
most 200 Unicode characters, no control characters or surrounding whitespace.
Malformed or absent fields are omitted. Zero coordinates are valid. Projection
reads current imported metadata even before Knowledge rebuild; it never returns
raw metadata. The existing maximum of 200 assets per API page remains unchanged
(Photos requests 25 as bounded lookahead for 24 visible cards). Source permission,
Hidden/shared consent, selected scope, owner, revision, and audit checks remain
mandatory before disclosure.

Photos displays source place, coordinates and explicit geography. Missing place
or geography is “Unknown”; missing coordinates are “Unavailable”. An unindexed
current revision says “Evidence awaiting Knowledge rebuild.” Inspect evidence
opens the existing Knowledge evidence panel, which performs a new authenticated
request with current authorization. A failed evidence request clears the Photos
results and open media selection; refresh checks access again. Filters, paging,
refresh and switching to media close the evidence panel. Session expiry clears
the private screen. Source text is rendered as React text, not HTML.

This is a synthetic-fixture verified UI/API slice, not real-device or deployment
acceptance. Original requests and media playback behavior are unchanged.

Server-side period, explicit place, trip and collection filters are specified in [PHOTOS-FILTERS.md](PHOTOS-FILTERS.md); all matching precedes pagination and retains current authorization.
