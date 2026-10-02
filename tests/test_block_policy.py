"""Unsafe global Markdown must never bypass current grant projection."""
import datetime
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vault import store
from blocks.travel_log import compute
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
rows = [{"id": "ev-fixture-new1", "kind": "photo", "source": "apple_photos", "ts": "2026-10-01T10:00:00+00:00", "title": "secret title", "location": {"place": "Visible city"}, "fixture": True},
        {"id": "ev-fixture-old1", "kind": "photo", "source": "apple_photos", "ts": "2020-01-01T10:00:00+00:00", "title": "old secret", "location": {"place": "Old city"}, "fixture": True}]
with tempfile.TemporaryDirectory(prefix="memory-block-policy-") as temp:
    Path(temp, "travel-log.md").write_text(compute(rows))
    grant = {"agent": "limited", "kinds": ["photo", "place"], "window_days": 7, "fields_redacted": ["title"]}
    with patch.object(store, "_now", return_value=now), patch.object(store, "load_events", return_value=rows), \
         patch.object(store, "load_grants", return_value=[grant]), \
         patch.object(store, "BLOCKS_DIR", temp), patch.object(store, "AUDIT_PATH", str(Path(temp)/"reads.jsonl")):
        result = store.block("limited", "travel-log")
        check("Block respects narrow grant window", result["records"] == 1 and "Old city" not in result["markdown"])
        check("Block redacts before rendering", "secret title" not in result["markdown"] and "Visible city" in result["markdown"])
        check("Block read produces exactly one audit receipt", len(Path(temp, "reads.jsonl").read_text().splitlines()) == 1)
        Path(temp, "travel-log.md").write_text("corrupt stale GLOBAL SECRET")
        result = store.block("limited", "travel-log")
        check("Block never serves stale broad Markdown bytes", "GLOBAL SECRET" not in result["markdown"] and result["records"] == 1)
        Path(temp, "travel-log.md").write_text(compute(rows))
        grant["window_days"] = 0
        result = store.block("limited", "travel-log")
        check("policy change takes effect without Block rebuild", result["records"] == 0 and "Visible city" not in result["markdown"])
        grant["expires"] = "2020-01-01T00:00:00+00:00"
        try:
            store.block("limited", "travel-log")
            denied = False
        except store.Denied:
            denied = True
        check("expired Block grant fails closed", denied)
        grant.pop("expires")
        grant["fields_redacted"] = ["kind"]
        for source_rows in [rows, []]:
            with patch.object(store, "load_events", return_value=source_rows):
                try:
                    store.block("limited", "travel-log")
                    denied = False
                except store.Denied:
                    denied = True
            check("required Block field redaction denies independently of record presence " + str(len(source_rows)), denied)
print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
