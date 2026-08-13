# Handoff — fleet-ci-runner-pool

**Ledger epic:** `livespec-s43svm` (plan anchor, `thewoolleyman/livespec`).
Written 2026-08-13 at session wrap.

> **Why this file exists at all.** The `plan` operation's own prose says it
> never authors `handoff.md` and that handoffs are append-only ledger comments.
> That still governs the PLAN. This file exists because the session overseer
> respawns a fresh session with exactly one instruction — read this path and
> follow it — so it is the only thing that survives. Treat it as the session
> resume record, and keep the durable plan reasoning in
> `plan/fleet-ci-runner-pool/research/design.md` and the ledger timeline.

---

## Read first, in this order

1. `plan/fleet-ci-runner-pool/research/design.md` — the design: pool model,
   label scheme, supervisor requirement, cache tiers, sequencing, homelab
   handoff.
2. `SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
   requirements" — now at **v203**, including the three clauses this work added.
3. `~/workspace/homelab/tmp/fleet-ci-runner-pool-handoff.md` — the handoff
   written for `thewoolleyman/homelab`. **Not committed to any repo** (it lives
   in maintainer-owned `tmp/`); if it matters long-term, that is unfinished
   business.
4. `.ai/ci-gate-discipline.md` — binds any change touching a merge-blocking
   gate. Fix the gate, never add a bypass.

---

## The one-sentence state

**Runners execute on `poweredge-xubuntu` and the host is provisioned, contained,
and proven for DIRECT jobs — but CONTAINERIZED jobs fail, fleet CI is entirely
containerized, so the host is NOT carrying gating CI and `CI_RUNNER_LABELS` is
deliberately still `["ubuntu-latest"]`.**

---

## Named next action

**Root-cause the containerized-execution failure.** It is the single thing
between this host and serving fleet CI. Everything else below is either done or
downstream of it.

The failure, at container create:

```
cannot resolve /github/home: lstat /github: no such file or directory
```

**Do not repeat these — each was tested and eliminated:**

- **Replaying the hook's exact `docker create` by hand SUCCEEDS.** The command
  is not the problem; something about the hook's invocation environment is.
  This is the central clue and the reason the obvious hypotheses all failed.
- Pre-creating the bind-source directories (`_github_home`, `_github_workflow`,
  `_work/_actions`, `_work/_tool`) does **not** fix it.
- `DOCKER_HOST` being set does **not** cause it — tested directly with and
  without.
- The `-v=` equals form does **not** cause it — tested against the space form.
- The podman-docker banner does **not** corrupt stdout. It is written to
  **stderr** (`read /usr/bin/docker` — it is a four-line shell script). An
  earlier commit in this work claimed otherwise; that claim was wrong and was
  corrected on master. `/etc/containers/nodocker` is log hygiene only.

**A separate failure produces a different error at the same step and will
mislead you if you hit it first:** a dead fuse-overlayfs warm-cache mount gives
`statfs .../uv/merged: transport endpoint is not connected`. Clear stale
overlays under `~ci-runner/cache/.overlay/` before diagnosing, and note that
`rm -rf` will not remove a directory holding a broken mount — unmount first
(`fusermount3 -u`, then `umount -l`).

Suggested next probes, none yet run: compare the hook's full environment against
a working manual invocation (the hook is `container-hooks/index.js` behind
`sanitize-hook.js`); check whether `sanitize-hook.js` rewrites the mount list;
and try a job with the warm-cache overlay disabled entirely (removing the cache
root is the documented kill switch and makes the hook a byte-for-byte no-op of
the uncached behavior).

---

## What is DONE and verified

- **Host provisioned.** `poweredge-xubuntu`, 72 threads (2× Xeon E5-2696 v3),
  188 GB RAM, Ubuntu 26.04, systemd 259, cgroups v2, x86_64. 50 runner instance
  dirs.
- **Containment proven:** isolation exit suite **14 pass, 0 fail, 3 skip**.
  Container-root maps to host uid 1001; all host-loopback denied; a job's write
  stayed in the throwaway upper with the shared lower unchanged; agent
  PID-namespace isolated. Run it from a neutral cwd — see the trap below.
- **A real job executed there**, direct (non-container), green, under contained
  uid `ci-runner` (single group, no sudo), then auto-deregistered.
- **Four livespec CI matrix jobs dispatched to the host and ran** — they failed
  on the container gap above, but execution and routing were verified.
- **Access:** SSH from the factory host as `cwoolley@poweredge-xubuntu`;
  `~/.ssh/config` on the factory host carries the `Host` stanza. Passwordless
  sudo. Tailnet grant `tag:vps → tag:ci-runner` `tcp:22`, merged and applied
  (`thewoolleyman/tailscale-admin` PR #23), plus new role tags `tag:ci-runner`
  and `tag:manual-install`.
- **Cache volume:** `/dev/sda5`, 718 GB ext4, mounted `/var/cache/ci-runner` by
  UUID with `noatime`, owned `ci-runner`, **658 GB usable**, in `/etc/fstab`,
  `findmnt --verify` clean. **Nothing has been moved onto it yet.**
- **Spec ratified as v203** — capacity is a label-keyed pool; every runner
  carries a shared pool label plus a host-unique one; a host is proven by
  EXECUTING a job, not by registering one.
- **Six provisioning defects fixed at source**, merged in
  `thewoolleyman/livespec-dev-tooling` PR #1374 (see below).

---

## In flight — check these FIRST

| PR | Repo | What | State at wrap |
|---|---|---|---|
| #2244 | `livespec` | v203 ratification (spec + `history/v203/`) | open, auto-merge armed |
| #2245 | `livespec` | plan: supervisor + cache tiers | open, auto-merge armed |
| #2241 | `livespec` | plan: `cwoolley` account + tailnet diagnosis | open, auto-merge armed |
| #1374 | `livespec-dev-tooling` | the six ci-runner fixes | **MERGED** |
| #23 | `tailscale-admin` | tags + grant | **MERGED and applied** |

If any of the three open ones failed rather than merged, the likely cause is the
recurring flake in the next section, not the content.

---

## Traps that cost this session real time

1. **The isolation suite reports FALSE containment breaches from an unreadable
   cwd.** It drops privileges to `ci-runner`; a maintainer home is mode 0750, so
   podman dies before the container starts, probes capture empty output, and
   T7/T8/T10/T11 all report FAIL. **Same host, same commit: 5 fail from a home
   directory, 0 fail from `/tmp`.** Fixed at source (the script now runs from
   `/`), but if you run an older copy, run it from `/tmp`.
2. **`shellcheck` download from the GitHub releases CDN fails intermittently in
   CI** — `connection closed before message completed` during `mise install`,
   killing an unrelated check before it runs. **Observed TWICE this session** on
   different PRs, so it is a recurring flake, not a one-off. Per `AGENTS.md` a
   recurring failure mode must be fixed at its source (retry/cache in the mise
   step, or bake shellcheck into the CI image) rather than re-run. **This is
   owed work and is not yet filed as a work-item.**
3. **The `github_rate_limit_guard` hook denies looped or `--cache`-less GitHub
   reads**, and denies more aggressively while a Monitor is polling GitHub.
   Prefer reading evidence off the box (runner logs in `/tmp/*.log`, `_diag/`)
   over the GitHub API.
4. **The ratification digest binds the review to exact bytes.** If you amend a
   proposal after its Fable review, you MUST re-review — the digest covers the
   proposal bytes *and* the resulting-file bytes. Also: `reviewer_identity` must
   equal `reviewer_model` (both `fable`), and `reviewed_at` must be strictly in
   the past.
5. **Ephemeral runners leave `.runner`/`.credentials` behind** when they exit
   without taking a job, and re-registration then refuses with "already
   configured". Remove those files first. The real supervisor does not have this
   problem.

---

## Blocked on the maintainer (do not attempt unilaterally)

- **The GitHub App key on the box.** The real supervisor needs the
  `thewoolleyman-ci-runners` App private key, readable only by `ci-sup` via a
  `with-github-ci-runners-env.sh` wrapper. That wrapper resolves its token
  through 1Password with `systemd-creds`, and **`systemd-creds` encrypts against
  the HOST key — the factory host's blob cannot be copied.** The installer
  (`create-1password-env-wrapper.sh`, from `thewoolleyman/1password-env-wrapper`)
  must be run ON `poweredge-xubuntu` with the service-account token. Secret
  provisioning: maintainer only.
- **Installing the App on `thewoolleyman/homelab`** if homelab is to join the
  pool. Currently installed on `livespec` only.

---

## Open decisions not yet made

- **arm64 macOS runners.** The maintainer tagged Mac machines intending them to
  run CI, but the spec's Platform clause requires x86_64 Linux, so they are out
  of contract for gating CI. Either publish arm64 images and amend the clause,
  or scope them to the non-gating auxiliary lane the spec already carves out.
  Deliberately left open by the v203 proposal.
- **A one-word spec wording nit**, raised as non-blocking by the ratification
  reviewer and accepted as-is: v203 says *"no coordination between hosts is
  required, and none MUST be introduced"*, which parses ambiguously between a
  prohibition and a permission. `and coordination MUST NOT be introduced` fixes
  it. Would need a fresh propose-change.

---

## Remaining sequence, after the container blocker

1. Stand up the **real supervisor** (needs the App key above).
2. Move the three cache tiers onto `/var/cache/ci-runner` — the warm overlay
   lowers exist; the **local Actions cache** (removing GitHub's unraisable 10 GB
   cap) and a Nix store/binary cache do not.
3. Scale slots against 72 threads; the dockershim is mandatory above one slot.
4. Install observability (`ci-runner/observability/install-observability.sh` —
   the only sanctioned way).
5. Verify fork-approval tier per repo (`livespec` measured
   `all_external_contributors`, which is the strictest tier the spec requires).
6. **Then** flip `CI_RUNNER_LABELS` to `["self-hosted","local-ci"]`, one repo
   first, and prove the hosted fallback by unsetting it. **The flip comes last** —
   a job routed to absent capacity queues forever rather than failing.
7. File the supervisor and Actions-cache work as ledger children of
   `livespec-s43svm` after a scoping event. **Not yet done** — no scoping event
   exists and no children are filed.

---

## Housekeeping state at wrap

- Primary checkout `/data/projects/livespec` clean on `master`.
- No runner processes left on `poweredge-xubuntu`; zero runners registered.
- `CI_RUNNER_LABELS` = `["ubuntu-latest"]` (verified).
- Throwaway proof branches deleted; their worktrees removed.
- Worktrees still present at wrap: `spec-revise-v203`,
  `plan-supervisor-and-cache`, `plan-ssh-account-cwoolley`,
  `spec-selfhosted-pool` (livespec) and `fix-linger-race` (dev-tooling). Reap
  them once their PRs merge — `just reap-stale-worktrees <repo> --dry-run`
  first; the bare form REAPS without confirmation.
