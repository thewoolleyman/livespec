---
topic: rename-orchestrator-plugin-template-path
author: claude-opus-4-8
created_at: 2026-07-02T23:52:37Z
---

## Proposal: Rename copier-template path templates/impl-plugin/ to templates/orchestrator-plugin/

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Rename the copier-template PATH `templates/impl-plugin/` to `templates/orchestrator-plugin/` throughout the live spec, and rename the template's proper NAME ("impl-plugin copier template" / "impl-plugin scaffold") to "orchestrator-plugin copier template" / "orchestrator-plugin scaffold". This is a path-and-name rename ONLY: the repo-CLASS / role term `impl-plugin` (as in "every impl-plugin repo", "each impl-plugin's `.github/workflows/`", and the repo-class enumeration `core / enforcement-suite / impl-plugin / driver-plugin / library / console`) is deliberately kept and NOT touched.

### Motivation

The copier scaffold that every `livespec-orchestrator-*` sibling is generated from is the orchestrator-plugin scaffold; naming its directory `templates/impl-plugin/` conflates the template path with the `impl-plugin` repo-class term. Renaming only the template path and its proper name (leaving the repo-class term intact) de-conflates the two senses so the spec reads: repos of class impl-plugin, generated from the orchestrator-plugin copier template.

### Proposed Changes

Apply three literal renames across the two live spec files, touching ONLY `SPECIFICATION/contracts.md` and `SPECIFICATION/non-functional-requirements.md` (no code, directory, test, `copier.yml`, README, AGENTS, or CHANGELOG change; those are a separate slice). No `##` heading is added, removed, or renamed, so `tests/heading-coverage.json` is untouched.

1. PATH rename (every occurrence): `templates/impl-plugin/` -> `templates/orchestrator-plugin/`. This covers all 12 path occurrences in `non-functional-requirements.md` (including `livespec/templates/impl-plugin/...`, `templates/impl-plugin/.github/workflows/`, `templates/impl-plugin/canonical-slugs.yml`, and `templates/impl-plugin/justfile.jinja`); `contracts.md` carries no path occurrence.

2. NAME rename (every occurrence): `impl-plugin copier template` -> `orchestrator-plugin copier template`. This covers the two occurrences in `contracts.md` ("generated from the impl-plugin copier template" and "shipped from the impl-plugin copier template") and the one occurrence in `non-functional-requirements.md` ("carried by the impl-plugin copier template").

3. NAME rename (every occurrence): `impl-plugin scaffold` -> `orchestrator-plugin scaffold`. This covers the one occurrence in `non-functional-requirements.md` ("EXHAUSTIVE for the impl-plugin scaffold").

DELIBERATELY LEFT UNCHANGED (repo-class / role sense, NOT the template path): in `non-functional-requirements.md`, "propose-change PRs in every impl-plugin repo", "the file EXISTS in each impl-plugin's `.github/workflows/`", and the repo-class enumeration `core / enforcement-suite / impl-plugin / driver-plugin / library / console`. After the rename these three still read `impl-plugin`. Nothing under `SPECIFICATION/history/**` is edited (frozen).
