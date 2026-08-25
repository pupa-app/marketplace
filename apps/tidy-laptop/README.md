# Tidy Laptop

A recoverable desktop-cleanup workflow. Ships **records off** — an empty
tracker plus the agent capability. On first open, run `/setup` to confirm scan
scope and topics, then scan produces the first suggestions.

## Flow

1. **Setup** (`/setup`) — confirm `scanScope.allow` (default `~/Desktop`), pick
   active topics, optionally add recurring scan reminders.
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

## Requirements

macOS host with shell access (uses `du`/`find`/`mdfind` for scans and Finder
Trash for recoverable deletes). Cleanup skills act only when you move a card to
**Apply** and confirm.
