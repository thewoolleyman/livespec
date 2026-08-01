---
topic: rowoutcome-railway-spelling
author: claude-opus-5-rop-railway-enforcement
created_at: 2026-08-01T02:39:04Z
---

## Proposal: A closed discriminated union is a sanctioned railway spelling at a rendering boundary, under three binding conditions

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The Result-return rule is spelled as a requirement on the ANNOTATION — `Result[_, _]` or `IOResult[_, _]` — while the property it exists to secure is that expected failure modes flow as failure-track VALUES rather than as sentinels, exceptions, or in-band nulls. A closed discriminated union whose failure-side variants are inhabited and load-bearing already has that property. This change states that such a union is a sanctioned spelling AT A RENDERING BOUNDARY, and binds it with three conditions without which the sanction would be a loophole. It is deliberately NOT a fifth member of this section's exemption set, which the section declares exhaustive: nothing is exempted from the railway here, and the leaf obligation is tightened rather than relaxed.

### Motivation

Produced by the `livespec-dev-tooling-8o8e` remediation, from evidence rather than argument. `livespec-dev-tooling`'s fleet engines carry `RowOutcome` — a closed union of `RowPass` / `RowSkip` / `RowFinding` — as the return type of 65 row functions across a Protocol BOTH engines walk. Converting only the convicted subset would leave ONE Protocol with TWO return shapes, which is worse than either end state.

THE EVIDENCE IS TWO CONVERSIONS THAT WERE ACTUALLY PERFORMED, not a prediction. Both defects fixed in that epic's 2026-08-01 pair lived at the LEAF — functions that DO the I/O and had nowhere to put 'this did not happen'. `open_bump_prs_for` returned `list | None` and fed a stale-pin row that then CLAIMED the never-fired class it had not established. `member_matrix_targets` returned `set | None` over three states, so an UNREAD ci.yml certified a member's phantom required checks as ALIGNED — a row returning PASS because a read failed. Both fixes put a `Result` exactly at the leaf and RENDERED it into `RowOutcome` at the row boundary. At no point did the three-way outcome fail to express the answer: one needed a distinct MESSAGE at unchanged severity, the other needed `RowSkip` instead of `RowPass`. The union was sufficient both times, and the railway was necessary both times — ONE LAYER DOWN. That is the architecture the requirement asks for, not a gap in it.

THE SAME PRINCIPLE SENDS OTHER FUNCTIONS THE OPPOSITE WAY, which is the test that it is a principle and not a rationalisation. The `default_gh_runner` / `default_command_runner` / `default_gh_downloader` trio call `subprocess.run` DIRECTLY rather than through an injected parameter, so they ARE the boundary. An `OSError` there has no `try` anywhere in the chain and CRASHES a nine-member sweep partway through a member. That failure ORIGINATES there and is unrepresentable there, so those convert — they get no benefit from this clause.

AND THE SANCTION WOULD BE A LOOPHOLE WITHOUT CONDITION 2, MEASURED ON THE LIVE CODE. `RowOutcome` today has `Result`'s SHAPE but none of its ENFORCEMENT. Counted on master: 14 consumption sites, ALL of them independent `if isinstance(...)` chains — `_lanes.py` 3, `local_reconcile.py` 3, `wire_fleet_member.py` 4, `_rows_claude_plugin.py` 2, `_adopter_lane.py` 2 — and ZERO `match` statements over the union anywhere. `assert_never` appears ZERO times in that whole package. So a fourth variant could be added tomorrow and every one of those sites would silently fall through. `Result`'s real advantage was never the spelling; it was that `unwrap()` is unavoidable. Ratifying the union without requiring exhaustive matching would preserve the exact property that let its `RowSkip` acquire two contradictory meanings in the first place — one lane reading it 'not evaluable' and reddening master, the other reading it 'not applicable' and logging info.

### Proposed Changes

### `non-functional-requirements.md` §"ROP composition"

After the four-member exemption set and its member-4 discussion, add:

**A SANCTIONED ALTERNATIVE SPELLING AT A RENDERING BOUNDARY.** The rule
above secures a PROPERTY — expected failure modes flow as failure-track
VALUES — and states it as a requirement on the annotation. A CLOSED
DISCRIMINATED UNION whose non-success variants are inhabited and
load-bearing already has that property, and satisfies the rule at a
RENDERING boundary, when ALL THREE of the following hold. This is NOT a
fifth member of the exemption set above, which remains exhaustive: nothing
is exempted, and condition 1 TIGHTENS the obligation at the leaf.

1. **The failure ORIGINATES elsewhere and is represented there.** The
   union is a RENDERING of an outcome, never the place a failure is first
   discovered. Any function that performs the I/O, and therefore has
   somewhere a failure can originate and nowhere to put "this did not
   happen", MUST be on `Result` / `IOResult` — the union does not reach
   it and MUST NOT be used to avoid converting it. A function that calls
   a side-effecting primitive DIRECTLY, rather than through an injected
   seam, IS such a boundary.
2. **Every consumption site matches EXHAUSTIVELY.** A consumer MUST
   discriminate the union with a `match` statement terminating in
   `case _: assert_never(<subject>)`. A chain of independent
   `if isinstance(...)` tests does NOT satisfy this condition and is NOT
   sanctioned, even where it is exhaustive today. The reason is
   mechanical rather than stylistic: `check-assert-never-exhaustiveness`
   polices `match` statements and CANNOT SEE an `isinstance` chain, so a
   union consumed that way is governed by nothing, and adding a variant
   silently falls through every site. `Result`'s guarantee was never its
   spelling — it was that `unwrap()` is unavoidable; a sanctioned
   alternative MUST buy that guarantee back explicitly.
3. **No variant carries two meanings.** Each variant MUST mean exactly
   ONE thing to EVERY consumer. A variant that one consumer reads as "not
   evaluable" and another as "not applicable" is not a discriminated
   union, it is a sentinel with a type annotation, and it reintroduces
   precisely the in-band ambiguity this section exists to remove. Where
   inapplicability and unevaluability both arise, they MUST be distinct
   variants or distinct values, never one variant read by context.

A union meeting all three is on the railway for the purposes of the
annotation rule. A union meeting fewer is NOT, and the functions
returning it MUST convert.

⛔ **The blind spot in condition 2 is itself an instance of what this
section governs, and is recorded so it is not rediscovered.** An armed,
fleet-wired check that structurally cannot see part of the universe it is
meant to govern reports GREEN over that part forever. That is the same
shape as a scan universe that resolves to zero files. Condition 2 is
written to put the consumption sites INSIDE the existing check's field of
view rather than to add a new check, and a future consumer that reaches
for an `isinstance` chain is choosing a form nothing polices.

### `non-functional-requirements.md` — the fleet+adopter-wide railway clause

In the bullet beginning "**The ROP railway is fleet+adopter-wide.**",
after "expected failure modes flow as failure-track values", add a
parenthetical pointing at the new text: "(a closed discriminated union
MAY carry them at a rendering boundary under the three conditions in
§\"ROP composition\"; the leaf that performs the I/O is never covered by
that allowance)".
