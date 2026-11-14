# How to connect Squire to ChatGPT, Claude and any AI agent

**Let your AI agent run the chair schedule.** Cotlet.dev connects your own signed-in Squire account to ChatGPT, Claude and any AI agent over MCP, and to n8n, Make and scripts over REST: appointments, barbers, clients, waitlist and reports for your barbershop.

Unofficial: Cotlet is independent and **not affiliated with Squire**.

## What you can ask

> Brief each barber's day at 7 am: every booking with client, services, start and end.

> Book waitlist clients into the gaps in tomorrow's schedule, after I approve each booking.

> Marcus is out sick today. Move his bookings to another barber with the same time open and the same services.

> Block Dev's calendar on Friday from 1 pm to 5 pm for time off.

> Show Monday revenue by barber for last week.

> Find clients who have not come in for 60 days.

## Connect in 2 minutes

1. **Log in to Commander yourself.** Make a Cotlet account at [cotlet.dev](https://cotlet.dev/app/signup?app=squire&utm_source=github&utm_medium=readme&utm_campaign=squire), open Squire in its Cloud Browser, log in to Commander with your own shop login, then press Enable for agents.
2. **Add the Cotlet address.** Paste `https://cotlet.dev/mcp/v1` into your agent as an MCP server or connector.
3. **Approve the connection.** Chat apps send you to a Cotlet sign-in. Code editors, n8n and scripts take an API key from the console.

Squire shares one address, `https://cotlet.dev/mcp/v1`, with every other app on your Cotlet account. If you enable Squire after connecting the agent, refresh the connector so the Squire tools appear. Free 7-day trial with 2,000 credits, no card needed.

### Claude

Settings > Connectors > Add custom connector, URL `https://cotlet.dev/mcp/v1/connect`.

### Claude Code

```bash
claude mcp add --transport http cotlet \
  https://cotlet.dev/mcp/v1 \
  --header "Authorization: Bearer $COTLET_API_KEY"
```

### ChatGPT

Settings > Apps & Connectors > Create, MCP server URL `https://cotlet.dev/mcp/v1/connect`, Authentication: OAuth. No API key is needed.

### Cursor

Copy `.cursor/mcp.json` from this repository into your project or `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "cotlet": {
      "url": "https://cotlet.dev/mcp/v1",
      "headers": { "Authorization": "Bearer ${env:COTLET_API_KEY}" }
    }
  }
}
```

### Codex

```toml
# ~/.codex/config.toml
[mcp_servers.cotlet]
url = "https://cotlet.dev/mcp/v1"
bearer_token_env_var = "COTLET_API_KEY"
```

### n8n, Make and Zapier

- n8n: MCP Client Tool inside an AI Agent, Transport HTTP Streamable, URL `https://cotlet.dev/mcp/v1`, Auth Bearer with your Cotlet key, tool `squire_read`.
- Make: MCP Client > Call a tool. Zapier: MCP Client by Zapier > Run Tool. Server URL `https://cotlet.dev/mcp/v1`, your Cotlet key as the token, tool `squire_write`.

## Squire REST API

Create a Cotlet API key with access to Squire and store it as `COTLET_API_KEY` in your environment or your automation platform's credential store, outside shared workflow exports.

```bash
curl https://cotlet.dev/api/v1/squire/barbers \
  -H "Authorization: Bearer $COTLET_API_KEY"
```

A successful call puts the tool output in `result`. MCP and REST carry the same 11 tools, inputs and answers, with one API key and one price. Agents use MCP; scripts, sheets and HTTP steps in n8n, Make or Zapier use REST at `https://cotlet.dev/api/v1/squire`.

## Squire tools through Cotlet.dev

6 read, 5 write. Over MCP each tool is an operation of `squire_read` or `squire_write`.

| Tool | What it does | Access | REST endpoint |
|---|---|---|---|
| `list_barbers` | List the barbers on your shop's team | read | `GET /api/v1/squire/barbers` |
| `list_services` | List the services on your shop's service menu | read | `GET /api/v1/squire/services` |
| `list_appointments` | List appointments for a day or a date range, optionally for one barber | read | `GET /api/v1/squire/appointments` |
| `create_appointment` | Book an appointment for a client with a barber | write, asks first | `POST /api/v1/squire/clients/{client_id}/appointments` |
| `reschedule_appointment` | Move an appointment to a new time or another barber | write, asks first | `POST /api/v1/squire/appointments/{appointment_id}/reschedule` |
| `cancel_appointment` | Cancel a client's appointment | write, asks first | `POST /api/v1/squire/appointments/{appointment_id}/cancel` |
| `block_time` | Block a barber's calendar for a time window | write | `POST /api/v1/squire/barbers/{barber_id}/time/block` |
| `remove_block` | Remove a blocked time window from a barber's calendar | write | `DELETE /api/v1/squire/blocks/{block_id}` |
| `list_waitlist` | List clients on the shop's waitlist | read | `GET /api/v1/squire/waitlists` |
| `list_clients` | List or search your shop's clients | read | `GET /api/v1/squire/clients` |
| `get_revenue_report` | Read revenue and client retention from the Reporting Dashboard for a date range | read | `GET /api/v1/squire/revenue-report` |

Times are in the shop's time zone. A slot that is booked or blocked fails with `SLOT_TAKEN` and nothing changes. Squire lists the Wait List under its PRO plan; on other plans the list comes back empty. Phone and email come back only when you ask for them. Revenue is in the shop's currency.

## Approvals and undo

Nothing reaches a client before you approve. 3 of the 5 write tools ask first: `create_appointment`, `reschedule_appointment` and `cancel_appointment` wait in your Cotlet console. `block_time` and `remove_block` run at once, because a block reaches no client and undoes in one call. Reads run at once too. For a scheduled run you can switch the wait off per tool.

| Action | Undo |
|---|---|
| Book an appointment | Cancel it; Squire may already have sent the confirmation |
| Reschedule an appointment | Move it back; the client may hear about both changes |
| Cancel an appointment | Book it again; a no-show or late fee is never charged by a tool |
| Block time | Remove the block |
| Remove a block | Block the window again |

A block does not clear the bookings already in its window. Ask the agent to list them first. When a whole day moves, let the agent go one booking at a time, so each client hears about a single change.

## Run it locally (stdio)

This repository is a small MCP server for clients that only start local processes. It speaks MCP over stdio, lists the 11 Squire tools without any key, and forwards every tool call to the hosted Cotlet.dev server as `squire_read` or `squire_write`. The hosted URL above stays the recommended setup. Python 3.10+, no dependencies.

```bash
# COTLET_API_KEY holds your Cotlet API key
claude mcp add squire -e COTLET_API_KEY="$COTLET_API_KEY" -- \
  uvx --from git+https://github.com/cotlet-connect/squire-mcp squire-mcp
```

`mcp.json` in this repository has the same server for clients that read a JSON config. Or with Docker:

```bash
docker build -t squire-mcp .
docker run -i --rm -e COTLET_API_KEY squire-mcp
```

Without `COTLET_API_KEY` a tool call answers with where to create a key.

## Command line

```bash
python3 squire_agent.py connect                     # hosted setup for Claude Code, Cursor, Codex and chat apps
python3 squire_agent.py tools                       # the 11 Squire tools
python3 squire_agent.py call list_barbers           # run one tool through Cotlet.dev
python3 squire_agent.py call list_appointments '{"date_from": "2026-11-16"}'
python3 squire_agent.py serve                       # stdio MCP server (same as no argument)
```

## Does Squire have an API or MCP server?

No. Squire has no MCP server, no public API and no developer docs (checked 28 Oct 2026). Zapier, n8n and Pipedream have no Squire app, and clients can be exported by hand from Commander only as a snapshot. On GitHub, repos named squire-mcp are coding tools of the same name, not servers for Squire barbershops. Cotlet runs 11 Squire tools hosted, over MCP for agents and REST for scripts.

## Privacy and access

- **What Cotlet stores:** your logged-in Commander profile, AES-256-GCM encrypted, in Finland. Never the password.
- **What your agent gets:** 11 Squire tools. No cookie, no login.
- **What the session sees:** what your Commander login sees: the whole shop for an owner, one chair for a barber.
- **What no tool touches:** checkout, cards on file, tips, deposits, booth rent and payouts.
- **If Squire asks for a code:** you type it in yourself.
- **How to cut access:** disable for agents, reset the browser or delete the key. The next call fails.

Client phone numbers and emails sit in the same Commander login, so give the agent a Squire user that sees only what it needs. Read Squire's terms in your own browser and look for rules on bots, automated access and shared logins before you connect.

## Price

10 credits per successful call, MCP or REST, and 50 credits a day for the Cloud Browser. One price for every barber in the shop. Only successful calls use credits; failed calls and timeouts cost nothing. Credit packs start at 5,000 credits for $29. Your Squire plan is billed by Squire as before. [Full pricing](https://cotlet.dev/pricing?utm_source=github&utm_medium=readme&utm_campaign=squire)

## Questions from Squire users

**How do I connect Squire to ChatGPT or Claude?**

Sign up at cotlet.dev, log in to Squire once in its Cloud Browser and add Cotlet to ChatGPT or Claude, following the steps in your console. No API key is needed. ChatGPT and Claude then work in your Squire account through Cotlet, in their phone apps too.

**Which Squire plan do I need?**

Cotlet works in your own Squire account, so it can only do what your plan shows in Commander. Squire's pricing page lists the waitlist and multiple barber accounts under its PRO plan and the Reporting Dashboard from the first plan (checked 28 Oct 2026).

**Can it take payments or issue refunds?**

No. Payments, payouts, rent collection and card processing stay in Squire. The tools book, move and cancel appointments and read reports.

**Does it work for an independent barber?**

Yes. Squire has accounts for independent barbers, and the tools then see your own chair: your bookings, blocks, clients and revenue.

**Can I use the Squire API without an AI agent?**

Yes. Call Cotlet's REST API from a script or an HTTP step in n8n, Make or Zapier with your Cotlet key.

## Find it on

- [Squire on Cotlet.dev](https://cotlet.dev/integrations/squire-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=squire&utm_content=find)
- [Odel](https://odel.app/modules/cotlet/squire)
- [mcpbeat](https://mcpbeat.com/mcp-servers/cotlet/squire/)
- [Step-by-step guide (PDF)](docs/how-to-connect-squire-to-chatgpt-claude-ai-agent.pdf)
- [All apps connected through Cotlet.dev](https://github.com/cotlet-connect)

Cotlet.dev is run by Take Group sp. z o.o., Katowice, Poland. Questions about the Squire tools: contact@cotlet.dev. Squire is a trademark of its owner.

More: https://cotlet.dev/integrations/squire-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=squire

Start free: https://cotlet.dev/app/signup?app=squire&utm_source=github&utm_medium=readme&utm_campaign=squire
