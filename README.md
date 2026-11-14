# How to connect TaxDome to ChatGPT, Claude and any AI agent

**Let your AI agent run the chair schedule.** Cotlet.dev connects your own signed-in TaxDome account to ChatGPT, Claude and any AI agent over MCP, and to n8n, Make and scripts over REST: jobs, accountings, clients, waitlist and reports for your accounting firm.

Unofficial: Cotlet is independent and **not affiliated with TaxDome**.

## What you can ask

> Brief each accounting's day at 7 am: every booking with client, services, start and end.

> Book waitlist clients into the gaps in tomorrow's schedule, after I approve each booking.

> Marcus is out sick today. Move his bookings to another accounting with the same time open and the same services.

> Block Dev's calendar on Friday from 1 pm to 5 pm for time off.

> Show Monday revenue by accounting for last week.

> Find clients who have not come in for 60 days.

## Connect in 2 minutes

1. **Log in to Commander yourself.** Make a Cotlet account at [cotlet.dev](https://cotlet.dev/app/signup?app=taxdome&utm_source=github&utm_medium=readme&utm_campaign=taxdome), open TaxDome in its Cloud Browser, log in to Commander with your own shop login, then press Enable for agents.
2. **Add the Cotlet address.** Paste `https://cotlet.dev/mcp/v1` into your agent as an MCP server or connector.
3. **Approve the connection.** Chat apps send you to a Cotlet sign-in. Code editors, n8n and scripts take an API key from the console.

TaxDome shares one address, `https://cotlet.dev/mcp/v1`, with every other app on your Cotlet account. If you enable TaxDome after connecting the agent, refresh the connector so the TaxDome tools appear. Free 7-day trial with 2,000 credits, no card needed.

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

- n8n: MCP Client Tool inside an AI Agent, Transport HTTP Streamable, URL `https://cotlet.dev/mcp/v1`, Auth Bearer with your Cotlet key, tool `taxdome_read`.
- Make: MCP Client > Call a tool. Zapier: MCP Client by Zapier > Run Tool. Server URL `https://cotlet.dev/mcp/v1`, your Cotlet key as the token, tool `taxdome_write`.

## TaxDome REST API

Create a Cotlet API key with access to TaxDome and store it as `COTLET_API_KEY` in your environment or your automation platform's credential store, outside shared workflow exports.

```bash
curl https://cotlet.dev/api/v1/taxdome/accountings \
  -H "Authorization: Bearer $COTLET_API_KEY"
```

A successful call puts the tool output in `result`. MCP and REST carry the same 14 tools, inputs and answers, with one API key and one price. Agents use MCP; scripts, sheets and HTTP steps in n8n, Make or Zapier use REST at `https://cotlet.dev/api/v1/taxdome`.

## TaxDome tools through Cotlet.dev

6 read, 5 write. Over MCP each tool is an operation of `taxdome_read` or `taxdome_write`.

| Tool | What it does | Access | REST endpoint |
|---|---|---|---|
| `list_accountings` | List the accountings on your shop's team | read | `GET /api/v1/taxdome/accountings` |
| `list_services` | List the services on your shop's service menu | read | `GET /api/v1/taxdome/services` |
| `list_jobs` | List jobs for a day or a date range, optionally for one accounting | read | `GET /api/v1/taxdome/jobs` |
| `create_job` | Book an job for a client with a accounting | write, asks first | `POST /api/v1/taxdome/clients/{client_id}/jobs` |
| `reschedule_job` | Move an job to a new time or another accounting | write, asks first | `POST /api/v1/taxdome/jobs/{job_id}/reschedule` |
| `cancel_job` | Cancel a client's job | write, asks first | `POST /api/v1/taxdome/jobs/{job_id}/cancel` |
| `block_time` | Block a accounting's calendar for a time window | write | `POST /api/v1/taxdome/accountings/{accounting_id}/time/block` |
| `remove_block` | Remove a blocked time window from a accounting's calendar | write | `DELETE /api/v1/taxdome/blocks/{block_id}` |
| `list_waitlist` | List clients on the shop's waitlist | read | `GET /api/v1/taxdome/waitlists` |
| `list_clients` | List or search your shop's clients | read | `GET /api/v1/taxdome/clients` |
| `get_revenue_report` | Read revenue and client retention from the Reporting Dashboard for a date range | read | `GET /api/v1/taxdome/revenue-report` |

Times are in the shop's time zone. A slot that is booked or blocked fails with `SLOT_TAKEN` and nothing changes. TaxDome lists the Wait List under its PRO plan; on other plans the list comes back empty. Phone and email come back only when you ask for them. Revenue is in the shop's currency.

## Approvals and undo

Nothing reaches a client before you approve. 3 of the 5 write tools ask first: `create_job`, `reschedule_job` and `cancel_job` wait in your Cotlet console. `block_time` and `remove_block` run at once, because a block reaches no client and undoes in one call. Reads run at once too. For a scheduled run you can switch the wait off per tool.

| Action | Undo |
|---|---|
| Book an job | Cancel it; TaxDome may already have sent the confirmation |
| Reschedule an job | Move it back; the client may hear about both changes |
| Cancel an job | Book it again; a no-show or late fee is never charged by a tool |
| Block time | Remove the block |
| Remove a block | Block the window again |

A block does not clear the bookings already in its window. Ask the agent to list them first. When a whole day moves, let the agent go one booking at a time, so each client hears about a single change.

## Run it locally (stdio)

This repository is a small MCP server for clients that only start local processes. It speaks MCP over stdio, lists the 14 TaxDome tools without any key, and forwards every tool call to the hosted Cotlet.dev server as `taxdome_read` or `taxdome_write`. The hosted URL above stays the recommended setup. Python 3.10+, no dependencies.

```bash
# COTLET_API_KEY holds your Cotlet API key
claude mcp add taxdome -e COTLET_API_KEY="$COTLET_API_KEY" -- \
  uvx --from git+https://github.com/cotlet-connect/taxdome-mcp taxdome-mcp
```

`mcp.json` in this repository has the same server for clients that read a JSON config. Or with Docker:

```bash
docker build -t taxdome-mcp .
docker run -i --rm -e COTLET_API_KEY taxdome-mcp
```

Without `COTLET_API_KEY` a tool call answers with where to create a key.

## Command line

```bash
python3 taxdome_agent.py connect                     # hosted setup for Claude Code, Cursor, Codex and chat apps
python3 taxdome_agent.py tools                       # the 14 TaxDome tools
python3 taxdome_agent.py call list_accountings           # run one tool through Cotlet.dev
python3 taxdome_agent.py call list_jobs '{"date_from": "2026-11-16"}'
python3 taxdome_agent.py serve                       # stdio MCP server (same as no argument)
```

## Does TaxDome have an API or MCP server?

No. TaxDome has no MCP server, no public API and no developer docs (checked 28 Oct 2026). Zapier, n8n and Pipedream have no TaxDome app, and clients can be exported by hand from Commander only as a snapshot. On GitHub, repos named taxdome-mcp are coding tools of the same name, not servers for TaxDome accounting firms. Cotlet runs 14 TaxDome tools hosted, over MCP for agents and REST for scripts.

## Privacy and access

- **What Cotlet stores:** your logged-in Commander profile, AES-256-GCM encrypted, in Finland. Never the password.
- **What your agent gets:** 14 TaxDome tools. No cookie, no login.
- **What the session sees:** what your Commander login sees: the whole shop for an owner, one chair for a accounting.
- **What no tool touches:** checkout, cards on file, tips, deposits, booth rent and payouts.
- **If TaxDome asks for a code:** you type it in yourself.
- **How to cut access:** disable for agents, reset the browser or delete the key. The next call fails.

Client phone numbers and emails sit in the same Commander login, so give the agent a TaxDome user that sees only what it needs. Read TaxDome's terms in your own browser and look for rules on bots, automated access and shared logins before you connect.

## Price

10 credits per successful call, MCP or REST, and 50 credits a day for the Cloud Browser. One price for every accounting in the shop. Only successful calls use credits; failed calls and timeouts cost nothing. Credit packs start at 5,000 credits for $29. Your TaxDome plan is billed by TaxDome as before. [Full pricing](https://cotlet.dev/pricing?utm_source=github&utm_medium=readme&utm_campaign=taxdome)

## Questions from TaxDome users

**How do I connect TaxDome to ChatGPT or Claude?**

Sign up at cotlet.dev, log in to TaxDome once in its Cloud Browser and add Cotlet to ChatGPT or Claude, following the steps in your console. No API key is needed. ChatGPT and Claude then work in your TaxDome account through Cotlet, in their phone apps too.

**Which TaxDome plan do I need?**

Cotlet works in your own TaxDome account, so it can only do what your plan shows in Commander. TaxDome's pricing page lists the waitlist and multiple accounting accounts under its PRO plan and the Reporting Dashboard from the first plan (checked 28 Oct 2026).

**Can it take payments or issue refunds?**

No. Payments, payouts, rent collection and card processing stay in TaxDome. The tools book, move and cancel jobs and read reports.

**Does it work for an independent accounting?**

Yes. TaxDome has accounts for independent accountings, and the tools then see your own chair: your bookings, blocks, clients and revenue.

**Can I use the TaxDome API without an AI agent?**

Yes. Call Cotlet's REST API from a script or an HTTP step in n8n, Make or Zapier with your Cotlet key.

## Find it on

- [TaxDome on Cotlet.dev](https://cotlet.dev/integrations/taxdome-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=taxdome&utm_content=find)
- [Odel](https://odel.app/modules/cotlet/taxdome)
- [mcpbeat](https://mcpbeat.com/mcp-servers/cotlet/taxdome/)
- [Step-by-step guide (PDF)](docs/how-to-connect-taxdome-to-chatgpt-claude-ai-agent.pdf)
- [All apps connected through Cotlet.dev](https://github.com/cotlet-connect)

Cotlet.dev is run by Take Group sp. z o.o., Katowice, Poland. Questions about the TaxDome tools: contact@cotlet.dev. TaxDome is a trademark of its owner.

More: https://cotlet.dev/integrations/taxdome-api-mcp-server?utm_source=github&utm_medium=readme&utm_campaign=taxdome

Start free: https://cotlet.dev/app/signup?app=taxdome&utm_source=github&utm_medium=readme&utm_campaign=taxdome
