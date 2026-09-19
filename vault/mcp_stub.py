"""vault/mcp_stub.py — the Safe Memory MCP server, SM-0 stub edition.

Speaks MCP over stdio: newline-delimited JSON-RPC 2.0 on stdin/stdout, the
same transport `claude mcp add`, `codex mcp add` and MindBase's own client
use. Three methods are implemented because three are what the contract needs:
`initialize`, `tools/list`, `tools/call`. Anything else answers JSON-RPC
error -32601 rather than pretending.

Six tools, all read-only, all grant-checked, every read one audit line. They
are the SAME six SM-1 ships against the SQLCipher store: this file is the
transport and the argument shapes, `vault/store.py` is every rule about what
an agent may see, and SM-1 replaces the loaders in that module without
touching this one.

The calling agent is taken from the MCP client identity in `initialize`
(`params.clientInfo.name`), never from a tool argument — an agent that could
name itself in a call could name itself into a wider grant. With no
`initialize`, the agent is unset and every read is denied.

Standard library only. Run it by hand with:
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 vault/mcp_stub.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vault import store  # noqa: E402

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "memory"


def _read_version() -> str:
    try:
        with open(os.path.join(store.HOME, "VERSION"), encoding="utf-8") as f:
            return f.read().strip() or "0.0.0"
    except OSError:
        return "0.0.0"


INSTRUCTIONS = (
    "Safe Memory answers what happened in GB's life: what he bought, watched, "
    "listened to, and where he was. It never stores ideas or plans - that is "
    "MindBase's half, and asking here for one returns nothing. Every read is "
    "checked against this agent's grant and appended to an audit log; call "
    "sm_grants first if you need to know what you may see. "
    "THIS IS THE SM-0 STUB: every row it returns is a fixture, stamped "
    "fixture: true, and none of it happened."
)

_STR = {"type": "string"}
_KINDS = {"type": "array", "items": {"type": "string", "enum": list(store.KINDS)}}

TOOLS = [
    {
        "name": "sm_search",
        "description": "Free text across every event kind this agent may read.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": _STR, "kinds": _KINDS, "since": _STR,
                           "until": _STR, "limit": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "sm_timeline",
        "description": "What happened on one local day: purchases, media, places.",
        "inputSchema": {
            "type": "object",
            "properties": {"date": _STR, "limit": {"type": "integer"}},
            "required": ["date"],
        },
    },
    {
        "name": "sm_purchases",
        "description": "What did we order, what do I own. Amounts are in minor units.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": _STR, "since": _STR, "until": _STR,
                           "source": _STR, "limit": {"type": "integer"}},
        },
    },
    {
        "name": "sm_media",
        "description": "What did I watch or listen to. kind: video | music; omitted means both.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": _STR, "since": _STR, "until": _STR,
                           "kind": {"type": "string", "enum": ["video", "music"]},
                           "limit": {"type": "integer"}},
        },
    },
    {
        "name": "sm_photos",
        "description": "Where was I, when. Metadata only: no image ever leaves the machine.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": _STR, "place": _STR, "since": _STR,
                           "until": _STR, "limit": {"type": "integer"}},
        },
    },
    {
        "name": "sm_grants",
        "description": "What this agent may read, how far back, and until when.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

TOOL_NAMES = tuple(t["name"] for t in TOOLS)


class Session:
    """One stdio connection. Holds the identity `initialize` declared."""

    def __init__(self):
        self.agent = os.environ.get("SAFE_MEMORY_AGENT", "") or ""

    # ------------------------------------------------------------- dispatch --
    def call_tool(self, name: str, args: dict) -> dict:
        args = args or {}
        limit = args.get("limit") or 20
        if name == "sm_grants":
            return store.grants(self.agent)
        if name == "sm_search":
            rows = store.query(self.agent, name, kinds=args.get("kinds"),
                               query_text=args.get("query"), since=args.get("since"),
                               until=args.get("until"), limit=limit)
        elif name == "sm_timeline":
            rows = store.query(self.agent, name, date=args.get("date"), limit=limit)
        elif name == "sm_purchases":
            rows = store.query(self.agent, name, kinds=["purchase"],
                               query_text=args.get("query"), since=args.get("since"),
                               until=args.get("until"), source=args.get("source"),
                               limit=limit)
        elif name == "sm_media":
            kind = args.get("kind")
            kinds = [store.MEDIA_KINDS[kind]] if kind in store.MEDIA_KINDS else ["watch", "listen"]
            rows = store.query(self.agent, name, kinds=kinds,
                               query_text=args.get("query"), since=args.get("since"),
                               until=args.get("until"), limit=limit)
        elif name == "sm_photos":
            rows = store.query(self.agent, name, kinds=["photo", "place"],
                               query_text=args.get("query"), place=args.get("place"),
                               since=args.get("since"), until=args.get("until"),
                               limit=limit)
        else:  # pragma: no cover - guarded by the caller
            raise ValueError(f"unknown tool: {name}")
        return {"events": rows, "count": len(rows), "agent": self.agent,
                "stub": True}

    def handle(self, request: dict) -> dict | None:
        """One JSON-RPC request in, one response out. None for a notification."""
        rid = request.get("id")
        method = request.get("method") or ""
        params = request.get("params") or {}

        if method == "initialize":
            client = params.get("clientInfo") or {}
            name = str(client.get("name") or "").strip()
            if name:
                self.agent = name
            return _result(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": _read_version()},
                "instructions": INSTRUCTIONS,
            })

        if method in ("notifications/initialized", "initialized"):
            return None

        if method == "tools/list":
            return _result(rid, {"tools": TOOLS})

        if method == "tools/call":
            name = params.get("name")
            if name not in TOOL_NAMES:
                return _error(rid, -32602, f"unknown tool: {name!r}")
            try:
                payload = self.call_tool(name, params.get("arguments") or {})
            except (store.Denied, store.AuditFailed) as e:
                # A refusal is a RESULT, not a transport error: the caller
                # asked a well-formed question and the answer is "you may not
                # see that". isError lets an agent say so out loud.
                #
                # An unwritable audit log lands here for the same reason and
                # with the same shape: CONTRACT.md §3 promises every read is
                # one audit line, so a read that cannot be audited does not
                # happen, and the caller is told why rather than handed
                # unaccountable data.
                payload = {"denied": True, "reason": str(e), "agent": self.agent,
                           "events": [], "count": 0, "stub": True,
                           "unaudited": isinstance(e, store.AuditFailed)}
                return _result(rid, {
                    "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                    "structuredContent": payload,
                    "isError": True,
                })
            except Exception as e:  # pragma: no cover - defensive
                return _error(rid, -32603, f"{type(e).__name__}: {e}")
            return _result(rid, {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "structuredContent": payload,
                "isError": False,
            })

        if rid is None:
            return None
        return _error(rid, -32601, f"method not found: {method!r}")


def _result(rid, result) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _error(rid, code, message) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def serve(stdin=None, stdout=None) -> int:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    session = Session()
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            stdout.write(json.dumps(_error(None, -32700, "parse error")) + "\n")
            stdout.flush()
            continue
        response = session.handle(request)
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(serve())
