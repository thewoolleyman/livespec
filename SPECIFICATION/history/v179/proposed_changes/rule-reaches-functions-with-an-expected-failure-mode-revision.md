---
proposal: rule-reaches-functions-with-an-expected-failure-mode.md
decision: accept
revised_at: 2026-07-29T05:01:11Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-rop-railway-enforcement
---

## Decision and Rationale

ACCEPTED under the delegated accept/reject authority, extended to this core spec tree. Supervisor brief 26 authorized filing it and named it the last gate before arming.

ACCEPTED ON A MEASUREMENT THAT ARGUES AGAINST HAND JUDGEMENT, which is why member 1 is mechanical rather than declared. Of six functions an experienced per-function reading called total, the fixpoint disqualified one: `classify_role_key_declarations` has no raise, no try and no I/O in its own body, but calls `layout_dependent_check_slugs`, which walks the filesystem. Clause (d) is therefore load-bearing rather than a refinement, and an implementation that checks only a function's own body would exempt functions that reach I/O one call away.

EROSION IS THE RISK THIS RULING WAS MOST TESTED AGAINST, and member 1 answers it structurally rather than procedurally: it stores no claim, so there is nothing to go stale. It is recomputed from the body and call graph on every run, so adding a raise, a try, an I/O call or a call to a function that has one re-arms the rule at that commit. A declaration plus re-verification would have been strictly weaker — true when written and silently false later, which is this rule set's signature defect.

MEMBER 2 IS THE ONE THAT CAN DECAY AND IT IS BOUNDED FOUR WAYS — a structural gate (only `X | None` annotations), a required written reason, a HARD-FAILING staleness detector so a declaration cannot outlive its subject, and a counted fleet-wide total so growth is measured rather than capped by a number nobody can calibrate. The one residual — a declared `None` changing meaning from absence to failure while keeping its shape — is UNGUARDED and is stated in the ratified text rather than hidden.

IT IS BOTH FIDELITY AND A NARROWING, and the ratified text says so. It is the second scoping in two revisions: v178 narrowed which functions are public, this narrows which public functions the rule reaches. Accepting it without recording that the core obligation has now been scoped twice would be exactly the kind of quiet reduction this epic exists to surface.

AND IT DELIBERATELY EXEMPTS NOTHING THAT RAISES. A raise is an expected failure mode expressed off-railway and disqualifies under clause (a) whichever flavour it is. Three of the eight measured offenders raise or reach I/O and remain ORDINARY CONVERSIONS.

## Resulting Changes

- non-functional-requirements.md
