# Executor decisions

Append-only log of executor judgment calls made during phase work that
weren't pre-decided in the plan. The bootstrap skill is the only
writer; entries are added via the skill's "record a decision first"
flow.

Each entry's heading carries the timestamp, phase, and sub-step. Body
captures the decision and its rationale.

## 2026-04-26T00:35:48Z — phase 0 sub-step 5

**Decision:** For plan-internal text-correction drift discovered
during Phase 0 sub-step 5 (three stale `bootstrap/.claude-plugin/`
references at plan lines 432, 2087, 2277), bypass the standard
halt-and-revise walkthrough and fix the references directly in a
regular commit. Codified the carve-out by amending
`.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`'s
"Plan/PROPOSAL drift is automatically blocking" section so this
distinction is durable.

**Rationale:** Halt-and-revise is calibrated for semantic drift
between executor interpretation and plan/PROPOSAL text (the v018-
v023 lineage). The drift here is entirely internal to the plan:
PROPOSAL.md is clean, plan §8's directory-shape diagram (lines
2179-2197) and four-command marketplace setup (lines 2199-2244)
are unambiguously authoritative, and three sentences elsewhere
in the plan failed to track the marketplace-setup propagation
in commit `4e423cc`. The fix is purely mechanical — there is no
decision to make about which path is correct. Producing a v024
snapshot with an unchanged PROPOSAL.md would be ceremony, not
verification. The skill carve-out preserves halt-and-revise as
the default for any non-mechanical drift.
