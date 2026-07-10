# Host your own Pupa marketplace

A marketplace is just an HTTPS URL serving an `index.json`. You can run your own
— for a company's internal apps, a themed collection, or your personal apps —
without asking anyone. Pupa can add any HTTPS base URL as a source.

## Quickest path: copy this repo

1. Fork or copy this repo's skeleton: `marketplace.json`, `scripts/validate.py`,
   `Makefile`, `apps/`, `.github/`.
2. Edit `marketplace.json` with your identity:

   ```json
   { "name": "Acme Internal Apps", "owner": "acme", "description": "…" }
   ```

3. Add apps under `apps/<slug>/` (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
4. `make validate && make index` — commit the regenerated `index.json`.
5. Tag a release (`git tag v0.0.1 && git push --tags`) so clients can pin it.

## The URL clients use

For a GitHub repo served raw, the base URL is:

```
https://raw.githubusercontent.com/<owner>/<repo>/<ref>/
```

and the manifest is that base + `index.json`. **Pin `<ref>` to a tag or commit
SHA**, not `main`, so the catalog can't shift under installed clients:

```
https://raw.githubusercontent.com/acme/marketplace/v0.0.1/index.json
```

Any static host works too — S3, GitHub Pages, a plain web server — as long as
`index.json` and every entry's `path` are reachable over HTTPS. Only the format
(§2 of [spec.md](spec.md)) is normative; the `apps/<slug>/` layout is this repo's
convention, not a requirement.

## Add your marketplace in Pupa

Settings ▸ Marketplace ▸ add source ▸ paste your pinned `index.json` URL.
Your `marketplace.json` `name`/`owner`/`description` is what users see labelling
the source.

## You are the moderator

Bundles are inert, but they carry agent prompts that run with the installing
user's tools. If you accept contributions, review every app's prompts before
publishing — that is the real safety layer (see spec §5). `make validate` checks
structure and caps; it cannot judge intent.
