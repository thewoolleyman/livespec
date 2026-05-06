---
proposal: proposal-critique-v18.md
decision: accept
revised_at: 2026-04-25T08:30:00Z
author_human: thewoolleyman
author_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v18

## Provenance

- **Proposed change:** `proposal-critique-v18.md` — a
  fast-track single-issue critique surfacing one self-contained
  logical contradiction in v018 §"Self-application": steps 2/4
  and the Q2 bootstrap-exception clause together produce a
  chicken-and-egg in which step 4 must implement
  `propose-change` / `revise` using `propose-change` /
  `revise`, but those sub-commands don't exist when step 4
  begins AND the imperative-landing window has already closed.
- **Revised by:** thewoolleyman (human) in dialogue with
  Claude Opus 4.7 (1M context).
- **Revised at:** 2026-04-25 (UTC).
- **Scope:** v018 `PROPOSAL.md` §"Self-application" only —
  three paragraphs amended (step 2 closing clause, step 4
  verb + scope, Q2 bootstrap-exception trailing acknowledgment
  sentence). No other PROPOSAL.md sections touched. No
  companion docs touched. No `deferred-items.md` entries open
  or close. Plan-side ripple
  (`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`'s Phase 3
  widening + Phase 7 re-narrative + Phase 0 re-freeze at
  v019) is part of this revision cycle's plan-side companion
  edits, applied alongside this revision.

## Pass framing

This pass was a **logical-contradiction critique**, not a
recreatability or integration critique. The finding is
narrow and self-contained: §"Self-application" carries a
three-paragraph contradiction that any literal reader hits
at step 4. Phase 6 of the bootstrap plan would migrate the
contradiction verbatim into `SPECIFICATION/spec.md`,
poisoning the seeded oracle on day one. The fix MUST land in
PROPOSAL.md before the seed.

Q1 accepted at Option A, the recommended disposition.

## Governing principles reinforced

- **Bootstrap exceptions are bounded and narrow.** v018 Q2
  established the bootstrap-exception clause as a ONCE-per-
  repo, ends-at-first-seed carve-out. Option A preserves this
  boundary by widening step 2 (which lives BEFORE the
  exception window closes) rather than extending the
  exception window into step 4.
- **Specify architecture, not mechanism.** The widened step 2
  enumerates WHICH sub-commands need minimum-viable
  implementations; it does NOT prescribe their internal
  composition or factor specific functions. Implementer
  retains mechanism choice within the architecture-level
  constraints already established by
  `python-skill-script-style-requirements.md`.
- **Honor the dogfood discipline strictly.** From the first
  dogfooded cycle onward, every change to spec, code, or
  template content flows through `propose-change` / `revise`.
  Option A makes this discipline mechanically achievable
  without an ambiguous "in-step bootstrap" carve-out.

## Decision: Q1 — Accept Option A

§"Self-application" steps 2, 4, and the Q2 bootstrap-exception
trailing paragraph are amended as follows. The complete amended
text (replacing the v018 originals quoted in the critique) is
codified in v019 PROPOSAL.md.

### Step 2 amended text

```
2. Implement the plugin skeleton: `plugin.json`, per-sub-command
   `SKILL.md` files, the Python package tree under
   `.claude-plugin/scripts/livespec/`, vendored libraries under
   `.claude-plugin/scripts/_vendor/`, `bin/*.py` shebang
   wrappers + `bin/_bootstrap.py`, doctor's static-check modules
   + the static registry at `doctor/static/__init__.py`, the
   minimum subset of the `livespec` template needed to consume
   PROPOSAL.md as seed input, AND minimum-viable
   implementations of `propose-change`, `critique`, and
   `revise` (wrappers + command modules + their schemas /
   dataclasses / validators) sufficient to file the first
   dogfooded change cycle against the seeded `SPECIFICATION/`.
   "Minimum-viable" means: correctness sufficient for the FIRST
   dogfooded cycle (parse a propose-change file, write a
   revision file, cut a new history version, route via
   `--spec-target`), not full-feature parity. Full-feature
   widening of these sub-commands lands in step 4 via
   propose-change/revise cycles against the seed. `prune-
   history` and doctor's LLM-driven phase at the skill layer
   stay out of step 2 — neither is required for the first
   dogfooded cycle.
```

### Step 4 amended text

```
4. **Widen** the minimum-viable sub-commands implemented in
   step 2 (`propose-change`, `critique`, `revise`) to
   full-feature parity (topic canonicalization, reserve-suffix
   discipline, collision disambiguation, single-canonicalization
   invariant routing, full critique-as-internal-delegation
   flow, full revise per-proposal LLM decision flow with
   delegation toggle and rejection audit trail), AND implement
   the remaining sub-commands not present in step 2
   (`prune-history`, doctor's LLM-driven phase at the skill
   layer), all using `propose-change` / `revise` cycles against
   the seeded spec trees. Each cycle targets a specific tree
   via `--spec-target <path>` (default: main spec root).
```

### Q2 bootstrap-exception clause — amended trailing
acknowledgment

The Q2 paragraph's substance stays unchanged. One trailing
sentence is appended to acknowledge the widened step 2:

```
The widened step 2 (v019) places minimum-viable
implementations of `propose-change`, `critique`, and
`revise` BEFORE the seed, inside the imperative window. The
imperative window's closing point (end of step 3, the first
seed) is unmoved by this widening; step 2 retains its
imperative status, and step 4 retains its
governed-loop-mandatory status.
```

### Plan-side companion edits

The bootstrap plan
(`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`) is not part
of the frozen brainstorming set, but is referenced by this
revision and receives ripple edits as part of this revision
cycle:

- **Version basis** updates from v018 to v019 (Phase 0
  freezes at v019; subsequent phases reference v019 as the
  authoritative basis).
- **Phase 3** widens to include minimum-viable
  `propose-change`, `critique`, `revise` implementations
  alongside seed, mirroring v019's step 2 scope. The Phase 3
  exit criterion grows accordingly.
- **Phase 7** re-narrates as pure dogfood (zero imperative
  landings after the seed). The first work item shifts from
  "implement propose-change" to "widen propose-change to
  full feature parity via propose-change/revise cycle
  against the seed."
- **Phase 6** seed scope unchanged (still seeds main +
  sub-specs from PROPOSAL.md + goals-and-non-goals.md +
  per-sub-spec PROPOSAL sections); the §"Self-application"
  text seeded into `SPECIFICATION/spec.md` carries v019's
  amended language, NOT v018's.

These plan-side edits are applied immediately following this
revision.

## Outcome

PROPOSAL.md v019 supersedes v018 with three amended paragraphs
in §"Self-application". No other content changes. The
contradiction at step 2 / step 4 / Q2 is resolved without
weakening the bootstrap-exception boundary or growing the
exception's scope.

`brainstorming/approach-2-nlspec-based/PROPOSAL.md` reflects
v019. The frozen v019 snapshot lives at
`brainstorming/approach-2-nlspec-based/history/v019/`. The v018
snapshot at `history/v018/` is unchanged.
