---
topic: rule-reaches-functions-with-an-expected-failure-mode
author: claude-opus-5-rop-railway-enforcement
created_at: 2026-07-29T05:00:34Z
spec_commitments:
  impl_followups:
    - id_hint: no-expected-failure-mode-mechanical-member
      description: |
        Implement the MECHANICAL member in `check-public-api-result-typed`: a purely syntactic, per-run analysis of a public function's own body plus a fixpoint over first-party callees. It stores nothing, so it cannot erode. Must be conservative in the disqualifying direction: an unresolved callee, any `raise`, any `try`, any I/O boundary, or an `X | None` return all DISQUALIFY.
    - id_hint: no-expected-failure-mode-declared-absence-key
      description: |
        Implement the DECLARED member: a `total_absence_returns` role key naming `<module>:<function>` entries whose `X | None` return models a legitimate ABSENCE rather than a failure, each with a written reason. The check MUST hard-fail on a STALE entry — one whose function no longer exists or no longer returns `X | None` — so a declaration cannot outlive its subject.
---

## Proposal: The Result-return rule applies to a function that HAS an expected failure mode

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"ROP composition" states the railway's purpose as expected failure modes flowing as failure-track values, then states the Result-return rule over 'every public function' without qualification. For a public function with NO expected failure mode the two are in tension: there is nothing to flow, and a `Result` on such a function has an uninhabited failure track that forces every caller to unwrap for nothing. This proposal scopes the rule to functions that HAVE an expected failure mode, via exactly two members — one MECHANICALLY DECIDED and recomputed on every check run, one ACTIVELY DECLARED with a written reason and a staleness detector. It states plainly that this is both fidelity to the stated purpose AND a narrowing of the rule's central requirement.

### Motivation

After ratified v178 scoped public API to what is CONSUMED ACROSS A BOUNDARY, `livespec-dev-tooling` measures 8 public offenders. Every one was read per function AND re-checked mechanically. Four have no expected failure mode at all; one returns `X | None` where the `None` is a legitimate absence; three have genuine failure modes and are ordinary conversions. Converting the first five would manufacture five `Result` types whose failure track cannot be inhabited, and the dead unwraps at their call sites are noise that hides the live ones — which inverts the rule's purpose rather than serving it. The design is driven by one measured fact: HAND JUDGEMENT GOT ONE OF SIX WRONG. `classify_role_key_declarations` reads as total — no raise, no try, no I/O in its own body — but it calls `layout_dependent_check_slugs`, which walks the filesystem. A per-function reading by an experienced reader classified it TOTAL; the mechanical fixpoint caught the transitive I/O and disqualified it. That is why the primary member must be mechanical rather than declared, and it is evidence rather than preference.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"ROP composition", immediately AFTER the paragraph block beginning "**WHAT COUNTS AS PUBLIC FOR THIS RULE.**" (ratified v178) and BEFORE the line "Enforced by `check-public-api-result-typed` (AST).", INSERT the following.

---

**WHAT THE RULE REACHES: A FUNCTION THAT HAS AN EXPECTED FAILURE MODE.** The railway exists so that EXPECTED failure modes flow as failure-track values. A public function with no expected failure mode has nothing to flow, and a `Result` over it carries an UNINHABITED failure track: every caller must unwrap for an outcome that cannot occur, and those dead unwraps are noise that hides the live ones. The Result-return rule therefore reaches a public function when, and only when, it HAS an expected failure mode. Membership is settled by exactly TWO mechanisms and there is no third — in particular there is NO per-function judgement at check time, because a rule that needs one is a triage rather than a check.

**MEMBER 1 — MECHANICALLY DECIDED, RECOMPUTED EVERY RUN.** A public function has no expected failure mode when a purely syntactic analysis of its body shows ALL of:

- (a) no `raise` statement;
- (b) no `try` statement;
- (c) no call to an I/O boundary — a module under the consumer's declared `io_trees`, or the filesystem / process / network / environment surface;
- (d) every FIRST-PARTY function it calls also satisfies (a)–(d), computed as a FIXPOINT over the consumer's own call graph; and
- (e) its `return` annotation is NOT of the form `X | None`.

The analysis MUST be CONSERVATIVE IN THE DISQUALIFYING DIRECTION: an unresolved callee, an ambiguous call target, or any doubt disqualifies, so the failure mode of the analysis itself is to DEMAND a `Result` that was not needed — never to excuse one that was.

**CLAUSE (d) IS LOAD-BEARING AND IS NOT A REFINEMENT.** Transitive reach is where a per-function reading fails. Measured during this proposal's preparation: a function with no `raise`, no `try` and no I/O in its OWN body was classified total by an experienced hand reading, and the fixpoint disqualified it because a callee walked the filesystem. **Any implementation that checks only the function's own body is WRONG and will exempt functions that reach I/O one call away.**

**CLAUSE (e) EXISTS BECAUSE `X | None` IS THE HAND-ROLLED FAILURE TRACK THIS RULE EXISTS TO CONVERT.** Whether a `None` models a FAILURE or a legitimate ABSENCE is a semantic question no AST can answer, so the syntactic member refuses the whole shape rather than guessing. That refusal is what member 2 exists to relieve, narrowly.

**MEMBER 1 CANNOT ERODE, AND THAT IS THE POINT OF MAKING IT MECHANICAL.** It is not a declaration; it stores no claim. It is recomputed from the function's own body and call graph on EVERY check run, so the moment an editor adds a `raise`, a `try`, an I/O call, or a call to a function that has one, the analysis stops holding and the rule demands a `Result` at that commit. **There is no stored assertion to go stale, and therefore no exemption whose truth decays undetected.** A declaration plus periodic re-verification would be strictly weaker: it would be true when written and silently false later, which is the exact defect class this rule set exists to remove.

**MEMBER 1 ALSO CANNOT BECOME A DUMPING GROUND**, and for the same reason: there is nothing to add to. Membership is a function of the code, not of a list, so no consumer can declare its way in. The only way to enter member 1 is to write a function that genuinely has no expected failure mode.

**MEMBER 2 — ACTIVELY DECLARED, AND STRUCTURALLY BOUNDED.** A public function whose `return` annotation is `X | None` and whose `None` models a legitimate ABSENCE rather than a failure is outside the rule when the consumer DECLARES it, per function, with a written reason, in the `total_absence_returns` role key of its `[tool.livespec_dev_tooling]` block. An absence is an ordinary answer the caller acts on; a failure is an outcome the caller must handle. Wrapping an absence in `Failure` forces every caller to unwrap for an ordinary answer.

Four bounds are part of the rule, not implementation detail:

1. **A STRUCTURAL GATE, not an open category.** The key reaches ONLY functions annotated `X | None`. A function of any other shape cannot be declared into it at all, so it is not a general-purpose escape hatch.
2. **A WRITTEN REASON per entry**, naming why the `None` is an absence. A bare path is not a declaration.
3. **A STALENESS DETECTOR THAT HARD-FAILS.** The check MUST verify each declared entry still resolves to an existing public function that still returns `X | None`, and FAIL when it does not. A declaration cannot outlive its subject, and a function that is refactored out of the `X | None` shape drops its declaration loudly rather than carrying a dead exemption forward.
4. **COUNTED, SO GROWTH IS VISIBLE.** The per-repo and fleet-wide count of `total_absence_returns` entries MUST be reported by a central-vantage conformance row. Six declarations in one repo is small; the same carve-out unremarked across six repos is how a rule dies, and the defense against that is a measured number rather than a cap nobody can calibrate.

**AND ONE RESIDUAL IS UNGUARDED — stated rather than hidden.** If a declared function's `None` changes meaning from ABSENCE to FAILURE while keeping the `X | None` shape, no detector above fires: bound 3 catches a shape change, not a semantic one. That residual is the honest cost of member 2, and it is why member 2 is gated to one annotation shape and required to carry a reason a reviewer can check, rather than being widened to cover the `raise`-bearing cases that member 1 correctly disqualifies.

---

**IS THIS FIDELITY OR A NARROWING? IT IS BOTH, and the flattering half alone would be a misstatement.**

- **FIDELITY**, because the rule set already states the railway's purpose as expected failure modes flowing as failure-track values, and already states that BUGS propagate rather than flowing. A function with no expected failure mode was never what the railway was for; requiring `Result` of it satisfies the letter of "every public function" while defeating the purpose the same section states.
- **AND A NARROWING OF THE CENTRAL REQUIREMENT, said plainly.** "Every public function's return annotation MUST be `Result[_, _]` or `IOResult[_, _]`" is the core obligation of the ROP regime, and this scopes it. It is the second scoping in two revisions — v178 narrowed WHICH functions are public; this narrows WHICH public functions the rule reaches. Two narrowings in succession deserve to be read together rather than each on its own, and a reader who takes either as cost-free has taken it wrongly.
- **WHAT KEEPS THE NARROWING HONEST is that neither member admits a judgement call.** Member 1 is computed and cannot be argued with; member 2 is declared, structurally gated, reason-bearing, staleness-detected and counted. The category this rule set has repeatedly been damaged by — an exemption asserted in prose or config that nothing recomputes — is admitted by neither.

**WHAT THIS DOES NOT DO.** It does not exempt a function that raises. A `raise` is an expected failure mode expressed off-railway, and it disqualifies under (a) whether the raised error is domain-meaningful, a framework's failure protocol, or a report of a caller's wiring mistake. Those are ORDINARY CONVERSIONS, not exemptions, and each is gated on the consumer-wiring discipline that already binds any change to a consumed symbol. **An explicit `raise` is the WEAKEST signal that a conversion is unnecessary and the STRONGEST signal that one is owed** — the opposite of a plausible reading that treated a raise as evidence the function was already handling its failures.
