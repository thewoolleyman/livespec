# Workaround design

## Objective

Keep the Codex Driver Stop hooks available to long-running sessions across
Codex marketplace auto-upgrades, without pinning release refs, disabling hooks,
or requiring a one-off Codex launch mode. Codex can delete the versioned cache
directory that an existing session captured in its hook command path. The
workaround must recreate compatibility links from recently active/known older
version names to the current complete Driver payload after each update.

## Proposed implementation

1. Add a Driver-owned reconciliation entry point that runs on every supported
   Codex plugin currency path immediately after marketplace upgrade/install.
   The entry point must be reachable from the Driver's ordinary provisioning
   path and from any native Codex update path that can replace an installed
   payload without running that provisioner.
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
   and what both startup auto-upgrade and explicit `codex plugin marketplace
   upgrade` / `codex plugin add` create, replace, or delete. This evidence
   decides whether the compatibility root is a versioned cache, a marketplace
   checkout, or another Codex-managed location. It is a hard precondition: no
   implementation may manufacture aliases against a guessed path.
2. Govern the resulting Driver-owned host-cache behavior in the Driver's
   specification by a propose-change → revise cycle. The contract must state
   the validated-payload gate, one-hop alias topology, preservation of real
   version directories, the bounded release-history retention window,
   idempotence, failure reporting, and the supported platform behavior.
3. Implement the reconciler and invoke it after each ordinary Codex
   marketplace currency/install sequence succeeds. If Codex can update a
   plugin outside that sequence, implement or document an equally reliable
   post-update trigger before claiming the fix covers native updates. It must
   use the evidence from step 1 to locate the payload, validate every declared Stop and
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

## Live incident evidence — 2026-08-14

An active Codex session retained these expanded Stop-hook commands after its
Driver cache had advanced:

```text
/usr/bin/python3 /home/ubuntu/.codex/plugins/cache/livespec-driver-codex/livespec/0.6.0/hooks/no_shadow_ledger.py
/usr/bin/python3 /home/ubuntu/.codex/plugins/cache/livespec-driver-codex/livespec/0.6.0/hooks/codex_background_memory_audit.py
```

At diagnosis, the old `0.6.0` cache directory and any `latest` alias were
absent. The current release cache was the complete real directory `0.6.1`.
`codex plugin list --json -m livespec-driver-codex` reported version `0.6.1`
but named the marketplace checkout
`~/.codex/.tmp/marketplaces/livespec-driver-codex/livespec` as its `source.path`;
that JSON field is therefore not the retained hook execution root. The
marketplace checkout was at release commit `2911d81` (`v0.6.1`), while the
removed cache name corresponded to `v0.6.0` (`2533d7d`).

The current Driver declares four Python hooks in `hooks/hooks.json`: one
`livespec_footgun_guard.py` PreToolUse hook, three `block_auto_memory.py`
PreToolUse matchers, and the two Stop hooks above. Its current
`dev-tooling/ensure-codex-plugins.sh` performs marketplace `add`, marketplace
`upgrade`, and plugin `add` commands only; it contains no reconciliation or
compatibility-alias step. Codex's local CLI help likewise describes
`marketplace upgrade` only as refreshing configured Git marketplace snapshots
and `plugin add` only as installing from a snapshot, with no post-update hook
or retention option. The official OpenAI documentation search did not expose
an authoritative cache-retention or lifecycle contract for this feature.

Upstream Codex issue [#31383](https://github.com/openai/codex/issues/31383),
open as of this incident, reports the same order of events: Codex loads
versioned hook commands, starts a background marketplace auto-upgrade at
session startup, and reinstalls the cache by deleting the old version or
replacing the cache entry. It also reports that a fresh session works because
it loads the newly materialized cache. This confirms that the durable trigger
cannot be limited to the Driver's explicit provisioner: startup auto-upgrade
is a normal update route and must either run reconciliation before retained
hook paths can execute or be covered by a cache layout that survives it.
The implementation must still retain a measured, version-pinned integration
probe rather than assume undocumented behavior beyond this reported lifecycle.

The then-current Codex source at CLI `0.147.0` corroborated the report:
[`manager.rs`](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/manager.rs)
spawns `plugins-marketplace-auto-upgrade` and force-reinstalls refreshed
non-curated plugin caches, while
[`store.rs`](https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/store.rs)
removes superseded semver directories or swaps the whole cache root on a
reinstall. Therefore an alias located inside that Codex-managed cache cannot
be the reconciliation trigger or durable state: the updater may remove it
with the old cache entry. A Driver-side observer has to live outside the
cache, and only an upstream Codex change can eliminate the race between hook
path capture and that background replacement.

The emergency repair established and verified this topology:

```text
0.6.0 -> latest -> 0.6.1/
```

Both retained Stop-hook paths resolved through that one hop to the `0.6.1`
payload and passed `python3 -m py_compile`. The repair also verified every
current hook script before retargeting `latest`. This proves the immediate
alias mechanism, but not its trigger: a durable implementation must prove
that every normal update route invokes the reconciliation after Codex has
materialized the new cache and before a retained hook path is needed.

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
