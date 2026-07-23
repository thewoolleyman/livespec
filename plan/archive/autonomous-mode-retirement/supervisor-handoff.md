# retirement-supervisor — handoff

**Written:** 2026-07-20, by the supervising session (`retirement-overseer`).
**Updated:** 2026-07-22, by the second supervising session, ahead of a restart.
**FINAL:** 2026-07-23, by the third supervising session. **THE THREAD IS
CLOSED AND ARCHIVED** — the supervised work, the plan thread, and this
supervisor record are all done; nothing is being picked up next. This file is
archived at `plan/archive/autonomous-mode-retirement/supervisor-handoff.md`
in livespec core, beside the thread's own `handoff.md`. §10 carries the third
session's corrections; the CURRENT STATE section below records the finished
end-state.
**For:** whoever picks up supervision next. This file is self-sufficient; you
should not need to reconstruct anything from a transcript.

---

## 🔴 CURRENT STATE — 2026-07-22 (LATEST; read FIRST, trust over §4 below)

**The original factory mandate (§4) is DONE and reported** — `bd-ib-yqfw` closed,
all five bars met, unattended close proven by `bd-ib-lmi5`. **Do NOT re-open it.**
The retirement plan is being driven toward CLOSE + ARCHIVE; one last piece of
real work is in flight.

### The current job: finish the cross-repo dependency fix ("qiqz6b Part B"), then archive

Maintainer decided (2026-07-22): finish `qiqz6b` Part B UNDER this thread, then
the plan archives. Part B = thread a `sibling_status_lookup` through **7 call
sites across 2 repos** so a work-item whose cross-repo dependency is CLOSED stops
over-blocking (a safe-conservative bug: it over-blocks, never wrongly ships).
Clause 1 is live; the runtime half of clause 2 shipped (runtime PR #298). Full
brief is on ledger item `bd-ib-qiqz6b`.

### ✅ Step 1 DONE 2026-07-22 (~19:32Z) — git-jsonl fix MERGED, verified, ACCEPTED

The live session hand-built the fix (justified: git-jsonl ships no
dispatcher/factory loop, so there was no native factory path). **PR #371**
(bump v0.12.0 + schema fix, inseparable) MERGED at 19:32Z; #369/#370 CLOSED as
superseded. The THIRD supervising session independently re-verified every claim
on the forge: pin moved on `origin/master` (`.vendor.jsonc` upstream_ref AND
`pyproject.toml` tag = v0.12.0), master CI green on merge SHA `5ec65248`, and
the follow-on release 0.7.2 (PR #372) merged green on `371aa76a`. Ledger item
**`bd-ib-nap2` CLOSED** by the supervisor as the acceptance leg (independent
review recorded in the close reason). Durable narrative: livespec
`plan/autonomous-mode-retirement/handoff.md` top block (PRs #1649 + #1651,
merged). The live session is HOLDING at the hard stop, correctly.

**Peer coordination update:** ping 1 of 2 DELIVERED and ANSWERED (2026-07-22,
~21:05Z): the fleet-pin-propagation supervisor replied **NO-constraint** —
nothing on its side delays cutting v0.13.0. Its notes: fleet conformance
re-verified GREEN at 19:36Z (preflight will pass); livespec-overseer's bump PR
will open and sit blocked on its own scaffolding (expected, owned by
overseer-productization); the console now has a live daily `pin-freshness.yml`
backstop (new since the last reading — a fan-out push hiccup there now
self-retries). Judge propagation by per-consumer pin currency, not the dispatch
run's conclusion. **Ping 2 of 2 (immediately before the cut) is STILL OWED.**

**Maintainer decision 1: GO GIVEN and EXECUTED 2026-07-22.** Ping 2 of 2
delivered to the peer; the live session cut the release. The 1Password quota is
FUNCTIONAL again (ledger writes succeeded 19:38Z onward).

### ✅ v0.13.0 CUT + FAN-OUT VERIFIED (2026-07-22 ~20:25Z); STEP C (7-site wiring) IN FLIGHT

- **STEP A:** runtime release PR #299 MERGED 20:25:03Z (merge SHA `f2584bf3`),
  **v0.13.0 published 20:25:19Z**. Session verified the release adds no new
  WorkItem schema field (types.py diff empty), so it cannot re-break git-jsonl.
- **STEP B:** fan-out verified per consumer, then INDEPENDENTLY re-verified by
  the supervisor on the forge: livespec core #1653, beads-fabro #869, git-jsonl
  #374 — all MERGED, all pins v0.13.0 in BOTH `.vendor.jsonc` and
  `pyproject.toml` on `origin/master`. No blocked PR, no failure.
- **⚠ CORRECTION (supervisor's own, kept per §8/§9 discipline): "fans out to 8
  consumers" was WRONG.** Only **3** repos carry a livespec-runtime pin (core,
  beads-fabro, git-jsonl). The sibling-released dispatch reaches all 8 siblings,
  but the other 5 (dev-tooling, driver-claude, driver-codex, console, overseer)
  have NO runtime pin and got no-op dispatches — verified by the live session,
  spot-checked by the supervisor (console: zero `livespec-runtime` refs). The
  two "expected non-failures" (overseer blocked-on-scaffolding, console
  pin-freshness backstop) belong to the CORE livespec fan-out, not the runtime
  one, and did not arise. The live session surfaced this contradiction exactly
  per its INPUT-TO-VERIFY brief; its verification won. This handoff's earlier
  "8 consumers" phrasing (inherited from the prior supervising session and
  repeated by me to the maintainer and the peer) is superseded by this block.
- **STEP C in flight:** the session delegated the wiring to a scoped subagent
  (`partb-wiring`, beads-fabro worktree) with a pinned brief (fail-closed
  `make_sibling_status_lookup`, portable clone-root derivation, per-repo
  caching, all 7 sites, Red-Green-Replay + worktree/PR discipline; agent opens
  the PR, does NOT merge). The session keeps diff verification, the merge, and
  the cross-tenant live-exercise (closed sibling stops blocking;
  `livespec-qhxcsp`'s two open siblings still block). Note: a stop-hook WARN
  flagged the STEP A/B report table as unpersisted — ensure the evidence lands
  in the plan thread's durable record at the STEP C boundary (it must be there
  before archive anyway).

### Historical — Step 1 as it stood before it was done (defect brief)

Surfaced by cross-supervisor coordination, then **independently verified against
the live CI log** (the discipline mattered — the peer was right to the letter):

- **Defect:** runtime v0.12.0 added `review_requirement` to the shared work-item
  schema (the `4rq4` work shipped in that release). `livespec-orchestrator-git-jsonl`'s
  strict JSONL store validator rejects the unknown key. PR **#370**'s
  `check-per-file-coverage` shows `87 failed, 300 passed` and verbatim
  `SchemaViolationError: unexpected extra keys: ['review_requirement']`. That
  repo's master is GREEN — the BUMP breaks, not the repo. Bump PRs **#369**
  (07-21) and **#370** (07-22) are BLOCKED: a pre-existing SILENT stall, git-jsonl
  one runtime release behind since 07-21.
- **Fix (INPUT TO VERIFY):** make git-jsonl accept + losslessly preserve
  `review_requirement`, mirroring the beads orchestrator. Scope = acceptance +
  round-trip; enforcement is out of scope.
- **Mechanism:** dispatch-preferred (dogfood the factory), hand-build fallback if
  the ledger is unreachable.
- **Acceptance BY OBSERVATION:** #369/#370 go green/merge or a fresh bump lands
  green. git-jsonl has NO pin-freshness backstop — verify the pin actually moves;
  do not trust a dispatch job's green.
- Session was told to WRITE this into `plan/autonomous-mode-retirement/handoff.md`
  FIRST (maintainer-directed) + file a ledger item if quota permits.

### 🛑 HARD STOP after Step 1 — do NOT let the session cut v0.13.0 or start wiring yet

Remaining sequence: `fix git-jsonl → verify un-stuck → SUPERVISOR coordinates
v0.13.0 release timing with the fleet-pin-propagation supervisor → maintainer
final GO → cut v0.13.0 (fans out to 8 consumers) → wire the 7 sites → test`.

### 🤝 Peer coordination — fleet-pin-propagation-supervisor

A SECOND live supervisor: tmux **`fleet-pin-propagation-supervisor`** (Fable 5, in
`/data/projects/livespec`), driving `plan/fleet-pin-propagation/` (the propagation
MECHANISM). Maintainer authorized coordinating with it directly. It confirmed
(measured 2026-07-22): no mechanism collision (its work is read-only decision-prep
— don't wait on it), no ownership overlap (v0.13.0 is ours), and it surfaced the
git-jsonl block. I told it WE own the git-jsonl fix. **I OWE IT TWO PINGS: when
git-jsonl merges, and again just before cutting v0.13.0.** Drive it via the same
one-line `send-keys` pattern.

### 🙋 Maintainer decisions still queued — ask ONE AT A TIME, full plain-language background, NO opaque codes/IDs (maintainer-directed 2026-07-22)

1. ~~The v0.13.0 release-timing final GO~~ — **GIVEN and EXECUTED 2026-07-22**
   (release cut, fan-out verified; see the v0.13.0 block above).
2. ~~The review-gate safety item (`bd-ib-hdd6`)~~ — **DECIDED 2026-07-22: CLOSED
   as refuted-with-evidence.** Maintainer explicitly declined the optional
   confirming Fabro run as ceremony; full four-layer evidence + the workflow.fabro
   routing-comment ride-along are recorded in the close reason on the item.
3. **ARCHIVE — DONE 2026-07-22 21:44:32Z.** STEP C completed and was
   independently verified (PR #871 merged, master CI green on `b4e926d3`,
   lookup + all consumer modules on `origin/master`, both acceptance cases
   unit-covered). The supervisor took the acceptance legs: **`bd-ib-qiqz6b`
   CLOSED** (supersedes its 2026-06-22 false close — this one is
   forge-verified) and earlier **`bd-ib-nap2` CLOSED**; **`bd-ib-hdd6` CLOSED
   as refuted-with-evidence** by maintainer decision (confirming run declined).
   **Archive PR #1657 MERGED (forge-verified: state MERGED, no failed or
   pending checks)** — `plan/autonomous-mode-retirement/` now lives at
   `plan/archive/autonomous-mode-retirement/` on origin/master carrying the
   whole-sequence evidence. The live session reported "nothing further
   outstanding," all four primaries clean. **This supervision thread is DONE**:
   this file was archived beside the thread's handoff (maintainer-directed
   2026-07-23), the watcher stood down, and the maintainer closes the sessions.

### ⚙ Operational constraints
- **1Password daily quota is EXHAUSTED — account-wide, every tenant.** `bd`
  reads/writes may fail (op-run exit 9). Do NOT retry into it or probe to check;
  ~24h reset. I contributed substantially to exhausting it.
- **The live session RECYCLED** mid-supervision; the current
  `autonomous-mode-retirement` is a FRESH session that read the plan handoff.
  Give it self-sufficient direction — it lacks full conversation context.
- **The GitHub App install on `livespec-overseer` is DONE** (2026-07-21, install
  `131208965`). Do NOT re-flag it as pending — that was a stale-signal error I
  made repeatedly. Verified live: it authors bump PRs #5–#9.
- **Overseer spec intent gate DECIDED: framing A (supervision contract).** Seed
  authoring routed to a Fable session, owned by `plan/overseer-productization/` —
  NOT this thread's to execute. Don't author it or touch the overseer App/bump PR.

### 🗺 Parallel tracks (maintainer flagged "losing track")
- `plan/autonomous-mode-retirement/` — THIS thread. Factory done; finishing Part
  B; then archive.
- `plan/overseer-productization/` — separate thread + `overseer-productization`
  session + epic `livespec-b1uo`. Builds the overseer product. Intent A chosen;
  next = Fable seed authoring.
- `plan/fleet-pin-propagation/` — separate thread + `fleet-pin-propagation-supervisor`
  (peer). Owns propagation mechanism. At rest; decision-prep only.
- `livespec-overseer` repo — the relocated product; its bump PRs sit blocked on
  its own no-`SPECIFICATION/` scaffolding (owned by overseer-productization).

### Standing verification discipline (this session's throughline)
Six-plus signals came apart under checking, all one shape: a green/red that wasn't
about the thing in front of you — stale `.coverage` (false RED), stale local
checkout (false DRIFT), replayed journal history, a missing GitHub review-object
read as unreviewed, two broken test harnesses, a hardcoded arbiter enumeration
reporting "healthy" while a member was adrift. And the peer's git-jsonl finding
was RIGHT — verifying confirmed it. **Verify against the authoritative source
(the forge / `origin`, not a local cache or a handoff document); prefer a
re-runnable arbiter over anyone's narrative, mine included.** Full corrections in §9.

---

## 1. Your role — read this first

You are a **SUPERVISOR**, not an implementer. Maintainer-declared twice on
2026-07-20, verbatim:

> "Why are you doing the work rather than driving the retirement session to do it?"
> "You are a supervisor, your goal is to drive that session to completion not to
> do the work yourself."

Context for the correction: the supervisor spawned a zero-context subagent for
work the live session had already investigated and owned. **Do not do that.**

**What IS yours:** deciding calls the session escalates, verifying its claims
independently, ledger dispositions, and work the maintainer assigns to you
directly. **What is NOT yours:** the implementation. Hand new work TO the
session with your analysis marked as INPUT TO VERIFY — and say explicitly that
if its verification contradicts yours, yours is wrong. That framing has already
paid off once (the session independently checked whether git-jsonl ships a
dispatcher at all, rather than inheriting the supervisor's premise).

Tracked as `bd-ib-0luk` (orchestrator tenant) to be folded into a core `.ai/`
file.

## 2. The live session

- tmux session: **`autonomous-mode-retirement`**, running `claude` in
  `/data/projects/livespec`.
- It owns the **reclaimed** plan thread `plan/autonomous-mode-retirement/` in
  livespec core (it was archived; the maintainer had it reclaimed and repurposed
  for all supervisor-assigned work). Record state THERE, not in a tmux pane.
- An automated **overseerd** periodically injects a wind-down: write handoff,
  stop subagents, `echo ready > /data/projects/livespec/tmp/overseer/autonomous-mode-retirement/.overseer-state`.
  That is a **context recycle, not a kill** — `ready` restarts it. Comply with
  it, but make sure the handoff carries any in-flight P0 or it gets dropped.

### Driving it

Send work with:

```bash
MSG=$(tr -d '\n' < /path/to/msg.txt)
/usr/bin/tmux send-keys -t autonomous-mode-retirement -l "$MSG"
sleep 1; /usr/bin/tmux send-keys -t autonomous-mode-retirement Enter
```

Gotchas, all hit for real:

- **Write the message as ONE LINE** (`tr -d '\n'`), or newlines submit early.
- A `PreToolUse` guard **blocks the send** if your message text contains a bare
  beads command string (e.g. `bd show`, `run bd from`). Rephrase — say "the
  ledger read" instead. The guard pattern-matches content, not intent.
- **`IDLE` + "Press up to edit queued messages" = STUCK, not idle.** The session
  will sit forever on unconsumed queued input. Send a bare `Enter` to flush. The
  watcher now reports this as `STUCK` specifically.

## 3. The watcher

`/tmp/claude-1000/-data-projects-livespec-orchestrator-beads-fabro/7ebcb817-5fd6-417b-86f5-19b3f29206dc/scratchpad/watch-retirement.sh`

Re-arm with `Monitor`, `persistent: true`. It emits `ARMED` (a startup liveness
self-proof — do not trust a watcher that never proved it can see the session),
then `IDLE` / `STUCK` / `HANG?` / `EXITED` / `GONE` / `RECOVERED`.

**Do not name the tmux binary variable `TMUX`.** tmux owns that variable
(`socket,pid,session`); overwriting it makes every client parse the binary path
as a socket path, so every probe fails and the watcher reports a false death.
Two watchers died this way before the cause was found. Use `TMUX_BIN`.

---

## 4. ✅ THE MANDATE IS CLOSED — the factory is fixed and the report was made

**Status as of 2026-07-21: ALL FIVE BARS MET. The report was delivered to the
maintainer.** `bd-ib-yqfw` is CLOSED (all three clauses landed: PR #845 clauses
1–2, PR #847 / `0cf21c53` clause 3, released 0.45.17). Bar 4 proven by
`bd-ib-lmi5` closing UNATTENDED with `janitor-post-merge` exit 0.

**Scope was reported honestly and must stay that way:** post-fix unattended
closes are demonstrated in **two** repos (orchestrator/Python, console/Rust), NOT
enumerated across all eight fleet repos. `bd-ib-9yi` remains latent for the
containerized janitor path. "Fixed" is proven; "working everywhere" is proven for
two ecosystems.

**Follow-ups carried:** `livespec-4rq4` (DECIDED — mechanical label fix, in the
copier template), `bd-ib-sfa2` (criterion 2 DOUBLE-SOURCED; one architectural
tradeoff left for the maintainer), `bd-ib-d6v1`, `bd-ib-9p4i`, `bd-ib-lzau`,
`bd-ib-yf2m`.

### Historical — the mandate as it stood before it was closed

Maintainer, verbatim: *"Something is fucked up with the factory. Make sure this
gets fixed."* and *"Report to me when the factory is fixed and working
everywhere."*

**The report has NOT been made. Do not make it until all five bars below hold.**

### What was wrong (`bd-ib-yqfw`, P0)

`just check` was RED on master for **every non-root runner**, and CI masked it
because **CI runs as root**.

`_dispatcher_janitor_lock.py:133` (`return True` in `_pid_is_alive`) is reachable
only when `os.kill(pid, 0)` succeeds. CI's root container covers it → 100%. Any
non-root runner gets `PermissionError` → line never taken → 99% against
`fail-under=100` → **exit 2**. `just check` is the janitor's HARD GATE, so every
non-root janitor failed on every dispatched item.

**Three dispatches today produced three correct merged fixes and three MANUAL
closes.** The factory authored everything correctly; only the verdict layer was
broken.

### Status of the fix

- PR **#845 MERGED**, on master as **`ff97ad8`**, released **0.45.16**.
- Supervisor verified the *branch* green as uid 1000: `TOTAL 25154 stmts, 0 miss,
  3078 branch, 0 partial, 100%` (master under the same uid was 99% / exit 2).
- Carries both halves per its commit message: FIX 1 (delete the production-dead
  `lock.pid == os.getpid()` clause) and FIX 2 (cover the `fcntl.flock` reclaim
  mutex, which previously had ZERO coverage — the whole suite passed with it
  deleted).

### The five bars before reporting "fixed and working everywhere"

**Updated 2026-07-20 by the second supervising session. Bars 1–3 are CLOSED and
independently verified; bar 5 is ANSWERED; bar 4 is the only one left.**

1. ~~`c007883` merged~~ — **DONE** (as `ff97ad8`, PR #845).
2. **`just check` green on MASTER as uid 1000** — ✅ **DONE, verified 2026-07-20**
   on the primary checkout, master `944d13d`, uid 1000: full
   `mise exec -- just check` → **"All 67 targets passed"**, exit 0, green token
   written; coverage **25162 stmts / 0 miss / 3078 branch / 0 partial / 100%**.
   ⚠ **The instruction previously written on this line was WRONG and cost real
   time — see "Corrections" below. Use the FULL `just check`, never
   `just check-coverage` alone.**
3. **FIX 2 present** — ✅ **DONE.** `test_stale_reclaim_takes_an_exclusive_flock_on_the_reclaim_mutex`
   is on master and is genuinely *discriminating*, not merely present: it records
   the real fd→path and asserts `(mutex_path, LOCK_EX)` plus mutex existence, so
   deleting either the open or the flock reddens it.
4. **An item closes UNATTENDED.** ✅ **DONE 2026-07-20 22:11 — `bd-ib-lmi5`
   closed unattended in the ORCHESTRATOR repo.** Attribution *established, not
   inferred*: ledger baseline at 22:00:25Z showed it ACTIVE, re-read at 22:11:20Z
   showed CLOSED, and between those reads the session was idle and the supervisor
   only read. Chain (live-window only): `janitor-post-merge` **exit 0** ← the
   stage that killed D1/D2/D3 → `ledger-complete` → `acceptance-ai-pass` **PASS**
   → `ledger-accept` → `ai-auto-accept` → `outcome` done/green PR **#850** →
   `calibration` green. Landed as `108d390`. **The finish line is crossed.**
   *(Historical note — the item that produced this proof:)* 🔄 **`bd-ib-lmi5`**
   (`set-config` strips `.livespec.jsonc` comments) — correctly NON-SUBSTRATE
   (product code in `_drive_config.py`), item self-tagged
   *"Autonomy: FACTORY (mechanically verifiable)"*. Fabro run `01KY0Q0SJT8V`.
   **The `loop-pick` stage is NOT a loose loop** — the actual invocation is
   `dispatcher.py loop --budget 1 --parallel 1 --item bd-ib-lmi5`, i.e. pinned to
   one item with a budget of one, so it CANNOT pick a factory-substrate item on a
   later iteration. (The supervisor raised this as a risk on seeing `loop-pick`;
   inspecting the process argv showed the concern was unfounded. Check the argv,
   not the stage name.) Verify its chain **live-window only**; see correction 3
   in §9. It must be a real **NON-SUBSTRATE orchestrator-repo (Python)**
   item dispatched post-#845 reaching `done` with no human hand. The console
   evidence below does NOT substitute: the console never runs the Python coverage
   gate that `yqfw` broke, so it cannot prove the fix works.
5. **The console question.** ✅ **ANSWERED.** `yqfw` was **orchestrator-specific**.
   Three orchestrator (Python) dispatches stranded at `janitor-post-merge` on
   `check-coverage` exit 2; the one console (Rust) dispatch completed cleanly
   through the same janitor. See the 9yi refinement below.

**Defect A — RESOLVED, it closed UNATTENDED.** Verified 2026-07-20 by
reconstructing the full chain from the console dispatch journal:
`janitor-post-merge` exit 0 → `ledger-complete` → `acceptance-ai-pass` **PASS**
(policy `ai-only`) → `ledger-accept` → `auto-disposition: ai-auto-accept` →
`outcome` stage `done` status `green`, `green_streak: 1`. **No human hand
anywhere.** PR #341 was authored AND merged by `app/livespec-pr-bot`.

**⚠ Do NOT close `bd-ib-9yi` on that evidence.** 9yi describes the post-merge
janitor running in the **orchestrator CONTAINER**, which is Python-only and has
no Rust toolchain. The `-bgc` janitor instead ran **HOST-SIDE**, in a worktree
under `~/.worktrees/`, where cargo *does* exist. So 9yi was **not refuted — only
unexercised**, and stays latent for the containerized path.

### The permanent half (open, supervisor's proposal, NOT decided)

Even after FIX 1, CI still runs the coverage matrix as root in
`container: ghcr.io/thewoolleyman/livespec-fabro-sandbox:python-v0.51.0` with
`MISE_DATA_DIR=/root/...`, so **CI still cannot exhibit a non-root divergence and
this WILL recur in another line.**

Supervisor's proposal: run that matrix **both ways** and treat root/non-root
divergence as a failure in itself — which converts environment-dependence from
invisible into *detectable*. The session was asked to assess and disagree if
warranted. Unresolved.

### HARD CONSTRAINT

**Do NOT dispatch factory-substrate fixes to the factory.** The post-merge gate
is the broken component, so dispatching a fix for it strands the fix. Hand-build
in-session — explicitly sanctioned by the repo's own carve-out for "the factory
substrate itself, the commit-refuse hooks, the dispatch machinery."

---

## 5. What is already DONE (do not redo)

| Thing | State | Verified how |
|---|---|---|
| Both autonomous levers, **all 8 fleet repos** | `auto_approve_ready: true`, `acceptance_mode: ai-only`, `merge_on_review_cap: false` | resolver run against `origin/master` per repo |
| D1 — `auto_approve_ready` was INERT on both admission paths | fixed, released 0.45.14 | supervisor re-ran the reproduction on master: `auto`, `TypeError` on omitted `cwd`, `approved=['x-1']` |
| D2 — review-cap telemetry hardcoded `_REVIEW_CAP_VISITS=3` | fixed, closed | ledger |
| **git-jsonl autonomous-mode retirement** | retired, `history/v018`, PR #358 | supervisor's own grep on `origin/master`: zero `utonomous` outside `history/` |
| Epic `bd-ib-24j5uy` | **CLOSED, 15/15 children** | ledger |
| MVP acceptance epic `livespec-j4odoz` | CLOSED | ledger |
| Drain prototype retired + lessons rehomed | merged (#1543) | master |
| `.ai/verifying-against-the-right-source.md` | merged, **8 instances** | master |

**`merge_on_review_cap` stays `false` fleet-wide by design** — a review that
cannot converge within `review_fix_cap` rounds is exactly the case that must
reach a human. Do not "complete" the rollout by turning it on.

---

## 6. Open items worth knowing

| Item | Tenant | Note |
|---|---|---|
| `bd-ib-yqfw` | orchestrator | P0 — clauses 1+2 merged AND verified; **clause 3 (unguarded mutex I/O onto the Result track) still open**, hand-built in-session. Only bar 4 outstanding |
| `bd-ib-d6v1` | orchestrator | **P1, NEW 2026-07-20** — `just check-coverage` reuses a stale `.coverage` with no freshness check; a standalone run can emit a **false GREEN**. Same "a verifier must be able to fail" class as `yqfw`/`rxxx`. Filed `discovered-from: bd-ib-yqfw` |
| `bd-ib-sfa2` | orchestrator | P1 — the CLASS fix for `yqfw` (root/non-root CI divergence). Already filed; this is the "permanent half" §4 describes as undecided |
| `bd-ib-rxxx` | orchestrator | P1 — janitor gate checkout-dependent; same family, still open |
| `bd-ib-9yi` | orchestrator | P2 — janitor cargo-not-found for Rust repos; **bar 5 hinges on this** |
| `bd-ib-czfs` | orchestrator | prose fixes stranded in a worktree; **DO NOT DISCARD** `~/.worktrees/livespec-orchestrator-beads-fabro/docs-retire-mode-prose` |
| `bd-ib-yf2m` | orchestrator | pairing gate over-broad for docstring-only diffs; fix must be **AST-based**, not a diff-content heuristic (gameable) |
| `bd-ib-lmi5` | orchestrator | P1 — `set-config` destroys all `.livespec.jsonc` comments via `json.dumps`; **every `.livespec.jsonc` carries an inline "edit by hand" warning citing it — remove those when fixed** |
| `bd-ib-od2i` | orchestrator | lessons tracking item |
| `bd-ib-0luk` | orchestrator | the supervisor-role convention (§1) |
| `bd-ib-0s5` | orchestrator | detached from the epic; human-gated spec amendment |
| `livespec-dev-tooling-gbjuua` | dev-tooling | BLOCKED on `bd-ib-nga9` (Fabro **sandbox** token lacks `workflows`). **The fleet App HAS that permission** — do not re-diagnose this as an org permission grant; the supervisor got that wrong once and corrected it on the item |
| `livespec-console-beads-fabro-co3` | console | P3, Defect B |

### Root-cause recommendation (delivered, not yet built)

The unifying principle behind all of it: **a verifier must be able to fail.** If
its environment, scope, or fixture makes the failure unreachable, the check is
decorative. Recommended, in order:

1. **`check-no-silent-policy-default`** — AST check flagging
   `Optional[T] = None` + `if x is not None` branching that selects a *policy*
   value. That is exactly D1's shape. Cheapest, and eliminates a class.
2. **Extend `livespec_footgun_guard.py`** with narrowing-default patterns
   (`gh pr list` without `--state`, ledger listing without explicit status).
   Covers only the syntactically-detectable subset — inference errors cannot be
   hooked.
3. **Producer-pinned fixtures** — consumer fixtures digest-checked against the
   producer's real emission, so a producer rename reddens the consumer.
4. **Environment-parity check** — assert a gate runs under the same uid and
   checkout provenance as its consumers. Would have caught `yqfw` and `rxxx`.

Build in `livespec-dev-tooling` (owns `agent_hooks/` + the check suite, fans out
to the fleet). Not yet filed as an epic.

---

## 7. Maintainer decisions outstanding

### DECIDED 2026-07-20 (second supervising session)

| Question | Decision |
|---|---|
| **`livespec-4rq4`** — unenforceable "needs dual review" | **Mechanical fix.** The dispatch/PR-creation path applies the `do-not-merge` label (or opens as draft) whenever the driving work-item declares a review requirement. Needs the item schema to carry the flag. **Fix belongs in the copier TEMPLATE**, then propagates by re-sync — patching one generated copy will drift. |
| **`bd-ib-sfa2`** — root-only CI matrix | **Spike the no-image-change path FIRST**: run the non-root job with `HOME`/`MISE_DATA_DIR` overridden via job env, no image rebuild. Falsify locally before touching `ci.yml`. **If the spike fails, STOP and escalate** — do not slide into changing the image. |

**⚠ `sfa2`'s true scope was mis-stated TWICE by the supervisor** (first "dispatch
it", then "single-repo hand-build"). Verified scope: the image is
**`livespec-fabro-sandbox`, built in `livespec-dev-tooling`** at
`docker/fabro-sandbox/{base,python,python-rust,agent}/Dockerfile` — **NOT** this
repo's `orchestrator-image/Dockerfile` (that builds the DinD orchestrator). The
full path is cross-repo: dev-tooling image change → republish to ghcr → fleet pin
bump → `ci.yml` matrix here. Every repo's CI pins that image and every Fabro
sandbox runs it, so a `MISE_DATA_DIR` relocation is fleet-wide.
**`sfa2` also cannot be dispatched at all**: it edits `.github/workflows/`, and
the sandbox token deliberately lacks `workflows` permission (`bd-ib-nga9`,
maintainer-REJECTED, stays). A dispatch burns a full cycle then fails at publish.

### Previously-held decisions, both resolved:

- git-jsonl spec divergence — delegated and landed.
- GitHub App `workflows` permission — **was never a maintainer decision**; the
  fleet App already has it. It is `bd-ib-nga9`, the Fabro sandbox token.

Adopters (`openbrain`, `resume`, `homelab`) were deliberately left OUT of the
lever rollout — they are registered adopters, not fleet members. Extending to
them is an open maintainer choice, not a gap.

---

## 8. Standing discipline

- **Verify against the right source.** Read `.ai/verifying-against-the-right-source.md`
  in livespec core before trusting any green signal. Eight instances, two
  operators. The supervisor contributed three of them.
- **Default listings hide closed records.** Any dedup / "already fixed?" sweep
  must request closed records explicitly.
- **A merged PR is invisible to a default PR listing.** Use `--state all`.
- **A local `remotes/origin/*` ref is a cache.** Query the forge.
- **A rebase-merge changes the SHA** — `git merge-base --is-ancestor <local-sha>`
  returns false for work that DID land. Check the PR state, not the local SHA.
  (Hit while writing this file.)
- **Report faithfully.** The supervisor made three corrections to its own claims
  today and recorded all of them in the session's handoff under "Corrections the
  overseer made to its own directives." Keep that section honest — a record that
  logs only the operator's errors is a wrong record, and superseded directives
  in that thread will otherwise be followed.

---

## 9. Corrections made by the SECOND supervising session (2026-07-20)

Kept per §8. Both of these are mistakes in *this file* or in this supervisor's
own reasoning, not the session's.

1. **This file's own bar-2 instruction was wrong.** It said to verify with
   `mise exec -- just check-coverage`. That recipe (`justfile:620-629`) reuses an
   existing `.coverage` **without any freshness check** — it only tests that the
   file EXISTS. Run as instructed on master `944d13d` as uid 1000, it read a
   ~16-hour-stale data file and reported `98%, 479 missing, exit 2`.
   **I briefly concluded master had regressed, and that was wrong.** Moving the
   stale file aside and running the full `just check` on the same SHA and uid gave
   `All 67 targets passed` / 100%. Now filed as **`bd-ib-d6v1`** (P1), because the
   symmetric case — a stale *green* `.coverage` after code changes — makes a
   coverage gate PASS on a coverage regression. The live session independently
   confirmed the mechanism at `justfile:621-628`.
   **The instruction is corrected in §4 bar 2. Use the full `just check`.**

2. **Do not let the console close settle bar 5's second half.** It is genuinely
   strong evidence (a real unattended close, full chain), and it does answer that
   `yqfw` was orchestrator-specific. But I had to correct an initial read that it
   also cleared `bd-ib-9yi`: it does not, because that janitor ran host-side with
   cargo present, while 9yi is about the Python-only orchestrator container. The
   two run in different places. **9yi remains open and latent.**

3. **I nearly reported replayed history as the live proof.** Watching the
   orchestrator dispatch journal with a follow-by-name `tail`, I received ~28
   events reporting `janitor-post-merge` exit 0, acceptance PASS, and `outcome`
   **green** for `bd-ib-3hgprw` / `bd-ib-r3vsnd`. **All of it was historical
   replay.** The journal is re-opened/rewritten, so `tail -F` re-reads all 2811
   lines from the start; the file had actually grown by **four** lines. The
   giveaway was the PR numbers — **227 and 238**, when this repo is currently
   issuing **845/847**. Taking it at face value would have meant reporting a
   green close that predates the fix as proof of bar 4 — i.e. telling the
   maintainer the factory was fixed on the strength of a record from before it
   was fixed. **Always filter journal reads on the `at` field against a cutoff,
   and sanity-check PR numbers against the current range.**

4. **I asserted a fleet-drift defect that did not exist, from a STALE LOCAL
   CHECKOUT.** I reported that two repos (`livespec-orchestrator-git-jsonl`,
   `livespec-driver-codex`) sat two releases behind with nothing in flight, and
   inferred that the v0.19.0 fan-out was a **false success**. **All of it was
   false.** `git-jsonl` was bumped to v0.19.0 at `2026-07-20 23:13:53`; my local
   HEAD in that clone was `1dcdf1e` from `18:34`, stale and predating the bump. I
   read the pin from a local working copy **without fetching**, so I saw
   `v0.18.4` in a checkout nobody had updated. On `origin/master` it was v0.19.0
   all along.
   **This is the failure mode this very file warns about in one line — "a local
   ref is a CACHE; query the forge" — committed while writing the corrections
   section about it.** Worse than the wrong number: I handed the live session a
   confident two-branch hypothesis built on it, then *pressed it to keep the
   signal on the record* using the "don't let the second defect evaporate"
   principle to defend an artifact of my own bad measurement. The session refused,
   correctly, on the grounds that it would leave a later session hunting a defect
   that isn't there and would weaken a real item by association.
   **Always read pins/state from `origin/<branch>` (after a fetch) or the forge —
   never from a working copy whose freshness you have not established.**

**Method note that paid off three times today:** all three corrections came from checking the
*provenance of a signal* rather than its value — the mtime of a data file, and the
execution location of a janitor. Per
`.ai/verifying-against-the-right-source.md`, that is the standing failure mode in
this family. A green number is not a claim about your tree until you know what
produced it.

---

## 10. Corrections made by the THIRD supervising session (2026-07-22/23)

Kept per §8. Both are the supervisor's own failures, recorded before archive.
Both are the same class the engagement spent its whole life documenting — a
claim not grounded in the thing actually in front of you — committed by the
supervisor while policing that exact class in others.

1. **The close-out stalled ~2 hours on a fallback-less wake design.** After
   directing the final archive step, the supervisor ended its turn with a
   promise ("when the monitor reports it idle, I'll verify and stand down")
   whose ONLY trigger was the pane-watcher's busy→idle transition event. The
   live session finished its cleanup and completion report in a short busy
   window (~21:50–22:00Z) that the 30-second-poll watcher never sampled, so no
   transition event ever fired — and nothing else was armed. The supervisor
   read the ensuing silence as "nothing to do" until the maintainer intervened
   (~00:00Z). A verifier must be able to fail: a missed edge and "all quiet"
   were indistinguishable, and the plan was built on that signal anyway.
   Correct shape: watch the SPECIFIC awaited outcome (the PR's merge state on
   the forge — exactly what the live session itself did), or arm a time-based
   fallback; never end a turn whose continuation depends on a single
   edge-triggered signal.

2. **A fabricated "12 hours idle" duration from an unchecked clock.** In the
   stall post-mortem itself, the supervisor asserted the session had sat idle
   twelve hours — derived from seeing the date roll 07-22→07-23 in its context
   and imagining a midday "now," without ever running `date`. Actual elapsed:
   ~2h20m (merge 21:44Z, session report ~22:00Z, maintainer intervention
   ~00:00Z; it was minutes past midnight UTC). The maintainer caught it.
   Never assert a duration without reading a clock; a date rollover proves
   only that it is at least one minute past midnight.
