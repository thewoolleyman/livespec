---
proposal: install-verification-must-not-pass-vacuously.md
decision: modify
revised_at: 2026-07-19T07:43:51Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted with modifications, after the mandatory independent Fable adversarial
review returned BLOCKERS FOUND (two blockers, seven nits). Dispositions below.

BLOCKER 1 (fixed) — the guard as proposed was itself vacuous one level down.
It tested `enabledPlugins` for dict non-emptiness, but a `false` value is a
non-empty entry, so `{"livespec@livespec": false, ...}` skipped both DEFECT
branches and certified a project with nothing enabled. Reproduced directly
against a root holding genuine install records: "OK: 2 enabled plugins all
installed for /data/projects/homelab", exit 0, with zero plugins enabled. The
state is one command away — `claude plugin disable --all -s project` is a
first-class CLI verb on the version in use. That a proposal titled "must not
pass vacuously" shipped a vacuous guard is precisely the failure this review
step exists to catch. The contract now defines the defective state as
`enabledPlugins` "empty, absent, or containing no `true`-valued entry", and the
enumeration clause now reads "for EVERY `true`-valued key".

BLOCKER 1, secondary (fixed) — the original "for EVERY key" wording forced an
install record for explicitly DISABLED plugins, so a mixed `{"a": true,
"b": false}` with `b` uninstalled produced a false MISSING. The amended clause
states that a `false` value MUST NOT be read as requiring a record.

ROUND-3 BLOCKER 1 (fixed) — the round-2 text asserted that `claude plugin
disable --all -s project` "sets every value to `false`". The review objected
that nobody had observed this and that upstream docs hinted the disable path
might write to `.claude/settings.local.json` instead. Running it settled both
points, and the sentence was wrong in a way neither of us predicted: the
invocation does not exist — the CLI rejects it with "Cannot use --scope with
--all". The valid form, `claude plugin disable <plugin> -s project`, WAS then
observed writing `false` into the COMMITTED `.claude/settings.json`, retaining
the key, leaving the install record intact, and creating no
`settings.local.json`. So the mechanism claim was right, the command form was
invented, and the `settings.local.json` hypothesis does not hold for this path.
The contract now states the observed form, hedged as observed, and notes the
`--all`/`--scope` incompatibility. The same correction is swept across the four
other surfaces that carried the claim.

ROUND-3 BLOCKER 2 (fixed) — `AGENTS.md`, `README.md`, and the prompt's own
post-snippet paragraph were still round-1 text: unhedged, silent on the
all-false route, and mandating an UNCONDITIONAL restore-from-version-control
that contradicted the de-adoption carve-out landing in the same PR. All three
now enumerate the three vacuity levels, hedge as observed, and carry the
carve-out.

ROUND-3, THIRD VACUITY LEVEL (folded in, not deferred) — the review supplied a
failing fixture: `enabledPlugins` reduced to a single `true` entry while
`extraKnownMarketplaces` still declares three marketplaces passed as
"OK: 1 enabled plugins all installed", exit 0, for a project missing two of its
three plugins. Whole-set non-vacuity cannot catch it. The contract now requires
every declared marketplace to be referenced by at least one `true`-valued entry,
and the reference check implements it. The reviewer's stronger remedy — compare
the working file against committed HEAD — is deliberately NOT adopted here: a
first-time adopter has not yet committed `.claude/settings.json`, so that
predicate would fail the exact case this whole change exists to fix. It is
recorded in livespec-dhro as the eventual class-killer.

BLOCKER 2 (fixed) — the paragraph's committed remediation covered less than the
invariant it sits inside. `ensure_plugins.py` derives its command set from the
same committed settings file, so an empty or all-`false` `enabledPlugins`
derives zero commands and exits 0: the same vacuous pass, in the very tool the
paragraph cites. The follow-up clause now names the non-vacuity guard alongside
the `projectPath` verification, and the scope of the owning work-item
(livespec-zxf6) has been extended in the ledger to match, so the commitment is
real rather than textual.

NIT 6 (applied) — boundary asymmetry. The review's verdict was that stating
observed platform behavior here is NOT a boundary violation, since every new
MUST binds livespec-side verification, matching established section style. Two
corrections adopted: the amendment now hedges as "has been observed to rewrite"
rather than asserting version-contingent behavior as timeless fact, and the
neighbouring uninstall clause now mirrors the update clause so uninstall and
disable are constrained by the invariant on the same footing.

NIT 7 (applied) — "MUST be restored from version control" presumed the removal
was accidental. Deliberate de-adoption now has an explicit carve-out: remove
both blocks together and commit.

NIT 3 (applied, docs) — absent or malformed `installed_plugins.json` produced a
raw traceback. Now caught, yielding a DEFECT message; an absent registry is
treated as "nothing installed" and reports MISSING.

NIT 9 (applied) — "a project ... is ITSELF a defective state" corrected to
"a configuration".

NITS 4, 5, 8 (deferred, filed as livespec-dhro) — marketplace-coverage gap,
stale-`installPath` gap, and the pre-existing tension that a machine-wide
(`-s user`) record carries no `projectPath` at all yet the contract calls that
form supported. Item 8 is a genuine internal inconsistency dating to v166 and
is flagged as the one to resolve first; folding any of the three into this
amendment would widen it beyond the defect it fixes.

Verified by execution, not inspection, across five states: all-false → DEFECT/1;
mixed true/false with the false one uninstalled → OK/1-enabled/0; healthy →
OK/0; empty enablement → DEFECT/1; enabled-without-record → MISSING/1.

No `## ` heading is added, changed, or removed, so no
`tests/heading-coverage.json` co-edit is owed.

## Modifications

Four exact-string replacements in SPECIFICATION/contracts.md §"Plugin
distribution", each asserted to match exactly once, expanding the proposal's
single replacement to cover the review's two blockers:
1. The non-vacuity requirement now covers all-`false` enablement, hedges the
   uninstall behavior as observed, names `claude plugin disable --all`, and
   carves out deliberate de-adoption.
2. The enumeration clause is scoped to `true`-valued keys, eliminating the false
   MISSING for explicitly disabled plugins.
3. The committed follow-up is extended to the non-vacuity guard, since
   `ensure_plugins.py` exhibits the same vacuity it is cited against.
4. The neighbouring uninstall clause is widened to uninstall AND disable and
   mirrors the update clause's constraint by the invariant.

## Resulting Changes

- contracts.md
