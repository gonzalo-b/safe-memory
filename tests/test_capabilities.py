"""Pure projected-evidence capability tests. No source or runtime data access."""
from __future__ import annotations

import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from blocks.capabilities import Capabilities


def event(identifier, ts, place=None, kind="photo"):
    result = {"kind": kind, "source": "apple_photos", "title": "Synthetic"}
    if identifier is not None:
        result["id"] = identifier
    if ts is not None:
        result["ts"] = ts
    if place is not None:
        result["location"] = {"place": place}
    return result


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            event("a", "2026-06-12T00:10:00+14:00", "Kyoto"),
            event("b", "2026-06-12T23:50:00-03:00", "Tokyo"),
            event("c", "2024-06-12T13:00:00+01:00", "Lisbon"),
            event("d", "2026-06-13T00:00:00+00:00"),
            event("no-offset", "2026-06-12T12:00:00", "Unknown date"),
            event("no-time", None, "Unknown date"),
        ]

    def test_original_offset_and_local_date_are_preserved(self):
        result = Capabilities(self.rows).where_on_date("2026-06-12")
        self.assertEqual([x["place"] for x in result["data"]], ["Kyoto", "Tokyo"])
        self.assertEqual(result["data"][0]["ts"], self.rows[0]["ts"])
        self.assertEqual(result["evidence"], ["a", "b"])
        self.assertEqual(result["coverage"]["missing_time_records"], 2)
        self.assertEqual(result["time_basis"], "source_offset_local_date")

    def test_range_is_inclusive_start_exclusive_end_and_year_is_calendar_year(self):
        cap = Capabilities(self.rows)
        self.assertEqual(cap.where_in_range("2026-06-12", "2026-06-13")["evidence"], ["a", "b"])
        self.assertEqual(cap.where_in_year(2024)["evidence"], ["c"])
        self.assertEqual(cap.where_on_date("2025-06-12")["status"], "no_evidence")

    def test_missing_and_invalid_offsets_do_not_become_local_dates(self):
        rows = [event(str(i), ts, "X") for i, ts in enumerate([
            "2026-01-01", "2026-01-01T12:00:00", "bad", "2026-01-01T12:00:00+25:00", None])]
        result = Capabilities(rows).where_in_year(2026)
        self.assertEqual(result["data"], [])
        self.assertEqual(result["coverage"]["missing_time_records"], 5)

    def test_unknown_offset_marker_and_coordinate_only_evidence(self):
        unknown = event("u", "2026-06-12T00:00:00-00:00", "Uncertain")
        coordinates = event("p", "2026-06-12T00:00:00Z")
        coordinates["location"] = {"lat": 35.0, "lon": 139.0}
        cap = Capabilities([unknown, coordinates])
        result = cap.where_on_date("2026-06-12")
        self.assertEqual(result["evidence"], ["p"])
        self.assertEqual(result["data"][0]["lat"], 35.0)
        self.assertNotIn("place", result["data"][0])
        self.assertEqual(cap.countries()["data"], [])

    def test_offset_minutes_are_validated_without_datetime_normalization(self):
        malformed = ["+00:99", "-00:99", "+24:00", "-24:00", "+10:60"]
        rows = [event(str(i), "2026-06-12T00:00:00" + offset, "X")
                for i, offset in enumerate(malformed)]
        result = Capabilities(rows).where_on_date("2026-06-12")
        self.assertEqual(result["data"], [])
        self.assertEqual(result["coverage"]["missing_time_records"], len(malformed))
        valid = Capabilities([event("v", "2026-06-12T00:00:00+05:45", "X")])
        self.assertEqual(valid.where_on_date("2026-06-12")["evidence"], ["v"])

    def test_empty_statistics_are_no_evidence_not_a_whole_library_zero_claim(self):
        for cap in [Capabilities([]), Capabilities(self.rows)]:
            result = cap.photo_statistics("2001-01-01", "2002-01-01")
            self.assertEqual(result["status"], "no_evidence")
            self.assertEqual(result["data"]["photo_records"], 0)
            self.assertEqual(result["coverage"]["scope"], "provided_authorized_projection")

    def test_absent_location_is_unknown_not_home(self):
        result = Capabilities(self.rows).where_on_date("2026-06-13")
        self.assertEqual(result["status"], "no_evidence")
        self.assertEqual(result["coverage"]["selected_records"], 1)
        self.assertEqual(result["coverage"]["selected_located_records"], 0)

    def test_geography_is_explicit_and_city_identity_is_not_guessed(self):
        cap = Capabilities(self.rows, geography={
            "a": {"country_code": "JP", "country": "Japan", "city": "Kyoto", "city_id": "jp-kyoto"},
            "b": {"country_code": "JP", "country": "Japan", "city": "Tokyo", "city_id": "jp-tokyo"},
            "c": {"country_code": "PT", "country": "Portugal", "city": "Lisbon", "city_id": "pt-lisbon"},
            "not-permitted": {"country_code": "AR", "city_id": "ar-ba", "city": "Buenos Aires"},
        })
        countries = cap.countries("2026-01-01", "2027-01-01")
        self.assertEqual(countries["data"], [{"country_code": "JP", "country": "Japan", "observed_days": 1, "record_count": 2, "evidence": ["a", "b"]}])
        self.assertEqual(len(cap.cities("2026-01-01", "2027-01-01")["data"]), 2)
        self.assertEqual(Capabilities(self.rows).countries()["data"], [])
        self.assertEqual(Capabilities(self.rows).cities()["data"], [])

    def test_unknown_and_third_party_provenance_never_assert_owner_presence(self):
        cap = Capabilities(self.rows, provenance={"a": "third_party", "b": "owner_confirmed"})
        data = cap.where_on_date("2026-06-12")["data"]
        self.assertEqual(data[0]["attribution"], "third_party")
        self.assertFalse(data[0]["owner_presence_confirmed"])
        self.assertTrue(data[1]["owner_presence_confirmed"])
        self.assertFalse(cap.where_on_date("2024-06-12")["data"][0]["owner_presence_confirmed"])

    def test_redacted_id_never_yields_evidence_or_sidecar_lookup(self):
        cap = Capabilities([event(None, "2026-06-12T00:00:00Z", "Kyoto")], geography={"None": {"country_code": "JP"}})
        result = cap.where_on_date("2026-06-12")
        self.assertEqual(result["evidence"], [])
        self.assertNotIn("id", result["data"][0])
        self.assertEqual(cap.countries()["data"], [])

    def test_statistics_count_photo_records_and_explicit_media_types(self):
        rows = self.rows + [event("place", "2026-06-12T00:00:00Z", "Tokyo", "place")]
        result = Capabilities(rows, media={"a": {"type": "video", "ready": True}, "b": {"type": "live", "ready": False}}).photo_statistics("2026-01-01", "2027-01-01")
        self.assertEqual(result["data"], {"photo_records": 3, "media_types": {"photo": 0, "video": 1, "live": 1, "unknown": 1}, "media_ready": 1, "media_pending": 1, "media_unknown": 1})

    def test_on_this_day_returns_all_matching_years_without_inventing_birthday(self):
        result = Capabilities(self.rows).on_this_day("06-12")
        self.assertEqual([row["year"] for row in result["data"]], [2026, 2024])
        self.assertEqual(result["evidence"], ["a", "b", "c"])

    def test_last_occurrences_keep_unknown_years_and_include_today(self):
        cap = Capabilities(self.rows)
        result = cap.occasion_history("06-12", 3, "2026-06-12")
        self.assertEqual([x["date"] for x in result["data"]], ["2026-06-12", "2025-06-12", "2024-06-12"])
        self.assertEqual(result["data"][1]["status"], "unknown")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(cap.occasion_history("06-12", 1, "2026-06-11")["data"][0]["date"], "2025-06-12")
        self.assertEqual(cap.occasion_history(None, 3, "2026-06-12")["status"], "needs_input")

    def test_leap_day_requires_named_policy_with_no_silent_substitution(self):
        cap = Capabilities([event("leap", "2024-02-29T00:00:00Z", "X")])
        default = cap.occasion_history("02-29", 2, "2026-03-01")
        self.assertEqual(default["leap_day_policy"], "leap_years_only")
        self.assertEqual([row["date"] for row in default["data"]], ["2024-02-29", "2020-02-29"])
        self.assertEqual(default["data"][1]["status"], "unknown")
        skip = cap.occasion_history("02-29", 2, "2026-03-01", leap_day_policy="leap_years_only")
        self.assertEqual([x["date"] for x in skip["data"]], ["2024-02-29", "2020-02-29"])
        feb = cap.occasion_history("02-29", 3, "2026-03-01", leap_day_policy="february_28")
        self.assertEqual([x["date"] for x in feb["data"]], ["2026-02-28", "2025-02-28", "2024-02-29"])
        march = cap.occasion_history("02-29", 1, "2026-03-01", leap_day_policy="march_1")
        self.assertEqual(march["data"][0]["date"], "2026-03-01")

    def test_replay_deduplicates_identified_records_but_preserves_distinct_ids(self):
        a = self.rows[0]
        b = dict(a, id="different")
        result = Capabilities([a, a.copy(), b]).photo_statistics()
        self.assertEqual(result["data"]["photo_records"], 2)
        with self.assertRaises(ValueError):
            Capabilities([a, dict(a, title="conflicting revision")])

    def test_deterministic_order_no_mutation_and_no_retained_caller_reference(self):
        before = copy.deepcopy(self.rows)
        cap = Capabilities(self.rows)
        first = cap.where_in_year(2026)
        self.assertEqual(first, Capabilities(list(reversed(self.rows))).where_in_year(2026))
        self.assertEqual(self.rows, before)
        self.rows[0]["location"]["place"] = "Changed"
        first["data"][0]["place"] = "Changed output"
        self.assertEqual(cap.where_on_date("2026-06-12")["data"][0]["place"], "Kyoto")

    def test_restricted_projection_does_not_use_excluded_rows_or_enrichment(self):
        result = Capabilities([self.rows[0]], geography={"b": {"country_code": "JP"}}).countries()
        self.assertEqual(result["data"], [])
        self.assertEqual(result["coverage"]["input_records"], 1)

    def test_invalid_queries_fail_explicitly_and_cost_is_bounded(self):
        cap = Capabilities(self.rows)
        for start, end in [("2026-01-02", "2026-01-01"), ("nonsense", "2026-01-01")]:
            with self.assertRaises(ValueError):
                cap.where_in_range(start, end)
        for count in [0, -1, 101, True]:
            with self.assertRaises(ValueError):
                cap.occasion_history("06-12", count, "2026-01-01")
        with self.assertRaises(ValueError):
            cap.on_this_day("02-30")
        with self.assertRaises(ValueError):
            cap.occasion_history("02-29", 1, "2026-01-01", leap_day_policy="guess")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CapabilityTests))
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed} passed, {failed} failed")
    sys.exit(0 if result.wasSuccessful() else 1)
