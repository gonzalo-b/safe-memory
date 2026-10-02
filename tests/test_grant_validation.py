"""Malformed policy cannot authorize a read. Synthetic fixtures only."""
import datetime
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vault import store
PASS = FAIL = 0

def check(name, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok  ', name)
    else:
        FAIL += 1
        print('  FAIL', name)

now = datetime.datetime(2026, 10, 2, 12, tzinfo=datetime.timezone.utc)
row = {'id': 'ev-fixture-0001', 'kind': 'photo', 'source': 'apple_photos',
       'ts': now.isoformat(), 'title': 'restricted synthetic title'}
base = {'agent': 'limited', 'kinds': ['photo', 'place'], 'window_days': 7}
invalid = [('expires', 'invalid'), ('expires', '2026-10-03junk'), ('expires', 999999),
           ('expires', '2026-10-03T12:00:00+00:99'), ('window_days', 'invalid'),
           ('window_days', -1), ('window_days', True), ('fields_redacted', 'title'),
           ('fields_redacted', [False]), ('kinds', 'photo'), ('kinds', ['photo', 'typo'])]
with tempfile.TemporaryDirectory(prefix='memory-grants-') as temp:
    Path(temp, 'travel-log.md').write_text('readiness marker')
    audit_path = Path(temp, 'reads.jsonl')
    with patch.object(store, '_now', return_value=now), patch.object(store, 'load_events', return_value=[row]), \
         patch.object(store, 'AUDIT_PATH', str(audit_path)), patch.object(store, 'BLOCKS_DIR', temp):
        for field, value in invalid:
            grant = dict(base, **{field: value})
            with patch.object(store, 'load_grants', return_value=[grant]):
                try:
                    store.query('limited', 'sm_photos')
                    denied = False
                except store.Denied:
                    denied = True
                check(f'malformed Grant {field}={value!r} denies and audits',
                      denied and json.loads(audit_path.read_text().splitlines()[-1])['allowed'] is False)
        with patch.object(store, 'load_grants', return_value=[dict(base, fields_redacted='title')]):
            try:
                store.block('limited', 'travel-log')
                denied = False
            except store.Denied:
                denied = True
            check('malformed Grant cannot authorize a Block', denied)
        with patch.object(store, 'load_grants', return_value=[base]):
            check('valid minimal Grant still reads', len(store.query('limited', 'sm_photos')) == 1)
print(f'\n{PASS} passed, {FAIL} failed')
sys.exit(1 if FAIL else 0)
