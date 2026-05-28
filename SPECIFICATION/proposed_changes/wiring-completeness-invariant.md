---
topic: wiring-completeness-invariant
author: claude-opus-4-7
created_at: 2026-05-28T04:15:00Z
---

## Proposal: wiring-completeness-invariant

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Extend `contracts.md` §"Shared code sync — livespec-dev-tooling" inline with a wiring-completeness invariant that closes the consumer-drift hole the existing partition contract does NOT close. The existing prose says which checks SHOULD ship in `livespec-dev-tooling` (the universal-by-intent subset), but it does not say that every consumer MUST actually wire all of those checks into its own `just check` aggregate. Today that hole produces real drift: `livespec` itself wires 25 of the 30 structural checks shipped in `livespec-dev-tooling`'s canonical set, and the impl-plugin siblings wire 0 of 30 — a shipped check like `no_stale_revise_branches.py` therefore exists but runs in zero consumers, gating nothing.

The invariant has four interdependent points and three layers of mechanical enforcement:

1. **The invariant.** Every check in `livespec-dev-tooling`'s canonical set (dynamically derived from `livespec_dev_tooling/checks/*.py`, excluding `_*` helpers and `__init__.py`) MUST appear in every consumer's `just check` aggregate, in alphabetical order. Consumer-private checks MAY appear after the canonical set.

2. **The in-repo gate.** Every consumer MUST wire `check-aggregate-completeness` (the new `livespec-dev-tooling` check that mechanically enforces (1) locally against its own `justfile`). This gate is non-optional and self-bootstrapping — the wiring of the gate itself is enforced by the gate, so once a consumer adopts it, drift is impossible without also dropping the gate (which the gate would then catch on the next run via its own absence).

3. **The template gate.** `livespec/templates/impl-plugin/justfile.jinja` MUST stamp the full canonical aggregate at copier-copy time so future siblings inherit the discipline from inception. Combined with `copier update`'s 3-way merge, this also helps existing siblings absorb canonical-set growth as new checks are added to `livespec-dev-tooling`.

4. **The cross-repo backstop.** A new doctor invariant `wiring-completeness-cross-repo` MUST walk each registered sibling's `local_clone` (or GitHub-query its `justfile`) and fail on any aggregate lacking any canonical slug. This catches the adversarial drift the in-repo gate cannot — a consumer that drops both a canonical check AND `check-aggregate-completeness` from its aggregate at the same time.

All four points are interdependent and form a single coherent enforcement loop: revise should accept or reject them as one unit.

### Motivation

`contracts.md` §"Shared code sync — livespec-dev-tooling" today specifies what `livespec-dev-tooling` SHIPS (the universal-by-intent partition), but it does not specify what consumers must CONSUME. The partition contract assumes — without saying so — that every consumer wires every universal-by-intent check. Reality does not match the assumption:

- `livespec` itself currently wires 25 of the 30 structural checks shipped in `livespec-dev-tooling`'s canonical set (heuristic count from the current `livespec_dev_tooling/checks/*.py` inventory vs. the current `livespec` justfile aggregate).
- Every `livespec-impl-*` sibling and `livespec-dev-tooling` itself currently wires 0 of those 30 — the sibling repos copied the `livespec` justfile shape but did not import the canonical aggregate.
- The concrete consequence: `no_stale_revise_branches.py` is shipped in `livespec-dev-tooling`'s canonical set but is wired into zero `just check` aggregates anywhere in the family. The check exists, has tests, has been merged, has a CI matrix entry in dev-tooling itself — but it gates nothing in the consumer fleet. Every other canonical check that is shipped-but-not-wired has the same status: a shipped binary that fires in no real workflow.

The wiring-completeness invariant turns the implicit assumption into an explicit, mechanically enforced contract. Three layers — in-repo gate, template stamp, cross-repo doctor backstop — give defense-in-depth: a consumer that drops a canonical slug from its aggregate gets caught locally by `check-aggregate-completeness` on the next `just check`; a consumer that drops both the canonical slug AND `check-aggregate-completeness` gets caught by `/livespec:doctor` via the `wiring-completeness-cross-repo` invariant; and a fresh sibling generated from `copier copy` inherits the full canonical aggregate at copy time so the wiring-completeness state is the default-on rather than the default-off.

This PC also closes the cosmetic-vs-structural ambiguity in the existing prose. The current "Enforcement-suite checks that ship in `livespec-dev-tooling` MUST be those whose intent and CLI surface are stable across every livespec-governed project" sentence describes a SHIPPING contract. With this PC, the corresponding CONSUMPTION contract becomes explicit: every consumer wires the full canonical set, in canonical (alphabetical) order, gated by `check-aggregate-completeness`.

### Heading-coverage co-edit discipline

This PC introduces NO new `## ` heading to `contracts.md`. The wiring-completeness prose is inline extension of the existing §"Shared code sync — livespec-dev-tooling" section. Therefore `tests/heading-coverage.json` requires NO co-edit under this proposal.

### Proposed prose insertion

Insert the following prose into `contracts.md` §"Shared code sync — livespec-dev-tooling" immediately after the existing paragraph that begins "Enforcement-suite checks that ship in `livespec-dev-tooling` MUST be those whose intent and CLI surface are stable across every livespec-governed project..." (currently the paragraph at line 557). The insertion extends the existing partition prose with the corresponding consumption contract; it does not introduce a new H2 or H3 subsection.

> **Wiring-completeness invariant.** Every check in `livespec-dev-tooling`'s canonical set MUST appear in every consumer's `just check` aggregate, in alphabetical order. Consumer-private checks MAY appear after the canonical set. The canonical set is dynamically derived from `livespec_dev_tooling/checks/*.py` (excluding `_*`-prefixed helper modules and `__init__.py`) by the `livespec_dev_tooling.canonical_checks` module, which is the single source of truth for the canonical slug list. Manual lists of "the canonical checks" elsewhere in any consumer (e.g., hand-maintained justfile arrays, READMEs, CI matrix snippets) MUST be replaced by mechanical derivation from `livespec_dev_tooling.canonical_checks` or by a check that compares the manual list to the canonical list and fails on drift.
>
> The invariant is enforced via three layers, designed as defense-in-depth so that no single layer's failure leaves the discipline unenforced:
>
> 1. **In-repo gate.** Every consumer MUST wire `check-aggregate-completeness` — the `livespec-dev-tooling` check (shipped at `livespec_dev_tooling.checks.aggregate_completeness`) that compares the consumer's own `just check` aggregate body against the canonical set and fails on any missing canonical slug or any non-alphabetical ordering within the canonical-set range. The gate is self-bootstrapping: `check-aggregate-completeness` is itself one of the canonical checks, so a consumer that drops it from its aggregate fails the invariant on the next `just check` run (because the canonical slug is now missing) and on every subsequent run until the gate is re-wired.
>
> 2. **Template gate.** `livespec/templates/impl-plugin/justfile.jinja` MUST stamp the full canonical aggregate at `copier copy` time so every newly-generated `livespec-impl-*` sibling inherits the wiring-completeness state from inception. The template MUST derive the stamped list from `livespec_dev_tooling.canonical_checks` at copy time (via a copier `_jinja_extension` or equivalent), NOT from a hand-maintained list in the template, so that template-generated repos pick up canonical-set growth automatically as new checks land in `livespec-dev-tooling`. For existing siblings, `copier update`'s 3-way merge surfaces canonical-set drift as merge conflicts in the regenerated `justfile`, giving an additional human-review checkpoint on top of the in-repo gate.
>
> 3. **Cross-repo backstop.** A doctor invariant `wiring-completeness-cross-repo` (see §"Doctor cross-boundary invariants") MUST walk every registered sibling repo (per the `livespec-dev-tooling` and `livespec-runtime` and `livespec-impl-*` registries declared in this contracts.md), read its `justfile`'s `check` recipe, compute the canonical-set difference, and fire `fail` on any aggregate lacking any canonical slug. The check MAY use a sibling's `local_clone` path when configured or fall back to a GitHub query against the sibling's default-branch `justfile`. The invariant covers the adversarial-drift case in which a consumer drops both a canonical slug AND `check-aggregate-completeness` from its aggregate in the same change — the in-repo gate cannot catch that combination (the gate is gone before it next runs), but the cross-repo doctor backstop can.
>
> The canonical-checks Python module (`livespec_dev_tooling.canonical_checks`) lands in `livespec-dev-tooling` per the work-item `li-canon` (epic li-univck Phase 1.2). The `aggregate_completeness` check that powers the in-repo gate lands per the work-item `li-aggchk` (epic li-univck Phase 1.3). The template stamp and the cross-repo doctor invariant land in subsequent phases of the same epic.
>
> Consumer-private checks (checks whose intent is specific to a single consumer per the partition rule above) MAY appear in a consumer's `just check` aggregate after the canonical set, in any order convenient to the consumer. The wiring-completeness invariant applies only to the canonical-set range; consumer-private extensions are unconstrained by it.

### Spec commitments

This PC declares no `spec_commitments.impl_followups[]` — the impl-side work that implements the in-repo gate's mechanical check (`check-aggregate-completeness`) and the canonical-checks Python module is already filed as the sibling work-items `li-canon` and `li-aggchk` against `livespec-dev-tooling` under epic `li-univck`. The template-stamp work-item and the cross-repo doctor-invariant work-item are also filed under the same epic. Cross-references to those work-item IDs appear in the prose for reader convenience but do NOT bind this PC's revise outcome to their landing schedule — the spec commits to the invariant; each consumer adopts the wiring on its own bump-pin cadence.
