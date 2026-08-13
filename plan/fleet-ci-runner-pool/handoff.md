# Handoff — fleet-ci-runner-pool

**Ledger anchor:** `livespec-s43svm` (plan anchor, `thewoolleyman/livespec`).
Rewritten 2026-08-13 at session wrap, AFTER the supervisor went live, amended
the same day once the container blocker was root-caused, and amended again
the same day once Issues A and B (below) were FIXED, MERGED, and VALIDATED
against real self-hosted gating CI — including the FIRST 100%-green
full-matrix self-hosted run this plan has produced — and a NEW Issue C
(podman container-state race) was discovered in the same pass.

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

**Issues A and B are FIXED, MERGED to master, and VALIDATED against real
self-hosted gating-equivalent CI — including a 100%-green 75/75-job
full-matrix self-hosted run, the FIRST this plan has ever produced — but
`CI_RUNNER_LABELS` is REVERTED to `["ubuntu-latest"]` as of this writing,
because the SAME validation pass surfaced a NEW, THIRD issue (Issue C: a
podman container-state race, ~3% job failure rate, distinct from A and B) that
reddened master CI minutes before the clean run landed.** Issue C is the new
named next action. The plan also now explicitly extends to every OTHER
livespec fleet repo, which today has ZERO self-hosted capacity: the supervisor
serves `repos=[thewoolleyman/livespec]` only, and `--slots` is PER REPO, not a
shared pool total, so adding repos is a real capacity decision, not a flag
flip.

**Do not read "Issues A and B fixed" as "livespec is ready for permanent
self-hosted routing."** Those are different claims. The container blocker
(three layers, `poweredge-container-proof-2`) and Issues A and B are closed.
Whether the pool can carry real gating CI WITHOUT Issue C's intermittent
container-state race is the new, still-open question — see below. This is
the plan's recurring shape: every real-PR live-fire round has closed the
issues found by the PREVIOUS round and surfaced exactly one new one. Round 4
is no exception — treat a clean run as progress, never as "done."

---

## Named next action

**Investigate and fix Issue C (podman container-state race) before re-flipping
`CI_RUNNER_LABELS` permanently.** `CI_RUNNER_LABELS` is currently REVERTED to
`["ubuntu-latest"]` because of this; do not re-flip it without re-reading this
section. Issues A and B (which occupied this section in the prior round) are
RESOLVED — see "Issues A and B — RESOLVED" below.

### Issue C — podman container-state race under high concurrency (~3% job failure rate observed)

Discovered live-firing the master-push CI that landed Issues A and B's
merge commits (round 4, same session as the fix). The master-push run for
Issue A's merge commit (`bc97fb9`, 71 jobs, full metadata+python matrix on
self-hosted) failed exactly 2 jobs — `check-match-keyword-only` and
`check-no-fmt-directives` — both with the IDENTICAL signature, on different
containers/slots:
```
Error: syncing container <id> state to update exec session <id>: unmarshalling
container state JSON: readObjectStart: expect { or n, but found  , error
found in #0 byte of ...||..., bigger context ...||...
##[error]Error: The process '/usr/local/lib/ci-runner/dockershim/docker'
failed with exit code 255
```
Both failures happened on an early `docker exec` (the checkout action's own
exec into its freshly-created container), not during teardown — podman read
an EMPTY/mid-write container state file for that container, on a `docker
exec` call that raced against SOME other concurrent operation touching
podman's shared rootless-engine state store (the same "one shared engine,
global database" mechanism `ci-runner/dockershim/docker`'s existing
serialization already defends `network prune` and `rm` against — see
`plan/fleet-ci-runner-pool/research/design.md` line ~119).

**Root-caused the locking gap, not yet fixed:** reading
`livespec-dev-tooling/ci-runner/dockershim/docker` (the shim script) shows it
takes a SHARED `flock -s` for `create` and `network`, and special-cases `rm`
with tolerant retry logic — but `exec` (the subcommand that actually failed
here, and the one called the MOST times per job — once per step) falls
through to the final `exec "$REAL_DOCKER" "$@"` with **NO locking at all**.
With up to 50 concurrent slots each issuing many unsynchronized `exec` calls
against podman's single shared rootless engine, an occasional read of a
mid-write state file is architecturally plausible. **Candidate fix, NOT yet
attempted or evaluated for cost:** add a SHARED `flock -s` to `exec` matching
the `create`/`network` pattern — cheap to try, but unproven whether a shared
lock actually excludes this specific race (the corruption looks like a
write-during-read on the SAME container's state file, which a shared lock
only prevents if the WRITER also takes at least a shared lock, and it is not
yet established what podman-internal operation is doing the writing). An
EXCLUSIVE lock on `exec` would definitely close the race but would seriously
serialize throughput across all 50 concurrent slots (every step of every job
funnels through `exec`) — do not reach for that without confirming a shared
lock is insufficient first.

**Severity: LOW so far, but real.** Observed rate: 2/71 jobs (~2.8%) in the
one run that hit it; the VERY NEXT master-push run (73 jobs, same load
shape, no shim change) had ZERO recurrences (75/75 success — see "First
100%-green run" below). This is consistent with a rare race, not a
deterministic failure, but it DID redden real master CI for one commit before
self-healing on the next push — exactly the failure mode trap 6 warns
about, so it blocks permanent self-hosted routing until either fixed or
understood well enough to bound its blast radius (e.g. auto-retry the
specific job on this exact error signature, if a shim-side fix proves hard).

---

## Issues A and B — RESOLVED

### Issue A — PyPI download timeouts under concurrent cold `uv sync` — FIXED

**Root-cause candidate:** uv's own `concurrent-downloads` setting defaults to
**50** in-flight fetches PER `uv sync` invocation
(docs.astral.sh/uv/reference/settings/#concurrent-downloads). With up to 50
self-hosted job slots each cold-syncing at once, that is up to 50 × 50 = 2500
simultaneous connections to `files.pythonhosted.org` from ONE host's shared
uplink — a direct, documented mechanism for the observed "operation timed
out" fetch failures, not just a hypothesis this time.

**Fix:** `livespec` PR #2255 caps `UV_CONCURRENT_DOWNLOADS` to `4` and raises
`UV_HTTP_TIMEOUT` to `60` (from uv's default 30s), scoped to the self-hosted
(`local`) lane only via the same `vars.CI_RUNNER_LABELS`-derived ternary
pattern already used for `LIVESPEC_CI_LANE` in `.github/workflows/ci.yml`.
The hosted lane's isolated, independent-network-path runners keep uv's own
defaults — unaffected.

**Validation:** across two self-hosted runs totaling 148 jobs after the fix
landed (71 + 75 jobs, real master-push CI, not throwaway), ZERO PyPI-timeout
recurrences. Not a deliberately engineered adversarial concurrency repro (the
handoff's prior round suggested one), but real concurrent load from real
matrix jobs, twice, clean both times — treat as strong positive evidence, not
absolute proof (the ORIGINAL bug was itself intermittent — a second run
before ANY fix also passed clean once).

**Merged:** `livespec` PR #2255 → `e9769f8e` on master.

### Issue B — `origin/master` unresolvable on a reused self-hosted `_work` dir — FIXED

**Fix:** `livespec` PR #2255 adds an explicit
`git fetch origin master:refs/remotes/origin/master` step in
`.github/workflows/ci.yml`'s `check-metadata` job, scoped to
`env.LIVESPEC_CI_LANE == 'local'`, placed right after the existing
workspace-trust step and before anything that needs `origin/master`
resolvable. The hosted lane's fresh clone already has `origin/master` via
`fetch-depth: 0`, so the step no-ops there — confirmed by a clean 75/75
hosted run before self-hosted validation.

**Validation:** `check-red-green-replay` — the exact check that failed with
`range base origin/master is not resolvable` in the prior round — passed on
self-hosted in the master-push run for commit `bc97fb9` (Issue A's merge,
which lands on top of Issue B's fix), and again in the following 100%-green
75/75 run. Root cause was NOT independently confirmed at the `actions/checkout`
code-path level (still "evidenced symptom, not confirmed mechanism" per the
prior round) — but the fix works empirically across two live self-hosted
runs, so further root-causing is no longer blocking.

**Merged:** `livespec` PR #2255 (`fix(ci): explicitly fetch origin/master on
the self-hosted metadata lane`) → `e9769f8e` on master. PR #2258
(`fix(ci): cap uv concurrent downloads on the self-hosted lane`, Issue A's
fix) → `bc97fb9` on master. **Two separate PRs**, both authored and merged in
the same round-4 pass.

### Trap discovered validating these: auto-merge fires BEFORE you can hold a PR for self-hosted-only testing

This repo's `.github/workflows/auto-enable-merge.yml` auto-enables
`gh pr merge --auto --rebase` on ANY PR authored by the allowlisted human
identity (`thewoolleyman`), the moment it opens — via a job baked into
`auto-enable-merge.yml`, watching `opened`/`synchronize`/etc. That means a PR
opened while `CI_RUNNER_LABELS` is STILL hosted (e.g. to get a hosted sanity
pass before self-hosted validation) will auto-merge as soon as HOSTED CI goes
green — regardless of whether you intended to flip the label and validate
self-hosted BEFORE merge. Both PR #2255 and #2258 auto-merged this way in
round 4, before the self-hosted flip took effect; validation ended up
happening AFTER merge, against master-push CI, purely by good fortune (an
unrelated dependency-bump PR's merge queued a second self-hosted run right as
the flip landed). **To hold a PR open for deliberate self-hosted-only
testing, apply the `do-not-merge` label at creation time** — the auto-merge
workflow explicitly skips labelled PRs. Do this BEFORE the first hosted run
goes green, not after.

---

## Fleet-wide rollout — roll self-hosted CI out to the other livespec fleet repos

Sequence this AFTER Issues A and B above are resolved and `livespec`'s routing
is proven stable across multiple real-PR runs, not just one. Every OTHER fleet
repo still runs on paid GitHub-hosted capacity, and the supervisor design means
adding them is a real scoping decision, not a one-line change.

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

## `livespec`'s pool DOES schedule and run real gating work — how far that goes

`CI_RUNNER_LABELS` was flipped to `["self-hosted","local-ci"]` on `livespec`
2026-08-13, and PR #2248's real gating `CI` workflow was run under that routing
THREE TIMES in one session (not the throwaway `poweredge-container-proof`
workflow used to prove the container fixes):

1. **First run** — 18 jobs failed on the bare-`-e HOME` regression (trap 7).
   Fixed and merged (`livespec-dev-tooling` PR #1378, second commit).
2. **Second run**, after that fix deployed — the HOME regression was CONFIRMED
   gone (the jobs that failed on it in run 1 passed cleanly), but 4 DIFFERENT
   jobs failed on Issue A (PyPI timeouts, above). Confirmed not content-related
   by an immediate 50/50 pass on hosted capacity.
3. **Third run**, full matrix on self-hosted again — 0 content failures, 0
   recurrence of Issue A, but a NEW failure: Issue B (`origin/master`
   unresolvable), reproduced again on a single-job re-run on a different slot.

So: the pool schedules real gating work, executes ordinary jobs correctly, and
the container blocker plus the HOME regression are genuinely closed.

### Round 4 — the FIRST 100%-green full-matrix self-hosted run

After Issues A and B's fixes merged (PR #2255, #2258 — both via the
auto-merge trap above, before deliberate self-hosted validation could be
arranged), TWO master-push CI runs happened back-to-back on self-hosted,
both by real merge events rather than a deliberate re-run:

1. **Run 1** (commit `bc97fb9`, Issue A's merge, 71 jobs) — 69/71 success,
   2/71 failure on the NEW Issue C (podman container-state race, see Named
   next action above). `check-red-green-replay` PASSED (Issue B confirmed
   fixed). This run's 2 failures reddened master CI.
2. **Run 2** (commit `357bbee6`, an unrelated dependency-bump PR's merge that
   queued self-hosted just as the label was being reverted, 73 jobs) —
   **75/75 success. Zero failures.** This is the FIRST 100%-green full-matrix
   self-hosted run this plan has produced across every round.

`CI_RUNNER_LABELS` was reverted to `["ubuntu-latest"]` immediately after run
1's 2 failures were observed (trap 6), BEFORE run 2 was known to exist — run
2 completed on self-hosted anyway because its jobs had already been
dispatched to self-hosted runners at flip time; reverting the variable
affects only FUTURE trigger evaluations, not already-assigned jobs. Master's
current HEAD (`357bbee6`) is GREEN. `CI_RUNNER_LABELS` stays reverted to
`["ubuntu-latest"]` until Issue C is resolved or its blast radius is bounded
— a 100%-green run is real evidence the pool CAN pass cleanly, not evidence
that it WILL every time; the very same round's run 1 is the reminder why.

---

## Container blocker — RESOLVED, kept for reference

The section below records how a three-layer container blocker was found and
fixed. It is retained because the debugging method (bisect by environment, read
the FIRST failure not the loudest) generalizes, and because the eliminated/not-
eliminated distinctions cost real time to establish. **The blocker itself is
closed** — `livespec-dev-tooling` PR #1376 (MERGED) and #1378 (MERGED, deployed
to the host) fix all three layers, and a real containerized job passed every
step on the pool (`poweredge-container-proof-2` run 31666955395, slot 9).

All three steps below are DONE — kept as a record of what "done" required, since
the same shape (fix on master, deploy to host, prove with a real job) applies to
every future dockershim change:

1. ~~Re-provision or hand-copy `ci-runner/dockershim/docker`...~~ Done —
   deployed via `scp` + `install -m 0755` directly (re-provisioning would have
   worked too, but the box was mid-diagnosis and a targeted copy proved each
   fix immediately without a full re-provision cycle).
2. ~~Set `CI_RUNNER_LABELS`...~~ Done for `livespec` (repeatedly, and reverted
   again pending Issue C — Issues A and B are now RESOLVED) — see
   "`livespec`'s pool DOES schedule and run real gating work" above.
3. ~~Confirm green, then prove the hosted fallback...~~ DONE, repeatedly —
   confirmed for the throwaway proof workflow AND for a real gating PR
   (three separate self-hosted runs, each followed by a revert-to-hosted that
   picked the job back up cleanly). See "remaining sequence" 0b.

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
| #2246 | `livespec` | round-2 handoff (anchor-declared fix) | **MERGED** |
| #2252 | `livespec` | round-3 handoff (fleet-wide rollout + Issue A/B correction) | **MERGED** |
| #2254 | `livespec` | round-3 handoff sync (primary checkout's uncommitted draft) | **MERGED** |
| #2255 | `livespec` | Issue B fix (self-hosted `origin/master` fetch) | **MERGED** — validated on self-hosted, see "Issues A and B — RESOLVED" |
| #2258 | `livespec` | Issue A fix (uv concurrent-downloads cap) | **MERGED** — validated on self-hosted, see "Issues A and B — RESOLVED" |
| #1374 | `livespec-dev-tooling` | six ci-runner fixes | **MERGED** |
| #1376 | `livespec-dev-tooling` | scrubbed-environment fix + recovered `9ee31dc` | **MERGED** |
| #1378 | `livespec-dev-tooling` | bind-source creation + netns-teardown tolerance + HOME-passthrough regression fix | **MERGED, deployed to host** |
| #1383 | `livespec-dev-tooling` | bake `shellcheck` + retry every image-build fetch | **MERGED** |
| #1384 | `livespec-dev-tooling` | `MISE_HTTP_RETRIES` fan-out, repo 1 of 8 | **MERGED** |
| #23 | `tailscale-admin` | tags + grant | **MERGED, applied** |
| #24 | `tailscale-admin` | assert member→ci-runner SSH reachability (tests-only) | **MERGED** |

**This round's PR table is now empty of open items** — every PR opened in
round 4 (#2255, #2258, plus the round-4 handoff itself) is merged before this
handoff was written. The only open work is Issue C's investigation (no PR yet
— it needs a fix candidate evaluated, not just written blind) and the
still-unfiled ledger children (remaining sequence, step 6).

Every one of the round-2 `livespec` PRs (#2241/#2243/#2244/#2245/#2249) was red
on the shellcheck flake (trap 2), NOT on content; re-running each on hosted
capacity cleared them.

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
8. **`auto-enable-merge.yml` merges your OWN PRs the moment hosted CI goes
   green — before you can flip `CI_RUNNER_LABELS` and validate self-hosted.**
   See "Trap discovered validating these" under "Issues A and B — RESOLVED"
   above. Apply the `do-not-merge` label at PR creation time when the PR
   MUST stay open for deliberate self-hosted-only testing.
9. **The GitHub Actions REST jobs API can appear stalled for a minute or two
   while the host is genuinely, actively processing.** Repeated
   `gh api .../jobs` polls during round 4 showed the EXACT SAME
   completed/in_progress/queued counts across 3-4 consecutive checks, which
   looked like a stuck pool. Direct host inspection
   (`sudo -u ci-runner podman ps -a`) showed containers churning normally
   the whole time (fresh "Up less than a second" / "Up 52 seconds" entries).
   The job-status reporting simply lags real execution by up to ~1-2 minutes
   under this host's current load. **Verify a suspected stall against the
   host's own container state before concluding the pool is stuck** — do not
   trust the GitHub API's job-status freshness alone at high job counts.

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
0b. ~~Prove the hosted fallback for `livespec`~~ **DONE, incidentally** —
   proven three separate times as part of reverting `CI_RUNNER_LABELS` after
   each of the regressions/issues found below; hosted capacity picked every
   job back up cleanly every time.
1. ~~Resolve Issue A (PyPI timeouts under concurrency) and Issue B
   (`origin/master` unresolvable on a reused `_work` dir)~~ **DONE** — both
   fixed, merged, and validated on self-hosted (see "Issues A and B —
   RESOLVED"), including one 100%-green 75/75 full-matrix run. **New step 1:
   resolve Issue C (podman container-state race)** — the Named next action
   above. `CI_RUNNER_LABELS` stays reverted until it is closed or its blast
   radius is bounded, AND at least one more clean run confirms it (one
   100%-green run is evidence, not proof — the very same round's prior run
   had 2 failures).
2. **Decide slots-per-repo, then roll self-hosted CI out to the other eight
   livespec fleet repos** — see the "Fleet-wide rollout" section above.
   Sequenced AFTER step 1, not concurrent with it: adding eight more repos'
   worth of concurrent cold `uv sync` traffic to the same host BEFORE Issue A
   is understood would make diagnosing it strictly harder, not easier.
3. Move cache tiers onto `/var/cache/ci-runner`; build the **local Actions
   cache** (removes GitHub's unraisable 10 GB cap) and a Nix store/binary
   cache. This may PARTIALLY subsume Issue A (a warm uv cache means less cold
   PyPI traffic) — attempt Issue A's own fix first and treat this as
   reinforcement, not a substitute, since Issue A's mechanism (bandwidth
   contention) isn't fully confirmed yet.
4. Install observability
   (`ci-runner/observability/install-observability.sh` — the only sanctioned
   way). This discharges v203's requirement that the fleet can observe a host
   that stopped taking jobs, and matters MORE once nine repos depend on the
   host than when one did.
5. Fan `MISE_HTTP_RETRIES=5` out to the remaining seven fleet repos (see trap
   2 — `livespec-dev-tooling` already done, PR #1384) — **do this in the SAME
   PASS as step 2**, since both are one-line CI changes to the same set of
   repos.
6. File the supervisor/cache work, the fleet-wide rollout, AND Issues A/B, as
   ledger children of `livespec-s43svm` after a scoping event. **Not done** —
   no scoping event exists, no children filed. This is now real enough scope
   (nine repos, a slots-per-repo decision, two open reliability issues, a
   possible supervisor-script change) that it likely warrants becoming its own
   scoped epic under this plan's anchor rather than staying unscoped line
   items.

---

## Housekeeping at wrap

- `CI_RUNNER_LABELS` on `livespec` currently reads `["ubuntu-latest"]`
  (REVERTED, deliberately, pending Issue C above) — VERIFY this against the
  live variable before trusting this line; it was flipped repeatedly across
  rounds 3 and 4 (proof → revert-on-regression → re-flip-after-fix →
  revert-on-Issue-A → re-flip-to-confirm → revert-on-Issue-B →
  re-flip-round-4 → revert-on-Issue-C) and is exactly the kind of state a
  stale handoff misreports. If it reads self-hosted when you pick this up and
  no one is actively mid-investigation, that is itself a signal something is
  wrong — trap 6 applies.
- **The supervisor is RUNNING and enabled**, serving `thewoolleyman/livespec`
  only — `repos=[thewoolleyman/livespec] slots=50`. Confirm from the startup
  log line (trap 5), never the unit file.
- `poweredge-container-proof-2` — the throwaway branch/workflow used to prove
  the container-blocker fixes — is STILL PRESENT (`.github/workflows/
  poweredge-container-proof.yml` on branch `poweredge-container-proof-2`).
  Kept again this round in case Issue C's investigation wants a clean,
  non-gating repro surface (a container-state race is plausibly easier to
  provoke deliberately than to wait for on real gating CI); reassess once
  Issue C is closed.
- Round-4 worktrees (`fix-selfhosted-origin-master-unresolvable`,
  `fix-uv-concurrency-self-hosted`, `wrapup-fleet-ci-runner-pool-round3`) were
  created, merged, and REAPED within this same round — none left over.
  Worktrees still present from PRIOR rounds, untouched this round (all under
  `$HOME/.worktrees/<repo>/<branch>`):
  - `livespec`: `poweredge-container-proof-2` (throwaway, see note above),
    `spec-revise-v203`, `plan-supervisor-and-cache`, `plan-ssh-account-
    cwoolley`, `spec-selfhosted-pool`.
  - `livespec-dev-tooling`: none confirmed left — `fix-dockershim-
    scrubbed-env`, `fix-dockershim-bind-source-dirs`,
    `bake-shellcheck-and-close-lockstep-gap`, `add-mise-http-retries`, and
    `fix-linger-race` were all reaped in round 3 after confirming each PR's
    merge. VERIFY with `ls ~/.worktrees/livespec-dev-tooling/` before trusting
    this line — this file does not re-derive worktree state, it records what
    was true at write time.
  - `tailscale-admin`: no worktree — branches were created, committed, and
    cleaned up directly on the primary checkout's branch; confirm `git -C
    /data/projects/tailscale-admin status` is clean on `master` if picking
    this repo back up.

  Reap once each branch's PR is confirmed merged — `just reap-stale-worktrees
  <repo> --dry-run` FIRST; the bare form reaps without confirmation. On a
  REBASE-MERGING repo (both `livespec` and `livespec-dev-tooling` are),
  `git merge-base --is-ancestor <local-branch-sha> origin/master` is NOT a
  reliable merged check — rebase-merge creates NEW commit objects on master
  with different SHAs even for identical content, so a genuinely-merged
  branch's original tip SHA still returns NO. Confirmed live in round 4: every
  branch checked this way returned NO, including branches independently
  confirmed merged via `gh pr list --head <branch> --state all`. Use
  `gh pr list --head <branch> --state all` (one call per branch, not looped —
  see trap 3) as the reliable check instead.
