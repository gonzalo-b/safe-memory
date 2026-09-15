"""tests/test_stub.py — the SM-0 contract, asserted.

Self-exiting script, the convention the rest of GB's fleet uses: exit 0 is
pass, and the last line is the count.

    python3 tests/test_stub.py

Every check drives the REAL server the way a client does — one subprocess,
newline-delimited JSON-RPC over stdio — rather than importing handle() and
calling it. The transport is half of what the contract promises, so the test
that proves the contract has to cross it.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
import tempfile

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HOME)

STUB = os.path.join(HOME, "vault", "mcp_stub.py")
SCHEMA_DIR = os.path.join(HOME, "schema")

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}{(' — ' + str(detail)) if detail else ''}")


# --------------------------------------------------------------- the client --
def talk(requests, agent="lazy", audit_dir=None, env_extra=None):
    """Run the stub as a subprocess, feed it lines, read the answers back."""
    env = dict(os.environ)
    env["SAFE_MEMORY_AUDIT"] = os.path.join(audit_dir or tempfile.mkdtemp(prefix="sm-audit-"),
                                            "reads.jsonl")
    env.pop("SAFE_MEMORY_AGENT", None)
    env.update(env_extra or {})
    body = []
    if agent is not None:
        body.append({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                     "params": {"protocolVersion": "2025-06-18",
                                "clientInfo": {"name": agent, "version": "test"}}})
    body.extend(requests)
    payload = "".join(json.dumps(r) + "\n" for r in body)
    proc = subprocess.run([sys.executable, STUB], input=payload, text=True,
                          capture_output=True, timeout=60, env=env, cwd=HOME)
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out, proc


def call(tool, args=None, agent="lazy", audit_dir=None):
    out, proc = talk([{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args or {}}}],
                     agent=agent, audit_dir=audit_dir)
    assert proc.returncode == 0, proc.stderr[-400:]
    last = out[-1]
    return last.get("result") or {}, last


# ----------------------------------------------------------------- 1. shape --
print("== schemas ==")
for name in ("event.json", "grant.json"):
    path = os.path.join(SCHEMA_DIR, name)
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        doc = None
        check(f"{name} parses", False, e)
    if doc:
        check(f"{name} parses", True)
        check(f"{name} declares $schema and $id",
              bool(doc.get("$schema")) and bool(doc.get("$id")))
        check(f"{name} lists required fields", bool(doc.get("required")))

with open(os.path.join(SCHEMA_DIR, "event.json"), encoding="utf-8") as f:
    EVENT_SCHEMA = json.load(f)
EVENT_PROPS = set(EVENT_SCHEMA["properties"])
EVENT_KINDS = set(EVENT_SCHEMA["properties"]["kind"]["enum"])
check("event schema closes additionalProperties",
      EVENT_SCHEMA.get("additionalProperties") is False)

with open(os.path.join(SCHEMA_DIR, "grant.json"), encoding="utf-8") as f:
    GRANT_SCHEMA = json.load(f)
check("grant schema requires agent, kinds and window_days",
      set(GRANT_SCHEMA["required"]) == {"agent", "kinds", "window_days"})


# -------------------------------------------------------------- 2. protocol --
print("\n== protocol ==")
out, proc = talk([{"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                  {"jsonrpc": "2.0", "id": 3, "method": "nope/nope"}])
check("server exits 0 when stdin closes", proc.returncode == 0, proc.stderr[-300:])
init = out[0]["result"]
check("initialize returns a protocolVersion", bool(init.get("protocolVersion")))
check("initialize names the server", (init.get("serverInfo") or {}).get("name") == "safe-memory")
check("initialize instructions say the rows are a stub",
      "stub" in (init.get("instructions") or "").lower())
check("initialize instructions state the boundary rule",
      "mindbase" in (init.get("instructions") or "").lower())

tools = out[1]["result"]["tools"]
names = [t["name"] for t in tools]
EXPECTED = ["sm_search", "sm_timeline", "sm_purchases", "sm_media", "sm_photos", "sm_grants"]
check("tools/list answers exactly the six contract tools", names == EXPECTED, names)
check("every tool declares an inputSchema",
      all(isinstance(t.get("inputSchema"), dict) for t in tools))
check("every tool declares a description",
      all((t.get("description") or "").strip() for t in tools))
check("an unknown method is -32601", (out[2].get("error") or {}).get("code") == -32601)

out, _ = talk([{"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "sm_delete_everything", "arguments": {}}}])
check("an unknown tool is -32602", (out[-1].get("error") or {}).get("code") == -32602)


# ----------------------------------------------------------------- 3. reads --
print("\n== the six tools answer ==")
today = datetime.date.today()
yesterday = (today - datetime.timedelta(days=1)).isoformat()

res, _ = call("sm_purchases", {"limit": 10})
purchases = res["structuredContent"]
check("sm_purchases returns events", purchases["count"] > 0)
check("sm_purchases returns only purchases",
      all(e["kind"] == "purchase" for e in purchases["events"]))
check("every row is stamped fixture: true",
      all(e.get("fixture") is True for e in purchases["events"]))
check("every row carries only schema'd fields",
      all(set(e) <= EVENT_PROPS for e in purchases["events"]),
      sorted(set().union(*[set(e) for e in purchases["events"]]) - EVENT_PROPS))
check("every kind is in the schema's enum",
      all(e["kind"] in EVENT_KINDS for e in purchases["events"]))

yday = [e for e in purchases["events"] if e["ts"][:10] == yesterday]
check("'what did we buy yesterday' has an answer today and every other day",
      len(yday) >= 1, f"{yesterday}: {len(yday)}")
check("a purchase carries an integer amount in minor units",
      all(isinstance(e.get("amount"), int) for e in yday))

res, _ = call("sm_timeline", {"date": yesterday})
timeline = res["structuredContent"]
check("sm_timeline is one local day only",
      timeline["count"] > 0 and all(e["ts"][:10] == yesterday for e in timeline["events"]))
check("sm_timeline crosses kinds",
      len({e["kind"] for e in timeline["events"]}) > 1,
      sorted({e["kind"] for e in timeline["events"]}))

res, _ = call("sm_media", {"kind": "music"})
media = res["structuredContent"]
check("sm_media kind=music is listens only",
      media["count"] > 0 and all(e["kind"] == "listen" for e in media["events"]))
res, _ = call("sm_media", {})
check("sm_media with no kind spans watch and listen",
      {e["kind"] for e in res["structuredContent"]["events"]} == {"watch", "listen"})

res, _ = call("sm_photos", {"place": "Bariloche"})
photos = res["structuredContent"]
check("sm_photos filters by place",
      photos["count"] > 0 and all("bariloche" in (e["location"]["place"] or "").lower()
                                  for e in photos["events"]))

res, _ = call("sm_search", {"query": "cafetera"})
found = res["structuredContent"]
check("sm_search finds a title", found["count"] == 1 and "Cafetera" in found["events"][0]["title"])
res, _ = call("sm_search", {"query": "Oster"})
check("sm_search finds an entity", res["structuredContent"]["count"] == 1)
res, _ = call("sm_search", {"query": "zzz-nothing-matches-zzz"})
check("a search with no hits is an empty list, not an error",
      res["structuredContent"]["count"] == 0 and res.get("isError") is False)


# ---------------------------------------------------------------- 4. grants --
print("\n== grants are the whole point ==")
res, _ = call("sm_grants", {}, agent="lazy")
g = res["structuredContent"]
check("sm_grants reports the calling agent's grant", g["granted"] is True and g["agent"] == "lazy")
check("the lazy grant is 90 days", g["window_days"] == 90)

res, _ = call("sm_grants", {}, agent="siri")
gs = res["structuredContent"]
check("the siri grant is narrower", gs["window_days"] == 7)
check("the siri grant redacts amounts", "amount" in gs["fields_redacted"])
check("sm_grants never reports another agent's grant", gs["agent"] == "siri")

res, last = call("sm_purchases", {"limit": 10}, agent="siri")
siri_rows = res["structuredContent"]["events"]
check("siri sees purchases", len(siri_rows) > 0)
check("siri never sees an amount",
      all("amount" not in e and "currency" not in e for e in siri_rows))
check("the siri window clips the 40-day-old purchase",
      all((datetime.date.today() - datetime.date.fromisoformat(e["ts"][:10])).days <= 7
          for e in siri_rows))

res, last = call("sm_photos", {}, agent="siri")
check("siri is refused a kind it was not granted", last["result"]["isError"] is True)
check("the refusal says why and returns nothing",
      res["structuredContent"]["denied"] is True
      and res["structuredContent"]["count"] == 0
      and "may not read" in res["structuredContent"]["reason"])

res, last = call("sm_purchases", {}, agent="stranger")
check("an agent with no grant reads nothing", last["result"]["isError"] is True)
check("the no-grant refusal names the agent",
      "stranger" in res["structuredContent"]["reason"])

out, _ = talk([{"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                "params": {"name": "sm_purchases", "arguments": {}}}], agent=None)
denied = out[-1]["result"]["structuredContent"]
check("a client that never identified itself reads nothing",
      out[-1]["result"]["isError"] is True and denied["count"] == 0)

res, _ = call("sm_purchases", {"agent": "lazy"}, agent="siri")
check("an agent cannot widen its grant through a tool argument",
      all("amount" not in e for e in res["structuredContent"]["events"]))


# ----------------------------------------------------------------- 5. audit --
print("\n== every read leaves a line ==")
audit_dir = tempfile.mkdtemp(prefix="sm-audit-")
call("sm_purchases", {}, agent="lazy", audit_dir=audit_dir)
call("sm_photos", {}, agent="siri", audit_dir=audit_dir)
audit_file = os.path.join(audit_dir, "reads.jsonl")
lines = []
if os.path.exists(audit_file):
    with open(audit_file, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
check("the audit log exists after a read", bool(lines))
check("an allowed read is audited",
      any(l["allowed"] and l["tool"] == "sm_purchases" and l["agent"] == "lazy" for l in lines))
check("a REFUSED read is audited too",
      any(not l["allowed"] and l["agent"] == "siri" for l in lines))
check("every audit line carries a timestamp and a count",
      all(l.get("ts") and isinstance(l.get("count"), int) for l in lines))


# ---------------------------------------------------------------- 6. no net --
print("\n== a memory vault that cannot phone out ==")
BANNED = ("import requests", "import httpx", "import urllib", "import socket",
          "from urllib", "http.client", "subprocess.")
for rel in ("vault/store.py", "vault/mcp_stub.py"):
    with open(os.path.join(HOME, rel), encoding="utf-8") as f:
        src = "\n".join(l for l in f.read().splitlines()
                        if not l.strip().startswith("#"))
    hits = [b for b in BANNED if b in src]
    check(f"{rel} imports no network client and shells out to nothing", not hits, hits)

for rel in ("vault/store.py", "vault/mcp_stub.py"):
    with open(os.path.join(HOME, rel), encoding="utf-8") as f:
        src = f.read()
    writes = [w for w in ("os.remove(", "os.unlink(", "shutil.rmtree(", "os.rmdir(")
              if w in src]
    check(f"{rel} deletes nothing", not writes, writes)

# The store is read-only apart from the audit log. Every open() for writing in
# the package must therefore name AUDIT_PATH; a second write target would be a
# store that mutates what it is meant to report.
import re  # noqa: E402

for rel in ("vault/store.py", "vault/mcp_stub.py"):
    with open(os.path.join(HOME, rel), encoding="utf-8") as f:
        src = f.read()
    write_opens = re.findall(r"open\(([^,\n]+),\s*\"(a|w|ab|wb|a\+|w\+)\"", src)
    bad = [t for t, _mode in write_opens if "AUDIT_PATH" not in t]
    check(f"{rel} opens nothing for writing except the audit log", not bad, bad)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
