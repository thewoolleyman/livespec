# Bootstrap status

**Current phase:** 3
**Current sub-step:** 16
**Last completed exit criterion:** phase 2
**Next action:** Phase 3 sub-step 16 — author `livespec/commands/revise.py` (minimum-viable per v019 Q1): reads every `<spec-target>/proposed_changes/*.md`, accepts a per-proposal accept/reject decision via stdin payload (the full LLM-driven decision flow lives in Phase 7), writes the paired `<topic>-revision.md`, and on accept cuts a new `<spec-target>/history/vNNN/` materialized from the current spec files. Accepts `--spec-target <path>`. Out-of-Phase-3 scope: per-proposal LLM decision flow with delegation toggle, rejection-flow audit-trail richness beyond the simplest "decision: reject" front-matter line. Sub-step 15 closed: authored `livespec/commands/critique.py` as a minimum-viable delegation wrapper — appends `-critique` reserve-suffix to the topic verbatim and forwards argv to `propose_change.run()`. Same CLI surface (topic, --findings-json, --author, --spec-target, --project-root) forwarded straight through. Phase 7 widens to full reserve-suffix canonicalization (v016 P3 / v017 Q1 algorithm). ruff clean.
**Last updated:** 2026-04-26T16:17:05Z
**Last commit:** 551119e
