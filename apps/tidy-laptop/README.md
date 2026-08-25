# Tidy Laptop

A recoverable desktop-cleanup workflow. Ships **records off** — an empty
tracker plus the agent capability. On first open, run `/setup` to confirm scan
scope and topics, then scan produces the first suggestions.

## Flow

1. **Setup** (`/setup`) — confirm `scanScope.allow` (default `~/Desktop`), pick
   active topics, optionally add recurring scan reminders (`tidy-notify`
   registers them as local notification banners that re-run the scan on tap).
2. **Scan** (`/tidy-scan`) — read-only. Populates the *Cleanup Jobs* tracker
   with `Suggested` items across four topics: **Junk/Delete**, **Reorganize**,
   **Security**, **Disk hogs**. Never modifies files.
3. **Triage** — move a card to the **Apply** column. The `apply-cleanup`
   automation (`confirm: true` — it proposes, you tap Start) runs the matching
   cleanup skill for that topic.
4. **Apply, recoverably** — junk → Trash (never `rm`), reorganize → logged
   `mv`, disk hogs → Trash/archive, security → least-destructive fix. Each
   writes a reversible change log to `tidy-log/<itemId>.md`, sets `LogRef`, and
   moves the card to **In-Review**.
5. **Purge** (`/clean-tracker`) — clears `Done`/`Rejected` cards; keeps logs.

## Safety

- **Recoverable only.** Trash and logged moves, never permanent delete.
- **Scope-bound.** Acts only inside `scanScope.allow`; system dirs, other
  users, and cloud-synced dirs are denied unless you add them.
- **Every action is logged and reversible** via `tidy-log/`.
- **Secrets are located, not copied.** A Security finding records the path and
  the kind of credential; the value never lands in a card, a log, or the chat.

## Requirements

**Needs shell access, which is not granted by default.** Every scan and every
fix shells out (`du`, `find`, `mdfind`, `osascript`, `mv`, `chmod`). Without it
the app installs and opens fine, but no scan can return anything.

Those commands run wherever your shell runs — not necessarily the laptop in
front of you — and they assume **macOS**: recoverable delete is `osascript`
driving Finder, so Trash and "Put Back" work. Somewhere without Finder, the app
stops rather than delete without a way back.

Recurring reminders use local notifications, so they need notification
permission. Only daily, weekly and every-N-hours cadences repeat; there is no
monthly trigger.

Cleanup skills act only when you move a card to **Apply** and confirm.
