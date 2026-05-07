---
topic: claude-opus-critique
author: claude-opus
created_at: 2026-05-07T07:31:46Z
---

## Proposal: contracts.md line 93 forbids zero-.py subsetting in pre-push and CI; must be inverted

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The rule in `SPECIFICATION/contracts.md` §'Pre-commit step ordering' line 93 currently states: 'Pre-push and CI never apply this subsetting — the full aggregate is the load-bearing safety net for any branch landing on master.' This rule is contradictory to the operational goal: when a commit/PR contains zero `.py` files, the ~28 Python-code checks have no work to do, yet the rule MANDATES they run regardless. The skip is wired only into `just check-pre-commit`; `just check` (used by pre-push line 49 of `lefthook.yml`) and the CI matrix in `.github/workflows/ci.yml` lines 47-73 invoke Python-code checks unconditionally even when the changeset has no `.py` files.

### Motivation

The current rule is silent on the cost/benefit asymmetry: running ~28 Python checks against a doc-only changeset is expensive, irrelevant, and produces no signal — every check passes trivially because there is no Python delta. The rule is internally inconsistent with `check-pre-commit-doc-only` (which already encodes the doc-only safe subset of 5 metadata-only checks). The 'load-bearing safety net' framing is unclear about what the safety net protects against on a doc-only changeset; if a PR touches only `*.md` files, no Python check can possibly fail-due-to-the-PR (only fail-due-to-pre-existing-master-state, which is a master-CI-green concern, not a per-PR concern). The contradiction between the existing pre-commit subsetting and the prohibition on pre-push/CI subsetting needs to be resolved.

### Proposed Changes

REPLACE the final sentence of `SPECIFICATION/contracts.md` line 93 — currently 'Pre-push and CI never apply this subsetting — the full aggregate is the load-bearing safety net for any branch landing on master.' — with the following:

'Pre-push and CI MUST apply the same zero-`.py` subsetting predicate as pre-commit. (a) Pre-push delegates to a new `just check-pre-push` recipe (mirroring `check-pre-commit`) that computes the changeset via `git diff --name-only @{upstream}..HEAD` (falling back to `git diff --name-only origin/master..HEAD` when no upstream is configured); when zero `.py` paths appear in the diff, the recipe delegates to `check-pre-commit-doc-only`; otherwise it delegates to `just check`. (b) CI in `.github/workflows/ci.yml` MUST add a `setup` job that runs `git diff --name-only origin/${{ github.base_ref }}...HEAD` for `pull_request` events (and outputs `py_changed=true` for `push` and `merge_group` events unconditionally, since master/merge-queue must always run the full safety net), exposes `outputs.py_changed`, and the Python-code matrix entries gate on `if: needs.setup.outputs.py_changed == ''true''`. The repo-metadata matrix entries (`check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`) MUST run unconditionally in CI to preserve the metadata safety net. (c) The lefthook `pre-push` stanza in `lefthook.yml` MUST be updated from `run: just check` to `run: just check-pre-push`. (d) The categorization of every `just check` target into either `python-code-checks` or `repo-metadata-checks` MUST be codified in `python-skill-script-style-requirements.md` §"Enforcement suite — Canonical target list" so the two subsets stay synchronized between justfile, lefthook, and CI without drift. The repo-metadata subset is exactly the current `check-pre-commit-doc-only` body: `check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`. Every other target in `just check` is a python-code check.'

ADDITIONALLY, ADD a paragraph after the modified paragraph clarifying the safety-net invariant: 'The zero-`.py` subsetting is sound because the Python-code checks are deterministic functions of the Python source tree; with no `.py` delta in the changeset, every Python-code check would pass-or-fail identically against the merge-base, and any pre-existing failure is a master-branch-state concern (covered by `check-master-ci-green`), not a per-PR concern. Master-branch CI runs (`push` to `master`, `merge_group`) MUST still run the full aggregate as the merge-queue safety net.'
