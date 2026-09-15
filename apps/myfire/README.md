# MyFIRE

Personal FIRE (Financial Independence, Retire Early) planning. A profile tracker
of your numbers feeds a calculator that works out savings rate, years to FIRE,
and the five variants.

Install from the [marketplace](https://pupa-app.com/marketplace), or open
`app.pupa` in Pupa.

## What's inside

| Component | Kind | What it holds |
|---|---|---|
| 👤 My FIRE Profile | tracker | Your inputs: current age, target age, income, expenses, portfolio, monthly contribution |
| 🔥 FIRE Calculator | calculator | 39 rows with an inline chart — core stats, savings rate, years to FIRE, and Lean / Regular / Fat / Coast / Barista |

The calculator pulls live values from the Profile through linked-field rows, so
editing a profile number flows straight into every output. No manual sync.

## Using it

Two sample profiles ship with it — *My Plan* (starting at 25) and *Later Start
(age 45)* — so the calculator has something to chew on immediately. Edit one
with your real numbers, or add a row and compare scenarios side by side.

## What it needs

Nothing. No backend tools, no subagents, no network — the calculator runs
entirely on the device.

## Notes for the agent

`AGENTS.md` ships with the bundle and tells the agent to activate the relevant
skill (`get_skill_tracker` / `get_skill_calculator`) before using its tools, and
to use `linkItem` / `unlinkItem` when wiring new tracker rows to calculator rows.
