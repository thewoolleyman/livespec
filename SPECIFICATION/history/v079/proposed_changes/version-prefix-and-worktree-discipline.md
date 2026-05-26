---
topic: version-prefix-and-worktree-discipline
author: claude-opus-4-7
created_at: 2026-05-25T17:19:48Z
---

## Proposal: require-project-name-prefix-on-version-references-in-spec-prose

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Adopt a project-wide rule: every version reference in spec prose (across the upstream `livespec` spec AND every sibling-repo spec governed by livespec) MUST be prefixed with the owning project name (e.g., `livespec v078`, `livespec-runtime v0.3.0`, `livespec-impl-plaintext v0.x`). External dependency versions follow the same shape (`uv 0.5.x`, `gh 2.x`, `Python 3.10+`). Inline JSON/TOML example snippets where the version is the value of a typed field whose key already encodes the project name are exempt — the structural key carries the disambiguation. This convention belongs in `livespec/SPECIFICATION/non-functional-requirements.md` (and a doctor-LLM-subjective check SHOULD eventually surface bare `v\d+\.\d+\.\d+` literals as a finding).

### Motivation

Surfaced while running `/livespec:doctor` against the sibling `livespec-runtime` repo on 2026-05-25. The spec there had eight bare `v0.2.0` references that had silently gone stale after release-please cut `livespec-runtime v0.3.0`. The reader of a bare `v0.2.0` in any livespec-governed repo cannot tell whether the literal refers to the meta-tool, this library, or a sibling impl-plugin; the project-name prefix removes that ambiguity at the source. The sibling-side fix already landed (`livespec-runtime` PR #7 merged 2026-05-25); this proposal pulls the rule upstream so every livespec-governed repo inherits it.

### Proposed Changes

Add a new section `## Prose conventions` (or fold into an existing contributor-conventions section if one fits better — `Constraints` is plausible) in `SPECIFICATION/non-functional-requirements.md` with the rule body:

```markdown
## Prose conventions

- Every version reference in spec prose MUST be prefixed with the
  owning project name. Examples: `livespec v078`,
  `livespec-runtime v0.3.0`, `livespec-impl-plaintext v0.x`,
  `livespec-dev-tooling v0.5.x`. External dependency versions
  follow the same shape (`uv 0.5.x`, `gh 2.x`, `Python 3.10+`).
  Rationale: livespec-governed repos cross-reference each other
  constantly; a bare `v0.2.0` is ambiguous between the meta-tool
  and its siblings.
- Inline JSON or TOML example snippets are exempt when the
  version is the value of a typed field whose key already encodes
  the project name (e.g. `livespec-runtime.compat.pinned`,
  `[tool.uv.sources].livespec-runtime`). The structural key
  carries the disambiguation; the value stays unprefixed and is
  automated via release-please `extra-files` wiring.
- Sibling-repo specs inherit this convention. The same rule applies
  to every livespec-governed `SPECIFICATION/` tree.

A future doctor LLM-subjective check SHOULD surface bare
`v\d+\.\d+\.\d+` literals in spec prose as findings.
```

The wording above is illustrative; the maintainer is free to pick the precise heading and adjust the prose during `/livespec:revise`.

## Proposal: codify-worktree-pr-merge-cleanup-discipline-for-spec-side-changes

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Make the worktree-PR-merge-cleanup discipline EXPLICIT in the upstream `livespec` spec. Today, the cleanup side is codified (the `no-stale-worktree` doctor invariant fires `warn` when a merged-branch worktree lingers), but the PRESCRIPTIVE side — that every spec-side change MUST land via a worktree → PR → merge → cleanup cycle — is nowhere written. The discipline is practiced (multiple active `~/.claude/projects/-data-projects-livespec--claude-worktrees-*/` shims demonstrate this), just unspecified. Codifying it removes a category of agent / contributor failure mode where work is done in-place on `master` and left in a dirty state.

### Motivation

Surfaced when a sibling-repo (`livespec-runtime`) propose-change flow drifted into a dirty-state failure mode on 2026-05-25. The user's framing: "every change happens on a work tree and the work tree gets successfully processed and cleaned up once the PR is successfully landed and merged to the main line branch." Codification ensures every agent (LLM or human) running spec-side flows applies the same discipline by default rather than asking per-step "should I commit?" confirmation questions that the user has to deflect.

### Proposed Changes

Add a new section `## Workflow discipline — spec-side changes` (or fold into an existing contributor-conventions section if a better one exists) in `SPECIFICATION/non-functional-requirements.md` with the rule body:

```markdown
## Workflow discipline — spec-side changes

Every change to a livespec-governed `SPECIFICATION/` tree (this repo
and every sibling-repo `SPECIFICATION/`) MUST land via a
worktree → PR → merge → cleanup cycle. The discipline:

1. Create a fresh `git worktree` on a new branch (typically
   `<type>/<topic>` per Conventional Commits — `spec/...`,
   `docs/...`, `feat/...`, `fix/...`, etc.).
2. Do every commit inside the worktree. The primary worktree (the
   one bound to `master`) MUST NOT carry uncommitted spec-tree
   edits at any time.
3. Run `/livespec:propose-change`, `/livespec:critique`,
   `/livespec:revise`, and any doctor passes from within the
   worktree.
4. Open a PR via `gh pr create`. CI runs against the worktree
   branch.
5. Rebase-merge the PR to `master` (per the rebase-merge-only rule
   already codified for `master`).
6. After the merge lands, remove the worktree (`git worktree
   remove <path>`) and delete the local branch. The remote branch
   deletion is part of the same step (use `gh pr merge
   --delete-branch`).

The `no-stale-worktree` doctor invariant codifies the CLEANUP side
of this cycle (warning on merged-branch worktrees that linger). This
rule codifies the PRESCRIPTIVE side (every change starts on a fresh
worktree). The two together close the loop.

Direct edits to `master`, leaving uncommitted state in the primary
worktree across sessions, or asking the user per-step "should I
commit?" confirmation gates are all FORBIDDEN.

A future doctor invariant SHOULD detect master-direct uncommitted
spec-tree edits as a `warn` finding (the static phase MAY check
for untracked / modified files under `<spec-root>/` in the primary
worktree).
```

The wording above is illustrative; the maintainer is free to pick the precise heading and refine the prose during `/livespec:revise`.
