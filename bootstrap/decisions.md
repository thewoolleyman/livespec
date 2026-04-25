# Executor decisions

Append-only log of executor judgment calls made during phase work that
weren't pre-decided in the plan. The bootstrap skill is the only
writer; entries are added via the skill's "record a decision first"
flow.

Each entry's heading carries the timestamp, phase, and sub-step. Body
captures the decision and its rationale.

(no entries yet)
