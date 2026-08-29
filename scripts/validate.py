#!/usr/bin/env python3
"""Validate the Pupa marketplace catalog and (re)generate index.json.

Dependency-free (python3 stdlib only) so contributors and any third-party
marketplace can run it with zero setup, and CI is a thin wrapper.

The Pupa app's importer (`MyAppImporter`) is the authoritative security
boundary — it re-validates every bundle as untrusted input. This script is a
courtesy pre-check plus the deterministic index generator: it catches problems
at PR time instead of at install time. The caps below mirror `MyAppImporter`;
keep them in sync (see the CAP table).

Usage:
  validate.py --check [--base <git-ref>]   validate; verify index is current;
                                           with --base, require a version bump
                                           on any changed app.pupa
  validate.py --write                      regenerate index.json
  validate.py --new-app <slug>             scaffold apps/<slug>/
  validate.py --self-test                  run built-in negative-path tests
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APPS = REPO / "apps"
INDEX = REPO / "index.json"
MARKETPLACE = REPO / "marketplace.json"

# ── Format constants (must track the Pupa app) ──────────────────────────────
CATALOG_FORMAT_VERSION = 1
BUNDLE_MAGIC = "pupa.myapp.bundle"          # MyAppBundle.formatMagic
SUPPORTED_BUNDLE_FORMAT = 1                  # MyAppBundle.currentFormatVersion
LIBRARY_MAGIC = "pupa.library.bundle"       # rejected: a marketplace *is* the library

# ── Publish policy vs MyAppImporter safety caps ─────────────────────────────
# Publish caps are marketplace policy (git-history hygiene), stricter than the
# app's import ceiling. The rest mirror MyAppImporter.swift:13-20.
PUBLISH_HARD_BYTES = 20 * 1024 * 1024       # policy: hard reject
PUBLISH_WARN_BYTES = 10 * 1024 * 1024       # policy: warn
MAX_COMPONENTS = 64                          # MyAppImporter.maxComponents
MAX_ITEMS_PER_COMPONENT = 5_000              # maxItemsPerComponent / maxSlackMessagesPerChannel
MAX_MEMORY_FILES = 2_000                     # maxMemoryFiles
MAX_MEMORY_FILE_BYTES = 1 * 1024 * 1024      # maxMemoryFileBytes

# Decode-shape mirrors: the Pupa client decodes bundles with strict Swift
# `Codable`, which rejects things valid JSON can't express. These two bit us in
# practice, so pre-check them at PR time (keep in sync with the client models):
#   • record ids in these collections are typed `UUID`
#     (TrackerItem/CalcRow/ChartSeriesSpec/CalendarEvent/ChecklistItem .id).
#   • calculator/chart `reduce` is the `CalcReduce` enum.
# Slack ids (channel/message) are plain strings and live under other keys, so
# they are intentionally out of scope here.
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
CALC_REDUCERS = {"sum", "avg", "min", "max", "count"}
UUID_ID_LIST_KEYS = {"items", "rows", "events", "series"}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
TAG_RE = re.compile(r"^[a-z0-9-]+$")
APPVERSION_RE = re.compile(r"^\d+(\.\d+)*$")
MEMORY_EXTS = {".md", ".json"}
# A myapp's declarative automations ride the bundle at this memory path
# (Pupa: MemoryStore.pupaAutomationsPath). Each rule's `confirm` flag gates the
# confirm bubble — default true (propose, wait for the user); false auto-fires
# the reaction with the installing user's tools. See validate_automations.
PUPA_AUTOMATIONS_PATH = "pupa/automations.json"
SCREENSHOT_EXTS = {".png", ".jpg", ".jpeg"}
MAX_SCREENSHOTS = 5
MAX_SCREENSHOT_BYTES = 1 * 1024 * 1024
ALLOWED_APP_FILES = {"app.pupa", "metadata.json", "README.md", "screenshots"}
ALLOWED_ROOT = {
    "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE", "CONTENT-LICENSE",
    "SECURITY.md", "CODE_OF_CONDUCT.md", "Makefile", "marketplace.json",
    "index.json", "scripts", "schemas", "docs", "apps",
    ".github", ".git", ".gitignore",
}
IMAGE_MAGIC = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpg"}


class AppError(Exception):
    """A fatal, per-app validation failure."""


def _count_listy(node, key_names):
    """Recursively sum lengths of lists stored under any of key_names."""
    total = 0
    if isinstance(node, dict):
        for k, v in node.items():
            if k in key_names and isinstance(v, list):
                total = max(total, len(v))
            total = max(total, _count_listy(v, key_names))
    elif isinstance(node, list):
        for v in node:
            total = max(total, _count_listy(v, key_names))
    return total


def _bad_memory_path(p):
    """Return a reason string if a memory path is unsafe, else None.

    Mirrors MemoryStore.resolve: relative, no traversal, .md/.json only.
    """
    if not isinstance(p, str) or not p:
        return "empty or non-string path"
    if p.startswith("/") or (len(p) > 1 and p[1] == ":"):
        return "absolute path"
    if "\\" in p:
        return "backslash in path"
    if any(c in p for c in "\x00\r\n"):
        return "control character in path"
    parts = p.split("/")
    if ".." in parts or "" in parts:  # no `..`, no empty segments (incl. leading/trailing)
        return "path traversal"
    ext = "." + p.rsplit(".", 1)[-1] if "." in parts[-1] else ""
    if ext not in MEMORY_EXTS:
        return "extension not .md/.json"
    return None


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_automations(memories):
    """Reject a bundle whose automations skip user validation.

    A myapp can ride declarative automation rules at `pupa/automations.json`:

        {"automations": {"<event>": [ {"id", "matcher", "action", "confirm"} ]}}

    Each rule's `confirm` flag is the confirm-bubble gate. It defaults to true
    (propose the reaction, wait for the user to tap Start); `confirm: false`
    routes the reaction to auto-fire — it runs with the *installing* user's
    tools without asking (Pupa: RuleEngine `pendingAutoFire`, AutomationRule
    `confirm`). Marketplace policy: never publish such a rule (spec §5 — bundled
    automations execute with the installing user's tools; a moderator can't
    approve a silent auto-fire on the user's behalf).

    Mirrors the app's tolerant parser: unreadable / non-conforming JSON yields
    no live rules, so it can't auto-fire and isn't flagged here. Only a rule
    that is genuinely `confirm: false` (a real JSON boolean, matching the app's
    `as? Bool ?? true` cast) is rejected.
    """
    for m in memories:
        if not isinstance(m, dict) or m.get("path") != PUPA_AUTOMATIONS_PATH:
            continue
        try:
            cfg = json.loads(m.get("content", "") or "")
        except (json.JSONDecodeError, TypeError):
            continue  # app treats unparseable automations.json as no rules
        autos = cfg.get("automations") if isinstance(cfg, dict) else None
        if not isinstance(autos, dict):
            continue
        offenders = []
        for event_key, entries in autos.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and entry.get("confirm") is False:
                    offenders.append(entry.get("id") or f"<unnamed {event_key} rule>")
        if offenders:
            raise AppError(
                f"{PUPA_AUTOMATIONS_PATH} ships automation rule(s) that skip user "
                f"validation (confirm: false): {sorted(offenders)}. Remove the flag "
                f"or set confirm: true so the reaction is proposed, not auto-fired."
            )


def validate_component_typing(app):
    """Reject decode-blockers the Swift importer enforces but JSON can't express.

    Mirrors client `Codable` types so a bundle that passes here won't fail
    `MyAppImporter` with an opaque "isn't a valid Pupa app bundle": record ids in
    UUID_ID_LIST_KEYS collections must be canonical UUIDs, and any `reduce` must
    be a CalcReduce case. Walks the whole app tree (rows/items live nested under
    component bodies, charts under calculators, etc.).
    """
    def walk(node):
        if isinstance(node, dict):
            r = node.get("reduce")
            if isinstance(r, str) and r not in CALC_REDUCERS:
                raise AppError(f"invalid reduce '{r}' (CalcReduce is {sorted(CALC_REDUCERS)})")
            for k, v in node.items():
                if k in UUID_ID_LIST_KEYS and isinstance(v, list):
                    for el in v:
                        if isinstance(el, dict) and "id" in el and not (
                            isinstance(el["id"], str) and UUID_RE.match(el["id"])
                        ):
                            raise AppError(f"{k} entry has non-UUID id {el['id']!r} "
                                           "(the client decodes these ids as UUID)")
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(app)


def validate_metadata(slug, meta):
    if not isinstance(meta, dict):
        raise AppError("metadata.json is not an object")
    required = {"id", "version", "author", "summary", "tags"}
    missing = required - meta.keys()
    if missing:
        raise AppError(f"metadata.json missing fields: {sorted(missing)}")
    if meta["id"] != slug:
        raise AppError(f"metadata.id '{meta['id']}' != directory '{slug}'")
    if not isinstance(meta["version"], int) or isinstance(meta["version"], bool) or meta["version"] < 1:
        raise AppError("metadata.version must be an int >= 1")
    order = meta.get("order")
    if order is not None and (not isinstance(order, int) or isinstance(order, bool)):
        raise AppError("metadata.order must be an int")
    if not isinstance(meta["author"], str) or not meta["author"]:
        raise AppError("metadata.author must be a non-empty string")
    summary = meta["summary"]
    if not isinstance(summary, str) or not summary or len(summary) > 200:
        raise AppError("metadata.summary must be a non-empty string <= 200 chars")
    tags = meta["tags"]
    if not isinstance(tags, list) or len(tags) > 8 or not all(
        isinstance(t, str) and TAG_RE.match(t) for t in tags
    ):
        raise AppError("metadata.tags must be <= 8 lowercase-kebab strings")
    hp = meta.get("homepage")
    if hp is not None and (not isinstance(hp, str) or not hp.startswith("https://")):
        raise AppError("metadata.homepage must be an https:// URL")
    # Content license. Absent ⇒ the repo default (CC0-1.0, per CONTENT-LICENSE).
    # Present ⇒ this app opts out of CC0; the contributor asserts they hold the
    # rights to release under the named license (SPDX id or short name).
    lic = meta.get("license")
    if lic is not None and (not isinstance(lic, str) or not lic.strip() or len(lic) > 100):
        raise AppError("metadata.license must be a non-empty string <= 100 chars (SPDX id or license name)")
    attr = meta.get("attribution")
    if attr is not None and (not isinstance(attr, str) or not attr.strip() or len(attr) > 500):
        raise AppError("metadata.attribution must be a non-empty string <= 500 chars")


def validate_bundle(raw):
    """Parse + validate a bundle's bytes. Returns the decoded dict."""
    if len(raw) > PUBLISH_HARD_BYTES:
        raise AppError(f"app.pupa is {len(raw)//(1024*1024)} MB (> {PUBLISH_HARD_BYTES//(1024*1024)} MB publish limit)")
    try:
        bundle = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise AppError(f"app.pupa is not valid UTF-8 JSON: {e}")
    if not isinstance(bundle, dict):
        raise AppError("app.pupa root is not an object")
    header = bundle.get("header")
    if not isinstance(header, dict):
        raise AppError("bundle missing header")
    fmt = header.get("format")
    if fmt == LIBRARY_MAGIC:
        raise AppError("library bundles are not catalog entries (submit apps individually)")
    if fmt != BUNDLE_MAGIC:
        raise AppError(f"bundle header.format is '{fmt}', expected '{BUNDLE_MAGIC}'")
    fv = header.get("formatVersion")
    if not isinstance(fv, int) or fv < 1:
        raise AppError("bundle header.formatVersion must be a positive int")
    if fv > SUPPORTED_BUNDLE_FORMAT:
        raise AppError(f"bundle formatVersion {fv} > supported {SUPPORTED_BUNDLE_FORMAT}; update this validator")
    av = header.get("appVersion")
    if not isinstance(av, str) or not APPVERSION_RE.match(av):
        raise AppError("bundle header.appVersion must be a dotted numeric string")
    app = bundle.get("app")
    if not isinstance(app, dict):
        raise AppError("bundle missing app")
    if not isinstance(app.get("name"), str) or not app["name"]:
        raise AppError("bundle app.name must be a non-empty string")
    if not isinstance(app.get("iconSystemName"), str) or not app["iconSystemName"]:
        raise AppError("bundle app.iconSystemName must be a non-empty string")
    comps = app.get("components")
    if not isinstance(comps, list) or not comps:
        raise AppError("bundle app.components must be a non-empty list")
    if len(comps) > MAX_COMPONENTS:
        raise AppError(f"{len(comps)} components (> {MAX_COMPONENTS})")
    items = _count_listy(app, {"items", "events"})
    if items > MAX_ITEMS_PER_COMPONENT:
        raise AppError(f"a component has {items} items (> {MAX_ITEMS_PER_COMPONENT})")
    validate_component_typing(app)
    memories = bundle.get("memories", [])
    if not isinstance(memories, list):
        raise AppError("bundle memories must be a list")
    if len(memories) > MAX_MEMORY_FILES:
        raise AppError(f"{len(memories)} memory files (> {MAX_MEMORY_FILES})")
    for m in memories:
        if not isinstance(m, dict):
            raise AppError("a memory entry is not an object")
        reason = _bad_memory_path(m.get("path"))
        if reason:
            raise AppError(f"unsafe memory path '{m.get('path')}': {reason}")
        content = m.get("content", "")
        if not isinstance(content, str):
            raise AppError(f"memory '{m.get('path')}' content is not a string")
        if len(content.encode("utf-8")) > MAX_MEMORY_FILE_BYTES:
            raise AppError(f"memory '{m['path']}' exceeds {MAX_MEMORY_FILE_BYTES//1024} KB")
    validate_automations(memories)
    return bundle


def validate_screenshots(app_dir):
    shots_dir = app_dir / "screenshots"
    paths = []
    if not shots_dir.exists():
        return paths
    if shots_dir.is_symlink():
        raise AppError("screenshots/ must not be a symlink")
    files = sorted(f for f in shots_dir.iterdir() if not f.name.startswith("."))
    if len(files) > MAX_SCREENSHOTS:
        raise AppError(f"{len(files)} screenshots (> {MAX_SCREENSHOTS})")
    for f in files:
        if f.is_symlink() or not f.is_file():
            raise AppError(f"screenshots/{f.name} must be a regular file")
        if f.suffix.lower() not in SCREENSHOT_EXTS:
            raise AppError(f"screenshots/{f.name} must be .png/.jpg")
        data = f.read_bytes()
        if len(data) > MAX_SCREENSHOT_BYTES:
            raise AppError(f"screenshots/{f.name} exceeds {MAX_SCREENSHOT_BYTES//1024} KB")
        if not any(data.startswith(sig) for sig in IMAGE_MAGIC):
            raise AppError(f"screenshots/{f.name} is not a real PNG/JPEG (magic bytes)")
        paths.append(f"apps/{app_dir.name}/screenshots/{f.name}")
    return paths


def validate_app(app_dir, warnings):
    """Validate one apps/<slug>/ directory; return its index entry dict."""
    slug = app_dir.name
    if not SLUG_RE.match(slug):
        raise AppError(f"slug '{slug}' must match {SLUG_RE.pattern}")
    if app_dir.is_symlink():
        raise AppError("app directory must not be a symlink")
    for child in app_dir.iterdir():
        if child.name not in ALLOWED_APP_FILES and not child.name.startswith("."):
            raise AppError(f"unexpected file '{child.name}' (allowed: {sorted(ALLOWED_APP_FILES)})")
        if child.is_symlink():
            raise AppError(f"'{child.name}' must not be a symlink")

    pupa = app_dir / "app.pupa"
    metaf = app_dir / "metadata.json"
    if not pupa.is_file():
        raise AppError("missing app.pupa")
    if not metaf.is_file():
        raise AppError("missing metadata.json")

    raw = pupa.read_bytes()
    bundle = validate_bundle(raw)
    if PUBLISH_WARN_BYTES < len(raw) <= PUBLISH_HARD_BYTES:
        warnings.append(f"{slug}: app.pupa is {len(raw)//(1024*1024)} MB — consider exporting with records off")

    try:
        meta = json.loads(metaf.read_text("utf-8"))
    except json.JSONDecodeError as e:
        raise AppError(f"metadata.json invalid: {e}")
    validate_metadata(slug, meta)
    known = {"id", "version", "author", "summary", "tags", "homepage", "license", "attribution", "order"}
    for k in meta.keys() - known:
        warnings.append(f"{slug}: unknown metadata key '{k}' (ignored)")

    screenshots = validate_screenshots(app_dir)

    header, app = bundle["header"], bundle["app"]
    entry = {
        "id": slug,
        "name": app["name"],
        "icon": app["iconSystemName"],
        "author": meta["author"],
        "summary": meta["summary"],
        "tags": meta["tags"],
        "version": meta["version"],
        "appFormatVersion": header["formatVersion"],
        "appVersion": header["appVersion"],
        "includedRecords": bool(header.get("includedRecords", False)),
        "includedMemories": bool(header.get("includedMemories", False)),
        "exportedAt": header.get("exportedAt", ""),
        "path": f"apps/{slug}/app.pupa",
        "sizeBytes": len(raw),
        "sha256": _sha256(raw),
        "screenshots": screenshots,
        "_order": meta.get("order", 0),
    }
    if meta.get("homepage"):
        entry["homepage"] = meta["homepage"]
    if meta.get("license"):
        entry["license"] = meta["license"]
    if meta.get("attribution"):
        entry["attribution"] = meta["attribution"]
    return entry


def load_marketplace():
    if not MARKETPLACE.is_file():
        raise AppError("marketplace.json missing")
    m = json.loads(MARKETPLACE.read_text("utf-8"))
    for k in ("name", "owner", "description"):
        if not isinstance(m.get(k), str) or not m[k]:
            raise AppError(f"marketplace.json.{k} must be a non-empty string")
    if m.keys() - {"name", "owner", "description"}:
        raise AppError(f"marketplace.json has unexpected keys: {sorted(m.keys() - {'name','owner','description'})}")
    return m


def build_index():
    """Return (index_dict, warnings). Raises AppError on any fatal problem."""
    warnings = []
    market = load_marketplace()
    for child in REPO.iterdir():
        if child.name not in ALLOWED_ROOT:
            warnings.append(f"unexpected root path '{child.name}'")
    entries = []
    names_seen = {}
    if APPS.exists():
        for app_dir in sorted(p for p in APPS.iterdir() if p.is_dir()):
            entry = validate_app(app_dir, warnings)
            if entry["name"] in names_seen:
                warnings.append(f"duplicate app name '{entry['name']}' ({names_seen[entry['name']]}, {entry['id']})")
            names_seen[entry["name"]] = entry["id"]
            entries.append(entry)
    entries.sort(key=lambda e: (e["_order"], e["id"]))
    for e in entries:
        del e["_order"]
    index = {
        "formatVersion": CATALOG_FORMAT_VERSION,
        "name": market["name"],
        "owner": market["owner"],
        "description": market["description"],
        "entries": entries,
    }
    return index, warnings


def dumps_index(index):
    """Deterministic serialization: sorted keys, 2-space, trailing newline."""
    return json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def git_show(ref, path):
    import subprocess
    try:
        return subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=REPO, capture_output=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None  # new file at base


def bundle_content_changed(old_raw, new_raw):
    """Compare bundles by parsed value, so a reformat alone is not a change.

    Falls back to bytes if either side won't parse (a malformed bundle is
    caught by validate_bundle; here it just means "assume changed").
    """
    if old_raw == new_raw:
        return False
    try:
        return json.loads(old_raw) != json.loads(new_raw)
    except (ValueError, UnicodeDecodeError):
        return True


def check_version_bumps(base):
    """Fail if any app.pupa's content changed vs base without a version bump."""
    problems = []
    for app_dir in sorted(p for p in APPS.iterdir() if p.is_dir()) if APPS.exists() else []:
        slug = app_dir.name
        rel = f"apps/{slug}/app.pupa"
        old_bundle = git_show(base, rel)
        if old_bundle is None:
            continue  # new app
        new_bundle = (app_dir / "app.pupa").read_bytes()
        if not bundle_content_changed(old_bundle, new_bundle):
            continue
        old_meta_raw = git_show(base, f"apps/{slug}/metadata.json")
        old_v = json.loads(old_meta_raw).get("version") if old_meta_raw else 0
        new_v = json.loads((app_dir / "metadata.json").read_text("utf-8")).get("version")
        if not isinstance(new_v, int) or new_v <= (old_v or 0):
            problems.append(f"{slug}: app.pupa changed but version not bumped ({old_v} -> {new_v})")
    return problems


def cmd_check(base):
    index, warnings = build_index()
    generated = dumps_index(index)
    if not INDEX.is_file():
        print("FAIL: index.json is missing — run `make index`", file=sys.stderr)
        return 1
    current = INDEX.read_text("utf-8")
    if current != generated:
        print("FAIL: index.json is stale — run `make index` and commit it", file=sys.stderr)
        return 1
    problems = []
    if base:
        problems = check_version_bumps(base)
    for w in warnings:
        print(f"warning: {w}")
    if problems:
        for p in problems:
            print(f"FAIL: {p}", file=sys.stderr)
        return 1
    print(f"OK: {len(index['entries'])} app(s) valid, index.json current.")
    return 0


def cmd_write():
    index, warnings = build_index()
    INDEX.write_text(dumps_index(index), "utf-8")
    for w in warnings:
        print(f"warning: {w}")
    print(f"Wrote index.json with {len(index['entries'])} app(s).")
    return 0


def cmd_new_app(slug):
    if not SLUG_RE.match(slug):
        print(f"invalid slug '{slug}'", file=sys.stderr)
        return 1
    d = APPS / slug
    if d.exists():
        print(f"apps/{slug}/ already exists", file=sys.stderr)
        return 1
    d.mkdir(parents=True)
    stub = {
        "id": slug, "version": 1, "author": "your-github-handle",
        "summary": "One line, <= 200 chars.", "tags": ["example"],
    }
    (d / "metadata.json").write_text(json.dumps(stub, indent=2) + "\n", "utf-8")
    print(f"Scaffolded apps/{slug}/. Add app.pupa, then run `make index`.")
    return 0


def cmd_self_test():
    """Exercise the validators against crafted bad inputs (no disk writes)."""
    import io
    passed, failed = 0, 0

    def expect_error(desc, fn):
        nonlocal passed, failed
        try:
            fn()
            failed += 1
            print(f"  FAIL (no error raised): {desc}")
        except AppError as e:
            passed += 1
            print(f"  ok: {desc} -> {e}")

    def expect_ok(desc, fn):
        nonlocal passed, failed
        try:
            fn()
            passed += 1
            print(f"  ok: {desc}")
        except AppError as e:
            failed += 1
            print(f"  FAIL (unexpected error): {desc} -> {e}")

    def expect_is(desc, got, want):
        nonlocal passed, failed
        if got == want:
            passed += 1
            print(f"  ok: {desc}")
        else:
            failed += 1
            print(f"  FAIL: {desc} -> got {got!r}, want {want!r}")

    def good_bundle(**over):
        b = {
            "header": {
                "format": BUNDLE_MAGIC, "formatVersion": 1, "appVersion": "0.0.180",
                "exportedAt": "2026-07-10T00:00:00Z",
                "includedRecords": False, "includedMemories": False,
            },
            "app": {"name": "Test", "iconSystemName": "star", "components": [{"id": "tracker-1"}]},
            "memories": [],
        }
        b.update(over)
        return json.dumps(b).encode("utf-8")

    expect_ok("valid bundle", lambda: validate_bundle(good_bundle()))
    expect_error("oversize bundle", lambda: validate_bundle(b"x" * (PUBLISH_HARD_BYTES + 1)))
    expect_error("not json", lambda: validate_bundle(b"not json"))
    expect_error("wrong magic", lambda: validate_bundle(good_bundle(header={
        "format": "nope", "formatVersion": 1, "appVersion": "1"})))
    expect_error("library magic", lambda: validate_bundle(good_bundle(header={
        "format": LIBRARY_MAGIC, "formatVersion": 1, "appVersion": "1"})))
    expect_error("newer format", lambda: validate_bundle(good_bundle(header={
        "format": BUNDLE_MAGIC, "formatVersion": 999, "appVersion": "1"})))
    expect_error("no components", lambda: validate_bundle(good_bundle(
        app={"name": "T", "iconSystemName": "s", "components": []})))
    expect_error("memory traversal", lambda: validate_bundle(good_bundle(
        memories=[{"path": "../escape.md", "content": "x"}])))
    expect_error("memory absolute path", lambda: validate_bundle(good_bundle(
        memories=[{"path": "/etc/passwd", "content": "x"}])))
    expect_error("memory bad extension", lambda: validate_bundle(good_bundle(
        memories=[{"path": "notes/x.txt", "content": "x"}])))
    expect_ok("memory ok path", lambda: validate_bundle(good_bundle(
        memories=[{"path": "pupa/AGENTS.md", "content": "x"}])))

    _UUID = "512D4EF1-C329-4FB3-91AB-B88439DF6FBA"
    def typed(**over):
        comp = {"id": "tracker-1", "body": {"data": {}}}
        comp["body"]["data"].update(over)
        return good_bundle(app={"name": "T", "iconSystemName": "s", "components": [comp]})
    expect_ok("uuid row id ok", lambda: validate_bundle(typed(rows=[{"id": _UUID, "name": "r"}])))
    expect_error("non-uuid row id", lambda: validate_bundle(typed(rows=[{"id": "calc-row-1", "name": "r"}])))
    expect_error("non-uuid tracker item id", lambda: validate_bundle(typed(items=[{"id": "x1"}])))
    expect_ok("valid reduce avg", lambda: validate_bundle(typed(
        rows=[{"id": _UUID, "kind": {"aggregate": {"reduce": "avg"}}}])))
    expect_error("invalid reduce mean", lambda: validate_bundle(typed(
        rows=[{"id": _UUID, "kind": {"aggregate": {"reduce": "mean"}}}])))
    expect_ok("slack channel string id not flagged", lambda: validate_bundle(typed(
        channels=[{"id": "c1", "name": "general"}])))

    def automations(*rules, event="item.moved"):
        return good_bundle(memories=[{
            "path": PUPA_AUTOMATIONS_PATH,
            "content": json.dumps({"automations": {event: list(rules)}}),
        }])

    move_action = {"startThread": {"prompt": "Item moved to {{toColumn}}."}}
    expect_error("automation confirm:false auto-fires", lambda: validate_bundle(
        automations({"id": "r1", "action": move_action, "confirm": False})))
    expect_error("one confirm:false among safe rules", lambda: validate_bundle(
        automations(
            {"id": "ok", "action": move_action, "confirm": True},
            {"id": "bad", "action": move_action, "confirm": False})))
    expect_ok("automation confirm:true", lambda: validate_bundle(
        automations({"id": "r1", "action": move_action, "confirm": True})))
    expect_ok("automation confirm omitted (defaults true)", lambda: validate_bundle(
        automations({"id": "r1", "action": move_action})))
    expect_ok("automation confirm:'false' string is not a bool false", lambda: validate_bundle(
        automations({"id": "r1", "action": move_action, "confirm": "false"})))
    expect_ok("unparseable automations.json is tolerated", lambda: validate_bundle(good_bundle(
        memories=[{"path": PUPA_AUTOMATIONS_PATH, "content": "{not json"}])))

    expect_ok("valid metadata", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 1, "author": "h", "summary": "s", "tags": ["a"]}))
    expect_error("slug mismatch", lambda: validate_metadata("my-app", {
        "id": "other", "version": 1, "author": "h", "summary": "s", "tags": []}))
    expect_error("version zero", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 0, "author": "h", "summary": "s", "tags": []}))
    expect_error("summary too long", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 1, "author": "h", "summary": "x" * 201, "tags": []}))
    expect_error("bad tag", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 1, "author": "h", "summary": "s", "tags": ["Bad Tag"]}))
    expect_error("http homepage", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 1, "author": "h", "summary": "s", "tags": [], "homepage": "http://x"}))
    expect_ok("valid license + attribution", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 1, "author": "h", "summary": "s", "tags": [],
        "license": "CC-BY-NC-SA-4.0", "attribution": "Schema content © NovoPsych, https://novopsych.com"}))
    expect_error("blank license", lambda: validate_metadata("my-app", {
        "id": "my-app", "version": 1, "author": "h", "summary": "s", "tags": [], "license": "   "}))

    raw = good_bundle()
    pretty = json.dumps(json.loads(raw), indent=2).encode("utf-8")
    renamed = good_bundle(app={"name": "Renamed", "iconSystemName": "star",
                               "components": [{"id": "tracker-1"}]})
    expect_is("reformat is not a content change", bundle_content_changed(raw, pretty), False)
    expect_is("identical bytes are not a change", bundle_content_changed(raw, raw), False)
    expect_is("content edit is a change", bundle_content_changed(raw, renamed), True)
    expect_is("unparseable side counts as changed", bundle_content_changed(raw, b"{not json"), True)

    print(f"\nself-test: {passed} passed, {failed} failed")
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate + verify index current")
    ap.add_argument("--write", action="store_true", help="regenerate index.json")
    ap.add_argument("--base", help="git ref to check version bumps against")
    ap.add_argument("--new-app", metavar="SLUG", help="scaffold a new app dir")
    ap.add_argument("--self-test", action="store_true", help="run built-in tests")
    args = ap.parse_args()
    try:
        if args.self_test:
            return cmd_self_test()
        if args.new_app:
            return cmd_new_app(args.new_app)
        if args.write:
            return cmd_write()
        if args.check:
            return cmd_check(args.base)
        ap.print_help()
        return 1
    except AppError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
