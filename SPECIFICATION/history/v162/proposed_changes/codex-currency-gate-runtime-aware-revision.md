---
proposal: codex-currency-gate-runtime-aware.md
decision: accept
revised_at: 2026-07-08T18:41:54Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

ACCEPT: ratify the runtime-aware, fail-soft Codex plugin-currency gate (work-item livespec-c1k9.4). The independent Fable review returned NO-BLOCKERS (the pre-ratification precondition), and the paired impl already landed as fb7ba5b. Applies the six edits (1a/1b/2/3 core amendments + 4/5/6 Fable drift-sweep co-fixes) to non-functional-requirements.md §"Plugin currency and the release train", each a verbatim-unique replace-target: the currency chokepoint's compare is runtime-aware (Claude = local offline running-vs-clone; Codex = last_revision vs remote tip of the configured ref); a confirmed-stale build fails hard on Claude but a confirmed-BEHIND build on Codex is a lever-gated soft signal (warn-by-default; hard only under LIVESPEC_CURRENCY_GATE=fail); and the before-session updater mechanism is native on Codex vs the committed SessionStart hook on Claude — with the Installer rationale, the currency-invariant sentence, and the plain-language summary drift-swept to match. This is a SUBSET revise: only this proposal is accepted; owned-heading-coverage-todos.md is left untouched in proposed_changes/. No ## (H2) heading changes, so no tests/heading-coverage.json co-edit is required.

## Resulting Changes

- non-functional-requirements.md
