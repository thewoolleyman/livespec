# Handoff — fleet-ci-runner-pool

**Ledger anchor:** `livespec-s43svm` (plan anchor, `thewoolleyman/livespec`).
Rewritten 2026-08-13, round 6, in the same continuous session as rounds 1-5.
Round 6 (this round), driven by the maintainer's explicit direction, did FOUR
things: (1) installed the missing GitHub App coverage for the 8th fleet repo
via the maintainer's own logged-in browser session, (2) chose and executed a
"full CI-matrix width per repo" slot-allocation strategy (correcting an
earlier wrong mental model about slots needing a shared/summed cap), (3)
found and fixed THREE more real infrastructure bugs live (a per-repo
shallow-fetch bug propagated to 5 more repos, a kernel keyring quota
ceiling, and a raised dockershim retry bound), and (4) completed the
fleet-wide rollout for 5 of the 6 remaining self-hosted-eligible repos,
proven with real green master-push CI on every one. One repo
(`livespec-console-beads-fabro`) has labels set and slots provisioned but is
blocked from a live proof by an unrelated, pre-existing gate failure on its
own master.

> **Why this file exists.** The `plan` operation's prose says it never authors
> `handoff.md` and that handoffs are ledger comments. That still governs the
> PLAN. This file exists because the session overseer respawns a fresh session
> with one instruction — read this path and follow it — so it is the only thing
> that survives. Durable plan reasoning lives in
> `plan/fleet-ci-runner-pool/research/design.md` and the ledger timeline
> (`livespec-s43svm` plus its four children, `livespec-s43svm.1`–`.4`).

---

## Read first

1. This file, start to finish — it supersedes the round-5 handoff entirely.
2. `plan/fleet-ci-runner-pool/research/design.md` — pool model, label scheme,
   supervisor, cache tiers, sequencing, homelab handoff (still accurate;
   round 6 did not touch cache tiers).
3. `SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
   requirements" (v203).
4. `.ai/ci-gate-discipline.md` — binds anything touching a merge-blocking gate.
5. Ledger children `livespec-s43svm.1` (fleet-wide rollout — now MOSTLY DONE,
   see below), `.2` (cache tier 1 relocation, untouched), `.3` (local Actions
   cache, untouched), `.4` (Nix store, untouched).

---

## State in one sentence

**6 of the 9 livespec fleet repos are now on PERMANENT self-hosted CI
routing, each proven green on a real self-hosted master-push run**:
`livespec` (50 slots), `livespec-driver-codex` (67), `livespec-driver-claude`
(66), `livespec-orchestrator-git-jsonl` (66), `livespec-overseer` (65),
`livespec-runtime` (64). A 7th (`livespec-console-beads-fabro`, 16 slots) has
`CI_RUNNER_LABELS` set and its slots provisioned but has NOT been proven live
— an unrelated pre-existing `check-fork-drift` gate failure on its own
current master blocks any push there right now (see "console-beads-fabro
blocker" below). The remaining 2 (`livespec-orchestrator-beads-fabro`,
`dolt-server`) are DELIBERATELY, PERMANENTLY excluded from self-hosted
routing by their own repos' documented policies — not gaps, not TODOs.

**What changed this round vs the round-5 handoff's understanding:**
- The round-5 handoff's claim that GitHub App installation blocked "7 of 8"
  repos was WRONG in degree (though right in kind) — 7 of those 8 already had
  the App installed; only `livespec-overseer` genuinely needed it. Fixed by
  the maintainer directly via their own browser session (see below).
- The round-5 handoff's rollout table listed `livespec-orchestrator-beads-fabro`
  (96-job matrix) as a rollout candidate. It is NOT — its own `ci.yml`
  documents a deliberate two-trust-tier security boundary against
  self-hosted routing, discovered live this round. This drops the eligible
  fleet-wide rollout scope from "8 repos" to "7."
- The round-5 handoff's Issue-C shallow-fetch fix (`livespec` PR #2261) was
  assumed fleet-portable. It is NOT automatically fleet-wide — it lives in
  ONE repo's `ci.yml`, and every other repo needed the exact same fix ported
  into ITS OWN `ci.yml` individually. Done this round for 5 repos (see
  below); confirmed NOT needed for a 6th (`console-beads-fabro`, which has no
  `fetch-depth: 0` checkouts and no `check-red-green-replay` job at all).
- A THIRD real infrastructure ceiling was found and fixed this round: the
  Linux kernel's per-UID keyring quota (`kernel.keys.maxkeys`), a fleet-wide
  (not per-repo) ceiling because every self-hosted container across every
  repo runs under the single shared `ci-runner` account.

---

## GitHub App installation — RESOLVED

Confirmed directly via `https://github.com/settings/installations/146033367`
(the `thewoolleyman-ci-runners` App): 7 of the 8 non-`dolt-server` fleet repos
ALREADY had the App installed (`livespec`, `livespec-orchestrator-git-jsonl`,
`livespec-dev-tooling`, `livespec-runtime`, `livespec-orchestrator-beads-fabro`,
`livespec-driver-claude`, `livespec-console-beads-fabro`, `livespec-driver-codex`
— 8 entries, one of which, `livespec-orchestrator-beads-fabro`, turned out to
be excluded from routing anyway for the unrelated security reason below). Only
`livespec-overseer` was genuinely missing App coverage. The maintainer added
it themselves via their own logged-in Chrome session (browser automation
driven from a scratch worktree, per the `primary_checkout_playwright_guard.py`
requirement that Playwright work happen outside the governed primary
checkout). Confirmed via GitHub's own "Okay, thewoolleyman-ci-runners was
updated" toast and the installation's repository list.

**This means the automation PAT's own 403/401 on `user/installations` and
`app/installations` (still true, re-confirmed this round) was NEVER a
reliable signal for "is the App installed on repo X" — it only reflects that
the PAT itself lacks App-management scope, which is a permanent, expected
property of that token, not a per-repo installation gap.** Future rounds:
verify actual App coverage via the web UI or a JWT-authenticated call, never
via the automation PAT's installations endpoints.

---

## `livespec-orchestrator-beads-fabro` is PERMANENTLY excluded from self-hosted routing

Discovered live while surveying job structures for the width test (NOT a gap
anyone should try to close). Its `.github/workflows/ci.yml` carries an
explicit, deliberate comment block:

> "RUNNER ROUTING — deliberately PLAIN `runs-on: ubuntu-latest` everywhere.
> Do NOT 'restore uniformity' by introducing the flippable
> `runs-on: fromJSON(vars.CI_RUNNER_LABELS...)` form... This repo hosts the
> fleet's PRIVILEGED on-demand gate-runner lane... Adding a contained
> `local-ci` lane here is a two-trust-tier security decision the maintainer
> owns, and it is deliberately NOT being made."

Treat this exactly like `dolt-server`'s `check-no-workflow-edits` policy: a
documented, standing boundary, not a TODO. Its 96-job matrix is the largest
in the fleet and will NEVER be part of this pool unless the maintainer
explicitly revisits that security decision.

---

## Slot-allocation strategy — corrected mental model, then decided

**The wrong model (mine, corrected mid-round by the maintainer's question):**
early in this round I proposed shrinking `livespec` from its proven 50 slots
down to ~7 so that a SUM across all repos stayed near 50, reasoning that the
"~50-concurrent-container ceiling" was a shared budget. The maintainer asked
directly: "why does it have to be per-repo, why can't it be total runners in
the pool... doesn't supervisor support that?"

**The correction:** reading `ci-runner-supervisor.sh` directly settled it —
each "slot" is a permanently-repo-bound background loop
(`for repo_spec in $REPOS; do ... for slot in $(seq 1 "$repo_slots"); do
( while :; do run_one "$repo" "$slot" || sleep 10; done ) & ...`). Slots are
NEVER shared across repos — an idle slot in repo A's allocation was never
available to repo B anyway, so there is no pool to divide. The only real
constraint is peak concurrent CONTAINERS for any ONE repo's own burst,
because that's what stresses the shared rootless podman engine (the Issue-C
SQLite race).

**The decision (the maintainer's, after that correction and a follow-up
explanation of the podman race's actual exposure — see below): give every
repo its own FULL measured CI-matrix width, no shared cap.** Accepted
trade-off: this pushes peak concurrent containers for wider repos above the
~50 previously proven safe (up to 67 this round), which is new territory for
the still-not-upstream-fixed podman SQLite race. Mitigated by raising the
dockershim's bounded retry from 3 to 10 attempts (see below).

**One clarifying exchange worth preserving:** the maintainer asked "it's only
one hit per job, right?" — i.e. is the podman-race exposure one attempt per
CI job. NO — verified directly against `livespec`'s own `check-metadata`
job: each individual job runs ~11 steps, and per the dockershim's own
comment "`exec` is the highest-volume, most latency-sensitive operation in
the whole shim (every job step runs one)" — so exposure is roughly
STEPS-PER-JOB × JOB-COUNT, not job-count alone. A 67-job matrix is closer to
~700+ independent exec calls per run, not 67.

---

## Dockershim exec retry raised 3 → 10

`livespec-dev-tooling` PR #1392 (MERGED). Given the exposure math above,
raised the Issue-C bounded-retry cap in `ci-runner/dockershim/docker` from 3
attempts to 10, scoped to the exact same error signature as before (never
masks a genuinely different failure). Deployed to
`/usr/local/lib/ci-runner/dockershim/docker` on `poweredge-xubuntu` via
`scp` + `install -m 0755` (checksums verified to match the source file
exactly). Validated: shellcheck clean, `dockershim-exit-tests.sh` 25/25
passing unchanged, and implicitly proven by the width tests below (zero
retry-signature hits across the whole round, including a ~394-slot mass
supervisor restart and multiple full-width master-push runs).

---

## The shallow-fetch bug is PER-REPO, not fixed fleet-wide by one PR — discovered and fixed live

**Discovery:** firing the FIRST real self-hosted `pull_request`-event proof
on `livespec-driver-codex` (PR #437, testing its 67-slot width) reproduced
the EXACT round-4/5 "Issue C shallow-fetch merge-commit bug" signature —
`check-red-green-replay` failed with `range base origin/master is not
resolvable`. This was surprising because that bug was supposedly already
fixed (`livespec` PR #2261). Root cause: PR #2261 only ever edited
`livespec`'s OWN `.github/workflows/ci.yml`. Every other repo has its own
separate `ci.yml` with its own `actions/checkout` step, so the fix never
propagated.

**Fix, ported verbatim (the same `git fetch --unshallow origin` pattern,
guarded by `--is-shallow-repository`) into 5 repos' `ci.yml` files, each as
its own PR, each MERGED:**

| Repo | PR | Where inserted |
|---|---|---|
| `livespec-driver-codex` | #437 | `check`, `check-doctor-static`, `check-red-green-replay` (3 separate jobs) |
| `livespec-driver-claude` | #470 | same 3-job structure as driver-codex |
| `livespec-orchestrator-git-jsonl` | #608 | single `check-metadata` matrix job (same structure as `livespec` itself) |
| `livespec-overseer` | #880 | single `check-metadata` matrix job |
| `livespec-runtime` | #518 | single `check-metadata` matrix job |

`livespec-console-beads-fabro` was checked and confirmed to NOT need this
fix — zero `fetch-depth: 0` checkouts anywhere in its `ci.yml`, no
`check-red-green-replay` job at all, so the bug's preconditions don't exist
there.

**Execution note — a dispatched agent CAN get stuck committed-but-unpushed
without reporting it (matches an existing traps-list entry, reconfirmed
twice this round):** both the `livespec-driver-claude` shallow-fetch-fix
agent and, later, the `livespec-driver-claude` self-hosted-proof agent got
stuck exactly at the same point — commit present, `git push` never
completed, agent reporting idle/available in a loop with no useful content.
Both times: verified the commit was correct directly (`git show --stat`,
`grep`, YAML validation), stopped the stuck agent
(`TaskStop`), and pushed + opened the PR manually. Don't trust an idle
notification as "done" — check the actual worktree state.

**Validation:** `livespec-driver-codex` PR #437 re-ran clean after the fix —
`check-red-green-replay` passed. (One OTHER job then failed on a completely
unrelated new issue — the keyring quota, see next section — and PR #437 is
now fully green, 67/67, after both fixes landed.)

---

## A THIRD infrastructure ceiling found live: the kernel keyring quota

**Discovery:** in the SAME `livespec-driver-codex` PR #437 width proof
(after the shallow-fetch fix), one job (`check-keyword-only-args`) failed
with:
```
crun: create keyring "...": Disk quota exceeded
```
The message is misleading — NOT disk space. `crun` allocates a Linux kernel
session keyring per container start, and the kernel enforces a per-UID quota
(`/proc/sys/kernel/keys/maxkeys`, default **200**). EVERY self-hosted
container across EVERY repo on this host runs under the single shared
`ci-runner` account, so this is a FLEET-WIDE ceiling, not per-repo — the
first time this ever surfaced was the first time TWO repos' slots were
concurrently active (`livespec`'s 50 + `livespec-driver-codex`'s 67).
Confirmed directly: `sudo -u ci-runner cat /proc/keys | wc -l` read 178/200
in use at the time of the failure.

**Fix:** `/etc/sysctl.d/60-ci-runner-keyring.conf` on `poweredge-xubuntu`:
```
kernel.keys.maxkeys = 2000
kernel.keys.maxbytes = 200000
```
Applied live (`sysctl -p`) and persisted (survives reboot). Sized ~4-5×
above the fleet's current full-width total (~394 slots as of this round;
`livespec-orchestrator-beads-fabro` never counts toward this since it's
permanently excluded) for headroom.

**Validation:** re-ran the failed job on PR #437 — passed. PR #437 then went
fully green (67/67). No keyring-quota failures observed across the rest of
the round, including the ~394-slot mass supervisor restart described below.

---

## Fleet-wide rollout execution — provisioning, supervisor config, and proof

### Instance-directory provisioning

Each repo needs its own set of `/home/ci-runner/runners/<reposlug>-<N>/`
instance directories (hard-linked copies of the shared Actions-runner
install) BEFORE the supervisor can start any slot for it — this was
discovered live (the very first attempt to add `livespec-driver-codex` to
the supervisor's `--repos` produced instant `ExecStartPre=+/usr/bin/rm -rf
.../runners/%i/_work (code=exited, status=200/CHDIR)` failures for every
slot, because the directories simply didn't exist).

Provisioned via `livespec-dev-tooling/ci-runner/provision-ci-runner.sh`
(idempotent, safe to re-run, scoped by `CI_RUNNER_SLOTS` +
`CI_RUNNER_REPOSLUGS` env vars — re-running it for a NEW repo/slot-count is
a no-op for every already-provisioned repo, confirmed live: `0 upgraded, 0
newly installed` on every re-run's package-install step). Ran once per repo,
each with its own measured slot count:

```
CI_RUNNER_SLOTS=67 CI_RUNNER_REPOSLUGS=thewoolleyman-livespec-driver-codex
CI_RUNNER_SLOTS=66 CI_RUNNER_REPOSLUGS=thewoolleyman-livespec-driver-claude
CI_RUNNER_SLOTS=66 CI_RUNNER_REPOSLUGS=thewoolleyman-livespec-orchestrator-git-jsonl
CI_RUNNER_SLOTS=65 CI_RUNNER_REPOSLUGS=thewoolleyman-livespec-overseer
CI_RUNNER_SLOTS=64 CI_RUNNER_REPOSLUGS=thewoolleyman-livespec-runtime
CI_RUNNER_SLOTS=16 CI_RUNNER_REPOSLUGS=thewoolleyman-livespec-console-beads-fabro
```

### Measured matrix widths (from each repo's own real CI run, via the GitHub API — NOT estimated)

| Repo | Jobs | Slots provisioned | Slots configured in supervisor |
|---|---|---|---|
| `livespec` | 75 | (already had 50 pre-round-6) | 50 — UNCHANGED this round, deliberately (see "Open decision" below) |
| `livespec-driver-codex` | 67 | 67 | 67 |
| `livespec-driver-claude` | 66 | 66 | 66 |
| `livespec-orchestrator-git-jsonl` | 66 | 66 | 66 |
| `livespec-overseer` | 65 | 65 | 65 |
| `livespec-runtime` | 64 | 64 | 64 |
| `livespec-console-beads-fabro` | 16 | 16 | 16 |
| `livespec-orchestrator-beads-fabro` | 96 | N/A | N/A — PERMANENTLY EXCLUDED |
| `dolt-server` | 2 | N/A | N/A — PERMANENTLY EXCLUDED |

### Supervisor config

Single systemd drop-in
(`/etc/systemd/system/ci-runner-supervisor.service.d/poweredge.conf`,
previous version backed up alongside it as `poweredge.conf.bak-round6`)
serving all 7 self-hosted-eligible repos via one `--repos` argument using
the PR #1389 `owner/repo:N` per-repo-slot suffix:

```
--repos "thewoolleyman/livespec:50 thewoolleyman/livespec-driver-codex:67 thewoolleyman/livespec-driver-claude:66 thewoolleyman/livespec-orchestrator-git-jsonl:66 thewoolleyman/livespec-overseer:65 thewoolleyman/livespec-runtime:64 thewoolleyman/livespec-console-beads-fabro:16" --labels self-hosted,local-ci,poweredge
```

Confirmed via the supervisor's OWN startup log line (never the unit file,
per this plan's standing trap 5):
```
ci-runner-supervisor: repos=[thewoolleyman/livespec:50 thewoolleyman/livespec-driver-codex:67 thewoolleyman/livespec-driver-claude:66 thewoolleyman/livespec-orchestrator-git-jsonl:66 thewoolleyman/livespec-overseer:65 thewoolleyman/livespec-runtime:64 thewoolleyman/livespec-console-beads-fabro:16] labels=self-hosted,local-ci,poweredge
```

### Proof — real green master-push CI on every configured repo

For each of the 5 newly-added-and-proven repos (`driver-claude`,
`git-jsonl`, `overseer`, `runtime`; `driver-codex` was proven earlier in the
round via the width test itself), the same discipline as `livespec`'s
original rollout: `CI_RUNNER_LABELS` flipped, then a real docs-only PR
(`do-not-merge` label held until confirmed green, then merged normally —
`livespec-driver-claude` and `livespec-orchestrator-git-jsonl` and
`livespec-overseer` didn't have a pre-existing `do-not-merge` label; created
it live via `gh label create`). Every PR went fully green on self-hosted,
then merged. Every subsequent MASTER-PUSH run (triggered by the merge
itself) ALSO went green on self-hosted:

| Repo | Proof PR | Master-push run after merge |
|---|---|---|
| `livespec-driver-codex` | #437 — 67/67 green | (not separately re-checked; PR itself IS the proof) |
| `livespec-driver-claude` | #472 — 65/65 pass + 2 skip | run 31700687807 — `completed success`, 62/62 non-skipped jobs succeeded |
| `livespec-orchestrator-git-jsonl` | #611 — MERGED clean | run 31700035855 — `completed success` |
| `livespec-overseer` | #883 — MERGED clean | run 31700091295 — `completed success` |
| `livespec-runtime` | #520 — MERGED clean | run 31700383099 — `completed success` |

---

## `console-beads-fabro` blocker — unrelated, pre-existing, NOT this plan's to fix

`CI_RUNNER_LABELS` is set (`["self-hosted","local-ci","poweredge"]`) and 16
slots are provisioned and running (`sudo -u ci-runner podman`/`systemctl
list-units` confirmed clean), but no proof PR was successfully pushed. The
attempt failed `check-pre-push`'s `check-fork-drift` recipe — this repo
tracks upstream `Fabro` orchestrator pin drift via a fixture that requires
active, judgment-heavy disposition (a long `REVIEWED YYYY-MM-DD` history in
the fixture's own comments shows this happens routinely and is resolved by
`just refresh-fork-upstream-pins`, which requires reading and deciding on
the actual upstream diff — not a mechanical fix). **Confirmed this is NOT a
staleness artifact of the worktree** — the worktree branched from the exact
tip of `origin/master` at push time, so the drift check is genuinely red on
this repo's current master, for reasons entirely unrelated to self-hosted CI
routing.

**Left as-is, deliberately:**
- A worktree with the ready, valid, harmless docs-only proof commit is
  PRESERVED (not discarded) at
  `~/.worktrees/livespec-console-beads-fabro/poweredge-selfhosted-proof`
  (commit `6c9a374`), so the proof push is a one-command retry
  (`mise exec -- git push -u origin poweredge-selfhosted-proof`) once
  someone resolves the fork-drift fixture.
- `CI_RUNNER_LABELS` was NOT reverted — the standing "never leave
  `CI_RUNNER_LABELS` pointed at a pool that cannot pass jobs" trap does not
  apply here, because the block is a LOCAL PRE-PUSH gate, not a live CI
  failure; no PR exists, so no merge is waiting on a check that will never
  arrive.

**Next action for this repo specifically:** resolve `check-fork-drift`
first (a maintainer or a dedicated agent with real context on the Fabro
upstream fork's pin-tracking policy — NOT something to force through blind),
then push the preserved worktree's proof commit, open the PR, confirm
green, merge. This is entirely independent of the fleet-CI-runner-pool plan
itself.

---

## Mass-restart I/O contention — a real, benign, characterized host behavior

Restarting the supervisor with ~394 total slots (adding 5 repos' worth of
slots to the already-running 2) produced two distinct, transient spikes,
BOTH confirmed benign (zero job failures, zero errors, self-resolving within
minutes):

1. **Provisioning-time**: the FIRST mass restart (going from 2 repos/117
   slots to 7 repos/394 slots at once) spiked load average to 243 (vs 72
   threads) — confirmed via `top`/`iostat` to be I/O WAIT (D-state
   processes: hundreds of simultaneous `ExecStartPre=+/usr/bin/rm -rf
   .../_work` calls across newly-provisioned instance directories
   contending for the same disk), NOT CPU contention (CPU stayed ~55-80%
   idle throughout). Fully converged (`394 running`, 0 failed units) within
   ~2 minutes.
2. **Post-merge burst**: merging 4 proof PRs back-to-back triggered 4
   simultaneous full-width master-push CI runs, spiking `iowait` to 82.7%
   briefly. Zero job failures; all 4 runs completed successfully within a
   few minutes, one visibly slower (`driver-claude`, sharing the burst)
   than the other 3.

**A GitHub secondary rate limit was also hit once** during the first mass
restart (`mint: no installation token: You have exceeded a secondary rate
limit`) — self-healed via the supervisor's own per-slot retry loop
(`|| sleep 10`) within ~2 minutes, zero recurrence since.

**Practical takeaway for future rounds:** a supervisor restart that adds
many new slots at once will show a scary-looking load spike (100s, well
above thread count) that is NOT a sign of trouble — check `iostat`/`top`
`%wa` and D-state process count to distinguish real CPU exhaustion from
I/O-wait-inflated load average before concluding anything is actually
broken. This host's storage (a single `sda` device) is the bottleneck under
mass-simultaneous filesystem churn, not CPU or memory (never got close to
either ceiling — peak observed ~59GB/188GB RAM, CPU never pinned).

---

## Open decision: should `livespec` itself move from 50 to its own full 75-job width?

NOT done this round, deliberately — left at its already-proven 50 to keep
that one variable constant while validating the OTHER repos' behavior at
full width. Now that 5 more repos are proven at full width with zero
regressions, bumping `livespec` to 75 is the natural next mechanical step
(no new risk category — just matching what's already proven pattern
elsewhere). Not done only because this round's actual asks (App install,
width test, fix-and-propagate) are complete and this is a new, separate,
lower-urgency increment.

---

## Cache tiers, `dolt-server`, and everything else from `research/design.md`

**UNCHANGED from the round-5 handoff** — not touched this round. See
`research/design.md` §"Cache tiers" and the round-5 handoff's own
now-superseded copy (in git history) for full detail:
1. Warm-overlay cache tier — still rooted at `/home/ci-runner/cache` (OS
   disk), not yet relocated to the dedicated `/var/cache/ci-runner` volume
   (658GB, still empty). Ledger child `livespec-s43svm.2`.
2. Local GitHub Actions cache service — not built. Ledger child `.3`.
3. Nix store / binary cache — not built. Ledger child `.4`.
4. `dolt-server` — still excluded from ALL of this (self-hosted routing,
   `MISE_HTTP_RETRIES`, any workflow edit) by its own
   `check-no-workflow-edits` attended-maintainer policy. Untouched this
   round; needs a maintainer-driven workflow change before any of it is
   possible.

---

## Traps and corrections carried forward (still binding; NOT repeated in full — see git history for the full round-1–5 text)

All round-1–5 traps (isolation-suite cwd readability, shellcheck CDN
retries, `github_rate_limit_guard`'s loop/sleep+`gh pr`/`gh run` denial
including a `for`/`while`/etc. bare word ANYWHERE in the command string —
even inside a Python list-comprehension's ` for ` keyword, confirmed hit
this round — the ratification digest, supervisor config via startup log
only, never leave `CI_RUNNER_LABELS` pointed at a dead pool, throwaway proof
workflows not exercising every real code path, `auto-enable-merge.yml`
racing a deliberate self-hosted-only hold, the Actions API lagging real host
state) all still apply and were all reconfirmed live at least once this
round. Two NEW ones from this round:

11. **A freshly-created git worktree does NOT inherit the primary
    checkout's materialized `worktree-pack` — `just bootstrap` must be
    re-run INSIDE the worktree itself, not just the primary.** Hit on
    `livespec-driver-codex`'s width-proof worktree: `just bootstrap` in the
    primary reported `worktree-pack: row already satisfied`, yet the SAME
    check run from the worktree failed with `worktree_pack_absent` — because
    the pack is a LOCAL, gitignored materialization
    (`dev-tooling/worktree-lib.sh` etc.), not something git worktrees share.
    Fix: run `just bootstrap` a SECOND time, from inside the worktree.
12. **`gh api --cache <duration>` does not bypass `github_rate_limit_guard`
    on its own** — the guard's denial is keyed off command-string patterns
    (a `for`/`while`/`until`/`select`/`sleep` bare word anywhere, INCLUDING
    inside an inline Python `for` list-comprehension, not just shell loop
    keywords), not off cache presence. Passing `--cache` is necessary but
    the command must ALSO avoid those bare words entirely — write results to
    a file and `jq`/`grep` them in a SEPARATE call rather than piping
    through inline Python with a `for` clause.

---

## Remaining sequence

0-4. (Everything through round 5's numbered items) **DONE.**
5. ~~Decide slots-per-repo, then roll self-hosted CI out to the other eight
   livespec fleet repos~~ **DONE for 6 of 7 eligible repos** (all but
   `console-beads-fabro`, blocked on its own unrelated gate — see above).
   `livespec-orchestrator-beads-fabro` and `dolt-server` are PERMANENTLY
   excluded, not pending.
6. **Push `console-beads-fabro`'s preserved proof commit once
   `check-fork-drift` is resolved there** (someone else's call, not this
   plan's) — the worktree is ready and waiting.
7. **Open decision: bump `livespec` from 50 to its own full 75-job width**,
   now that 5 other repos are proven at full width with zero regressions.
8. **Relocate the warm-cache tier onto `/var/cache/ci-runner`** — ledger
   child `.2`. Still the next-most-valuable infra work after 6-7.
9. **Build the local Actions cache service and the Nix store/binary cache**
   — ledger children `.3` and `.4`. Genuinely new infrastructure; needs a
   design pass, not blind implementation.

---

## Housekeeping at wrap (round 6)

- `CI_RUNNER_LABELS` reads self-hosted (`["self-hosted","local-ci","poweredge"]`)
  on ALL of: `livespec`, `livespec-driver-codex`, `livespec-driver-claude`,
  `livespec-orchestrator-git-jsonl`, `livespec-overseer`, `livespec-runtime`,
  `livespec-console-beads-fabro` — verified live via `gh api
  repos/.../actions/variables/CI_RUNNER_LABELS` for all 7, this round.
- Supervisor is RUNNING, serving exactly these 7 repos at the slot counts in
  the table above (confirmed via its startup log line, not the unit file).
  Host load settled to ~19 (baseline) after all bursts this round.
- All worktrees this round were reaped after merge EXCEPT
  `~/.worktrees/livespec-console-beads-fabro/poweredge-selfhosted-proof`
  (deliberately preserved, see above) and the pre-existing large set of
  OTHER sessions' worktrees under `livespec-dev-tooling` (untouched, not
  this round's concern — `just reap-stale-worktrees livespec-dev-tooling
  --dry-run` first if anyone wants to clean those).
- `poweredge.conf.bak-round6` is a backup of the pre-round-6 systemd
  drop-in, left in place on the host at
  `/etc/systemd/system/ci-runner-supervisor.service.d/` for rollback
  reference; safe to delete once this round's config is trusted.
- PRs opened/merged this round (all confirmed MERGED at write time):
  `livespec-dev-tooling` #1392 (retry raise); `livespec-driver-codex` #437
  (width proof + both fixes); `livespec-driver-claude` #470 (shallow-fetch
  fix), #472 (self-hosted proof); `livespec-orchestrator-git-jsonl` #608
  (shallow-fetch fix), #611 (self-hosted proof); `livespec-overseer` #880
  (shallow-fetch fix), #883 (self-hosted proof); `livespec-runtime` #518
  (shallow-fetch fix), #520 (self-hosted proof).
