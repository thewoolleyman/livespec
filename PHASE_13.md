# Phase 13 — Codify live-spec authority via PROPOSAL.md citation purge

**Status:** Pending. Phase 12 closed the bootstrap-process residue and
archived the bootstrap-era directories under `archive/`. Phase 13 is
the follow-up that completes the LIVESPEC self-containment principle:
no production-permanent file may cite `PROPOSAL.md` (the archived
genesis document) as the authority for any rule. The live
`SPECIFICATION/` tree is the canonical authoritative source; citations
must point there or be removed entirely.

## Motivation

The Phase-6 seed and the Phase-8 deferred-items migration moved the
substantive PROPOSAL.md content into `SPECIFICATION/spec.md`,
`contracts.md`, `constraints.md`, and `scenarios.md`. But many
docstrings, comments, and prompt-prose passages throughout the codebase
still cite "Per PROPOSAL.md §X" as their authority. Now that PROPOSAL.md
lives at `archive/brainstorming/approach-2-nlspec-based/PROPOSAL.md`,
those citations point at archive content — they're load-bearing
rationale references but their target is no longer the live oracle.

The fix: every PROPOSAL.md citation in production-permanent files
either (a) drops entirely (when the citation is redundant — the live
spec content adjacent in the same file is the rule), or (b) rewrites
to point at the corresponding `SPECIFICATION/<file>.md §<section>`.

## Scope

Approximate scope (re-grep at session start to confirm current state):
~107 production-permanent files, ~267 PROPOSAL.md / brainstorming-citation
matches.

| Category | Files | Treatment |
|---|---|---|
| Live `SPECIFICATION/*.md` | 4 | Drop PROPOSAL.md citations entirely — the spec body IS the rule. Dogfood `propose-change` → `revise`. |
| Live `SPECIFICATION/templates/livespec/*.md` | 1+ | Same. Dogfood against the sub-spec target. |
| Production source code (`.claude-plugin/scripts/livespec/**.py`, `.claude-plugin/scripts/bin/**.py`) | ~30 | Replace `# Per PROPOSAL.md §X` docstring/comment with `# Per SPECIFICATION/<file>.md §<section>`. Edit directly (impl change, `chore:`/`docs:` commit). |
| Skill prompts (`.claude-plugin/skills/<sub-cmd>/SKILL.md`) | 6 | Replace PROPOSAL.md references with SPECIFICATION/ references. Edit directly. |
| Built-in template prompts (`.claude-plugin/specification-templates/{livespec,minimal}/prompts/*.md`) | 9 | Replace PROPOSAL.md references with SPECIFICATION/ references. These ship to consumer projects, so the references must point at the consumer's spec tree, not at livespec's own `SPECIFICATION/`. Re-evaluate per-prompt; some references may need rewording rather than rewriting. Edit directly. |
| Test files (`tests/**`) | ~30 | Most are docstring provenance refs — replace with SPECIFICATION/ references or remove. Edit directly. |
| Tooling (`justfile`, `lefthook.yml`, `NOTICES.md`, `dev-tooling/checks/**.py`, `.github/workflows/**.yml`, `pyproject.toml`, `.mise.toml`, `.vendor.jsonc`) | ~15 | Replace PROPOSAL.md comment refs with SPECIFICATION/ refs or remove. Edit directly. |

## Mapping requirement

Phase 13 requires a mapping table from PROPOSAL.md sections to
their corresponding SPECIFICATION/ sections. Most sections were
migrated 1-to-1 during Phase 8; some were split or merged. Build the
mapping at session start by:

1. Listing every distinct PROPOSAL.md citation pattern across the
   ~267 matches (`grep -hoE 'PROPOSAL\\.md §"[^"]+"' ... | sort -u`).
2. For each unique section name, locate the corresponding section in
   `SPECIFICATION/{spec,contracts,constraints,scenarios}.md`.
3. For citations whose substantive content didn't migrate (rare), the
   citation gets removed and the rule (if still load-bearing) is
   added to the live spec via dogfooded propose-change.

## Dogfooding requirement

Live `SPECIFICATION/**.md` edits MUST flow through `propose-change` →
`revise`. Treat the citation purge as a single propose-change per spec
file (or one batched propose-change covering all four files); the
revise cuts a new history version per cycle.

All other files (impl, tests, skills, templates, tooling) edit
directly with `chore:` or `docs:` commits. Bundle related changes
into reasonable-size commits (e.g., one commit per skill prompt; one
commit per impl subpackage).

## Exit criteria

- `grep -rn "PROPOSAL\\.md" .claude-plugin/ dev-tooling/ tests/ SPECIFICATION/ pyproject.toml justfile lefthook.yml .mise.toml .github/ NOTICES.md .vendor.jsonc README.md AGENTS.md | grep -v _vendor | grep -v "SPECIFICATION/history/"` returns empty.
- `just check` aggregate passes (full enforcement suite).
- Phase 13 lands as one PR (or a small series of PRs grouped by file
  category if scope justifies).
- `archive/bootstrap/STATUS.md` updates to reflect Phase 13 closure
  (the file lives at `archive/` post-Phase-12 but is allowed to be
  edited as the bootstrap-status historical record).

## Out of scope

- Editing `archive/**` (frozen historical content; PROPOSAL.md citations
  there are time-bound and correct as of the version-cut moment).
- Editing `SPECIFICATION/history/vNNN/` snapshots (frozen audit-trail
  records).
- Adding new spec content beyond what's needed to absorb a citation
  whose substantive rule didn't migrate during Phase 8.
- Publishing the plugin to a Claude Code plugin marketplace.

## Sequencing

1. Re-grep to confirm current scope.
2. Build the PROPOSAL.md → SPECIFICATION/ section mapping table
   (capture in `tmp/phase13/mapping.md` for executor reference).
3. Dogfood the live-spec citation purge (propose-change → revise per
   spec file or batched).
4. Sweep impl source files. Group by subpackage where practical.
5. Sweep skill prompts.
6. Sweep built-in template prompts (per-template, per-prompt).
7. Sweep test files.
8. Sweep tooling files.
9. Verify exit criteria; commit; merge as Phase 13 PR.
