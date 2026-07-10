# Pupa Marketplace

A catalog of [Pupa](https://github.com/pupa-app/pupa) MyApp bundles (`.pupa`
files) you can browse and install from the app.

A **marketplace** is just an HTTPS URL serving an `index.json` manifest that
points at `.pupa` bundle files — this repo is the official one, and anyone can
host their own (see [docs/hosting.md](docs/hosting.md)). The full format is
specified in [docs/spec.md](docs/spec.md).

## Install an app

- In Pupa: Settings ▸ Marketplace, pick an app, review its agent prompts,
  install.
- Or download an `apps/<slug>/app.pupa` file and open it with Pupa.

## Publish your app

1. In Pupa: Settings ▸ Import & Export ▸ export your MyApp as a `.pupa` file.
2. Fork this repo, add a directory:

   ```
   apps/<your-slug>/
     app.pupa          # your exported bundle
     metadata.json     # see CONTRIBUTING.md
     screenshots/      # optional, ≤5 png/jpg, ≤1 MB each
     README.md         # optional
   ```

3. Run `make validate`, then `make index` to regenerate `index.json`.
4. Open a PR — the template walks you through the checklist.

Full guide: [CONTRIBUTING.md](CONTRIBUTING.md).

## Trust model

Bundles are **inert JSON** — no code executes on import, and the Pupa importer
validates every bundle as untrusted input. But bundles carry **agent prompts**
(`AGENTS.md`, personas) that run with *your* configured tools once installed.
PR review here is a moderation layer, not a guarantee: review an app's prompts
in the install preview before accepting it.

## Layout

- `index.json` — generated catalog manifest. Never hand-edit; regenerate with
  `make index`.
- `marketplace.json` — this marketplace's identity (name, owner, description).
- `apps/<slug>/` — one directory per published app.
- `scripts/validate.py` — dependency-free validator + index generator.
- `docs/spec.md` — the marketplace format spec (host-agnostic).
- `docs/hosting.md` — host your own marketplace.

## Releases

Patch-only versions (`0.0.X`) tracked in [CHANGELOG.md](CHANGELOG.md), tagged
`v0.0.X`. Clients pin a tag (or commit SHA), not `main`:

```
https://raw.githubusercontent.com/pupa-app/marketplace/v0.0.X/index.json
```
