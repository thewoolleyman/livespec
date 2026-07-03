---
topic: readme-contract
author: claude-opus-4-8
created_at: 2026-07-03T05:30:00Z
---

## Proposal: Add a README contract governing the repo-root entry document

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new `## README contract` section to contracts.md governing the repository's top-level `README.md` as livespec core's human entry document: its purpose, its zero-knowledge-newcomer audience, the required ordered section set a conforming README must carry, and a reference-not-duplicate rule that generalizes the existing single-source rule for the canonical architecture diagram. The section is scoped to livespec CORE's own repo-root README only (it makes no fleet-wide claim on sibling repos). This is the spec-side slice (Slice 1) of the `livespec-127o` README-rewrite epic; Slice 2 (authoring the README to conform) follows once this lands.

### Motivation

The repo-root README grew incrementally (PR #723): it leads with enablement JSONC before explaining what livespec is, fragments setup across three scattered sections, interleaves maintainer machinery with newcomer content, and embeds copies of content whose source of truth is `SPECIFICATION/` (the work-item lifecycle state machine, states, and valves). No contract governs what a conforming README must contain, for whom, in what order — so it drifts on every PR. This section makes the README a governed, spec-driven artifact, mirroring how §"Fleet agent-instruction core" governs the agent-facing entry surface (the README contract is its human-facing peer). Filed from the fleet-followups planning thread (inventory item A / `livespec-127o`), groomed 2026-07-03.

### Proposed Changes

Add the following new `## README contract` section to `SPECIFICATION/contracts.md`, placed adjacent to §"Fleet agent-instruction core" (the human-facing peer of that agent-facing entry-surface contract). This adds exactly one `## ` heading; no other heading is added, renamed, or removed. Because it adds a `## ` heading, the revision that accepts this proposal MUST also add a matching `## README contract` entry to `tests/heading-coverage.json` (carried in the revise payload's `resulting_files[]` as `../tests/heading-coverage.json`; per the v064 pattern the `test` field MAY be a `TODO` placeholder with a `reason` until Slice 2 lands a README-conformance check), or `check-heading-coverage` fails.

The new section text to add:

```markdown
## README contract

The repository's top-level `README.md` is livespec core's **primary human entry
document** — the first artifact a newcomer reads to learn what livespec is, why
it exists, and how to begin. It is a governed self-machinery artifact of this
repo: the human-facing peer of the agent-facing entry surface governed by
§"Fleet agent-instruction core". This contract governs the **repo-root
`README.md` of livespec core only**; it does NOT govern the
`livespec`-template-declared per-spec-tree `README.md` or the skill-owned
`proposed_changes/README.md` / `history/README.md` (separate artifacts governed
by spec.md §"Specification model"), and it makes no fleet-wide claim on sibling
repos' READMEs.

**Audience.** The README MUST be written for a **zero-knowledge newcomer** — a
reader who has never heard of livespec and knows none of its vocabulary (Driver,
orchestrator, Gap/Drift, planes, factory, work-item lifecycle). Every term of art
MUST be defined at first use or immediately linked to its canonical definition.
The README MUST NOT assume prior context, and MUST NOT lead with configuration,
enablement JSONC, or maintainer machinery before the reader understands what
livespec is and why it exists.

**Purpose and scope boundary.** The README answers *what is this*, *who is it
for*, *what does it do*, and *how do I start*, then routes the reader to the
authoritative sources for everything deeper. It is NOT a second specification, a
second install guide, or a second architecture document: normative detail lives
in `SPECIFICATION/`, the full install/onboarding walkthrough in
`docs/installation.md`, and agent orientation in `AGENTS.md`. The README
references these; it MUST NOT restate their content at length.

**Required structure.** A conforming README MUST contain sections covering the
following concerns, in this order, each present and non-empty:

1. **What livespec is** — a plain-language statement of the system and the
   problem it solves, understandable with zero prior context, before any
   configuration or vocabulary.
2. **Newcomer orientation** — a pointer into the canonical lifecycle/overview in
   `spec.md` (referenced, never copied) so a reader sees the whole workflow at a
   glance.
3. **Install / getting started** — the single minimal path to enable livespec on
   a project, deferring the full walkthrough to `docs/installation.md`. This is
   the ONE place newcomer setup is described; setup MUST NOT be scattered across
   multiple sections.
4. **Command surface** — the user-invocable operations (the `/livespec:*`
   sub-commands), each named with a one-line purpose.
5. **Architecture** — a reference to the canonical architecture diagram and its
   contract in `spec.md` §"Contract + reference implementations architecture",
   never an embedded copy of that diagram.
6. **Maintainer / dogfooding** — repo-development entry points (fresh-clone
   bootstrap, dogfooding modes), clearly separated from the newcomer-facing
   sections above so a newcomer is never routed through maintainer machinery.
7. **Further reading** — links to `SPECIFICATION/`, `docs/installation.md`,
   `AGENTS.md`, and `archive/`.

A conforming README MAY add further sections AFTER the required set, but MUST NOT
reorder or omit a required concern, and MUST NOT interleave maintainer-facing
material into the newcomer-facing sections.

**Reference-not-duplicate.** The README is a routing document, not a mirror. For
any artifact with a canonical home elsewhere in the repo, the README MUST
**reference** that home rather than embed a copy — generalizing the existing
single-source rule for the canonical architecture diagram in spec.md §"Contract +
reference implementations architecture" (the README references that diagram,
never embeds a second copy). In particular the README MUST NOT reproduce: the
architecture diagram (canonical in `spec.md`), the work-item-lifecycle state
machine or its states/valves as normative content (canonical in
`SPECIFICATION/`), the full install walkthrough (canonical in
`docs/installation.md`), or any normative rule stated in `SPECIFICATION/`. Where
such content aids a newcomer, the README summarizes it at newcomer altitude in
its own words and links to the canonical source, so no second copy can rot or
drift. The README MAY embed original content that has no other canonical home (a
newcomer-oriented framing, or a diagram that exists nowhere else) — exactly as
the diagram rule permits the README to carry non-architecture diagrams.
```
