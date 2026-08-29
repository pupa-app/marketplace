# Daily Briefing

A morning-briefing workspace. The agent pulls a handful of feeds, writes a tight
brief, and pushes it at 7am.

Install from the [marketplace](https://pupa-app.com/marketplace), or open
`app.pupa` in Pupa.

## What's inside

| Component | Kind | What it holds |
|---|---|---|
| Briefing Sources | tracker | 6 feeds, each naming the tool it needs and whether it's On |
| Today's Briefing | tracker | One card per section, kept under ~500 words total |
| Briefing History | tracker | Per-day feed volume + whether the focus item got done |
| Feed Volume | bar chart | The week's volume, live from Briefing History |
| Schedule | calendar | The recurring 7am push + a sample day |

Ships with sample rows and the agent prompt (`pupa/AGENTS.md`). No subagents.

## The morning loop

1. For each **On** source, pull fresh data with its named tool. Skip a source
   whose tool is missing.
2. Rewrite the Today's Briefing rows — lead with `Now` items, link each section
   back to its source.
3. Append a Briefing History row so the Feed Volume chart updates.
4. Send the brief as a notification. To automate it, ask *"send my briefing
   every morning at 7"* and the agent schedules a daily `sendNotification`.

## What it needs

Sources are a capability contract — each works only if its tool is configured on
your backend:

| Source | Tool | Ships |
|---|---|---|
| Weather | weather MCP (forecast) | On |
| Calendar | calendar MCP / EventKit | On |
| Hacker News (AI) | tavily_search / HN API | On |
| GitHub notifications | github MCP | On |
| Newsletters (RSS) | rss tool | On |
| Markets | markets MCP (quotes) | **Off** — no markets MCP is assumed |

If a tool fails, the agent is told to mark that source's `last_pulled` and note
the gap in the brief rather than invent data.

## Making it yours

Replace the sources with your own feeds. The agent maintains `MEMORY.md` (which
sources are noisy vs. useful) and `USER.md` (which sections you actually read,
your preferred tone and length) at the app's memory root, and writes a
`skills/morning-brief.md` once it learns the order and length that land well.
