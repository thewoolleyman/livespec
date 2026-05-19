# Proposal: retire the `livespec` → `livespec-core` rename

## Motivation

v064 codified Phase E of the multi-repo-split execution plan as a rename
of `livespec` → `livespec-core` on the rationale that the `-core` suffix
distinguishes the spec-lifecycle authority from the
`livespec-impl-<X>` family of implementation plugins.

Reconsideration after Phase D landed surfaced two concerns:

1. **The `-impl-` infix in the satellite repos already encodes the
   asymmetry** the rename was meant to make explicit. `livespec-impl-
   plaintext` is unambiguously NOT-the-core regardless of whether the
   core is named `livespec` or `livespec-core`; the rename is mostly
   aesthetic given that distinction.
2. **Renaming vacates the `livespec` plugin / marketplace name**, which
   leaves the name available for anyone else to publish an unrelated
   plugin under. The cleanest defense against that is for the canonical
   project to keep occupying the name. A "dormant pointer plugin"
   workaround (publishing a stub plugin under the vacated name that
   redirects to `livespec-core`) is feasible but adds maintenance cost
   and signals that the rename itself wasn't worth it.

The rename also carries concrete migration cost — slash-command
namespace migration in every consumer project, copier-answers
`_src_path` updates, `compat` block key migration (`livespec_core` →
???), URL-redirect grace-period dependency — none of which is recovered
by aesthetic improvement.

## Proposal: cancel the rename

The project keeps the name `livespec`. The Phase E branch of the
multi-repo-split execution plan is retired. All references to
`livespec-core` in the spec, copier templates, satellite-repo spec
files, satellite-repo skill prose, and configuration manifests revert
to `livespec`.

Specific renames in this revise pass:

- **Spec text (livespec/SPECIFICATION/):** every "`livespec-core`"
  occurrence becomes "`livespec`". Every "`/livespec-core:<skill>`"
  becomes "`/livespec:<skill>`". Every path reference
  "`livespec-core/SPECIFICATION/...`" becomes
  "`livespec/SPECIFICATION/...`".
- **`compat` block key:** the cross-repo coordination block's required
  semver-range key renames from `livespec_core` to `livespec`. Doctor's
  `contract-version-compatibility` invariant updates accordingly.
- **Copier template (livespec/templates/impl-plugin/):** every
  generated artifact (jinja sources + the post-render output template)
  references the upstream by the name `livespec`, not `livespec-core`.
- **Satellite-repo spec content (livespec-impl-plaintext's own
  SPECIFICATION/):** a companion revise pass in that repo applies the
  same rename across its own spec tree, SKILL.md files, `.livespec.jsonc`,
  `.copier-answers.yml`, and plugin manifests. The satellite's
  `compat.livespec_core` key likewise becomes `compat.livespec`.
- **Plan-doc (research/workflow-processes/
  multi-repo-split-execution-plan.md):** Phase E's section is rewritten
  to "Phase E retired" with a short note explaining why; the
  session-start prompt's `li-9l5` reference (Phase E epic) is updated
  to reflect the retirement; the dependency graph at the bottom drops
  the Phase E node.
- **Beads invariants — `Phase E` epic (`li-9l5`):** closed (in the
  migrated work-items.jsonl) with resolution `wontfix` and reason
  "rename retired per proposed change retire-livespec-core-rename".

## Out-of-scope

- The post-D.10 spec drift around `.beads/` / `bd` / "Beads invariants"
  in non-functional-requirements.md (mentioned in the cutover commit
  message) is its own follow-up propose-change, NOT bundled here.
- Plugin distribution mechanics (the GitHub-marketplace shape) are
  unchanged — install commands stay
  `/plugin marketplace add thewoolleyman/livespec` and
  `/plugin install livespec@livespec`.
- The nine-skill surface, Spec Reader API, JSONL record schemas, and
  pin-and-bump mechanism are unchanged in shape; only the project name
  used to refer to them changes.

## Acceptance

- Every `livespec-core` reference in live spec, copier template, plan
  doc, and satellite-repo spec is gone (history snapshots before this
  revision retain their original text).
- `just check` is green across both repos.
- The copier template's generated artifacts no longer reference
  `livespec-core`.
- The `compat` block's required key is `livespec` (not `livespec_core`)
  in spec text and example JSONC excerpts.
- `tests/heading-coverage.json` entries with `livespec-core` in the
  `heading` field are updated to the new heading text.
- The plan-doc's session-start prompt no longer lists `li-9l5` (Phase E
  epic) as an actionable item; the work-item itself closes as `wontfix`
  in `work-items.jsonl`.
