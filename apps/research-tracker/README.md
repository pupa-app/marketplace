# Research Tracker

A competitive-intelligence workspace. Run a weekly sweep with the research
agents, append findings, and watch the signal trend move. Ships seeded with
Pupa's own companion-app landscape as real intel.

Install from the [marketplace](https://pupa-app.com/marketplace), or open
`app.pupa` in Pupa.

## What's inside

| Component | Kind | What it holds |
|---|---|---|
| Watchlist | tracker (kanban) | 5 rival apps grouped by threat — Us / Watch / Rising / Direct |
| Findings Log | tracker | 7 dated rows of evidence, tagged by sweep week and signal strength |
| Signal Trend | line chart | Findings per sweep, with a strong-only overlay |
| Deltas | calculator | Signal counts + week-over-week change in strong signals |
| Research Room | slack | `#research`, staffed by three subagents |

Findings link back to the Watchlist row they're about, so the chart and Deltas
resolve live.

## The agents

Three personas ship in `pupa/agents/`, and their prompts are shown for review on
import:

- **@Scout** — finds sources.
- **@Analyst** — scores finds and logs them.
- **@Digest** — writes the weekly summary.

## The weekly sweep

1. Open Research Room and ask `@Scout` what's new for the Watchlist apps.
2. `@Analyst` scores each find and appends it to the Findings Log, linked to its
   Watchlist row.
3. Check Signal Trend and Deltas — is any competitor's strong signal rising?
4. Ask `@Digest` for the "what's new since last week" summary; it saves to
   `research-tracker/digests/`.
5. Update Watchlist threat levels if a rival's position changed.

## What it needs

`@Scout` needs a search, RSS, or web-fetch tool configured on your backend. The
rest of the workspace works without one — you just have to add findings by hand.

## Making it yours

The Watchlist is seeded with our real landscape; replace it with the competitors
in your space and the whole workspace retargets. The agents maintain `MEMORY.md`
(which sources pay off) and `USER.md` (the niches you care about), and write a
`skills/weekly-sweep.md` once the source list and scoring rubric settle.
