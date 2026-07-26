---
topic: retire-loop-iteration-broad-catch-permission
status: proposed
author: claude-opus-5
---

# Retire the supervision-loop per-iteration broad-catch permission

## Motivation

**Maintainer ruling, 2026-07-26.** A daemon does not get a per-iteration broad catch. "Let it
crash, systemd restarts": a bug raised while evaluating one supervised unit propagates, the daemon
logs the full traceback and exits, and its process supervisor restarts it. **Exactly one broad
catch per program, in `main()`.**

Three previously-considered alternatives are ALL rejected, and none may be reintroduced:

| Option | What it was | Status |
|---|---|---|
| (A) | A file-scoped loop-body exemption confined to declared entry artifacts | REJECTED |
| (B) | A loop-body exemption anywhere in `source_trees` | REJECTED |
| (C) | A new role key declaring loop position | REJECTED |

No new exemption shape, no widened position rule, no new config key.

### Why the permission is safe to withdraw, verified rather than assumed

The only armed site in the fleet is `livespec-overseer` `overseer/supervisor.py`, the per-tick catch
in `Supervisor.run` (line 2793 as of this writing) (swept across
`origin/master` of all nine fleet repos). The `run()` docstring that justified it named exactly two
failure cases, and BOTH are already boundaried by narrow catches below it:

- "an unreadable `plan/` dir" — caught in `overseer/registry.py`'s plan-thread discovery
  (`discover_plans`, the handler on the `plan_dir.iterdir()` call; line 529 as of this writing),
  whose own docstring cites the same "must not crash the daemon that supervises ALL tracks"
  rationale.
- "a malformed store" — caught in `overseer/registry.py`'s `_read_rows` (the handler on the mapping
  store's `read_text`; line 279 as of this writing), plus a per-line `json.JSONDecodeError` catch.

Both are cited by FUNCTION first and line second on purpose: the line numbers moved by two while
this change was in flight, because closing the `UnicodeDecodeError` leaks (livespec-overseer PR
#118) added comments above those very handlers. An independent reviewer caught the stale numbers.
A function name survives that; a bare line number does not.

So once predictable I/O failures are boundaried narrowly, **bugs are the only exception class that
can reach the loop guard** — which is exactly the condition under which propagation is correct. One
genuine leak was found and closed first (`UnicodeDecodeError` subclasses `ValueError`, so six
`OSError`-only handlers let it through; livespec-overseer PR #118), because deleting the guard
before closing it would have converted a recoverable environmental error into a permanent
crashloop.

## The change

Amends `non-functional-requirements.md` at FOUR locations. A single-location edit would ratify a
PARTIAL narrowing, leaving §"Linter rule set" still listing the retired marker as conforming.

### EDIT 1 — §"ROP composition" fleet-wide railway bullet (line 114)

"Two categories sit outside this boundary-handler rule" becomes **ONE**, governed by §"ROP
composition" alone, with an explicit note that the supervision-loop permission was withdrawn.

### EDIT 2 — §"ROP composition" breadth clause (line 651), three amendments

1. The enumerated boundary forms drop `loop-iteration`: "its supervisor, fail-open, and
   fail-closed forms".
2. Only the foreign-code catch now "sits OUTSIDE a `main()` boundary", governed by its own clause.
3. The review-attribution sentence is re-derived (see EDIT 4's rationale — the same claim appears
   in both sections and must move in lockstep).

### EDIT 3 — §"Supervisor discipline" (line 675), the permission itself

The `**Long-running supervision loop (per-iteration resilience):**` block granting ONE ADDITIONAL
broad catch is replaced by `**Long-running supervision loop — NO per-iteration exemption:**`, and
the preceding carve-out drops "and the loop-iteration catch defined next". The replacement:

- states the MUST NOT plainly, and that the daemon logs and exits for its process supervisor to
  restart;
- records that the cardinality rule above is therefore the WHOLE rule for a daemon as much as for
  a CLI, and that **a daemon has no second accounting unit**;
- retains the withdrawn permission's own reasoning as history, then says why it does not hold: a
  loop that swallows a bug and re-enters keeps re-reading the same bad state, so it presents as
  supervising while enforcing nothing;
- adds the load-bearing operational corollary: **a daemon MUST boundary its predictable I/O
  failures narrowly BEFORE relying on crash-and-restart, or restarting merely repeats the crash.**

### EDIT 4 — the enforcement-attribution sentences (lines 651 and 675)

These two sentences list what is enforced by REVIEW rather than mechanically. Both were stale in
the **understating** direction, independently of this ruling — this is the amendment
`livespec-dev-tooling-jjb`'s hard constraints already required, and it is folded in here because it
is literally the same prose the narrowing rewrites. Landing it separately would mean editing the
same two sentences twice.

Of the four items previously listed as review-enforced:

| Item | New attribution |
|---|---|
| Exact marker wording | **MECHANIZED** — `check-no-except-outside-io` matches the three boundary wordings by EQUALITY (text before, around, or after a wording disqualifies the comment) and the foreign-code template by an anchored shape |
| Per-artifact `sole` cardinality | **MECHANIZED** — a per-entry-artifact tally of marked boundary catches, naming the EXCESS catch (livespec-dev-tooling PR #662) |
| Per-supervision-loop cardinality | **DISSOLVED** — withdrawn with the permission, not mechanized; it appears in neither list |
| Flavor pairing | still REVIEW-enforced |
| Per-flavor contract discharge | still REVIEW-enforced |

So **TWO** rules remain review-enforced, not four. The old text's "beyond the closed-set substring
the check matches" is also retired: the check no longer matches a substring.

### EDIT 5 — §"Linter rule set" closed marker set (line 783)

The retired wording is removed from the closed set, and **both closed counts are re-derived**:

- "the **five** standardized markers" → **four**
- "the **four** supervisor/boundary/loop categories" → **three**

The "`sole` scope differs by marker" sentence existed ONLY to explain the per-supervision-loop
scope, so it is rewritten: `sole` now has ONE scope, and the three boundary markers SHARE a single
per-artifact slot. A closing sentence records the retirement explicitly, so a reader who
encounters the wording in older code learns it no longer conforms rather than assuming an omission.

## Counts and enumerations touched

Recorded explicitly because counts are this specification's most fragile clause type — the
`livespec-dev-tooling-e9j` ratification needed repair to four separate closed enumerations, and two
reviewers once disagreed over a tally because the document contained two different populations:

- five standardized markers → four
- four supervisor/boundary/loop categories → three
- two categories outside the boundary-handler rule → one
- four review-enforced rules → two

## What this does NOT change

- The foreign-code isolation catch, its per-extension-invocation-surface accounting, and its
  anchored template shape are untouched.
- The per-artifact single-boundary cardinality rule binds unchanged; it simply becomes the whole
  rule rather than one of two accounting units.
- `livespec-dev-tooling` `SPECIFICATION/contracts.md`, the `supervisor_entry_files` role-key bullet
  (line 217 as of this writing), needs NO amendment — it already reads "files whose `main()`
  direct-child `try/except` is exempt", which is exactly the narrowed rule.
- No `## ` H2 heading is added, renamed, or removed, so no `tests/heading-coverage.json` co-edit is
  required (verified by diffing the H2 sets).

## Sequencing

`livespec-dev-tooling` PR #681 already retired the wording from the enforcement suite's closed set
and INVERTED the test that sanctioned it. That deliberately landed FIRST: had this specification
narrowed alone, the enforcement suite would have actively sanctioned what the ratified
specification forbids. `livespec-driver-claude-jzy` (the hand-copied closed-set literal) has ALSO
already landed, as that repo's commit `56269561`, which deleted the local copy rather than trimming
it and delegated the retired-wording proof to PR #681's inverted test.

**The sole remaining consumer work is `overseer-bg2.2`** — deleting the armed catch named above. Its
own precondition (livespec-overseer PR #118, closing six `UnicodeDecodeError` boundary leaks) has
landed, so nothing gates it but this ratification.

This enumeration is written as of ratification and is deliberately short-lived; treat any later
reading of it as history rather than as current fleet state.
