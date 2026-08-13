# Handoff — fleet-ci-runner-pool

**Ledger anchor:** `livespec-s43svm` (plan anchor, `thewoolleyman/livespec`).
Rewritten 2026-08-13 at session wrap, AFTER the supervisor went live, and
amended the same day once the container blocker was root-caused.

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

**The full self-hosted lane exists and is running — real supervisor, 50
auto-replenishing runners, correct labels — and the container blocker is now
ROOT-CAUSED AND FIXED on master (`livespec-dev-tooling` PR #1376); what remains
is deploying that fix to the host and proving one real containerized job, after
which `CI_RUNNER_LABELS` can move off `["ubuntu-latest"]`.**

---

## Named next action

**Deploy the merged dockershim fix to the host, then prove ONE real
containerized job green on the pool.**

The container blocker is root-caused and fixed on master
(`livespec-dev-tooling` PR #1376, merged 2026-08-13). What is NOT yet done is
the live exercise, which is what "done" requires here:

1. Re-provision or hand-copy `ci-runner/dockershim/docker` from
   `livespec-dev-tooling` master to `/usr/local/lib/ci-runner/dockershim/docker`
   on `poweredge-xubuntu` (`root:root`, 0755).
2. Set `CI_RUNNER_LABELS` to `["self-hosted","local-ci"]` on ONE repo and push a
   throwaway branch carrying a containerized job.
3. Confirm green, then prove the hosted fallback by unsetting the variable.

**Do NOT leave `CI_RUNNER_LABELS` pointed at the pool if that job fails** — jobs
do not fail on a missing runner, they QUEUE, and every merge then waits on a
check that never arrives.

### What the blocker actually was

The container hooks invoke the docker CLI with a SCRUBBED environment: the
runner's hook layer passes the JOB CONTAINER's env rather than the runner
account's. Dumping `env` from the shim on a live `start` call showed it receives
only `HOME` and `DOCKER_HOST`, with `HOME` pointing INSIDE the container.
Rootless podman derives real host paths from three variables and dies without
them:

| Missing / wrong | Symptom |
|---|---|
| `HOME=/github/home` | `cannot resolve /github/home: lstat /github: no such file or directory` |
| `PATH` absent | `setting up Pasta: could not find pasta … not found in $PATH` |
| `XDG_RUNTIME_DIR` absent | falls off the per-user runtime dir holding the rootless socket |

The fix restores all three in the dockershim from the invoking account.

### Corrections to this handoff's earlier round — READ BEFORE RE-INVESTIGATING

The previous round named the wrong layer, and its eliminated-hypotheses list was
partly wrong. Both cost real time and are corrected here so the errors are not
repeated:

- **The `TypeError: Cannot read properties of null (reading 'container')` is NOT
  the bug.** It is downstream noise. The FIRST failure is `PrepareJob`, whose
  real error is that the dockershim exited 1; the next step then reads a null
  container and throws. `CleanupJob` succeeds throughout, which is exactly why
  the hook layer looked healthy. Read `_diag/Worker_*.log` top-down and trust the
  FIRST failure, not the loudest one.
- **The runner/hooks version mismatch is real but irrelevant.** The runner did
  self-update 2.335.1 → 2.336.0 against hooks pinned at 0.8.1. That is not the
  cause, and chasing it first was a dead end.
- **`cannot resolve /github/home` was recorded as eliminated ("came from
  hand-launched runners; does not appear through the real supervisor"). That is
  WRONG** — it is the exact live error, on slot 33, in the real
  `poweredge-container-proof` job (run 31658073499). The earlier round reached
  the opposite conclusion because replaying the failing `docker create` BY HAND
  always succeeded — a hand shell simply has a real environment. **Bisect by
  environment, not by argv.**

These remain correctly eliminated, each re-confirmed by single-variable test:
the T10 dependency cache (its kill switch reproduces the failure identically
with the cache disabled), missing bind-source directories, the `-v=` equals
form, and `DOCKER_HOST`.

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
| #2244 | `livespec` | v203 ratification | **MERGED** |
| #2245 | `livespec` | plan: supervisor + cache tiers | **MERGED** |
| #2243 | `livespec` | round-5 delta verdict | **MERGED** |
| #2241 | `livespec` | plan: `cwoolley` + tailnet diagnosis | **MERGED** |
| #2249 | `livespec` | dependency-fetch retries + hosted uv cache | **MERGED** |
| #2246 | `livespec` | **this handoff** | open, auto-merge armed |
| #1374 | `livespec-dev-tooling` | six ci-runner fixes | **MERGED** |
| #1376 | `livespec-dev-tooling` | **the container-blocker fix** + recovered `9ee31dc` | **MERGED** |
| #23 | `tailscale-admin` | tags + grant | **MERGED, applied** |

Every one of the round-2 PRs was red on the shellcheck flake (trap 2), NOT on
content; re-running each on hosted capacity cleared them.

`livespec-dev-tooling` PR #1376 also recovered commit `9ee31dc`, which had been
pushed to `fix-linger-race` EIGHT MINUTES AFTER PR #1374 merged and so never
reached master, although it WAS hand-deployed to the live host. This handoff's
own "reap `fix-linger-race`" instruction would have discarded it. **Before
reaping any branch this plan touched, confirm master actually contains its
tip** — `git merge-base --is-ancestor <sha> origin/master`.

---

## Traps that cost this session real time

1. **The isolation suite reports FALSE containment breaches from an unreadable
   cwd.** Drops privileges to `ci-runner`; a maintainer home is 0750, so podman
   dies before the container starts and probes capture empty output. **Same
   host, same commit: 5 fail from a home dir, 0 fail from `/tmp`.** Fixed at
   source; run older copies from `/tmp`.
2. ~~**`shellcheck` download from the GitHub releases CDN fails
   intermittently**~~ — **FIXED AT SOURCE 2026-08-13**, three ways. The cause
   was that `.mise.toml` declares four tools and the CI image baked three:
   `shellcheck` had no baked ARG, so `mise install` re-fetched it from the
   releases CDN on EVERY containerized job in EVERY fleet repo. It reddened
   master in both `livespec` and `livespec-dev-tooling`, and — because
   `check-master-ci-green` blocks commits behind a red master — a red master
   then blocks the commit that would fix it. Watch for that deadlock shape.
   - `livespec-dev-tooling`: bakes `shellcheck`, and the lockstep gate now
     DERIVES its obligation from the `[tools]` table (every declared tool must be
     both ARG-pinned and `mise use -g`-installed), so a newly declared tool can
     never again become a silent per-job network fetch.
   - `livespec-dev-tooling`: every image-build fetch retries — `curl --retry 5
     --retry-all-errors` (its backoff is already exponential; `--retry-delay`
     would REPLACE that with a fixed sleep, so do not add it), `apt -o
     Acquire::Retries=5`, `ENV MISE_HTTP_RETRIES`/`UV_HTTP_RETRIES`, npm
     `--fetch-retries`.
   - `livespec` PR #2249: `MISE_HTTP_RETRIES=5` in CI (mise's own default is
     `http_retries = 0` — one attempt), plus the uv cache restored for the
     HOSTED lane, which had been dropped on reasoning that only holds for the
     self-hosted lane.

   **Still owed:** `MISE_HTTP_RETRIES` is set in `livespec` only; the other
   eight fleet repos still carry `UV_HTTP_RETRIES` with no mise equivalent.
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

## Remaining sequence

0. **Deploy the merged shim fix and prove one containerized job** — the Named
   next action above. Everything below stays blocked until a real job on the
   pool goes green, because until then the lane cannot carry gating CI.
1. Move cache tiers onto `/var/cache/ci-runner`; build the **local Actions
   cache** (removes GitHub's unraisable 10 GB cap) and a Nix store/binary cache.
2. Install observability
   (`ci-runner/observability/install-observability.sh` — the only sanctioned
   way). This discharges v203's requirement that the fleet can observe a host
   that stopped taking jobs.
3. **Then** flip `CI_RUNNER_LABELS` to `["self-hosted","local-ci"]`, one repo
   first, and prove the hosted fallback by unsetting it.
4. Fan `MISE_HTTP_RETRIES=5` out to the remaining eight fleet repos (see trap 2).
5. File the supervisor/cache work as ledger children of `livespec-s43svm` after
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
