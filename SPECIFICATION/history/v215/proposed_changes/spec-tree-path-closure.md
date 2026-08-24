---
topic: spec-tree-path-closure
author: claude-opus-5-plan-spec-tree-manifest-and-clause-citation
created_at: 2026-08-24T00:14:43Z
---

## Proposal: Close the spec tree: an undeclared path under an explicitly-manifested spec root is a doctor failure

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Make the set of paths permitted under a spec root ratified, declared content, and make an undeclared path a doctor FAILURE that names it. Under a template that declares its `spec_files` manifest explicitly, the spec root is CLOSED over that manifest's `kind: markdown` entries — no new file kind is added, `markdown` remains the only kind, and the declared set is exact in both directions (every declared path must exist; every present path must be declared). A new `spec.md` §"Spec-tree path closure" states the rule, its explicitly refused case (a failure, never a warning and never a silence), its exact-paths-never-patterns property, its on-disk rather than git-tracked enumeration, and three visible exemptions (v1 implicit manifests, reported as `skipped`; project-root spec roots; sub-spec trees). The clause names the implementation-side check that settles it by path. The v136 clause permitting an externally-rendered image to sit undeclared INSIDE the spec root is reversed — such an image is committed outside the spec root — and the two v136-era sentences still describing the removed `diagram_source`/`diagram_rendered` mechanism are amended, so no ratified statement is left contradicting the closure.

### Motivation

Finding F6 of the cross-repo `pre-foreman-livespec-hardening` program (coordinator plan in `mi-homelab/homelab` at `plan/pre-foreman-livespec-hardening/research/001-findings-and-gates.md` §F6 and §"Gate 0"; this repo's Track-1 plan is `plan/spec-tree-manifest-and-clause-citation/`, ledger epic `livespec-r6siae`, work-item `livespec-6fhcw7`).

A `SPECIFICATION/checks/` directory was created inside the homelab consumer's spec tree by an automated bot. It appears in no template, is referenced by no ratified clause, and was authored by no human. It survived three layers:

1. The template governs `seed` only; it materializes an initial file set and then has no further authority, because nothing re-validates the tree against it afterwards.
2. The doctor static suite checks for MISSING files only. `doctor/static/template_files_present.py` computes a `missing` list and fails on that alone; there is no unexpected-path finding anywhere in the suite. CONTROL: the full 21-check static run performed before cutting that consumer's `v004` revision PASSED `template-files-present` with the directory present.
3. A later janitor guard was drafted around the shape the bot had already invented, excluding the directory from its own refusal.

The consequence is now frozen: an unratified artifact sits inside an immutable ratified `history/v004/` snapshot, because the snapshot mechanism copies whatever is under the spec root. An independent ratification review had passed the neighbouring proposal correctly, by comparing file CONTENTS — nothing in the review was scoped to the file SET. Ratification governs contents with rigour and tree shape not at all.

**This proposal partly reverses a v136 decision, and says so.** The v136 revision (`mermaid-default-scrub-rendering`) removed the `diagram_source`/`diagram_rendered` manifest kinds and the whole render-on-revise pipeline, replacing them with a whole-tree history snapshot and a single clause permitting an externally-rendered image to be committed INSIDE the spec root, undeclared, on the reasoning that the snapshot preserves it anyway. That reasoning is true about PRESERVATION and silently false about PERMISSION: the same indiscriminate snapshot that carries a permitted image also carried `SPECIFICATION/checks/` into an immutable revision. This proposal keeps every v136 deletion — no diagram kinds, no rendering, no drift check — and reverses only the in-tree-undeclared-image clause, moving such an image outside the spec root. Two lines the v136 sweep left standing (`spec.md` §"Specification model", which still offers "diagram source, diagram rendered output" as declarable kinds, and the "Canonical architecture diagram" paragraph, which asserts the removed mechanism and its removed check "remain available") are amended here; `tests/livespec/validate/test_template_config.py` already asserts the validator rejects `diagram_source`.

Two facts measured across the fleet while scoping this proposal, both of which shaped it:

- Every non-markdown file under every fleet spec root (excluding the lifecycle-owned subdirectories) is one of the homelab `checks/` files — the exact thing this rule exists to fail. The alternate-diagram in-tree image permission has never been exercised, so no consumer is broken by moving that permission outside the tree.
- The built-in `minimal` template sets `spec_root: "./"`, the project root. A closure rule that did not exempt project-root spec roots would condemn every unrelated file in the repository.

`spec.md` §"Template manifest" already names the manifest as the source of truth and already carries the extension point; what is missing is that anything re-checks the tree against it. The maintainer selected the markdown-only closed form on 2026-08-24 over two alternatives — a second `opaque` manifest kind (withdrawn after the sweep above found no demand for it), and a link-derived exemption (rejected because the permitted set would no longer be readable from the manifest alone).

### Proposed Changes

This proposal makes the set of paths permitted under a spec root ratified,
declared content, and makes an undeclared path a doctor FAILURE. It adds NO
manifest file kind: `markdown` remains the only kind, and the spec tree is
closed over exactly the manifest's markdown entries. Every clause that today
permits an undeclared committed asset inside the spec root is amended to place
that asset outside the spec root instead.

---

### 1. `SPECIFICATION/spec.md` — §"Specification model", final sentence

REPLACE this sentence (the final sentence of the paragraph beginning "A spec tree is a directory rooted at the `spec_root` path"):

> Per §"Template manifest" below, the active template MAY declare additional file kinds (markdown sub-files, diagram source, diagram rendered output) beyond the canonical NLSpec markdown set; the manifest is the source of truth for per-kind behavior across heading-coverage, LLM-context inclusion, and history-snapshot scope.

WITH:

> Per §"Template manifest" below, the active template MAY declare additional `kind: markdown` spec files beyond the canonical NLSpec markdown set; the manifest is the source of truth for which files are subject to heading-coverage and LLM-context inclusion, and — under an explicit manifest — for which paths may exist under the spec root at all (§"Spec-tree path closure"). The history snapshot captures the whole spec tree irrespective of the manifest.

### 2. `SPECIFICATION/spec.md` — §"Template manifest", the `livespec-with-diagrams` sentence

REPLACE this sentence (in the paragraph beginning "The built-in `livespec` template's manifest MUST declare only the six markdown files"):

> The separate `livespec-with-diagrams` template variant seeds these Mermaid diagram conventions and example fenced blocks into its spec files; it differs from the built-in `livespec` template only in that seeded content.

WITH:

> The separate `livespec-with-diagrams` template variant seeds these Mermaid diagram conventions and example fenced blocks into its spec files; it differs from the built-in `livespec` template in that seeded content and in declaring its `spec_files` manifest explicitly (`template_format_version: 2`), which makes a project using it subject to §"Spec-tree path closure" while the built-in `livespec` template's implicit manifest is exempt.

### 3. `SPECIFICATION/spec.md` — §"Template manifest", "Alternate diagram tools"

REPLACE this paragraph:

> **Alternate diagram tools.** If a diagram genuinely needs a tool Mermaid lacks (rare), an author MAY use an alternate tool such as PlantUML or Graphviz: render it to an image OUTSIDE livespec and commit that image alongside the markdown that references it (e.g., `![](diagrams/foo.svg)`). livespec treats such an image as an opaque committed asset — it does NOT detect, recommend, install, invoke, render, or otherwise manage any external diagram tool, and the manifest carries no diagram-specific file kinds. The committed image is preserved across revisions by the whole-tree history snapshot (see §"Lifecycle participation").

WITH:

> **Alternate diagram tools.** If a diagram genuinely needs a tool Mermaid lacks (rare), an author MAY use an alternate tool such as PlantUML or Graphviz: render it to an image OUTSIDE livespec and commit that image OUTSIDE the spec root, referencing it from the markdown by relative path (e.g., `![](../docs/diagrams/foo.svg)`). livespec treats such an image as an opaque committed asset — it does NOT detect, recommend, install, invoke, render, or otherwise manage any external diagram tool, and the manifest carries no diagram-specific file kinds. Under an explicit manifest the spec root is closed over its declared markdown files (§"Spec-tree path closure"), so an image committed INSIDE the spec root is a doctor failure, not a permitted asset; because the image lives outside the spec root, the whole-tree history snapshot does not carry it: an alternate-tool image is not revision-pinned, and a relative reference authored for the live spec file does not resolve from a `history/vNNN/` snapshot two directory levels deeper. This is the accepted cost of keeping the spec root closed over markdown alone; an author who needs old revisions to render a diagram uses Mermaid.

### 3b. `SPECIFICATION/spec.md` — §"Template manifest" → "Lifecycle participation", history-snapshots bullet

REPLACE this sentence:

> This preserves not only the manifest's markdown files but any other committed asset the markdown references (e.g., an image produced by an alternate diagram tool), so viewing an old revision in a browser renders correctly.

WITH:

> Under an explicit manifest the snapshotted set is exactly the manifest's markdown files, since the spec root is closed over them (§"Spec-tree path closure"); an externally-rendered image lives outside the spec root, is not carried by the snapshot, and does not render from an old revision.

### 4. `SPECIFICATION/spec.md` — NEW `## ` section

INSERT a new top-level section immediately AFTER the whole of §"Template manifest" (that is, after its final "Explicitly rejected alternatives" subsection) and immediately BEFORE the existing `## Lifecycle` heading:

> ## Spec-tree path closure
>
> Under an active template that declares its `spec_files` manifest explicitly (`template_format_version: 2`), that manifest is the CLOSED definition of what may exist under the spec root. Every file under the spec root MUST be declared in `spec_files` by exact spec-target-relative path, with the sole exception of the three lifecycle-owned sibling subdirectories `history/`, `proposed_changes/`, and `templates/` and everything beneath them — the same set §"Template manifest" → "Lifecycle participation" excludes from the whole-tree history snapshot, named there and reused here so the two stay in lockstep. A file present under the spec root and absent from the manifest is a doctor static `fail` naming that path. The declared set is exact in both directions: every declared path MUST exist (the presence direction, settled by `doctor-template-files-present`) and every present path MUST be declared (the closure direction, settled by the check named at the end of this section).
>
> **The refused case is a failure, and it is neither a warning nor a silence.** An undeclared file under the spec root MUST produce a `fail`-status finding that names the offending path; it MUST NOT be reported as a warning, folded into a pass, or omitted. Ratification governs the CONTENTS of the files a template materializes; without this rule it governs the SHAPE of the tree not at all, and a directory can appear with no proposal, no revise, and no finding — after which the whole-tree history snapshot freezes it into an immutable ratified revision that was never ratified.
>
> **Exact paths, never patterns.** `spec_files` keys are exact spec-target-relative paths. No glob, wildcard, prefix, or directory-recursive form is permitted as a key, and no separate pattern-based permitted-path list exists. A pattern language would let one permissive entry silently reopen the closure this section exists to establish, so the permitted set stays enumerable by reading the manifest. A directory under the spec root is therefore permitted exactly when every file it holds is declared.
>
> **Enumeration is of files on disk, not of git-tracked files.** The check enumerates what is present under the spec root, irrespective of version-control status. An untracked file is copied into `history/vNNN/` by the whole-tree snapshot exactly as a tracked one is, so a git-derived file universe would leave open the very freeze hole this section closes.
>
> **Scope.** The rule binds only where the permitted set is EXPLICITLY declared and the spec root is a dedicated tree. Three exemptions, each stated so it is a visible decision rather than an accidental gap:
>
> - **v1 templates are exempt.** A `template_format_version: 1` template has only an implicit manifest (§"Template schema versioning") derived from its seed prompt's prose rather than from a machine-readable declaration; closing the tree over a prose-derived set would make the permitted set depend on how the prompt is read, and a v1 template has no declaration form with which to settle a disagreement. For a v1 template the check MUST report `status: skipped` naming the template format version, so the exemption is surfaced on every run rather than passing silently. Migrating a template from v1 to v2 is how it opts into closure.
> - **Project-root spec roots are exempt.** A template whose `spec_root` resolves to the project root rather than to a dedicated subdirectory — the single-file shape, such as the built-in `minimal` template's `spec_root: "./"` — is exempt: there is no dedicated spec tree to close, and applying the rule would condemn every unrelated file in the repository.
> - **Sub-spec trees are exempt.** A sub-spec tree under `<main-spec-root>/templates/<name>/` carries no template manifest of its own and already sits inside a lifecycle-owned exclusion of the main tree.
>
> This clause is settled on the implementation side by `.claude-plugin/scripts/livespec/doctor/static/spec_tree_manifested.py`, which contributes check id `doctor-spec-tree-manifested` to the doctor static phase; drift between this clause and the shipped behavior is caught by that check.

### 5. `SPECIFICATION/spec.md` — §"Contract + reference implementations architecture", "Canonical architecture diagram" paragraph, final sentence

REPLACE this sentence:

> The escape-hatch `diagram_source`/`diagram_rendered` manifest mechanism and its `doctor-diagram-source-rendered-drift` static check remain available ONLY for the PlantUML diagram types Mermaid lacks first-class support for (a Mermaid syntax lint MAY be added as a CI nicety but is not a contract requirement).

WITH:

> A diagram type Mermaid lacks first-class support for follows the §"Template manifest" alternate-diagram-tools path: rendered outside livespec and committed outside the spec root (a Mermaid syntax lint MAY be added as a CI nicety but is not a contract requirement).

### 6. `SPECIFICATION/contracts.md` — §"Template manifest wire contract", declaration-object paragraph, final sentence

REPLACE this sentence:

> Diagrams are fenced Mermaid blocks authored inside markdown spec files (per `spec.md` §"Template manifest"); an alternate diagram tool's rendered image, if any, is committed as an opaque asset that the manifest does not enumerate.

WITH:

> Diagrams are fenced Mermaid blocks authored inside markdown spec files (per `spec.md` §"Template manifest"); an alternate diagram tool's rendered image, if any, is committed as an opaque asset OUTSIDE the spec root, since under an explicit manifest the spec root is closed over the manifest's markdown entries (per `spec.md` §"Spec-tree path closure"). Manifest keys are exact spec-target-relative path strings; a key MUST NOT be a glob, wildcard, prefix, or directory-recursive pattern, and no sibling pattern-based permitted-path field exists.

### 7. `SPECIFICATION/constraints.md` — §"Renderer non-vendoring"

REPLACE this sentence:

> An author who needs a diagram type Mermaid lacks (per `spec.md` §"Template manifest") renders it with an alternate tool such as PlantUML or Graphviz OUTSIDE livespec and commits the resulting image as an opaque asset.

WITH:

> An author who needs a diagram type Mermaid lacks (per `spec.md` §"Template manifest") renders it with an alternate tool such as PlantUML or Graphviz OUTSIDE livespec and commits the resulting image as an opaque asset OUTSIDE the spec root (per `spec.md` §"Spec-tree path closure").

---

### Revise co-edit required — `tests/heading-coverage.json`

Change 4 adds one `## ` heading to `SPECIFICATION/spec.md`, so the accepting
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
  result on landing. Two templates are ALREADY v2 and become closure-bound the
  moment the check ships, with no further decision: the built-in
  `livespec-with-diagrams` (whose one fleet consumer's tree equals its manifest
  exactly, so it passes) and the homelab adopter's project-local template
  (whose `SPECIFICATION/checks/` will fail — the program's intended Gate 0
  outcome, remediated on the homelab side). Whether the built-in template
  should bump — newly binding twelve fleet repos — is a separate rollout
  decision with cross-repo consequences, deliberately left to a follow-on.
- **No second manifest kind.** A kind for permitted-but-uninterpreted files was
  designed and withdrawn: a sweep of every fleet spec root found no legitimate
  non-markdown file under any of them, so the kind would have served a
  hypothetical while re-adding contract surface v136 removed and requiring
  further rules (declared-but-absent semantics) to be coherent.
- **No `SPECIFICATION/checks/` directory is introduced into any template**, and
  no executable check is placed inside any spec tree. The executable check
  lives on the implementation side and the clause cites it by path.
