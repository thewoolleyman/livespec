---
topic: operator-authored-git-commits
author: codex
created_at: 2026-09-10T14:23:50Z
---

## Proposal: Fail-closed operator authorship for Git work

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Introduce an opt-in governed-project declaration of the operator's exact Git author identity, strengthen agent-path authorship from advisory guidance to a fail-closed invariant for operator-owned work, preserve explicitly mechanical bot and genuine third-party attribution, bind the livespec fleet to Chad Woolley <thewoolleyman@gmail.com>, and add end-to-end scenario coverage.

### Motivation

The fix-git-email audit found that correcting global and repository Git config is insufficient: long-lived environments can override config, Red-Green-Replay preserves the initially selected author, Fabro defaults to Fabro <noreply@fabro.sh>, sandbox fallbacks have authored real work as E2E Test, and low-level commit paths can bypass ordinary hooks. Across 28 owned non-fork repositories, thousands of Chad-directed commits therefore carry obsolete, fixture, host-local, or tool identities. The contract currently says only that agent-path authorship SHOULD be preserved via Git config, which neither defines the intended identity nor requires fail-closed enforcement.

### Proposed Changes

Amend `SPECIFICATION/contracts.md` to define an optional core-owned top-level `.livespec.jsonc` object named `git_author`. When present, it MUST contain non-empty string fields `operator_name` and `operator_email`; it MAY contain `mechanical_authors`, an array of objects each containing the exact non-empty `name` and `email` pair of an autonomous job that is permitted to author exclusively mechanical changes. Unknown fields within `git_author` or a `mechanical_authors` entry MUST be rejected by config validation. Absence preserves the current behavior for a governed project that has not opted in; presence activates the author-policy obligations below. Every livespec fleet member MUST opt in, and the livespec fleet's declarations MUST use exactly `operator_name: Chad Woolley` and `operator_email: thewoolleyman@gmail.com`.

Replace the advisory final sentence of `SPECIFICATION/non-functional-requirements.md`'s **GitHub automation credential** rule and add an adjacent **Operator Git authorship** rule. For every new commit containing operator-owned feature, fix, documentation, specification, planning, test, or maintenance work and produced through an interactive coding-agent, standalone-agent, Dispatcher, Fabro, pre-commit, Red-Green-Replay, amend, rebase, cherry-pick, or low-level commit path in an opted-in repository, the Git author MUST equal the declared `operator_name` and `operator_email` byte-for-byte. An agent identity MAY appear in a `Co-Authored-By` trailer. A GitHub App, token owner, or other transport identity MUST NOT replace the operator author; it MAY remain the committer or forge audit actor.

Define the two narrow non-operator cases. A job MAY use a pair from `mechanical_authors` only when the commit contains exclusively mechanical release, dependency-pin, backup, tripwire, or equivalent generated output; a commit containing operator-owned judgment or authored content MUST use the operator pair even when automation transports it. A genuinely third-party commit imported without operator-owned modification MUST retain its original author. Neither exception permits a tool, fixture, host-local, obsolete, or synthetic identity to author operator-owned work.

Require effective rather than config-only validation. The Installer MUST enable `user.useConfigOnly`, provision the declared operator identity into each participating clone and sandbox, and leave no plausible production fallback identity. The commit-time guard MUST evaluate the author Git will actually write, including `GIT_AUTHOR_*`, explicit author options, preserved author state during amend/replay, and repository/worktree config. It MUST refuse a conflicting operator-owned commit before creation wherever the Git hook surface can observe it. The pre-push and fleet-time Verifiers MUST inspect commits created through bypassable paths such as `commit-tree` and MUST refuse publication when a newly introduced operator-owned commit is noncanonical. Red-Green-Replay MUST validate the Red author and preserve that validated author through the Green amend; revision metadata MUST use the same effective-identity resolution or fail on disagreement.

The same Verifier MUST run at commit-time, dispatch-time, and fleet-time under the existing enforcement-in-depth pattern. Its scan scope MUST be non-empty and MUST include every published branch and tag selected by the fleet conformance inventory, rather than only the default branch. It MUST report the exact offending commit and author pair, distinguish operator-owned work from declared mechanical and preserved third-party work, and fail closed when a required classification is absent. A long-lived agent, terminal, tmux server, service, or factory process MUST be restarted after its identity source changes; changing config on disk alone MUST NOT count as reconciliation.

Add `## Operator-owned Git work retains the declared author` to `SPECIFICATION/scenarios.md`, containing at least these Gherkin scenarios: (1) an ordinary agent commit, a Red-Green-Replay commit, and a Fabro run in a configured repository all record the exact declared operator pair while their agent/App attribution remains trailer, committer, or forge metadata; (2) a conflicting environment value, explicit author, stale local/worktree config, or missing declaration causes the commit or at latest its publication to fail with an actionable diagnostic; (3) an explicitly declared mechanical release or pin job retains its bot author while a mixed or judgment-bearing automation commit cannot use that exemption; (4) an imported genuine third-party commit retains its author; and (5) the all-ref Verifier refuses an empty scan and reports a forbidden operator alias on any published branch or tag. Each scenario's normative Then clauses MUST use BCP14 language.

Because this adds an H2 behavioral scenario, the accepting revise operation MUST atomically add `../tests/heading-coverage.json` to `resulting_files[]` and append an entry with `heading` equal to `## Operator-owned Git work retains the declared author`, `spec_root` equal to `SPECIFICATION`, `spec_file` equal to `scenarios.md`, `test` equal to `TODO`, `work_item` equal to `livespec-7goynx`, and a `reason` that explicitly states integration-tier coverage is required for the end-to-end interactive, Red-Green-Replay, Fabro, mechanical-bot, third-party, and all-ref failure paths. The revise MUST also link every new behavior-clause gap id to this scenario through that entry's `clauses[]` field when the behavior-scenario-link inventory supplies those ids.
