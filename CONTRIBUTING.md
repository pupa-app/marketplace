# Contributing

Two audiences: **authors** publishing an app, and **reviewers** (maintainers)
merging PRs. Read your half.

> AI assistants must not merge PRs to this repo. A human maintainer reviews
> every app's agent prompts before it lands.

## Authors — publish an app

### 1. Export from Pupa

Settings ▸ Import & Export ▸ pick the MyApp ▸ export. You get an `app.pupa`
file (inert JSON). Decide the toggles:

- **Include records** — ships your real rows (tracker items, events…). Off =
  the app's structure + agent prompts only. **Sharing is publishing** — if you
  leave records on, everything in them becomes public. Review first.
- **Include memories** — ships your memory files. Off still keeps the `pupa/`
  config subtree (agent + subagent prompts, skills), because that is the app's
  capability, not your private data.

### 2. Add a directory

```
apps/<slug>/
  app.pupa            # the exported bundle, exactly this name
  metadata.json       # required, see below
  README.md           # optional, long description / setup notes
  screenshots/        # optional, ≤5 files, .png/.jpg, ≤1 MB each
```

Bundles are stored as indented JSON so diffs read line by line. The export is
one long line — reformat it once after exporting:

```sh
python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); \
  open(p,"w").write(json.dumps(d,indent=2,ensure_ascii=False)+"\n")' \
  apps/<slug>/app.pupa
```

Re-serialization only: indentation and escape form change (`\/`→`/`,
`\uXXXX`→UTF-8). The parsed bundle is identical.

`<slug>` matches `^[a-z0-9][a-z0-9-]{1,63}$` and is the app's stable id. Pick it
once; renaming it later reads as a different app.

`metadata.json`:

```json
{
  "id": "<slug>",
  "version": 1,
  "author": "<your-github-handle>",
  "summary": "One line, ≤200 chars, honest about what it does.",
  "tags": ["productivity", "research"],
  "homepage": "https://optional-url"
}
```

Only fields the bundle can't state about itself go here. `name` and `icon` are
read from the bundle — you can't override them, so the catalog can't misrepresent
what installs.

### 3. Validate + regenerate the index

```
make validate      # checks your app against all rules
make index         # regenerates index.json (never hand-edit it)
```

Commit both your `apps/<slug>/` directory **and** the regenerated `index.json`.

Sign off every commit — CI enforces [DCO](https://developercertificate.org/):

```
git commit -s
```

The `Signed-off-by` trailer certifies you wrote the change and may submit it
under this repo's license. Missing it fails the `DCO` check; fix with
`git commit --amend -s` and force-push.

### 4. Updating an app you already published

Change `app.pupa`, then **bump `version`** in `metadata.json`. CI rejects a
bundle whose content changed without a version bump — it compares parsed JSON,
so a pure reformat needs no bump. `make index` picks up the new size and
checksum.

### 5. The realism bar

A good app is a real, augmentable starting point — not a feature demo. Aim for:

- Plausible seed data (real-looking names/numbers, no `foo`/lorem), or ship
  with records off.
- A real recurring workflow in the app's `AGENTS.md` "How to use", not a tour.
- Cross-component links so it's one app, not N widgets.
- Honest capability boundaries — say what needs a tool/MCP that may be off.

Full rubric: Pupa's [`docs/templates.md`](https://github.com/pupa-app/pupa/blob/main/docs/templates.md).

### 6. Licensing

By opening a PR you dedicate your app's content (`apps/<slug>/**` — bundle,
metadata, README, screenshots) to the public domain under **CC0 1.0** (see
[CONTENT-LICENSE](CONTENT-LICENSE)) — **unless** you set a `license` in
`metadata.json`. The repo's tooling/docs are MIT (see [LICENSE](LICENSE)). Only
submit content you have the right to release — CC0 does not clear third-party
rights in material you don't own.

**Non-CC0 apps.** If your app embeds third-party content under a license that
forbids CC0 (e.g. a validated questionnaire under CC BY-NC-SA), declare it:

```json
{ "license": "CC-BY-NC-SA-4.0",
  "attribution": "Schema content © NovoPsych, https://novopsych.com — used under their Open Source Licence" }
```

You still attest you have the right to redistribute under that license, that the
whole `apps/<slug>/**` tree complies with it (attribution present, any
ShareAlike/NonCommercial terms honoured), and that any in-app medical/legal
disclaimers it requires are included. Absent `license` ⇒ CC0, as before.

## Reviewers — moderation checklist

The bundle is inert, but it carries **agent prompts that run with the installing
user's tools**. That is the real attack surface. Before merging:

1. **Read every agent prompt.** The PR body must paste every `AGENTS.md` /
   persona in the bundle. Reject prompts that:
   - instruct the agent to exfiltrate data (send memories/records anywhere),
   - contain "ignore previous instructions"-style injection,
   - direct tool abuse (shell, network, deleting/modifying *other* apps' data),
   - impersonate the user or Pupa to extract secrets.
2. **Check for PII** in included records/memories — real emails, tokens, private
   notes. Sharing is publishing.
3. **Check summary honesty** — does it match what the app actually does.
4. **Check licensing** — if `metadata.json` declares a non-CC0 `license`, confirm
   the required `attribution` is present in-bundle and the terms are honoured
   (e.g. NonCommercial/ShareAlike). If it embeds a clinical/legal instrument,
   confirm an in-app disclaimer. Reject copyrighted third-party content shipped
   as CC0.
5. **Confirm `make validate` passes** and `index.json` is current (CI runs this;
   re-run locally if Actions is billing-blocked — see below).
6. **Update PRs:** confirm `version` bumped.

### CI may be billing-blocked

The org's GitHub Actions is sometimes unavailable. The real gate is:

- the author's "I ran `make validate`" PR checkbox, and
- a maintainer re-running `make check-pr BASE=origin/main` locally before merge.

Never merge on a green-looking-but-skipped check alone.
