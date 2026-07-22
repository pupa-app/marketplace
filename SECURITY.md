# Security Policy

## What this repo is

This repo is a **catalog** of `.pupa` MyApp bundles. Bundles are inert JSON —
no code runs on import, and the Pupa client validates every bundle as untrusted
input (see the Trust model in [README.md](README.md)). The security surface here
is therefore twofold:

1. **The tooling** (`scripts/validate.py`, CI, `Makefile`) — a normal codebase.
2. **The published content** — bundles carry **agent prompts** (`AGENTS.md`,
   personas) that run with *your* configured tools once installed. A malicious
   bundle is a prompt-injection / social-engineering vector, not a code-exec one.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Report privately via either channel:

- GitHub's [private vulnerability reporting](https://github.com/pupa-app/marketplace/security/advisories/new)
  ("Report a vulnerability" under the repo's **Security** tab), or
- email **pupa-app-help@proton.me**.

We aim to acknowledge within a few days and will coordinate a fix and disclosure
timeline with you.

Please include: the affected file/app slug (or validator behaviour), a
description of the issue and its impact, and steps to reproduce.

## Reporting a malicious or abusive published app

If a **published** app in `apps/` carries harmful agent prompts (prompt
injection, data-exfiltration instructions, deceptive personas, disallowed
content), that is a moderation issue, not a private vulnerability. Open a
[Report an app](https://github.com/pupa-app/marketplace/issues/new?template=report_app.yml)
issue so it can be triaged publicly and pulled quickly.

## Scope notes for reviewers

Findings that weaken any of these properties are in scope for the private
channel:

- **Validator bypass** — a bundle that passes `make validate` but violates the
  spec's integrity rules (path traversal in memory paths, symlinks, oversized
  screenshots, bad magic bytes, tampered `sha256` / `sizeBytes` in `index.json`).
- **Index tampering** — a way to make `index.json` point at content whose hash
  or size does not match the served bundle.
- **Supply-chain** — anything letting a PR land content that the diff does not
  show, or that bypasses the version-bump / CI gates.

Out of scope: the fact that an installed app's prompts can act with the user's
tools — that is by design and surfaced in the install preview.
