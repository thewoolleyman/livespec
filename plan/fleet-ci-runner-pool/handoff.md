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

**`livespec` gating CI is LIVE on the self-hosted pool — `CI_RUNNER_LABELS`
flipped to `["self-hosted","local-ci"]` 2026-08-13, real matrix jobs from a real
open PR observed running on it, all three container-blocker layers fixed — and
the plan now explicitly extends to every OTHER livespec fleet repo, which today
has ZERO self-hosted capacity: the supervisor serves `repos=[thewoolleyman/livespec]`
only, and `--slots` is PER REPO, not a shared pool total, so adding repos is a
real capacity decision, not a flag flip.**

---

## Named next action

**Roll self-hosted CI out to the other livespec fleet repos.** `livespec` is
proven live (see "`livespec` is live" below); every OTHER fleet repo still runs
on paid GitHub-hosted capacity, and the supervisor design means that is a real
scoping decision, not a one-line change.

### Why this is not a flag flip

`ci-runner-supervisor.sh --repos "<space-separated owner/repo ...>" --slots N`
— `REPOS` accepts multiple repos natively (confirmed by reading the script:
`for repo in $REPOS; do for slot in $(seq 1 "$SLOTS_PER_REPO"); do ...`), but
**`--slots` is PER REPO, not a shared pool total.** The live unit is
`--repos thewoolleyman/livespec --slots 50` — 50 runner instance dirs. Naively
adding repos at the same slot count (`--repos "repo-a repo-b repo-c" --slots
50`) would create 150 instance dirs on a 72-thread host that the current
comment in `poweredge.conf` already says is sized so 50 "leaves headroom for
the OS and the rootless container engine" — i.e. 50 is close to this host's
ceiling for ONE repo, not a per-repo default that scales.

So the rollout needs an explicit **slots-per-repo** decision before touching
the unit, not just a longer `--repos` list. Candidates, not yet decided:

- Uneven allocation by repo size/CI-matrix width (e.g. `livespec` and
  `livespec-dev-tooling` — the two largest matrices — get more slots than a
  small binding repo like `livespec-driver-claude`).
- A flat low number per repo (e.g. 5–10) across all nine, sized to this host's
  thread count divided by repo count, with headroom preserved.
- A SEPARATE supervisor unit / systemd `runner@.service` instantiation per
  repo, so each repo's slot count can be tuned independently rather than one
  shared `SLOTS_PER_REPO` value across a single `--repos` invocation — check
  whether the script supports per-repo slot counts before assuming a single
  flat value is the only shape; if not, that is new work, not configuration.

### What else the rollout needs, per additional repo

1. **The GitHub App installed on that repo.** Per "Open decisions" below, the
   `thewoolleyman-ci-runners` App is installed on `livespec` only today. No new
   App or key — the existing App just needs installing on each additional repo
   (maintainer action, App settings), exactly as already noted for `homelab`.
2. **`CI_RUNNER_LABELS` set on that repo** to `["self-hosted","local-ci"]` (plus
   any per-host label the routing needs), the same variable flipped for
   `livespec`.
3. **Its CI workflow already using the `runs-on: ${{ fromJSON(vars.CI_RUNNER_LABELS
   || '["ubuntu-latest"]') }}` pattern.** `livespec`'s `ci.yml` does; VERIFY each
   other repo's workflow follows the same convention before assuming the
   variable alone routes it — `check-self-hosted-routing` (already fleet-wide in
   `livespec-dev-tooling`) is the mechanical check for this, run it per repo
   rather than assuming.
4. **The dockershim + bind-source + netns fixes on that host build.** They live
   in `livespec-dev-tooling/ci-runner/`, shared across every repo the same
   supervisor serves — ONE fix, ONE host, every repo it serves benefits. No
   per-repo dockershim work.
5. **Proof**, the same way `livespec` was proven here: re-run one real (not
   throwaway) PR's gating CI after flipping the label, confirm matrix jobs
   actually schedule on the pool (`in_progress` jobs on the run, not stuck
   `queued`), and prove the hosted fallback still works by unsetting the
   variable.

### Candidate repo list (from `.livespec-fleet-manifest.jsonc` / this repo's
`AGENTS.md` "Standing environment facts")

`livespec-dev-tooling`, `livespec-overseer`, `livespec-orchestrator-beads-fabro`,
`livespec-driver-claude`, `livespec-driver-codex`,
`livespec-orchestrator-git-jsonl`, `livespec-runtime`, `dolt-server` — the same
eight repos already tracked for the `MISE_HTTP_RETRIES` fan-out (trap 2), which
is worth doing IN THE SAME PASS as adding each repo to `--repos`, since both are
one-line-per-repo CI changes to the same set of repos.

**Do this AFTER deciding slots-per-repo, not before** — registering runners
against a repo whose slot allocation is undecided means re-registering them
(deleting and re-minting every JIT config) once the real number is chosen.

---

## `livespec` is live — how it was proven

`CI_RUNNER_LABELS` was flipped to `["self-hosted","local-ci"]` on `livespec`
2026-08-13, and PR #2248's real gating `CI` workflow was re-run under that
routing (not the throwaway `poweredge-container-proof` workflow used to prove
the container fixes) — matrix jobs (`check-lint`, `check-file-lloc`,
`check-check-mutation`, etc.) were observed `in_progress`, not stuck `queued`,
proving the pool schedules real gating work. **Verify the run's final
conclusion before treating this as fully closed** — `in_progress` at write time
is evidence the pool works, not yet evidence the whole matrix passed.

---

## Container blocker — RESOLVED, kept for reference

The section below records how a three-layer container blocker was found and
fixed. It is retained because the debugging method (bisect by environment, read
the FIRST failure not the loudest) generalizes, and because the eliminated/not-
eliminated distinctions cost real time to establish. **The blocker itself is
closed** — `livespec-dev-tooling` PR #1376 (merged) and #1378 (open, auto-merge
armed, already deployed to the host) fix all three layers, and a real
containerized job passed every step on the pool
(`poweredge-container-proof-2` run 31666955395, slot 9).

All three steps below are DONE — kept as a record of what "done" required, since
the same shape (fix on master, deploy to host, prove with a real job) applies to
every future dockershim change:

1. ~~Re-provision or hand-copy `ci-runner/dockershim/docker`...~~ Done —
   deployed via `scp` + `install -m 0755` directly (re-provisioning would have
   worked too, but the box was mid-diagnosis and a targeted copy proved each
   fix immediately without a full re-provision cycle).
2. ~~Set `CI_RUNNER_LABELS`...~~ Done for `livespec` — see "`livespec` is live"
   above.
3. ~~Confirm green, then prove the hosted fallback...~~ Confirmed for the
   throwaway proof workflow AND for a real gating PR; hosted-fallback proof
   (unset the variable, confirm hosted capacity picks the job back up) is
   NOT yet done for `livespec` — do this before or alongside the fleet-wide
   rollout above, since it is cheap and closes a real gap.

**Do NOT leave `CI_RUNNER_LABELS` pointed at the pool if a job fails** — jobs do
not fail on a missing runner, they QUEUE, and every merge then waits on a check
that never arrives. This applies to every repo added in the rollout above, not
just `livespec`.

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
7. **A throwaway proof workflow does NOT exercise every step a real gating
   workflow does — verify against real gating CI before declaring a fix
   proven.** `poweredge-container-proof` proved `prepare_job`/`cleanup_job`
   green and looked conclusive. Flipping `CI_RUNNER_LABELS` and re-running a
   REAL PR's `CI` workflow immediately surfaced a regression the proof workflow
   never exercised: a `docker exec ... git config --global` step (the "Trust
   workspace for git" step every real matrix job runs, that the throwaway
   workflow never included) failed with
   `could not lock config file /home/ci-runner/.gitconfig: No such file or
   directory`.

   Root cause: `docker create`'s real argv carries a BARE `-e HOME` (no
   `=value`) — docker's "pass through MY OWN HOME into the container"
   convention — and that gets BAKED into the container's persistent env at
   create time, becoming the default HOME for every LATER `exec` that doesn't
   specify its own. The scrubbed-environment fix (trap-adjacent, this same
   session) exports a REPAIRED host HOME before `create` runs so PODMAN's OWN
   process can resolve its storage — and that repaired value leaked through the
   SAME bare `-e HOME` flag into the container, corrupting what every later
   `exec` on that container saw as its home.

   Fixed by preserving the ORIGINAL (pre-repair) HOME and rewriting a bare
   `-e HOME` at `create` specifically back to an explicit `-e HOME=<original>`
   — scoped to `create` alone, since that is the only subcommand whose real
   argv carries this bare passthrough (`livespec-dev-tooling` PR #1378, second
   commit). **The general lesson: when a fix touches an env var that gets
   bare-passed into a container at create time, check whether the SAME var
   later governs anything read from INSIDE an already-running container — a
   fix for the client side can silently corrupt the container side through
   that one shared flag.**

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

0. ~~Deploy the merged shim fix and prove one containerized job~~ **DONE** —
   `livespec` proved on both the throwaway workflow and real gating CI.
0b. **Prove the hosted fallback for `livespec`** — unset `CI_RUNNER_LABELS` (or
   set it back to `["ubuntu-latest"]`) and confirm a job routes to hosted
   capacity again. Cheap, not yet done, do it before declaring `livespec` fully
   closed.
1. **Decide slots-per-repo, then roll self-hosted CI out to the other eight
   livespec fleet repos** — the Named next action above. This is now the
   critical-path item; everything numbered below was written when the plan's
   scope was `livespec`-only and is now correctly understood as "polish that
   applies fleet-wide once step 1 lands the other repos," not as blocking it.
2. Move cache tiers onto `/var/cache/ci-runner`; build the **local Actions
   cache** (removes GitHub's unraisable 10 GB cap) and a Nix store/binary cache.
   Do this AFTER the fleet-wide rollout, not before — a shared cache root that
   only one repo has ever populated is a smaller win than one every repo's jobs
   warm.
3. Install observability
   (`ci-runner/observability/install-observability.sh` — the only sanctioned
   way). This discharges v203's requirement that the fleet can observe a host
   that stopped taking jobs, and matters MORE once nine repos depend on the
   host than when one did.
4. Fan `MISE_HTTP_RETRIES=5` out to the remaining eight fleet repos (see trap
   2) — **do this in the SAME PASS as step 1**, since both are one-line CI
   changes to the same set of repos and reopening each repo's workflow twice is
   wasted motion.
5. File the supervisor/cache work, AND the fleet-wide rollout itself, as ledger
   children of `livespec-s43svm` after a scoping event. **Not done** — no
   scoping event exists, no children filed. The rollout is real enough scope
   now (nine repos, a slots-per-repo decision, a possible supervisor-script
   change) that it may warrant becoming its own scoped epic under this plan's
   anchor rather than staying an unscoped line item.

---

## Housekeeping at wrap

- `CI_RUNNER_LABELS` on `livespec` currently reads
  `["self-hosted","local-ci"]` — VERIFY this against the live variable before
  trusting this line; it has been flipped four times in this session alone
  (proof → revert-on-regression → re-flip-after-fix) and is exactly the kind of
  state a stale handoff misreports. If real gating CI is not passing when you
  read this, revert it immediately (trap 6) before doing anything else.
- **The supervisor is RUNNING and enabled**, serving `thewoolleyman/livespec`
  only — `repos=[thewoolleyman/livespec] slots=50`. Confirm from the startup
  log line (trap 5), never the unit file.
- `poweredge-container-proof-2` — the throwaway branch/workflow used to prove
  the container-blocker fixes — is STILL PRESENT (`.github/workflows/
  poweredge-container-proof.yml` on branch `poweredge-container-proof-2`).
  Delete both once `livespec-dev-tooling` PR #1378 is confirmed merged AND the
  hosted-fallback proof (remaining sequence 0b) is done — it may still be
  useful for one more regression check before then.
- Worktrees created this session, not yet cleaned up: `fleet-wide-ci-runner-
  rollout`, `poweredge-container-proof-2` (livespec); `fix-dockershim-scrubbed-
  env`, `fix-dockershim-bind-source-dirs`, `bake-shellcheck-and-close-lockstep-
  gap` (dev-tooling). Also still present from the prior round: `spec-revise-
  v203`, `plan-supervisor-and-cache`, `plan-ssh-account-cwoolley`, `spec-
  selfhosted-pool` (livespec), `fix-linger-race` (dev-tooling, ALREADY MERGED —
  see trap-adjacent note above about confirming a branch's tip is actually on
  master before reaping it).
  Reap once each branch's PR is confirmed merged — `just reap-stale-worktrees
  <repo> --dry-run` FIRST; the bare form reaps without confirmation.
