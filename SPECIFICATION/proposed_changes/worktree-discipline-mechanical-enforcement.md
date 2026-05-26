---
topic: worktree-discipline-mechanical-enforcement
author: claude-opus-4-7
created_at: 2026-05-26T08:00:00Z
---

## Proposal: mandate-bare-flag-on-livespec-governed-primary-checkouts

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a paragraph to `non-functional-requirements.md` §"Workflow
discipline — spec-side changes" (the v079-ratified section) that
mandates `core.bare = true` MUST be set in `.git/config` on every
livespec-governed primary checkout (this repo and every sibling-repo
`SPECIFICATION/` host). The bare-flag is the **mechanical**
enforcement of the v079 worktree-only discipline; without it, the
discipline is enforceable only by author-vigilance plus post-edit
detection. The bare-flag makes the violation impossible at the git
layer — `git pull`, `git checkout`, `git merge`, and any other
working-tree command refuses to run against a bare-flagged checkout,
so the user is structurally forced into `git worktree add` for any
edit. Pairs with the bootstrap step (sibling proposal) and the
doctor static check (sibling proposal) to form a complete enforcement
loop.

### Motivation

v079's prose codifies the worktree → PR → merge → cleanup discipline
but does NOT name a mechanical enforcement mechanism. The non-functional-
requirements.md text says only "A future doctor invariant SHOULD detect
master-direct uncommitted spec-tree edits as a `warn` finding" — a
post-edit detection check that fires only when doctor is invoked. That
gap leaves four concrete failure modes uncovered:

1. **Author forgets to use a worktree** and edits `SPECIFICATION/spec.md`
   directly on master. Doctor would catch the snapshot mismatch via the
   existing `out-of-band-edits` check on the next run — but the next run
   might be days away, and the audit trail is already polluted.
2. **Multiple in-flight branches** force checkout-switching on the
   primary worktree, which interacts poorly with the rebase-merge-only
   master rule when stashes / WIP state accumulate.
3. **Tooling that assumes `git pull` works** (CI helpers, IDE plugins,
   `gh pr checkout`, etc.) writes back to the primary checkout in ways
   that bypass the worktree discipline silently.
4. **The discipline is invisible to new contributors / fresh clones.**
   A fresh `git clone` is `core.bare = false` by default; the workflow
   rule applies but the mechanical safety belt does not.

The bare-flag enforcement closes (1) and (3) at the git layer
immediately, structurally improves (2) by making per-branch worktrees
the only edit surface, and — paired with the bootstrap-step sibling
proposal — applies to (4) on every clone uniformly.

A counterargument might be that the bare-flag is "too blunt" — it
prevents all direct master edits, not just spec-tree edits. But
livespec-governed repos already enforce rebase-merge-only master (v053
or thereabouts), which means every change in those repos already flows
through a feature branch. Whether that feature branch is materialized
via `git checkout -b` or `git worktree add -b` is a small ergonomic
difference, not a discipline difference. The bare-flag's whole-repo
scope happens to match the already-existing branching discipline; the
marginal friction is small.

### Proposed Changes

Append the following paragraph to `non-functional-requirements.md`
§"Workflow discipline — spec-side changes", immediately after the
existing line 746 paragraph that mentions the future doctor invariant:

> **Bare-flag enforcement.** Every livespec-governed primary checkout
> MUST have `core.bare = true` set in `.git/config`. The bare-flag is
> the mechanical enforcement of the worktree-only discipline above:
> with the flag set, `git pull`, `git checkout`, `git merge`, and
> other working-tree commands refuse to run against the primary
> checkout, forcing every edit through `git worktree add`. The
> bare-flag pairs with two companion mechanisms: a bootstrap step
> (see §"Bare-flag bootstrap procedure" below) that idempotently
> applies the flag on fresh clones, and the `primary-checkout-bare-flag-set`
> doctor static invariant (see `contracts.md` §"Doctor cross-boundary
> invariants") that verifies the flag is set on every doctor run. Per-clone
> non-bare state is the failure mode the bootstrap step addresses; user-
> tampering or pre-bootstrap clones are the failure mode the doctor
> invariant addresses. Together the three (NFR rule, bootstrap step,
> doctor invariant) make the workflow discipline structurally
> enforceable rather than author-vigilance-dependent.


## Proposal: document-bootstrap-step-for-bare-flag-application

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new subsection §"Bare-flag bootstrap procedure" to
`non-functional-requirements.md` immediately after §"Workflow
discipline — spec-side changes". The bootstrap step is the
idempotent mechanism that applies `core.bare = true` on every clone of
every livespec-governed repo, closing the per-clone-config-state hole
that would otherwise make the bare-flag mandate (sibling proposal) a
one-workstation hack. The bootstrap MUST be reachable via a single
documented entry point (e.g., a `just bootstrap` target, a setup
skill, or a clone-time hook) per repo; the exact mechanism is
implementation choice, but the contract is that running it on a fresh
clone leaves `core.bare = true` set and is safe to re-run.

### Motivation

`core.bare = true` lives in per-clone `.git/config` and does NOT flow
through `git clone`, `git fetch`, or `git push`. A fresh clone of any
livespec-governed repo gets `core.bare = false` by default, regardless
of what state the upstream's primary checkout is in. The mandate in
the sibling `mandate-bare-flag-on-livespec-governed-primary-checkouts`
proposal would therefore be a one-workstation hack unless a per-clone
mechanism exists to apply the flag automatically.

The bootstrap step closes that gap. By documenting that every
livespec-governed repo MUST surface an idempotent bootstrap command,
and by tying doctor's bare-flag-verifying invariant to the existence of
that command's effect, fresh clones become first-class participants in
the discipline.

The bootstrap step is also the natural home for any future per-clone
setup the discipline accumulates (lefthook installation, mise tool
provisioning, etc.). Defining the bootstrap-step contract now is
forward-compatible.

### Proposed Changes

Insert the following new subsection in
`SPECIFICATION/non-functional-requirements.md`, immediately after the
existing §"Workflow discipline — spec-side changes" (i.e., before the
existing §"Project-local plugin layout" at line 748):

> ### Bare-flag bootstrap procedure
>
> Every livespec-governed repository MUST surface an idempotent
> bootstrap entry point that, when invoked, sets `core.bare = true` in
> the primary checkout's `.git/config`. The exact entry point shape is
> implementation choice (a `just bootstrap` target, a livespec-managed
> setup skill, a hook chained into clone-time tooling, etc.); the
> contract is that:
>
> 1. The entry point MUST be documented in the repo's `README.md`,
>    `CLAUDE.md`, or equivalent first-touch-discovery surface.
> 2. Running the entry point on a fresh clone MUST result in
>    `core.bare = true` being set, equivalent to invoking
>    `git config core.bare true` against the primary checkout.
> 3. Running the entry point again on a checkout that already has the
>    flag set MUST be a no-op (idempotent; no error, no side-effect).
> 4. The entry point MAY perform other clone-time setup (lefthook
>    installation, dependency installation, mise tool resolution) as
>    long as the bare-flag step is uncoupled from the rest (a partial
>    failure in another setup step MUST NOT leave the bare-flag unset).
>
> The bootstrap step is what makes the sibling `core.bare = true`
> mandate enforceable across clones rather than constituting a single-
> workstation hack. Doctor's `primary-checkout-bare-flag-set`
> invariant (see `contracts.md` §"Doctor cross-boundary invariants")
> verifies the flag's presence; the bootstrap step is the mechanism by
> which a user resolves a doctor `fail` finding on that invariant.


## Proposal: add-primary-checkout-bare-flag-set-doctor-invariant

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new `primary-checkout-bare-flag-set` doctor static invariant to
`contracts.md` §"Doctor cross-boundary invariants". The invariant reads
`<project-root>/.git/config` on the primary checkout and fires `fail`
when `core.bare != true`. The narration points the user at the
bootstrap step defined by §"Bare-flag bootstrap procedure" (sibling
proposal). Without this invariant, the sibling bare-flag mandate is
unenforceable on doctor invocations — a user could clone fresh, never
run the bootstrap, and never get caught.

### Motivation

`core.bare = true` is per-clone local config and is invisible to the
remote. The only way to verify the workflow-discipline mandate
mechanically across clones is to check the config at doctor time. The
existing doctor static check pool covers the CLEANUP side of the
worktree discipline (the three impl-side cleanup invariants under
§"Impl-side cleanup invariants (cross-boundary)") but lacks any check
on the PRESCRIPTIVE side (every edit STARTS in a worktree). This
invariant closes that asymmetry.

The check is trivial to implement (read `.git/config`, parse for
`[core] bare = true`, fire if absent or `false`). It fits the existing
static-check shape and slots naturally between `no-stale-worktree` and
the workflow-discipline cleanup invariants.

### Proposed Changes

Insert a new subsection in `SPECIFICATION/contracts.md` §"Doctor
cross-boundary invariants" immediately after the existing
`### depends_on-ref-wellformedness` subsection (current line 136):

> ### `primary-checkout-bare-flag-set`
>
> Every livespec-governed primary checkout MUST have `core.bare = true`
> set in its `.git/config`. The check reads `<project-root>/.git/config`,
> parses the `[core] bare` entry, and fires `fail` when the value is
> absent or set to `false`. The narration directs the user to invoke
> the repo's documented bootstrap step (per
> `non-functional-requirements.md` §"Bare-flag bootstrap procedure"),
> which idempotently applies the flag.
>
> The invariant is structural per the catalogue's intro principles
> (binary, contract-level, mechanically checkable); the bare-flag is
> either set or it isn't. The check MUST NOT distinguish between
> "bare = false explicitly" and "bare key absent" — both fire equally;
> both are corrected by the same bootstrap invocation.
>
> The check applies to the primary checkout only. Secondary worktrees
> (per `git worktree list`) MUST NOT carry `core.bare = true` — that
> would prevent normal work in the worktree. The invariant reads only
> the primary `.git/config`; the standalone `.git` files inside
> worktrees are not inspected.
>
> Fresh clones that have not yet had the bootstrap step run fail this
> invariant immediately. This is intentional: the failure is the
> mechanism by which a fresh contributor discovers the discipline. The
> narration includes the corrective bootstrap command verbatim so the
> resolution path is one terminal invocation away.


## Proposal: add-master-direct-uncommitted-spec-edits-doctor-invariant

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add the `master-direct-uncommitted-spec-edits` doctor static invariant
that v079 explicitly anticipated ("A future doctor invariant SHOULD
detect master-direct uncommitted spec-tree edits as a `warn` finding"
— `non-functional-requirements.md:746`). The invariant fires `warn`
when the primary worktree has uncommitted modifications under
`<spec-root>/` AND the primary worktree's HEAD points at the default
branch (`master`). Belt-and-suspenders for the rare edge cases the
bare-flag enforcement (sibling proposals) cannot physically prevent —
specifically, a user who runs `git worktree add /tmp/somepath master`
and edits in that secondary worktree, bypassing the bare-flag
constraint on the primary checkout.

### Motivation

The v079-ratified rule prose mentions this exact follow-up at line 746.
Filing it now closes the unfiled-commitment that v079 itself left
behind (the same class of silent-drop the upstream sibling propose-
change `spec-impl-commitment-tracking` is also trying to systemically
prevent — this propose-change is in fact a concrete worked example of
the pattern, by addressing one such unfiled commitment).

The bare-flag enforcement (sibling proposals) handles the common case:
the user cannot edit on the primary checkout because git refuses.
However, the bare-flag does NOT prevent every possible bypass:

- `git worktree add /some/path master` creates a secondary worktree
  checked out to `master`. Edits in that secondary worktree are on
  master, bypass the worktree-PR-merge cycle, and are invisible to the
  bare-flag check.
- Some IDE workflows or future tooling MAY synthesize transient master
  worktrees that the user doesn't directly see.

The `master-direct-uncommitted-spec-edits` invariant catches both. It
runs as a structural static check, not at edit time, but as long as
doctor is invoked before the edit gets pushed, the check surfaces the
violation.

### Proposed Changes

Insert a new subsection in `SPECIFICATION/contracts.md` §"Doctor
cross-boundary invariants" immediately after the
`### primary-checkout-bare-flag-set` subsection (proposed in the
sibling section above):

> ### `master-direct-uncommitted-spec-edits`
>
> Every worktree (primary or secondary, per `git worktree list
> --porcelain`) whose HEAD points at the default branch MUST NOT
> carry uncommitted modifications under `<spec-root>/`. The check
> enumerates every worktree, identifies the subset whose HEAD is the
> default branch (typically `master`), and for each invokes
> `git status --porcelain` scoped to `<spec-root>/`. Any non-empty
> output fires `warn` with corrective action narration that:
>
> 1. Names the offending worktree path.
> 2. Names the modified files under `<spec-root>/`.
> 3. Directs the user to commit-into-a-feature-branch
>    (`git checkout -b <branch>` then commit) per the workflow
>    discipline, OR to discard the edits if they were unintentional
>    (`git checkout -- <files>`).
>
> The check fires `warn` (not `fail`) consistent with the v079 prose at
> `non-functional-requirements.md:746` ("a `warn` finding"). Spec
> edits on master are a discipline violation, but the violating commit
> is not yet pushed — the warning gives the user time to recover.
>
> The check covers the secondary-worktree-on-master bypass that the
> sibling `primary-checkout-bare-flag-set` invariant cannot
> physically prevent (the bare-flag is scoped to the primary checkout
> only; secondary worktrees on master are still possible via
> `git worktree add /path master`). The two checks together close the
> enforcement loop.
>
> Committed-and-then-discovered violations (the user committed on
> master and now the commit needs to be moved) are out of scope for
> this invariant; the existing `out-of-band-edits` check surfaces those
> via the snapshot-mismatch invariant.


## Impl-side follow-ups (filed as work-items, not spec changes)

The three implementation tasks below MUST be filed in the active
impl-plugin's store once these spec changes are revised in:

### Work-item: implement-bare-flag-bootstrap-step

Implement the bootstrap entry point per §"Bare-flag bootstrap
procedure". The natural shape is a `just bootstrap` target (or
`.claude/skills/bootstrap/SKILL.md`) that runs `git config core.bare
true` against `<project-root>/.git/config`, idempotently. Document the
entry point in `README.md` and `CLAUDE.md`.

### Work-item: implement-primary-checkout-bare-flag-set-doctor-static-check

Write the static check at
`.claude-plugin/scripts/livespec/doctor/static/primary_checkout_bare_flag_set.py`
following the existing static-check shape (the same module pattern as
`no_stale_worktree.py`). Register the check in the doctor static
registry. Add unit tests.

### Work-item: implement-master-direct-uncommitted-spec-edits-doctor-static-check

Write the static check at
`.claude-plugin/scripts/livespec/doctor/static/master_direct_uncommitted_spec_edits.py`
following the same shape. The check enumerates worktrees via
`git worktree list --porcelain`, identifies the subset on the default
branch, runs `git status --porcelain <spec-root>/` against each, and
emits a `warn` finding per non-empty result. Register and test.

**Forward-pointer.** If the sibling upstream proposed-change
`spec-impl-commitment-tracking` (introducing the `spec_commitments`
front-matter field and the `unresolved-spec-commitment` doctor
invariant) is revised in BEFORE this propose-change is revised in,
the three impl follow-ups above SHOULD be re-declared as structured
`spec_commitments.impl_followups[]` entries in this file's YAML
front-matter at revise time, so the work-items are mechanically
tracked rather than prose-only. The meta-irony — that this propose-
change itself is subject to the silent-drop risk that the sibling
propose-change exists to fix — is intentional and acknowledged.
