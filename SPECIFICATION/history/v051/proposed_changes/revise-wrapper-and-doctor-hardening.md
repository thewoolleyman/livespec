---
topic: revise-wrapper-and-doctor-hardening
author: claude-opus
created_at: 2026-05-07T08:08:45Z
---

## Proposal: Add path-relativity guard to revise wrapper resulting_files

### Target specification files

- SPECIFICATION/spec.md

### Summary

The revise wrapper currently joins `resulting_files[].path` to `spec_target` via `Path /` without structural validation. When the LLM emits a path that begins with the spec-target's basename (e.g., `"SPECIFICATION/contracts.md"` against `spec_target=SPECIFICATION/`), the wrapper writes silently to `spec_target/SPECIFICATION/contracts.md` (i.e., `SPECIFICATION/SPECIFICATION/contracts.md`) and exits 0. The post-step doctor static does not detect this. Add a wrapper-side structural validation rule that rejects this class of malformed paths at the schema-validation boundary.

### Motivation

Without this guard, a path-relativity error in `resulting_files[].path` produces silent data loss: the wrapper completes successfully (exit 0), the snapshot captures byte-identical-to-prior-version content, the `proposed_changes/` files are moved into `history/`, and the audit trail is internally inconsistent (revision-files claim `decision: accept` with named resulting files, but the snapshot shows no change). Recovery requires manual rollback. This is not a hypothetical scenario — the asymmetric path semantics between `proposal_findings.target_spec_files` (project-root-relative) and `revise_input.decisions[].resulting_files[].path` (spec-target-relative) make this a high-probability LLM error mode that already occurred during a v050 cut and required two rollback cycles to recover from.

### Proposed Changes

ADD a new normative paragraph to §"Sub-command lifecycle" adjacent to the existing **`revise` lifecycle and responsibility separation** paragraph: '**`revise` resulting_files path-relativity guard.** `bin/revise.py` MUST reject any `resulting_files[].path` that is (a) absolute (begins with `/`) or (b) begins with the spec-target directory's basename followed by `/` (e.g., `SPECIFICATION/contracts.md` when `spec_target` is `SPECIFICATION/`). These shapes indicate the LLM emitted a project-root-relative path where a spec-target-relative path is required. The wrapper MUST reject via `UsageError` (exit 2) at the same validation boundary as the schema check, before any file-shaping work runs. The narrowed predicate — basename + `/` at the start of the path, not a substring match — avoids false positives for legitimate paths that contain the spec-target stem internally (e.g., a hypothetical `templates/SPECIFICATION/foo.md`). The error message MUST name the offending path and state that paths MUST be relative to `<spec-target>/` with no leading prefix.'

## Proposal: Add accept-decision-snapshot-consistency doctor static check

### Target specification files

- SPECIFICATION/spec.md

### Summary

Add a new doctor static check, `accept-decision-snapshot-consistency`, that verifies every `history/vNNN/proposed_changes/<stem>-revision.md` with `decision: accept` or `decision: modify` and a non-empty `## Resulting Changes` section produces a non-byte-identical snapshot for each named file in `vNNN/` vs `v(NNN-1)/`. The check guards against the silent-data-loss failure mode where a revision claims spec changes were applied but the snapshot is byte-identical to the prior version.

### Motivation

When a wrapper or LLM mistake causes `resulting_files[]` to silently fail to write to the working spec (e.g., a path-relativity error that lands the write at a meaningless location), the post-step doctor static still passes — the byte-identical snapshot is internally well-formed (every spec file is structurally valid, every check passes). The ONLY signal of the failure is the contradiction between the revision-file's stated decision (`accept`/`modify` with named resulting files) and the snapshot's byte-equivalence with the prior version. A static check that flags this contradiction at post-step would catch the failure immediately at revise time, before the user notices missing changes downstream. This complements the path-relativity guard (Proposal 1) as defense-in-depth: Proposal 1 catches the specific known error class at validation time; this check catches any future write-silent-failure error class regardless of root cause.

### Proposed Changes

ADD a new normative paragraph to §"Sub-command lifecycle" / §"Per-sub-spec doctor parameterization": '**`accept-decision-snapshot-consistency` doctor static check.** A new static check MUST run against every `<spec-target>/history/vNNN/` directory where `NNN >= 2`. For every `<stem>-revision.md` in `vNNN/proposed_changes/` with YAML front-matter `decision` in `{accept, modify}` AND a non-empty `## Resulting Changes` section: every spec-target-relative file path listed under `## Resulting Changes` MUST exist in both `vNNN/` and `v(NNN-1)/`, AND `vNNN/<file>` MUST NOT be byte-identical to `v(NNN-1)/<file>`. A byte-identical pair indicates the `resulting_files[]` write silently failed during the revise that cut `vNNN`. The check emits a `fail` Finding naming the inconsistent `(vNNN, file)` pair and lifts the wrapper exit to non-zero; the user is directed to roll back the cut and re-run revise. The check is exempt for `vNNN` directories that contain a `PRUNED_HISTORY.json` marker (per the existing pruned-marker exemption convention).'

## Proposal: Document path-relativity convention in every wire-contract schema

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The two schemas describing 'spec file paths' use different path-relativity conventions with no documentation: `proposal_findings.target_spec_files[]` is project-root-relative (e.g., `"SPECIFICATION/contracts.md"`); `revise_input.decisions[].resulting_files[].path` is spec-target-relative (e.g., `"contracts.md"`). Neither schema's `description` field states this explicitly. Add a contract requirement that every wire-contract schema field naming a spec file path MUST document its path-relativity convention in the field description.

### Motivation

The asymmetry is invisible to LLMs and human authors at payload-authoring time. The propose-change/critique flows establish a 'use `SPECIFICATION/foo.md`' mental model in the LLM's context that carries over verbatim to revise's `resulting_files[].path`, where it produces a silent path-mismatch error. Documenting the convention in each schema's `description` field surfaces it at the payload-authoring step: the schema is loaded by every wrapper for validation, and the description is visible to any LLM or tool that reads the schema before authoring a payload. This is the lowest-effort prevention measure of the four (description-only edits to two existing schemas) and complements the wrapper-side guard (Proposal 1) and the doctor-side check (Proposal 2) by closing the error at its origin: the LLM authoring step.

### Proposed Changes

ADD a normative paragraph to §"Skill ↔ template JSON contracts": '**Path-relativity documentation requirement.** Every wire-contract schema field that names a spec file path MUST document its path-relativity convention in the field `description`: either *project-root-relative* (e.g., `"SPECIFICATION/contracts.md"`) OR *spec-target-relative* (e.g., `"contracts.md"`). The two conventions MUST NOT be mixed within a single schema. Specifically: `proposal_findings.schema.json` `target_spec_files[]` items are project-root-relative; `revise_input.schema.json` `decisions[].resulting_files[].path` is spec-target-relative. Schema description text is the v1 enforcement surface; the description MUST appear directly on the field (not only in the surrounding human-prose contracts) so it is visible to any LLM or tool inspecting the loaded schema. A future revise cycle MAY add a doctor static check that grep-asserts every schema field whose JSON-pointer path matches `/path/i` or `/file/i` carries one of the two convention strings in its description.'

## Proposal: Revise resulting_files target file MUST already exist

### Target specification files

- SPECIFICATION/spec.md

### Summary

The revise wrapper's `resulting_files[]` application currently writes to the resolved target path with implicit parent-directory auto-creation. A malformed path (the path-relativity error from the v050 cut, or a typo in the filename, or a stale path from a renamed file) produces a NEW file at a NEW location instead of failing. Add a rule that `resulting_files[]` is for *updating existing spec files only*: the resolved target MUST already exist, and the wrapper MUST exit 3 (`PreconditionError`) when it does not.

### Motivation

Creating new spec files is a template-declaration / seed concern, not a per-revision concern. Every spec file in a working tree was authored at seed time (template-declared spec file) or by a prior revise that updated existing template-declared content; revise's `resulting_files[]` should only OVERWRITE existing content. Auto-creating new files via the `resulting_files[]` write path is overly permissive — it converts every path-typo, every renamed-file, and every wrong-spec-target into silent data loss. Combined with the path-relativity guard (Proposal 1), this provides defense-in-depth: Proposal 1 catches the 'wrong-prefix' error class at validation time (fast, precise error); this rule catches every other path-resolution error class at write time (typo, stale rename, wrong sub-spec target). Without auto-creation, my v050 path-relativity error would have failed loudly with `PreconditionError: target SPECIFICATION/SPECIFICATION/contracts.md does not exist` instead of producing a silent half-applied state.

### Proposed Changes

MODIFY the existing **`revise` lifecycle and responsibility separation** paragraph in §"Sub-command lifecycle" by extending clause (c) (the resulting_files application clause) with the following normative addition: '...the working-spec files named in those decisions' `resulting_files[]` are updated in place before the snapshot. **Every resolved `resulting_files[].path` target MUST already exist as a regular file at the path `<spec-target>/<resulting_files[i].path>` before the wrapper writes to it. A non-existent target is a `PreconditionError` (exit 3); the wrapper MUST emit a structured finding naming the missing target and abort before any write occurs. Creating new spec files via `resulting_files[]` is forbidden — new template-declared spec files are added through a future template-revision mechanism, not through revise; new sub-spec trees are added through a future seed-extension mechanism, not through revise.** When every decision is `reject`, the new version's spec files are byte-identical copies of the prior version's spec files (rejection-flow audit trail);'.
