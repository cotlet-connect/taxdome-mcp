---
name: squire-cotlet
description: Connect Squire to Claude Code, ChatGPT and any AI agent through Cotlet.dev, so the agent can read barbers' schedules, work the waitlist, book, move and cancel appointments, block time off and read revenue in your own signed-in Squire account.
---

# Squire through Cotlet.dev

## What it does

Cotlet.dev runs 11 Squire tools hosted, in your own Squire account, signed in to Commander as you in its Cotlet Cloud Browser. Unofficial, not affiliated with Squire.

## Setup

1. Make a Cotlet account, open Squire in its Cloud Browser, log in to Commander with your own shop login and press Enable for agents.
2. Add the MCP server `https://cotlet.dev/mcp/v1` and send your Cotlet API key as a Bearer token in the `Authorization` header.

## Working rules

- Start with `list_barbers` and `list_services`: their ids feed every booking tool.
- Bookings, moves and cancellations wait for the user's OK in the Cotlet console.
- `block_time` does not clear bookings already in its window: call `list_appointments` first.
- When a whole day moves, go one booking at a time, so each client hears about a single change.
- Return client phone and email only when the user asks for them.

More: https://cotlet.dev/integrations/squire-api-mcp-server?utm_source=clawhub&utm_medium=skill&utm_campaign=squire
