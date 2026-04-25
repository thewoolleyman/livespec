# Open issues

Append-only log of plan / PROPOSAL drift discovered during bootstrap
execution. The bootstrap skill is the only writer; entries are added
via the skill's "report an issue first" flow.

Each entry's heading carries the timestamp, phase, severity, and
disposition. Severity is one of: `blocking`, `non-blocking-pre-phase-6`,
`non-blocking-post-phase-6`. Disposition is one of:
`halt-and-revise-brainstorming`, `defer-to-spec-propose-change`,
`resolved-in-session`.

(no entries yet)
