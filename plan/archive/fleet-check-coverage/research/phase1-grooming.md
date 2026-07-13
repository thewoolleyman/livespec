# Phase-1 grooming — the corrected burndown model (2026-07-09)

This note grooms the seven per-repo Phase-1 tracks into ready slices. It
supersedes the ordering sketched in the handoff's "next action" ("partition-
config restate first, then per-check fixes, then big-module splits") after a
load-bearing correction: **claiming a file for `partition_completeness` and
flipping the Phase-2 severity are the SAME config action, so partition config
comes LAST, not first.** Read this before dispatching any burndown work.

Authoritative inputs:
- `research/phase1-inventory.md` — the measurement method + caveat (never a
  repo's own stale venv).
- The v0.35.2 re-measurement (below) — supersedes the v0.35.1 table in
  `phase1-inventory.md` after the main_guard fix (dev-tooling v0.35.2).

## 1. The v0.35.2 WARN inventory (authoritative)

Grand total **474** `newly_covered` WARN (down from 563 at v0.35.1 — the entire
−89 is the main_guard reclassification). Measured with the dev-tooling v0.35.2
venv python, cwd = each target repo (the trustworthy method).

| repo | file_lloc | partition | all_decl | main_guard | kw_only | no_write | no_lloc_soft | global | no_inh | priv | **TOTAL** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| livespec (core) | 0 | 120 | 17 | 0 | 8 | 10 | 10 | 1 | 0 | 0 | **166** |
| orchestrator-beads-fabro | 16 | 6 | 26 | 2 | 29 | 69 | 3 | 0 | 4 | 1 | **156** |
| runtime | 1 | 27 | 2 | 0 | 19 | 0 | 0 | 0 | 3 | 0 | **53** |
| dev-tooling | 17 | 1 | 1 | 0 | 6 | 8 | 7 | 0 | 0 | 0 | **40** |
| orchestrator-git-jsonl | 3 | 12 | 11 | 2 | 7 | 2 | 0 | 0 | 0 | 0 | **37** |
| driver-codex | 1 | 0 | 2 | 0 | 8 | 2 | 0 | 0 | 0 | 0 | **13** |
| driver-claude | 0 | 0 | 2 | 0 | 6 | 1 | 0 | 0 | 0 | 0 | **9** |
| console-beads-fabro | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** |

Fleetwide zero: assert_never_exhaustiveness, comment_line_anchors,
match_keyword_only, rop_pipeline_shape. Orchestrator + git-jsonl retain 2
main_guard rows each — those are REAL `.claude-plugin/scripts/**` plugin-tree
hits main_guard correctly still catches (not the library false-positives the
v0.35.2 fix removed); they are genuine burndown, not check bugs.

file_lloc per-file split-vs-exempt candidates (all repos with any):
- **orchestrator (16):** dispatcher.py 1586, _dispatcher_plan.py 730,
  _dispatcher_reflector_oob.py 719, _beads_client.py 462, _dispatcher_engine.py
  445, drive.py 424, _dispatcher_reflection.py 402, store.py 389,
  needs_attention.py 385, _otel_receive.py 368, _otel_enrich.py 302,
  _dispatcher_cost_sink.py 259, _dispatcher_io.py 253, _dispatcher_cost.py 247,
  _dispatcher_janitor_checks.py 203, _dispatcher_cost_report.py 202. (14 of 16
  exceed the 250 hard ceiling.)
- **dev-tooling (17):** fleet/contract.py 399 … tdd_commit.py 205 (10 of 17
  exceed 250) — HOST-SIDE.
- **git-jsonl (3):** needs_attention.py 381, merge_evidence_backfill.py 298,
  store.py 296.
- **runtime (1):** hygiene_scan.py 471. **driver-codex (1):** footgun_guard 263.

orchestrator no_write_direct (69 hits / 20 files): dispatcher.py 19,
_orchestrator_spec_reader.py 6, detect_impl_gaps.py 5, next.py 5, + 16 more
files 1-3 each (full list in the measurement journal).

## 2. THE CORRECTION — role declaration == Phase-2 flip (partition comes last)

Every `[tool.livespec_dev_tooling]` role key is consumed by the applies-to-all
checks as a **severity classifier**, not merely as a `partition_completeness`
claim. Verified in dev-tooling v0.35.2:

| role key | which checks key on it as the legacy/hard classifier |
|---|---|
| `source_trees` | the 7: keyword_only_args, all_declared, no_inheritance, private_calls, global_writes, assert_never_exhaustiveness, match_keyword_only |
| `covered_trees` | no_write_direct, no_lloc_soft_warnings |
| `source_tree_prefixes` | check_coverage_incremental (imposes the incremental-coverage gate) |
| (hardcoded `.claude-plugin/scripts/livespec/`) | file_lloc `_LEGACY_HARDFAIL_TREES`; main_guard scope |

`partition_completeness` claims a file via ANY role (specific: io_trees,
commands_trees, pure_trees, dataclasses_tree, supervisor_entry_files; broad
fallback: source_trees, covered_trees, target_dirs, mirror_pairings,
source_tree_prefixes). But there is **no side-effect-free "claim-only" role** —
every role a file could be claimed under is ALSO a severity classifier or gate
input for some check.

Consequence: **declaring core's real role layout to clear its 120 partition
WARN would, in the same commit, flip the 7 checks + no_write + no_lloc to
hard-fail on those files — breaking CI if their violations aren't fixed first.**
Claiming-for-partition IS the Phase-2 severity flip. They cannot be separated.

### The corrected per-repo model

1. **Phase 1 = drive the NON-partition `newly_covered` WARN to zero** — the real
   code fixes: keyword_only (`*,` separators), all_declared (`__all__`),
   no_write_direct (route through the `io/` exemption surface), no_lloc_soft +
   file_lloc (split or named-exempt over-ceiling files), no_inheritance /
   private_calls / global_writes where present. Files stay unclaimed/newly_covered
   throughout, so every diagnostic is WARN (exit 0) — no CI risk mid-burndown.
2. **Phase 2 = declare the role layout** (`source_trees` + `covered_trees` +
   the specific io/commands/pure trees) covering the repo's universe. This ONE
   reviewed config commit simultaneously (a) claims every file →
   `partition_completeness` goes green, and (b) flips the keyed checks to
   hard-fail. Because Phase 1 already made them clean, CI stays green through the
   flip. This resolves the bulk of **OQ3**: the per-repo flip lever is a
   committed pyproject role declaration, NOT an env var — clean, visible, no
   escape hatch (`.ai/ci-gate-discipline.md`).

The 165 fleetwide partition WARN (core 120, runtime 27, git-jsonl 12,
orchestrator 6) are therefore a DERIVED indicator, not a fixable bucket: they go
to zero automatically at each repo's flip. Do NOT groom a standalone
"partition-config" slice ahead of the code fixes.

### One residual flip-mechanism gap (file_lloc, non-core repos)

file_lloc's legacy classifier is the HARDCODED `_LEGACY_HARDFAIL_TREES =
.claude-plugin/scripts/livespec/` — NOT config-driven. So a repo whose package
dir is `.claude-plugin/scripts/livespec_orchestrator_beads_fabro/` (orchestrator,
16 over-ceiling files incl dispatcher.py 1586) CANNOT flip file_lloc to hard via
its pyproject; declaring `source_trees` flips the 7 but leaves file_lloc WARN.
To flip file_lloc for non-core repos, dev-tooling must make its legacy tree
config-driven (or derive it from `source_trees`). This is a **dev-tooling
mechanism follow-up** (host-side), tracked under `livespec-iily`. Core is
unaffected (its file_lloc newly_covered = 0; its over-ceiling files are already
under the hardcoded legacy tree).

## 3. footgun_guard — per-copy fix, NOT propagate (corrects the handoff)

`livespec_footgun_guard.py` is copied into 7 repos (console has none) but there
is **no sync mechanism** — no copier template, no `just` recipe, no manifest
entry — and the copies are hand-forked into 4 behaviorally-divergent groups
(core carries a memory-write rule; driver-codex a primary-checkout-edit variant;
group A = older "family" body ×4; driver-claude = a precedence variant). The
handoff's "fix core's copy once and propagate to 6" would CLOBBER driver-codex's
intentional variant. Correct disposition: **fix each copy in place, per repo**
(the keyword_only fix is signature-local — insert `*, ` + keyword call sites,
behavior-neutral — safe to apply independently to each variant). This is folded
into each repo's keyword_only slice, NOT a cross-repo propagation. Violating
defs (core copy): `_strip_heredoc_bodies`, `_segments`, `_strip_leading_noise`,
`_git_subcommand`, `_memory_write_reason`, `_check_segment`, `_deny`. Future
single-sourcing (a copier template / `just sync-hooks`) is a SEPARATE design
decision that must first reconcile the deliberate core-vs-codex behavioral split
— out of scope for the burndown.

## 4. The driver + console check-wiring prerequisite

`livespec-driver-claude`, `livespec-driver-codex`, and
`livespec-console-beads-fabro` wire ZERO git-derived structural checks into
their justfile `check` target or CI matrix (verified: 0 structural recipes, 0
`check-aggregate-completeness`). Their CI runs only plugin-structure / lint /
format / hooks / e2e / heading-coverage / doctor-static. So although the Phase-0
universe fix pulls the drivers' hook `.py` (2 in claude, 3 in codex) INTO the
check universe, the checks never RUN there — coverage is theoretical and the
Phase-2 flip has nothing to flip.

Making driver/console coverage real requires WIRING the applies-to-all checks
into their justfile + CI matrix. The bump-pin composite action will not do this
automatically (PR #296 deliberately does not edit CI matrices, and only adds
slugs where the consumer already uses `check-aggregate-completeness` — the
drivers do not). This is a genuine choice the maintainer should confirm: subject
the thin binding repos' 2-3 hook files to the full livespec Python discipline
suite (they are even ruff-excluded today), or scope a subset. The handoff's
Phase-2 note already signals the intent to wire them ("once the wiring/fan-out
lands"). **Recommendation:** wire the full applies-to-all suite into the drivers
+ console (uniform coverage is the thread's entire point), as a per-repo
prerequisite slice BEFORE their flip. Fix the 9/13 driver WARN in the same slice
(they are tiny). Console (0 files) needs only the wiring so its flip is a
verified no-op.

## 5. The groomed slice structure

Factory-safety routing (from `phase1-inventory.md` §4, unchanged):
- **HOST-SIDE maintainer-driven (NOT factory):** dev-tooling (`livespec-iily`,
  the shared enforcement package) + the file_lloc flip-mechanism follow-up + each
  repo's Phase-2 role-declaration flip (config the fleet mirrors).
- **FACTORY-SAFE (dispatch under the janitor gate):** every repo's Phase-1
  CODE-fix burndown — orchestrator (`livespec-236f`), runtime (`livespec-8x7d`),
  git-jsonl (`livespec-t4e0`), drivers (`livespec-gqte`/`livespec-v74p`), AND
  core's code fixes (`livespec-9bym`; only core's role-declaration flip is
  host-side).

Per-repo slices (the existing 7 tracks are the Phase-1 code-fix burndown for
their repo; big repos sub-slice by check-family so each is one sandbox-sized PR):

| repo (track) | Phase-1 code-fix slices (factory-safe unless noted) | Phase-2 flip (host-side) |
|---|---|---|
| core `livespec-9bym` | S1 all_declared (17) + global_writes (1); S2 keyword_only (8, incl footgun copy); S3 no_write (10) + no_lloc_soft (10, split/exempt) | declare role layout (the fleet-mirrored config) |
| orchestrator `livespec-236f` | S1 no_write (69); S2 keyword_only (29) + all_declared (26) + no_inh (4) + priv (1) + main_guard (2); S3 file_lloc splits (16, dispatcher.py 1586 the tentpole) | declare source_trees (flips the 7); file_lloc flip needs dev-tooling follow-up |
| runtime `livespec-8x7d` | ONE slice: keyword_only (19) + no_inh (3) + all_declared (2) + file_lloc (hygiene_scan 471 split/exempt) + assert_never (1) | declare role layout |
| git-jsonl `livespec-t4e0` | ONE slice: all_declared (11) + keyword_only (7) + main_guard (2) + no_write (2) + file_lloc (3) | declare role layout |
| driver-codex `livespec-gqte` | PREREQ wire checks into justfile+CI, THEN keyword_only (8, footgun) + all_declared (2) + no_write (2) + file_lloc (footgun 263) | declare role layout |
| driver-claude `livespec-v74p` | PREREQ wire checks, THEN keyword_only (6, footgun) + all_declared (2) + no_write (1) | declare role layout |
| dev-tooling `livespec-iily` (HOST-SIDE) | file_lloc (17) + no_write (8) + no_lloc_soft (7) + keyword_only (6) + partition (1) + all_declared (1) | already declares source_trees; extend to full universe |
| console `livespec-q7bx` | wire full suite only (0 files) | flip = verified no-op |

Ordering within a factory-safe repo: do the mechanical per-check slices in any
order (they are independent — different files/edits), THEN the file_lloc splits
(judgment-heavy), THEN hand the repo to the host-side flip once WARN-clean.

**Two gates, kept separate — the slice's acceptance vs. the overseer's
ratification (convention correction, 2026-07-10).** A slice's `Acceptance:` line
is read verbatim by the Fabro implement agent (`render_goal` → `{{ goal }}`),
so it MUST contain ONLY conditions that agent can verify ITSELF in-sandbox: the
target checks measured to 0 `newly_covered` WARN (dev-tooling-pinned venv) + a
green `just check`. Do NOT author the external adversarial review INTO the slice
acceptance — the groom prose already requires an acceptance to be
"autonomously-verifiable", and a downstream reviewer is not. When a leaked
"+ independent adversarial NO-BLOCKERS review before acceptance" clause rode in
the slice acceptance, the implement agent tried to run that review itself,
timed out, and stalled at the unattended human gate (core-A `livespec-2j46re`,
v0.37.1 validation). The independent adversarial NO-BLOCKERS review of the
merged commit is the OVERSEER's separate pre-`accept:` ratification gate, done
OUTSIDE the factory (and, in-factory, the graph's own `review` node) — it is NOT
a slice acceptance criterion. (Auto-merge repos: land → overseer review → fix-
forward.) The `implement.md` prompt now also carries an ACCEPTANCE-CRITERIA
SCOPE guard as defense-in-depth. Do NOT `depends_on`-link any child to the OPEN
epic (perpetual block via `lifecycle._entry_blocks`) — narrate epic membership
in the description.

## 6. Open decisions surfaced to the maintainer

1. **Driver/console wiring (§4). — RESOLVED 2026-07-10: WIRE THE FULL SUITE.**
   Maintainer chose the full applies-to-all suite (via `check-aggregate-completeness`,
   the app-repo mechanism) into all 3 unwired repos' justfile + CI. Slice0 (wire
   full suite) is the prerequisite before each thin repo's WARN fix + flip.
   Recorded on `livespec-gqte`, `livespec-v74p`, and the new console track
   `livespec-q7bx` (console = wire + verify empty-universe no-op flip).
2. **file_lloc flip mechanism for non-core repos (§2 residual).** Make
   dev-tooling's file_lloc legacy tree config-driven so the orchestrator's 16
   over-ceiling files (dispatcher.py 1586) can flip. Host-side dev-tooling work;
   sequence it before the orchestrator flip.
3. **dispatcher.py 1586 (6.3× the 250 ceiling).** Split into modules vs
   named-justified file_lloc exemption? Design-laden; the orchestrator S3 slice
   owner decides per-file under review. Not a blocker for S1/S2.
</content>
</invoke>
