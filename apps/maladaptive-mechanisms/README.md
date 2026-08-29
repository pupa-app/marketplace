# Maladaptive Mechanisms

A schema-therapy self-tracker built on the openly-licensed **MSS-YSQ**: a 76-item
questionnaire, live scores for 19 schemas, domain charts, and a schema/mode diary.

Install from the [marketplace](https://pupa-app.com/marketplace), or open
`app.pupa` in Pupa.

## Not medical advice

This is a **self-reflection tool** — not a diagnostic instrument, not a medical
device, and not a substitute for assessment or treatment by a qualified
mental-health professional. Scores are self-report snapshots. A high score is a
prompt for reflection, not a diagnosis. Nothing here creates a therapeutic
relationship.

**If you are in distress or thinking about harming yourself, contact a crisis
line now.** US: call or text **988**. UK/ROI: **Samaritans 116 123**. Elsewhere:
<https://findahelpline.com>.

The full text ships with the bundle at `pupa/DISCLAIMER.md`.

## What's inside

| Component | Kind | What it holds |
|---|---|---|
| MSS-YSQ Items | tracker (kanban by schema) | The 76 questionnaire items and your 0–4 responses |
| Schema Scores | calculator | 24 rows scoring 19 schemas by mean response |
| Disconnection & Rejection | bar chart | Domain scores |
| Impaired Autonomy & Performance | bar chart | Domain scores |
| Impaired Limits & Other-Directedness | bar chart | Domain scores |
| Overvigilance & Inhibition | bar chart | Domain scores |
| Schema Work Exercises | checklist | 25 follow-up exercises |
| Schema Origins & Links | tracker | Where a schema came from — childhood memory, caregiver role, present-day trigger |
| Schema Diary & Mode Mapping | tracker (grouped by schema) | Dated entries: trigger, mode, coping style, emotions, healthier response |

Scores and charts resolve live from your questionnaire responses.

## Using it

Three skills ship with the app:

- **`/complete-questionnaire`** — walks the 76 items in batches with one-tap 0–4
  answers. Resumable; you don't have to finish in one sitting.
- **`/mentor-me`** — reads your current state plus the interpretation guide and
  suggests a tailored next step.
- **`/add-diary-entry`** — logs a schema/mode diary entry.

The agent grounds its replies in `pupa/research/mss-ysq-interpretation-guide.md`
(scoring bands, domains, follow-up exercises, caveats) and is instructed to frame
everything as self-understanding, never diagnosis.

## What it needs

Nothing — no backend tools, no network. Your responses and diary stay on device.

## Licence and attribution

The questionnaire items, the
19-schema structure, and the scoring method are the **Maladaptive Schema Scale –
Young Schema Aligned (MSS-YSQ)**, © **NovoPsych Pty Ltd**, used under NovoPsych's
Open Source Licence (modelled on CC BY-NC-SA). So the app as a whole is
distributed under **CC BY-NC-SA 4.0**.

That carries the conditions:

- **Attribution** — [MSS-YSQ © NovoPsych](https://novopsych.com/assessments/formulation/mss-ysq-young-schema-questionnaire/).
- **NonCommercial** — don't sell this app or the instrument, or bundle it into a
  paid product, without a separate licence from NovoPsych.
- **ShareAlike** — redistribute only under the same terms, carrying the notice.
- **Integration cap** — NovoPsych's licence limits software integration to ≤100
  users (or ≤1,000 administrations) per calendar year. Beyond that, get a
  separate licence.

Keep `pupa/LICENSE-NOTICE.md` with the bundle if you redistribute it.

Citation: Buchanan, B., Bartholomew, E., Smyth, C., & Hegarty, D. (2025). *The
Maladaptive Schema Scale (MSS).* Assessment. <https://osf.io/c3upr/>
