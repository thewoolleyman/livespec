# Workaround design

## Objective

Keep the Codex Driver Stop hooks available to long-running sessions across
Codex marketplace auto-upgrades, without pinning release refs, disabling hooks,
or requiring a one-off Codex launch mode. Codex can delete the versioned cache
directory that an existing session captured in its hook command path. The
workaround must recreate compatibility links from recently active/known older
version names to the current complete Driver payload after each update.

## Proposed implementation

1. Add a Driver-owned reconciliation entry point that runs on the normal
   Codex plugin currency path immediately after marketplace upgrade/install.
2. Discover the installed Driver's current version and exact `installedPath`
   from `codex plugin list --json`, rather than assuming a cache layout or
   trusting only the enabled flag.
3. Validate the current payload before creating links: manifest, `hooks.json`,
   and every hook named by the Stop/PreToolUse declarations must exist and be
   callable by the bare Python invocation used by Codex.
4. Ensure the Driver cache root has a `latest` symlink pointing to the current
   complete version. `latest` is the only moving compatibility target; update
   it atomically after the new payload is validated.
5. Backfill the release-version names seen during the prior month. For every
   such name whose directory was deleted by Codex, create a relative symlink
   from that old version name to `latest` (or the platform-equivalent directory
   junction). Existing complete real directories are preserved. Existing
   compatibility links are preserved only when they resolve to `latest`; stale
   or unsafe links are replaced safely.
6. Retain compatibility aliases for one month only. A cleanup pass may delete
   compatibility symlinks older than the one-month window, but MUST NOT delete
   real version directories or the current `latest` target. Backfill must use
   the Driver release history/tag metadata rather than guessing arbitrary
   version names, and must be deterministic at month boundaries.
7. Verify `latest`, every backfilled alias, and both Stop-hook paths resolve to
   the validated current payload. Emit a concise repair report. Failure must
   be loud enough that the currency path cannot claim success while Stop hooks
   are absent.
8. Make the reconciliation idempotent and safe to rerun after every
   marketplace update. The next update may delete aliases, so the currency
   path recreates only the missing aliases and retargets `latest`.

## Runtime and safety boundaries

The repair is host-local Codex cache maintenance, not a repository plugin
payload. It must work for macOS/Linux and document the Windows junction
fallback. It must not alter marketplace refs, disable hooks, or symlink over a
complete version. It must account for concurrent Codex processes as far as the
available CLI permits and should prefer atomic link creation (`ln`/equivalent
with no follow) plus post-write verification. The alias topology must remain
one hop (`old-version -> latest -> current-version`), not a chain of old
version links, so each update changes only `latest` plus newly missing aliases.

## Verification and rollout

Cover discovery, `latest` creation/retargeting, one-hop alias creation,
one-month release-history backfill, month-boundary cleanup, idempotent rerun,
complete existing directory preservation, incomplete-current-payload refusal,
malformed or unsafe path refusal, and both Stop-hook resolution paths.
Exercise the real installed-cache shape in an integration test or a
deterministic mock cache, and run the Driver's full checks plus a post-update
smoke probe.

The first implementation should land in the Codex Driver's currency/installer
surface, then be exercised by a fresh Codex session and an update transition.
The plan remains open until the fix is merged, released, installed, and
verified against a real cache transition.
