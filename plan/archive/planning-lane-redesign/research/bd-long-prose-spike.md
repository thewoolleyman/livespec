# bd long-prose spike

Captured 2026-08-04 for work-item `livespec-zsn2xh.1`.

## Question

Can `bd` carry real-sized Markdown plan handoffs directly in the ledger, and
which surface should the plan redesign standardize on?

## Method

I installed `@beads/bd` 1.1.2 into `/tmp` and used the package's native
binary directly. The host sandbox had no `bd` on `PATH` or at
`/usr/local/bin/bd`.

The probe ledger was an embedded Beads workspace in a temporary git repository
under `/tmp/bd-long-prose-spike-tYkEgi`, outside every livespec checkout. Beads
1.1.2 has no non-`init` first-workspace creation path: `bd bootstrap` refused
without an existing `.beads` workspace, and an explicit `--db` path refused
without initialized `issue_prefix` config. The probe therefore used:

```sh
bd init --non-interactive --skip-agents --skip-hooks --prefix spike --role maintainer --sandbox
```

The payload was a 34,294 byte Markdown document assembled from
`plan/planning-lane-redesign/supervisor-handoff.md` plus an excerpt from
`research/brainstorm.md`. Its SHA-256 was:

```text
cb6043411f3538567e1805bc28d30941c946f894d19562b96847115dbac90405
```

The probe wrote that payload to three candidate surfaces:

- issue description: `bd create --body-file payload.md`
- notes field: `bd create --notes "$payload_text"`
- comments: `bd comments add <id> --file payload.md`

Then it appended a second 41 byte entry to each candidate and read the results
back through the `bd` CLI using `bd show --json --include-comments`,
`bd comments <id> --json`, and field queries.

## Results

### Description

- **Size limits / truncation:** No truncation observed at 34,294 bytes. After
  replacing the description with payload plus the second entry, `bd show --json`
  returned 34,335 bytes and matched the expected combined content exactly.
- **Escaping / round-trip fidelity:** JSON readback preserved Markdown content,
  including fenced code, tables, backticks, arrows, and angle-bracket examples.
  `bd show` in human text mode wraps and indents long prose for display, so it is
  readable but not a byte-faithful copy surface; JSON is the faithful read path.
- **Append ergonomics:** Weak. There is file-based replacement
  (`bd update --body-file`), but no description append command. A sequential
  handoff entry requires reading the old body, concatenating locally, and
  replacing the whole field.
- **Read / query ergonomics:** Good for one current body. `bd show --json`
  returns the full field, and `bd query 'description="Research context excerpt"'
  --json` found the issue. It is poor for an append-only journal because entries
  are not individually addressable.

### Notes

- **Size limits / truncation:** No truncation observed at 34,294 bytes.
  `bd show --json` returned the original payload plus the appended entry.
- **Escaping / round-trip fidelity:** The original long payload round-tripped
  through the notes field. The append command preserved the appended content
  except for the shell-command-substitution trailing newline used by the probe;
  the marker and text were present exactly after stripping that shell-added
  artifact. This is a command invocation issue, not observed ledger truncation.
- **Append ergonomics:** Medium. `bd update --append-notes` exists and appends a
  newline separator, but it accepts a string flag, not a `--notes-file` or stdin
  input. That makes 30-50 KB handoffs awkward for agents and shells because the
  write path depends on large argv strings unless the caller builds a wrapper.
- **Read / query ergonomics:** Good for one accumulated body. `bd show --json`
  returns the full notes field, and `bd query 'notes="Research context excerpt"'
  --json` found the issue. It is poor for sequential handoffs because entries
  are flattened into one growing field with no separate author/timestamp per
  entry beyond the bead's update time.

### Comments

- **Size limits / truncation:** No truncation observed at 34,294 bytes. The first
  comment read back at 34,294 bytes with the exact payload SHA-256. The second
  comment read back as a separate 41 byte entry with its own exact SHA-256.
- **Escaping / round-trip fidelity:** JSON comment readback preserved the
  Markdown body exactly. Human `bd comments <id>` output wraps and indents for
  display, so JSON is the faithful read path and text mode is a browsing path.
- **Append ergonomics:** Strong. `bd comments add <id> --file payload.md` is the
  natural handoff write path: file-based, append-only, no read-modify-write, and
  each sequential entry remains separate.
- **Read / query ergonomics:** Good for timeline reads, limited for field
  queries. `bd show --json --include-comments` and `bd comments <id> --json`
  both return full comment bodies and preserve entry boundaries. `bd search
  "Research context excerpt"` returned no rows for the comment-only bead — a
  true observation, but on its own an INVALID inference: `bd search` text
  queries are title-and-ID scoped, so the same command also returns no rows
  for content sitting in a DESCRIPTION, and an empty result from it proves
  nothing about comments. The corrected evidence (independent review,
  2026-08-04, bd 1.0.5): `bd search <title-word> --desc-contains <marker>`
  finds planted description content but not a comment-only marker, and
  `bd query 'comments="..."'` fails with an explicit `unknown field: comments`
  — a definitive rejection rather than an empty result. The conclusion is
  unchanged: comment bodies are not reachable through `bd query` or
  `bd search`.

## Recommendation

Use comments as the ledger surface for plan handoffs.

Comments are the only probed surface that gives the redesign all required
handoff properties at once: long Markdown round-trips without observed
truncation, append-only sequential entries, file-based writes, and per-entry
boundaries with author/timestamp metadata. Description and notes can store the
bytes, but they are single-field state; using either one as a handoff journal
would recreate a mutable document inside the ledger.

The design should account for one limitation: comment bodies are not searchable
through `bd query` in Beads 1.1.2. Store any machine-queryable handoff metadata
outside the prose body, for example in labels or metadata on the plan epic or
in a short index comment convention, and use `bd comments <epic-id> --json` as
the authoritative handoff read path.

## Addendum — independent review verification (2026-08-04)

The independent adversarial review required for research deliverables
re-derived this spike's claims against the fleet's CURRENT pin,
`bd version 1.0.5 (6a3f515ce)` at the guarded `/usr/local/bin/bd`, on an
embedded scratch ledger outside every checkout:

- **The recommendation carries NO version condition.** Every capability it
  depends on — `bd comments add <id> --file`, exact long-prose round-trip,
  per-entry boundaries with author/timestamp metadata, and
  `bd show --json --include-comments` — is present and verified on 1.0.5 as
  well as the 1.1.2 this spike probed.
- **The round-trip envelope is verified to 133,457 bytes**, digest-exact
  (SHA-256), not merely the 34 KB probed above. Three sequential comments of
  38,518 / 42 / 133,457 bytes read back as three separately addressable
  entries, each byte-exact.
- **Search-evidence repair:** the `bd search` sentence under "Comments" above
  was corrected by that review. On 1.0.5 the query-language limitation is an
  explicit `unknown field: comments` rejection — firmer ground than the empty
  search result originally cited, which a title-and-ID-scoped `bd search`
  would have returned even for indexed content.
- **Embedded-init flag parity:** 1.0.5 needed only
  `bd init --non-interactive --prefix <p>`; the 1.1.2 flags `--skip-agents`,
  `--skip-hooks`, and `--sandbox` do not exist / were not needed on 1.0.5.
  Comment entry ids are UUIDs on 1.0.5.
