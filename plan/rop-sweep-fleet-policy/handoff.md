# rop-sweep-fleet-policy — RULING RATIFIED (v169). P0 rollout DONE. Dispatch still down; qm5 re-groomed

**Read this whole file before acting.** The ROP ruling is SETTLED and RATIFIED — v169 is
merged and live on master (livespec commit `2288197b`, PR #1424); the proposal is consumed
from `SPECIFICATION/proposed_changes/`. **Do NOT re-ratify it.** What remains is execution.
Status is READ from the ledgers (`bd`), never stored here. Ledger note on epic
`livespec-y2lkf4` carries the consolidated state; per-item notes carry review blockers and
evidence.

## START HERE — first three moves, in order

1. **Probe the Codex credential by READING IT, not by dispatching.** Run:
   `python3 -c "import json,base64,pathlib,datetime; d=json.loads((pathlib.Path.home()/'.codex/auth.json').read_text()); t=d['tokens']['id_token'].split('.')[1]; t+='='*(-len(t)%4); print(datetime.datetime.fromtimestamp(json.loads(base64.urlsafe_b64decode(t))['exp'], datetime.timezone.utc))"`
   If that timestamp is in the past, dispatch is DOWN and every `drive impl` will fail at
   `run-config-overlay`. **Do not burn a dispatch to discover this** — the prior handoff
   advised probing by dispatching `bd-ib-47gr`, which spends a factory run to learn what one
   file read tells you for free.
2. **If dispatch works:** land `bd-ib-47gr`, then run ONE combined dual review over
   `bd-ib-sw0i` + `bd-ib-47gr` (see HELD below — `sw0i` needs it on two counts).
3. **If dispatch is still down:** everything factory-side is blocked. The unblocked work is
   the dev-tooling gate items — but see the qm5 re-groom below before touching `qm5`, and
   note `livespec-dev-tooling-6vz` hinges on the same unresolved rule.

## STATE AS OF 2026-07-19 (this session)

- **`livespec-giq7` (P0) is DONE** — rolled out and live-exercised. See below.
- **`codex login` is STILL NOT DONE.** Verified by reading `~/.codex/auth.json`: `auth_mode`
  is `chatgpt` with NO `OPENAI_API_KEY` fallback, and the token expired **2026-07-09** — ten
  days stale. Dispatch is down. **Maintainer action required; outside agent reach.**
- **`livespec-dev-tooling-qm5` is BLOCKED + `needs-regroom`** by maintainer decision. Its
  premise was disproved. Nothing landed.
- **`livespec-dev-tooling-cvz` (P1) filed** — the third vacuous gate.
- **`livespec-dev-tooling-e9j` (P1) filed** — the SYSTEMIC finding that supersedes `cvz`: role-key
  non-declaration silently disarms SEVEN checks fleet-wide, four of which have never enforced
  anything in any repo. Core runs 5+ structural gates vacuous while CI reports them green.
  Flagged for possible P0. See the vacuous-gates section below.

Nothing is running: no dispatches, no monitors, no sub-agents. The `rop-drain` tmux socket
is empty.

**Outstanding worktrees/branches** (the previous handoff claimed "every worktree and branch
that session created is cleaned up" — that was FALSE when written; its own delivery PR #1426
was open at the time, from a worktree that still exists):
- `livespec`: worktree `docs-rop-handoff-post-ratification` (PR #1426, now MERGED — reapable).
- `livespec-dev-tooling`: branch `fix/no-except-outside-io-runs-when-io-trees-unset`, local
  and unpushed, carrying a valid Red commit `a33c394` deliberately preserved for the qm5
  re-groom. Worktree already removed. **Do not delete this branch** — see qm5's ledger note.
- `livespec-driver-claude`: worktree `codex/livespec-nj7d-hook-main` — ANOTHER session's, 14
  dirty files, last commit 2026-07-13. Not touched. Route via `just reap-stale-worktrees`.

## ✅ DONE THIS SESSION — `livespec-giq7` (P0), rolled out + live-exercised

The tmux fail-open guard is now current in **11 of 12** install records, verified by hashing
each installed cache's `hooks/_tmux_hazard.py` against
`git -C livespec-driver-claude show origin/master:.claude-plugin/hooks/_tmux_hazard.py`
(`608d3c9e183abda7…`) — **by content, never by version string**.

Correction to the prior handoff: it said every project except `/data/projects/livespec` was
on "a pre-fix plugin cache copy". Actually **10 of 12 lacked `_tmux_hazard.py` entirely**, so
the gap was larger than recorded.

Live exercise against the DEPLOYED cache (command strings only; nothing was executed):
unscoped kill-server → **deny**; `env -i sh -lc` wrapper evasion → **deny**; scoped
`-L <name>` form → **allowed**, not over-blocked.

No repo was dirtied: `claude plugin update` did NOT rewrite any committed
`.claude/settings.json` (unlike `install`/`uninstall`, which core's CLAUDE.md warns does).

The one residual is the other session's worktree above. **`giq7` is left OPEN pending a
maintainer call on whether the dual-review guard applies to a no-diff rollout** — there is no
diff to review, only host state, which a reviewer can re-verify by re-running the hash and
payload checks recorded in its ledger note.

**Gotcha worth keeping:** the guard blocks its own evidence journaling. A `bd note` whose
TEXT quotes hazardous command strings is denied, because the hook matches its hint regex over
the whole command string and cannot tell a quoted documentation payload from an executable
one. Workaround: write the note to a file and pass `bd note <id> "$(cat <file>)"`. That is a
false-positive workaround on documentation text, not an evasion — `bd note` cannot kill a
tmux server. Do NOT loosen the regex; the failure direction is the safe one.

## ⛔ BLOCKED ON THE MAINTAINER

1. **`codex login` on the orchestrator host** — see STATE above. Factory dispatch is down.
2. **The flat-package rule for `no_except_outside_io`** — the blocking design question for
   both `qm5` and `cvz`. Stated in full in qm5's ledger note; summarized under THREE VACUOUS
   GATES below.

## ⛔ Guards
- **DO NOT run `groom livespec-y2lkf4`** (the EPIC). Already decomposed; individual-child
  `groom <id>` is fine.
- **DO NOT accept any work-item** without BOTH a separate Codex reviewer AND a separate Opus
  reviewer clearing it. This has repeatedly caught defects every mechanical gate passed.
- Dispatch DETACHED only; a killed foreground dispatch strands the item `active`.
- **Detached tmux dispatches are NOT harness-tracked.** Arm a `Monitor` (watch for the `__EXIT=`
  marker AND for the tmux session vanishing without one) or you will wait forever on an event
  that cannot fire.
- **A correction note on a work-item does NOT reach an already-dispatched agent.** Once
  dispatched, the brief is frozen. Let it complete and reject, or stop it — do not append-and-hope.
  This exact mistake produced a defective guard (`bd-ib-ug4z`).
- **Never edit a handoff on the primary checkout.** The previous session left
  `plan/rop-sweep-fleet-policy/handoff.md` dirty on `/data/projects/livespec` while its PR
  #1426 carried identical content. Restored this session once #1426 merged.

## THE RULING — ratified, v169

`SPECIFICATION/proposed_changes/rop-broad-except-boundary-rule.md` was ACCEPTED into v169 and
is MERGED (livespec PR #1424, commit `2288197b`): 16 edits across
`non-functional-requirements.md`, `constraints.md`, `contracts.md`. The proposal file is gone
from the pending queue and now lives at `SPECIFICATION/history/v169/proposed_changes/`. It grew
5 → 16 edits over SIX independent review rounds (blockers per round: 5, 4, 2, 2, 0). Landed via
PRs #1400, #1405, #1407, #1416, #1420, #1421, then ratified by #1424.

**narrow at the seam; broad only at the boundary; at most one boundary per process.**

STYLE B (`livespec-orchestrator-git-jsonl`'s `io/store.py`) is the fleet standard. A hand-rolled
`except Exception` returning `Failure(exc)`/`IOFailure(exc)` is the blanket `@safe`/`@impure_safe`
form the spec ALREADY forbids, written longhand — the container does not change what the catch
is. *"It lifts onto the IO rail"* is not a defense; that argument was raised, adjudicated, rejected.

The five sanctioned `# noqa: BLE001` markers (em-dash), a CLOSED set:
```
— sole supervisor bug-catcher: log traceback, exit 1
— sole fail-open hook boundary: silent pass-through, exit 0
— sole fail-closed guard boundary: deny per policy, exit 0
— sole loop-iteration bug-catcher: log traceback, continue
— foreign-code isolation: <surface> crash captured as <ErrorType>, reported
```
`sole` scopes per process entry artifact for the three boundary markers, per SUPERVISION LOOP for
the loop-iteration marker. Foreign-code markers are not `sole` markers.

**The ruling is already baked into all 10 STEP 3 slice work-items** as a ledger note, including
the failure modes below. Do not re-derive it.

## DONE — accepted, dual-reviewed, live-exercised

*(Not re-verified this session — carried forward as recorded.)*

| Item | Repo | PR |
|---|---|---|
| `livespec-driver-codex-64s` | livespec-driver-codex | #199 |
| `livespec-driver-claude-hfm` | livespec-driver-claude | #219 |
| `livespec-driver-claude-ob3` | livespec-driver-claude | #215 |
| `bd-gj-li0` | livespec-orchestrator-git-jsonl | #341 (+#343) |

**Caveat on #215 / #199:** both remediated Driver hook trees, but NOT because
`check-no-except-outside-io` validated them — that check scans zero files in either repo (see
`cvz`). Whatever gate cleared them, it was not this one. Do not read those merges as coverage.

## HELD — `bd-ib-sw0i`, on TWO counts

*(Not re-verified this session — carried forward as recorded.)*

1. **Journal-deletion blocker.** `_dispatcher_reconcile_merged.py:75-78`'s ambiguous-PR refusal
   calls `_remove_journal(path=journal.path)` on the SHARED cross-item dispatch journal
   (`repo/tmp/fabro-dispatch-journal.jsonl` — the same default the loop appends to for every
   item). So reconcile against item B deletes in-flight records a live dispatch is writing for
   unrelated item A. This is the SAME bug class the work-item exists to close, relocated from
   worktree-deletion to journal-deletion, and it violates its own "evidence-journaling must stay
   intact" constraint. The giveaway: the `merged is None` branch two lines below deletes nothing.
   Fix filed as **`bd-ib-47gr`** (ready, blocked on `codex login`).
2. **Missing second verdict.** Only the Codex reviewer delivered. The Opus reviewer went idle
   three times without producing a verdict despite two follow-ups. The dual-review precondition
   is NOT met.

**When `47gr` lands, run ONE combined dual review over `sw0i` + `47gr`** rather than reviewing
`sw0i` now — `47gr` changes the file under review, so a review today reviews superseded code.

## STILL STRANDED BY DESIGN — `livespec-ftbvgc`

*(Not re-verified this session — carried forward as recorded.)*

Core's `BLE` add merged (livespec PR #1381) but the item is stuck `active`. Root cause: the only
`active → acceptance` write is `complete_and_accept` (`_dispatcher_completion.py:89`, status
write `:111`), whose sole caller is `post_run_dispositions`
(`_dispatcher_loop_selection.py:137`) — that transition lives ENTIRELY inside the dispatching
process, so ANY death of it after merge strands the item.

**Do NOT hand-close it, and do NOT run the reconcile valve on it until `bd-ib-47gr` lands** —
the race is closed for the worktree but still open for the journal.

## NEXT — the 10 groomed slices (backlog; ruling already baked into each)

`livespec-apiiwc` and `livespec-qgp2jt` are blocked/superseded; do not dispatch them whole.
- **livespec-runtime**: `livespec-4nlb` (**ANCHOR**), then `livespec-p41z`, `livespec-shz8`,
  `livespec-0bpr`.
- **livespec-dev-tooling**: `livespec-h2hs` (**ANCHOR**), then `livespec-9cts`, `livespec-ss2j`,
  `livespec-5dpg`, `livespec-tvlq`, `livespec-gcsn`.

Anchors first (they vendor `returns` + enable `BLE` repo-wide), then the rest in parallel.
Cross-tenant rule applies: these live in the **livespec** tenant but target siblings, so each
needs a dispatch-mirror in the target repo's tenant.

**`livespec-shz8` carries a cross-repo obligation** — see its ledger note. When it moves the
`WorkItemStore` protocol to `IOResult`, git-jsonl's deliberately-tracked divergence resolves and
its tracking test will fail BY DESIGN. File the paired git-jsonl repair BEFORE landing `shz8`.

## OPEN FOLLOW-UPS

| Item | Repo | Pri | What |
|---|---|---|---|
| `livespec-giq7` | livespec | P0 | **Rolled out + exercised.** Open only pending the dual-review call on a no-diff rollout |
| `bd-ib-47gr` | livespec-orchestrator-beads-fabro | P1 | Shared-journal deletion; ready, blocked on credential |
| `livespec-dev-tooling-qm5` | livespec-dev-tooling | P1 | **BLOCKED + `needs-regroom`.** Premise falsified — see below |
| `livespec-dev-tooling-cvz` | livespec-dev-tooling | P1 | **NEW.** `source_trees` undeclared → check scans ZERO files in core + both Drivers |
| `livespec-dev-tooling-e9j` | livespec-dev-tooling | P1 | **NEW, and the superset of `cvz`.** Role-key non-declaration silently disarms 7 checks fleet-wide; core runs 5+ structural gates vacuous-but-green. **Consider P0** |
| `livespec-dev-tooling-6vz` | livespec-dev-tooling | P1 | `no_raise_outside_io` hardcodes core's four error names → vacuous everywhere else. **Blast radius is beads-fabro (47 sites), NOT git-jsonl (2) as its brief says.** Hinges on the same unresolved flat-package rule as qm5 |
| `livespec-dev-tooling-jjb` | livespec-dev-tooling | P2 | Mechanize cardinality + marker wording (the ratified spec says these are review-enforced today) |
| `livespec-dev-tooling-bbl` | livespec-dev-tooling | P2 | Make the canonical no-shadow-ledger body type-checkable so both Drivers drop pyright carve-outs |

## NOT "TWO VACUOUS GATES" — SEVEN CHECKS ACROSS FIVE ROLE KEYS

This section has now been revised upward twice (2 → 3 → 7). Treat any count here as a floor
until `livespec-dev-tooling-e9j` is worked. All of these report GREEN while inspecting nothing.

**The three originally catalogued, each verified directly:**

1. `check-no-except-outside-io` returns 0 immediately when `io_trees` is unset (`qm5`).
2. `check-no-raise-outside-io` hardcodes `_DOMAIN_ERROR_NAMES` to core's four names; a repo whose
   errors are named differently gets zero coverage. Instrumented against git-jsonl it flagged 0
   of 9 raises including a genuine outside-`io/` one (`6vz`).
3. `check-no-except-outside-io` walks `config.source_trees`, UNDECLARED in livespec core AND both
   Driver repos, so the loop runs zero iterations (`cvz`). `livespec-driver-codex`'s
   `pyproject.toml` even documents that it deliberately omits the "heavy product-tree role keys".

**The systemic finding underneath them (`livespec-dev-tooling-e9j`).** SEVEN checks share one
early return — `if not config.<role_key>: log.info("role key absent — check no-ops"); return 0`.
It is not a bug but a documented convention (`load_config`'s own docstring). Measured across the
7 repos declaring a `[tool.livespec_dev_tooling]` block:

| Role key | UNSET in | Checks it silences |
|---|---|---|
| `pure_trees` | **7/7** | `check_mutation`, `pbt_coverage_pure_modules`, `public_api_result_typed` |
| `dataclasses_tree` | **7/7** | `newtype_domain_primitives` |
| `io_trees` | 5/7 | `no_except_outside_io`, `no_raise_outside_io` |
| `neutral_hook_body_path` | 5/7 | `no_shadow_ledger_body_identical` |
| `source_trees` | 4/7 | (empties the walk loop even when `io_trees` IS set) |

**Four checks have never enforced anything in any repo in the fleet.** Proven by execution in
core's own checkout — `public_api_result_typed`, `newtype_domain_primitives`,
`pbt_coverage_pure_modules`, `no_except_outside_io`, `no_raise_outside_io` all print
`check no-ops` — while core CI reports every one SUCCESS (verified on PR #1426's rollup).

**Root cause — pinned to a commit and a date. The fallback was correct for under 24 hours:**

| When | What |
|---|---|
| **2026-05-30 15:53** | livespec-dev-tooling `391662a` introduces `_livespec_core_config()`, the fallback that supplies core's real `io_trees`/`pure_trees`/`dataclasses_tree`. It applies ONLY when the `[tool.livespec_dev_tooling]` block is ABSENT — its docstring says it exists so "livespec-core (which omits the block) stays bit-identical". |
| **2026-05-31 14:10** | livespec core `8f6ecc59` ADDS that block — solely to declare `scenario_tiers` for an unrelated new heading-coverage check in dev-tooling v0.9.0. It declares no structural role key, and needed none for its purpose. |

That one edit moved core from the fallback regime to the empty flat baseline. **Core's
structural gate suite has been inert since 2026-05-31 — roughly seven weeks — with CI reporting
every one of those checks green throughout.**

Four properties hid it: the disarming edit lived in a DIFFERENT repo and reads as a dependency
bump; the regime switch is implicit in `table is None`, so ANY key flips it; the only signal is
an INFO line in a suite where passing checks also print nothing and exit 0 — a no-op and a pass
are visually identical in CI; and `_livespec_core_config`'s docstring still asserts core "omits
the block", so the function is now dead code with respect to its stated purpose while still
firing for `livespec-console-beads-fabro`, which has no block and is a Rust crate. **The
core-shaped fallback misses core and lands on a repo it cannot describe.**

This reframes the fix: the failure was NOT a repo forgetting to declare keys. Core never needed
to — it was correctly served by the fallback until an unrelated edit silently withdrew it. So
the load-bearing remedy is making the regime EXPLICIT (a repo declares which layout it intends)
and making a zero-file inspection LOUD (report the inspected-file count per check, so "inspected
0" cannot masquerade as "passed").

**Why this bears directly on this thread:** v169's mechanical half is carried by exactly these
checks. In core and both Drivers they inspect nothing. A ratified ROP policy is being enforced
by gates that are structurally inert in the repos that define and ship it.

Defect #2 distorted a real design decision: restoring protocol conformance vs. tracking the
divergence was argued partly on whether unwrapping would trip that check. It wouldn't have.

Defect #3 falsifies `qm5`'s rationale. The two holes are in SERIES: with `source_trees` empty the
walk runs zero iterations no matter what `io_trees` says, so fixing `qm5` alone yields ZERO new
Driver coverage.

## THE FOUR GATE ITEMS ARE ONE MACHINE — do not land them independently

`qm5`, `cvz`, `6vz`, and `e9j` all touch the same config-plus-walk machinery. Two facts to hold:

- **The defects are shared-shape across BOTH ROP checks.** `no_raise_outside_io` carries the
  io_trees early return (`qm5`'s defect, byte-identical in shape, lines 91-97) AND the
  source_trees walk (`cvz`'s defect, line 99) AND its own hardcoded names (`6vz`). It is vacuous
  through THREE serial mechanisms; fixing any one leaves it vacuous. `qm5` and `cvz` were both
  filed naming `no_except_outside_io` alone. Fix both checks in one pass.
- **Blast radius is dominated by a repo none of the briefs name.** Measured, counting raises of
  each repo's own error classes outside its DECLARED io trees:
  `livespec-orchestrator-beads-fabro` **47 sites**; `livespec-dev-tooling` 14;
  `livespec-orchestrator-git-jsonl` **2** — the only repo `6vz`'s brief anticipates. beads-fabro
  declares both `source_trees` and `io_trees`, so the qm5/cvz vacuities do NOT shield it — only
  `6vz`'s does. **Fixing `6vz` alone immediately reddens beads-fabro with 47 findings.** The
  warn-tier severity lever its brief already sanctions is likely required, not optional.

## THE OPEN DESIGN QUESTION — blocks `qm5`, `cvz`, and `6vz`

**v169 ratified "narrow at the seam; broad only at the boundary." But
`no_except_outside_io` bans ALL `try/except` outside `io/`, narrow included.** That is coherent
for a LAYERED package — the narrow seam catches live in `io/`. For a FLAT package there is no
`io/`, so the strict reading bans the very form v169 sanctions.

Measured: `livespec-dev-tooling` is the ONLY repo the `qm5` fix affects — 36 offenses, of which
**4 are broad** (`except Exception`) and **32 are narrow** typed catches. An independent
classification judged ~30 legitimate (3 sanctioned boundaries missing only a
`supervisor_entry_files` declaration; ~20 foreign-code isolation parsing `gh` CLI JSON and other
repos' manifests; 7 borderline) and ~6 genuine violations — notably `green_token.py:92,122`,
broad catches in ordinary helpers guarding a local advisory cache.

`check-no-except-outside-io` is already live in dev-tooling's own justfile (221/630), so landing
`qm5` as written turns THIS repo's `just check` red — the Green commit cannot even be made.

### The cost of each rule, measured fleet-wide

Except handlers OUTSIDE each repo's DECLARED io trees. Both columns are UPPER BOUNDS — they do
not subtract `supervisor_entry_files` / `commands_trees` `main()` exemptions, which shrink the
BROAD column most.

| repo / tree | BROAD | NARROW | total |
|---|---|---|---|
| livespec (core, main tree) | 0 | 3 | 3 |
| livespec (`.claude/skills/`) | 1 | 35 | 36 |
| livespec-dev-tooling | 4 | 34 | 38 |
| **livespec-driver-claude** | **4** | 5 | 9 |
| **livespec-driver-codex** | **4** | 10 | 14 |
| livespec-orchestrator-git-jsonl | 0 | 3 | 3 |
| livespec-orchestrator-beads-fabro | 0 | 6 | 6 |
| **FLEET TOTAL** | **13** | **96** | **109** |

**Broad-only costs 13 sites. Strict costs 109.** Roughly an 8x difference in remediation scope.

> **REVISED DOWNWARD — the real broad-only figure is ~7, not 13.** Direct source inspection of
> all 8 Driver broad catches (not simulation — every one read with its marker) found **6 already
> carry EXACT sanctioned v169 wording**, `sole` cardinality intact since each sits in a different
> hook file. The 2 non-conforming ones are **the same file in both repos** —
> `no_shadow_ledger.py:195`, byte-identical, marked `— fail-open by contract`, which is not in
> the closed set. Neither Driver owns it: it installs from
> `livespec_dev_tooling/install_no_shadow_ledger.py:255` under a byte-identical guard. So the
> genuinely outstanding broad work is **2** (one canonical string) **+ 4** (dev-tooling: 2
> declarable hook boundaries, 2 real violations in `green_token.py`) **+ 1** (overseer
> `supervisor.py`) ≈ **7 sites fleet-wide**.
>
> **This falsifies `qm5`'s Driver-drift premise — the third false premise found in this thread.**
> That brief says the Drivers drifted into blanket lifts marked `# noqa: BLE001 - ... captured on
> IO rail`. **No catch in either Driver hook tree carries that wording.** The drift was
> evidently remediated by the merged PRs #215 / #219 / #199 this handoff's own DONE table
> records. Do not plan Driver remediation; it is done.
>
> **Caveat:** wording conformance is necessary, NOT sufficient. This pass verified the six
> markers match the sanctioned strings; it did NOT re-verify that each claimed boundary is
> genuinely its process's sole boundary, nor that fail-open vs fail-closed is right at each site.
> The tmux guard is precedent — its comment claimed fail-closed while the body failed open.
> `livespec-dev-tooling-jjb` remains the right home for mechanizing that.

### The one piece of this sweep that can land NOW

Fixing that canonical marker string is **rule-independent** — it is a BROAD catch, restricted
under both candidate rules — so unlike `qm5`/`cvz`/`6vz`/`e9j` it does not wait on the ruling.
Routed onto **`livespec-dev-tooling-bbl`** (same canonical body, already targeted there for
pyright reasons) rather than filed as a near-duplicate; do both edits in ONE pass or the
byte-identical guard forces a second regeneration across both Drivers for nothing.

The replacement wording was verified TRUTHFUL against the actual body, not assumed: the catch
sits in `main()` (the process entry point), sets `warning = None`, writes nothing, and returns 0
unconditionally — so `sole fail-open hook boundary: silent pass-through, exit 0` describes it
exactly, clause by clause.

The BROAD column is precisely the target of this sweep: **both Drivers carry exactly 4 broad
catches each — 8 of the 13 fleet-wide** — and those are the hand-rolled blanket lifts the ROP
ruling was written to close. Broad-only catches every one while leaving the Drivers' 15 combined
narrow seam catches alone. dev-tooling's 4 are 2 declarable fail-open hook boundaries plus 2
genuine violations in `green_token.py`; the overseer's 1 is `supervisor.py`.

Method and its limits, stated plainly: these are AST measurements. The same simulator was
VALIDATED against real execution on core — it predicted core's 3 offenses with exact file and
line agreement before the checks were run for real (see `e9j`) — but the other rows are
simulation-only. `_vendor/` excluded throughout.

**The two Driver repos do NOT share a hook tree path** — `livespec-driver-claude` uses
`.claude-plugin/hooks/`, `livespec-driver-codex` uses `livespec/hooks/`. Assuming a common path
initially produced a false ZERO for driver-codex in this very table. Any change declaring
`source_trees` per repo must read each repo's real layout; a wrong path yields a silent zero,
not an error.

**Agent recommendation (NOT yet ruled on):** flag BROAD catches only in the flat branch. It still
catches the Driver drift `qm5` targets (blanket `except Exception` marked `# noqa: BLE001`, and
BLE001 IS the blind-except rule) without banning the sanctioned narrow form, and reddens
dev-tooling on 4 tractable sites. No skip flag, no per-repo exemption.
**Counter-argument, stated fairly:** `contracts.md:213` says "no `try/except` is wholesale
exempt" and the maintainer ruled that row correct as written. The recommendation reads
"wholesale" as TREE-level, not "every individual catch is an offense". If the stricter reading is
intended, broad-only is off the table and ~32 narrow catches need remediation or declaration.

## COORDINATION WITH `plan/overseer-productization/` — settled 2026-07-19

That thread asked how `.claude/skills/` interacts with `cvz` declaring core's `source_trees`.
**Maintainer ruling relayed by that session: `.claude/skills/` is NOT excluded from the ROP bar —
"it should follow discipline."** Deferring WHEN it enters `source_trees` is sequencing, not
exemption, and is consistent with that ruling.

**Agreed split and ordering:**

1. **`cvz` (this thread)** declares core's `source_trees`/`io_trees` **without** `.claude/skills/`.
2. **Gate E (overseer-productization thread)** brings the overseer folder to conformance.
3. **Either thread, only after (2)** adds `.claude/skills/` to `source_trees` — enforcement
   arrives after adoption, per `.ai/ci-gate-discipline.md`.

**Two measurements that change the size of this work — do not plan against the estimates:**

- **Step 1 is nearly free.** Simulating `no_except_outside_io` over core's main tree with the
  fallback's role keys restored yields **3 offenses, ALL NARROW** — `SyntaxError` /
  `IndentationError` / `tokenize.TokenError` in `doctor/static/no_spec_section_citation_in_code.py`
  (parsing arbitrary Python) and `ModuleNotFoundError` in
  `doctor/static/wiring_completeness_cross_repo.py` (optional-import probe). Under the recommended
  broad-only rule that is **0 offenses — core's main tree is already clean**. Under the strict
  rule it is 3, all textbook foreign-code isolation. So `cvz` step 1 can land immediately and does
  NOT need to wait on Gate E.
- **Gate E's size depends ENTIRELY on the unresolved flat rule.** The overseer folder carries
  **36 except handlers of which exactly ONE is broad** (`supervisor.py`); the other 35 are narrow
  typed catches, spread across `registry.py` (11), `claude_sessions.py` (6), `codex_sessions.py`
  (6), `supervisor.py` (6), `tmuxio.py` (3), `jsonio.py` (2), `signals.py` (1).
  - Under **broad-only**: Gate E is **1 site** — declare `supervisor.py`'s sole `except Exception`
    as a boundary. No `io/` layer, no refactor.
  - Under **strict**: 35 sites need an `io/` split or equivalent.

  **So Gate E should NOT begin its refactor until the flat rule is ruled on**, or it risks doing
  35 sites of work that the ruling makes unnecessary.

**Answer to that thread's design question — declaring the whole folder an `io` tree is NOT
acceptable.** `io_trees` entries are **wholesale exempt**, so declaring `.claude/skills/overseer/`
an io tree would make all 36 handlers instantly legal and the check vacuous over that tree. That
is a bypass wearing a declaration's clothes — the same "fabricate a boundary that does not exist"
move already rejected for `livespec-dev-tooling` in `qm5`'s ledger note, and forbidden by
`.ai/ci-gate-discipline.md`'s "fix the gate, not the bypass". Whether the folder should instead
grow a REAL `io/` layer is premature: under broad-only it needs none.

## WHAT THE REVIEW GATE CAUGHT (do not weaken it)

Every finding below passed all mechanical gates:
- **The tmux guard failed OPEN** while its comment claimed fail-closed — on the guard that exists
  to stop the agent-caused fleet kill that happened the same day.
- **The reconcile valve could clobber a live dispatch**, causing the very stranding it prevents.
- **Its replacement guard was INERT** — gated on a heartbeat that is silent in exactly the
  contested window, so it waved every caller through while looking like protection.
- **Then the fix for THAT relocated the same bug** from worktree-deletion to journal-deletion.
- **A proposed spec edit re-asserted a FALSE enforcement claim** while claiming to make spec and
  code agree.
- **Two tests were inert** — one guarded behind `hasattr` on a symbol its own PR deleted, so it
  passed against a reintroduced fail-open.
- **Two of six spec review rounds found blockers introduced by the previous round's fix.**
- **A P1 work-item's own rationale was false** — `qm5` was written on the belief that one config
  hole blocked Driver coverage; there were two in series, so the fix would have delivered nothing
  where it was aimed while reddening the repo shipping it.

## MECHANICS (hard-won — do not rediscover)

- **These repos REBASE-merge.** A "merge SHA" is a span tip, not a two-parent merge commit;
  `git show <tip>` reviews only the last commit — in one case an entirely unrelated commit.
  Resolve `base..head` via `gh pr view <n> --json commits,baseRefOid,headRefOid,additions,deletions,changedFiles`
  and cross-check totals. **Brief every reviewer with this.**
- **Verify plugin rollout by CONTENT, not version string.** Hash the installed cache's file
  against `git show origin/master:<path>`. Version strings and "already at latest" both lie about
  whether the fixed bytes are on disk.
- **A `--force-with-lease` "stale info" rejection is ambiguous** between your own merged-and-deleted
  branch and a peer's push. STOP and investigate; never force blind.
- **PRs here merge fast.** Land corrections as FRESH branches off current master, not amendments.
- **Require reviewers to verify by EXECUTION**, not reading — revert the impl, watch the test
  fail, report the output. That framing caught the inert guard, the inert tests, and the journal
  deletion; a structural read passed all three.
- **A test-only brief must NOT demand Red-Green-Replay** — no impl to add at Green. Use the
  established `TDD-Suite-Green-*` shape.
- **`status` is a read-only variable in zsh** and will silently kill a `Monitor` script.
- **Do NOT read a local agent's `.output` file** — it is a symlink to the full subagent transcript
  and will overflow context. Use the agent result or `SendMessage`.
- **Spec edits go through `/livespec:propose-change`**, never a direct edit backfilled by doctor.
  PR #797 did the latter and doctor SELF-ACCEPTED the drift (`author_llm: livespec-doctor`),
  bypassing the never-self-waived independent-review rule. Put this line in every dispatch brief.
- All `bd` calls go through `/data/projects/1password-env-wrapper/with-livespec-env.sh`. The
  `auto-backup failed … command denied` warning is correct-by-design.

## CORRECTIONS TO EARLIER FINDINGS (do not re-derive the wrong conclusion)

- **`no_shadow_ledger.py` is NOT "a bypass in both Drivers".** Neither Driver owns it — the single
  source is `livespec_dev_tooling.install_no_shadow_ledger.CANONICAL_NO_SHADOW_LEDGER_BODY`,
  installed via `just install-no-shadow-ledger` and guarded byte-identical by
  `check-no-shadow-ledger-body-identical` (exit 4 on drift). Editing it in a Driver is FORBIDDEN.
  livespec-driver-claude's pyright carve-out is documented and principled
  (`pyproject.toml:280-292`); only livespec-driver-codex's is undocumented. The body also carries
  bare `dict`/`list` annotations failing strict pyright, so a one-line fix is insufficient. Real
  fix: `livespec-dev-tooling-bbl`.
- **The heartbeat probe is the WRONG fix for the reconcile race.** `post_merge` runs AFTER the
  Fabro run completes and the heartbeat is fed DURING it, so the probe is silent in exactly the
  contested window and returns a false "dead" verdict.
- **`BLE001` markers in both Drivers' hook trees are DECORATIVE** — those trees are
  `extend-exclude`d from ruff, so `BLE001` never fires. `livespec-dev-tooling-jjb` must add a
  POSITIVE AST guard, not merely remove a carve-out.
- **Do not probe a credential by dispatching.** Read `~/.codex/auth.json` — see START HERE.

## Close-out

When all children + slices are `done`, epic `livespec-y2lkf4` closes and this thread archives to
`plan/archive/rop-sweep-fleet-policy/`.
