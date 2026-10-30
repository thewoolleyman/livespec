---
topic: hand-built-class-obligation-inventory
author: claude-bootstrap-pi-driver-wrapup
created_at: 2026-08-19T17:20:00Z
---

## Proposal: Name the per-class obligation inventory that today only the copier template carries, so hand-built classes stop inheriting a donor's omissions

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The **Obligations per repo class** rule enumerates obligations by three types (committed files, GitHub-side state, host-side state), but the committed-files list it gives is the pin/CI/answers set only. A substantial set of further committed-file obligations reaches a repo today ONLY as a side effect of being generated from the copier template — the `.ai/` seed topic plus its AGENTS.md convention block, both `CLAUDE.md` symlinks, `.claude/settings.json`, the `plan/` store, `tests/heading-coverage.json`, and the `.livespec.jsonc` `external_references` / `cross_repo_targets` keys. `TEMPLATE_BORN_CLASSES` deliberately excludes `driver-plugin`, so for that class those obligations are carried by nothing at all: a new driver is hand-built by copying a donor sibling, and inherits precisely the donor's omissions. This amendment names the inventory in the contract for classes that have no template, WITHOUT adding new asserted conformance rows (so no member goes red and the **New-obligation discipline** rule is satisfied trivially).

### Motivation

The templatization revisit condition recorded against `TEMPLATE_BORN_CLASSES` — "if a third runtime driver is created — three hand-built drivers is the templatization trigger" — has now fired: `livespec-driver-pi` is the third. Its post-bootstrap audit (plan `bootstrap-pi-driver-wrapup`, epic `livespec-driver-pi-jvvhxi`) found the failure mode is not carelessness but INHERITANCE, and produced three measured instances:

1. `livespec-driver-pi` shipped with NO `.ai/` tree, because its donor `livespec-driver-codex` has none. `check-agents-ai-references-resolve` was wired into its `just check` and CI from bootstrap and was structurally incapable of firing the whole time — it is a dangling-REFERENCE check, so a repo referencing zero `.ai/` files passes by construction. Repaired 2026-08-19.
2. The converse defect then turned up in two more repos: `livespec-overseer` and `livespec-orchestrator-beads-fabro` each shipped `.ai/` topic files that their own AGENTS.md never referenced — guidance present but unreachable from the documented entry point. Both also passed the same check. Both repaired 2026-08-19 (livespec-overseer#1242, livespec-orchestrator-beads-fabro#1585).
3. `.livespec.jsonc` `external_references` is mandated by `constraints.md` §"Allowlist mechanism" and enforced only by doctor-static; no `livespec_dev_tooling` module mentions it, and until 2026-08-19 the copier template did not either. `livespec-driver-pi` declared it correctly by luck of its seed pass rather than by any mechanism. Now documented in the template (this repo, merged), which covers template-born classes only.

The asymmetry is the point. For a template-born class these obligations are mechanised — the template ships `.ai/agent-disciplines.md`, and `tests/dev-tooling/checks/test_copier_template_smoke.py` PINS it in `_EXPECTED_FILES` citing this contract's own fleet agent-instruction requirement. For `driver-plugin` there is no template, so the same obligations are carried by a donor's example, which is exactly how an omission propagates silently between siblings. The only end-to-end inventory that ever existed is ARCHIVED plan research (`plan/archive/bootstrap-pi-driver/research/initial-research.md`); archived research is not a maintained obligation.

This is deliberately the SMALL lever. Extending `TEMPLATE_BORN_CLASSES` and the copier template to `driver-plugin` — the large lever — stays deferred, with the re-trigger "a fourth runtime driver is planned"; a maintained inventory is the cheap compensating control until then.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md, §"Fleet membership contract":

1. In the **Obligations per repo class** rule, after the existing sentence ending "...and the primary-checkout commit-refuse hooks per the **Primary-checkout commit-refuse hook** rule under §\"Workflow discipline — spec-side changes\").", append the following:

   "**Template-carried obligations for classes with no template.** Several committed-file obligations reach a template-born member as a side effect of generation rather than as an independently stated rule. For a class that is NOT in the enforcement suite's template-born set, those same obligations bind directly and MUST be satisfied by the repo's own construction: a seed `.ai/<topic>.md` guidance file AND an AGENTS.md convention block that REFERENCES it (presence and reachability are separate requirements — a `.ai/` file no AGENTS.md names is guidance the documented entry point never routes to, and neither state is detectable by a dangling-reference check); both `CLAUDE.md` symlinks (repo root and `.claude/`); a committed `.claude/settings.json`; the `plan/` store; `tests/heading-coverage.json` where the member carries a spec tree; and the `.livespec.jsonc` `external_references` and `cross_repo_targets` keys where the member's spec cites a sibling. A hand-built member is built by copying a donor sibling, so an obligation absent from the donor is absent from the new member with no signal; this list exists so the construction is checked against a maintained inventory rather than against one sibling's example.

   This paragraph adds no new asserted conformance row: it states obligations that the fleet-conformance check MAY be extended to assert later, each such extension carrying its own retrofit per the **New-obligation discipline** rule. Arming a row before its retrofit lands is what that rule forbids, and two retrofits are already known to be outstanding at the time of writing — `livespec-driver-codex` carries no `.ai/` tree, and `livespec-driver-pi` has no `CI_RUNNER_LABELS` repo variable set."

2. In the **New-obligation discipline** rule, after the existing sentence "The check's fail-fast bite is reserved for new members and regressions, so the fleet is never red by construction at the moment a rule lands.", append: "A rule that DOCUMENTS an obligation without adding an asserted conformance row carries no retrofit debt at landing time; the debt attaches to the later change that arms the row, and that change MUST carry the retrofit for every member the row would newly fail."
