<!-- New app or app update. Fill every box — reviewers gate on these. -->

## App

- **Slug:** `apps/<slug>/`
- **New app** or **Update** (if update, old → new `version`):

## Agent prompts (required — this is the moderation surface)

Paste **every** `AGENTS.md` and agent/persona prompt contained in the bundle,
verbatim, so reviewers can read them without unpacking the JSON. Bundles are
inert, but these prompts run with the installing user's tools.

```
<paste all agent prompts here>
```

## Checklist

- [ ] I exported this from Pupa and it re-imports cleanly on my device.
- [ ] I ran `make validate` locally and it passed.
- [ ] I ran `make index` and committed the regenerated `index.json`.
- [ ] I pasted every agent prompt above.
- [ ] No personal data: I reviewed the included records/memories ("sharing is
      publishing").
- [ ] Update only: I bumped `version` in `metadata.json`.
