---
topic: total-predicate-io-boundary
author: claude-opus-5
created_at: 2026-08-02T05:30:00Z
---

## Proposal: an I/O boundary is a primitive that CAN FAIL, not a primitive that is NAMED

### Target specification files

- non-functional-requirements.md

### Summary

§"ROP composition" defines an I/O boundary twice — once in the rendering-boundary clause's **condition 1** ("a function that calls a side-effecting primitive DIRECTLY … IS such a boundary") and once in **member 1 clause (c)** ("no call to an I/O boundary — a module under the consumer's declared `io_trees`, or the filesystem / process / network / environment surface"). Neither definition asks whether the primitive can FAIL. For a **total predicate** — a filesystem call that swallows its own `OSError` and returns a value rather than raising — the two clauses give OPPOSITE answers about the same function, and both answers are ratified. Add a rule making failability the criterion: a primitive that CANNOT fail is not an I/O boundary for either clause.

### Motivation

**This is a contradiction in the ratified text, not a judgement call, and it is reachable today.** A public function whose ONLY direct primitive is `Path.exists()`, `Path.is_file()` or `Path.is_dir()` is simultaneously:

- an I/O boundary under condition 1, which says the clause "does not reach it and MUST NOT be used to avoid converting it" — so it MUST be on `Result`/`IOResult`; and
- a function with no expected failure mode under member 1's own stated rationale, since a `Result` over it "carries an UNINHABITED failure track: every caller must unwrap for an outcome that cannot occur, and those dead unwraps are noise that hides the live ones."

Two ratified clauses, opposite verdicts, same function. Under the current text the only way to comply with one is to violate the other's rationale.

**The premise is MEASURED, not assumed.** Against CPython 3.10, with both polarities from the same probe so the negative result is credible:

```
is_file()  on a path whose parent is a FILE  -> False      (swallows)
is_dir()   on a path whose parent is a FILE  -> False      (swallows)
exists()   on a path whose parent is a FILE  -> False      (swallows)
read_text() on a DIRECTORY                   -> RAISES IsADirectoryError
```

`Path.exists()`, `Path.is_file()` and `Path.is_dir()` catch `OSError` internally and answer `False`. They are TOTAL: there is no input for which they fail, so there is nothing for a failure track to carry.

**The exposure is not hypothetical and it is about to multiply.** In `livespec-dev-tooling` today, 2 of the repo's remaining condition-1 failures are exactly this shape (`reconcile_beads_dir_perms`, `reconcile_beads_metadata_present`) — every other condition-1 failure in that repo has been closed by a seam, and these two are what remains because no seam can close them. Fleet-wide the arming cost is 455 offenders over a universe of 719 across seven repos, none of which has yet been triaged against this clause. A contradiction met once is a puzzle; met hundreds of times it becomes unenforced practice, which this specification's own rule refuses: an exemption that is right MUST be ratified rather than left to accumulate.

**FRAMING, STATED PLAINLY BECAUSE THE WRONG FRAMING HAS COST THIS FLEET BEFORE.** This is NOT a fifth member of the exemption set, which §"ROP composition" declares EXHAUSTIVE, and it is NOT a widening of what counts as on-the-railway in the manner of the rendering-boundary clause. **It is a CORRECTION to the definition of "I/O boundary" itself, and it moves in BOTH directions:**

- **Relaxing**, for a function whose only direct primitives are total predicates: it was never a place a failure could originate, so it leaves scope — the honest answer rather than an exemption granted to it.
- **TIGHTENING**, for a function calling a primitive that genuinely raises but is absent from a NAMED verb set: `open`, `readlink`, `chown`, `truncate` and `Path.walk` all raise and are currently missed by at least one conforming implementation, so they come INTO scope.

A rule that only relaxed would be a relief and would deserve the scrutiny a relief gets. This one corrects a criterion that is wrong in both directions, and the tightening half is the evidence that it is a fidelity fix rather than a convenience.

**Deliberately NOT proposed:** any enumerated list of verbs in the specification text. A list is what fails — it is what produced the wrong answers in both directions — and a normative list here would have to be re-ratified for every standard-library revision. The rule specifies the CRITERION and requires the implementation to record its per-verb determinations; the list is an implementation artifact, recomputed, never a spec constant.

This proposal adds no new `## ` heading — it inserts a bolded rule block inside the existing §"ROP composition" section — so it carries no `tests/heading-coverage.json` co-edit obligation.

### Proposed Changes

In `non-functional-requirements.md` §"ROP composition", insert a new bolded rule block **What counts as an I/O boundary** immediately before the **MEMBER 1 — MECHANICALLY DECIDED, RECOMPUTED EVERY RUN** block:

**What counts as an I/O boundary.** Every rule in this section that turns on a function "performing I/O" or "calling a side-effecting primitive" — the rendering-boundary clause's condition 1 and member 1's clause (c) alike — means a primitive AT WHICH A FAILURE CAN ORIGINATE. **A primitive that CANNOT FAIL is NOT an I/O boundary, and a function is not made one by calling it.** A primitive cannot fail when, for every input, it either returns a value or the language guarantees it does not raise: the filesystem TOTAL PREDICATES (`Path.exists`, `Path.is_file`, `Path.is_dir`, and their siblings that catch `OSError` internally and answer `False`) are the governing case, and they are total by the standard library's own contract rather than by the caller's discipline. This is a CORRECTION to the criterion, NOT a fifth member of the exemption set above, which remains EXHAUSTIVE: a function whose only direct primitives are total predicates was never a place a failure could originate, so nothing is exempted from the railway here. It follows that the two clauses can no longer disagree about such a function — under the previous reading condition 1 convicted it while member 1's rationale forbade converting it, since a `Result` over a call that cannot fail carries exactly the UNINHABITED failure track that rationale exists to prevent. **The correction is NOT one-directional and MUST NOT be implemented as though it were.** It equally brings INTO scope every primitive that genuinely raises, including those a name-matching implementation omits — `open`, `readlink`, `chown`, `truncate` and directory walks among them — so a conforming implementation MUST NOT satisfy this rule by removing total predicates from a list while leaving that list otherwise unchanged. **A conforming implementation decides failability MECHANICALLY and STORES NO CLAIM**, recomputing membership from the code and the language's contract on every run, exactly as member 1 does; there is no per-function judgement at check time, and there is no declaration a consumer can write to assert that a primitive is total. Where a primitive's failability is genuinely ambiguous — a call that raises for one argument shape and returns empty for another, such as globbing and directory iteration — the implementation MUST resolve it against the language's actual behavior and MUST record the determination and its evidence, and MUST resolve UNRESOLVED ambiguity as FAILABLE, so that doubt tightens the rule rather than relaxing it.
