"""vault/store.py — the read-only event store the six MCP tools answer from.

SM-0 (the contract stage) backs this with `fixtures/`. SM-1 replaces the two
loaders below with an SQLCipher-backed store and changes NOTHING else: every
rule that decides what an agent may see — the grant lookup, the window clip,
the field redaction, the audit line — lives here, not in the transport, so it
survives the storage swap.

Standard library only. No network client is imported anywhere in this package,
and `tests/test_stub.py` greps the source to keep it that way: a memory vault
that can phone out is not a memory vault.
"""
from __future__ import annotations

import datetime
import json
import os

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.environ.get("SAFE_MEMORY_FIXTURES", os.path.join(HOME, "fixtures"))
AUDIT_PATH = os.environ.get("SAFE_MEMORY_AUDIT", os.path.join(HOME, "audit", "reads.jsonl"))

KINDS = ("purchase", "watch", "listen", "photo", "place", "health")
MEDIA_KINDS = {"video": "watch", "music": "listen"}


# --------------------------------------------------------------------- time --
def _now() -> datetime.datetime:
    return datetime.datetime.now().astimezone()


def _parse_ts(value) -> datetime.datetime | None:
    """ISO 8601 in, aware datetime out. A naive string takes the local zone,
    because every timestamp in this store is a local-day fact."""
    if not value:
        return None
    try:
        dt = datetime.datetime.fromisoformat(str(value))
    except ValueError:
        try:
            dt = datetime.datetime.fromisoformat(str(value)[:10])
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


# -------------------------------------------------------------------- events --
def _resolve_fixture_row(row: dict) -> dict | None:
    """One fixture line to one event.

    A fixture row may carry `day_offset` + `time` instead of `ts`. It has to:
    "what did we buy yesterday" is the question this stub exists to answer, and
    a frozen timestamp stops answering it the day after it is written. The
    resolved row is stamped `fixture: true` — the real store never sets that
    key, so no caller can mistake one for the other.
    """
    if not isinstance(row, dict):
        return None
    out = dict(row)
    if "ts" not in out:
        offset = out.pop("day_offset", None)
        clock = out.pop("time", "12:00:00")
        if offset is None:
            return None
        try:
            day = (_now() - datetime.timedelta(days=int(offset))).date()
            hh, mm, ss = (list(str(clock).split(":")) + ["0", "0", "0"])[:3]
            stamp = datetime.datetime(day.year, day.month, day.day,
                                      int(hh), int(mm), int(ss)).astimezone()
        except (TypeError, ValueError):
            return None
        out["ts"] = stamp.isoformat(timespec="seconds")
    out["fixture"] = True
    return out


def load_events() -> list[dict]:
    """Every event, newest first. A malformed line is skipped, never fatal."""
    path = os.path.join(FIXTURES, "events.jsonl")
    events: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                resolved = _resolve_fixture_row(row)
                if resolved and resolved.get("kind") in KINDS:
                    events.append(resolved)
    except OSError:
        return []
    events.sort(key=lambda e: e.get("ts") or "", reverse=True)
    return events


# -------------------------------------------------------------------- grants --
def load_grants() -> list[dict]:
    path = os.path.join(FIXTURES, "grants.json")
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return [r for r in rows if isinstance(r, dict) and r.get("agent")]


def grant_for(agent: str) -> dict | None:
    """The live grant for `agent`, or None. An expired grant is not a grant."""
    if not agent:
        return None
    now = _now()
    for row in load_grants():
        if row.get("agent") != agent:
            continue
        expires = _parse_ts(row.get("expires"))
        if expires and expires < now:
            return None
        return row
    return None


class Denied(Exception):
    """No grant, or none covering what was asked. Carries the reason."""


class AuditFailed(Exception):
    """The audit line could not be written, so the read does not happen.

    Found by the cross-family review gate: `audit()` used to swallow OSError
    "so an audit that can break a read is not an incentive to skip it", and a
    probe with the audit writer raising PermissionError still got a purchase
    back. That reasoning was backwards for a privacy vault. CONTRACT.md §3
    promises "every read is one append-only audit line", and a promise that
    quietly degrades to "usually" is worse than one that fails loudly: an
    unaudited read is exactly the read nobody can later account for.
    """


def _redact(event: dict, fields) -> dict:
    if not fields:
        return event
    out = dict(event)
    for field in fields:
        if field == "location":
            loc = out.get("location") or {}
            # A redacted location keeps the place name and loses the point: a
            # town is an answer, coordinates are a tracker.
            out["location"] = {"lat": None, "lon": None, "place": loc.get("place")}
        else:
            out.pop(field, None)
    return out


# -------------------------------------------------------------------- audit --
def audit(agent: str, tool: str, args: dict, allowed: bool,
          count: int, reason: str = "") -> None:
    """One append-only line per read, refusals included.

    Raises AuditFailed when the line cannot be written. The caller must let
    that reach the client rather than answering anyway — see AuditFailed.
    """
    line = {
        "ts": _now().isoformat(timespec="seconds"),
        "agent": agent or "",
        "tool": tool,
        "args": {k: v for k, v in (args or {}).items() if v is not None},
        "allowed": bool(allowed),
        "count": int(count),
    }
    if reason:
        line["reason"] = reason
    try:
        os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
        with open(AUDIT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
    except OSError as e:
        raise AuditFailed(f"the audit log at {AUDIT_PATH} is not writable: {e}") from e


# --------------------------------------------------------------------- query --
def _match(event: dict, query: str | None) -> bool:
    if not query:
        return True
    needle = query.strip().lower()
    if not needle:
        return True
    hay = " ".join([
        str(event.get("title") or ""),
        " ".join(str(e) for e in (event.get("entities") or [])),
        str(event.get("source") or ""),
        str(((event.get("location") or {}) or {}).get("place") or ""),
    ]).lower()
    return all(word in hay for word in needle.split())


def query(agent: str, tool: str, *, kinds=None, query_text=None, since=None,
          until=None, place=None, source=None, date=None, limit: int = 20) -> list[dict]:
    """The one read path. Grant first, window second, filters third, audit last.

    Raises Denied when the agent has no grant at all or asked only for kinds
    it may not read. A narrower-than-asked answer is NOT an error: the window
    clip and the kind intersection are applied silently and recorded.
    """
    grant = grant_for(agent)
    if grant is None:
        audit(agent, tool, {"kinds": kinds, "query": query_text}, False, 0, "no grant")
        raise Denied(f"agent {agent!r} has no grant")

    allowed_kinds = [k for k in (grant.get("kinds") or []) if k in KINDS]
    asked = [k for k in (kinds or allowed_kinds) if k in KINDS]
    effective = [k for k in asked if k in allowed_kinds]
    if not effective:
        audit(agent, tool, {"kinds": kinds}, False, 0, "kinds not granted")
        raise Denied(f"agent {agent!r} may not read {sorted(set(asked)) or 'anything'}")

    now = _now()
    try:
        window_days = max(0, int(grant.get("window_days", 0)))
    except (TypeError, ValueError):
        window_days = 0
    floor = (now - datetime.timedelta(days=window_days)).replace(
        hour=0, minute=0, second=0, microsecond=0)

    since_dt = _parse_ts(since)
    if since_dt and since_dt > floor:
        floor = since_dt
    until_dt = _parse_ts(until)
    day = None
    if date:
        parsed = _parse_ts(date)
        day = parsed.date() if parsed else None

    out = []
    for event in load_events():
        if event.get("kind") not in effective:
            continue
        ts = _parse_ts(event.get("ts"))
        if ts is None or ts < floor:
            continue
        if until_dt and ts > until_dt:
            continue
        if day and ts.date() != day:
            continue
        if source and event.get("source") != source:
            continue
        if place:
            where = str(((event.get("location") or {}) or {}).get("place") or "").lower()
            if place.strip().lower() not in where:
                continue
        if not _match(event, query_text):
            continue
        out.append(_redact(event, grant.get("fields_redacted")))
        if len(out) >= max(1, int(limit)):
            break

    audit(agent, tool,
          {"kinds": effective, "query": query_text, "since": since,
           "until": until, "place": place, "source": source, "date": date},
          True, len(out))
    return out


def grants(agent: str) -> dict:
    """What THIS agent may read, and until when. Never another agent's grant:
    the roster is GB's, not a readable resource."""
    grant = grant_for(agent)
    if grant is None:
        audit(agent, "sm_grants", {}, False, 0, "no grant")
        return {"agent": agent, "granted": False, "kinds": [], "window_days": 0,
                "expires": None, "fields_redacted": [],
                "reason": "no grant; ask GB to add one in the Safe Memory settings"}
    audit(agent, "sm_grants", {}, True, 1)
    return {
        "agent": agent,
        "granted": True,
        "kinds": list(grant.get("kinds") or []),
        "window_days": grant.get("window_days", 0),
        "expires": grant.get("expires"),
        "fields_redacted": list(grant.get("fields_redacted") or []),
        "note": grant.get("note", ""),
    }
