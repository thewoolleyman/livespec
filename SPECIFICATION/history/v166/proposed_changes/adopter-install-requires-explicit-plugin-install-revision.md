---
proposal: adopter-install-requires-explicit-plugin-install.md
decision: modify
revised_at: 2026-07-19T06:39:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted with modifications, after the mandatory independent Fable adversarial
review returned BLOCKERS FOUND (one blocker, four non-blocking nits). Every item
is dispositioned below.

BLOCKER (fixed in this payload). The review found that contracts.md's existing
sentence "Plugin uninstall and update flows are Claude Code platform behaviors
and are not part of this contract" sits six lines below the insertion point and
would be false once the amendments say normative things about the update flow.
Narrowed it to exclude uninstall only, and to scope update mechanics as
platform-owned but constrained by the new install-verification invariant.

Evidence upgrade. The proposal was filed on circumstantial evidence. Two
independent verifications since: (a) a direct test showed a fresh project with
`enabledPlugins` alone and no explicit install yields no installed plugin;
(b) the reviewer found this is documented upstream platform behavior as of
Claude Code v2.1.195 ("A plugin that only the project's `.claude/settings.json`
enables ... doesn't load until the team member installs it"), reiterated in the
v2.1.207 changelog. The amended contract now states documented platform
behavior, not an inference.

NIT 2 (applied). "NO error is reported" was categorical and version-dependent.
On Claude Code >= 2.1.195 an interactive session surfaces a not-installed
notice; the silence the adopter experienced holds for non-interactive and
headless runs. Reworded to say exactly that, and to make the normative point
the durable one: this state MUST NOT be detected by waiting for an error.

NIT 3 (applied). Amendment 2 asserted a third-party CLI's internal resolution
rule ("resolves against the set of project-scoped install records rather than
binding to the invoking project root") from a single observation. Reworded as
observed behavior ("has been observed to act on ANOTHER project's record and
report success"). The normative consequence is identical under every candidate
mechanism, and the contract no longer claims knowledge of internals it cannot
verify.

NIT 5 (applied). contracts.md's hook-scoping sentence read as though enablement
alone gates loading. Added the paired project-scoped install requirement.

NIT 1 (deferred to work-items, NOT fixed here). Two sibling repos'
READMEs (`livespec-driver-claude`, `livespec-orchestrator-beads-fabro`) present
a bare machine-wide install as THE install path. That is pre-existing drift in
other repositories, widened but not created by this amendment; it is out of
scope for a livespec-repo PR and is being filed as per-repo work-items instead.

NIT 4 (acknowledged). The front-matter `impl_followups` description names the
installation prompt and AGENTS.md but omits README.md, which this branch also
correctly edits. Recorded here rather than rewriting immutable proposal
front-matter; the committed follow-up work covers all three files.

Split (i) deviation, recorded deliberately. The revise prose requires
load-bearing behavior to carry a `## Scenario` in scenarios.md. The
install-verification invariant is load-bearing, but scenarios.md headings are
under the heading-coverage gate, which maps every heading to a real test, and
this invariant governs Claude Code's runtime state on an adopter's host —
something livespec's own suite structurally cannot exercise. Adding a scenario
would require either a fabricated test mapping or a test that cannot run. The
invariant's executable check therefore lives in its cited reference
implementation (`ensure_plugins.py`) rather than in a Gherkin scenario. No
`## ` heading is added, changed, or removed by this pass, so no
`tests/heading-coverage.json` co-edit is owed; `just check-pre-commit-doc-only`
passes all seven targets including check-heading-coverage.

## Modifications

Five exact-string edits to SPECIFICATION/contracts.md §"Plugin distribution",
each asserted to match exactly once before application:
1. Amendment 1 as proposed, with the categorical "no error is reported" claim
   replaced by version-accurate wording (interactive notice vs. silent headless).
2. Amendment 2 as proposed, with the inferred internal-resolution mechanism
   restated as observed behavior.
3. Amendment 3 (install-verification invariant) inserted verbatim as proposed.
4. NEW, resolving the review blocker: the pre-existing "Plugin uninstall and
   update flows ... are not part of this contract" sentence narrowed so it no
   longer contradicts the amendments.
5. NEW, resolving review nit 5: the hook-scoping sentence no longer reads as
   though enablement alone gates plugin loading.

## Resulting Changes

- contracts.md
