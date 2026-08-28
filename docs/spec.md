# Pupa Marketplace format (v1)

This spec defines the marketplace format **independently of any one repo**, so
anyone can host their own marketplace of Pupa MyApp bundles. It is modelled on
the "a marketplace is just a URL" idea from plugin ecosystems: a client is
pointed at a base URL, reads a well-known manifest, and installs bundles it
references.

Keywords MUST / SHOULD / MAY per RFC 2119.

## 1. Definitions

- **Marketplace** — an HTTPS base URL that serves an `index.json` manifest at
  its root. Everything else (bundle files, screenshots) is referenced by a
  relative `path` resolved against that base URL.
- **Bundle** — a `.pupa` file: an inert, self-contained MyApp artifact
  (see §3).
- **Client** — the Pupa app (or any consumer) reading the manifest and
  installing bundles.

The base URL is the only integration point. A GitHub repo served over
`raw.githubusercontent.com` is one host; an S3 bucket or any static file server
works identically.

## 2. `index.json` manifest

Top-level object:

| Field | Type | Req | Meaning |
|---|---|---|---|
| `formatVersion` | int | ✓ | Manifest schema version. This spec is `1`. |
| `name` | string | ✓ | Display name of the marketplace. |
| `owner` | string | ✓ | Who runs it (handle/org). |
| `description` | string | ✓ | One-line description. |
| `entries` | array | ✓ | The apps, sorted by `metadata.order` (default 0) then `id`. |

Each entry:

| Field | Type | Req | Meaning |
|---|---|---|---|
| `id` | string | ✓ | Stable app id, slug `^[a-z0-9][a-z0-9-]{1,63}$`. |
| `name` | string | ✓ | Display name (from the bundle). |
| `icon` | string | ✓ | SF Symbol name (from the bundle). |
| `author` | string | ✓ | Contributor handle. |
| `summary` | string | ✓ | ≤200 chars. |
| `tags` | [string] | ✓ | ≤8 lowercase-kebab tags. |
| `version` | int | ✓ | Entry version; bumped on any bundle change. |
| `appFormatVersion` | int | ✓ | Bundle schema version. Client greys out entries newer than it supports. |
| `appVersion` | string | ✓ | Pupa version that exported the bundle (compat soft-signal). |
| `includedRecords` | bool | ✓ | Bundle ships sample rows. |
| `includedMemories` | bool | ✓ | Bundle ships memory files. |
| `exportedAt` | string | ✓ | ISO-8601 export timestamp (from the bundle header). |
| `path` | string | ✓ | Relative path to the `.pupa`, resolved against the base URL. |
| `sizeBytes` | int | ✓ | Exact byte length of the bundle. |
| `sha256` | string | ✓ | Lowercase-hex SHA-256 of the exact bundle bytes. |
| `screenshots` | [string] | ✓ | Relative image paths (possibly empty). |
| `homepage` | string | — | Optional author URL. |

### Evolution rules

- Clients MUST **hard-reject** a manifest whose `formatVersion` exceeds the
  version they support (fail closed — do not install from a manifest you can't
  fully understand).
- Clients MUST **ignore unknown fields**. New optional fields are additive and
  MUST NOT bump `formatVersion`.
- `id` is the stable identity. Renaming it is a new app, not an update.

## 3. Bundle format (`.pupa`)

A `.pupa` is the Pupa app's `MyAppBundle`: pretty-printed, sorted-key,
ISO-8601-dated JSON. Load-bearing invariants:

- `header.format` MUST equal `pupa.myapp.bundle`. (`pupa.library.bundle`
  multi-app containers are **not** valid catalog entries — a marketplace *is*
  the container; submit apps individually.)
- `header.formatVersion` is the bundle schema version.
- The bundle is **inert**: pure data, no executable content. All rebuild logic
  lives in the client, dispatched by component `kind`.

Full bundle spec + threat model: Pupa
[`docs/marketplace.md`](https://github.com/pupa-app/pupa/blob/main/docs/marketplace.md).

Hosts MUST NOT alter bundle bytes — `sha256`/`sizeBytes` cover the exact bytes a
client will verify.

## 4. Integrity requirements (client)

A conforming client MUST:

1. Fetch only over **HTTPS**.
2. Reject an entry before download if `sizeBytes` exceeds its import cap.
3. Enforce a maximum byte length while/after downloading (defence against a lying
   `sizeBytes`).
4. Verify the downloaded bytes' SHA-256 equals `entry.sha256` **before** import.
5. SHOULD pin an **immutable ref** (git tag or commit SHA), not a moving branch,
   when the host is a git forge — so the catalog can't change under a pinned
   client.

## 5. Security model

**The client is the security boundary.** A marketplace is only a byte source.
The Pupa importer treats every bundle as untrusted: size + count caps, a settings
allow-list, memory-path traversal guards, fresh ids, slug-collision-safe renames.
A malicious manifest or bundle cannot widen those.

The one risk the transport can't neutralise: a bundle carries **agent prompts**
(`AGENTS.md`, personas) that run with the *installing user's* tools once
accepted. Therefore:

- Hosts SHOULD moderate — review each bundle's prompts before publishing
  (in this repo, PR review is that moderation).
- Clients SHOULD surface the prompts to the user before install.
- A future revision MAY add an optional top-level `signature` field (additive,
  no `formatVersion` bump) for signed manifests.

## 6. Layout convention (informative)

Only `index.json` and reachable `path`s are normative — a host MAY lay out files
however it likes. This repo uses, and its validator enforces:

```
index.json
marketplace.json          # name/owner/description → copied into index
apps/<slug>/
  app.pupa
  metadata.json           # author-supplied fields not derivable from the bundle
  screenshots/*.png|jpg
  README.md
```

`name`/`icon` in the manifest are derived from the **bundle**, not from
author-supplied metadata, so a catalog entry cannot misrepresent what installs.

## 7. Large bundles (informative)

Bundles live in the host's storage (git history, for a repo host) indefinitely,
so this repo caps published bundles well under the client import ceiling and does
not use Git LFS (bandwidth quotas break popular installs). A future revision MAY
let `path` be an absolute HTTPS URL (Release asset / object store / backend) for
large bundles — additive, no `formatVersion` bump.
