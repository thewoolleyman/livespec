---
proposal: proposal-critique-v14.md
decision: modify
revised_at: 2026-04-23T09:55:54Z
author_human: thewoolleyman
author_llm: GPT-5 Codex
---

# Revision: proposal-critique-v14

## Provenance

- **Proposed change:** `proposal-critique-v14.md` — a
  recreatability-and-cross-doc-consistency critique over v014
  focused on four items:
  - O1: template-agnostic lifecycle prose still hardcoded old
    `SPECIFICATION/...` paths.
  - O2: seed's generic `history/v001` snapshot rule still
    contradicted `minimal`'s explicit "no per-version README"
    rule.
  - O3: topic canonicalization ownership was under-specified
    between direct `propose-change` and `critique`'s internal
    delegation.
  - O4: retry semantics and the E2E retry-path requirement were
    over-specified in one place, under-specified in another, and
    operationally flaky in the real tier.
- **Revised by:** thewoolleyman (human) in dialogue with GPT-5
  Codex.
- **Revised at:** 2026-04-23 (UTC).
- **Scope:** v014 `PROPOSAL.md` + `deferred-items.md` +
  `python-skill-script-style-requirements.md` → v015 equivalents.
  `livespec-nlspec-spec.md`, `goals-and-non-goals.md`,
  `prior-art.md`, `subdomains-and-unsolved-routing.md`, and the
  2026-04-19 lifecycle/terminology companion docs remain
  unchanged.

## Pass framing

This pass was a **recreatability-and-cross-doc-consistency**
critique. The accepted changes preserve earlier structural
decisions rather than reopening them:

- **O1** preserves v009 I7 `spec_root` parameterization and v014
  N1's introduction of the `minimal` built-in template by
  parameterizing generic lifecycle paths as `<spec-root>/...`
  instead of walking back template-agnosticity.
- **O2** preserves `minimal`'s explicit versioned shape and fixes
  stale generic seed wording rather than inventing synthetic
  per-version README files.
- **O3** preserves the kebab-case artifact identity invariant
  while moving topic canonicalization to the deterministic
  `propose-change` wrapper boundary, making direct callers and
  internal delegates converge on one rule.
- **O4** preserves v010 J4's exit-4-vs-exit-3 distinction, but
  removes the fake precision of a hardcoded retry budget.
  Retry remains a skill/prompt orchestration responsibility keyed
  off return codes, and the E2E retry-path test becomes
  deterministic mock-only coverage rather than flaky real-tier
  wishful thinking.

## Summary of dispositions

| Item | Failure mode | Disposition |
|---|---|---|
| O1 | malformation | Accept A — generic operational paths are parameterized as `<spec-root>/...`; literal `SPECIFICATION/...` paths remain only in `livespec`-template-specific sections or illustrative examples labeled as such |
| O2 | malformation | Accept A — seed/history snapshot wording is template-aware; per-version README copies exist only for templates whose versioned surface defines one; `minimal` gets none |
| O3 | ambiguity | Accept B — `propose-change` centrally canonicalizes inbound topic hints and uses the canonicalized topic for filename, front-matter `topic`, and collision namespace; `critique` passes a raw author-derived topic hint into that shared rule |
| O4 | incompleteness | Accept modified B — remove exact retry-count requirements; keep exit `4` as the malformed-payload signal; SKILL/prompt orchestration SHOULD retry based on return codes; deterministic retry-path E2E coverage is mock-only and skipped in real mode via pytest markers / `skipif` |

## Governing principles reinforced

- **Template-governed structure stays real.** O1 and O2 both
  reinforce that templates define on-disk placement and versioned
  surfaces; generic lifecycle prose must not smuggle the old
  single-template layout back in.
- **Deterministic shaping belongs in wrappers.** O3 treats topic
  canonicalization like author-derived slugging: one central,
  deterministic rule at the wrapper boundary, not prompt-local
  hygiene duplicated across callers.
- **Return codes are the orchestration seam.** O4 keeps the
  wrapper single-shot and deterministic. Prompt/skill retry uses
  exit-code interpretation rather than wrapper-internal retry
  loops or a hardcoded global attempt counter.
- **Real E2E should validate real contracts, not random model
  mistakes.** The real tier stays valuable for happy-path and
  state-transition coverage; the deterministic schema-malformed
  retry-path test moves to mock-only coverage where it is
  actually reproducible.

## Disposition by item

### O1. Generic lifecycle paths still hardcoded `SPECIFICATION/...` (malformation → accepted, option A)

Accepted as proposed.

The accepted repair parameterizes every generic operational path as
`<spec-root>/...` (or equivalent prose naming the active
template's spec root) and leaves literal `SPECIFICATION/...`
examples only in `livespec`-template-specific sections or in
examples explicitly labeled as representative for that template.

Applied consequences:

- `doctor`'s `allowed-tools` guidance now names
  `<spec-root>/proposed_changes/` and `<spec-root>/history/`.
- Generic `propose-change`, `revise`, `versioning`,
  `prune-history`, `revision-file-format`, and doctor-output
  example paths are parameterized.
- Bare generic `history/vN/` and `proposed_changes/` references
  were swept for path-root ambiguity.

### O2. Seed snapshot wording still required a per-version README that `minimal` forbids (malformation → accepted, option A)

Accepted as proposed.

The generic seed rule now says seed snapshots the active
template's versioned surface, including a per-version README only
for templates that actually define one. For the built-in
`minimal` template, no `history/v001/README.md` is written.

This keeps the template boundary clean and preserves v014 N1's
explicit minimal-template structure rather than inventing a
synthetic file.

### O3. Topic canonicalization ownership was under-specified (ambiguity → accepted, option B)

Accepted as **user-supplied direction** after interview
clarification.

The critique originally framed this as mostly a `critique`
topic-suffix issue. During interview, the user correctly pushed
the broader question: what happens when `propose-change` is
called directly with a non-kebab-case topic? That widened the
item from a `critique`-local ambiguity to a wrapper-boundary
contract issue.

Final disposition:

- `bin/propose_change.py` treats inbound `<topic>` as a
  user-facing topic hint.
- The wrapper canonicalizes it centrally before filename write,
  front-matter `topic`, or collision lookup.
- `critique` passes raw `<resolved-author>-critique` topic hints
  into that shared canonicalization rule.
- Empty-after-canonicalization is a `UsageError` (exit 2), not a
  silent fallback.

This is more user-friendly than strict rejection and more robust
than prompt-owned slugification.

### O4. Retry semantics and retry-path E2E coverage were over-specified and operationally weak (incompleteness → accepted, modified B)

Accepted in the reshaped form discussed during interview.

The accepted disposition is:

1. Remove exact retry-count requirements (`2 retries`, `3 attempts
   total`) from the working docs.
2. Keep exit `4` as the machine-readable malformed-payload signal
   distinct from exit `3`.
3. Specify that SKILL/prompt orchestration SHOULD inspect return
   codes and SHOULD retry on exit `4` by re-invoking the relevant
   template prompt with error context.
4. Leave the exact retry count intentionally unspecified in v1.
5. Keep deterministic retry-path E2E coverage in the mock tier
   only: first malformed, second well-formed, exactly one retry.
6. Keep a common pytest suite, but annotate mock-only retry-path
   coverage with pytest markers / `skipif` so the real tier skips
   it.

This preserves the useful exit-code distinction while removing the
under-specified retry counter and the flaky real-tier retry-path
expectation.

## Deferred-items inventory (carried forward + scope-widened + new)

Per the deferred-items discipline, every carried-forward item is
enumerated below.

**Carried forward unchanged from v014:**

- `python-style-doc-into-constraints`
- `returns-pyright-plugin-disposition`
- `claude-md-prose`
- `basedpyright-vs-pyright`
- `user-hosted-custom-templates`
- `companion-docs-mapping`
- `front-matter-parser`
- `enforcement-check-scripts`
- `wrapper-input-schemas`
- `local-bundled-model-e2e`

**Scope-widened in v015:**

- `template-prompt-authoring`
  O4: prompt authoring now needs to describe return-code-driven
  retry behavior without baking in a fixed retry count.
- `static-check-semantics`
  O3: author-derived topic-hint handling clarified; new central
  `propose-change` topic-canonicalization rule added.
- `skill-md-prose-authoring`
  O3/O4: SKILL.md bodies must describe central
  topic-canonicalization ownership and return-code-driven retry
  semantics without hardcoded attempt counts.
- `end-to-end-integration-test`
  O4: retry-on-exit-4 becomes deterministic mock-only coverage;
  real mode skips via pytest markers / `skipif`.

**New in v015:**

None.

**Removed in v015:**

None.

## Self-consistency check

Post-apply invariants rechecked against the working docs:

- Generic lifecycle prose now consistently parameterizes
  operational paths by `<spec-root>/...` in the sub-command,
  versioning, pruning, revision-format, and doctor-output
  example sections.
- The built-in `minimal` template still explicitly has no
  per-version README, and seed/revise generic wording now matches
  that rule.
- `propose-change` now owns canonical topic derivation; the file
  format's `topic: <kebab-case-topic>` rule and `critique`'s
  internal delegation text both align to that ownership.
- Exit `4` remains the retryable malformed-payload signal across
  PROPOSAL.md, the style doc, and deferred implementation notes,
  but no working doc now claims a fixed retry budget.
- E2E docs now agree that retry-path determinism is mock-only and
  that the real tier skips that scenario via pytest
  markers/`skipif`.

Follow-up review passes after the initial apply phase:

- **Careful-review pass 1** caught additional O1 path drift:
  generic lifecycle prose outside the sub-command sections still
  had stale hardcoded operational paths that needed to be
  parameterized.
- **Careful-review pass 2** caught 5 more stale generic-path
  references: `Versioning`, `Pruning history`, `Revision file
  format`, the doctor output example, and the self-application
  seed path still needed `<spec-root>/...` or explicit
  `livespec`-template scoping.
- **Careful-review pass 3** landed no additional load-bearing
  fixes.
- **Dedicated deferred-items-consistency pass** found no
  additional drift beyond the working-doc edits already applied
  for O3 and O4.

## Outstanding follow-ups

Tracked in the updated `deferred-items.md`.

The v015 pass touched 4 existing entries with scope-widenings:

- `template-prompt-authoring`
- `static-check-semantics`
- `skill-md-prose-authoring`
- `end-to-end-integration-test`

No new deferred items were added and none were removed.

## What was rejected

No item was rejected outright.

- O1 option B was rejected because it would preserve literal
  `SPECIFICATION/...` wording and ask readers to reinterpret it
  mentally.
- O1 option C was rejected because it would effectively demote
  `minimal` from a real v1 built-in to a quasi-demo template.
- O2 option B was rejected because it would invent a synthetic
  versioned README that the `minimal` section explicitly says does
  not exist.
- O3 option A was rejected after interview clarification because
  strict pre-slugification is less user-friendly than shared
  canonicalization at the wrapper boundary.
- O4 original option A was rejected because it over-constrained
  the mechanism; deterministic retry-path coverage is valuable,
  but only in the mock tier where it is actually reproducible.
