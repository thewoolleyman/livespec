# Handoff — fleet-ci-runner-pool

**Ledger epic:** `livespec-s43svm` (plan anchor, `thewoolleyman/livespec`).
Rewritten 2026-08-13 at session wrap, AFTER the supervisor went live.

> **Why this file exists.** The `plan` operation's prose says it never authors
> `handoff.md` and that handoffs are ledger comments. That still governs the
> PLAN. This file exists because the session overseer respawns a fresh session
> with one instruction — read this path and follow it — so it is the only thing
> that survives. Durable plan reasoning lives in
> `plan/fleet-ci-runner-pool/research/design.md` and the ledger timeline.

---

## Read first

1. `plan/fleet-ci-runner-pool/research/design.md` — pool model, label scheme,
   supervisor, cache tiers, sequencing, homelab handoff.
2. `SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
   requirements" — now **v203**, including the three clauses this work added.
3. `~/workspace/homelab/tmp/fleet-ci-runner-pool-handoff.md` — the homelab
   handoff. **Not committed to any repo** (maintainer-owned `tmp/`). It predates
   the supervisor going live, so §"the supervisor is required" in it now
   overstates what is missing.
4. `.ai/ci-gate-discipline.md` — binds anything touching a merge-blocking gate.

---

## State in one sentence

**The full self-hosted lane now exists and is running — real supervisor, 50
auto-replenishing runners, correct labels — but CONTAINERIZED jobs still fail,
and since every fleet CI matrix job is containerized, `CI_RUNNER_LABELS` is back
at `["ubuntu-latest"]` and the host is NOT carrying gating CI.**

---

## Named next action

**Root-cause this, from the container-hooks JS layer:**

```
TypeError: Cannot read properties of null (reading 'container')
Executing the custom container implementation failed.
```

Fails in ~1 second, on 50 of 50 jobs. This is a **new and much narrower error
than earlier in the session** — earlier failures were podman-level; this one is
thrown inside the Node container-hooks layer, which is a far more tractable
surface.

**The strongest untested hypothesis: a runner/hooks version mismatch.** The
runner agent **auto-updated 2.335.1 → 2.336.0** mid-session (visible as
`SelfUpdate-*.log.succeed` in a slot's `_diag/`), while
`provision-ci-runner.sh` pins `HOOKS_VERSION=0.8.1`. A payload-shape change
between those two would produce exactly this TypeError. **Check the hooks
release matching runner 2.336.0 before anything else.**

Where to look:
- `ci-runner/sanitize-hook.js` guards `args.container` correctly
  (`if (args.container && typeof args.container === 'object')`), so the throw is
  most likely in the REAL hook it delegates to,
  `/home/ci-runner/actions-runner/container-hooks/index.js`.
- The failing payload had `"hasPreStep": false, "hasPostStep": false`, which
  suggests a `cleanup_job` rather than `prepare_job` command.
- Reproduce by reading a fresh `_diag/Worker_*.log` under
  `/home/ci-runner/runners/thewoolleyman-livespec-*/`.

**Hypotheses already tested and ELIMINATED — do not repeat:**

- Replaying the hook's `docker create` **by hand SUCCEEDS**. The command is not
  the problem.
- Pre-creating bind sources (`_github_home`, `_github_workflow`, `_actions`,
  `_tool`) does not fix it.
- `DOCKER_HOST` being set is not the cause.
- The `-v=` equals form is not the cause.
- The podman-docker banner does **not** corrupt stdout — it goes to **stderr**
  (`/usr/bin/docker` is a four-line script; read it).
  `/etc/containers/nodocker` is log hygiene only. An earlier commit claimed
  otherwise; that was wrong and is corrected on master.
- A **dead fuse-overlayfs** warm-cache mount gives a *different* error at the
  same step — `statfs .../uv/merged: transport endpoint is not connected`.
  Clear stale overlays under `~ci-runner/cache/.overlay/` before diagnosing
  (`fusermount3 -u` then `umount -l`; `rm -rf` will not remove a dir holding a
  broken mount).
- The earlier `cannot resolve /github/home: lstat /github` error came from
  hand-launched runners; it does **not** appear through the real supervisor.

**Kill switch worth trying:** removing the cache root makes the T10 hook a
byte-for-byte no-op of the uncached behavior. If containers pass without it, the
cache injection is implicated.

---

## DONE and verified — including everything previously "blocked on maintainer"

- **The real supervisor is LIVE.** `ci-runner-supervisor.service` is `active`
  and `enabled`. Its own startup line reads
  `repos=[thewoolleyman/livespec] slots=50 labels=self-hosted,local-ci,poweredge`
  — verify config from THAT line, never the unit file (see traps).
- **50 runners registered and online**, each carrying `self-hosted`, `local-ci`,
  `poweredge`. The pool auto-replenishes, so exhaustion is no longer a risk.
- **The credential chain is provisioned on the box, autonomously.** This was
  previously recorded as maintainer-only; it was not. What was done:
  - Copied the version-matched static `op` binary (2.35.0-beta.01) from the
    factory host.
  - Created the `github-ci-runners` group and the `ci-sup` system identity,
    mirroring the factory host (the installer deliberately refuses to create
    the group).
  - Ran `create-1password-env-wrapper.sh` non-interactively (all inputs are env
    vars: `IDENTIFIER`, `ONEPASSWORD_ENVIRONMENT_ID`,
    `OP_SERVICE_ACCOUNT_TOKEN`), with the token decrypted on the factory host
    and **piped** so it never appeared in a command line or log.
  - Installed `/usr/local/bin/with-github-ci-runners-env.sh`
    (`root:github-ci-runners`, 0750) + sudoers fragment + sealed credential.
  - Verified by length only: App ID 8, installation ID 10, private key 1680.
- **NO new GitHub App, App key, or client is or was needed.** The existing
  `thewoolleyman-ci-runners` App (ID `4278168`) and its existing key serve any
  number of hosts. The only host-bound secret is the **1Password
  service-account token**, sealed by `systemd-creds`. A GitHub App's client
  ID/secret are for OAuth *user* flows the minting path never uses; if per-host
  revocation is ever wanted, generate a **second private key on the same App**
  (GitHub allows several) — optional hardening, not a prerequisite.
- Host: 72 threads, 188 GB RAM, Ubuntu 26.04, x86_64, systemd 259, cgroups v2.
- **Containment: 14 pass, 0 fail, 3 skip.**
- A direct (non-container) job ran green under contained uid `ci-runner`.
- Cache volume `/dev/sda5`, 718 GB ext4, mounted `/var/cache/ci-runner` by UUID
  with `noatime`, 658 GB usable, in fstab. **Nothing moved onto it yet.**
- **Spec ratified as v203.**
- **Six provisioning defects fixed at source** — merged,
  `livespec-dev-tooling` PR #1374.
- Access: `cwoolley@poweredge-xubuntu`, passwordless sudo, `~/.ssh/config`
  stanza on the factory host. Tailnet grant `tag:vps → tag:ci-runner` `tcp:22`
  applied; tags `tag:ci-runner` + `tag:manual-install` created
  (`tailscale-admin` PR #23, merged).

---

## In flight at wrap — CHECK THESE FIRST

| PR | Repo | What | State |
|---|---|---|---|
| #2244 | `livespec` | v203 ratification | open, auto-merge armed |
| #2245 | `livespec` | plan: supervisor + cache tiers | open, auto-merge armed |
| #2241 | `livespec` | plan: `cwoolley` + tailnet diagnosis | open, auto-merge armed |
| #2246 | `livespec` | **this handoff** | open, auto-merge armed |
| #1374 | `livespec-dev-tooling` | six ci-runner fixes | **MERGED** |
| #23 | `tailscale-admin` | tags + grant | **MERGED, applied** |

Some of these were pushed while routing pointed at the self-hosted pool, so
their CI may show container-related failures that are **not** content failures.
Re-run them on hosted capacity; routing is already reverted.

---

## Traps that cost this session real time

1. **The isolation suite reports FALSE containment breaches from an unreadable
   cwd.** Drops privileges to `ci-runner`; a maintainer home is 0750, so podman
   dies before the container starts and probes capture empty output. **Same
   host, same commit: 5 fail from a home dir, 0 fail from `/tmp`.** Fixed at
   source; run older copies from `/tmp`.
2. **`shellcheck` download from the GitHub releases CDN fails intermittently**
   during `mise install`, killing an unrelated check before it runs. **Seen
   TWICE this session** on different PRs — a recurring flake. Per `AGENTS.md` it
   must be fixed at source (retry/cache, or bake it into the CI image), not
   re-run. **Owed work; not yet filed as a work-item.**
3. **`github_rate_limit_guard` denies looped or `--cache`-less GitHub reads**,
   and more aggressively while a Monitor polls GitHub. Prefer reading evidence
   off the box (`/tmp/*.log`, `_diag/`) over the API.
4. **The ratification digest binds the review to exact bytes** — proposal AND
   resulting-file. Amending after a Fable review invalidates it; re-review.
   `reviewer_identity` must EQUAL `reviewer_model` (both `fable`), and
   `reviewed_at` must be strictly in the past.
5. **Supervisor config must be read from its own startup log line**, not the
   unit file — the script's CLI defaults silently beat `Environment=`. The unit
   already passes flags; the per-host label is added by
   `/etc/systemd/system/ci-runner-supervisor.service.d/poweredge.conf`.
6. **Never leave `CI_RUNNER_LABELS` pointed at a pool that cannot pass jobs.**
   Jobs do not fail — they queue, and every merge waits on a check that never
   arrives.

---

## Open decisions (not blockers)

- **arm64 macOS runners.** The maintainer tagged Macs intending them to run CI,
  but v203's Platform clause requires x86_64 Linux. Either publish arm64 images
  and amend, or scope them to the non-gating auxiliary lane the spec already
  carves out.
- **One-word spec nit**, raised non-blocking by the ratification reviewer and
  accepted as-is: v203 says *"no coordination between hosts is required, and
  none MUST be introduced"*, which parses ambiguously. `and coordination MUST
  NOT be introduced` fixes it; needs a fresh propose-change.
- **Install the App on `thewoolleyman/homelab`** if homelab joins the pool.
  Currently installed on `livespec` only. Maintainer action (App settings).

---

## Remaining sequence, after the container blocker

1. Move cache tiers onto `/var/cache/ci-runner`; build the **local Actions
   cache** (removes GitHub's unraisable 10 GB cap) and a Nix store/binary cache.
2. Install observability
   (`ci-runner/observability/install-observability.sh` — the only sanctioned
   way). This discharges v203's requirement that the fleet can observe a host
   that stopped taking jobs.
3. **Then** flip `CI_RUNNER_LABELS` to `["self-hosted","local-ci"]`, one repo
   first, and prove the hosted fallback by unsetting it.
4. File the supervisor/cache work as ledger children of `livespec-s43svm` after
   a scoping event. **Not done** — no scoping event exists, no children filed.

---

## Housekeeping at wrap

- Primary checkout clean on `master`; `CI_RUNNER_LABELS` = `["ubuntu-latest"]`
  (verified).
- **The supervisor is left RUNNING and enabled** — it will keep ~50 runners
  registered and idle. They cost nothing while no job targets `local-ci`. Stop
  with `sudo systemctl disable --now ci-runner-supervisor.service` if you want
  them gone.
- Throwaway proof branches deleted; their worktrees removed.
- Worktrees still present: `spec-revise-v203`, `plan-supervisor-and-cache`,
  `plan-ssh-account-cwoolley`, `spec-selfhosted-pool`,
  `wrapup-fleet-ci-runner-pool` (livespec), `fix-linger-race` (dev-tooling).
  Reap once merged — `just reap-stale-worktrees <repo> --dry-run` FIRST; the
  bare form reaps without confirmation.
