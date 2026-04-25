# Open issues

Append-only-with-status-mutation log of plan / PROPOSAL drift
discovered during bootstrap execution. The bootstrap skill is the
only writer.

Each entry's heading carries the timestamp, phase, severity, and
disposition. Severity is one of: `blocking`,
`non-blocking-pre-phase-6`, `non-blocking-post-phase-6`. Disposition
(intent) is one of: `halt-and-revise-brainstorming`,
`defer-to-spec-propose-change`, `resolved-in-session`. Status
(lifecycle) is one of: `open`, `resolved`, `superseded`.

Existing entries' bodies are written once; the `Status:` field MAY
be mutated in place, and a `**Resolved:** ...` line MAY be appended
on resolution. Never rewrite or delete entries without explicit
user direction.

Entry format:

```markdown
## <UTC ISO 8601> — phase N — <severity> — <disposition>

**Status:** open

**Description:** <description, 1-3 sentences>
```

On resolution, the skill mutates `Status:` to `resolved` and
appends:

```markdown
**Resolved:** <UTC ISO 8601> — <one-line resolution summary>
```

(no entries yet)
