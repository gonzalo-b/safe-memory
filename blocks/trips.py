"""Pure inferred trip candidates from already authorized projected Records.

This is not a persistent trip/correction store or an authorization boundary.
Callers must project Records, provenance, geography and habitual areas first.
Only explicit source coordinates locate evidence; labels never imply geography.
Known third-party evidence is excluded; unknown provenance stays visibly unknown.

Grouping defaults are versioned implementation hypotheses, not accepted product
quality thresholds: consecutive observations within 72 hours and 2,000 km form
one candidate. A confirmed habitual observation closes a candidate. Areas have
explicit historical [start, end) validity and can coexist. Unconfirmed area
suggestions never silently suppress evidence. Routine commuting is excluded only
when it lies within those explicit areas; no inferred home/work classifier ships.

A one-observation outing is an inferred candidate, never proof of travel. Multiple
observed dates yield an overnight *candidate*, not proof of an overnight stay.
UTC conversion is solely for elapsed-time ordering; original timestamps/offsets
and local dates are retained in outputs. Gaps are unknown, never interpolated.

candidate_id hashes policy and permitted evidence IDs. Membership/policy changes
change this detection identity. Future persisted owner corrections must own a
separate stable trip ID and explicit lineage/reconciliation; they must not attach
only to this hash. A redacted evidence ID makes candidate identity unavailable.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
from dataclasses import asdict, dataclass

from blocks.capabilities import _capture_date, _date, _text

DEFINITION_VERSION = "projected-trips-1"


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


@dataclass(frozen=True)
class TripPolicy:
    version: str = "distance-time-1"
    max_gap_hours: float = 72
    max_leg_km: float = 2000
    min_observations: int = 1

    def __post_init__(self):
        if not _text(self.version):
            raise ValueError("Policy version is required")
        for value in (self.max_gap_hours, self.max_leg_km):
            if not _finite(value) or value <= 0:
                raise ValueError("Distance and time limits must be finite and positive")
        if type(self.min_observations) is not int or self.min_observations < 1:
            raise ValueError("Minimum observations must be a positive integer")


def _coordinates(value):
    if not isinstance(value, dict):
        return None
    lat, lon = value.get("lat"), value.get("lon")
    if any(not _finite(x) for x in (lat, lon)):
        return None
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None


def _distance(a, b):
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat, dlon = lat2 - lat1, math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1, max(0, h))))


def _areas(values):
    result = []
    for value in values:
        point = _coordinates(value)
        start, end = _date(value.get("start")), _date(value.get("end"))
        radius = value.get("radius_km")
        if point is None or start >= end or not _finite(radius) or radius <= 0:
            raise ValueError("Habitual area requires coordinates, positive radius and explicit historical window")
        if value.get("confirmed") is True:
            result.append((point, radius, start, end))
    return result


def _candidate(group, policy):
    observations = [item["observation"] for item in group]
    evidence = sorted({row["id"] for row in observations if _text(row.get("id"))})
    dates = sorted({row["date"] for row in observations})
    start, end = _date(dates[0]), _date(dates[-1])
    observed = set(dates)
    unobserved = []
    day = start
    while day < end:
        if day.isoformat() not in observed:
            unobserved.append(day.isoformat())
        day += dt.timedelta(days=1)
    identity = None
    if all(_text(row.get("id")) for row in observations):
        basis = json.dumps({"definition": DEFINITION_VERSION, "policy": asdict(policy), "evidence": evidence}, sort_keys=True, separators=(",", ":"))
        identity = "candidate-" + hashlib.sha256(basis.encode()).hexdigest()[:24]
    confirmed = all(row["attribution"] == "owner_confirmed" for row in observations)
    return {"candidate_id": identity, "state": "inferred",
            "kind": "same_day_candidate" if len(dates) == 1 else "overnight_candidate",
            "start": dates[0], "end": dates[-1],
            "boundary_basis": "min_max_observed_local_dates_not_departure_or_return",
            "observed_dates": dates, "unobserved_dates": unobserved,
            "continuous_presence": False, "owner_presence_confirmed": confirmed,
            "attribution": "owner_confirmed_evidence" if confirmed else "includes_unknown",
            "places": sorted({row["place"] for row in observations if row.get("place")}),
            "countries": sorted({row["country_code"] for row in observations if row.get("country_code")}),
            "cities": sorted({(row["city_id"], row["city"]) for row in observations if row.get("city_id") and row.get("city")}),
            "evidence": evidence, "observations": observations}


def detect_trips(events, *, habitual_areas=(), provenance=None, geography=None, policy=None):
    """Return deterministic candidate groupings with explicit coverage/limitations.

    Optional enrichment is projected separately and keyed by a visible event ID.
    Geography may enrich labels/codes but never supplies guessed coordinates.
    Provenance is 'owner_confirmed', 'third_party', or unknown. 'owner_confirmed'
    means explicit presence confirmation, not merely ownership of the photo.
    """
    policy = policy if policy is not None else TripPolicy()
    if not isinstance(policy, TripPolicy):
        raise ValueError("Expected TripPolicy")
    areas = _areas(habitual_areas)
    provenance, geography = provenance or {}, geography or {}
    coverage = dict.fromkeys(("input_records", "duplicate_replays", "third_party_excluded", "missing_time", "missing_coordinates", "habitual_excluded", "candidate_observations", "below_minimum_observations"), 0)
    observations, seen = [], {}
    for original in events:
        if original.get("kind") not in ("photo", "place"):
            continue
        row = copy.deepcopy(original)
        identifier = _text(row.get("id"))
        if identifier and identifier in seen:
            if seen[identifier] != row:
                raise ValueError("Conflicting projected record revisions")
            coverage["duplicate_replays"] += 1
            continue
        if identifier:
            seen[identifier] = row
        coverage["input_records"] += 1
        attribution = provenance.get(identifier) if identifier else None
        if attribution == "third_party":
            coverage["third_party_excluded"] += 1
            continue
        local_date = _capture_date(row.get("ts"))
        if local_date is None:
            coverage["missing_time"] += 1
            continue
        point = _coordinates(row.get("location"))
        if point is None:
            coverage["missing_coordinates"] += 1
            continue
        instant = dt.datetime.fromisoformat(row["ts"].replace("Z", "+00:00")).astimezone(dt.timezone.utc)
        habitual = any(start <= local_date < end and _distance(point, center) <= radius for center, radius, start, end in areas)
        observation = {"ts": row["ts"], "date": local_date.isoformat(), "lat": point[0], "lon": point[1],
                       "attribution": "owner_confirmed" if attribution == "owner_confirmed" else "unknown"}
        if identifier:
            observation["id"] = identifier
        place = _text(row["location"].get("place"))
        if place:
            observation["place"] = place
        extra = geography.get(identifier, {}) if identifier else {}
        if isinstance(extra, dict):
            for field in ("country_code", "city_id", "city"):
                if _text(extra.get(field)):
                    observation[field] = extra[field]
        observations.append({"instant": instant, "point": point, "habitual": habitual, "observation": observation})
    observations.sort(key=lambda item: (item["instant"], json.dumps(item["observation"], sort_keys=True)))
    candidates, group = [], []

    def finish():
        if len(group) >= policy.min_observations:
            candidates.append(_candidate(group, policy))
            coverage["candidate_observations"] += len(group)
        else:
            coverage["below_minimum_observations"] += len(group)
        group.clear()

    for item in observations:
        if item["habitual"]:
            coverage["habitual_excluded"] += 1
            finish()
            continue
        if group:
            previous = group[-1]
            gap = (item["instant"] - previous["instant"]).total_seconds() / 3600
            if gap > policy.max_gap_hours or _distance(item["point"], previous["point"]) > policy.max_leg_km:
                finish()
        group.append(item)
    finish()
    return {"definition_version": DEFINITION_VERSION, "policy": asdict(policy),
            "status": "candidates" if candidates else "no_candidates",
            "coverage": coverage, "candidates": candidates,
            "scope": "provided_authorized_projection",
            "time_basis": "elapsed_instants_for_grouping_source_offset_local_dates_for_display",
            "limitations": ["inferred_candidates_not_confirmed_trips", "missing_days_are_unknown",
                            "commuting_exclusion_requires_explicit_historical_habitual_areas",
                            "candidate_hash_is_not_a_persistent_correction_identity"]}
