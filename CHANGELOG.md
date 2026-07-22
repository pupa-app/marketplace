# Changelog

All notable changes to the Pupa Marketplace catalog. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Patch-only versions
(`0.0.X`), mirroring the Pupa app convention. Each release is a git tag `v0.0.X`
that clients can pin.

## [0.0.2] — 2026-07-22

### Added

- `myfire` app — personal FIRE planner (profile tracker + calculator).
- `SECURITY.md` (vuln reporting + malicious-app moderation), `CODE_OF_CONDUCT.md`,
  and `.github/ISSUE_TEMPLATE/` (bug report, report-an-app, config).
- `schemas/` — JSON Schemas for `index.json` and `metadata.json`.
- README badges (CI, release, licenses).

### Changed

- Genericized `research-tracker` and `daily-briefing` seed data: removed real
  third-party GitHub handles / repos and internal roadmap references, replaced
  with fictional competitors and reserved `.example` domains. Both bumped to
  `version 2`.

## [0.0.1] — 2026-07-10

### Added

- Initial marketplace scaffolding: `index.json` catalog (`formatVersion` 1),
  per-app `apps/<slug>/` layout, `marketplace.json` identity manifest.
- `scripts/validate.py` — dependency-free validator + deterministic index
  generator.
- Format spec ([docs/spec.md](docs/spec.md)) and self-hosting guide
  ([docs/hosting.md](docs/hosting.md)).
- Seed apps: `research-tracker`, `daily-briefing`.
- Dual licensing: MIT for tooling/docs, CC0 1.0 for contributed app content
  (`CONTENT-LICENSE`), attested via the PR checklist.
