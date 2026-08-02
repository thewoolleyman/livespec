---
proposal: discharging-narrow-try-is-not-an-expected-failure-mode.md
decision: accept
revised_at: 2026-08-02T18:12:01Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. The correction is confined to what member 1's clause (b) COUNTS, and it lands as a CORRECTION TO THE CRITERION rather than as a fifth member of the exemption set, which stays EXHAUSTIVE — the same shape v184 used for the failability correction and the reason that one was ratifiable.

**THE SHAPE DECIDED IT, NOT THE COUNT.** Every function the correction relieves is a parse-or-classify function that catches a parse error and returns a defined value for that input class; none is a filesystem, process or network call; and `livespec` and `livespec-overseer` — between them 188 of the fleet's 411 convictions — are relieved not at all. A relaxing change that relieved a mixed bag would be the declared-empty escape wearing a new name. This one relieves a single coherent semantic class, which is the distinction on which v181 turned.

**THE MECHANICAL RULE REPRODUCES TWO HAND RULINGS AND REFUSES A THIRD, and the refusal is what settled acceptance.** `livespec-dev-tooling` had ruled all three of its remaining convictions, independently and earlier, as not-conversions. The correction reaches the same verdict on two of them without being told, and REFUSES the third — `cross_member_consumption`, whose handler is narrow but RECORDS the failure and continues rather than returning. A correction that relieved that one too would be a blanket; limb (iii) is what stops it being one.

**THE NARROW LIMB IS KEPT AND IT COSTS NOTHING MEASURED.** Written loose — "a `try` that returns a defined value" — the rule would exempt by its own terms exactly the population ruff `BLE` exists to convict, and this section binds `BLE` for that reason. Measured with limb (ii) removed on every governed member: ZERO functions anywhere are relieved by a broad handler, while broad discharging constructs do exist. The guardrail is free, so it is kept.

**RE-DERIVED BEFORE RATIFICATION, WITH THE CONTROL AND THE IDENTITY CONTROL BOTH RUN.** On `livespec-dev-tooling` master `7ffec46`: the shipped criterion reproduces universe 171 / offenders 3 and names the three known functions; an IDENTITY rewrite through the same probe pipeline moves NOTHING (3 -> 3), which is what makes the widened figure quotable at all, because an earlier probe of this same question was contaminated by a global `Path.read_text` patch and reported an increase a relaxing change cannot produce; the four-limb rule measures 3 -> 1; and the loose arm relieves the SAME two, adding nothing.

**THE INTENT-PRESERVATION GATE WAS CHECKED AND DOES NOT FIRE, recorded as an explicit negative rather than a silence.** The candidate conflict is between clause (b) as written and member 1's own uninhabited-track rationale, and neither carries a design-record citation — the shape that forced the brief-84 acknowledgment in v184. It is NOT that shape here: clause (b) is a limb of member 1's own test rather than an independent ratified statement, and the ratified text already declares its analysis CONSERVATIVE IN THE DISQUALIFYING DIRECTION, so a limb over-approximating its own purpose is the sanctioned failure direction rather than a contradiction. What that conservative rule governs is DOUBT; a discharging narrow `try` is decidable from the AST with no ambiguity, and the accepted text preserves the doubt rule verbatim by requiring any doubt about a limb to disqualify.

**WHAT IS DELIBERATELY NOT RATIFIED HERE.** Clause (e)'s spelling gap — an `Any` or absent return annotation defeats the `X | None` refusal, so one relieved function's failure-`None` escapes it — is recorded in the ratified text as an unguarded residual with its cause named, and is left to its own amendment. Its exposure cannot be honestly quoted before it is mechanized, which is this section's own rule, and bundling an unmeasured tightening into a measured correction is what that rule exists to prevent.

## Resulting Changes

- non-functional-requirements.md
