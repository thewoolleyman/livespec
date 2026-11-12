---
topic: driver-fleet-route-guard
author: claude-fable-5-2:homelab-k8s-worker-nodes
created_at: 2026-11-12T19:21:39Z
---

## Proposal: Admit the fleet route guard to the Driver hook bundle, with required Codex and pi ports

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Admit a fifth guard, the fleet route guard, to the Driver hook bundle in SPECIFICATION/contracts.md §"Driver-shipped hooks", and state its behavioural discipline and posture in core. The guard refuses a `tailscale ssh` to a machine the tailnet record documents with no Tailscale SSH server, and an `ssh`, `scp`, `rsync` or `sftp` to a recorded machine under an account other than the documented one. Each refusal names the documented command or account and the record. The guard is advisory and fail-open. The proposal requires behavioural ports in the Codex and pi Drivers, and adds one scenario section to scenarios.md.

### Motivation

Origin. Maintainer direction, 2026-11-12, relayed through plan homelab-k8s-worker-nodes (livespec-dev-tooling epic livespec-dev-tooling-ko26ez): "update the hooks to catch this, do it now as part of your plan". Work item livespec-driver-claude-bmacrp carries the Claude implementation. The companion Driver proposal is livespec-driver-claude#1068 (topic `fleet-route-guard-refuse-tailscale`). The coordinator ruled on 2026-11-12 that core ratifies first and #1068's revise follows.

What happened. On 2026-11-12 a session on the VPS ran `ssh macbook-m4-max` and `tailscale ssh cwoolley@macbook-m4-max`. The first logs in under the VPS's own account name, which is not an account on that Mac. The second fails with "No ED25519 host key is known ... strict checking", because the macOS GUI Tailscale client cannot host a Tailscale SSH server. The session recorded "NO agent route to the macbook-m4-max host exists", a coordinator carried the ask to the maintainer, and a host-side plan step sat blocked for about eight hours. The working route, `ssh cwoolley@macbook-m4-max.perch-rudd.ts.net`, was in the `tailscale-admin` repository's machine table throughout. The maintainer rejected a managed `~/.ssh/config` as the fix ("We are not going to maintain manual ssh auth"), so a guard has to teach the right command at the moment the wrong one is typed.

Why this needs a core cycle. This section closes with: "Adding or removing a hook in the Driver bundle, renaming a hook surface, or changing a hook's posture (block vs. warn) requires a propose-change cycle against this section." It also owns the hooks' behavioural disciplines and postures; the Driver repositories hold the implementations. So the guard's discipline belongs here, and the Driver's spec realizes it.

Why a separate guard. The fleet-host mutation guard "acts only on a POSITIVE identification of one of the denials stated above", and "A read-only reach MUST NOT be denied". A wrong-route `ssh host true` is a read-only reach, so the mutation guard cannot refuse it. The mutation guard is also a declared fail-closed guard whose reason names the GitOps deployment discipline. A wrong route is not a hand change, and this rule is advisory. So it is a separate guard with its own reason and the default fail-open posture.

Relation to livespec-driver-claude#1068. The behaviour stated here is the same as #1068's Driver paragraph: both rules, the order in which the effective login account is read, the allowed cases, the record named in every refusal, the fail-open cases, the pass-through outside a governed project, and the no-hardcoding rule. Once core states the discipline, #1068's paragraph realizes it. #1068 adds a sentence calling the fleet route guard "the one hook whose discipline this section states itself"; with this proposal ratified first, that sentence is no longer true and should be adjusted at #1068's revise. This proposal does not edit #1068.

Position on Codex and pi ports: required. A wrong SSH route is typed the same way from any agent runtime, and the cost (a false "no route" finding carried to the maintainer) is the same. Core already treats the nearest precedent that way: "The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the behavioral port of the Claude Driver's fleet-host mutation guard", and "The pi Driver (`livespec-driver-pi`) MUST carry, in the same sanctioned first-party extension that registers its footgun guard's `tool_call` handler, the behavioral port of the Claude Driver's fleet-host mutation guard". The ports share behaviour, not bytes, as the single-sourcing paragraph says of runtime-specific hooks. If ratified, this creates three pieces of follow-on work, none filed by this proposal: a Codex port item in the livespec-driver-codex tenant, a pi port item in the livespec-driver-pi tenant, and a livespec item owning the integration-tier test for the new scenario heading. livespec-driver-claude-bmacrp already owns the Claude guard. Each Driver's own specification states its bundle wiring through its own propose-change cycle, as #1068 does for Claude.

Scope notes. The guard claims no exception to the rule that hooks MUST NOT disturb non-livespec projects, so it passes through outside a governed project; the tailnet record is resolved as a sibling of the governed project, which fits. The clause names no machine, account or tailnet; the guard reads them from the record. The machine name in the scenarios is an example. Three guards the Claude bundle already ships (`github_rate_limit_guard.py`, `tmux_fleet_guard.py`, `block_raw_bd_create.py`) are named in neither this section nor the Driver's; that drift is out of this proposal's scope.

In-flight survey, 2026-11-12: the open spec pull requests livespec#3189 and livespec#3190 and the two pending proposals (`gitops-deployment-topic`, `orchestrator-roll-currency-exception`) do not change §"Driver-shipped hooks". `gitops-deployment-topic` only cites it. This proposal is compatible with all four.

### Proposed Changes

All clause changes are in `SPECIFICATION/contracts.md` §"Driver-shipped hooks". The hook failure discipline paragraph is unchanged: the fleet route guard is an ordinary fail-open hook and is not an exception to the non-livespec-project rule.

**Change 1.** In the section's opening paragraph, replace

> The bundle carries the four hooks listed below, plus the Claude fleet-host mutation guard stated in a bold paragraph after the list:

with:

> The bundle carries the four hooks listed below, plus the Claude fleet-host mutation guard and the Claude fleet route guard, each stated in a bold paragraph after the list:

**Change 2.** In the "Cross-Driver single-sourcing (no-shadow-ledger)" paragraph, replace

> Runtime-specific hooks — the per-runtime auto-memory guards, the Codex and pi footgun guards, the per-runtime fleet-host mutation guards, the Claude-only plan-persistence WARN hook, and the Claude-only primary-checkout Playwright guard —

with:

> Runtime-specific hooks — the per-runtime auto-memory guards, the Codex and pi footgun guards, the per-runtime fleet-host mutation guards, the per-runtime fleet route guards, the Claude-only plan-persistence WARN hook, and the Claude-only primary-checkout Playwright guard —

**Change 3.** In the "pi footgun guard" paragraph, replace

> This guard's extension is the ONE sanctioned first-party pi extension in the pi Driver, and the pi fleet-host mutation guard below MUST be carried by that same extension rather than by a second one

with:

> This guard's extension is the ONE sanctioned first-party pi extension in the pi Driver, and the pi fleet-host mutation guard and the pi fleet route guard below MUST be carried by that same extension rather than by a second one

**Change 4.** Insert these three paragraphs after the "pi fleet-host mutation guard (required)" paragraph and before the closing paragraph that begins "Adding or removing a hook in the Driver bundle":

> **Fleet route guard (required).** The Claude Code Driver (`livespec-driver-claude`) MUST ship a `PreToolUse` guard on the `Bash` tool that refuses a POSITIVELY-IDENTIFIED wrong SSH route to a tailnet machine before the command runs, and names the documented route. It is a separate guard from the fleet-host mutation guard: it has its own refusal reason, and that reason MUST NOT present a wrong route as a hand change or name the GitOps deployment discipline. The tailnet record: the guard reads the machine table of the fleet's tailnet record, the `tailscale-admin` repository's `README.md`, which gives each machine's name, its SSH account and its SSH server. It MUST resolve that repository as a sibling clone of the governed project, or of the primary checkout when the session runs in a linked worktree. The guard MUST NOT hardcode any machine name, account name, tailnet name or tailnet domain; it MUST read each from the record. A recorded machine is a command target that equals, in full or by its first DNS label compared case-insensitively, a machine name in the table, and whose row gives the documented SSH account and SSH server the rule in question needs. Rule 1: the guard MUST deny a `tailscale ssh` whose target is a recorded machine that the record documents with no Tailscale SSH server, and the refusal reason MUST name the working command, `ssh <documented account>@<host>.<tailnet domain>`, filled in from the record. Rule 2: the guard MUST deny an `ssh`, `scp`, `rsync` or `sftp` to a recorded machine whose effective login account differs from the SSH account the record documents for that machine, and the refusal reason MUST name the documented account. The effective login account MUST be read from an explicit `user@` on the target, else from `-l <user>`, else from the SSH client's own resolved configuration for that host (the `user` that `ssh -G <host>` prints locally, without connecting), so a host that the caller's SSH configuration already maps to the documented account MUST be allowed. A command that reaches a recorded machine with its documented account and method MUST NOT be denied by this guard, and a command whose target is not a recorded machine MUST NOT be denied by this guard. Every refusal reason of this guard MUST name the tailnet record as the place where each machine's SSH account and SSH server are documented. Posture: the guard is advisory and follows the default fail-open discipline above. It acts only on a POSITIVE identification of rule 1 or rule 2, and it MUST allow a command it cannot parse, a command whose effective login account it cannot determine, and a target whose record entry it cannot classify. When the tailnet record cannot be read (the sibling clone is absent, the file is unreadable, or no machine table can be read from it), the guard MUST deny nothing, and its verdict record for the command MUST state that no record answered; a failure to write a verdict record MUST NOT change a verdict. The guard is not an exception to this section's rule that hooks MUST NOT disturb non-livespec projects: it MUST pass through when the project is not livespec-governed. Like the other Driver hooks, the implementation and its tests live in the Driver repo. How the guard reads a command (segments, wrapper prefixes, option grammar) and how it classifies the wording of an SSH server entry are Driver-side detection internals the Driver tunes per the closing paragraph of this section, provided the denials, allowances and posture stated here hold.
>
> **Codex fleet route guard (required).** The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the behavioral port of the Claude Driver's fleet route guard: the same tailnet record and sibling-clone resolution, the same no-hardcoding rule, the same recorded-machine rule, the same two denials with the same required content of each refusal reason, the same order for reading the effective login account, the same allowances, the same naming of the tailnet record in every refusal, the same pass-through outside a livespec-governed project, and the same advisory fail-open posture, including the unreadable-record case and its verdict record. A hook failure MUST be a silent pass-through, and the guard acts only on a POSITIVE identification of one of the Claude guard's two denials. Like the Codex footgun guard, the implementation and its tests live in the Driver repo, and its detection internals are Driver-side as for the Claude guard.
>
> **pi fleet route guard (required).** The pi Driver (`livespec-driver-pi`) MUST carry, in the same sanctioned first-party extension that registers its footgun guard's `tool_call` handler, the behavioral port of the Claude Driver's fleet route guard: the same tailnet record and sibling-clone resolution, the same no-hardcoding rule, the same recorded-machine rule, the same two denials (as pi block decisions) with the same required content of each reason, the same order for reading the effective login account, the same allowances, the same naming of the tailnet record in every refusal, the same pass-through outside a livespec-governed project, and the same advisory fail-open posture, including the unreadable-record case and its verdict record. Because a pi `tool_call` handler error blocks the tool by default, the guard MUST catch its own errors internally and pass the call through, as the pi footgun guard does. Like the pi footgun guard, the implementation and its tests live in the Driver repo, and its detection internals are Driver-side as for the Claude guard.

**Change 5.** In `SPECIFICATION/scenarios.md`, add this section after the section "## A hand change to a fleet host is refused outside the committed apply". The machine, account and domain in it are examples read from the record, not rules.

## A wrong SSH route to a tailnet machine is refused with the documented one

```gherkin
Feature: Teach the documented route to a tailnet machine when a wrong one is typed

Scenario: A tailscale ssh to a machine with no Tailscale SSH server is refused with the working command
  Given a livespec-governed project whose Driver bundle carries the fleet route guard
  And a tailnet record that documents machine `macbook-m4-max` with SSH account `cwoolley` and no Tailscale SSH server
  When the agent's shell tool attempts `tailscale ssh cwoolley@macbook-m4-max true`
  Then the Driver denies the call before it runs
  And the denial reason names the working command `ssh cwoolley@macbook-m4-max.perch-rudd.ts.net`
  And the denial reason names the tailnet record as the place where each machine's SSH account and SSH server are documented

Scenario: An ssh under the wrong account is refused with the documented account
  Given the same project and record
  And the caller's SSH configuration resolves the login account for that machine to `ubuntu`
  When the agent's shell tool attempts `ssh macbook-m4-max true`
  Then the Driver denies the call before it runs
  And the denial reason names the documented account `cwoolley` and the tailnet record

Scenario: The documented account and method pass through
  Given the same project and record
  When the agent's shell tool attempts `ssh cwoolley@macbook-m4-max.perch-rudd.ts.net true`
  Then the Driver allows the call

Scenario: A host the caller's SSH configuration maps to the documented account passes through
  Given the same project and record
  And the caller's SSH configuration resolves the login account for that machine to `cwoolley`
  When the agent's shell tool attempts `ssh macbook-m4-max true`
  Then the Driver allows the call

Scenario: An unreadable tailnet record denies nothing and is recorded
  Given a livespec-governed project whose Driver bundle carries the fleet route guard
  And a tailnet record that cannot be read
  When the agent's shell tool attempts `tailscale ssh cwoolley@macbook-m4-max true`
  Then the Driver allows the call
  And the guard's verdict record for the call states that no record answered
```

**Co-edit owed at revise.** This proposal adds one `## ` heading to `scenarios.md`. The revise that accepts it MUST add one `tests/heading-coverage.json` entry for that heading in the same commit (`spec_file: "scenarios.md"`, `test: "TODO"`, a `work_item` key naming the open livespec item that owes the test, and a `reason` that names the integration tier and that item), and MUST regenerate `tests/heading-coverage-debt.json`. No other `## ` heading is added, changed or removed.
