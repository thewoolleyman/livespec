# critique-fix v034 → v035 revision

## Origin

The v034 step-3 activation commit
(`chore!: activate v034 replay hook + remove v033 hook`,
sha `495e5ce`) wired the replay hook into lefthook's
`commit-msg` stage and removed the v033 honor-system gate.
The activation was deliberately slim per
`bootstrap/decisions.md` 2026-05-02T06:00:00Z (user-gated
choice) and the cycle-183 commit body (anti-cheat reflog
deferral). v035 reconciles PROPOSAL.md and the plan with
the slim-activation reality so a fresh drain-cycle agent
reading the spec is not misled by stale text.

The drift items reconciled here are **not** architectural
disagreements with v034 — the v034 codification's eight
decisions remain authoritative. v035 documents that two of
the v034 mechanisms (D6 baseline-grandfathered violations;
the §"Anti-cheat" reflog inspection inside D3) are deferred
indefinitely or to post-v1.0.0 hardening, codifies an
implementation choice the activation surfaced (multi-test-
file rejection enforces the singular trailer schema), and
fixes a wording slip (PROPOSAL line 3517 calls the hook
"pre-commit" but the design is `commit-msg`).

Pre-v035 commits remain unaffected; the v035 codification
commit is itself a `chore!:` (no D8 breaking-change
implication — chore covers the spec text edits).

The remedy is a v035 revision covering five decisions:

- **D1** Defer the v034 D6 baseline-grandfathered-
  violations mechanism. The thinned `just check` aggregate
  retained at activation; v034 D7 drain proceeds against
  it via the v033 D5b grow-as-passing pattern.
- **D2** Fix PROPOSAL line 3517 wording: "the pre-commit
  hook" → "the commit-msg hook". The replay hook lives at
  `commit-msg` stage in lefthook; the design (writes
  trailers via `git interpret-trailers --in-place`,
  inspects HEAD~0 to distinguish Red vs Green amend) is
  fundamentally commit-msg.
- **D3** Defer the v034 D3 §"Anti-cheat" reflog-inspection
  mechanism to post-v1.0.0 hardening. The local Red→Green
  amend pattern is already mechanically airtight for
  honest workflows; reflog-based bad-actor protection adds
  zero value for the v034 D7 drain (which operates
  locally with the developer following discipline).
- **D4** Codify multi-test-file rejection in PROPOSAL §"Red
  mode (initial commit)". The hook authored at cycle 179
  (sha `446b96b`) rejects multi-test-file staged trees with
  a structured `red-green-replay-multi-test-file`
  diagnostic since the v034 D2 `TDD-Red-Test-File-Checksum:`
  trailer is singular. v035 makes the per-file constraint
  explicit in PROPOSAL.
- **D5** Plan-text + housekeeping. Plan §"v034 transition"
  step 3 + §"Aggregate-restoration drain" updated to
  reflect D1's deferral; the standard housekeeping
  bumps Version basis preamble (v035 decision block),
  Phase 0 step-1 byte-identity reference, Phase 0 step-2
  frozen-status header, Execution-prompt block authorita-
  tive-version line.

The v034 D7 drain proceeds against the post-v035 PROPOSAL.

## Decisions captured in v035

### D1 — Defer v034 D6 baseline-grandfathered violations indefinitely

**Surface in PROPOSAL.md.** §"Baseline-grandfathered
violations (v034 D6)" lines 4096-4180 — the entire
sub-section.

**Decision.** The mechanism described — a TOML baseline
file at `<repo-root>/phase-5-deferred-violations.toml`
loaded by each check, with per-`(target, file, rule,
location)` skip semantics — is **deferred indefinitely**.
The v034 D7 drain proceeds against the existing thinned
`just check` aggregate retained at activation. Each drain
cycle that resolves a currently-unbound target rejoins it
to the aggregate in the same commit, matching the v033
D5b cycles 1-172 pattern. Once the four currently-unbound
canonical targets (`check-pbt-coverage-pure-modules`,
`check-newtype-domain-primitives`,
`check-schema-dataclass-pairing`, `check-complexity`) and
the two config-tier targets (`check-lint`, `check-format`)
are bound and passing, the aggregate matches the full
canonical-target list de facto.

**Rationale.** Per
`bootstrap/decisions.md` 2026-05-02T06:00:00Z, implementing
v034 D6 as written would require ~22 check-script
modifications (each script loads the TOML, builds its
violation set, filters its own output). The drain itself
only resolves ~6 violations across ~11-15 cycles. The
per-check baseline-loading machinery is over-engineered
for that scope; the simpler thinned-aggregate-grows
pattern has been proven through cycles 1-172 + the v034
hook authoring (cycles 173-183).

**PROPOSAL edit.** Replace §"Baseline-grandfathered
violations (v034 D6)" body with a brief note marking the
mechanism deferred + cross-referencing `bootstrap/
decisions.md` 2026-05-02T06:00:00Z + describing the actual
slim-activation path (thinned aggregate retained;
each drain cycle rejoins its target). Preserve the
sub-section header so internal cross-references remain
valid.

### D2 — Fix PROPOSAL "pre-commit" → "commit-msg" wording

**Surface in PROPOSAL.md.** §"v034 D2-D3 Red→Green replay
contract" line 3517: "The pre-commit hook
(`dev-tooling/checks/red_green_replay.py`, replacing the
v033 `red_output_in_commit.py`) operates in two modes,
distinguished by inspecting `HEAD~0`'s commit message".

**Decision.** Replace "pre-commit hook" with "commit-msg
hook" in PROPOSAL line 3517. The replay hook lives at
lefthook `commit-msg` stage:

- The hook writes trailers via `git interpret-trailers
  --in-place` on the commit-message file (passed as argv[1]);
  this requires the file to exist, which is true at
  commit-msg stage but not pre-commit.
- The hook distinguishes Red vs Green by inspecting `HEAD~0`'s
  commit message. At commit-msg stage during `git commit
  --amend`, HEAD still points at the pre-amend commit; the
  hook reads its trailers to detect Green-mode candidacy.
  At pre-commit stage, the same semantic is achievable but
  the trailer-writing step isn't.

**Rationale.** The two stages are not interchangeable. The
v034 D3 design requires commit-msg semantics. The
"pre-commit" wording in PROPOSAL line 3517 is loose —
likely shorthand for "git hook that gates commits before
they finalize" — and was authored before the implementation
existed.

**PROPOSAL edit.** Replace "The pre-commit hook" with "The
`commit-msg` hook" at line 3517.

### D3 — Defer v034 D3 anti-cheat reflog inspection

**Surface in PROPOSAL.md.** §"v034 D2-D3 Red→Green replay
contract" §"Anti-cheat" (the paragraph beginning "A bad
actor could attempt to skip the Red moment...").

**Decision.** Mark the reflog-inspection mechanism deferred
to post-v1.0.0 hardening. The implementation in
`dev-tooling/checks/red_green_replay.py` does NOT inspect
`.git/logs/HEAD` or verify `TDD-Green-Parent-Reflog`
SHA presence; it simply captures the SHA from `git
rev-parse HEAD` and writes it as a trailer.

**Rationale.** Per the cycle-183 commit body (sha
`ec2d3e6`): "the local Red→Green amend pattern is already
mechanically airtight for honest workflows". The reflog
inspection is bad-actor protection — it catches an attacker
who hand-fakes Red trailers without ever having been in a
Red moment. The v034 D7 drain operates locally with the
developer following discipline; bad-actor protection is
not load-bearing. Adding it would be ~30 lines of code +
paired test for a scenario that doesn't materially exist
during the drain. Post-v1.0.0 hardening can revisit if
warranted (e.g., for hosted-CI verification of remote
contributor commits).

**PROPOSAL edit.** Append to §"Anti-cheat" paragraph: "**v034
D3 implementation status (per v035 D3):** the reflog-
inspection mechanism described above is deferred to
post-v1.0.0 hardening. The
`dev-tooling/checks/red_green_replay.py` hook captures the
parent SHA via `git rev-parse HEAD` and writes the
`TDD-Green-Parent-Reflog` trailer, but does NOT verify the
SHA's presence in the reflog or inspect its trailers. The
local Red→Green amend pattern is mechanically airtight for
honest workflows; bad-actor protection via reflog
inspection is not load-bearing for the v034 D7 drain or
Phase 6+ self-application work."

### D4 — Codify multi-test-file rejection in §"Red mode"

**Surface in PROPOSAL.md.** §"v034 D2-D3 Red→Green replay
contract" §"Red mode (initial commit)" (lines 3522-3531) +
§"Trailer schema" (lines 3548-3554).

**Decision.** Make explicit the per-file constraint that is
implicit from the singular `TDD-Red-Test-File-Checksum:`
trailer. The hook (cycle 179, sha `446b96b`) rejects
multi-test-file staged trees with a structured
`red-green-replay-multi-test-file` diagnostic + skips
checksum computation.

**Rationale.** The implicit per-file constraint surfaced
during cycle 179 authoring as an enforcement question:
when multiple test files are staged with a `feat:`/`fix:`
subject, what does the hook do? Three options were
considered: compute one checksum per file (would require
multiple `TDD-Red-Test-File-Checksum:` trailers,
diverging from PROPOSAL's singular schema); pick a
canonical "first" file (arbitrary, fragile); reject
explicitly with a diagnostic (matches PROPOSAL's singular
schema; clearest user-facing failure mode). The third
option was implemented. v035 codifies it in PROPOSAL so
fresh agents understand the constraint.

**PROPOSAL edit.** Append a sentence to §"Red mode (initial
commit)" describing the per-file constraint: "**Per-file
constraint.** Red mode is per-file: exactly one test file
must be staged. If multiple test files are staged, the
hook rejects with a `red-green-replay-multi-test-file`
diagnostic and skips checksum computation. The constraint
follows from the singular `TDD-Red-Test-File-Checksum:`
trailer in §"Trailer schema"; staging multiple test files
in a single Red commit produces ambiguity the schema
cannot represent."

### D5 — Plan-text and housekeeping edits

**Surface in plan and PROPOSAL.**

1. PROPOSAL.md §"Versioning" decisions block:
   add a v035 entry summarising D1-D4.

2. PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md §"Version
   basis": preamble decision block bump (current text
   describes v034; append v035 D1-D5 summary line).

3. PLAN §"Phase 0 step 1": byte-identity check reference
   bumps from `history/v034/` to `history/v035/`.

4. PLAN §"Phase 0 step 2": frozen-status header bumps
   from "Frozen at v034" to "Frozen at v035".

5. PLAN §"Execution prompt": authoritative-version line
   bumps from "Treat PROPOSAL.md v034 as authoritative" to
   v035.

6. PLAN §"v034 transition — replay-hook activation +
   drain authorization (v034 D3 / D5 / D6)" step 3:
   - "lefthook.yml pre-commit ordering" → "lefthook.yml
     `commit-msg` stage" (paired D2 wording fix).
   - Remove the sentence "Authors the initial
     `phase-5-deferred-violations.toml` (D6) at the repo
     root enumerating every currently-failing canonical-
     target violation" + replace with "v034 D6 baseline-
     grandfathered mechanism deferred per v035 D1; see
     `bootstrap/decisions.md` 2026-05-02T06:00:00Z. The
     thinned `just check` aggregate is retained; each
     drain cycle rejoins its now-passing target."
   - Remove "Replaces the thinned `just check` aggregate
     at `justfile:75-99` with the full canonical-target
     list + a one-line reference to D6 + the baseline
     file." (paired D1 deferral).
   - Adjust the subject-line example: `chore!: activate
     v034 replay hook + remove v033 hook (slim
     activation; v034 D6 deferred)` (matches the actual
     activation commit `495e5ce`).

7. PLAN §"Aggregate-restoration drain (v034 D7)":
   - "Entry condition." Remove the sentence "AND
     `phase-5-deferred-violations.toml` exists at the repo
     root enumerating the initial set of grandfathered
     violations" (paired D1 deferral); replace with "The
     thinned `just check` aggregate is retained; each
     drain cycle rejoins its now-passing target to the
     aggregate."
   - "Exit condition." Replace the
     `phase-5-deferred-violations.toml`-empty wording
     with: "Every previously-unbound canonical target
     (`check-pbt-coverage-pure-modules`,
     `check-newtype-domain-primitives`,
     `check-schema-dataclass-pairing`,
     `check-complexity`, `check-lint`, `check-format`) is
     bound to the `just check` aggregate AND passes. From
     that commit forward, the local pre-commit hook runs
     the full canonical-target list de facto."
   - "Per-cycle workflow." Update step 3 to remove the
     `phase-5-deferred-violations.toml` baseline-diff
     verification language; replace with: "The Green
     amend rejoins the now-passing target to the
     `just check` aggregate's `targets=(...)` list in the
     same commit. The replay hook verifies the Red→Green
     pair under the v034 D2 trailer schema; the aggregate
     re-binding is plain `justfile` editing."

**Rationale.** Standard housekeeping pattern from v022 →
v034 codifications. Without these edits, fresh agents
would read stale plan text and STATUS during the drain.

## Activation sequencing summary

The v035 codification commit is itself a `chore!:` commit
that:

- Applies all D1-D4 PROPOSAL.md edits.
- Applies all D5 plan-text edits.
- Snapshots `history/v035/PROPOSAL.md` (post-edit) +
  `history/v035/proposed_changes/critique-fix-v034-revision.md`
  (this file).
- Marks the four originating
  `bootstrap/open-issues.md` entries (timestamps
  2026-05-02T07:00:00Z through 2026-05-02T07:00:03Z) as
  `Status: resolved` with a `**Resolved:** ...` line
  pointing back at v035.
- Updates `bootstrap/STATUS.md` to reflect v035 as the
  authoritative version + clears the four drift items
  from the next-action prose.

After v035 lands, the v034 D7 drain begins from a clean
PROPOSAL/plan state. Drain commits (`feat:` Red + Green
amend) operate under the post-v035 spec.

## Open items NOT covered by v035

- **v034 D8 branch protection on master** — still scheduled
  for the final Phase 5 sub-step per Plan §"D8 activation".
  Not affected by v035.
- **Anti-cheat reflog inspection (post-v1.0.0)** —
  acknowledged as deferred in v035 D3; actual implementation
  is post-Phase-10 hardening work, out of scope for v035.
- **Full v034 D6 baseline-grandfathered mechanism** —
  permanently deferred per v035 D1. If a future situation
  warrants re-introducing baseline-grandfathered
  violations, that's a future propose-change cycle (post-
  Phase-6 against `SPECIFICATION/`, not against PROPOSAL).
- **`pre-Phase-6` PROPOSAL revisions** — none anticipated.
  The drain proceeds; the v034 D5c quality-comparison
  report runs against `pre-redo.zip` + `pre-second-redo.zip`;
  Phase 5 exit gates fire; D8 activates; Phase 6 begins.
