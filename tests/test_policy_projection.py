"""Behavioral regressions for policy before matching. Synthetic data only."""
import datetime
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vault import store

PASS = FAIL = 0

def check(name, result):
    global PASS, FAIL
    if result:
        PASS += 1
        print("  ok  ", name)
    else:
        FAIL += 1
        print("  FAIL", name)

now = datetime.datetime(2026, 10, 2, 12, tzinfo=datetime.timezone.utc)
row = {"id": "ev-fixture-secret", "kind": "photo", "source": "apple_photos",
       "ts": "2026-10-01T12:00:00+00:00", "title": "hidden-title",
       "entities": ["hidden-person"], "location": {"place": "Allowed city", "lat": 1, "lon": 2},
       "fixture": True}
with tempfile.TemporaryDirectory(prefix="memory-policy-") as temp:
    grant = {"agent": "limited", "kinds": ["photo"], "window_days": 7,
             "fields_redacted": ["title", "entities", "source"]}
    with patch.object(store, "_now", return_value=now), patch.object(store, "load_events", return_value=[row]), \
         patch.object(store, "load_grants", return_value=[grant]), \
         patch.object(store, "AUDIT_PATH", str(Path(temp) / "reads.jsonl")):
        for value, label in [("hidden-title", "title"), ("hidden-person", "entities"), ("apple_photos", "source")]:
            result = store.query("limited", "sm_search", query_text=value)
            check("redacted " + label + " cannot influence matching", result == [])
        check("redacted source cannot influence source filter",
              store.query("limited", "sm_photos", source="apple_photos") == [])
        result = store.query("limited", "sm_photos", place="Allowed city")
        check("visible place remains searchable", len(result) == 1 and "title" not in result[0])
        check("projection does not mutate source Record", row["title"] == "hidden-title" and row["source"] == "apple_photos")
        grant["fields_redacted"] = ["location"]
        result = store.query("limited", "sm_photos", place="Allowed city")
        check("legacy location redaction preserves place and removes coordinates",
              result[0]["location"] == {"place": "Allowed city", "lat": None, "lon": None})
        check("policy denial is audited", len(Path(temp, "reads.jsonl").read_text().splitlines()) == 6)
        grant["fields_redacted"] = ["ts"]
        for kwargs, label in [({"date": "2026-10-01"}, "date"),
                              ({"since": "2026-09-30"}, "since"),
                              ({"until": "2026-10-02"}, "until")]:
            check("redacted timestamp cannot influence " + label + " filter",
                  store.query("limited", "sm_timeline", **kwargs) == [])
        second = dict(row, id="ev-fixture-zzzz", ts="2026-09-30T10:00:00+00:00")
        with patch.object(store, "load_events", return_value=[row, second]):
            check("redacted timestamp cannot rank results before limit",
                  store.query("limited", "sm_search", limit=1)[0]["id"] == second["id"])
        grant["fields_redacted"] = ["ts", "id"]
        first = dict(row, title="A")
        second = dict(row, id="ev-fixture-second", title="B", ts="2026-09-30T10:00:00+00:00")
        with patch.object(store, "load_events", return_value=[first, second]):
            order_one = store.query("limited", "sm_search", limit=1)
        with patch.object(store, "load_events", return_value=[second, first]):
            order_two = store.query("limited", "sm_search", limit=1)
        check("hidden timestamps and IDs cannot break visible rank ties", order_one == order_two)
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
