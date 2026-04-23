---
topic: proposal-critique-v14
author: GPT-5 Codex
created_at: 2026-04-23T09:08:56Z
---

# Proposal-critique v14

A recreatability-and-cross-doc-consistency critique pass over v014
`PROPOSAL.md`, with targeted checks against
`deferred-items.md` and
`python-skill-script-style-requirements.md`.

The critique is grounded in the recreatability test: could a
competent implementer, reading the current brainstorming docs alone,
produce the v015 proposal without being forced to guess between
conflicting rules?

Findings in this pass:

- **Major gaps (2 items):** O1-O2
- **Significant gaps (2 items):** O3-O4

## Proposal: O1 — Template-agnostic v014 still hardcodes `SPECIFICATION/` operational paths

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: malformation (self-contradiction).**

v014 explicitly broadened the model from the built-in multi-file
`livespec` template to two built-ins, including the repo-root
`minimal` template with `spec_root: "./"` and root-level
`proposed_changes/` plus `history/` directories
(PROPOSAL.md lines 827-857). But several later, supposedly generic
sub-command sections still hardcode the old
`SPECIFICATION/...` paths:

- `propose-change` says it creates
  `SPECIFICATION/proposed_changes/<topic>.md`
  (lines 1534-1536).
- `revise` says processed proposals are moved
  from `SPECIFICATION/proposed_changes/` and that the directory
  must be empty afterward (lines 1760-1768).
- The seed-input JSON example still shows
  `SPECIFICATION/spec.md` as the canonical emitted path
  (lines 1441-1450), even though v014 now says the active
  template controls placement.

Those rules cannot all be true at once. Under `minimal`,
`proposed_changes/` and `history/` live at repo root, not under
`SPECIFICATION/`. An implementer following the path-parameterized
minimal-template section and an implementer following the later
sub-command sections would build incompatible filesystem behavior.

### Motivation

This is the largest current recreatability blocker because it
affects the core lifecycle surfaces, not just examples. The NLSpec
guidance in `livespec-nlspec-spec.md` requires explicit defaults
and unambiguous interfaces; here the interface for where
proposals/history live depends on which section the implementer
trusts.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** make every operational path in the
generic sub-command sections explicitly template-parameterized via
`<spec-root>/...` or equivalent prose ("under the active template's
spec root"), and move concrete `SPECIFICATION/...` examples into
`livespec`-template-only subsections. This preserves v014's
template-agnostic architecture cleanly.

**Option B:** keep the current generic prose but add a global rule
that unqualified `SPECIFICATION/...` examples in sub-command
sections are illustrative aliases for "the active template's
spec-root-relative path". This is smaller, but it asks readers to
mentally reinterpret literal paths.

**Option C:** retreat from full v014 template-agnosticity for
proposal/history placement and say v1 operational flows are only
fully specified for the `livespec` template; `minimal` becomes a
special-case demo template. This resolves the contradiction by
narrowing scope, but it discards one of v014's main additions.

---

## Proposal: O2 — Seed's generic `history/v001` snapshot rule still requires a per-version README that `minimal` explicitly forbids

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`

### Summary

**Failure mode: malformation (self-contradiction).**

The `minimal` template section states, unambiguously, that there is
**no per-version `README.md` in `history/vNNN/` for minimal**
(lines 859-863). But the generic `seed` section later says
`bin/seed.py` creates `history/v001/` including **a `README.md`
copy** (lines 1461-1465).

These are mutually exclusive for `minimal`:

- one rule says `history/v001/README.md` must exist;
- the other says no such file exists for any version under the
  minimal template.

Because the contradiction is in normative prose, an implementer
cannot resolve it by treating one side as a mere example.

### Motivation

This is a pure recreatability defect. A competent implementer
cannot know whether the seed wrapper snapshots only
template-declared files for `minimal`, or whether it invents a
synthetic per-version README despite the explicit contrary rule.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** parameterize the generic seed-history
copy rule by active template contents: seed snapshots the active
spec files plus the standard `proposed_changes/` subdir, and a
per-version README is copied only for templates that actually have
one as part of their versioned spec surface. For `minimal`, no
`history/v001/README.md` is written.

**Option B:** keep the generic seed rule as-is and change the
`minimal` section to allow a synthetic `history/vNNN/README.md`
written by livespec even though the live template has no separate
README. This restores uniformity at the cost of adding a file that
the current minimal-template section says does not exist.

**Option C:** keep "no per-version README" for minimal, but treat
the seed-section `README.md` language as a non-normative example.
This is the weakest repair because the current sentence is written
as required wrapper behavior, not example prose.

---

## Proposal: O3 — `critique` does not specify whether its generated topic/front-matter use the raw author string or the slugged form

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: ambiguity.**

The proposed-change file format requires file-level front-matter
`topic: <kebab-case-topic>` (lines 2188-2196). v014 N5 then adds
an author-to-slug transformation for cases where the resolved
author is used as a filename component (lines 1570-1587). But the
`critique` sub-command says two subtly different things:

- the resolved author is used as the topic suffix
  (lines 1656-1658),
- internal delegation calls `propose_change` with topic
  `<resolved-author>-critique` (lines 1659-1661),
- collision handling is described against the slugged filename
  `<resolved-author-slug>-critique.md`
  (lines 1665-1672).

If the author is something like `Claude Opus 4.7 (1M context)`,
three plausible implementations emerge:

- raw topic in front-matter and internal logic, slug only for the
  final filename;
- slugged topic everywhere;
- raw topic passed into `propose_change`, which itself must then
  normalize the topic before both front-matter and write-path.

Those produce different front-matter `topic` values and possibly
different collision behavior. The current text does not choose.

### Motivation

This is exactly the kind of accidental ambiguity the NLSpec
guidelines warn against: the surface looks specified, but the
important normalization step is underspecified at the point where
it affects an externally visible artifact.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** codify that `critique` derives the
topic as `<resolved-author-slug>-critique` before delegating to
`propose_change`, and that the same slugged string is used for the
filename topic, the front-matter `topic`, and collision lookup.
The original unslugged author remains only in the `author` field.

**Option B:** allow `critique` to keep an internal raw topic, but
explicitly define a second normalization stage in
`propose_change`: any incoming topic is converted to kebab-case
before file write and front-matter population. This is coherent,
but it broadens `propose_change`'s responsibilities.

**Option C:** relax the proposed-change front-matter format so
`topic` is no longer required to be kebab-case. This would remove
the contradiction, but it weakens a previously crisp filename and
artifact identity rule.

---

## Proposal: O4 — The real-tier E2E retry-on-exit-4 test has no deterministic trigger

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness.**

v014 makes the E2E harness REQUIRED and says both mock and real
tiers share the same pytest suite (PROPOSAL.md lines 2498-2530).
It also requires an explicit retry-on-exit-4 error-path test
(lines 2551-2555). But the deferred implementation entry fills in
the real-tier trigger as:

- mock tier: a specific delimiter directive triggers a
  schema-invalid payload;
- real tier: it "relies on LLM nondeterminism to occasionally
  trigger" the same failure mode
  (`deferred-items.md` lines 1351-1355).

That is not a recreatable acceptance criterion. A required test
cannot depend on the model happening to make a mistake. One
implementer may ship a flaky real-tier test; another may silently
skip the retry assertion in real mode; another may invent a
completely separate deterministic injection path. All three claim
to satisfy the current text.

### Motivation

The whole point of N9 was to add top-of-pyramid integration
coverage. Leaving one of the named required error-path tests
dependent on accidental model misbehavior breaks the "testable
acceptance criteria" property the NLSpec document demands.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** require a deterministic, harness-owned
trigger for exit-4 in BOTH tiers. For example, the E2E harness can
inject a first-attempt malformed payload through a test-only hook
or a prompt-mode directive that both the mock and real harness
honor. The real LLM still runs, but the failure trigger is no
longer accidental.

**Option B:** keep the real tier fully live, but narrow the
required shared suite: `test_retry_on_exit_4` is mandatory in mock
mode only, while real mode runs only happy-path + doctor-fix +
prune-no-op. This reduces scope but abandons the "same pytest
suite covers both tiers" claim.

**Option C:** keep the shared suite claim and keep the current
real-tier behavior, explicitly accepting flakiness for this one
test. This is implementable, but it formalizes a weak acceptance
criterion.
