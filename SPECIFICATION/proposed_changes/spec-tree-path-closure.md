---
topic: spec-tree-path-closure
author: claude-opus-5-plan-spec-tree-manifest-and-clause-citation
created_at: 2026-08-24T00:14:43Z
---

## Proposal: Close the spec tree: an undeclared path under a spec root is a doctor failure, and permitted non-spec files are declared as a second manifest kind

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Make the set of paths permitted under a spec root ratified, declared content, and make an undeclared path a doctor FAILURE that names it. The `spec_files` manifest gains a second file kind, `opaque` — a file livespec permits under the spec root but does not interpret (no markdown-shaped checks, no LLM-context inclusion, no parsing or rendering) — so the two cases the current text blesses by leaving them undeclared (an alternate diagram tool's rendered image; a non-spec companion file such as a per-directory agent-instruction file) acquire a declaration form instead of an exemption. A new `spec.md` §"Spec-tree path closure" states the rule, its explicitly refused case (a failure, never a warning and never a silence), its exact-paths-never-patterns property, its on-disk rather than git-tracked enumeration, and three visible exemptions (v1 implicit manifests, project-root spec roots, sub-spec trees). The clause names the implementation-side check that settles it by path. The `contracts.md` wire contract and the `constraints.md` renderer clause are amended in the same pass so no ratified statement is left asserting that the manifest does not enumerate such a file.

### Motivation

Finding F6 of the cross-repo `pre-foreman-livespec-hardening` program (coordinator plan in `mi-homelab/homelab` at `plan/pre-foreman-livespec-hardening/research/001-findings-and-gates.md` §F6 and §"Gate 0"; this repo's Track-1 plan is `plan/spec-tree-manifest-and-clause-citation/`, ledger epic `livespec-r6siae`, work-item `livespec-6fhcw7`).

A `SPECIFICATION/checks/` directory was created inside the homelab consumer's spec tree by an automated bot. It appears in no template, is referenced by no ratified clause, and was authored by no human. It survived three layers:

1. The template governs `seed` only; it materializes an initial file set and then has no further authority, because nothing re-validates the tree against it afterwards.
2. The doctor static suite checks for MISSING files only. `doctor/static/template_files_present.py` computes a `missing` list and fails on that alone; there is no unexpected-path finding anywhere in the suite. CONTROL: the full 21-check static run performed before cutting that consumer's `v004` revision PASSED `template-files-present` with the directory present.
3. A later janitor guard was drafted around the shape the bot had already invented, excluding the directory from its own refusal.

The consequence is now frozen: an unratified artifact sits inside an immutable ratified `history/v004/` snapshot, because the snapshot mechanism copies whatever is under the spec root. An independent ratification review had passed the neighbouring proposal correctly, by comparing file CONTENTS — nothing in the review was scoped to the file SET. Ratification governs contents with rigour and tree shape not at all.

Two further cases measured in this fleet while scoping this proposal, both of which any closure rule must answer:

- `thewoolleyman/resume` carries `SPECIFICATION/AGENTS.md` — a legitimate per-directory agent-instruction file that is not spec content and that no manifest declares. A rule with no declaration form for a permitted non-spec file would break a correct repository.
- The built-in `minimal` template sets `spec_root: "./"`, the project root. A closure rule that did not exempt project-root spec roots would condemn every unrelated file in the repository.

`spec.md` §"Template manifest" already names the manifest as the source of truth and already carries the extension point; what is missing is that anything re-checks the tree against it, and a declaration form for the two cases the current text blesses by leaving them undeclared. The reconciliation mechanism — one manifest with a second `opaque` kind, exact paths only, rather than a second permitted-path list or a markdown-only tree with assets moved outside it — was selected by the maintainer on 2026-08-24 against those alternatives.

### Proposed Changes


This proposal makes the set of paths permitted under a spec root ratified,
declared content, and makes an undeclared path a doctor FAILURE. It adds one
manifest file kind (`opaque`) so the currently-blessed undeclared cases have a
declaration form, and it reconciles every clause that today asserts the
manifest does not enumerate them.

---

### 1. `SPECIFICATION/spec.md` — §"Template manifest", opening paragraph

REPLACE this paragraph:

> The active template MAY declare a `spec_files` manifest in `template.json` mapping spec-target-relative paths to per-file declarations. Each declaration MUST carry a `kind` field whose only value is `markdown`. The wire shape is codified in `contracts.md` §"Template manifest wire contract".

WITH:

> The active template MAY declare a `spec_files` manifest in `template.json` mapping spec-target-relative paths to per-file declarations. Each declaration MUST carry a `kind` field whose value is either `markdown` or `opaque`. A `kind: markdown` entry is ratified spec content: it is subject to markdown-shaped checks and is included in LLM context. A `kind: opaque` entry is a file livespec PERMITS under the spec root but does not interpret — it is excluded from markdown-shaped checks and from LLM-context inclusion, and livespec neither parses, renders, nor otherwise manages it; declaring a path `opaque` is a declaration of NON-management, and adds no diagram-source or rendered-output handling to livespec. Both kinds are captured identically by the whole-tree history snapshot. The wire shape is codified in `contracts.md` §"Template manifest wire contract".

### 2. `SPECIFICATION/spec.md` — §"Template manifest", the extension-point sentence

REPLACE this sentence (the final sentence of the paragraph beginning "The built-in `livespec` template's manifest MUST declare only the six markdown files"):

> The built-in opinion stays narrow; the manifest is the extension point that lets custom templates add markdown files without forking the entire template surface.

WITH:

> The built-in opinion stays narrow; the manifest is the extension point that lets custom templates add markdown spec files, and declare permitted non-spec companion files as `kind: opaque`, without forking the entire template surface.

### 3. `SPECIFICATION/spec.md` — §"Template manifest", "Alternate diagram tools"

REPLACE this paragraph:

> **Alternate diagram tools.** If a diagram genuinely needs a tool Mermaid lacks (rare), an author MAY use an alternate tool such as PlantUML or Graphviz: render it to an image OUTSIDE livespec and commit that image alongside the markdown that references it (e.g., `![](diagrams/foo.svg)`). livespec treats such an image as an opaque committed asset — it does NOT detect, recommend, install, invoke, render, or otherwise manage any external diagram tool, and the manifest carries no diagram-specific file kinds. The committed image is preserved across revisions by the whole-tree history snapshot (see §"Lifecycle participation").

WITH:

> **Alternate diagram tools.** If a diagram genuinely needs a tool Mermaid lacks (rare), an author MAY use an alternate tool such as PlantUML or Graphviz: render it to an image OUTSIDE livespec and commit that image alongside the markdown that references it (e.g., `![](diagrams/foo.svg)`). livespec treats such an image as an opaque committed asset — it does NOT detect, recommend, install, invoke, render, or otherwise manage any external diagram tool, and the manifest carries no diagram-specific file kinds: `opaque` is a single non-management kind, not a diagram kind. Under a template that declares `spec_files` explicitly, the committed image MUST be declared in the manifest by exact path as a `kind: opaque` entry, per §"Spec-tree path closure"; an image the manifest does not declare is a doctor failure, not a permitted asset. The committed image is preserved across revisions by the whole-tree history snapshot (see §"Lifecycle participation").

### 4. `SPECIFICATION/spec.md` — §"Template manifest" → "Lifecycle participation", lead-in

REPLACE this line:

> A `spec_files` manifest entry (always `kind: markdown`) participates in livespec's lifecycle on two axes:

WITH:

> A `spec_files` manifest entry participates in livespec's lifecycle on two axes, and its `kind` decides the first axis only:

### 5. `SPECIFICATION/spec.md` — NEW `## ` section

INSERT a new top-level section immediately AFTER the whole of §"Template manifest" (that is, after its final "Explicitly rejected alternatives" subsection) and immediately BEFORE the existing `## Lifecycle` heading:

> ## Spec-tree path closure
>
> Under an active template that declares its `spec_files` manifest explicitly (`template_format_version: 2`), that manifest is the CLOSED definition of what may exist under the spec root. Every file under the spec root MUST be declared in `spec_files` by exact spec-target-relative path, with the sole exception of the three lifecycle-owned sibling subdirectories `history/`, `proposed_changes/`, and `templates/` and everything beneath them — the same set §"Template manifest" → "Lifecycle participation" excludes from the whole-tree history snapshot, named there and reused here so the two stay in lockstep. A file present under the spec root and absent from the manifest is a doctor static `fail` naming that path.
>
> **The refused case is a failure, and it is neither a warning nor a silence.** An undeclared file under the spec root MUST produce a `fail`-status finding that names the offending path; it MUST NOT be reported as a warning, folded into a pass, or omitted. Ratification governs the CONTENTS of the files a template materializes; without this rule it governs the SHAPE of the tree not at all, and a directory can appear with no proposal, no revise, and no finding — after which the whole-tree history snapshot freezes it into an immutable ratified revision that was never ratified.
>
> **Exact paths, never patterns.** `spec_files` keys are exact spec-target-relative paths. No glob, wildcard, prefix, or directory-recursive form is permitted as a key, and no separate pattern-based permitted-path list exists. A pattern language would let one permissive entry silently reopen the closure this section exists to establish, so the permitted set stays enumerable by reading the manifest. A directory under the spec root is therefore permitted exactly when every file it holds is declared.
>
> **Enumeration is of files on disk, not of git-tracked files.** The check enumerates what is present under the spec root, irrespective of version-control status. An untracked file is copied into `history/vNNN/` by the whole-tree snapshot exactly as a tracked one is, so a git-derived file universe would leave open the very freeze hole this section closes.
>
> **Scope.** The rule binds only where the permitted set is EXPLICITLY declared and the spec root is a dedicated tree. Three exemptions, each stated so it is a visible decision rather than an accidental gap:
>
> - **v1 templates are exempt.** A `template_format_version: 1` template has an implicit manifest (§"Template schema versioning") and no way to declare a permitted companion file; closing that implicit set would forbid a legitimate file with no mechanism to permit it. For a v1 template the check MUST report `status: skipped` naming the template format version, so the exemption is surfaced on every run rather than passing silently. Migrating a template from v1 to v2 is how it opts into closure.
> - **Project-root spec roots are exempt.** A template whose `spec_root` resolves to the project root rather than to a dedicated subdirectory — the single-file shape, such as the built-in `minimal` template's `spec_root: "./"` — is exempt: there is no dedicated spec tree to close, and applying the rule would condemn every unrelated file in the repository.
> - **Sub-spec trees are exempt.** A sub-spec tree under `<main-spec-root>/templates/<name>/` carries no template manifest of its own and already sits inside a lifecycle-owned exclusion of the main tree.
>
> This clause is settled on the implementation side by `.claude-plugin/scripts/livespec/doctor/static/spec_tree_manifested.py`, which contributes check id `doctor-spec-tree-manifested` to the doctor static phase; drift between this clause and the shipped behavior is caught by that check.

### 6. `SPECIFICATION/contracts.md` — §"Template manifest wire contract", the declaration-object paragraph

REPLACE this paragraph:

> Each declaration object MUST carry `{"kind": "markdown"}` — a textual markdown spec file (subject to markdown-shaped checks and full LLM-context inclusion). `markdown` is the ONLY file kind: livespec manages no diagram-source or rendered-output kinds. Diagrams are fenced Mermaid blocks authored inside markdown spec files (per `spec.md` §"Template manifest"); an alternate diagram tool's rendered image, if any, is committed as an opaque asset that the manifest does not enumerate.

WITH:

> Each declaration object MUST carry a `kind`, and `kind` MUST be one of exactly two values. `{"kind": "markdown"}` is a textual markdown spec file, subject to markdown-shaped checks and full LLM-context inclusion. `{"kind": "opaque"}` is a file permitted under the spec root that livespec does not interpret: excluded from markdown-shaped checks and from LLM-context inclusion, never parsed, never rendered. livespec still manages no diagram-source or rendered-output kinds — `opaque` is one non-management kind, not a typed asset taxonomy, and carries no renderer, no MIME handling, and no tool detection. Diagrams are fenced Mermaid blocks authored inside markdown spec files (per `spec.md` §"Template manifest"); an alternate diagram tool's rendered image, if any, is committed under the spec root and MUST be enumerated by the manifest as a `kind: opaque` entry.
>
> Manifest keys are exact spec-target-relative path strings. A key MUST NOT be a glob, wildcard, prefix, or directory-recursive pattern, and no sibling pattern-based permitted-path field exists; the manifest is the single enumerable statement of what may exist under the spec root, per `spec.md` §"Spec-tree path closure".

### 7. `SPECIFICATION/contracts.md` — §"Template manifest wire contract", schema note

REPLACE this sentence (the opening of the section's final paragraph):

> The schema bump from v1 to v2 lands in `.claude-plugin/scripts/livespec/schemas/template_config.schema.json`; the paired dataclass under `livespec/schemas/dataclasses/template_config.py` MUST stay co-authoritative per the schema-dataclass-pairing convention (v013 M6).

WITH:

> The schema bump from v1 to v2 lands in `.claude-plugin/scripts/livespec/schemas/template_config.schema.json`, whose per-file `kind` enum MUST admit exactly `markdown` and `opaque`; the paired dataclass under `livespec/schemas/dataclasses/template_config.py` MUST stay co-authoritative per the schema-dataclass-pairing convention (v013 M6), so its `SpecFileKind` literal carries the same two values.

### 8. `SPECIFICATION/constraints.md` — §"Renderer non-vendoring"

REPLACE this sentence:

> An author who needs a diagram type Mermaid lacks (per `spec.md` §"Template manifest") renders it with an alternate tool such as PlantUML or Graphviz OUTSIDE livespec and commits the resulting image as an opaque asset.

WITH:

> An author who needs a diagram type Mermaid lacks (per `spec.md` §"Template manifest") renders it with an alternate tool such as PlantUML or Graphviz OUTSIDE livespec and commits the resulting image as an opaque asset, declared in the active template's manifest as a `kind: opaque` entry where that template declares `spec_files` explicitly (per `spec.md` §"Spec-tree path closure").

---

### Revise co-edit required — `tests/heading-coverage.json`

Change 5 adds one `## ` heading to `SPECIFICATION/spec.md`, so the accepting
revise MUST carry `../tests/heading-coverage.json` in its `resulting_files[]`
with this entry added:

```json
{
  "heading": "## Spec-tree path closure",
  "spec_root": "SPECIFICATION",
  "spec_file": "spec.md",
  "test": "TODO",
  "reason": "Ratified ahead of its executable check; work-item livespec-hipozh lands doctor-spec-tree-manifested together with its negative control (an undeclared path under a v2-manifest spec root produces a fail naming that path) and MUST replace this TODO with that test id.",
  "work_item": "livespec-hipozh"
}
```

No other `## ` heading is added, renamed, or removed by this proposal.

### Deliberately NOT in scope

- **No template is migrated from v1 to v2 here.** The built-in `livespec`
  template stays v1, so this ratification changes no fleet member's doctor
  result on landing. Whether the built-in template should bump — which would
  newly bind twelve fleet repos and require `thewoolleyman/resume` to declare
  its existing `SPECIFICATION/AGENTS.md` — is a separate rollout decision with
  cross-repo consequences, deliberately left to a follow-on.
- **No `SPECIFICATION/checks/` directory is introduced into any template**, and
  no executable check is placed inside any spec tree. The executable check
  lives on the implementation side and the clause cites it by path.

