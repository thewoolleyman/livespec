# Critique + Interview Session Prompt (generic)

Paste the block below into a new Claude Code session (in the livespec
repo) to start the next critique-and-interview pass, producing the
next version from the current working `PROPOSAL.md`.

Before pasting, fill in the three numbers at the top of the prompt:

- `N`         — the current (latest completed) version number.
                This is the version recorded as the latest entry in
                `history/README.md`, and the working `PROPOSAL.md` is
                byte-identical to `history/vN/PROPOSAL.md`.
- `NEXT`      — `N + 1` — the version being produced by this session.
- `CRITIQUE`  — the critique-file sequence number for this pass.
                Convention so far:
                `v002` produced via `critique-v01`;
                `v003` produced via `critique-v02`;
                `v004` produced via `critique-v03`;
                `v005` produced via `critique-v04`;
                `v006` produced via `critique-v05`.
                So `CRITIQUE = N` (the current version number),
                zero-padded to two digits — equivalently,
                `CRITIQUE = NEXT - 1` (e.g. producing v007 →
                `CRITIQUE = 06`).

Everything below the `---` is the prompt body. The placeholders
`vNNN` / `v(NEXT)` / `critique-vCC` are written using the literal
variables `N`, `NEXT`, `CRITIQUE` — replace them verbatim before
pasting. (Or hand the whole prompt to Claude Code and let it do the
substitution.)

---

I want to do another iteration of the livespec PROPOSAL.md
critique-and-interview process, producing v{NEXT} from the current
v{N}.

Version knobs for this session:

- Current version: **v{N}**
- Next version: **v{NEXT}**
- Critique sequence number for this pass: **v{CRITIQUE}** (so critique
  file basename is `proposal-critique-v{CRITIQUE}`)

## Required reading (please load all of these before starting)

Working proposal and its embedded grounding:

- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `/data/projects/livespec/prior-art/nlspec-spec.md`
  (upstream source for `livespec-nlspec-spec.md`, preserved verbatim
  at the repo-root `prior-art/` directory for manual diffing against
  the adapted version)

Companion documents in the brainstorming folder (load every file
directly under `brainstorming/approach-2-nlspec-based/` that isn't
`PROPOSAL.md`, the two spec files above, this prompt itself, or a
one-off session prompt like `python-conversion-prompt.md` — the
current set is):

- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/goals-and-non-goals.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/subdomains-and-unsolved-routing.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/prior-art.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-diagram-detailed.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-lifecycle-legend.md`
- `/data/projects/livespec/brainstorming/approach-2-nlspec-based/2026-04-19-nlspec-terminology-and-structure-summary.md`

If new files have landed there since this prompt was last updated,
load those too. The now-retired bash style doc lives at
`history/v006/retired-documents/bash-skill-script-style-requirements.md`
(see the README beside it) — do NOT load it by default; it is
reference-only for understanding the v005→v006 language migration.

History (for versioning/lifecycle context and the prior decision
records — load **every file** under
`/data/projects/livespec/brainstorming/approach-2-nlspec-based/history/`,
including:

- `history/README.md`
- every `history/vNNN/PROPOSAL.md` (frozen per-version snapshots)
- every `history/vNNN/proposed_changes/*.md` (critiques, revisions,
  and any additional reference artifacts such as pre-interview
  drafts — v001/v002 use the legacy `vNNN-proposed-change-…` naming,
  v003+ uses the flat `proposed_changes/` subdir)
- every `history/vNNN/conversation.json` that exists (previous
  sessions' full dialogue records — use these to understand what was
  already considered and why; do not re-ask decisions that were
  explicitly resolved unless I bring them up)

Exception: `history/vNNN/retired-documents/` subdirectories (new in
v006) hold superseded companion docs that are intentionally out of
scope for the current proposal. Skim the README inside each such
directory to understand what was retired and why, but do not load
the retired docs themselves unless a critique item specifically
references one.

The v{N} entry is the most recent and the most important — its
PROPOSAL, its critique(s), its revision, and its `conversation.json`
(if present) are the direct input to this pass.

## What to produce

1. **Produce a new critique document** evaluating the current
   PROPOSAL.md (which is v{N}) against the embedded
   `livespec-nlspec-spec.md` guidelines, using the same
   failure-mode framework as prior critiques: label each finding as
   **ambiguity**, **malformation** (self-contradiction),
   **incompleteness**, or **incorrectness**. Apply the
   recreatability test. Produce major gaps, significant gaps, and
   smaller issues / cleanup items. Reference specific line numbers
   or section names in PROPOSAL.md.

2. **Save the critique** to
   `brainstorming/approach-2-nlspec-based/proposed_changes/v{NEXT}-proposed-change-proposal-critique-v{CRITIQUE}.md`.
   Use the multi-proposal file format established in v003+
   PROPOSAL.md (flat `## Proposal: <name>` sections with `### Target
   specification files`, `### Summary`, `### Motivation`, `###
   Proposed Changes` sub-headings; file-level YAML front-matter with
   `topic` / `author` / `created_at`).

3. **Interview me through every item**, one question at a time.
   Strict rules:

   - Print each item's sub-options visibly before asking.
   - Ask exactly ONE question per turn — never batch multiple
     sub-items into a single AskUserQuestion call.
   - Push back when I'm wrong or when something I'm proposing
     conflicts with decisions already in PROPOSAL.md or any prior
     revision file under `history/`.
   - Don't obsess over preserving v{N} compatibility during
     brainstorming — if a cleaner break is better, propose it.
   - If I ask you to clarify, clarify before re-asking.
   - If mid-interview I rewrite one of the companion files (e.g. the
     python style doc, goals/non-goals), append new critique items
     for any gaps that rewrite opens up against PROPOSAL.md before
     finishing.

4. **After the interview**, do the full dogfood lifecycle apply:

   - Write
     `history/v{NEXT}/proposed_changes/proposal-critique-v{CRITIQUE}-revision.md`
     capturing per-item decisions (accept / modify / reject +
     rationale).
   - Rewrite top-level `PROPOSAL.md` to v{NEXT} incorporating all
     decisions. Apply matching edits to every other working
     companion doc the decisions touch (typically
     `python-skill-script-style-requirements.md` and
     `deferred-items.md`).
   - **Run multiple careful-review passes BEFORE the byte-identical
     history copy.** A single pass is insufficient — v012's
     experience surfaced 22 inconsistencies across 3 passes
     (10 + 6 + 6). Diminishing returns are visible but not zero
     until at least pass 2 lands no non-cosmetic findings.
     **Minimum 2 passes; continue passes until a pass lands no
     load-bearing fixes.** Each pass MUST:
     - Re-read all working docs (PROPOSAL.md + companion docs)
       end-to-end after the previous pass's edits.
     - Look for places where the new decisions need ripple
       effects elsewhere (cross-doc references, examples,
       package-layout trees, DoD checklist entries).
     - Look for stale references to concepts the new decisions
       superseded (renamed targets, replaced enforcement checks,
       removed features).
     - Look for inconsistencies between the working docs (e.g.,
       counts, role names, file lists, cross-references to
       sections that don't exist).
     - Look for v012-style discoveries: examples that don't yet
       reflect the new conventions (e.g., a `match` statement
       missing the new `assert_never` terminator); existing rules
       that contradict each other after the new decision lands;
       AST checks whose exemption lists need broadening to cover
       newly-documented surfaces.
     - **Re-check the revision file against the post-pass
       working state.** The revision file is written FIRST (in
       the lifecycle's first sub-step) but its claims about the
       working docs become stale as later passes amend the
       working state. Each pass MUST verify the revision file's
       Summary-of-dispositions table, Self-consistency-check
       section, Deferred-items-inventory section, and
       Outstanding-follow-ups counts still match the working
       deferred-items.md state and PROPOSAL.md state after the
       pass's edits. v012's fourth pass surfaced this drift
       class (revision-file inventory listed entries as "carried
       forward" that pass 3 had widened; entry-touch counts
       stale; summary-table row text stale). Update the revision
       file in lock-step with each pass's findings.
     - **Pass record-keeping.** Each pass MUST be recorded
       distinctly: in the `conversation.json` final assistant
       turns AND in the `history/README.md` v{NEXT} entry. The
       cumulative finding count across all passes is also
       recorded.
   - **Run a dedicated deferred-items-consistency pass.** This is
     a SPECIFIC review pass — distinct from the general careful-
     review passes above — that walks every deferred-items entry
     and verifies its source line + body fully reflect every
     decision that touched it across every prior version. v012's
     third pass found multi-version drift in
     `enforcement-check-scripts` (PROPOSAL.md's
     `dev-tooling/checks/` layout had not been updated since v005
     and was missing v011 K4 + v012 L5/L7/L8/L9/L10/L12 added
     check scripts) and `claude-md-prose` (source line stale at
     "v006 carried forward to v008" through v009-v012). Required
     checks for this pass:
     - **Source-line drift.** For every deferred-items entry,
       does its `Source:` line record every prior-version
       widening that touched it? Cross-reference against every
       `history/vNNN/proposed_changes/*-revision.md` revision
       file's "Deferred-items inventory" section to find missing
       widening notations.
     - **Layout-tree drift.** For every package-layout tree
       in PROPOSAL.md (e.g., `dev-tooling/checks/`,
       `livespec/**`, `tests/**`), does the tree match what the
       cumulative K/L decisions produce? List every item in the
       tree and verify each is still introduced/extant per
       current decisions; list every artifact the cumulative
       decisions introduce and verify each appears in the tree.
     - **Cross-reference validity.** For every `§"..."`
       cross-reference in any working doc, verify the target
       subsection / section actually exists. Stale references
       to renamed or removed sections are common drift artifacts.
     - **Example-vs-rule alignment.** For every code example in
       any working doc, verify it follows the current rules
       (e.g., dataclass examples use the current strict-triple
       form; match-statement examples include the current
       exhaustiveness terminator; wrapper examples reflect the
       current bin/_bootstrap.py contract).
   - Create `history/v{NEXT}/PROPOSAL.md` as a byte-identical
     copy of the working `PROPOSAL.md`. (If any review pass
     edited PROPOSAL.md after a prior copy, RE-COPY and verify
     byte-identical via `diff -q`.)
   - Move the critique from `proposed_changes/` to
     `history/v{NEXT}/proposed_changes/proposal-critique-v{CRITIQUE}.md`.
   - If a pre-interview draft of the critique exists, also move it
     to `history/v{NEXT}/proposed_changes/` with a descriptive
     suffix (e.g. `…-original-questions-pre-interview.md`).
   - Update `history/README.md` to add a v{NEXT} entry summarizing
     the major structural changes and pointing at the revision file;
     update its final "Pointer" paragraph to reference v{NEXT}.
     The v{NEXT} entry MUST record the careful-review-pass
     findings distinctly per pass (count of issues caught;
     summary of the most load-bearing fixes), and MUST record
     the dedicated deferred-items-consistency pass's findings
     separately.
   - Capture the session's turns into
     `history/v{NEXT}/conversation.json` (user verbatim, assistant
     summaries) — same schema as prior `conversation.json` files.
     Each careful-review pass + the dedicated deferred-items
     pass MUST appear as distinct assistant turns recording what
     the pass caught.

## Known constraints to honor

Do NOT reopen any decision that is currently written into
`PROPOSAL.md` or into any prior `history/vNNN/proposed_changes/
*-revision.md` unless I explicitly raise it. The latest revision
file (`history/v{N}/proposed_changes/…-revision.md`) is the
authoritative record of what was most recently settled — read it
first and treat its dispositions as load-bearing. Same for the
`history/README.md` summary of each version's scope.

Start by reading all the required files, then produce the critique
and save it. Then begin the interview.
