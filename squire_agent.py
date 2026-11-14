#!/usr/bin/env python3
"""Squire through Cotlet.dev: stdio MCP server and small CLI over the hosted Cotlet.dev MCP server (stdlib only).

Every tool forwards to the hosted call the Squire page documents: squire_read or squire_write with
{"operation": <tool>, "arguments": {...}}. Source: https://cotlet.dev/integrations/squire-api-mcp-server
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

SLUG = "squire"
NAME = "Squire"
URL = "https://cotlet.dev/mcp/v1"
PAGE = "https://cotlet.dev/integrations/squire-api-mcp-server"
KEY_HELP = "Set COTLET_API_KEY. Create a Cotlet API key with access to Squire in your Cotlet console: https://cotlet.dev"
VERSION = "1.1.0"
PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")

CONFIG = {"mcpServers": {"cotlet": {"url": URL, "headers": {"Authorization": "Bearer ${env:COTLET_API_KEY}"}}}}


def _s(description):
    return {"type": "string", "description": description}


def _obj(props, required=()):
    schema = {"type": "object", "properties": props, "additionalProperties": False}
    if required:
        schema["required"] = list(required)
    return schema


DATE = "YYYY-MM-DD"
ASKS_FIRST = " Waits for your OK in the Cotlet console before it runs."

# The 11 Squire tools of the live page: (name, side, description, input schema).
TOOLS = [
    ("list_barbers", "read",
     "List the barbers on your shop's team. Returns each barber with id and name. Use the ids in the appointment "
     "tools. Reads the team as your signed-in account sees it in Commander.",
     _obj({})),
    ("list_services", "read",
     "List the services on your shop's service menu. Returns each service with id, name, duration in minutes and "
     "price as shown in Squire, in menu order. Use the service ids when you book.",
     _obj({"barber_id": _s("Only services this barber offers.")})),
    ("list_appointments", "read",
     "List appointments for a day or a date range, optionally for one barber. Returns appointments in time order "
     "with client name, barber, services, start and end. Follow next_cursor until it is null. Blocked time is "
     "listed with type blocked so you can tell it from a booking.",
     _obj({"date_from": _s("First day, %s." % DATE),
           "date_to": _s("Last day, %s. Defaults to date_from." % DATE),
           "barber_id": _s("Only this barber. Omit for the whole shop."),
           "cursor": _s("next_cursor from the previous page.")}, ["date_from"])),
    ("create_appointment", "write",
     "Book an appointment for a client with a barber. Books the slot and returns the appointment. It fails with "
     "SLOT_TAKEN if the barber is booked or blocked then, and nothing is created. Payments are not part of this "
     "call." + ASKS_FIRST,
     _obj({"client_id": _s("Client id from list_clients."),
           "barber_id": _s("Barber id from list_barbers."),
           "service_ids": {"type": "array", "items": {"type": "string"},
                           "description": "Service ids from list_services."},
           "start": _s("Start time, YYYY-MM-DDTHH:MM:SS in the shop's time zone.")},
          ["client_id", "barber_id", "service_ids", "start"])),
    ("reschedule_appointment", "write",
     "Move an appointment to a new time or another barber. Moves the booking and returns it with the new times. "
     "It fails with SLOT_TAKEN when the new slot is not free, and the original stays." + ASKS_FIRST,
     _obj({"appointment_id": _s("Appointment id from list_appointments."),
           "start": _s("New start time, YYYY-MM-DDTHH:MM:SS."),
           "barber_id": _s("New barber. Omit to keep the same one.")}, ["appointment_id", "start"])),
    ("cancel_appointment", "write",
     "Cancel a client's appointment. Cancels the booking and returns its new status. Cotlet takes no payment and "
     "issues no refund." + ASKS_FIRST,
     _obj({"appointment_id": _s("Appointment id from list_appointments."),
           "reason": _s("Short note kept with the cancellation.")}, ["appointment_id"])),
    ("block_time", "write",
     "Block a barber's calendar for a time window. Blocks the window so no one can book it and returns the block. "
     "It does not touch existing bookings: check list_appointments first. Undo it with remove_block.",
     _obj({"barber_id": _s("Barber id from list_barbers."),
           "start": _s("Start, YYYY-MM-DDTHH:MM:SS."),
           "end": _s("End, YYYY-MM-DDTHH:MM:SS.")}, ["barber_id", "start", "end"])),
    ("remove_block", "write",
     "Remove a blocked time window from a barber's calendar. Reopens the window for booking. The block can be set "
     "again with block_time.",
     _obj({"block_id": _s("Block id from block_time or list_appointments.")}, ["block_id"])),
    ("list_waitlist", "read",
     "List clients on the shop's waitlist. Returns each waiting client with the barber and the day they asked "
     "for, in the order Squire shows them. Squire notifies the waiting client itself when a slot opens. The "
     "waitlist needs a Squire plan that includes it; on others the call returns an empty list.",
     _obj({"barber_id": _s("Only clients waiting for this barber.")})),
    ("list_clients", "read",
     "List or search your shop's clients. Returns clients with id, name, phone, email and last visit date, as "
     "Squire shows them. Phone and email are personal data: return them only when the user asks for them. "
     "Follow next_cursor until it is null.",
     _obj({"query": _s("Name, phone or email to search for."),
           "cursor": _s("next_cursor from the previous page.")})),
    ("get_revenue_report", "read",
     "Read revenue and client retention from the Reporting Dashboard for a date range. Returns revenue and "
     "returning clients, and per barber when group_by is barber. Figures are in the shop's currency. It reads "
     "the report only and moves no money.",
     _obj({"date_from": _s("First day, %s." % DATE),
           "date_to": _s("Last day, %s." % DATE),
           "group_by": {"type": "string", "enum": ["barber"],
                        "description": "Split by barber. Omit for shop totals."}}, ["date_from", "date_to"])),
]
BY_NAME = {t[0]: t for t in TOOLS}


def annotations(side):
    if side == "read":
        return {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}
    return {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": True}


class Client:
    def __init__(self, key):
        self.key = key
        self.session = None
        self.next_id = 0

    def _post(self, payload):
        headers = {
            "Authorization": "Bearer " + self.key,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(URL, json.dumps(payload).encode(), headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self.session = resp.headers.get("Mcp-Session-Id") or self.session
                return resp.read().decode(), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode(errors="replace")[:300]))

    @staticmethod
    def _parse(body, ctype, rid):
        if "text/event-stream" in ctype:
            for line in body.splitlines():
                if line.startswith("data:"):
                    try:
                        msg = json.loads(line[5:].strip())
                    except ValueError:
                        continue
                    if msg.get("id") == rid:
                        return msg
            raise RuntimeError("No JSON-RPC answer in stream")
        return json.loads(body)

    def rpc(self, method, params=None):
        self.next_id += 1
        rid = self.next_id
        body, ctype = self._post({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        msg = self._parse(body, ctype, rid)
        if "error" in msg:
            raise RuntimeError(msg["error"].get("message", str(msg["error"])))
        return msg.get("result", {})

    def start(self):
        self.rpc("initialize", {
            "protocolVersion": PROTOCOLS[0],
            "capabilities": {},
            "clientInfo": {"name": SLUG + "-mcp", "version": VERSION},
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, tool, args):
        res = self.rpc("tools/call", {"name": tool, "arguments": args})
        text = "\n".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        if res.get("isError"):
            raise RuntimeError(text or "tool error")
        return text


def forward(client, name, args):
    """One Squire tool as the hosted call: squire_read or squire_write with the operation and its arguments."""
    _, side, _, _ = BY_NAME[name]
    return client.call("%s_%s" % (SLUG, side), {"operation": name, "arguments": args})


def missing(name, args):
    required = BY_NAME[name][3].get("required", [])
    return [field for field in required if field not in args]


class Server:
    def __init__(self):
        self.client = None

    def call_tool(self, name, args):
        if name not in BY_NAME:
            return {"content": [{"type": "text", "text": "Unknown tool: %s" % name}], "isError": True}
        args = args or {}
        if not isinstance(args, dict):
            return {"content": [{"type": "text", "text": "arguments must be an object"}], "isError": True}
        lack = missing(name, args)
        if lack:
            return {"content": [{"type": "text", "text": "Missing: %s" % ", ".join(lack)}], "isError": True}
        key = os.environ.get("COTLET_API_KEY")
        if not key:
            return {"content": [{"type": "text", "text": KEY_HELP}], "isError": True}
        try:
            if self.client is None:
                self.client = Client(key)
                self.client.start()
            return {"content": [{"type": "text", "text": forward(self.client, name, args)}]}
        except Exception as e:
            self.client = None
            return {"content": [{"type": "text", "text": str(e)}], "isError": True}

    def handle(self, msg):
        method, rid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
        if rid is None:
            return None  # notification
        if method == "initialize":
            want = params.get("protocolVersion")
            result = {
                "protocolVersion": want if want in PROTOCOLS else PROTOCOLS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SLUG + "-mcp", "version": VERSION},
                "instructions": (
                    "Squire through Cotlet.dev: 11 tools for barbers, services, appointments, blocked time, the "
                    "waitlist, clients and the revenue report, in the user's own Squire account. Bookings, moves "
                    "and cancellations wait for the user's OK in the Cotlet console. Phone and email of clients "
                    "only when the user asks. Set COTLET_API_KEY. More: " + PAGE
                ),
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": [
                {"name": n, "description": d, "inputSchema": s, "annotations": annotations(side)}
                for n, side, d, s in TOOLS
            ]}
        elif method == "tools/call":
            result = self.call_tool(params.get("name", ""), params.get("arguments"))
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found: %s" % method}}
        return {"jsonrpc": "2.0", "id": rid, "result": result}


def serve():
    """MCP stdio transport: one JSON-RPC message per line on stdin/stdout, logs on stderr."""
    server = Server()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = None
        try:
            msg = json.loads(line)
            reply = server.handle(msg) if isinstance(msg, dict) else None
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        except Exception as e:
            print("Error: %s" % e, file=sys.stderr)
            rid = msg.get("id") if isinstance(msg, dict) else None
            reply = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(e)}}
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


def connect():
    print("Claude Code:\n  claude mcp add --transport http cotlet %s --header \"Authorization: Bearer $COTLET_API_KEY\"\n" % URL)
    print("Cursor (~/.cursor/mcp.json):\n" + json.dumps(CONFIG, indent=2) + "\n")
    print("Codex (~/.codex/config.toml):\n  [mcp_servers.cotlet]\n  url = \"%s\"\n  bearer_token_env_var = \"COTLET_API_KEY\"\n" % URL)
    print("Claude and ChatGPT: add the connector URL %s/connect and sign in with Cotlet (no API key)." % URL)


def main():
    p = argparse.ArgumentParser(description="Squire through Cotlet.dev")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="start the stdio MCP server (same as no argument)")
    sub.add_parser("connect", help="print the hosted setup for Claude Code, Cursor, Codex and chat apps")
    sub.add_parser("tools", help="list the 11 Squire tools")
    c = sub.add_parser("call", help="run one Squire tool, e.g. call list_barbers")
    c.add_argument("tool", choices=sorted(BY_NAME))
    c.add_argument("arguments", nargs="?", default="{}", help="JSON object of inputs")
    args = p.parse_args()
    if args.cmd in (None, "serve"):
        return serve()
    if args.cmd == "connect":
        return connect()
    if args.cmd == "tools":
        for n, side, d, _ in TOOLS:
            print("%-24s %-5s %s" % (n, side, d.split(". ")[0]))
        return None
    try:
        inputs = json.loads(args.arguments)
    except ValueError:
        print("arguments must be a JSON object", file=sys.stderr)
        sys.exit(2)
    result = Server().call_tool(args.tool, inputs)
    print(result["content"][0]["text"])
    if result.get("isError"):
        sys.exit(1)
    return None


if __name__ == "__main__":
    main()
