"""Deterministic queries over an already authorized legacy-event projection.

INTERNAL BUILDING BLOCK, not a deployed API, authorization service or persistent
Block store. The caller must filter/redact events AND optional enrichment before
construction, and audit disclosure itself. Rebuild this object after any policy
change; never share it across principals or treat it as a permission cache.

Enrichment is kept outside the closed legacy event schema. Maps are keyed only
by IDs retained in the projected events; they must contain only permitted fields:
  geography: country_code/country, city_id/city (explicit source geography)
  provenance: 'owner_confirmed', 'third_party', or 'unknown'
  media: type ('photo', 'video', 'live'), ready (bool)

A media/source ownership label is not confirmation of the owner's presence.
Only explicit permitted owner-confirmed presence may use 'owner_confirmed'.
No network, model, persistence, clock, geocoding, source writes or inference.
"""
from __future__ import annotations

import bisect
import calendar
import copy
import datetime as dt
import json
import re
from collections import defaultdict

DEFINITION_VERSION = "projected-capabilities-1"
TIME_BASIS = "source_offset_local_date"
MAX_OCCURRENCES = 100
LEAP_POLICIES = ("leap_years_only", "february_28", "march_1")


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected calendar date YYYY-MM-DD")
    return dt.date.fromisoformat(value)


def _month_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}-\d{2}", value):
        raise ValueError("Expected month and day MM-DD")
    parsed = _date("2000-" + value)
    return parsed.month, parsed.day


def _capture_date(value):
    # A redacted or absent offset cannot be silently replaced by the host zone.
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        return None
    if value.endswith("-00:00"):
        return None  # RFC 3339 unknown-local-offset marker, not known UTC.
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.date() if parsed.utcoffset() is not None else None
    except ValueError:
        return None


def _text(value):
    return value if isinstance(value, str) and value.strip() else None


def _refs(rows):
    return sorted({row["id"] for row in rows if _text(row.get("id"))})


class Capabilities:
    """Snapshot query helper. Date selection uses a sorted local-date index.

    Geography and statistics aggregate selected projected rows. This helper does
    not establish production scale budgets, durable generations or revocation.
    Input replay with an identical visible ID is idempotent; conflicting visible
    revisions are rejected so the caller must resolve the coherent generation.
    Rows with redacted IDs are not deduplicated by content or synthetic identity.
    """

    def __init__(self, events, *, geography=None, provenance=None, media=None):
        self._geography = copy.deepcopy(geography or {})
        self._provenance = copy.deepcopy(provenance or {})
        self._media = copy.deepcopy(media or {})
        rows, seen = [], {}
        for original in events:
            if original.get("kind") not in ("photo", "place"):
                continue
            row = copy.deepcopy(original)
            identifier = _text(row.get("id"))
            if identifier is not None:
                if identifier in seen:
                    if seen[identifier] != row:
                        raise ValueError("Conflicting projected record revisions")
                    continue
                seen[identifier] = row
            rows.append(row)
        self._rows = sorted(rows, key=lambda row: (
            _capture_date(row.get("ts")) or dt.date.max,
            row.get("ts") or "", row.get("id") or "",
            json.dumps(row, sort_keys=True, ensure_ascii=True)))
        self._known = [row for row in self._rows if _capture_date(row.get("ts"))]
        self._dates = [_capture_date(row.get("ts")) for row in self._known]
        self._missing_time = len(self._rows) - len(self._known)

    @staticmethod
    def _location(row):
        location = row.get("location")
        if not isinstance(location, dict):
            return {}
        result = {}
        place = _text(location.get("place"))
        if place:
            result["place"] = place
        lat, lon = location.get("lat"), location.get("lon")
        if (isinstance(lat, (int, float)) and not isinstance(lat, bool)
                and isinstance(lon, (int, float)) and not isinstance(lon, bool)
                and -90 <= lat <= 90 and -180 <= lon <= 180):
            result.update(lat=lat, lon=lon)
        return result

    @staticmethod
    def _extra(mapping, row):
        identifier = _text(row.get("id"))
        return mapping.get(identifier, {}) if identifier else {}

    def _select(self, start=None, end=None, *, include_unknown=False):
        start_date = _date(start) if start is not None else None
        end_date = _date(end) if end is not None else None
        if start_date and end_date and start_date >= end_date:
            raise ValueError("Range requires start before exclusive end")
        if start is None and end is None and include_unknown:
            return self._rows
        lo = bisect.bisect_left(self._dates, start_date) if start_date else 0
        hi = bisect.bisect_left(self._dates, end_date) if end_date else len(self._known)
        return self._known[lo:hi]

    def _observation(self, row):
        location = self._location(row)
        if not location:
            return None
        attribution = self._extra(self._provenance, row)
        if attribution not in ("owner_confirmed", "third_party"):
            attribution = "unknown"
        result = {"date": _capture_date(row.get("ts")).isoformat(),
                  "ts": row["ts"], **location, "attribution": attribution,
                  "owner_presence_confirmed": attribution == "owner_confirmed"}
        if _text(row.get("id")):
            result["id"] = row["id"]
        return result

    def _result(self, capability, rows, data, *, evidence_rows=None, status=None):
        located = sum(bool(self._location(row)) for row in rows)
        if status is None:
            status = "ok" if data else "no_evidence"
            if data and (self._missing_time or located < len(rows)):
                status = "partial"
        return {"capability": capability, "definition_version": DEFINITION_VERSION,
                "status": status, "data": copy.deepcopy(data),
                "evidence": _refs(rows if evidence_rows is None else evidence_rows),
                "time_basis": TIME_BASIS,
                "counting_basis": "projected_records_and_distinct_observed_local_dates",
                "coverage": {"scope": "provided_authorized_projection",
                             "input_records": len(self._rows),
                             "known_time_records": len(self._known),
                             "missing_time_records": self._missing_time,
                             "selected_records": len(rows),
                             "selected_located_records": located,
                             "known_date_start": self._dates[0].isoformat() if self._dates else None,
                             "known_date_end": self._dates[-1].isoformat() if self._dates else None},
                "freshness": {"source_check": "unknown", "persistent_generation": None}}

    def where_in_range(self, start, end):
        rows = self._select(start, end)
        evidence = [row for row in rows if self._location(row)]
        return self._result("travel.where_in_range", rows,
                            [self._observation(row) for row in evidence], evidence_rows=evidence)

    def where_on_date(self, date):
        day = _date(date)
        if day == dt.date.max:
            rows = [row for row in self._known if _capture_date(row.get("ts")) == day]
            evidence = [row for row in rows if self._location(row)]
            result = self._result("travel.where_on_date", rows,
                                  [self._observation(row) for row in evidence], evidence_rows=evidence)
        else:
            result = self.where_in_range(date, (day + dt.timedelta(days=1)).isoformat())
            result["capability"] = "travel.where_on_date"
        return result

    def where_in_year(self, year):
        if type(year) is not int or not 1 <= year <= 9999:
            raise ValueError("Year must be an integer from 1 through 9999")
        if year == 9999:
            rows = self._select("9999-01-01")
            evidence = [row for row in rows if self._location(row)]
            result = self._result("travel.where_in_year", rows,
                                  [self._observation(row) for row in evidence], evidence_rows=evidence)
        else:
            result = self.where_in_range(f"{year:04d}-01-01", f"{year + 1:04d}-01-01")
            result["capability"] = "travel.where_in_year"
        return result

    def _geography_rollup(self, kind, start, end):
        rows = self._select(start, end)
        groups = defaultdict(list)
        descriptions = {}
        for row in rows:
            supplied = self._extra(self._geography, row)
            if not isinstance(supplied, dict):
                continue
            # Country text/place-name substrings never manufacture a country code.
            key = _text(supplied.get("country_code" if kind == "country" else "city_id"))
            if not key:
                continue
            description = {"country_code": key, "country": _text(supplied.get("country")) or key} if kind == "country" else {
                "city_id": key, "city": _text(supplied.get("city")) or key,
                "country_code": _text(supplied.get("country_code"))}
            if key in descriptions and descriptions[key] != description:
                raise ValueError("Conflicting explicit geography labels")
            descriptions[key] = description
            groups[key].append(row)
        data = [{**descriptions[key], "observed_days": len({_capture_date(row["ts"]) for row in groups[key]}),
                 "record_count": len(groups[key]), "evidence": _refs(groups[key])} for key in sorted(groups)]
        evidence = [row for key in groups for row in groups[key]]
        result = self._result("travel.countries" if kind == "country" else "travel.cities", rows, data,
                              evidence_rows=evidence,
                              status="partial" if data and (len(evidence) < len(rows) or self._missing_time) else ("ok" if data else "no_evidence"))
        result["counting_basis"] = "distinct_explicit_geography_ids_in_projected_media_evidence_not_owner_presence"
        return result

    def countries(self, start=None, end=None):
        return self._geography_rollup("country", start, end)

    def cities(self, start=None, end=None):
        return self._geography_rollup("city", start, end)

    def photo_statistics(self, start=None, end=None):
        rows = [row for row in self._select(start, end, include_unknown=True) if row.get("kind") == "photo"]
        types = dict.fromkeys(("photo", "video", "live", "unknown"), 0)
        readiness = {"media_ready": 0, "media_pending": 0, "media_unknown": 0}
        for row in rows:
            supplied = self._extra(self._media, row)
            supplied = supplied if isinstance(supplied, dict) else {}
            media_type = supplied.get("type")
            types[media_type if media_type in ("photo", "video", "live") else "unknown"] += 1
            ready = supplied.get("ready")
            readiness["media_ready" if ready is True else "media_pending" if ready is False else "media_unknown"] += 1
        return self._result("photos.statistics", rows,
                            {"photo_records": len(rows), "media_types": types, **readiness},
                            status="partial" if self._missing_time or readiness["media_unknown"] else "ok")

    def on_this_day(self, month_day):
        month, day = _month_day(month_day)
        rows = [row for row in self._known if (_capture_date(row["ts"]).month, _capture_date(row["ts"]).day) == (month, day)]
        years = sorted({_capture_date(row["ts"]).year for row in rows}, reverse=True)
        data = []
        for year in years:
            year_rows = [row for row in rows if _capture_date(row["ts"]).year == year]
            data.append({"year": year, "date": f"{year:04d}-{month_day}",
                         "record_count": len(year_rows), "evidence": _refs(year_rows),
                         "observations": [self._observation(row) for row in year_rows if self._location(row)]})
        return self._result("photos.on_this_day", rows, data)

    def occasion_history(self, month_day, count, as_of, *, leap_day_policy=None):
        if type(count) is not int or not 1 <= count <= MAX_OCCURRENCES:
            raise ValueError("Occurrence count must be an integer from 1 through 100")
        cutoff = _date(as_of)
        if month_day is None:
            result = self._result("travel.occasion_history", [], [], status="needs_input")
            result["required_input"] = "month_day"
            return result
        month, day = _month_day(month_day)
        if leap_day_policy is not None and leap_day_policy not in LEAP_POLICIES:
            raise ValueError("Unknown leap-day policy")
        if (month, day) == (2, 29) and leap_day_policy is None:
            result = self._result("travel.occasion_history", [], [], status="needs_input")
            result["required_input"] = "leap_day_policy"
            return result
        dates = []
        for year in range(cutoff.year, 0, -1):
            current_month, current_day = month, day
            if (month, day) == (2, 29) and not calendar.isleap(year):
                if leap_day_policy == "leap_years_only":
                    continue
                current_month, current_day = (2, 28) if leap_day_policy == "february_28" else (3, 1)
            occurrence = dt.date(year, current_month, current_day)
            if occurrence <= cutoff:
                dates.append(occurrence.isoformat())
            if len(dates) == count:
                break
        if len(dates) != count:
            raise ValueError("Requested occurrences exceed supported calendar")
        data, evidence_rows, selected_rows = [], [], []
        for date in dates:
            response = self.where_on_date(date)
            # Select through the index while retaining a closed upper calendar boundary.
            day_rows = self._select(date, (_date(date) + dt.timedelta(days=1)).isoformat()) if date != "9999-12-31" else self._select(date)
            selected_rows.extend(day_rows)
            evidence_rows.extend(row for row in day_rows if self._location(row))
            data.append({"date": date, "status": "observed" if response["data"] else "unknown",
                         "observations": response["data"], "evidence": response["evidence"]})
        result = self._result("travel.occasion_history", selected_rows, data, evidence_rows=evidence_rows,
                              status="partial" if any(row["status"] == "unknown" for row in data) or self._missing_time else "ok")
        result["leap_day_policy"] = leap_day_policy
        result["counting_basis"] = "most_recent_calendar_occurrences_on_or_before_as_of_including_unknowns"
        return result
