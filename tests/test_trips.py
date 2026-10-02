"""Synthetic behavioral proof for projected-evidence trip candidate detection."""
from __future__ import annotations

import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from blocks.trips import TripPolicy, detect_trips


def observation(identifier, ts, lat=35.0, lon=139.0, place="Synthetic city"):
    row = {"kind": "photo", "source": "apple_photos", "ts": ts,
           "location": {"lat": lat, "lon": lon, "place": place}}
    if identifier is not None:
        row["id"] = identifier
    return row


def area(identifier="base", lat=0, lon=0, start="2025-01-01", end="2027-01-01", confirmed=True):
    return {"id": identifier, "lat": lat, "lon": lon, "radius_km": 30,
            "start": start, "end": end, "confirmed": confirmed}


class TripTests(unittest.TestCase):
    def test_same_day_outing_between_habitual_observations_is_eligible(self):
        rows = [observation("home-a", "2026-06-12T08:00:00Z", 0, 0),
                observation("outing", "2026-06-12T13:00:00Z", 0, 1),
                observation("home-b", "2026-06-12T20:00:00Z", 0, 0)]
        result = detect_trips(rows, habitual_areas=[area()])
        self.assertEqual(len(result["candidates"]), 1)
        trip = result["candidates"][0]
        self.assertEqual(trip["kind"], "same_day_candidate")
        self.assertEqual(trip["evidence"], ["outing"])
        self.assertFalse(trip["continuous_presence"])
        self.assertEqual(trip["state"], "inferred")

    def test_overnight_multi_city_with_gaps_is_not_continuous_presence(self):
        rows = [observation("a", "2026-06-12T23:00:00+09:00", 35, 139, "Tokyo"),
                observation("b", "2026-06-14T10:00:00+09:00", 35, 135, "Kyoto")]
        trip = detect_trips(rows)["candidates"][0]
        self.assertEqual(trip["kind"], "overnight_candidate")
        self.assertEqual(trip["observed_dates"], ["2026-06-12", "2026-06-14"])
        self.assertEqual(trip["unobserved_dates"], ["2026-06-13"])
        self.assertEqual(trip["places"], ["Kyoto", "Tokyo"])
        self.assertEqual(trip["observations"][0]["ts"], rows[0]["ts"])
        self.assertFalse(trip["owner_presence_confirmed"])

    def test_known_third_party_excluded_unknown_attribution_stays_explicit(self):
        rows = [observation("third", "2026-06-12T00:00:00Z"),
                observation("unknown", "2026-06-13T00:00:00Z")]
        result = detect_trips(rows, provenance={"third": "third_party"})
        self.assertEqual(result["candidates"][0]["evidence"], ["unknown"])
        self.assertEqual(result["candidates"][0]["attribution"], "includes_unknown")
        self.assertEqual(result["coverage"]["third_party_excluded"], 1)

    def test_commuting_inside_two_explicit_habitual_areas_does_not_create_trip(self):
        rows = [observation("home", "2026-06-12T08:00:00Z", 0, 0),
                observation("work", "2026-06-12T09:00:00Z", 0, 1),
                observation("back", "2026-06-12T18:00:00Z", 0, 0)]
        result = detect_trips(rows, habitual_areas=[area(), area("work", lon=1)])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["coverage"]["habitual_excluded"], 3)

    def test_historical_residences_do_not_rewrite_earlier_travel(self):
        rows = [observation("old-home", "2024-06-12T00:00:00Z", 0, 0),
                observation("old-trip", "2024-06-13T00:00:00Z", 0, 1),
                observation("new-home", "2026-06-12T00:00:00Z", 0, 1),
                observation("new-trip", "2026-06-13T00:00:00Z", 0, 0)]
        result = detect_trips(rows, habitual_areas=[
            area("old", start="2024-01-01", end="2025-01-01"),
            area("new", lon=1, start="2025-01-01", end="2027-01-01")])
        self.assertEqual([t["evidence"] for t in result["candidates"]], [["old-trip"], ["new-trip"]])

    def test_unconfirmed_area_does_not_silently_suppress_trip_and_windows_required(self):
        rows = [observation("a", "2026-06-12T00:00:00Z", 0, 0)]
        self.assertEqual(len(detect_trips(rows, habitual_areas=[area(confirmed=False)])["candidates"]), 1)
        missing_window = area()
        del missing_window["start"]
        with self.assertRaises(ValueError):
            detect_trips(rows, habitual_areas=[missing_window])

    def test_missing_ambiguous_timestamp_or_coordinates_never_get_guessed(self):
        rows = [observation("a", "2026-06-12T00:00:00"),
                observation("b", "2026-06-12T00:00:00-00:00"),
                observation("c", "2026-06-12T00:00:00Z", None, None, "Tokyo"),
                observation("d", "2026-06-12T00:00:00Z", 100, 0),
                observation("e", "2026-06-12T00:00:00Z", float("nan"), 0)]
        result = detect_trips(rows)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["coverage"]["missing_time"], 2)
        self.assertEqual(result["coverage"]["missing_coordinates"], 3)

    def test_explicit_policy_gap_distance_and_return_to_area_split_candidates(self):
        rows = [observation("a", "2026-06-12T00:00:00Z", 0, 1),
                observation("b", "2026-06-12T12:00:00Z", 0, 2),
                observation("c", "2026-06-13T12:00:00Z", 0, 2)]
        self.assertEqual(len(detect_trips(rows, policy=TripPolicy(max_gap_hours=6))["candidates"]), 3)
        self.assertEqual(len(detect_trips(rows, policy=TripPolicy(max_leg_km=50))["candidates"]), 2)
        home = observation("home", "2026-06-12T06:00:00Z", 0, 0)
        self.assertEqual(len(detect_trips(rows + [home], habitual_areas=[area()])["candidates"]), 2)
        with self.assertRaises(ValueError):
            TripPolicy(max_gap_hours=-1)

    def test_candidate_identity_replay_order_and_missing_ids(self):
        a = observation("a", "2026-06-12T00:00:00Z")
        b = observation("b", "2026-06-13T00:00:00Z")
        first = detect_trips([a, b])["candidates"][0]
        replay = detect_trips([b, a, a.copy()])["candidates"][0]
        self.assertEqual(first, replay)
        self.assertTrue(first["candidate_id"].startswith("candidate-"))
        changed = detect_trips([a])["candidates"][0]
        self.assertNotEqual(first["candidate_id"], changed["candidate_id"])
        absent = detect_trips([observation(None, "2026-06-12T00:00:00Z")])["candidates"][0]
        self.assertIsNone(absent["candidate_id"])
        self.assertEqual(absent["evidence"], [])

    def test_projected_geography_provenance_inputs_not_mutated_or_joined_to_hidden_ids(self):
        rows = [observation("a", "2026-06-12T00:00:00Z")]
        original = copy.deepcopy(rows)
        result = detect_trips(rows, provenance={"a": "owner_confirmed"}, geography={
            "a": {"country_code": "JP", "city": "Tokyo", "city_id": "jp-tokyo"},
            "excluded": {"country_code": "AR", "city": "Buenos Aires"}})
        self.assertEqual(rows, original)
        self.assertEqual(result["candidates"][0]["countries"], ["JP"])
        self.assertTrue(result["candidates"][0]["owner_presence_confirmed"])
        with self.assertRaises(ValueError):
            detect_trips(rows + [dict(rows[0], ts="2026-06-13T00:00:00Z")])

    def test_offset_crossing_midnight_sorts_instants_preserves_observed_local_dates(self):
        rows = [observation("later", "2026-06-12T23:00:00-03:00"),
                observation("earlier", "2026-06-13T00:00:00+14:00")]
        trip = detect_trips(rows)["candidates"][0]
        self.assertEqual([x["id"] for x in trip["observations"]], ["earlier", "later"])
        self.assertEqual(trip["observed_dates"], ["2026-06-12", "2026-06-13"])
        self.assertEqual(trip["boundary_basis"], "min_max_observed_local_dates_not_departure_or_return")


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TripTests))
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed} passed, {failed} failed")
    sys.exit(0 if result.wasSuccessful() else 1)
