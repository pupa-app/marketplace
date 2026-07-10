# Changelog

All notable changes to the Pupa Marketplace catalog. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Patch-only versions
(`0.0.X`), mirroring the Pupa app convention. Each release is a git tag `v0.0.X`
that clients can pin.

## [0.0.1] — unreleased

### Added

- Initial marketplace scaffolding: `index.json` catalog (`formatVersion` 1),
  per-app `apps/<slug>/` layout, `marketplace.json` identity manifest.
- `scripts/validate.py` — dependency-free validator + deterministic index
  generator.
- Format spec ([docs/spec.md](docs/spec.md)) and self-hosting guide
  ([docs/hosting.md](docs/hosting.md)).
- Seed apps: `research-tracker`, `daily-briefing`.
