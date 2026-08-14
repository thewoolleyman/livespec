# Codex hook-cache workaround handoff

**Ledger anchor:** epic `livespec-ipfg65` (`thewoolleyman/livespec` tenant).

## Immediate live-state first check

The active Codex session captured Stop-hook paths under:

```text
/home/ubuntu/.codex/plugins/cache/livespec-driver-codex/livespec/0.6.0/hooks/no_shadow_ledger.py
/home/ubuntu/.codex/plugins/cache/livespec-driver-codex/livespec/0.6.0/hooks/codex_background_memory_audit.py
```

Codex `0.147.0` deletes old versioned cache paths during its background
marketplace auto-upgrade. The live repair established:

```text
0.6.0 -> latest -> 0.6.1/
```

The verified current payload is
`/home/ubuntu/.codex/plugins/cache/livespec-driver-codex/livespec/0.6.1`.
Before any plugin/bootstrap command, verify these two old paths with
`/usr/bin/python3 -m py_compile`; they must resolve to the `0.6.1` hooks.

## Live watcher

A cache-external emergency watcher script is installed at:

```text
/home/ubuntu/.local/bin/livespec-codex-hook-cache-watch.sh
```

It polls the Driver cache every 0.2 seconds and recreates `latest` and the
`0.6.0` compatibility alias from outside the cache. Its log is at:

```text
/home/ubuntu/.local/state/livespec-codex-hook-cache-watch.log
```

The process was launched with `nohup`; find it with:

```bash
ps -eo pid,ppid,etime,args | rg 'livespec-codex-hook-cache-watch\.sh'
```

**The watcher is a foreground `nohup`'d process, NOT a systemd/cron-managed
service — it does NOT survive a host reboot or a terminated parent session,
and previous sessions' watcher instances have been found dead on resume.**
Confirmed dead-on-resume once already, at the start of the 2026-08-14 06:4x
UTC session that wrote this note (`ps` found only the grep/rg self-match; the
`latest` and `0.6.0` aliases were both absent from
`/home/ubuntu/.codex/plugins/cache/livespec-driver-codex/livespec/`). It was
restarted then via the same `nohup ... &`/`disown` pattern, and both aliases
reappeared within one poll interval. **Every session that resumes this plan
MUST re-run the liveness check above FIRST, before any Codex plugin/bootstrap
command, and restart the watcher if it is not running:**

```bash
nohup /home/ubuntu/.local/bin/livespec-codex-hook-cache-watch.sh \
  > /home/ubuntu/.local/state/livespec-codex-hook-cache-watch.log 2>&1 < /dev/null &
disown
```

This is a stopgap, not the fix — it lasts only until PR #2286's platform-level
diagnosis + the Driver spec proposal below land as a real implementation
(step 5 of the resume order). Do not treat "watcher currently running" as a
reason to deprioritize that implementation work.

The final controlled alias-removal probe from the prior session was
interrupted by the operator. Do not assume its final topology: run the
liveness check above first.

## Root cause

Codex's current source confirms the issue:

- `core-plugins/src/manager.rs` starts a background
  `plugins-marketplace-auto-upgrade` task at startup and force-reinstalls
  refreshed non-curated plugin caches.
- `core-plugins/src/store.rs` removes superseded semver directories or swaps
  the entire plugin cache root on reinstall.

Thus cache-local aliases are deliberately removed on normal updates. A
cache-external observer can restore them after an update, but it cannot make
the race between captured hook paths and Codex's cache replacement atomic.
The platform-complete remedy is an upstream Codex change to retain old cache
paths or re-resolve hook roots.

## Core plan and PR

Plan epic: `livespec-ipfg65`.

Core plan research worktree:

```text
/home/ubuntu/.worktrees/livespec/plan/workaround-codex-plugin-bug-live-evidence
branch: plan/workaround-codex-plugin-bug-live-evidence
```

PR: https://github.com/thewoolleyman/livespec/pull/2286

It contains the measured incident, exact cache topology, upstream issue
`openai/codex#31383`, and direct Codex source corroboration. Auto-merge is
enabled. CI is waiting on the repository's sole online `self-hosted/local-ci/
poweredge` runner; every other matching runner was offline. This is capacity,
not a code failure.

The primary core checkout has a user-owned dirty file and is behind origin:

```text
/data/projects/livespec
M plan/fleet-ci-runner-pool/supervisor-handoff.md
```

Do not stash/revert that file or pull the primary checkout over it.

## Driver spec proposal

Driver worktree:

```text
/home/ubuntu/.worktrees/livespec-driver-codex/spec/codex-hook-cache-reconciliation
branch: spec/codex-hook-cache-reconciliation
```

Committed proposal: `3248deb docs(spec): propose Codex hook cache reconciliation`.
It adds only:

```text
SPECIFICATION/proposed_changes/codex-hook-cache-reconciliation.md
```

The proposal requires a cache-independent reconciler + observer, explicit
provisioning integration, bounded one-hop aliases, real-directory safety,
mock-cache coverage, and a real old-session upgrade test. Its static doctor
passes.

The Driver worktree initially failed full pre-push only because its gitignored
worktree pack was absent. Run the standalone safe repair (NOT `just bootstrap`,
which can update plugins and remove aliases):

```bash
mise exec -- just install-worktree-pack
```

After that, `mise exec -- just check-pre-push` passed in full: 394 hook tests,
33 e2e mock tests, lint/types, static doctor, and all aggregate checks. It
wrote a green token. A prior installer-added tracked `.livespec.jsonc` change
was removed; ensure the branch still has only the proposal commit before push.

The proposal requires the repository's independent ratification review before
it can be revised into the live Driver spec. Default policy is `manual-spawn`,
so obtain a separate read-only reviewer verdict containing `NO BLOCKERS` and
the exact resulting-files digest before invoking `livespec:revise`. Do not
start product implementation before that revision is accepted.

## Safe resume order

1. Verify/recreate the live hook aliases if needed; confirm the watcher is
   running. Do not run `just bootstrap` or normal plugin provisioning first.
2. Check whether PR #2286 merged; clean up only after merge, preserving the
   primary's user-owned dirty file.
3. Verify/push the Driver proposal branch and open its PR if the interrupted
   push did not complete.
4. Obtain independent ratification, revise the Driver spec, then create the
   Driver-tenant implementation work item from the proposal's
   `codex-hook-cache-reconciliation` commitment.
5. Implement the durable external watcher/reconciler using TDD, release it,
   and run the real long-session upgrade probe.
