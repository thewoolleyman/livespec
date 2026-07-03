# research/spec-ready/

Distilled, spec-ready versions of the active research synthesis
docs. The originals (in `research/architecture/` and
`research/workflow-processes/`) are research artifacts that retain
historical framing — dates, status callouts, "what changed since
X" tables, "things to sit with" sections, decision-callout boxes,
research-conversational asides. The versions here have that
chrome stripped so the content reads as direct spec material,
ready to flow through `/livespec:propose-change` →
`/livespec:revise` into `SPECIFICATION/`.

## Files

- [`tool-agnostic-workflow.md`](./tool-agnostic-workflow.md) — the
  generic spec ↔ implementation pattern with domain terminology
  not bound to LiveSpec. Intended landing place in SPECIFICATION/:
  introductory sections of `spec.md`. Cross-references the
  diagram at
  [`../workflow-processes/diagrams/tool-agnostic-workflow.svg`](../workflow-processes/diagrams/tool-agnostic-workflow.svg).
- [`livespec-architecture.md`](./livespec-architecture.md) — the
  LiveSpec-specific instantiation of that pattern: plugin
  catalog, skill surfaces, `.livespec.jsonc` shape, marketplace
  install flow, dogfooding choice. Intended landing places:
  `SPECIFICATION/contracts.md` (impl-plugin contract, Spec Reader
  required capabilities, `.livespec.jsonc` schema rules) and
  `SPECIFICATION/non-functional-requirements.md` (multi-repo
  distribution, plaintext-dogfood choice, shared-content sync).
- [`multi-repo-implementation-providers.md`](./multi-repo-implementation-providers.md)
  — the architectural shape of the multi-repo decision: topology,
  dependency direction, contract-vs-dogfooding distinction,
  bootstrap considerations. Intended landing place:
  `SPECIFICATION/non-functional-requirements.md` §"Plugin
  distribution".

## What is NOT included

- **Conversation transcripts** (`research/workflow-processes/
  conversation-transcript.html`) — verbatim source records of the
  brainstorm. Useful as audit trail, not spec material.
- **Beads workaround catalogue** (`research/beads/
  beads-gaps-workarounds.md`) — upstream bug catalogue intended
  for filing upstream, explicitly non-spec per its own
  `CLAUDE.md`.
- **Archived snapshots** (`research/workflow-processes/archive/`)
  — frozen historical versions of superseded synthesis docs.

## Audit invariants

These docs are cross-checked for internal consistency. The
following invariants hold across all three:

- **Three canonical stores:** Specification, Implementation,
  Persistent Agent Knowledge.
- **Four queue/archives:** Proposed Changes (pure queue),
  Specification History (pure archive), Work Items (queue +
  archive), Memos (queue + archive).
- **Seven spec-side skills:** seed, propose-changes, critique,
  revise, doctor, prune-history, help.
- **Six impl-side skills (canonical):** capture-impl-gaps,
  capture-spec-drift, capture-work-item, implement, capture-memo,
  process-memos. `list-memos` is plugin-discretionary, not
  canonical.
- **One impl-side adapter:** Spec Reader, with four required
  capabilities.
- **Five cross-boundary contract edges:** two spec → impl
  (Specification → Spec Reader, Specification History → Spec
  Reader); three impl → spec (Capture Spec Drift → Propose
  Change, Process Memos spec-bound → Propose Change, Memos
  untriaged → Doctor).
- **Three work-item closure paths:** gap-tied fix (verify +
  audit), freeform fix (simple reason), non-fix (administrative
  reason).
- **Plugin catalog:** livespec-core plus implementation plugins
  matching the pattern `livespec-impl-<tracking-mechanism>`.
  Concrete plugins in scope: livespec-impl-plaintext,
  livespec-impl-beads, livespec-impl-gascity,
  livespec-impl-darkfactory-kilroy, livespec-impl-gitlab.
