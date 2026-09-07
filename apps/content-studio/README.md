# Content Studio

A content pipeline for one person publishing on a schedule — written posts
and short video, on one board.

## What's in it

- **Content Pipeline** (tracker) — kanban by stage. `type` picks the path:
  `Written` runs Idea → Research → Draft → Review → Scheduled → Published;
  `Video` adds Footage, Voiceover and Assemble.
- **Publish Checklist** — reusable pre-publish gate. Reset between pieces.
- **Publishing Calendar** — publish slots and planning sessions. The publish
  slot is linked to its pipeline card, so you can jump calendar → card.
- **Studio Room** (slack) — `@Researcher` (facts, data, sources),
  `@Editor` (hook, structure, CTA), `@Ideator` (angles and formats),
  `@Scriptwriter` (reel scripts), `@Producer` (pacing, captions, the edit).

## The video path

Drag a `type=Video` card across the board and each stage fires a skill —
`project-kickoff` → footage → `generate-audio` → `build-video` →
`review-reel` → `publish-video` — while `project-checklist` keeps a
per-project "▶ &lt;title&gt;" checklist in sync and `pipeline-handover` passes
notes between stages (each runs in its own thread). Every rule ships with
`confirm: true`: the app proposes, you tap Start.

## Requirements — read before installing

The written pipeline works out of the box. **The video path does not.** It
needs a self-hosted backend on your own Mac with the `shell` tool enabled —
`shell` is off in the cloud image, so video builds cannot run there.

Run `/setup` once. It walks you through:

- **ffmpeg**, ideally a libass build for karaoke captions (`.srt` captions
  are the fallback if not).
- **A voiceover provider** — the skills are written against an ElevenLabs
  MCP; the API key stays an env placeholder and is never bundled. No key?
  macOS `say` works as a placeholder voice.
- **A projects folder** — one parent folder for media, ideally cloud-synced.
  `/setup` suggests candidates and asks you to confirm; it never picks one
  silently. The path is saved to `pupa/PROJECTS_DIR.md` in the app's memory.
- **Optionally `tavily_search`** for `@Researcher` to pull live data. Without
  it the agent still works, from its own knowledge.

## Seed data

This bundle ships records (`includedRecords: true`): three written cards,
two calendar events, and a two-message exchange in the Studio Room. They
are generic demo rows — no host paths, credentials, private notes, or
unpublished work. The `Video` card is a seed added for this release.

Nothing here is configured for you: set your own brand voice, voice id,
and projects folder at `/setup`.
