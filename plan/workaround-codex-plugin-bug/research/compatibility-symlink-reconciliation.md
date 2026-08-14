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
2. Discover the current Driver version and the actual hook execution root from
   Codex's current JSON schema and a captured hook command. The reconciler
   must not assume an `installedPath` field or a cache layout: the current CLI
   can report a marketplace source path instead of a versioned cache copy.
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

## Delivery plan

The work lands in `livespec-driver-codex`; the core repo holds this plan and
the cross-repository ledger anchor only.

1. Establish the real Codex artifact lifecycle on a disposable, release-tracking
   marketplace install. Record the JSON fields returned by `codex plugin list`,
   the exact expanded Stop-hook commands in a session that predates an update,
   and what `codex plugin marketplace upgrade` / `codex plugin add` creates,
   replaces, or deletes. This evidence decides whether the compatibility root
   is a versioned cache, a marketplace checkout, or another Codex-managed
   location. It is a hard precondition: no implementation may manufacture
   aliases against a guessed path.
2. Govern the resulting Driver-owned host-cache behavior in the Driver's
   specification by a propose-change → revise cycle. The contract must state
   the validated-payload gate, one-hop alias topology, preservation of real
   version directories, the bounded release-history retention window,
   idempotence, failure reporting, and the supported platform behavior.
3. Implement the reconciler and invoke it only after the ordinary Codex
   marketplace currency/install sequence succeeds. It must use the evidence
   from step 1 to locate the payload, validate every declared Stop and
   PreToolUse hook under bare `python3`, atomically retarget `latest`, then
   backfill only bounded, known release names. It may never modify a complete
   real directory, follow an unsafe existing link, or change marketplace refs
   or hook configuration.
4. Prove the transition in a deterministic mock-cache integration test and a
   real host transition. The latter starts a session on an older released
   Driver, upgrades the marketplace/installation, and verifies that both
   retained Stop-hook command paths resolve through one hop to the current,
   validated payload. Release, install, and repeat the probe after the next
   upgrade.

## Scope and deferrals

The immediate objective is long-running-session hook continuity for the Codex
Driver while tracking the normal `release` ref. It deliberately does not pin a
marketplace, disable hooks, or require an alternate Codex launch command.

- Windows junction implementation is deferred until the macOS/Linux lifecycle
  has been measured and the implementation contract is ratified. The first
  delivery must document the platform result explicitly rather than pretending
  that POSIX symlink behavior is portable.
- Compatibility names are restricted to versions obtained from the Driver's
  release history within the defined retention window. Arbitrary user-supplied
  directory names and indefinite alias retention are deferred because they
  would turn a hook-recovery mechanism into an unsafe cache mutator.
- A general repair for all Codex plugins is out of scope. This plan owns only
  the `livespec-driver-codex` payload and its declared hooks; a reusable Codex
  platform fix can be proposed separately once the observed lifecycle is
  established.

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
