# fleet-pin-propagation — handoff

**Ledger anchor:** epic `livespec-n4ptl2` (livespec CORE tenant).
**Opened:** 2026-07-19.

---

## 🟢 START HERE — 2026-07-21 (FOURTH session close). READ THIS FIRST.

**Everything below this section is history. This section is the current truth.
Nothing of mine is in flight; every primary checkout is clean on `master`; no PR
of mine is unmerged.**

### THE P0 IS RESOLVED — propagation restored AND the fan-out itself verified

**`livespec-dh9r` (P0) no longer needs emergency action.** The third session
closed with this thread's headline reading "fleet propagation is STALLED right
now". That is no longer true, and the correction is measured, not assumed.

Final state, measured 2026-07-21T04:42Z:

    latest livespec release          v0.20.0
    all SEVEN consumers pinned at    v0.20.0      <- gap ZERO
    fan-out attempt 4               preflight SUCCESS,
                                    all EIGHT dispatch jobs SUCCESS
                                    (livespec-overseer included)
    fleet conformance                passed, 9 members, 0 error findings

**The root cause was a single one:** the fleet GitHub App did not cover
`livespec-overseer`, the 9th member registered ten minutes before the v0.20.0
release. Installing the App (maintainer-only; that obligation row has no
reconcile function by design) cleared it. Registering before wiring is BY DESIGN
— the fleet manifest says so in its own header comment — so the red was the
system working, not a defect.

**⚠ THE HANDOFF'S OWN UNBLOCK HYPOTHESIS WAS TWO-THIRDS WRONG.** The third
session predicted the blockers were the App install "plus its stale dev-tooling
pin and its missing impl-plugin connection block". Measured against the actual
CI findings: the stale pin is severity **WARNING** and the connection block is a
**SKIP**. Neither can move the exit code, so neither was ever blocking. Only
rows returning a finding at error severity fail the gate. Check the severity
before treating a conformance line as a blocker.

**⚠ TWO OF THE THREE "VIOLATIONS" WERE FALSE.** `merge-settings` and
`delete-branch-on-merge` reported violated with values `is None`. `None` there
meant the field was ABSENT from the payload — the App token could not read it —
not that the setting was wrong. An admin-scoped token showed all five settings
already correct at the same moment. Both rows went green with **no repo setting
ever changed**. The tell is the literal word `None` in a conformance finding.
**Fixed and merged this session:** livespec-dev-tooling PR #523 (`61f2d7bf`)
makes both rows report absence as not-evaluable, matching the sibling
`secret-names` / `branch-protection` rows. Filed as `livespec-dev-tooling-6ge`.

**⚠ A SECOND, INDEPENDENT BLOCKER the third session never saw.**
`livespec-overseer` had **zero CI runners**: its `CI_RUNNER_LABELS` was unset, so
it fell back to `["self-hosted","local-ci"]` while having none registered. Its CI
sat QUEUED from 00:35Z for ~2h and had never once run, which is why its PR #1 —
the PR that clears the stale pin and the connection block — was permanently
unmergeable. Seven of nine members set `["ubuntu-latest"]`; the only other member
leaving it unset (`livespec-orchestrator-beads-fabro`) legitimately has 6 online
self-hosted runners. **Fixed this session** (maintainer-approved): set
`CI_RUNNER_LABELS=["ubuntu-latest"]` on `livespec-overseer`. Its CI now runs.

### ⚠ THE RESIDUAL — a red run status on a WORKING fan-out

Run 29790751188's OVERALL conclusion still reads `failure`, because a run's
conclusion reflects its worst attempt and attempts 1–3 failed. Attempt 4 is
wholly green. **So "the fan-out run is red" and "the fan-out is broken" are now
different statements**, and anyone polling run status will read a false alarm.

This is the THIRD instance of this thread's central lesson, after the
open-bump-PR count and the blind-row false violations: **a status artifact is not
a health signal.** PIN CURRENCY remains the correct measure.

### ⚠ DO NOT TRUST THE SIBLING THREAD'S P0 SECTION — it is stale

`plan/autonomous-mode-retirement/handoff.md` carries a P0 block (livespec commit
`dde445c7`, written 04:39:03Z) stating "The fleet GitHub App still does not cover
`livespec-overseer`" and predicting "the next release stalls identically". Both
are FALSE as of 04:42:25Z — three minutes later — when the fan-out preflight
logged `fleet conformance passed` and dispatched to all eight siblings. That
block also frames the recovery as "a MANUAL REPLAY of one release's fan-out, not
a fix"; the automated path is now exercised end-to-end. Corrections are journaled
on `livespec-cbmw` and `livespec-dh9r`.

The method point generalizes: that claim was written from an earlier reading and
recorded as current without re-measuring. **When two sessions work the same
problem concurrently, a conclusion about live forge state has a shelf life of
minutes.** Re-measure before acting on any P0 text, including this section.

### What the FOURTH session landed

| what | where |
|---|---|
| `CI_RUNNER_LABELS=["ubuntu-latest"]` — unblocked a ~2h-queued CI that had never run | `livespec-overseer` repo variable |
| can't-read vs misconfigured fix for two conformance rows, +5 tests | dev-tooling PR #523 (`61f2d7bf`) |
| Fan-out re-run to attempt 4 — preflight green, 8/8 dispatches | livespec run 29790751188 |
| Corrected diagnosis + stale-claim correction | `livespec-dh9r`, `livespec-cbmw`, `livespec-dev-tooling-6ge` |
| Two P1 defects found in the propagation SAFETY NET (below) | `livespec-oq9w`, `livespec-dev-tooling-bmf` |
| Both safety-net defects FIXED, merged, and live-verified | dev-tooling PRs #526, #529, #533 |

### ✅ THE SAFETY NET IS NOW REPAIRED — supersedes the 🔴 section below

**The section immediately below diagnosed the sweep as degraded. Two of its three
defects are now FIXED, merged, and verified against real sweeps — not merely
green CI.** Read that section for the diagnosis and the method lesson; read this
for the current state.

| defect | state |
|---|---|
| `livespec-dev-tooling-bmf` — empty diff exits 1 | **FIXED** — PR #526, live-verified |
| `livespec-dev-tooling-clrk` — false staleness (the ROOT cause) | **FIXED** — PR #533, live-verified |
| `livespec-oq9w` — console has no shim at all | **OPEN**, maintainer-gated |

**`clrk` was the root cause, and it was not what `bmf` first claimed.** `bmf`
was filed blaming a race; measuring the scan's own output instead showed a
deterministic TAG-FORMAT MISMATCH — `current=python-v0.50.8` compared against
`latest=v0.50.8`, the same version in different forms, so the Fabro image pin
was stale BY CONSTRUCTION forever. The rewrite half already knew that grammar
(`fabro_image_pin_rewrite` is prefix-preserving by design); only the comparison
half did not. `bmf`'s recorded mechanism is corrected on the item.

**The live proof, and why a green run could not have faked it.** Before: the
scan emitted `livespec-dev-tooling stale: current=python-v0.50.8 latest=v0.50.8
distance=1` and the bump job RAN and failed. After (sweep 29820693692):

    ##[notice]livespec-dev-tooling pinned at python-v0.51.7, already current
    freshness / open-bump-pr <matrix>   SKIPPED

The distinguishing observable is the bump job being **SKIPPED**, not the run
being green — the intermediate sweep (after `bmf`, before `clrk`) was ALSO green
while still attempting a pointless bump daily. That criterion was written down
BEFORE the fix existed, precisely so it could not be satisfied vacuously.

**A second defect fell out of `clrk`:** `ordinal_distance` matched a prefixed
tag against bare release tags, matched nothing, and took the `fallback` — which
the caller passes as the staleness threshold itself, so every prefixed pin
reported MAXIMALLY stale. **At the default threshold of 1 the wrong answer
coincides with the right one**, which is exactly why it hid behind the currency
bug instead of surfacing on its own. Fixed in the same change.

**PR #529 exists because #526 created the problem it solves.** Making the
composite SUCCEED on the no-op path made the codex-acp gate steps reachable
there for the first time, where `gh pr view "$BRANCH"` would fail on a branch
that was never pushed. A fix that relocates a failure is not finished.

**⚠ ONE PROPAGATION BLOCKAGE IS STILL LIVE, and it GROWS on its own.**
`livespec-overseer` pins `v0.50.7` while every other member is at `v0.51.7` —
~10 releases behind, the largest pin debt in the fleet. The fan-out IS
delivering to it (PRs #7 and #6 are open bump PRs); they are **BLOCKED** by
`check-doctor-static` and `check-source-trees-scoped-to-consumer`, i.e. by the
scaffolding gaps, not by anything about pins. Every release widens the gap with
no further mistake required, and PR #1 — the change that would clear its stale
pin — is gated behind the same red. Recorded on `livespec-cbmw`; the seed itself
is owned by `plan/overseer-productization/`, not by this thread.

That is the third shape of this thread's one recurring lesson, and the only one
still open: **a propagation stall's last mile is usually a gate that has nothing
to do with pins.**

### 🔴 THE SAFETY NET IS DEGRADED — found by checking, not by reading

The fleet's backstop for a failed fan-out is the daily 13:00 UTC pin-freshness
sweep: each consumer independently re-checks its own pins and opens its own bump
PR. **It is real and it does work** — that is what bounds any fan-out failure at
~24h rather than indefinitely. But it is degraded in two independent ways, and
**neither is visible from the sweep's status**, because the sweep is red anyway.

**1. The sweep reports FAILURE on every member, every day —
`livespec-dev-tooling-bmf` (P1).** Measured across all seven members carrying the
shim (runs of 2026-07-20T15:0xZ): `scan-pin-freshness` SUCCESS everywhere,
`open-bump-pr livespec-dev-tooling` FAILURE everywhere, one cause —

    nothing to commit, working tree clean
    ##[error]Process completed with exit code 1.

The rewrite yields an empty diff because the fan-out already landed that bump,
and `git commit` on an empty diff returns non-zero under `set -euo pipefail`. A
no-op is treated as a hard failure. It hits the dev-tooling leg specifically
because that source released v0.51.0 → v0.51.4 inside one day and so loses the
race on essentially every sweep, while the slower `livespec` leg wins it and
SUCCEEDS in the same runs.

**2. The scan can silently MISS a stale pin — `livespec-dev-tooling-ews` (P1,
filed 2026-07-19, not mine).** A SIGPIPE-corrupted ordinal distance makes the
scan emit `stale=[]` and skip `open-bump-pr` entirely.

**They degrade it in OPPOSITE directions** — `bmf` fails loudly on a pin needing
nothing, `ews` passes silently over a pin needing everything — and they compound:
because `bmf` makes red the normal daily state, red carries no information, so
**`bmf` also conceals `ews`.** Anyone checking whether the backstop works sees red
either way. (`ews`'s symptom was NOT present in the 2026-07-20 runs, so it is
intermittent or already addressed — re-measure, don't assume.)

**3. One member has no backstop at all — `livespec-oq9w` (P1).**
`livespec-console-beads-fabro` is the only member of nine with no
`pin-freshness.yml`. It ships `bump-pin-from-dispatch.yml`, so it RECEIVES a
fan-out push but never PULLS — the one repo where nothing ever retries, and no
~24h bound applies. **This is very likely the mechanical explanation for this
thread's FOUNDING problem** (the console ~12 releases behind while every sibling
stayed current): it was never really about that repo's gates, it is the only repo
with no recovery path. `oq9w` also records that the fleet manifest's
console-class rationale — "non-pin-consuming ... ships none of the three shims" —
is contradicted on BOTH clauses by live state (it carries a `v0.20.0` **livespec**
pin and ships one of the three), which is probably why the absence went
unquestioned. Do not just add the shim: settle which side is authoritative first,
because either choice needs the contract text amended in the same change.

**⚠ A METHOD WARNING ABOUT THIS SESSION'S OWN WORK.** I first journaled on
`livespec-dh9r` that the backstop was sound and bounded the stall at ~12.5h. That
was reasoned from the workflow's documented behavior and its cron **without
opening a single actual run**. Checking the runs falsified the confident half
within minutes. The mechanism claim survived; the health claim did not. Corrected
in place on `dh9r`. **Reading what a system is SUPPOSED to do is not
measurement** — the same failure this thread has now recorded three times in
other people's work.

### Still open — none of it urgent, all maintainer-gated

1. **`livespec-overseer` is substantially unwired**, and its CI can finally show
   it. Now-visible reds: **no `SPECIFICATION/` tree at all** (every
   `doctor-static` check errors on `SPECIFICATION/spec.md`), source-tree role
   config still pointing at livespec CORE's paths
   (`.claude-plugin/scripts/livespec`, `dev-tooling`), and `Release Please`
   failing on its master. **None of this blocks the fan-out** — no conformance
   row inspects a member's CI result — but it blocks its own PR #1. Owned by
   `plan/overseer-productization/`, not by this thread.
2. **The systemic half of `livespec-dh9r`** — a persisting-gap assertion keyed on
   PIN CURRENCY in `reusable-pin-freshness.yml`. Unaffected by any of the above
   and still the right fix; the residual above is a fresh argument for it.
3. The four items the third session left open (heading-coverage TODO sequencing,
   `livespec-u7x5zn`'s self-parent dependency, Driver defects `tun` + `6lc`,
   `reconcile-merged-dispatch-lock`) are untouched and still accurate below.

### ⚠ THE METRIC THIS THREAD USED IS NOT A HEALTH SIGNAL — correct this belief

This thread measured propagation health as **open bump PR count**, and drove it
43 → 13 → 2 → 0. **Zero open bump PRs is indistinguishable from a dead fan-out.**
Both show zero. The fleet looked its healthiest — 0 open PRs, all nine masters
green — at the exact moment propagation had stopped.

**Use PIN CURRENCY instead:** compare each consumer's pinned version against the
producer's latest release. That comparison caught this stall immediately; the PR
count could not have. `reusable-pin-freshness.yml` already exists and is the
natural home for a persisting-gap assertion. This is recorded as the systemic
half of `livespec-dh9r`.

### The founding problem IS solved — that part still stands

Original stall: 43 open bump PRs, one repo (`livespec-console-beads-fabro`)
genuinely blocked 12 releases behind. **Resolved.** The console reached
`v0.19.0`, fully current at the time, via supersession rather than a refresh
(PR #328 was CLOSED, not merged — supersession category 2 working in
production). Detail in §"THE THREAD'S FOUNDING PROBLEM IS SOLVED" below, which
remains accurate for the ORIGINAL stall. The v0.20.0 stall above is a NEW,
different failure that opened during this session.

### What this session landed (all merged, all verified independently)

| what | where |
|---|---|
| The owed constraint FILED and RATIFIED as **v045** | orchestrator PR #844, #852 (`e9a7507`) |
| `reusable-release-park-parity` RATIFIED as **v029** | dev-tooling PR #517 (`bcdf175`) |
| Its blocker fixed (unswept `spec.md` drift) | dev-tooling PR #510 |
| Its stale narration fixed (sweep count + dead design-record path) | dev-tooling PR #513 |
| Console master red FIXED — CI flipped `failure` → `success` | console PR #345 (`e4afef40`) |
| `bd-ib-nga9` description rewritten (rejected option removed) | ledger |

Both 2026-07-04 filed-but-never-ratified proposals are now live spec. v029's
deliverable is verified falsifiably: `grep -c 'reusable-release-park' --
SPECIFICATION/contracts.md` was **0**, now **2** — a shipped workflow finally
has contract coverage.

### Still open — ALL maintainer-gated, none of them mine to decide

1. **`owned-heading-coverage-todos`** (core, pending). Ratifiable, but it arms
   per-commit rejection of TODOs missing `work_item`. Core has **0** such
   entries; the seven siblings have **233**, none carrying the field. Ratifying
   before the backfill leaves the authoring repo green while every consumer
   fails per-commit on unrelated work. **A sequencing call.** Measured on
   `livespec-915y`.
2. **`livespec-u7x5zn`** — root-caused: it declares its own parent epic as a
   dependency, so the child waits on the epic while the epic waits on the child.
   All three slices of that one groom carry the shape. The fix is removing one
   edge, but whether it was intentional is a grooming judgment.
3. **Driver defects `livespec-driver-claude-tun` + `6lc`** — `tun` is the
   core-root probe testing the prose DIRECTORY rather than the operation's prose
   FILE, in all EIGHT skills; `6lc` is the `entries[0]` fallback. **Sequence
   them together: `tun` currently MASKS `6lc`, so fixing `tun` alone makes `6lc`
   surface MORE often.** Both snippets are untested prose.
4. **`reconcile-merged-dispatch-lock`** (orchestrator, pending, UNREVIEWED) —
   outside this thread; deliberately left untouched.

### Method lessons from this session — each cost real time

- **I stated a wrong diagnosis with high confidence and it cost a dispatch
  cycle.** I declared the console failure "conclusive" from a plausible code
  path while the disproof — `Repo: $LIVESPEC_CONSOLE_REPO`, an unexpanded shell
  variable — sat in output I had already pasted into the ticket. Corrected in
  both places it was recorded. **Confidence language is not verification.**
- **The instruction that saved it: brief every dispatched agent to HALT if its
  analysis contradicts the brief.** It did exactly that, turning a wrong
  prescription into a verified one-hunk fix. Keep that clause in every brief.
- **`resolution: None` is NOISE.** All 50 closed items in the console tenant
  carry it, because the `bd` CLI cannot set the field at all. Judge a closed item
  by its `close_reason` and by whether the work landed in git.
- **A stale `.coverage` file lies** — `just check-coverage` reuses it rather than
  re-running. It implicated four innocent modules. `rm -f .coverage` before
  believing any coverage failure.
- **Test-only fix + Red-Green-Replay:** a tests-only staged tree that PASSES is
  rejected under `feat:`/`fix:` as `test-passed-at-red`; any other prefix takes
  the green-verified leg. `chore(test):` is the designed path, not a bypass.
- **Filing is not ratifying.** That confusion stalled two proposals 17 days,
  left a shipped workflow uncontracted, and misled a work-item into citing a
  contract section that was never written.

---

## 🎯 THE THREAD'S FOUNDING PROBLEM IS SOLVED — measured 2026-07-21 (the ORIGINAL stall; superseded by the P0 above)

**The propagation stall this thread was opened to diagnose is cleared.** Both
halves — the noise and the one genuine blockage — are resolved, and the fleet is
propagating normally.

| measure | at opening | now |
|---|---|---|
| fleet-wide open bump PRs | **43** | **1** |
| repos carrying open bump PRs | 8 | **1** |
| `livespec-console-beads-fabro` core pin | `v0.16.0`, ~12 releases behind | **`v0.19.0` — fully current** |
| latest `livespec` release | — | `v0.19.0` |

**The console — the one repo this thread identified as genuinely blocked, by a
gate the fan-out structurally could not satisfy — is now current with zero gap.**
Its pin moved `v0.16.0` → `v0.19.0` (landed `c858743`). PR #328 was CLOSED, not
merged: superseded by a newer bump PR targeting the newer release. That is
supersession category 2 working in production, i.e. `livespec-dev-tooling-5o6ssu`'s
automation doing exactly what it was built for.

**The one remaining open bump PR is normal operation, not residue:** livespec
core #1581, opened 2026-07-21, bumping dev-tooling to `v0.51.3`. A fresh PR for a
fresh release is what a healthy fan-out looks like.

**Chain of unblocks, for the record.** The console's blockage had three layers,
each hiding the next, and all three are now cleared:

1. The captured-manifest completeness gate — fixed by the re-key `f5fa99f`.
2. PR #328 was red anyway because its branch PREDATED that fix (stale-branch
   trap). Resolved by supersession rather than by refreshing it.
3. `check-e2e-tmux` was red on master — a REQUIRED check blocking every PR in the
   repo regardless — fixed by `e4afef40`, which flipped master CI
   `failure` → `success`. That fix came from correcting my own wrong diagnosis
   (see §"THE CONSOLE MASTER RED" below); the real cause was an unexpanded shell
   variable in a test fixture.

Layer 3 is the one worth remembering: the pin bump could not have landed even
after layers 1 and 2 cleared, because an unrelated red required-check gated the
whole repo. **A propagation stall's last mile can be a gate that has nothing to
do with pins.**

Everything below remains accurate as history and as the record of what is still
open (the maintainer-gated items, the 233-entry heading-coverage backfill, and
the Driver defects). The thread's own subject is done.

---

## ⚠ `resolution: None` IS NOISE — do not read it as a signal

Measured 2026-07-21. This corrects a suspicion recorded in the loose-ends table
below, and it matters because chasing it costs real time.

**Every one of the 50 closed items in the `livespec-console-beads-fabro` tenant
has `resolution: None`. Not one carries a value.** The cause is mechanical:
**the `bd` CLI cannot set that field at all** — neither `bd close` nor
`bd update` exposes a `--resolution` flag. Anything closed through the CLI is
`resolution: None` by construction. Values like `no-longer-applicable` seen
elsewhere in this thread are written by the livespec/orchestrator layer (the
`drive` valve's disposition paths), not by `bd`.

So the earlier read of `livespec-console-beads-fabro-5kd56a` — "closed with
`resolution: None` + empty reason ... which is exactly what made it read as an
accident" — was **half wrong**. The `resolution: None` half carries NO
information. Only the EMPTY CLOSE REASON was ever the real signal, and even that
is not unique: **7 of those 50 closed items have an empty `close_reason`**, so it
is a ~14% pattern rather than a one-off anomaly.

**Practical rule:** when triaging a closed item in a beads tenant, judge it by
its `close_reason` and by whether the work actually landed in git — never by
`resolution`. And when closing an item yourself, put everything load-bearing in
the reason, because the resolution field will not carry it.

**`livespec-console-beads-fabro-1s1` is CLOSED** on that basis: fixed by console
PR #345 (`e4afef40`), master CI flipped `failure` → `success` after four
consecutive failures, verified on `origin/master`. Its close reason carries the
full account INCLUDING a warning that its own middle comment states a wrong
mechanism — the comments disagree, and the reason says which one to trust.

## 🟢 START HERE — definitive resume state, 2026-07-20 (second session close)

Everything below this section is history and reasoning. This section is the
current truth. **Nothing is in flight; no PR of either session's is unmerged;
every primary checkout is clean on its default branch.**

### ✅ BOTH 2026-07-04 STALLED PROPOSALS ARE NOW RATIFIED

The filed-but-never-ratified cluster is cleared. Both are live spec:

| proposal | repo | outcome |
|---|---|---|
| `factory-sandbox-credential-capability-boundary` | orchestrator | **v045**, PR #852 (`e9a7507`) |
| `reusable-release-park-parity` | dev-tooling | **v029**, PR #517 (`bcdf175`) |

**v029's deliverable is verified by a falsifiable test, not a report:**
`git grep -c 'reusable-release-park' origin/master -- SPECIFICATION/contracts.md`
was **0** and is now **2**. A shipped workflow — the fleet's only detector for a
release train that never departs — finally has contract coverage. `spec.md`'s
category definition names the backstop, `history/v029/` is paired, and the queue
holds only `README.md`.

Getting there took two fixes to that proposal, both from its FIRST-EVER
independent review (17 days pending, never reviewed):

- **A real blocker:** it swept `contracts.md` but not the `spec.md` sentence
  DEFINING the category, so ratifying would have landed a contradiction — the
  spec asserting the category is pin-and-bump-only while its own inventory said
  otherwise. Fourth target added (PR #510).
- **Two staleness fixes** (PR #513): a sweep count that contradicted itself, and
  a **dead design-record path** cited twice —
  `plan/fleet-plugin-currency/research/design.md` no longer resolves; the thread
  was archived and it now lives under `plan/archive/`. Both were narration, so
  neither reached the ratified spec — but ratification freezes the proposal into
  `history/` BYTE-IDENTICALLY, so they had to be fixed BEFORE the accept, not
  after.

### ⚠ THE RATIFICATION SURFACED A SYSTEMIC GATE GAP — already tracked, do NOT re-file

v029's revise CLI **exited 3**: post-step doctor reported two FAILs that had
nothing to do with the ratification. Confirmed pre-existing against the untouched
master primary.

**Root cause, and it is the interesting part: `livespec-dev-tooling` is the ONLY
fleet repo whose `just check` does not wire `check-doctor-static`.** Measured
2026-07-21 — `grep -c check-doctor-static justfile` is **0** there versus **2–3**
in livespec, orchestrator-beads-fabro, console-beads-fabro, driver-claude, and
runtime. So spec-tree violations accumulate invisibly and ambush the next
unrelated revise. Its justfile comment asserting "doctor-static — dev-tooling has
none" is FALSE: the repo has a six-file governed `SPECIFICATION/` tree. That stale
comment is likely why the gap persisted.

**All of it was ALREADY filed** — `livespec-dev-tooling-tem4t2` (the systemic
gap, `blocked`), `7bfhkm` and `kkmhwo` (its two blockers), `goucoq`. **No new
item was filed**, and that was a deliberate call: the ratifying run recommended
filing "one small work-item covering both findings", which would have duplicated
AND mis-scoped them.

**The mis-scope is worth carrying as a method warning.** Post-step doctor names
ONE offender for the section-citation finding (`livespec_dev_tooling/__init__.py`),
which reads like a one-docstring fix. Measured: **116 `§"` occurrences across 71
`.py` files**. The existing blockers already scope it correctly (~100-file,
~16 cross-repo, matching 116/13 measured) — so the DOCTOR OUTPUT is the
misleading artifact, and triaging from it alone under-scopes by two orders of
magnitude. Caveat kept honest: the check scans comment tokens and docstrings
only, and the same marker inside a normal string literal is legitimate, so 116 is
an UPPER BOUND, not a violation count.

**Two corrections journaled on `tem4t2`:**

- Its evidence says findings (1)+(2) "are being fixed by a dedicated PR
  (`fix-dt-stale-spec-citations`)". **That PR never existed** — no PR in any
  state, no branch. Both findings are still live 17 days on. Do not read that
  line as in-flight work.
- Its prediction that finding (3) "resolves at the next `contracts.md` revise"
  **came true** — v029 was that revise, and doctor now reports 2 findings, not 3.
  The drop is vindication, not evidence drift.

### ✅ RATIFIED — the constraint is LIVE SPEC as of v045

**The owed constraint is no longer a pending proposal.** A Fable agent drove
`/livespec:revise` in `livespec-orchestrator-beads-fabro`; it merged as
[PR #852](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/852)
(`e9a7507`), cutting **v045**. `just check` 67/67.

**Verified independently on `origin/master`, not taken on the agent's report:**

- `constraints.md:216` now carries `## Factory sandbox credential constraints`,
  with both the capability rule and the coarse-grants rule.
- The three opposite-posture statements are GONE from the live spec —
  `grep -c 'among the App-installation requirements'` is **0** in both
  `contracts.md` and `scenarios.md` (history snapshots correctly retain them).
- `history/v045/` holds the proposal plus its paired `-revision.md`.
- The negative `.github/actions/` scenario landed.
- The `tests/heading-coverage.json` co-edit landed (84 → 85 entries).
- **`reconcile-merged-dispatch-lock.md` is STILL PENDING and untouched** — the
  hard safety constraint held. That second, unreviewed proposal shares the queue,
  and the brief pinned the mechanism that protects it: the CLI moves proposals BY
  TOPIC (`proposed_changes/{topic}.md` per decision entry), so a single-entry
  `decisions[]` provably leaves it in place.

**Do NOT run `capture-impl-gaps` over v045 expecting a new item — it would
duplicate `bd-ib-nga9`.** The ratifying run deliberately skipped the revise
prose's post-step gap-capture (it files work-items behind a per-gap consent
dialogue with no operator attached). v045 DOES legitimately register as a
spec→impl gap, because it specifies the pre-dispatch refusal predicate that does
not exist yet — but that gap IS `nga9`. Map any finding onto it; do not file a
second record. Journaled on `nga9`, which now also records that its spec
authority is ratified rather than pending.

### ⚠ NEW DRIVER DEFECT — it false-matches in THIS repo specifically

Surfaced BY the ratification run. All eight `livespec-driver-claude` SKILL.md
bindings resolve `<core-root>` with a bash test that contradicts the rule stated
two paragraphs above it:

    rule (line 32):  if `<project-root>/.claude-plugin/prose/revise.md` exists
    bash (line 42):  [ -d "./.claude-plugin/prose" ]

File versus DIRECTORY. The validity guard below it tests the directory too, so a
false match survives both. Any governed project shipping its own prose tree
WITHOUT core's prose therefore resolves `<core-root>` to itself.

**`livespec-orchestrator-beads-fabro` is exactly that repo** — six prose files
for its own skills, no `revise.md`. Measured across the fleet, core is the only
legitimate match and the orchestrator is the only false one; exposure GROWS as
more impl plugins ship authored skills. The run recovered only because the
operator followed the stated rule rather than the shipped snippet.

Filed as **`livespec-driver-claude-tun`** (P2). It is a DIFFERENT defect from the
existing `livespec-driver-claude-6lc` (that one is the step-3
`installed_plugins.json` `entries[0]` fallback), and **the two interact**: this
step-2 defect currently MASKS `6lc` by short-circuiting before the fallback runs,
so fixing step 2 will make `6lc` surface MORE often. Sequence them together.
Cross-referenced on both records.

### ⚠ A SECOND, OLDER FILED-BUT-NEVER-RATIFIED PROPOSAL — and it already misled a work-item

A fleet-wide sweep for pending proposals found the same failure mode this
thread's own handoff warns about, twice, both filed **2026-07-04**:

| repo | proposal | state |
|---|---|---|
| `livespec-dev-tooling` | `reusable-release-park-parity` | blocker fixed 2026-07-21; needs re-review |
| `livespec` (core) | `owned-heading-coverage-todos` | pending; backfill must precede arming |
| `livespec-orchestrator-beads-fabro` | `reconcile-merged-dispatch-lock` | pending, unreviewed |

**`reusable-release-park-parity` is the ONLY contract coverage for a SHIPPED
workflow.** `.github/workflows/reusable-release-park.yml` exists on master, but
the string `reusable-release-park` appears NOWHERE in that repo's
`contracts.md`. That workflow is the fleet's only detector for a release train
that never departs — the silent propagation stall
`livespec-dev-tooling-2kt` exists to close.

**It already caused real damage.** `2kt`'s description cites the resulting
contract subsection as landed authority, naming "PR #267, merged 2026-07-04".
PR #267 is titled "chore(spec): **FILE** … propose-change" and merged exactly one
file — the proposal itself. Merging a proposal lands the PROPOSAL; only a revise
pass applies it. Anyone implementing `2kt` would hunt for a section never
written. Journaled there with proof: all FIND targets still resolve, which is
direct evidence of non-application.

**Its first-ever independent review found a real blocker, now fixed.** The
proposal writes into `contracts.md` that the fourth workflow "participates in no
pin rewrite", but the sentence DEFINING that category lives in `spec.md`, which
it never targeted — so ratifying as written would have landed a contradiction.
Fourth verbatim target added; all four now resolve exactly once. Merged as
[dev-tooling PR #510](https://github.com/thewoolleyman/livespec-dev-tooling/pull/510)
(`94dba99e`). **Deliberately NOT ratified** — the review returned BLOCKERS FOUND,
so the amended text needs a re-review before any accept.

### ⚠ `owned-heading-coverage-todos` CANNOT ship before a 233-entry backfill

Core's pending proposal arms the PER-COMMIT tier to reject any heading-coverage
TODO missing a `work_item` field. Measured per-repo 2026-07-21 (its tracking item
`livespec-915y` scopes this sweep and says "verify siblings per-repo, never
assume"):

| repo | TODO entries | with `work_item` |
|---|---|---|
| `livespec` (the AUTHOR) | **0** | 0 |
| `livespec-orchestrator-beads-fabro` | 62 | 0 |
| `livespec-driver-codex` / `livespec-driver-claude` | 36 / 36 | 0 |
| `livespec-dev-tooling` | 35 | 0 |
| `livespec-runtime` | 29 | 0 |
| `livespec-orchestrator-git-jsonl` | 25 | 0 |
| `livespec-console-beads-fabro` | 10 | 0 |
| **TOTAL** | **233** | **0** |

The authoring repo is the ONLY one with zero exposure, so its CI stays green
while all seven siblings begin failing per-commit on unrelated work — the exact
required-key-schema cross-repo trap. Scope item (3)'s backfill is a HARD
PRECONDITION for arming item (1), not a trailing tidy-up. Also recorded there: the
proposal's auto-filing mechanism covers only NEW entries, so these 233 are a
LEGACY BULK backfill — a materially different job than the go-forward mechanism
implies. Journaled on `915y`; no duplicate filed, the hazard's home already
existed and only lacked numbers.

(Note: v045's own heading-coverage entry landed as `test: "TODO"`, taking the
orchestrator from 62 to 63. Ratifying adds to this debt.)

### ⚠ THE THREAD'S CENTRAL BLOCKAGE IS RESOLVED — measured 2026-07-21

**This supersedes the "exactly one repo is genuinely blocked" framing below.**
That claim was true when written and is now stale in the way that matters.

**Fleet-wide open bump PRs: 2.** (Thread history: 43 → 13 → 1 → 2.) Seven of
eight members carry zero or one fresh PR. The 30 closed superseded PRs have NOT
re-accumulated, which is continuing production evidence for
`livespec-dev-tooling-5o6ssu`'s close-superseded automation.

| repo | open bump PRs |
|---|---|
| `livespec-orchestrator-beads-fabro` | 1 — #849 → dev-tooling v0.51.1 (fresh) |
| `livespec-console-beads-fabro` | 1 — #328 → livespec v0.18.4 |
| all six others | 0 |

**THE CONSOLE'S GATE IS FIXED. `check-completeness` now PASSES on the console's
master** — the config-manifest re-key (`f5fa99f`) genuinely worked. The gate the
thread described as one "the fan-out structurally cannot satisfy" is no longer
failing.

**PR #328 is still red on that check, but ONLY because its branch is STALE.**
Measured: #328's head `2123b4db` was created 03:50Z; the re-key landed 06:01Z,
and `git merge-base --is-ancestor f5fa99f 2123b4db` is FALSE. The branch
predates its own fix. This is the thread's own documented trap — *"do not read
the red check names on a superseded PR as a symptom list; its branch is simply
stale"* — recurring on the one PR nobody expected it on.

**So `livespec-console-beads-fabro-ogpok4`'s remaining work is probably a
BRANCH REFRESH, not a gate fix.** Refresh #328 (or let the fan-out open a fresh
bump PR) and re-read. Do not re-derive the completeness gate. **But it cannot
merge yet** — see the console master red immediately below.

### ⚠ THE CONSOLE MASTER RED — CAUSE FOUND, and my first diagnosis was WRONG

**An earlier revision of this section gave a confident mechanism that was
incorrect. It has been replaced. The correction is journaled on
`livespec-console-beads-fabro-1s1`; read the LATEST comment there, not the one
headed "BEHAVIOR QUESTION RESOLVED".**

**The wrong claim:** that the persisting row was a journal-backed escalation
(`valve:set-admission:...`) made immune by the product's
`AttentionSourceRef::new("orchestrator-journal", ...)` sentinel. FALSE for this
test — the tmux harness has NO journal or escalation source at all, and there is
no `set-admission` row anywhere in it. I read the product escalation path and
asserted it was the path this test exercises, without checking that it is.

The disproof was already inside the evidence quoted in this very file: the
captured failure frame shows `Repo: $LIVESPEC_CONSOLE_REPO` — an UNEXPANDED
SHELL VARIABLE — beside an `approve:` action, not `set-admission:`. Both were
read past.

**The actual cause is a TEST-FIXTURE bug, not a product one.** In
`crates/console-cli/tests/support/lifecycle.rs`, the needs-attention stub builds
its JSON with a SINGLE-QUOTED `printf` format and places
`\"repo\":\"$LIVESPEC_CONSOLE_REPO\"` inside it. Bash does not expand inside
single quotes, so the emitted JSON carries the LITERAL string (the harness does
export that variable — expansion was plainly intended). The same `printf` builds
the id as `valve:%s:` from the verb, so the row is `valve:approve:`, never
`set-admission:`. Ingest records the snapshot verbatim, so the item APPEARS
(appearance is unfiltered) but its recorded repo matches no real repo — so after
`3c0496d4` repo-scoped the RESOLUTION, it can never be resolved and the
`attention: 0` wait times out.

**The prescribed fix was therefore unimplementable:** there is no
`set-admission` row to drive, and driving one would not resolve the stuck
`approve` row. Following it would have meant ADDING an escalation source to the
fixture — a far larger change duplicating coverage `scenario_15` already owns —
while leaving the real bug buried.

**What survives, and it is not nothing:**

- `3c0496d4`'s repo-scoping of `prior` is correct and MUST NOT be reverted.
- The walkthrough's `attention: 0` was passing for the WRONG REASON, via the
  unscoped collateral sweep that was the bug.
- Do not skip or `#[ignore]` the walkthrough.
- **The SHAPE of the diagnosis was right and is now STRONGER.** A non-repo
  literal in `source_ref.repo` is silently immune to repo-scoped resolution; the
  error was attaching it to the wrong instance. The residual noted below now has
  a SECOND independent instance, so the overloading is a real root cause that has
  bitten twice — once in the product sentinel, once in the fixture.

**The fix being landed** (test-side only, no `lib.rs` change): expand the
variable via `%s` so `source_ref.repo` carries the real ingesting repo, plus a
doc comment recording the repo-scoped-resolution invariant. Every existing
assertion stays byte-identical, so the walkthrough proves the genuine
repo-matched drain rather than the sweep. Verified before landing: red
reproduced on `origin/master`, then `check-e2e-tmux` 8 passed / 0 failed and
full `just check` exit 0.

**Residual, unchanged and now better evidenced:** the `source_ref` repo field is
overloaded — sometimes a repo name, sometimes an origin kind, sometimes (in the
fixture) an unexpanded literal. Any future code comparing `source_ref().repo()`
against a repo list inherits the same silent non-match. Worth a typed
distinction.

**METHOD LESSON, carried because it cost a dispatch cycle.** The prior section
was marked "ANSWERED" and "decisive" on the strength of a plausible code path,
without checking whether the failing test reaches that path — while the
contradicting evidence sat in the frame already pasted into this file.
Confidence language is not verification. It was caught only because the
dispatched agent was briefed to HALT rather than proceed if its analysis
contradicted the brief, and it did exactly that. **Keep that instruction in
every dispatch brief**; here it converted a wrong prescription into a correct
one-hunk fix instead of a large wrong test change.

### ⚠ ORIGINAL FILING: the console's master CI is RED — filed P1

`livespec-console-beads-fabro`'s `check-e2e-tmux` fails on
`tmux_tui_e2e_lifecycle_walkthrough_two_repos`. It is a REQUIRED check, so it
blocks every PR in that repo, #328 included.

**Bisected: first red is `3c0496d4` "fix: preserve journal escalation
attention"** (20:55Z). The run before it, `a7429d99` — itself a pin bump to
dev-tooling v0.51.0 — was GREEN, and `6b4f393c` (pin bump v0.51.1) inherits the
failure. **Not a pin-bump breakage**, despite a pin bump sitting at the red
run's head; do not chase the dev-tooling bump. Two consecutive failures on
different commits, so not a flake.

The test waits 20s for `attention: 0` and captures `attention: 1` holding a
pending `approve work-item …` row — i.e. exactly the persistence the breaking
commit's subject says it introduced. Most likely the walkthrough's expectation
encodes the OLD "attention clears" semantics and is now stale, rather than the
fix being wrong. Filed as **`livespec-console-beads-fabro-1s1`** (P1) with the
behavior question stated first, because it must be resolved as
"which semantics are correct" before either side is edited.

### ✅ The proposal's ratification precondition is MET

The independent Fable review was re-run against the FINAL merged text (the
first pass returned BLOCKERS FOUND, and the fix had never itself been
reviewed). Second pass: **VERDICT: NO BLOCKERS**, verified against CURRENT
`origin/master` — all replacement targets byte-exact and unique, the prior
blocker's fix real and complete, the directed generalization faithful, drift
sweep exhaustive with nothing new contradicting it, and both appended scenarios
evidence-backed. So `/livespec:revise` in
`livespec-orchestrator-beads-fabro` is unblocked and is the thread's cheapest
remaining win.

### ✅ `livespec-u7x5zn`'s stuck state — ROOT CAUSE CONFIRMED

The loose-ends table below records this cause as **unconfirmed**, with an
instruction not to act on the recorded hypothesis. It is now confirmed by direct
measurement, and it is NOT that hypothesis. Full detail is journaled on the item.

**It declares its own PARENT EPIC as a dependency:**

    parent:      livespec-n4ptl2
    depends_on:  livespec-e7lanq  (closed)
                 livespec-n4ptl2  (the same epic — status: backlog)

The epic stays `backlog` until its children finish, so the child waits on the
epic while the epic waits on the child. **Closing `e7lanq` was necessary but not
sufficient**, which is precisely why "self-routes, no action needed" was
falsified.

**It is the shape of that entire groom** — all three slices cut from
`livespec-xw65el` carry `parent=n4ptl2` AND `depends_on=[n4ptl2]`. The two
closed ones were driven through by hand, so the edge never bit them. Slices from
OTHER grooms in the tenant (`2hya5g`, `dbbgoc`, `i6pyy6`, `qhxcsp`) do NOT carry
it, so this is specific to that one groom's slice-filing — a plausible third
symptom for `bd-ib-dvmh`.

**Second, independent cause:** it carries no autonomy tier ("Autonomy tier at
groom."), so it is not dispatchable even once the edge clears.

**NOT repaired** — removing a `depends_on` edge changes dispatch eligibility
(unlike a description edit), and whether that edge was intentional is a grooming
call the maintainer owns. Recommended fix if unintentional: drop
`livespec-n4ptl2` from its `depends_on`, leaving the native parent edge.

**Method note:** `auto_approve_ready: true` IS set in core's `.livespec.jsonc`,
and `livespec-qhxcsp` sits at `pending-approval` with ZERO dependencies — so
`pending-approval` is not dependency-driven per se, and that sibling's stall is
a separate, unexplained anomaly (logged on the item, not chased).

### What the SECOND session did — the owed constraint is FILED

**Action 2 of the previous next-actions list is DONE.** The
"credentials passed into the factory MUST NOT carry `workflows` permission"
boundary no longer lives only in a ledger comment. It is filed as a proposed
change in the `livespec-orchestrator-beads-fabro` repo and MERGED:
[PR #844](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/844)
(`abdc50cc`), landing
`SPECIFICATION/proposed_changes/factory-sandbox-credential-capability-boundary.md`.

**It is a PROPOSAL, not yet ratified.** It sits in `proposed_changes/` awaiting
a `/livespec:revise` pass in THAT repo. Until that pass runs, the spec still
carries the contradicting text the proposal repairs.

**Written at the CAPABILITY level, per maintainer direction mid-session** ("you
should document this in the specifications for future scenarios that are like
this as well"). The rule is not about one GitHub grant: no credential projected
into the factory sandbox may carry a capability that executes code on the host
substrate or modifies a gate validating the factory's own output. `workflows`
read-write is the worked instance. The rationale for generalizing is that the
rejection's three properties — self-hosted substrate, gates defined in the
governed artifacts, coarser-than-needed grant — are all substrate-independent,
so a `workflows`-only rule would need re-amending for the next such grant.

**The proposal is 7 changes, not 1, because the spec actively asserted the
OPPOSITE posture in three places.** A drift sweep found them; filing the
constraint alone would have left the spec self-contradictory:

| Location | What it said |
|---|---|
| `contracts.md` §"Self-contained plugin dispatch" | preflight + adopter docs MUST surface the `workflows` grant as an App-installation **requirement** |
| `scenarios.md` Scenario 32 | the Gherkin twin of that requirement |
| `contracts.md` §"Work-item beads-issue mapping" | the `factory_safety` sharp line classifies writing CODE as factory-safe — making a `.github/workflows/` edit **factory-safe**, i.e. exactly the dispatch the boundary forbids |

The third is the load-bearing one: it is why an item could pass grooming, be
admitted, burn a full implement cycle, and only fail at publish.

**Maintainer decided (picker, 2026-07-20):** route workflow edits under the
**EXISTING** `mutates-host-machinery` reason rather than adding a fourth
`factory_safety` enum member. That reason already covers work that "changes the
live host substrate the factory itself runs on", which is the rejection's own
leading argument. The enum stays closed at three, and the admission valve's
existing non-null-`factory_safety` refusal path needs no new machinery.

**A NEGATIVE scenario was added deliberately:** `.github/actions/` must NOT be
refused. Without it, an implementation could satisfy every other scenario with
a `.github/` or `*.yml` glob that wrongly refuses dispatchable work such as
`livespec-dev-tooling-dqfmjr`. Proven by two adjacent-directory items on
opposite sides of the line (dev-tooling PR #495 published a composite action
through the sandbox; PR #506's three workflow files had to land from a host
session).

**Independent Fable review ran and found a REAL blocker**, which was fixed
before merge: a bullet lead-in read `**No self-examining capability.**` while
its body stated the all-or-nothing granularity rule — naming a rule the
maintainer never decided, and backwards besides (examining is fine; rewriting
the examiner is bullet 1). Renamed to
`**Coarse grants are judged at the granularity offered.**` All eight
replacement targets were verified to resolve EXACTLY ONCE, twice.

### `bd-ib-nga9`'s description was REWRITTEN (maintainer-authorized)

Its title had been re-scoped and a comment declared fix option 1 REJECTED, but
the **description** still opened its FIX OPTIONS with "Grant the sandbox token
`workflows` permission" — the field an implementer reads first. An agent
picking it up description-first would have implemented the rejected option.

The rejected option is now removed outright. The body leads with the boundary
being correct and staying, and scopes the deliverable to (a) pre-dispatch
refusal keyed on the `.github/workflows/` prefix specifically, (b) a
non-interactive terminal verdict, (c) a refusal message naming the host-session
route. `Autonomy tier at groom.` is preserved — **it is still `backlog` and NOT
dispatchable**; it needs the maintainer's grooming pass.

**Audit caveat:** per `.ai/beads-gaps-workarounds.md` Entry 13,
`.beads/interactions.jsonl` logs only status VALUE changes, so a description
rewrite is recorded NOWHERE. A comment was added to that item as the only
durable record that the body changed and why.

### ⚠ A REAL MASTER BREAKAGE was found and fixed — read this, it generalizes

`livespec-orchestrator-beads-fabro`'s master was **red on local `just check`
while CI reported green**. Root-caused precisely, and it is the same signature
as the P0 in livespec `aa1feb80` ("master's just check is red for non-root, CI
masks it").

**The mechanism.** `_dispatcher_janitor_lock.py:133` is the `return True` in
`_pid_is_alive` — the branch taken when the lock-holding process IS alive. Its
test hardcoded `pid: 1` (init). Root may signal init; a normal user may not:

| Environment | `os.kill(1, 0)` | Line 133 | `just check` |
|---|---|---|---|
| CI (root) | succeeds | executes | 100% → **green** |
| Local (uid 1000) | `PermissionError` | never runs | 99.99% → **red** |

So coverage of that line was **privilege-dependent**. Fixed in the same PR
(#844, separate commit `chore(test):` so the two are independently revertible).
Verified as uid 1000: 100.00%, 1928 passed.

**Three traps this cost real time on; do not repeat them:**

- **A stale `.coverage` lies.** `just check-coverage` REUSES an existing
  `.coverage` file rather than running the suite ("no duplicate suite run"). A
  fresh worktree inherited a stale one and reported 67 misses across four
  files, implicating innocent modules. `rm -f .coverage` before believing any
  coverage failure. The real gap was ONE statement.
- **`os.getpid()` does NOT fix it.** The caller short-circuits on
  `lock.pid == os.getpid()` BEFORE consulting `_pid_is_alive`, so a self-PID
  lock never reaches the branch. This was tried and measured, not assumed.
- **Spawning a process is banned** (`check-tests-no-subprocess-spawn`). The
  working shape is to fake the probe, which additionally lets the test ASSERT
  the probe shape (exactly one signal-0 check against the lock's own PID).

**The Red-Green-Replay path for a test-only fix** (this is documented nowhere
obvious and cost a rejected commit): a tests-only staged tree whose test PASSES
is rejected as `test-passed-at-red` under a `feat:`/`fix:` subject, because that
prefix DECLARES a behavior change. Per the check's own rule 3, **any other
prefix is a test-only cleanup and takes the green-verified leg** — `chore(test):`
ran the full suite and recorded `TDD-Suite-Green-*` trailers. Use it for
coverage repairs; it is the designed path, not a bypass.

### ⚠ OVERLAPPING UNMERGED WORK — not mine to reconcile

`livespec-orchestrator-beads-fabro` carries an unmerged branch and worktree
**`fix-janitor-lock-nonroot`** (`2f33a21`, "fix: restore the janitor gate for
non-root runners and cover the reclaim mutex"), based on the same commit as
PR #844 and adding a NEW 115-line `test_dispatcher_janitor_lock_nonroot.py`.
Another actor hit the same non-root problem independently.

**PR #844 merged first**, so that branch is now PARTLY REDUNDANT — but only
partly: it also covers **the reclaim mutex**, which #844 does not. Do NOT
delete it as a duplicate, and do not force-push it; it belongs to whoever
created it. Reconciling it is a live task for its owner.

### Also observed, deliberately NOT acted on

- **`bd-ib-w4h4` is stranded `active`** (`assignee: fabro`, last moved 18:20Z)
  even though its TOCTOU fix ALREADY LANDED as `ba9fdaf`, an ancestor of
  master. This is the known stranded-`active` shape — `reconcile-merged` covers
  only an already-MERGED active item. Its two janitor worktrees are still on
  disk.
- **The dark factory is landing into `livespec-orchestrator-beads-fabro`
  concurrently.** `origin/master` advanced twice mid-session (`349fe79` Fabro,
  `c5e2aab` release). Re-read that repo's state immediately before acting on
  it; do not trust a reading from earlier in a session.

### The dispatch round is COMPLETE — all four slices resolved

| Slice | Outcome |
|---|---|
| `livespec-2hya5g` | MERGED (livespec #1508) → **`acceptance`, awaits you** |
| `livespec-dev-tooling-5o6ssu` | MERGED (dev-tooling #495) → **`acceptance`, awaits you** |
| `livespec-console-beads-fabro-5kd56a` | Work LANDED (console `f5fa99f`); item closed |
| `livespec-dev-tooling-gbjuua` | **DONE** — dev-tooling #506, closed with evidence |

### ⚠ THE AUTHORIZATION-BOUNDARY RULE — maintainer-declared 2026-07-20

**This is the load-bearing decision of the session. Read it before touching any
workflow-editing item.**

| Surface | `.github/workflows/` writes | Why |
|---|---|---|
| **Factory sandbox** (Fabro, unattended) | **DENIED — and this stays** | Self-hosted runners ⇒ workflow write is arbitrary code execution on the maintainer's host; an unattended agent could rewrite the very gates that validate it; GitHub's `workflows` permission is all-or-nothing (no per-path scoping) |
| **Attended host session** (a `/livespec:*` session like this one) | **ALLOWED**, via `gh`/git | Supervised, every diff seen, credential already held legitimately |

**Granting the sandbox `workflows` permission is REJECTED, not deferred.** The
existing asymmetry is correct by design: `livespec-pr-bot[bot]` (the fan-out)
holds it because it is a deterministic pin-string rewrite; the sandbox is an
open-ended agent.

**The resolution is ROUTING, not privilege — and NEVER manual maintainer work.**
Requiring the maintainer to hand-edit is explicitly unacceptable. A
workflow-touching item is performed FROM THE HOST SESSION, automatically.
**Proven the same day:** `gbjuua` failed twice in the factory at publish, then
landed from a host session in one pass (#506, comment-only, CI green). Zero
manual steps. The boundary costs no autonomy — it relocates which actor
publishes.

### NEXT ACTIONS, in order

1. **Accept `livespec-2hya5g` and `livespec-dev-tooling-5o6ssu`** (maintainer;
   `ai-then-human`). **Full clause-by-clause AI-leg evidence is already
   journaled on each item**, including a genuinely satisfied live-exercise
   clause for `5o6ssu` (fleet sweep: ONE open bump PR fleet-wide, console
   13 → 1, after two real post-merge releases). Accepting them moves both to
   `done` and **releases two more slices**:
   - `livespec-dbbgoc` and `livespec-dev-tooling-dqfmjr`. Both were
     PRE-VERIFIED 2026-07-20 (journaled): premises still hold, `dbbgoc`'s DO
     step 3 is already satisfied by `2hya5g`, and `dqfmjr` is confirmed NOT
     workflow-exposed (it edits a COMPOSITE ACTION under `.github/actions/`,
     proven safe because `5o6ssu` merged a change to that same file).
2. ~~**OWED — file the constraint.**~~ **FULLY DONE 2026-07-20/21 — filed AND
   ratified.** Filed as
   [PR #844](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/844),
   then ratified as **v045** via `/livespec:revise` and merged as
   [PR #852](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/pull/852)
   (`e9a7507`). The constraint is LIVE SPEC; the three contradicting statements
   are gone from the live tree. No residual step. See §"RATIFIED" above for the
   independent verification and for the do-not-duplicate warning about
   `capture-impl-gaps`.
3. **Implement the re-scoped `bd-ib-nga9`** (orchestrator tenant). Its title,
   scope, **and now its DESCRIPTION** are corrected: the permission boundary is
   NOT the defect; the FAILURE HANDLING is. It should deliver (a) pre-dispatch
   refusal keyed on the `.github/workflows/` prefix **specifically** — not a
   broader `.github/` or `*.yml` heuristic, which would wrongly refuse
   dispatchable work like `dqfmjr`; (b) a NON-INTERACTIVE terminal verdict, so a
   refusal never parks on an `[R]/[I]/[A]` prompt nobody can answer; (c) a
   message naming the host-session route.
   **It is still `backlog` and needs a GROOMING pass before dispatch** (it
   carries "Autonomy tier at groom."), so it is maintainer-gated like item 4.
   The rule it enforces is now specified — see item 2.
4. **Groom `livespec-dev-tooling-9j8.6`** (maintainer). Still gates three
   slices. **Consider DECOMPOSITION rather than blanket refusal:** most of its
   value is new tested modules under `livespec_dev_tooling/` that the sandbox
   CAN push, with only a thin `run:`-glue swap on the privileged surface. The
   right question per item is not "does it touch workflows" but "does it touch
   anything else worth an agent's time" — `gbjuua` was 100% workflow comments
   (factory added nothing); `9j8.6` is the opposite.

### Loose ends — surfaced, deliberately NOT acted on

| Item | State |
|---|---|
| `livespec-u7x5zn` | ~~Cause **unconfirmed**~~ — **ROOT-CAUSED 2026-07-21**, and it was not the recorded hypothesis: the item declares its own parent epic (`livespec-n4ptl2`, `backlog`) as a dependency. See §"ROOT CAUSE CONFIRMED" above; detail journaled on the item |
| `livespec-console-beads-fabro-5kd56a` | Closed with `resolution: None` + empty reason. **The work DID land** (`f5fa99f`) — do NOT reopen. ⚠ **Half of that suspicion is now FALSIFIED — see §"`resolution: None` is NOISE" below.** Only the empty reason was ever a real signal |
| `livespec-console-beads-fabro-ogpok4` | STATE section **stale** (claims 13 open bump PRs / #320; reality is 1 / #328 → v0.18.4, re-confirmed 2026-07-21). Correction journaled on the item; its body already self-flags "counts drift — re-read live", so it was deliberately NOT rewritten. **Its gate is FIXED** — remaining work is likely a branch refresh; see §"CENTRAL BLOCKAGE IS RESOLVED" |
| `livespec-dev-tooling-2kt` | The **propagation blind spot**: release-park leg (b) unimplemented — the only detector for a release train that NEVER DEPARTS, i.e. a silent fleet-wide propagation stall |
| `reusable-release-park-parity.md` | Pending ~16 days in dev-tooling; **verified still ratifiable** — all three `FIND (verbatim)` targets resolve exactly once |

### Ledger repairs made this session

- **Epic `livespec-n4ptl2`'s cross-tenant refs were ALL DEAD** (five, all
  pointing at regroomed-out closed items). Repointed to the live set; every
  mapping read from each closed item's own regroomed-out reason, so nothing was
  invented. Filed as a THIRD symptom on `bd-ib-dvmh` (parent side of the gap;
  its two existing symptoms are the child side).
- **`bd-ib-w3d0` FIXED and CLOSED** by me after verifying `c8bde4a` landed —
  the image pulled flipped `python-agent` → `python-rust-agent`, exit 0.
- **Corrected a misattribution** on `livespec-console-beads-fabro-6ma`: it
  quoted my operator note as an aborted run's own log. The stranding bug is
  REAL (two reproductions) but "the agent lied in its run log" is not.

### Method traps — each cost real time; do not repeat

- **A merge SHA is not a PR.** Reading only `5o6ssu`'s merge commit shows a
  1-line change and makes it look unimplemented. Verify a PR's FULL file set.
- **`bd list --json` OMITS the dependencies array** — a dependency check via
  `bd list` returns cleanly and looks like a negative result. Only `bd show
  --json` carries it.
- **The fleet is non-uniform on default branch.** `openbrain`/`homelab` use
  `origin/main`; everything else `origin/master`. Reading `origin/master:<path>`
  in the first two returns nothing and reads as "not declared" rather than
  erroring — it silently under-reported two of three adopters.
- **`git ls-remote` is NOT an auth probe** on a public repo (succeeds
  anonymously). **`git push --dry-run` from the PRIMARY CHECKOUT is not one
  either** (the commit-refuse hook rejects it, not GitHub). The valid probe is
  `git push --dry-run` **from a worktree**.
- **Status-page ≠ capability.** GitHub showed `partial_outage` while the fleet
  merged normally. Measure recent CI runs + a real auth probe instead.

---

Status is READ from the ledger, never stored here. This file carries no
checkbox queue.

**Composing status.** Each operation named in this file is a skill of the
`livespec-orchestrator-beads-fabro` plugin — invoke as
`/livespec-orchestrator-beads-fabro:<operation>` (`list-work-items`, `next`,
`groom`, `drive`). Each repo is its OWN beads tenant and the read surfaces
resolve the tenant from the working directory, so to read a non-core tenant,
run from that repo's clone (`/data/projects/<repo>`) — there is no `--repo`
flag on `list-work-items`. This thread spans three tenants: `livespec`,
`livespec-dev-tooling`, `livespec-console-beads-fabro`.

**"Autonomy tier"** is the per-item dispatch-eligibility rating assigned
during the `groom` operation, with the maintainer owning the call; an item
without one cannot be dispatched. The vocabulary is the orchestrator's, not
this thread's — read it from the `groom` operation and from a groomed
exemplar in the ledger rather than from this file, which deliberately does
not restate it. Every item this thread filed carries the marker
"Autonomy tier at groom." for exactly this reason, matching
`livespec-dev-tooling-adqmnm`.

## Read-first chain

1. This file.
2. `plan/fleet-pin-propagation/research/diagnosis.md` — the measured evidence,
   the classification axis every decision turns on, the consolidation verdicts
   for the ten pre-existing ledger items, and the settled decisions that must
   NOT be re-litigated. **Start with its "⚠ MAJOR REVISION" section**, which
   corrects four load-bearing claims from the first draft.

That is the whole chain. Everything needed to pick up the next action is in
those two files plus the ledger.

Optional depth, not required to act:
`plan/fleet-pin-propagation/research/recovered/` holds the three raw research
inventories the diagnosis summarizes — per-gate `file:line` citations, the full
pin-format table, and each agent's own flagged unknowns. Read them when you
need evidence behind a specific claim; the diagnosis note is the authority.

## What this thread owns

Fleet-wide **pin propagation** and the **consumer-side gates that pin bumps
break** — every pin format, including the image-tag pins.

It does NOT own `plan/fabro-ci-image-factoring/`, which owns the CI substrate
(baked images, hot runners, resource-health-gated rollout). The two threads
meet at exactly one seam: image tags are themselves unmanaged pins, and those
items (`livespec-dev-tooling-fz4`, `livespec-dev-tooling-xb7`) are owned HERE
while what goes *inside* an image is owned THERE. Scope boundary confirmed by
the maintainer 2026-07-19.

## The situation in one paragraph

41 open pin-bump PRs across 8 member repos, every master green. Those two
facts together are the diagnosis: the fleet is green *at rest* but cannot
absorb propagation, and the green masters are what hid it. The 41 are not 41
breakages — ~29 are superseded PRs nothing ever closed, and exactly one repo
(`livespec-console-beads-fabro`) is genuinely blocked, 12 releases behind,
by a gate the fan-out structurally cannot satisfy. Do not read the red check
names on a superseded PR as a symptom list; its branch is simply stale.

**The noise half is now CLEARED (2026-07-19).** The paragraph above is the
original diagnosis and is kept for the reasoning; the counts in it are
historical. Re-measured immediately before cleanup: **43** open bump PRs, not
41 — it had drifted up by 2 exactly as predicted. Each was classified
individually (target version vs. the version its own master carries for the
same source repo): **30 provably superseded, 13 not, 0 ambiguous.** The 30 were
closed with an explanatory comment and their branches deleted.

**Fleet-wide open bump PRs: 43 → 13. Seven of eight member repos now carry
ZERO.** All 13 remaining are `livespec-console-beads-fabro`, so "exactly one
repo is genuinely blocked" is now directly visible in the PR listing instead of
buried under the noise. Subsequent fleet sweeps read true.

**A third supersession category the diagnosis did not name.** Of those 13
console PRs, only **one** is genuinely live — `#320`, targeting the latest
`v0.18.2`. The other **twelve** are superseded by a *newer open sibling PR*
rather than by master (console pins core at `v0.16.0`; they target `v0.17.0` ..
`v0.18.1`, all newer than the pin but older than #320). So:

| Category | Count | Disposition |
|---|---|---|
| Superseded by master | 30 | CLOSED by this pass |
| Superseded by a newer OPEN sibling PR | 12 | left open deliberately |
| Genuinely live | 1 (console `#320`) | left open |

The twelve were left open on purpose: they are the console's own blocked pin
train, and collapsing it belongs to `livespec-console-beads-fabro-tafkuw`, not
to the cleanup. **Whoever implements the `livespec-dev-tooling-q37xxt`
automation must handle BOTH supersession categories**, or the console
re-accumulates a stack the moment it unblocks.

The one-time cleanup is DONE and journaled on `livespec-dev-tooling-q37xxt`;
that item now tracks the AUTOMATION only. The same pass also confirmed
`livespec-dev-tooling-y6kqgr`'s duplicate defect live: `livespec-runtime`
#206/#208 both targeted dev-tooling `v0.44.0`, and #207/#209 both targeted core
`v0.10.1`.

## ⚠ The epic's cross-tenant refs were ALL DEAD — repaired 2026-07-20

Every one of `livespec-n4ptl2`'s five `non_local_depends_on` entries pointed at
a regroomed-out, CLOSED item. Not one referenced its live replacement, so
reading the epic to find its sibling-tenant work surfaced only closed records.
The table immediately below (§"Filed this session") lists the ORIGINAL ids and
is kept for history; the epic itself now carries the live set:

| was (closed) | now (live) |
|---|---|
| `livespec-dev-tooling-q37xxt` | `livespec-dev-tooling-5o6ssu` |
| `livespec-dev-tooling-y6kqgr` | `livespec-dev-tooling-dqfmjr` |
| `livespec-dev-tooling-f5or5c` | `livespec-dev-tooling-zm5cbp` |
| `livespec-dev-tooling-tuyje7` | `livespec-dev-tooling-gbjuua` |
| `livespec-console-beads-fabro-tafkuw` | `livespec-console-beads-fabro-ogpok4` |

**Nothing was invented** — each replacement was read from the closed item's own
regroomed-out close reason, the authoritative record of the maintainer-owned
cut, so the repair repoints at decisions already made rather than making new
ones. `tafkuw` regroomed into TWO slices; only `ogpok4` is carried, because
`5kd56a` is itself closed (its work landed — see the top-of-file correction).

Verified after the write: `rank` preserved, epic status untouched (`backlog`),
every entry a well-typed `{kind, repo, work_item_id}` dict (bare strings are
rejected by doctor-static), all five targets confirmed live, and
`just check-doctor-static` re-run clean.

**Root cause, filed as a THIRD symptom on `bd-ib-dvmh`.** That record's two
existing symptoms are the CHILD side — groom's `file_approved_slices` records
only LOCAL slices, so cross-tenant replacements are dropped. This is the PARENT
side: when a child is regroomed out, nothing repoints the refs pointing AT it.
Complementary halves of one gap. It is only VISIBLE cross-tenant because local
parent-child edges are native beads edges beads maintains, while
`non_local_depends_on` is livespec metadata nothing maintains — so assume the
same rot in any epic whose children have been regroomed.

## Filed this session (children of `livespec-n4ptl2`)

Cited read-only; check live status in the ledger before acting.

| Item | Tenant | Covers |
|---|---|---|
| `livespec-xw65el` | livespec (core) | Classify every consumer-side gate as (a)-derivable or (b)-needs-live-system |
| `livespec-dev-tooling-q37xxt` | livespec-dev-tooling | Fan-out never closes superseded bump PRs |
| `livespec-dev-tooling-y6kqgr` | livespec-dev-tooling | Fan-out opens duplicate PRs for the same version |
| `livespec-console-beads-fabro-tafkuw` | livespec-console-beads-fabro | The console's captured-manifest gate; the one real blockage |

All four were routed by the intake Definition-of-Ready checklist to the single
status `blocked`, carrying `blocked_reason: needs-human` (one status plus a
reason, not two statuses), because they carry no autonomy tier yet — the same
posture as `livespec-dev-tooling-adqmnm`, whose description ends "Autonomy
tier at groom." Each needs a grooming pass before it can be dispatched.

All four are mechanically linked to the epic, in two different ways because
beads edges do not span tenants:

- `livespec-xw65el` (same tenant) — a native beads `parent-child` edge, so it
  renders indented under the epic in `bd list`.
- The other three (other tenants) — typed `sibling_work_item` entries in the
  EPIC's `depends_on`, riding in beads metadata under `non_local_depends_on`
  and resolved by livespec's cross-repo layer. Core's `.livespec.jsonc`
  `cross_repo_targets` declares both tenants so the refs resolve.

The directions differ (child→epic for the local edge, epic→children for the
sibling refs) purely because of that tenant boundary; both are correct. Per
`.ai/no-circular-dependency.md` §"Scope", direction carries no
circular-dependency significance for ledger records.

## Pre-existing items this thread absorbs

Not re-filed; they stay in their own tenants. Verdicts and justification are
in the diagnosis note.

**ALREADY FIXED on master — close-or-narrow, do not implement** (fix commits
verified as ancestors of `origin/master`; per-item acceptance check is scoped
into `livespec-xw65el`): `livespec-dev-tooling-adqmnm` (`8975025`),
`livespec-dev-tooling-q9a` (`5693955`), `livespec-dev-tooling-fz4`
(`ebf54cc`), `livespec-dev-tooling-u0x` (`7dc0d9b`),
`livespec-dev-tooling-xb7` (`b0c320d`), `livespec-o0x1` (fan-out stamps at
`bump-pin-rewrite/action.yml:379`).

**Genuinely open, absorbed as children in spirit:** ~~`livespec-p9s0` (stale
local-clone false reds), `livespec-dev-tooling-p73` (pin-freshness
first-record blind spot).~~ — see the verification sweep below; `p73` is closed,
`p9s0` is confirmed live.

**Premise does not reproduce — re-derive or close:**
`livespec-console-beads-fabro-7wy`.

### Verification sweep, 2026-07-19/20 — every remaining item checked live

Each was re-verified against `origin/master` before any disposition, because six
items in this thread had already turned out to be stale records. The sweep found
the population genuinely mixed — one fixed, one live, one settled, one stale
evidence — which is why "verify before implementing" is the standing rule here.

| Item | Verdict | Evidence |
|---|---|---|
| `livespec-dev-tooling-p73` | **CLOSED — already fixed** | The `.[0].current_value` jq collapse is gone; selection now comes from the tested `pin_staleness` module, and the surviving comment names the item by id as the resolved cause. Fix `4ad8344`, confirmed an ancestor of `origin/master` |
| `livespec-p9s0` | **LIVE — do not assume fixed** | Path A still does `git -C <local_clone> show HEAD:justfile`; the GitHub-API read is only a FALLBACK taken when Path A *fails*, so a stale-but-valid clone never reaches it |
| `livespec-console-beads-fabro-tafkuw` | **LIVE, and its owed design decision is now SETTLED** | See the diagnosis note's §"scope question" — the stamp is keyed to the core pin while the fixture depends on the orchestrator's key set, whose two emitting modules have 1 and 2 commits ever |
| `livespec-dev-tooling-tuyje7` | **LIVE** | All three workflow files still claim `just check` runs; `bump-pin-rewrite/action.yml` explicitly documents that it deliberately does NOT run the consumer's `just check` |
| `livespec-dev-tooling-f5or5c` | **EVIDENCE STALE, framing too strong — NOT closed** | Claimed producer at `python-v0.43.2` vs consumers `v0.49.2`; both now `python-v0.50.3`. Self-bumps DO happen and ARE automated (`4f47762`, bot-authored). Real defect is SPORADIC-WITH-SKIPS (v0.46.5 → v0.50.1 skipped v0.47–v0.49), not absent |

`livespec-p9s0` gained a new dimension worth carrying: it and `livespec-fxxfq6`
are two faces of one weakness — the cross-repo wiring check's notion of "the
sibling's state" is **environment-dependent**, reading local clone `HEAD`
locally and a fresh clone in CI. That split is exactly why the 2026-07-19
breakage blocked every local push while master CI stayed green. Fix either with
the other in view.

Linked but NOT owned: `livespec-dev-tooling-9j8.6` (CI-logic extraction epic —
this thread depends on it, must not absorb it), `livespec-dev-tooling-q9a`
(CI-matrix hygiene, not pin propagation).

### ⚠ The `livespec-dev-tooling-9j8.6` dependency is OPEN, and it collides with four queue items

Verified 2026-07-20. Two traps here, one about status and one about sequencing.

**Do not read the parent epic's status as the dependency's status.** The parent
`livespec-dev-tooling-9j8` is **CLOSED**, but `livespec-dev-tooling-9j8.6` is
**`backlog`** — still open. The epic's closure is deliberate and correct, not a
ledger defect: its close reason reads *"Planning lane archived; remaining
implementation/gate work stays tracked as child ledger items."* So checking the
epic and concluding "the dependency is satisfied" is wrong at the wrong level.
Seven of that epic's nine children are still `backlog`.

**The collision.** `livespec-dev-tooling-9j8.6` extracts untested logic out of
exactly the files this thread's fixes must edit:

- `reusable-pin-freshness.yml:124-168` — the awk ordinal-distance staleness compare
- `reusable-release-dispatch.yml:101-134, 204-237` — manifest curl + comment-strip
  + **`.fleet // .members` array build**, dispatch payload, `gh api`, http-status
  soft-fail branching

Four queue items land in that same code:

| Queue item | Touches |
|---|---|
| `livespec-dev-tooling-q37xxt` | fan-out close-superseded logic |
| `livespec-dev-tooling-y6kqgr` | fan-out dedupe against open PRs |
| `livespec-dev-tooling-f5or5c` | the release-dispatch matrix (the "excludes this repo" line) |
| `livespec-bg47fr` | **the `.fleet // .members` array build itself** |

`livespec-bg47fr` is the sharpest case: adopters never receive a dispatch
*because* the matrix is built from `.members`, and that array build is a named
extraction target of `livespec-dev-tooling-9j8.6`. Implementing the adopter fix
in shell first and extracting afterward is either double work or a silent drop of
the change during extraction.

**MEASURED 2026-07-20 — the adopter numbers `bg47fr` never took.** Latest
livespec release at measurement: **v0.18.4**. Its replacement slices are
`livespec-qhxcsp`, `livespec-dev-tooling-qrunmn` (released posture) and
`livespec-dev-tooling-z7wxbd` (pinned posture); the measurement is journaled on
the latter two.

| adopter | posture | pin | gap | last pin change |
|---|---|---|---|---|
| `openbrain` | pinned | **v0.6.10** | ~12 minors | 2026-07-08, human |
| `resume` | pinned | **v0.7.1** | ~11 minors | 2026-07-10, human |
| `homelab` | released | **v0.17.1** | ~1 minor | 2026-07-18, human |

This confirms the earlier unmeasured guess that `openbrain` is staler than
`resume`, and it establishes the core defect **by commit authorship rather than
by inference**: NOT ONE adopter pin was ever moved by `livespec-pr-bot[bot]`.
All three were hand-edited, each as a side effect of some other change
(onboarding, a compatibility fix, a store migration). Fleet MEMBERS get
bot-authored bumps by name through v0.50.8. So "no adopter is wired into the
fan-out" is now direct evidence, not a deduction from staleness.

**⚠ A TRAP IN THAT TABLE — `homelab` is NOT evidence that the released-posture
path works.** At ~1 minor behind it looks healthy beside the other two. That is
an artifact of RECENT ONBOARDING (its pin was hand-set on 2026-07-18 when the
repo was seeded), not of any fan-out reaching it. Nothing automated will move
it, and it will drift exactly as the other two did — it is simply younger.
Sampling adopter staleness on a single day would wrongly suggest the released
path is fine and only the pinned path is broken. **Both are unwired**, which
matters because `qrunmn` is scoped precisely to the released-posture path.

**⚠ METHOD TRAP, and it fails SILENTLY.** `openbrain` and `homelab` default to
**`origin/main`**; `resume` and every fleet member default to **`origin/master`**.
Reading `origin/master:.livespec.jsonc` in the first two returns nothing and
reads as "no pin declared" rather than as an error — it under-reported two of
three adopters on the first attempt here. Any cross-repo adopter sweep MUST
resolve each repo's own default branch (`git rev-parse --abbrev-ref origin/HEAD`)
instead of assuming `master`.

**Recommendation for grooming (a sequencing call, still the maintainer's):**
decide `livespec-dev-tooling-9j8.6`'s position relative to these four BEFORE
cutting any of them. Extracting first means the fixes are written once, in tested
Python. Fixing first means writing them twice. The one thing to avoid is cutting
them without making the choice at all.

## ⚠ TWO SESSIONS ARE IN THIS EPIC — read before dispatching anything

A second session groomed `livespec-xw65el` into three replacement slices
(`livespec-e7lanq`, `livespec-u7x5zn`, `livespec-b7ropo`) while this session
was working. **Dispatch is theirs**; maintainer-directed 2026-07-19, this
session stood down from dispatching rather than risk duplicate worktrees and
conflicting closes.

**RESOLVED — the grooming session dispatched them, so this coordination note is
now history rather than an open hazard.** `livespec-e7lanq` and
`livespec-b7ropo` are both merged (PRs #1459 / #1462); `livespec-u7x5zn` waits
on the acceptance gate. No duplicate worktrees or conflicting closes occurred.
See §"NEXT ACTION" for the single remaining human step.

**The groom was cut against a STALE diagnosis** — it predates the recovery, so
each slice carried "treat the earlier attempt's absence as absence," which is
no longer true. All three bodies have since been corrected, in two different
ways (maintainer-approved 2026-07-19; the CUT was left intact, since grooming
is maintainer-owned):

- `livespec-e7lanq` and `livespec-u7x5zn` were **fully re-scoped**, not merely
  annotated. `e7lanq` now verifies and completes the recovered 12-gate table
  instead of producing it. `u7x5zn` was re-scoped twice: its second body told
  an agent to close six items and file three gaps that a Fable review then
  found were ALREADY closed and filed (handoff §"COMPLETED 2026-07-19"), so it
  now carries only the genuine residue — naming the 4 (b)-class gates as owing
  design decisions, and chasing the `u0x` facet-(b) and `o0x1` residues.
- `livespec-b7ropo` keeps its original scope (the reverse-hazard search is NOT
  covered by the recovery) with a `READ FIRST` correction: its worked example
  `livespec-console-beads-fabro-7wy` is DISPROVEN and closed, so the sweep
  starts from zero confirmed instances, and its acceptance now admits a
  zero-instance outcome as a valid result.

**Anyone dispatching those slices must read the current bodies, not the
original framing** — two of them would otherwise re-derive an inventory already
committed to master, or re-close closed items.

That session also contributed a measurement this thread lacked: the 8 members
carry **106 distinct `check-*` recipe names across ~490 instances**, of which
only 6 names appear in all 8 repos and 37 are repo-local. That is the
UNFILTERED universe; the recovered inventory's 12 is the pin-bump-reachable
SUBSET. Reconciling those two numbers is the sharpest remaining sweep task.

## NEXT ACTION

**DONE 2026-07-20 — both acceptances and the whole grooming queue are
COMPLETE.** A Fable agent, acting as the maintainer's explicit written
delegate, accepted `livespec-e7lanq` and `livespec-b7ropo` (clause-by-clause
verification with live spot-checks, journaled on each item) and groomed all
eight queue items through the sanctioned path (`drive
resolve-blocked:<id>:backlog` where needed, then the `groom` operation). The
full acceptance evidence, the per-item cuts, and the replacement-slice map are
journaled on the epic `livespec-n4ptl2` (comment dated 2026-07-20) and on each
original item's regroomed-out close record. Everything below this paragraph in
this section is the pre-completion state, kept for the reasoning.

### Adversarial verification round — COMPLETE, no blocking concerns

The maintainer directed that the delegate's work be confirmed by independent
Codex agents until no blocking concerns remained, with a Fable tie-break if the
driving session and Codex disagreed. **Three Codex reviews ran; all closed
clean; no tie-break was needed** (the driving session never disagreed with
Codex). One review indexed 2,568 items across four tenants and found zero
orphans and zero dangling references.

**One genuine blocking concern was found and repaired.**
`livespec-bg47fr`'s regroomed-out reason named only ONE of its THREE
replacement slices. This was NOT a delegate error — it is a SILENT second
symptom of the cross-repo defect the delegate had itself filed as `bd-ib-dvmh`:
`groom`'s `file_approved_slices` records only LOCAL slices in that field, so
cross-tenant replacements are dropped. `livespec-bg47fr` was the ONLY cut in
the set whose slices span two tenants (verified across all eight), so it is the
only exposure. Repaired via `bd close --reason-file`; `status: done` and
`resolution: no-longer-applicable` verified intact afterward. `bd-ib-dvmh` now
carries this as a second symptom plus a regression test to pin.

**Two follow-on defects surfaced BY that repair**, both catalogued in
`.ai/beads-gaps-workarounds.md` as **Entry 13**:
- `.beads/interactions.jsonl` logs only `status` VALUE changes, so
  reason/label/metadata edits are recorded NOWHERE. The repair moved
  `updated_at`/`closed_at` but wrote no log row; the log's newest entry for
  that issue still shows the SUPERSEDED reason.
- The `bd close` reason-rewrite ALSO overwrites `closed_at` with the repair
  time (`23:04:14Z` → `23:41:31Z` on `livespec-bg47fr`). These compound: the
  only surviving record of the true first-close time is the very log Entry 13
  says not to trust. If that timestamp matters, capture it BEFORE repairing.

**Also repaired:** `livespec-b1uo` (unrelated epic) pointed at
`livespec-fxxfq6` as the live tracker for the dual-purpose-registry defect.
This thread closed that item, so the pointer dangled. Repointed to the live
successors `livespec-2hya5g` / `livespec-i6pyy6`.

### SETTLED — the live-exercise rule now covers research deliverables

**Maintainer-declared 2026-07-20.** The rule carried its scope qualifier in
sentence 1 ("any *behavior-bearing change*") but omitted it in sentence 2's
unqualified `MUST NOT trigger accept:` — and that valve gates EVERY item. Both
readings were defensible and produced opposite actions.

Resolved: **ad hoc adversarial review IS the discharge mechanism** for
non-behavior-bearing (research/document) deliverables, and satisfies the
`ai-then-human` acceptance policy's second leg. The review must re-derive the
deliverable's factual claims against live state rather than trust the artifact,
CI-green, or its author. What never relaxes is "no release with zero
verification" — not the particular form. Text amended in livespec core
`AGENTS.md` (surfaced as `.claude/CLAUDE.md` via symlink); `livespec-hmstw3`
closed with the decision.

**LANDED — nothing in flight.** That amendment merged as PR
[#1488](https://github.com/thewoolleyman/livespec/pull/1488), and this handoff's
own update merged as [#1490](https://github.com/thewoolleyman/livespec/pull/1490);
both were verified present on `origin/master` and on the primary checkout's disk
before this session declared itself ready. No PR from this session is awaiting a
merge, so **do not open by chasing one** — go straight to the next actions below.

### ⚠ LATER THE SAME DAY — one of the two "blockers" is FIXED and the other item's work LANDED

**Read this before the dispatch-round subsection below; it supersedes two of
its claims.** Both were true when written and both changed within hours.

**1. `bd-ib-w3d0` is FIXED and CLOSED.** The orchestrator landed
`c8bde4a fix: discover the dispatch target's own committed Fabro workflow`
(released 0.45.11). `workflow_toml()` now resolves by precedence: explicit
`--workflow` → **the dispatch target's own committed
`<repo>/.fabro/workflows/implement-work-item/workflow.toml`** → the plugin's
bundled workflow. That is exactly the fix the record proposed, and its
docstring names this scenario. Verified LIVE on the same work-item, not by
reading the diff — the image actually pulled flipped:

    03:25  python-agent-v0.50.4       FAILED (cargo/rustc absent)
    04:21  python-agent-v0.50.5       FAILED (cargo/rustc absent)
    06:06  python-rust-agent-v0.50.7  exit 0
    06:50  python-rust-agent-v0.50.8  exit 0

The console's `python-rust-agent` pin stopped being dead config. One residue
kept: nothing yet pins "a non-Python consumer resolves ITS OWN image", so a
future re-layering could silently reintroduce it — that is a test-coverage
item, not an open bug.

**2. `livespec-console-beads-fabro-5kd56a`'s work LANDED — do NOT treat its
closure as a lost item.** Its implementation merged as console `f5fa99f`
("fix: key config-manifest staleness to declared keys", 06:01:54Z): 210 lines
of `crates/console-completeness-check/src/lib.rs` plus `main.rs`, the justfile,
and the manifest fixture. The re-key is DONE.

**CORRECTION to an earlier read (mine).** An earlier note in this session
flagged `5kd56a`'s closure as possibly UNINTENDED, because it carries
`resolution: None` and an EMPTY `close_reason` and spawned no replacement
slices. That inference was WRONG: the work was implemented and merged. What is
actually wrong is only the RECORD-KEEPING — a completed item closed with no
resolution and no reason, which is exactly what made it read as an accident.
Do not reopen it; if anything, backfill the reason.

**3. The `ogpok4` dependency is genuinely satisfied, but its STATE section is
now STALE.** `livespec-console-beads-fabro-ogpok4` (slice 2 of 2, "land the
console's core-pin bump") depends on the re-key slice, and that dependency is
GENUINELY satisfied by `f5fa99f` — not merely by a status flip. BUT its body says
"13 open bump PRs; only #320 (targeting core v0.18.2) is genuinely live; the
other twelve ... superseded". Measured live 2026-07-20: the console carries
**ONE** open bump PR, **#328 → v0.18.4**. The twelve-deep train it was cut to
collapse was already collapsed by `5o6ssu`'s automation, and the surviving PR
is a different number targeting a different version. **Re-read the live PR list
before executing `ogpok4`; do not act on #320.**

### DISPATCH ROUND COMPLETE 2026-07-20 — 2 of 4 merged, 2 blocked on NEW infra defects

**Read this subsection instead of the outage narrative that follows it.** All
four slices were dispatched. Two landed end-to-end; two were stopped by
infrastructure defects that did not previously exist in this thread's record,
both now filed.

| Slice | Outcome |
|---|---|
| `livespec-2hya5g` | **MERGED** — livespec PR #1508 (`3496b45a`), now at `acceptance` |
| `livespec-dev-tooling-5o6ssu` | **MERGED** — livespec-dev-tooling PR #495 (`17a5b633`), now at `acceptance` |
| `livespec-dev-tooling-gbjuua` | BLOCKED — `bd-ib-nga9`; recovered to `ready` |
| `livespec-console-beads-fabro-5kd56a` | BLOCKED — `bd-ib-w3d0`; recovered to `ready` |

Both merged items sit at `acceptance` under `ai-then-human` and were
deliberately NOT self-accepted — that policy exists to require the maintainer.

**Two NEW infrastructure defects, both filed in the
`livespec-orchestrator-beads-fabro` tenant (P1), both blocking a groomed slice
of THIS thread:**

- **`bd-ib-w3d0`** — the dispatcher resolves the Fabro `workflow.toml`, and
  therefore the SANDBOX IMAGE, from `plugin_root()` and NEVER from `--repo`
  (`commands/_dispatcher_paths.py::workflow_toml()`). The plugin pins the
  Python-only `python-agent-*`, so the console's own correct
  `python-rust-agent-v0.50.5` pin is DEAD CONFIG and every Rust-touching
  console item dies at `Implement` on absent `cargo`/`rustc`. Reproduced three
  times by two different actors. Note the asymmetry: `journal_path()` in the
  same module IS repo-relative.
  **This is NOT the image-factoring thread's missing work** — that thread built
  `python-rust-agent` correctly and the console pins it correctly. Only the
  SELECTION path is wrong. It is a regression from the `-agent-` layer split:
  `…-f2k` is also Rust-touching and dispatched fine on 2026-07-19 using
  `python-v0.48.1`, so the pre-split `python-` images still carried Rust.
- **`bd-ib-nga9`** — the Fabro sandbox's App token lacks `workflows`
  permission, so any item editing `.github/workflows/` completes its
  implementation and then fails at publish. `gbjuua` is comment-only edits to
  three workflow files and still cannot land. Worse, the run raised an
  interactive `[R]etry/[I]/[A]` prompt with nobody attached, which is how the
  item stranded.

**⚠ DO NOT "fix" this file's workflow-permission finding — it is CORRECT.**
§"COMPLETED 2026-07-19" says the fleet App HAS `workflows` permission. That was
independently RE-CONFIRMED 2026-07-20: `livespec-pr-bot[bot]` authors
`.github/workflows/` commits routinely in both repos (dev-tooling `ac5217e`,
`104f038`, `36c60fb`; livespec `0d67e14d`, `fc84ef11`), as recently as the
v0.50.7 bump. `bd-ib-nga9` is a DIFFERENT credential: the FAN-OUT path can
write workflow files; the FABRO SANDBOX token cannot. An earlier revision of
this section wrongly read the two as contradictory. They are not — do not
weaken the fan-out finding, and do not assume the sandbox inherits it.

**Both blocked items were recovered** from the stranded-`active` shape via
`drive --action move:<id>:ready` and verified. Their scopes, cuts, and
acceptance criteria are UNCHANGED and remain valid; each unblocks the moment
its filed defect is fixed.

**A grooming lesson worth carrying:** both blockers are hidden
factory-eligibility constraints. An item can pass grooming, carry autonomy tier
`factory`, be admitted, burn a full 10-minute run, and only then fail on the
substrate. "Does this item edit `.github/workflows/`?" and "is this a non-Python
repo?" are both knowable BEFORE dispatch.

---

### Superseded outage narrative — kept for reasoning, do NOT act on it

**The GitHub outage described below did NOT ultimately block this thread.** It
was real and it did fail the first dispatch attempt, but it cleared, and all
four slices were dispatched afterward (results above). Two probes used to track
the recovery were INVALID and are recorded here so the mistake is not repeated:
`git ls-remote` succeeds ANONYMOUSLY on this public repo and never exercises
the App-token mint, and a `git push --dry-run` from the PRIMARY CHECKOUT is
refused by the repo's own commit-refuse hook rather than by GitHub. The valid
probe is `git push --dry-run` **from a worktree**; the real health signal is
recent CI runs plus that probe, not the status page, which still showed
`partial_outage` while the fleet was merging normally.

All four slices below were confirmed `ready` with `admission:auto` and autonomy
tier `factory`, and capacity was confirmed available. Dispatch was attempted and
**halted after the first item on an external GitHub outage, not on anything in
this thread's state.**

`drive --action impl:livespec-2hya5g` was admitted (so this was NOT the false-green
capacity case) and then FAILED at stage `run-config-overlay`:

```
C-mode dispatch refused: GitHub App token mint failed:
GitHub App API call to https://api.github.com/app/installations
failed: HTTP Error 503: Service Unavailable
```

`githubstatus.com` confirmed the cause as a live incident, not a fleet defect:
**API Requests = `partial_outage`** (which is what fails the App-token mint) and
**Actions = `partial_outage`** (two unresolved incidents, opened 2026-07-19
23:34Z and 2026-07-20 00:25Z).

**The remaining three were deliberately NOT dispatched.** Both halves of the
factory path are impaired: the mint needs API Requests, and the janitor hard
gate needs Actions. Dispatching into that would have stranded three more items
mid-flight — worse than waiting, because a Fabro-launched item strands with a
sandbox and an open PR rather than merely a status.

**The failed dispatch stranded `livespec-2hya5g` in `active` with nothing
running.** There is no automatic reaper for this shape — `reconcile-merged`
only covers an already-MERGED active item, and `ledger-normalize` only remaps
`open`→`backlog` / `in_progress`→`active`. It was recovered through the
sanctioned human valve:

```
drive --action move:livespec-2hya5g:ready --repo /data/projects/livespec
```

Verified back at `ready` afterward. **If a dispatch fails at
`run-config-overlay`, expect this and use `move:<id>:ready`** — do not
hand-edit the ledger, and do not leave it `active` (an `active` item is not a
dispatch candidate, so the retry would silently no-op). One residue worth
knowing: the move valve does NOT clear the `assignee`, so the item sits at
`ready` with a stale `assignee: fabro`. That did not block anything, but do not
read it as evidence of an in-flight dispatch.

**To resume:** re-check `https://www.githubstatus.com/api/v2/status.json` and
re-run the four dispatches below from the top. Nothing else in this thread's
state changed — the only ledger writes this pass made were the stranding and
its reversal, which cancel out.

The thread's NEW next actions:

**Action 1 is DONE — see §"DISPATCH ROUND COMPLETE 2026-07-20" above for what
landed and what blocked. The live next actions are now:**

- **A. Accept (or reject) the two merged slices.** `livespec-2hya5g` and
  `livespec-dev-tooling-5o6ssu` both sit at `acceptance` under
  `ai-then-human`. Maintainer-owned; an operator accepting on the maintainer's
  behalf defeats the policy.

  **The AI leg is DONE for both — full clause-by-clause evidence is journaled
  on each item (2026-07-20), so the human leg should be quick.** Headlines:

  - `livespec-2hya5g`: `just check-doctor-static` **exit 0 LOCALLY against real
    sibling checkouts** (the item warned CI is not evidence) — 20 pass, 1
    legitimate skip, and the decisive
    `doctor-wiring-completeness-cross-repo: PASS` with the console registered,
    i.e. the 53 drift pairs are gone. `just check` 71/71.
  - `livespec-dev-tooling-5o6ssu`: the **live-exercise clause is genuinely
    satisfied**, not waived. Two real releases (0.50.7, 0.50.8) fired after the
    merge, and a fleet sweep of all eight members found **ONE** open bump PR
    total, zero superseded. The console went **13 → 1**, and the survivor
    (#328 → v0.18.4) is above its master pin (v0.16.0), so it is genuinely
    live. That is supersession category 2 working in production. Delivered
    shape also matches the DO clause: a 287-line tested module invoked from 26
    lines of thin glue. `just check` 60/60.

  **A METHOD TRAP that nearly produced a wrong verdict:** inspecting only the
  MERGE SHA of `5o6ssu` (`17a5b633`) shows a 1-line `action.yml` change and
  makes it look as though the required module was never written. That is an
  artifact of reading ONE commit of a multi-commit PR. **Verify a PR's full
  file set, not the merge commit.**

  **This acceptance is the thread's only remaining unblock, and it releases two
  MORE slices.** Verified live 2026-07-20: with the four dispatched, there is
  NO further agent-dispatchable work in this thread — every other candidate is
  gated behind these two acceptances.

  | Follow-on slice | Blocked by | Releases when accepted |
  |---|---|---|
  | `livespec-dbbgoc` (the CI-blindness companion to the registry split) | `livespec-2hya5g` | ✅ |
  | `livespec-dev-tooling-dqfmjr` (fan-out dedupe, the `y6kqgr` replacement) | `livespec-dev-tooling-5o6ssu` | ✅ |

  **Both were pre-verified 2026-07-20 (journaled on each), because each one's
  BLOCKER edited the very code the slice targets — so their premises could have
  gone stale between grooming and dispatch. Both still hold, with adjustments:**

  - `livespec-dbbgoc`: premise intact — Path A still reads
    `git -C <local_clone> show HEAD:justfile` with no fetch, Path B still
    fallback-only. But **DO step 3 is ALREADY SATISFIED** by `2hya5g` (the check
    now reads the conformance registry), so remaining scope is steps 1–2 only.
    A ride-along worth taking: `filter_sibling_targets` still names its
    parameter `cross_repo_targets` while every caller passes the CONFORMANCE
    registry — the same overloaded-name hazard that caused this thread, now
    re-created at the code level.
  - `livespec-dev-tooling-dqfmjr`: defect still live — `gh pr create` runs with
    NO existence check, and supersession runs AFTER it. **`5o6ssu` pre-wired the
    fix**: it ships `class BumpKey` documented as "the shared bump identity used
    by supersession and future dedupe logic". **And it is NOT exposed to
    `bd-ib-nga9`** — it edits `.github/actions/…/action.yml`, a composite action,
    not `.github/workflows/`. Proven, not assumed: `5o6ssu` modified that same
    file and merged through the factory. So this slice has no substrate blocker
    and should dispatch cleanly.

  **⚠ Do NOT cite the clean fleet sweep as evidence `dqfmjr` is unnecessary.**
  One open bump PR fleet-wide proves duplicates are CLOSED, not that they are
  never OPENED. The wasteful create and its CI run still happen; only the
  residue is swept. That is cleanup, not prevention.

  So accepting two items releases two more, and both follow-ons avoid the new
  infra defects (`dqfmjr` is a Python repo and touches no
  `.github/workflows/`), so they should dispatch cleanly.

  **A TRAP FOR THE NEXT SESSION — do not read a `ready` status as
  dispatchable.** Both follow-ons show livespec status `ready` with
  `admission:auto`, which looks dispatchable and is NOT. The dispatcher keeps
  its OWN ready set, which additionally requires each blocker to be `done` —
  and only the human acceptance moves an `acceptance` item to `done`. Both were
  attempted and cleanly refused:

  ```
  ERROR: requested work-item(s) not in the ready set: livespec-dbbgoc
  ```

  This is a `--action impl:` exit code **3** (precondition), NOT the
  empty-journal false-green of `bd-ib-c4jfp6`: the refusal is honest, nothing
  is admitted, no Fabro run is burned, and the item is NOT stranded `active`.
  Attempting a gated item is therefore cheap and safe — but pointless until the
  acceptance lands.
- **B. Route `bd-ib-nga9`** (sandbox `workflows` permission),
  `livespec-orchestrator-beads-fabro` tenant. **This is now the thread's real
  critical path — see item C.**

  Its sibling `bd-ib-w3d0` (workflow/image resolution) is **FIXED and CLOSED**
  (`c8bde4a`, released 0.45.11) — do not route it. `nga9` was deliberately
  re-tested after that fix landed, in case both had been addressed in the same
  sweep; they had not. `livespec-dev-tooling-gbjuua` was re-dispatched on a
  later plugin build and failed identically at publish, on the same file, for
  the same reason. **Two independent reproductions; the two defects were
  genuinely unrelated.**

  Re-dispatching a workflow-file-editing item before this is fixed is worse
  than a no-op: the run implements and COMMITS correct work, then is rejected
  at push and throws it away, then parks on an interactive
  `[R]etry/[I]/[A]` prompt with nobody attached and strands the item `active`.
  `gbjuua` has now been recovered from that shape three times via
  `drive --action move:<id>:ready`.
- **C. Groom `livespec-dev-tooling-9j8.6`** — still needed, but **grooming it
  is no longer sufficient, and it is no longer the true critical path.**

  **`bd-ib-nga9` now sits UNDER `9j8.6`.** Verified 2026-07-20: `9j8.6`'s DO
  clause is "move the decision logic into tested importable modules called from
  thin `run:` glue" for `reusable-pin-freshness.yml` and
  `reusable-release-dispatch.yml` — which necessarily EDITS both workflow
  files. The Fabro sandbox token cannot push edits under `.github/workflows/`
  (`bd-ib-nga9`, re-confirmed live with two independent reproductions). So even
  a perfectly groomed `9j8.6` cannot be factory-dispatched today: it would
  implement, commit, and then fail at publish.

  Two of the three slices `9j8.6` gates are in the same position —
  `livespec-dev-tooling-qrunmn` (`bump-pin-from-dispatch.yml`,
  `reusable-release-dispatch.yml`) and `livespec-dev-tooling-z7wxbd`
  (`reusable-pin-freshness.yml`) — and the third,
  `livespec-dev-tooling-zm5cbp`, is **DOUBLE-gated**: blocked on `9j8.6` AND on
  `nga9` (it edits `ci.yml` + `bump-pin-from-dispatch.yml`).

  **So the ordering is: fix `bd-ib-nga9` FIRST, then groom `9j8.6`, then the
  three slices.** Grooming first is not wasted — the cut is still maintainer-
  owned and still needed — but it will not produce a dispatchable item on its
  own, and queueing any of these into the factory before `nga9` is fixed burns
  a full implement cycle per attempt and throws the (correct) work away at the
  push step.

  **Blast radius, for prioritising `nga9`.** A keyword scan of every live
  work-item across four tenants found **~24** whose scope names a workflow
  file: `livespec` 5, `livespec-dev-tooling` 14,
  `livespec-console-beads-fabro` 1, `livespec-orchestrator-beads-fabro` 4.
  **That 24 is an UPPER BOUND from a heuristic** — an item that merely CITES a
  workflow file as evidence scores the same as one that edits it, so confirm
  per item before acting on the number. Three were confirmed by reading their
  scopes as genuine edits: `9j8.6`, `gbjuua`, `zm5cbp`. Full measurement is
  journaled on `bd-ib-nga9`.

1. ~~**Dispatch the four READY slices**~~ — **DONE 2026-07-20.**
   `livespec-2hya5g` (registry split, livespec) → MERGED #1508;
   `livespec-dev-tooling-5o6ssu` (close-superseded automation) → MERGED #495;
   `livespec-dev-tooling-gbjuua` (fan-out prose fix) → blocked, `bd-ib-nga9`;
   `livespec-console-beads-fabro-5kd56a` (re-key the completeness stamp) →
   blocked, `bd-ib-w3d0`.

   **⚠ `drive` LIES ABOUT SUCCESS WHEN IT DISPATCHES NOTHING — read this
   before you dispatch, not after.** When the dispatcher admits zero items,
   the loop exits 0 with an empty journal and `_dispatch_status` maps that
   onto `status: "green"` with the summary "Dispatcher reported green for
   <id>". The item never moves. Filed as `bd-ib-c4jfp6`
   (`livespec-orchestrator-beads-fabro` tenant); details at §"A defect found
   while dispatching" below.

   **CORRECTED 2026-07-20 — the trigger above was stated wrong.** An earlier
   revision said "`--budget 1 --parallel 1`, so if another item is already
   `active` there is NO CAPACITY". That is FALSE and it will cause a
   mis-diagnosis. `--parallel` only sizes the `ThreadPoolExecutor`; it is not
   a capacity gate. The real gate is in
   `commands/_dispatcher_admission.py::admit_and_select`:

   ```
   active_count = sum(1 for item in items if item.status == "active")
   free_slots   = max(0, resolve_wip_cap(cwd=repo) - active_count)
   ```

   `resolve_wip_cap` reads `livespec-orchestrator-beads-fabro.dispatcher.wip_cap`
   from the repo's `.livespec.jsonc`, defaulting to `DEFAULT_WIP_CAP = 5`.
   NONE of the three tenants in this thread sets that key, so the cap is **5**
   everywhere. One `active` item therefore leaves FOUR free slots, not zero.
   Verified live 2026-07-20: core carried 3 `active` items and
   `livespec-2hya5g` was still admitted normally.

   So the false green appears only when `active_count >= 5` in that tenant —
   a much rarer condition than the original text implies. Do not conclude
   "capacity" from the mere existence of one active item; count them against
   the cap. The operative advice is unchanged and still cheap: **dispatch one
   at a time and re-read the item's status after each.** A `green` verdict
   whose `stdout_json` is `[]` means NOTHING HAPPENED.

   So: **dispatch these ONE AT A TIME, and after each one re-read the item's
   status** to confirm it actually went `active`. A `green` verdict whose
   `stdout_json` is `[]` means NOTHING HAPPENED. Do not fire all four and
   assume four dispatches.
2. **Groom `livespec-dev-tooling-9j8.6`** — the sequencing call gated three
   slices (`livespec-dev-tooling-qrunmn`, `livespec-dev-tooling-z7wxbd`,
   `livespec-dev-tooling-zm5cbp`) on that extraction, so it is now this
   thread's critical path. It belongs to the shell-logic-hardening epic, not
   this one; groom it in its own context.
3. ~~`livespec-u7x5zn` self-routes now that `livespec-e7lanq` is `done`
   (admission auto) — no action needed, just don't re-block it.~~
   **FALSIFIED 2026-07-20 — it did NOT self-route, and "no action needed" will
   strand this item indefinitely if believed.**

   Measured live: `livespec-e7lanq` is **`closed`**, and `livespec-u7x5zn` is
   still **`pending-approval`**. The condition the claim was waiting on has
   been satisfied and the routing did not happen. Two independent confirmations
   that it is genuinely not dispatchable, not merely mislabelled:

   - `dispatcher.py loop --repo /data/projects/livespec --budget 5 --dry-run`
     returns `[]` — the tenant offers ZERO candidates.
   - `drive --action impl:livespec-dbbgoc` (a different `ready` item in the
     same tenant) is refused with `not in the ready set`, exit 3.

   **Mechanism — HYPOTHESIS, deliberately not asserted.** Readiness is
   `lane_of(...).name == "ready"`, and `_has_open_dependency` blocks on any
   `depends_on` entry resolving to `OPEN`
   (`_vendor/livespec_runtime/work_items/lifecycle.py`). `u7x5zn`'s remaining
   non-closed dependency is the EPIC `livespec-n4ptl2`, which is `backlog`;
   `dbbgoc`'s is `livespec-2hya5g`, which is `acceptance`. If `backlog` and
   `acceptance` both resolve as `OPEN`, both observations follow. What does NOT
   fit that story: `livespec-e7lanq` and `livespec-b7ropo` carry the same epic
   dependency and DID dispatch to completion. So either the epic's status
   changed since, or the blocking entry is something else. **Do not act on the
   mechanism until it is confirmed** — a probe attempting to read the
   dispatcher's own `depends_on` for these items failed to import
   (`load_items` is not a public symbol of `_dispatcher_loop`), and the
   shortcut check via `bd list --json` is VACUOUS because that surface omits
   the `dependencies` array. Only `bd show --json` carries it.

   What IS safe to rely on: attempting a gated item is cheap and harmless
   (exit 3, no admission, no Fabro run, no strand), so the next session can
   simply retry `u7x5zn` after the acceptances land and see whether it frees.
   If it does not, the epic-dependency hypothesis above is the first thing to
   test — and note that an epic which stays `backlog` while its children need
   it `done` would deadlock every child under it.

One defect found while grooming, filed as `bd-ib-dvmh`
(`livespec-orchestrator-beads-fabro` tenant): groom's cross-repo slices mint
local-prefix ids the target tenant's bd prefix guard rejects; worked around by
minting native ids and repointing `livespec-qhxcsp`'s sibling refs.

---

**Blocked on the maintainer — TWO acceptances, then a grooming queue.** The
grooming session dispatched both `READY` slices; both are merged and their
artifacts are on master. No further work here is agent-eligible.

**Correction:** an earlier revision of this section said "one acceptance". It is
**two** — `livespec-e7lanq` AND `livespec-b7ropo` are both at `acceptance`.
Verified live 2026-07-20.

Everything else in the thread has now been re-verified against `origin/master`
and needs exactly one thing: **grooming**, which is maintainer-owned by design
(the `groom` operation's cut belongs to the maintainer, and none of these items
carries an autonomy tier yet). The evidence work is done; the cuts are not.

Ids are written tenant-prefixed IN FULL, and each tenant repo is named in full,
because this queue spans three tenants and a bare suffix cannot be turned into a
command. Read each tenant from its own clone (`/data/projects/<repo>`) — the read
surfaces resolve the tenant from the working directory.

| Item | Tenant repo | Verified state | What grooming must decide |
|---|---|---|---|
| `livespec-fxxfq6` | `livespec` | backlog | Which of the two fixes; **both are single-repo edits** (the "cross-repo + pin bump" claim was false). Re-read its corrected workflow-permission paragraph first |
| `livespec-p9s0` | `livespec` | LIVE | Whether to make the canonical ref the default rather than the fallback. Design with `livespec-fxxfq6` in view — same weakness |
| `livespec-bg47fr` | `livespec` | LIVE, understated | Whether adopters get the SAME fan-out as members or only a staleness signal. Note `openbrain` is at `v0.6.10` — staler than `resume`, and the body never measured it |
| `livespec-console-beads-fabro-tafkuw` | `livespec-console-beads-fabro` | LIVE, design settled | Only the implementation shape remains; the invalidation-trigger question is answered (see diagnosis §"scope question") |
| `livespec-dev-tooling-q37xxt` | `livespec-dev-tooling` | backlog CLEARED | Automation only. Must handle BOTH supersession categories |
| `livespec-dev-tooling-y6kqgr` | `livespec-dev-tooling` | CONFIRMED live | Dedupe design; co-design with `livespec-dev-tooling-q37xxt` — same `(source_repo, target_version, consumer)` tuple |
| `livespec-dev-tooling-tuyje7` | `livespec-dev-tooling` | CONFIRMED live | Docs-vs-implementation contradiction; decide whether to fix the prose or add the step |
| `livespec-dev-tooling-f5or5c` | `livespec-dev-tooling` | evidence STALE | **Re-scope before grooming** — "nothing fans out to it" is wrong; the real defect is sporadic-with-skips |

**A trap for whoever grooms `y6kqgr` or `q37xxt`:** the duplicate-PR evidence is
no longer observable in the open-PR population, because that population went
43 → 13 and the four PRs that demonstrated it (`livespec-runtime` #206–#209) are
among the 30 closed. Validate a fix against the fan-out's dedupe logic or the
next real releases — **not** by inspecting today's open PRs.

**Accept (or reject) `livespec-e7lanq`.** It sits at `acceptance` under
`acceptance_policy: ai-then-human`; the AI pass verdict was PASS. It was
deliberately NOT self-accepted — that policy exists to require a human, and an
operator accepting on the maintainer's behalf would defeat it.

That one acceptance is load-bearing for the rest of the thread:
`livespec-u7x5zn` is `pending-approval` and NOT rankable, because its blocker
`livespec-e7lanq` must reach `done`, which only the acceptance produces. Note
the `approve:` valve does NOT apply to it — `approve:` requires an
effective-MANUAL item, and `u7x5zn` carries `admission_policy: auto`, so it
routes itself into `ready` once the dependency clears. Do not try to force it.

| Slice | State | What landed |
|---|---|---|
| `livespec-e7lanq` | `acceptance` — **awaits human** | PR #1459 (`63c62dc5`) → `research/recovered-gate-verification.md` |
| `livespec-b7ropo` | merged, dispatcher green | PR #1462 (`805a9dcc`) → `research/reverse-hazard.md` |
| `livespec-u7x5zn` | `pending-approval` | blocked until `e7lanq` is `done` |

**What the two artifacts settled:**

- The recovered 12-gate table is VERIFIED against live sibling clones at named
  SHAs — 9 clean, 3 verified-with-correction (reusable-workflow refs and Fabro
  image tags have moved `v0.49.2` → `v0.50.3`). Both (b) classifications held.
  One recovered unknown resolved (`_vendor` is excluded by both
  `tests_mirror_pairing` and `partition_completeness`); the `f5380aa8`
  auto-merge-bypass unknown remains honestly unconfirmable (Actions history
  aged out). No missed gate found, by a stated method — the fan-out's managed
  pin formats compared against the recipes reading those artifacts. That
  negative is scoped to fan-out-managed artifacts, NOT to all ~106 recipes.
- The reverse-hazard sweep found **ZERO live instances**, and that is a real
  result rather than an absence of effort: the dev-tooling canonical check tree
  is byte-identical from every active consumer's pinned ref (`v0.50.3`) to
  `origin/master`, the core doctor static-check tree is byte-identical from
  every consumer's core pin to master INCLUDING the console's older `v0.16.0`,
  and the reusable-workflow callable contracts are unchanged. The disproven
  `…-7wy` example was re-confirmed disproven from a third direction (identical
  tree object `c6e69209…` at both refs).

**A defect found while dispatching — read before trusting any `drive` verdict.**
`drive --action impl:<id>` reported `status: green` / "Dispatcher reported
green" for `livespec-b7ropo` while dispatching NOTHING; the item stayed `ready`.
Cause: `drive`'s impl path runs the dispatcher with `--budget 1 --parallel 1`,
so with another item already `active` there was no capacity, the loop ran zero
iterations, and `commands/drive.py::_dispatch_status` maps an EMPTY journal plus
exit 0 onto `green`. Filed as **`bd-ib-c4jfp6`** in the
`livespec-orchestrator-beads-fabro` tenant. Until it is fixed, **always confirm
a dispatch by re-reading the item's status** — never trust the green alone. The
re-dispatch after capacity freed worked normally.

## COMPLETED 2026-07-19 — the answerable half of `livespec-xw65el`

- **Workflow-permission contradiction RESOLVED.** The fleet App DOES have
  `workflows` permission: `livespec-pr-bot[bot]` authored real `ci.yml` content
  changes that landed on master (`livespec-runtime 0d6b3a2`, bumping the
  container image across two `container:` blocks). The standing "the App
  deliberately lacks `workflows` permission" decision record is STALE for the
  fan-out path, and `adqmnm`'s "never `.github/workflows/`" acceptance clause is
  MOOT rather than violated. **(a)-class auto-fix design may assume the fan-out
  can write workflow files.**
- **Six already-done items CLOSED**, each checked against its own written
  acceptance with per-item evidence — not bulk-closed: `adqmnm` (`8975025`),
  `q9a` (`5693955`), `fz4` (`ebf54cc`, live-exercise satisfied in production by
  console `a6d7221`), `u0x` (`7dc0d9b`), `xb7` (`b0c320d`), `livespec-o0x1`
  (fan-out stamps at `action.yml:379`). Two carry recorded residue rather than a
  clean close: `u0x` facet (b) (ordered cross-repo merge sequencing — no
  evidence of a fix) and `o0x1` (how a red bump PR reached master remains
  undetermined; Actions history aged out).
- **Three new gaps FILED**: `livespec-dev-tooling-f5or5c` (the producer is
  outside its own fan-out), `livespec-dev-tooling-tuyje7` (three workflow files
  document a `just check` step that does not exist),
  `livespec-bg47fr` (no adopter is wired into the fan-out; `resume` 11 minors
  stale).
- **`livespec-console-beads-fabro-7wy` closed by an independent console-side
  session**, which verified zero `§"` marker hits under `crates/**/src/` and
  confirmed `…-tafkuw` is the ONLY console-side gate on the pin train —
  corroborating this thread's byte-identity disproof from the other direction.

**Do NOT re-run the sweep from scratch.**

Grooming route: the `groom` operation on `livespec-xw65el`. The maintainer
owns the cut.

### The single most important correction

Six of the ten pre-existing ledger items this thread set out to absorb are
**already fixed on master** — including `livespec-dev-tooling-adqmnm`, the
settled "fan-out writes the wiring" decision the whole plan was written to
honor. It shipped 2026-07-09 (`8975025`) and its `blocked-reason:needs-human`
is stale because its blocking dependency closed 2026-07-15. **Do not
re-implement it.** This thread is substantially a ledger-reconciliation job
plus a small number of genuinely-open defects, not the build job the first
draft assumed.

### Scope boundary — the console's cockpit thread

`livespec-console-beads-fabro-tafkuw` and the console's
`plan/cockpit-ux-docs-release/` deliverable **B6** both edit
`crates/console-completeness-check/src/lib.rs` — ~200 lines apart, different
functions, different concerns (B6: which doc surface is read; `tafkuw`: when
the pin stamp invalidates). **B6 goes first, unconditionally.** Full boundary
in the diagnosis note; do not start `tafkuw` before B6's impl lands on console
master.

**Implementation route, for this and every item in this thread: the FACTORY.**
Dispatch through the `drive` operation with action `impl:<work-item-id>`, or
let the Dispatcher drain it once it is `ready`. Do NOT hand-code these in a
planning session and do NOT use the in-session Red→Green `implement`
operation — none of these items is recorded as factory-ineligible.

### Recommended order after the sweep

Ids are written tenant-prefixed in full, because this list mixes three
tenants and a bare suffix cannot be turned into a command.

1. `livespec-dev-tooling-q37xxt` (close superseded PRs) — cheapest, and it
   removes the noise that camouflages everything else. Do it early so
   subsequent fleet sweeps read true.
2. `livespec-console-beads-fabro-tafkuw` — the real blockage. Sequence
   `livespec-console-beads-fabro-7wy` before or with it, or the unblock trades
   one red for another.
3. `livespec-dev-tooling-adqmnm` (already-decided (a)-class mechanism) and the
   unmanaged-pin pair `livespec-dev-tooling-fz4` / `livespec-dev-tooling-xb7`.
4. `livespec-dev-tooling-y6kqgr`, `livespec-dev-tooling-p73`,
   `livespec-dev-tooling-u0x`, `livespec-o0x1`, `livespec-p9s0` as the sweep's
   findings rank them.

## Decisions taken (all three open questions RESOLVED 2026-07-19)

1. **Cross-tenant epic links — LINK THEM, in whichever direction is true.**
   An earlier draft of this handoff withheld these links, citing a
   No-Circular-Dependency concern. **That was a misapplication of the
   directive** and the maintainer corrected it: `.ai/no-circular-dependency.md`
   governs CODE and hard dependencies — checks, tools, reads, clones, pinned
   artifacts — NOT work-items. The ledger is a planning tool; a work-item
   dependency states that one piece of work genuinely blocks or contains
   another, and it may point in EITHER direction across repos when that
   relationship is real. No CI clones anything because of a ledger edge, so no
   cycle exists. The directive now carries an explicit scope section saying so.
   Do not re-raise this.
2. **Store-wrapper defect — FILED against the orchestrator plugin.**
   `append_work_item` hardcodes `--type blocks` for every `depends_on` entry,
   but beads rejects a task blocking an epic ("tasks can only block other
   tasks, not epics"), so the wrapper creates the item and THEN fails the edge,
   leaving a partially-linked record. It is our wrapper's defect, not a beads
   gap — beads' restriction is a legitimate upstream constraint the wrapper
   fails to accommodate — so it is filed in the
   `livespec-orchestrator-beads-fabro` tenant, which owns the wrapper, rather
   than catalogued in `.ai/beads-gaps-workarounds.md`. Workaround until fixed:
   file without `depends_on`, then add the edge with a direct
   `bd dep add <child> <epic> --type parent-child`.
3. **`livespec-o0x1` stays NARROW** — its acceptance criteria remain specific
   to the `canonical-slugs.yml` instance until `livespec-xw65el`'s sweep
   reveals how many (a)-class instances actually exist. Deliberately not
   generalized ahead of the data; revisit once the sweep lands.

## ⚠ A propagation BLIND SPOT this thread never named — `livespec-dev-tooling-2kt`

Surfaced 2026-07-20 by a fleet-wide `needs-attention` sweep (93 items across all
11 repos, zero unreachable). Not owned by this thread, but it sits directly on
this thread's causal chain and no other section here mentions it.

**The chain this thread depends on**, as stated in `.claude/CLAUDE.md`:
dogfooding pins track the latest RELEASE → release-please cuts a release on
every `feat:`/`fix:` push → the fan-out's `bump-pin` rewrites every consumer pin
to each new release tag. **Every link is downstream of a release actually being
CUT.**

`reusable-release-park.yml` is the backstop for a stalled release train, and it
ships only ONE of the TWO detection legs its design record specifies:

- **leg (a), IMPLEMENTED** — a `release-please--*` PR that is open and PARKED
  beyond `park_threshold_hours`.
- **leg (b), NOT IMPLEMENTED** (`livespec-dev-tooling-2kt`, `backlog`) — the
  default branch carries `feat`/`fix` commits newer than the latest release tag
  beyond the threshold, i.e. **release-please never opened a release PR at all.**

If a release PR is never opened, no tag appears, so the fan-out never fires, so
NO consumer pin moves — and nothing alarms, because leg (a) can only see a PR
that exists. **A train that never departs is invisible to leg (a) by
construction.** That is strictly worse than the parked case: parked is visible
in the PR list; never-opened is visible nowhere.

So leg (b) is the only detector for a SILENT fleet-wide propagation stall — the
exact failure this thread exists to prevent. Worth weighing when `2kt` is
prioritised: its value is not spec parity, it is the absence of any alarm on the
failure mode that stops propagation entirely.

**Its paired spec change is still ratifiable — verified, not assumed.**
`livespec-dev-tooling`'s `SPECIFICATION/proposed_changes/reusable-release-park-parity.md`
has been pending since 2026-07-04 (~16 days), long enough for replace-target
drift to make it unratifiable. It has NOT drifted: all THREE declared
`FIND (verbatim)` blocks were checked against
`origin/master:SPECIFICATION/contracts.md` and each resolves EXACTLY ONCE.
Ratifying it does NOT close `2kt` — by design the contract describes the
two-leg DESIGN while the missing leg stays tracked, so it is not silently
contracted away.

## What could invalidate the plan

The superseded-PR count is a snapshot and drifts upward as the fan-out keeps
opening PRs. CI logs older than roughly a day have aged out on the self-hosted
runners, so historical red PRs can no longer be diagnosed from their logs —
re-run a check to observe a live failure rather than trusting a reconstructed
cause.

**Superseded 2026-07-19 — this paragraph used to end with a claim that is now
false.** It read: "the (a)/(b) sweep is genuinely not done: an earlier
dispatched attempt returned no usable output, so treat its absence as absence."
The sweep WAS done. Its inventories were lost to a harness fault and have been
RECOVERED into `research/diagnosis.md` (see its ⚠ MAJOR REVISION section):
12 reddenable gates, 8 (a)-derivable / 4 (b)-needs-live-system, adopters zero.
**Do NOT re-run the sweep from scratch** — this file says so above, and the
stale sentence here contradicted it. What remains is verification of the
recovered table, not discovery.
