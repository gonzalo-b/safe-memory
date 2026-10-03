# Photos API filters

`GET /api/photos` remains an authenticated owner read with audited disclosure.
The response remains `{assets, coverage, fixture}`; no total or excluded-record
counts are added. Existing `day`, `media_type`, `limit` (1–200), and `offset`
(0–1,000,000) semantics are preserved. Default page size remains 50.

All supplied filters combine with AND. Current owner, revision, selected scope,
source permission and Hidden/shared consent predicates apply to the same query.
Filtering occurs before the existing newest-instant/id order and offset/limit.

| Parameter | Contract |
| --- | --- |
| `from_day` | Inclusive lower bound on known capture-local `YYYY-MM-DD`. |
| `to_day` | Inclusive upper bound on known capture-local `YYYY-MM-DD`. |
| `place` | Literal, Unicode-casefolded substring of explicit `location.place` or `geography.country_code`, `country`, `city_id`, `city` from current imported metadata. |
| `trip_id` | Exact lowercase 32-hex ID of a current, authorized active trip. Matches only members of its current trip revision. |
| `collection` | Exact `personal`, `shared_library`, `shared_album`, or `unknown`. Selecting a collection does not grant access to it. |

Either date bound may stand alone. Equal bounds select one local day. Unknown or
instant-only local dates never match a date bound. A `day` combined with either
bound, an invalid calendar date, or `from_day > to_day` returns
`400 invalid_filter`. No UTC/device/server timezone is substituted.

`place` must be 1–200 Unicode characters without surrounding whitespace or control
characters; blank input should be omitted by the client. It searches only valid
source strings with the same 200-character validation as the returned projection.
Matching retains accents and treats `%`, `_`, quotes and SQL syntax literally.
Coordinates, filenames, private arbitrary raw metadata and inferred geography
do not participate. Place search works before Knowledge rebuild and reads no
Source or network. This implementation adds no persistent index/schema and may
scan current candidate metadata for place matching; page bounds do not establish
a search-latency or whole-library scale claim.

Trip access uses the existing Knowledge active-trip predicate in the same
transaction as Photos disclosure. Every current member must have a current
authorized indexed fact with its retained evidence signature, and inferred trips
must belong to the active generation. A missing member, policy restriction,
unindexed revision, changed signature, different owner, nonexistent trip or
superseded/dismissed trip produces the same `404 not_found`, even if another
filter would otherwise return no rows. A malformed ID is `400 invalid_filter`.
Equivalent metadata reimport becomes eligible again after rebuild only when
the retained signature still matches. Authorized manual trips with no members
return an empty asset list; owner-asserted dates do not invent membership.

Unknown query keys, duplicate keys, more than nine fields, malformed query integer
values or invalid percent-encoded UTF-8 are rejected with `400 invalid_query`.
Invalid enum/string/date values are `400 invalid_filter`; no error echoes a
private filter value. Sessions and audit failures retain their existing 401/503
fail-closed behavior. Responses retain `Cache-Control: no-store`.

The UI can obtain authorized trip choices from the existing paginated
`GET /api/knowledge/trips?limit=...&cursor=...`; it should retain only the selected
ID for this filter and clear visible results on a rejected/stale trip. All new
parameters are optional; omitting them preserves existing callers.

This is a fixture-verified API extension, not device or production acceptance.
