# Beads-only gap storage — workflow-process discussion

**Date captured:** 2026-05-11
**Branch:** `spec/v060-claude-opus-4-7-critique` (PR #84, auto-merge armed)
**Status:** Open question. User is sitting with the framing before
formalizing.
**Related artifacts:**
- `SPECIFICATION/non-functional-requirements.md` §"Repo-local
  implementation workflow", §"Implementation-gap report shape",
  §"Beads invariants", §"Gap-tied issue closure verification"
- `implementation-gaps/current.json` + `current.schema.json`
- `dev-tooling/implementation/refresh_gaps.py`,
  `plan.py`, `implement.py`
- `research/workflow-processes/spec-vs-implementation-line.md`
  (companion sit-with on the spec-vs-implementation routing
  question)
- `research/workflow-processes/workflow-diagrams.md` (the high-level
  / spec / implementation / observation-flow PlantUML set)
- `dev-tooling/implementation/research/beads-problems.md` (vendored
  upstream-issue catalogue)

## Why this conversation happened

While running `/livespec-implementation-beads:plan` after the v060
revise landed, refresh-gaps regenerated
`implementation-gaps/current.json` with a metadata-only diff:
new `generated_at`, new `run_id`, updated `spec_sources.spec_md.
git_blob_sha` (because spec.md changed). `gaps: []` was unchanged.

The user asked the sharp question: *why are we tracking those
fields at all — do they have any value that git history doesn't
already give us?* That opened a second, larger architectural
question: the `current.json` file is the only piece of the
implementation-layer workflow that's stored outside the beads /
Dolt source of truth. Why have two persistent stores when one
of them can do the job alone?

This document captures the brainstorm for further reflection
before any formal proposed-change is authored.

---

## Turn 1 — User

> Why are we even tracking these fields? Do they have any value
> that the Git history doesn't give us?

(Context: the three fields are `generated_at`, `run_id`, and the
per-spec-file `git_blob_sha` blocks inside `spec_sources`.)

---

## Turn 2 — Assistant (per-field analysis)

Honest pushback after grepping every consumer:

- **`spec_sources[*].git_blob_sha`** — `refresh_gaps.py:100` writes
  it; nothing reads it back. The schema requires it
  (`current.schema.json:84`) but no code compares the recorded
  blob to `git hash-object` to detect staleness. **Pure audit
  cosmetic and strictly redundant with git** — `git ls-tree
  <commit> -- <path>` gives the same answer for any committed
  state. Verdict: drop it.
- **`run_id`** — `implement.py:166-174,225,231` threads it into the
  `bd close --reason` text and the close-note, intending to
  correlate with `refresh_gaps`'s stderr structlog line bearing
  that UUID. In practice nobody archives that stderr for `bd
  show` lookups weeks later. **Theoretical value, zero practical
  consumer.** Verdict: drop it (or keep stderr-only and stop
  persisting in JSON).
- **`generated_at`** — same `implement.py` path embeds this in the
  `bd close` reason and close-note, which Dolt persists. Weak but
  real value: tells you when the verifying refresh-gaps ran,
  which can be minutes-to-hours before the close-commit timestamp
  `git log` shows. **The only one of the three with a non-zero
  non-git consumer.** Verdict: could go either way — easy enough
  to inline in the `bd close --reason` text on the spot, without
  persisting it in a JSON file.

Net diagnosis: every refresh-gaps run creates a 7-line metadata-only
diff (timestamp + uuid + 3-5 blob shas) for zero downstream
decisions. That's the noise the user was feeling. The deeper issue
is that the JSON file is the only implementation-layer artifact
that lives outside beads — every other piece of state (issue
status, dependencies, audit notes, planning history, freeform
issues) is already in `.beads/`.

---

## Turn 3 — User

> I want to step back and think about this as a bigger
> architectural question.
>
> Read under research/workflow-processes for context.
>
> The fact that this is stored in git is an anti-pattern. We'd
> really like to have just one persistent store for workflow
> tracking. And in this current implementation pattern of beads,
> that is the [Dolt] database and beads itself.
>
> So I want you to brainstorm on how we can collapse this gap
> tracking to metadata in beads itself and eliminate the yaml
> file.
>
> Carefully read the workflow processes, diagrams, and other
> documents in there to see the larger direction we are going with
> pluggable implementations, and think about the API surface
> between the LiveSpec Core and the implementation, and how the
> decision here impacts that.

(The "yaml file" referenced is `current.json` — the storage
format is JSON, but the user's framing is "the gap-tracking
file persisted in git.")

---

## Turn 4 — Assistant (brainstorm)

### The forces at play

Three load-bearing facts surfaced from reading the workflow
diagrams and the NFR sections:

1. **Beads / Dolt is already the source of truth for everything
   else** in the implementation layer — issue state, dependencies,
   audit notes, planning history, freeform issues. `current.json`
   is the only implementation-layer artifact that lives outside
   it.
2. **The implementation layer is intentionally outside LiveSpec
   Core.** NFR §"Repo-local implementation workflow" says
   discovery is "repository-specific implementation knowledge …
   intentionally outside `livespec` core." So whatever we
   standardize is not a core contract — it's an *emerging pattern*
   other projects can adopt or replace.
3. **The current shape leaks every refresh into git.** Every
   refresh-gaps regenerates timestamps, UUIDs, and 5 blob SHAs
   independent of whether any gap actually changed. The
   user-visible smell is the metadata diff; the deeper smell is
   the dual-store split — bd carries one half of the workflow
   truth, JSON carries the other, and they have to be kept
   consistent (the 1:1 invariant is exactly the cost of that
   split).

### Design alternatives

**Option A — Pure beads, refresh-gaps writes directly.**
refresh-gaps detects predicates and immediately reconciles bd:
files new gap-tied issues, updates drifted descriptions, surfaces
stale labels for triage.

- *Pro:* simplest data flow; one writer, one store.
- *Con:* breaks the load-bearing read-only invariant on
  refresh-gaps. plan's whole purpose is the per-issue
  user-consent gate — you don't want refresh-gaps to silently
  file 12 new issues from a spec edit.

**Option B — Beads as truth, refresh-gaps stays read-only, no
persisted JSON.** ⭐ (assistant leaning, paired with C below)
refresh-gaps becomes an in-memory predicate runner that emits
a 3-way diff to stdout: *predicted-but-untracked*,
*tracked-but-no-longer-predicted*, *both*. plan reads from stdin
(or a transient `/tmp` path), surfaces per-issue with consent,
then bd-writes. implement's verify step re-runs refresh-gaps and
fails if the predicate still fires for the gap-id being closed.

- *Pro:* preserves the consent gate; no git artifact; refresh-gaps
  stays deterministic and free to re-run.
- *Con:* loses the "reproducible snapshot" property. Mitigation:
  it was never load-bearing — implement already requires a fresh
  re-run on close.

**Option C — Pure beads with a rich label vocabulary.**
Same storage move as B, plus structured labels for enumerated
gap fields:

- `gap-id:gap-NNNN` (already exists)
- `area:plugin` / `area:dev-tooling` / `area:tests` / …
- `severity:blocking` / `severity:partial` / `severity:drift` / …
- `evidence-kind:code` / `evidence-kind:absent` / …
- `destructive:true` / `destructive:false`

Description carries the prose (expected, observed, evidence,
fix_hint). `bd update --priority` covers priority. `bd dep add`
covers `depends_on`. A `dev-tooling/checks/label_vocabulary.py`
keeps the namespace clean.

- *Pro:* every gap field becomes queryable
  (`bd list -l severity:blocking`); plays well with bd's existing
  primitives; no parser needed.
- *Con:* mild label-namespace sprawl. Negligible with a vocab
  linter.

**Option D — Hybrid with ephemeral on-demand view.**
Same as C, plus an optional `just implementation::view` that
derives a Markdown rollup from `bd list --label='gap-id:*' --json
| jq …` for human reading, never committed.

- Pure additive; use when you want cat-current.json ergonomics
  without the git noise.

### What dies, decisively (Option B+C)

| Field | Today's source | After collapse |
|---|---|---|
| `gap-id` | JSON `gaps[].id` | bd label (already) |
| `area` / `severity` / `evidence_kind` / `destructive_to_fix` | JSON enums | bd labels |
| `priority` | JSON | `bd update --priority` (bd-native) |
| `title` | JSON | bd title |
| `expected` / `observed` / `evidence` / `fix_hint` | JSON | bd description (structured Markdown headings) |
| `depends_on` | JSON array | `bd dep add` (bd-native) |
| `spec_refs` | JSON array | bd description anchor list |
| `generated_at` | JSON | verifying `bd close --reason` text |
| `run_id` | JSON | generated on-the-spot in implement, embedded in close-note |
| `spec_sources.git_blob_sha` | JSON | gone — was never consumed |
| `inspection.scopes_inspected/skipped` | JSON | gone, or moved into refresh-gaps stdout self-narration |
| `summary.by_*` aggregates | JSON | gone — derive on demand from `bd list --json` |

The `current.schema.json` document goes away. `dev-tooling/
implementation/gap_blueprints.json` is a separate concern
(author-time blueprints, not refresh-time output); could survive
or migrate to `bd remember` entries — doesn't have to be coupled
to this decision.

### API-surface impact for pluggable implementations

**Today's implicit contract for any project adopting the
livespec-implementation pattern:**

> Produce a `current.json` conforming to `current.schema.json`
> with N typed fields per gap, fingerprint your spec sources, and
> commit on every refresh.

That's a heavy schema-shaped commitment. Adopters have to map
predicate output to that exact JSON shape, author a paired schema
when they extend it, eat the merge churn, and reproduce the
LiveSpec-Core / implementation-layer split exactly.

**Beads-only contract:**

1. Implement a refresh-gaps detector (any language, any predicate
   vocabulary).
2. Every detected gap MUST exist as exactly one bd issue with the
   `gap-id:gap-NNNN` label.
3. Issue closure with `resolution:fix` MUST re-run the detector
   and confirm the predicate no longer fires.

Three sentences. No schema. No file. Implementation is free to
use any internal data shape; the external contract is bd labels
plus a re-runnable detector. Strictly smaller, strictly more
pluggable. Tracks the way the workflow diagrams already think
about it — the high-level lifecycle and observation-flow diagrams
already treat `.beads/` as the single store; the JSON is an
artifact of the current implementation, not the conceptual model.

The `observation-flow` diagram already routes both paths
(gap-tied + freeform) into the same `.beads/` cylinder. Today the
JSON is the only thing that distinguishes the two paths at the
storage layer. Collapse it and the diagram becomes more honest:
both paths are bd writes; the only difference is the `gap-id:`
label and the closure verification step.

### Assistant leaning

**Option C with Option D as the optional human-view layer.**
Concretely:

- Drop `current.json`, its schema, and the
  `spec_sources` / `run_id` / `generated_at` fields entirely.
- refresh-gaps emits the 3-way diff to stdout; plan consumes from
  stdin (preserves the consent gate).
- Gap fields move into bd labels (enumerated) + description
  (prose) + dep edges (`depends_on`) + priority (already
  bd-native).
- `check-gap-tracking` becomes a bd query.
- audit-on-close fields (timestamp, run_id) live only in the
  `bd close --reason` text.
- Update the NFR §"Repo-local implementation workflow" +
  §"Implementation-gap report shape" + §"Beads invariants"
  sections accordingly via `/livespec:propose-change`.
- API contract for adopters compresses to three sentences.

---

## Things to sit with

1. **Open Brain coordination.** NFR §"Repo-local implementation
   workflow" names Open Brain as the "canonical pattern source"
   and the implementation-gap report schema is "modeled on Open
   Brain's `PLAN/current-specification-drift.schema.json`." If
   livespec moves first, that pointer needs an update — either
   "canonical for the original pattern; livespec has evolved it"
   or coordinate the migration with Open Brain. Either is fine;
   it's a coordination decision, not a technical one.

2. **Audit reproducibility loss.** Today you can `git log -p
   implementation-gaps/current.json` to see what the predicates
   reported on any given commit. Beads-only loses that — bd has
   issue history but not "the full predicate output as of day X".
   The close-note records what was true at verification time, and
   predicate evolution lives in `git log
   dev-tooling/implementation/refresh_gaps.py`. Is the
   reproducibility loss acceptable? (Assistant leaning: yes, it
   was never load-bearing.)

3. **Static-check ergonomics.** `check-gap-tracking` becomes a
   bd-query script instead of a JSON-vs-bd diff. Trivial
   conceptually, but the new shape needs naming. Probably
   `check_gap_tracking.py` that runs `bd list -l 'gap-id:*'
   --json` and asserts 1:1 against a fresh refresh-gaps in-memory
   output.

4. **`bd remember` as the home for non-actionable observations.**
   Spec-vs-implementation-line.md flags a third observation
   category that doesn't have a clear home today: "I noticed bd's
   export throttles at 60s by default; might matter later." With
   the auto-memory ban in NFR (per li-jdq), `bd remember` is a
   natural successor — beads-native, persists across sessions,
   grep-able via `bd memories <keyword>`. Worth deciding if the
   formalization couples to that.

5. **Plan-pass commits become very small.** Today's planning
   commit bundles the JSON regeneration + the bd export. Without
   the JSON, planning commits are pure `.beads/issues.jsonl` —
   which is arguably what you'd want (commits only when issues
   actually change). Confirm this matches the desired review
   ergonomic.

6. **Does the JSONL export survive at all?** NFR §"Beads
   invariants" #3 says "the beads Dolt database is the source of
   truth; `.beads/issues.jsonl` is a git-tracked human-readable
   export view ONLY". If Dolt+`refs/dolt/data` is the cross-machine
   protocol, the JSONL exists only for `git grep` and review.
   Keep? Drop? (Assistant leaning: keep — `git grep`-ability and
   review continuity are real even if the file is derived.)

7. **`gap_blueprints.json` disposition.** plan.py reads this for
   static gap definitions (the predicate authoring side, not the
   refresh-time output side). Stays as Python-side data?
   Migrates to `bd remember`? Migrates to a directory of
   per-gap-id markdown files? Independent decision; doesn't
   have to be coupled to this collapse.

8. **Migration path.** If formalized, existing gap-tied beads
   issues already carry the `gap-id:gap-NNNN` label. The
   labelization of enum fields (area, severity, evidence-kind,
   destructive) needs a one-time backfill — straightforward but
   needs sequencing in the proposed-change.

9. **Where the "spec-sources fingerprint" intent goes, if
   anywhere.** Today it's "implement rejects stale reports by
   comparing recorded blob SHAs to current files on disk." In
   practice this check doesn't exist in code; the field is
   audit-only. If we ever want freshness-gating, it lives in
   refresh-gaps' freshness logic, not in a persisted artifact.
   So: probably dies entirely; flag if a use case surfaces.

10. **Diagram updates.** workflow-diagrams.md's
    implementation-lifecycle and observation-flow diagrams
    currently show `implementation-gaps/current.json` as a
    cylinder between refresh-gaps and plan. If the collapse
    lands, those cylinders disappear and the diagrams simplify.
    Diagram update is part of the formalization, not a
    pre-decision.
