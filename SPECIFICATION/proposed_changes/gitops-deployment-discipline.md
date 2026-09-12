---
topic: gitops-deployment-discipline
author: claude-fable-5-1 (gitops-deployment-discipline C1 session, livespec-vbqmdd)
created_at: 2026-09-12T05:47:33Z
---

## Proposal: A deploy-surface member or adopter carries a GitOps-deployment agent-instruction topic, enforced by the fleet-membership obligation suite

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add one clause to SPECIFICATION/contracts.md §"Fleet agent-instruction core" requiring every member or adopter whose tree carries a host-provisioning or deploy surface to carry a GitOps-deployment agent-instruction topic — a `.ai/gitops-deployment*.md` file referenced from its root `AGENTS.md` by a read-BEFORE hook line naming deployment, Ansible, GitOps, host provisioning, `kubectl`, and ssh-to-a-fleet-host — stating the six rules of the fleet GitOps deployment discipline plus that repository's own layer map; the deploy surface is derived from the tree, never declared in a manifest key; `livespec` itself carries the fleet-canonical statement of the six rules; and the obligation is enforced by the shared fleet-membership obligation suite alongside the section's existing instruction obligations (the section's closing enforcement sentence is amended to enumerate it).

### Motivation

Epic livespec-qurhq2, child livespec-vbqmdd (C1); design and rationale in livespec `plan/gitops-deployment-discipline/research/000-failures-root-causes-and-binding-fixes-2026-09-12.md` §1–§3. On 2026-09-11/12 a session resuming plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn) ssh'd into two k3s nodes and reasoned imperatively about deploying by hand, while the provisioning README in the repository it had been editing states the control node is `vps` and playbooks run from committed source; it then edited the retired shell installers instead of the Ansible role that actually deploys the file, filed the stale role as future work although Ansible IS the apply path, and asked the maintainer to change hosts by hand. Nothing in any repository's agent instructions told the session to read the provisioning model first, so the GitOps premise was not load-bearing in its reasoning. The fix that binds is an instruction obligation on every repository that carries a deploy surface, mechanically enforced: §"Fleet agent-instruction core" already states the `AGENTS.md` / `.ai/<topic>.md` convention and enforces instruction obligations through the fleet-membership obligation suite, so this clause adds one obligation in that shape. The seven host/deploy repositories the research names are onboarded as adopters under sibling children of the epic; the canonical livespec topic is child livespec-eyjepk (C2); the conformance row `gitops-deployment-topic` in `livespec-dev-tooling` is child livespec-hsdguf (C4).

### Proposed Changes

**Change 1 — the new clause.** In SPECIFICATION/contracts.md §"Fleet agent-instruction core", insert the following paragraph immediately AFTER the paragraph that ends:

> so the destination the auto-memory redirect (§"Driver-shipped hooks") points to actually exists.

and immediately BEFORE the paragraph that begins:

> Beads-backed members MUST ship a **beads-access guard**:

The inserted paragraph, verbatim:

> A member or adopter whose tree carries a **host-provisioning or deploy surface** MUST carry a **GitOps-deployment agent-instruction topic**. A deploy surface is DERIVED from the tree by the obligation suite — never declared in a manifest key — and is present when the tree carries any of: an `ansible/` directory, a `services/` directory, an `install*.sh` script at most three directory levels deep, or a host record (a repository that describes one fleet host, named `<host>-info`). The topic is a `.ai/gitops-deployment*.md` file referenced from the root `AGENTS.md` by a **read-BEFORE hook line** — a reference bullet in the `AGENTS.md` `.ai/` convention block whose text names deployment, Ansible, GitOps, host provisioning, `kubectl`, and ssh-to-a-fleet-host as the actions the topic is to be read before — so the guidance loads before the first such action rather than after a host has been touched. The topic MUST state, in that repository's own voice, the six rules of the fleet GitOps deployment discipline: (1) the provisioning model — the control node and the committed apply and drift commands — is read before any host or infrastructure action, and ssh to a host is for read-only verification only; (2) no live host is changed by hand — "this has to be done by hand on the host" names a gap in the committed automation to fix, never a task for the maintainer and never an improvised privileged action, and a deploy is a change to git followed by the committed apply; (3) a mechanism change lands in the layer the automation APPLIES — the role or playbook that deploys the changed file — never only in a runtime artifact that layer copies; (4) a layer replaced by its successor is retired, with its pre-deletion commit cited, never maintained beside the replacement; (5) the drift report is run and read before every apply, and a green repository is never taken as proof that a host matches it; and (6) a review-gated change is a DRAFT pull request until its independent review returns NO-BLOCKERS, because a repository whose automation merges on green does not wait for a human once its checks pass. The topic MUST also carry the repository's own layer map: which committed role or playbook deploys which file, from which control node. `livespec` itself MUST carry the fleet-canonical statement of the six rules at `.ai/gitops-deployment-discipline.md`, referenced from its `AGENTS.md`, so that a member's topic MAY cite it for the rules and carry only that member's layer map and fleet facts.

**Change 2 — enumerate the obligation in the section's enforcement sentence** (clause lockstep: the closing paragraph enumerates the obligations the suite enforces, so the new obligation is added to that enumeration in the same change). In the same section, replace the sentence fragment, verbatim:

> Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the resolvability of every `AGENTS.md`-declared `.ai/<topic>.md` reference at each directory level, the beads-runtime section in beads-backed members, and the beads-access guard MUST be enforced fleet-wide

with:

> Presence of the core, the `AGENTS.md` / `.claude/CLAUDE.md` symlink shape, the resolvability of every `AGENTS.md`-declared `.ai/<topic>.md` reference at each directory level, the beads-runtime section in beads-backed members, the beads-access guard, and the GitOps-deployment topic in deploy-surface members and adopters MUST be enforced fleet-wide

The remainder of that sentence and paragraph is unchanged.

No `## ` or `### ` heading is added, changed, or removed by this finding, so it contributes no tests/heading-coverage.json co-edit (the co-edit this proposal DOES require arises from the scenario in the second finding).

## Proposal: Every Driver ships a fleet-host mutation guard denying positively-identified hand changes to fleet-managed hosts outside the sanctioned apply

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Add a REQUIRED fleet-host mutation guard to SPECIFICATION/contracts.md §"Driver-shipped hooks" as three bold clauses in the shape of the existing footgun-guard clauses — a Claude clause plus Codex and pi sibling clauses: a pre-tool-use hook on the runtime's shell tool that denies a POSITIVELY-IDENTIFIED mutating `ssh`/`scp`/`rsync`/`sftp` reach to a fleet-managed host and a cluster-mutating `kubectl`, unless the command is the sanctioned apply; read-only reaches and the drift report stay allowed; the host set is read from the provisioning inventory, never hardcoded, with a documented fallback; the deny reason routes to the repository's `.ai/gitops-deployment*.md` topic; the section's fail-open discipline applies, with a fail-closed rule for a hazard-hinted segment whose target or command head is an unresolvable shell expansion; verb-taking tools (`kubectl`, `helm`, `systemctl`, `git`, `k3s`, `crictl`, `ctr`, `docker`, `tailscale`) are judged by enumerated read-only verbs with every other verb convicted, the remote-shell mutation signals are a non-exhaustive enumeration, a remote `sudo` is a negative-space rule, sanctioning is first-command-head-only with a committed playbook being a relative in-repository path, `kubectl` and `helm` mutations are denied regardless of host, host identity is by first DNS label against inventory names, `host_vars/` stems, and declared `ansible_host` values, the fail-closed family fires only on a hinted command, unprivileged scratch under `/tmp`, `/var/tmp`, `/dev/shm`, and `$HOME` is out of scope, piped shells and `eval`, `watch`, `script -c`, and tmux payloads are inspected, local mutation on the control node is out of scope, and telemetry is one record per in-scope command that never changes a verdict. Three drift-sweep amendments keep the section self-consistent (the Claude bundle's hook count, the runtime-specific-hooks enumeration, and the pi Driver's one-extension sentence), and one `## ` scenario is added to scenarios.md with its tests/heading-coverage.json entry.

### Motivation

Epic livespec-qurhq2, child livespec-vbqmdd (C1); design in livespec `plan/gitops-deployment-discipline/research/000-failures-root-causes-and-binding-fixes-2026-09-12.md` §3 (the row for failures 1 and 4). The instruction obligation in the first finding tells an agent to read the provisioning model before touching a host; this guard is its mechanical half — the same instruction-plus-mechanism pairing the section already applies to `--no-verify` (footgun guard) and to local-memory writes (auto-memory guard). The hand reaches of the session described in the first finding's motivation were ordinary `ssh` commands from a governed session, exactly the shape a `PreToolUse` guard on the shell tool intercepts. The host set is read from the provisioning inventory because the inventory is the committed statement of which hosts the automation owns, and a hardcoded list in a hook would be the inverted-layer defect (a copy maintained beside its source) this epic exists to remove. The Claude guard is child livespec-ggs36t (C3), built in parallel and merged only after this clause ratifies; the Codex and pi sibling guards have no ledger item yet and MUST be filed as follow-ups under the epic when this proposal is accepted. The scenario is added because the propose-change authoring discipline requires load-bearing behavior to carry a `## Scenario`, and the section's own precedent — the primary-checkout Playwright guard — carries one (`## Primary-checkout Playwright calls are refused`) mapped through tests/heading-coverage.json to an integration-tier lockstep test.

### Proposed Changes

**Change 1 — the three new guard clauses.** In SPECIFICATION/contracts.md §"Driver-shipped hooks", insert the following three paragraphs immediately AFTER the paragraph that begins:

> **Codex auto-memory-write guard (required).**

and immediately BEFORE the paragraph that begins:

> Adding or removing a hook in the Driver bundle, renaming a hook surface, or changing a hook's posture (block vs. warn) requires a propose-change cycle against this section.

The inserted paragraphs, verbatim:

> **Fleet-host mutation guard (required).** The Claude Code Driver (`livespec-driver-claude`) MUST ship a `PreToolUse` hook registered on the `Bash` tool that denies a POSITIVELY-IDENTIFIED mutating reach from an agent session to a fleet-managed host, so that a live host is changed only by the committed automation and never by hand from a session — the mechanical half of rule (2) of the GitOps deployment discipline that §"Fleet agent-instruction core" requires every deploy-surface member's topic to state. The guard inspects each command segment of the shell command (every `;`, `&&`, `||`, and pipeline segment) and classifies a segment by its command head, reached through wrapper prefixes (such as `env`, `sudo`, `timeout`, `sh -c`). It MUST deny: (a) a remote reach — an `ssh`, `scp`, `rsync`, or `sftp` segment whose target is a fleet-managed host — whose remote command or transferred payload is mutating; and (b) a `kubectl` or `helm` segment carrying a verb outside that tool's read-only set, denied regardless of which host the session or the command names — a `kubectl` segment exempted ONLY by a `--dry-run` value other than `none`. For a verb-taking tool the guard decides "mutating" by NEGATIVE SPACE: for `kubectl`, `helm`, `systemctl`, `git`, `k3s`, `crictl`, `ctr`, `docker`, and `tailscale` it enumerates the tool's READ-ONLY verbs and convicts every other verb as mutating, so `kubectl apply`, `patch`, `taint`, `delete`, `cordon`, `uncordon`, `drain`, `label`, `annotate`, `edit`, `scale`, `create`, `replace`, `set`, `rollout`, and `exec` are denied because none is `get`, `describe`, or `logs` — not because a mutating list happens to name them — and a verb the tool grows later is denied until the Driver adds it to the read-only set (a Driver-side widening that needs no core spec cycle). For a remote shell the mutating signals are a NON-EXHAUSTIVE enumeration the Driver MAY widen and MUST NOT narrow below: privilege escalation (`sudo`); a write into a protected tree — `/etc`, `/usr`, `/opt`, `/var/lib`, `/srv`, `/boot` — by `install`, `tee`, `cp`, `mv`, or output redirection (`>`, `>>`, `1>`, `2>`, `>|` into a protected tree is a write); `rm`, `chmod`, `chown` on a protected tree; a package manager; any non-read-only verb of the verb-taking tools above; and a flag-judged mutation of a head whose verbs are not enumerated: `find -delete` or `-exec`, `journalctl --vacuum*`, `sed -i`, `yq -i`, `awk -i inplace`, `iptables -A`/`-D`/`-I`/`-F`, `ip … add`/`del`/`set`/`flush`/`netns exec`, `sysctl -w`/`--system`, and `dmesg -c`. A `scp` or `rsync` DOWNLOAD from a fleet host is a read, as is an `rsync --dry-run` (`-n`) upload; an `rsync --remove-source-files` from a fleet host is a mutation. A remote `sudo` is governed by a NEGATIVE-SPACE rule: it is treated as a mutation UNLESS the escalated command is on the guard's documented read-only allowlist, so an unlisted escalated command is denied rather than presumed harmless. The sanctioned set — the commands the guard MUST NOT deny — is exactly `just ansible-apply`, `just ansible-drift`, and `ansible-playbook` running a committed playbook, with or without `--check`. Sanctioning is judged on the command's FIRST command head only, so a sanctioned name appearing later in the command, as an argument, or inside a remote payload sanctions nothing. A committed playbook is a relative path within the repository: an `ansible-playbook` or `just ansible-apply` whose playbook is named by an absolute, `~`, or `..` path is NOT sanctioned unless run with `--check`, and an ad-hoc `ansible -m … -b` is NOT sanctioned. A read-only reach MUST NOT be denied: an `ssh` whose remote command only inspects state (such as `cat`, `ls`, `stat`, `systemctl status`, a `journalctl` read, `grep`) or a read-only verb of `kubectl` (`get`, `describe`, `logs`) or `helm`. Host identity: a target is a fleet-managed host when, compared case-insensitively by its first DNS label, it matches an inventory host name, a `host_vars/<host>.yml` file stem, or a DECLARED `ansible_host` value in the provisioning inventory — the governed project's own Ansible inventory when its tree carries one (a linked worktree resolves it through its primary checkout), else the fleet provisioning repository's (`livespec-dev-tooling`'s `ansible/inventory/`); the host set MUST NOT be hardcoded; a documented fallback to a named legacy host list is permitted ONLY when no inventory resolves, and the hook MUST name it as a fallback in its own documentation; and an IP address that no inventory entry declares as `ansible_host` is NOT recognized, an address held under any other variable included — a stated limit of this guard, not an omission. Payload carriers: the guard MUST inspect, for the same hazards as a direct segment, a piped shell on a fleet host (`curl … | sh`, `| bash`, `bash <<<`), an `eval` or `watch` payload, a `script -c` payload, and the operands of tmux `new-session` and `send-keys`; `echo` and `printf` operands are data even when unquoted, and a pipe from `echo`, `printf`, or a `cat` here-document is readable stdin for `sftp`, `bash`, or `ssh … bash -s` and is inspected as a payload. Stated known limits: interpreter payloads (`python3 -c …`), `sftp -b <file>` batch files, `sudo bash -s < file`, a script assembled in another language, and a loop over host names not present in the command text. Fail-closed on an unresolvable hazard: the fail-closed family — an unparseable command, an unresolvable target, an unresolvable command head, a command substitution, nesting beyond the guard's depth, and a piped shell — fires ONLY when the command is HINTED, meaning a fleet host name or a remote-reach head is present together with a mutation signal; a hinted segment whose target or command head the guard cannot resolve (`$var`, `$(…)`, `{}`) MUST be denied — the rule the Claude Driver's tmux fleet guard already applies to a `kill-server` reached through a command substitution — because a parser exhausted on a hinted command is evidence of evasion, not of safety; and an unresolvable `ssh` target whose remote payload is provably read-only is ALLOWED, because no mutation signal is present to hint it. Telemetry: the guard MUST write one telemetry record per in-scope command (every command carrying a hazard hint), for allow and deny alike, and a telemetry failure MUST NOT change a verdict. Out of scope, stated so each is a commitment rather than an omission: a LOCAL (non-remote) mutation on the control node itself, which the committed automation's own playbooks perform and which no remote reach carries; and — a SCOPE DECISION — an unprivileged user-level filesystem change on a fleet host under `/tmp`, `/var/tmp`, `/dev/shm`, or `$HOME` (a `mkdir`, `touch`, `rm`, or `ln` without privilege), because the guard protects host CONFIGURATION — the protected trees named above, services, packages, and cluster state — not scratch. The deny reason MUST route the agent to the repository's `.ai/gitops-deployment*.md` topic and MUST name the sanctioned apply as the path to take instead. The fail-open discipline of this section applies: a hook failure is a silent pass-through, and the guard acts only when it POSITIVELY identifies a mutating reach to a fleet-managed host, a cluster-mutating `kubectl`, or a hazard-hinted segment it cannot resolve — an `ssh` to a host outside the set, a `kubectl` read, and a command carrying no hazard hint all pass through. The guard is footgun-prevention, not the isolation boundary (the isolation boundary is each host's own access control together with the committed automation's control node); like the beads-access guard, its purpose is to convert a silent hand change into an actionable block that names the committed path. Like the other Driver hooks, the script implementation, its command classifier, and their tests live in the Driver repo; token sets beyond the enumerations above are detection internals tunable Driver-side per the closing paragraph of this section, and this section states the required surface and its behavioral discipline.

> **Codex fleet-host mutation guard (required).** The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the behavioral port of the Claude Driver's fleet-host mutation guard: the same mutation posture (a mutating `ssh`, `scp`, `rsync`, or `sftp` reach to a fleet-managed host; a `kubectl` or `helm` verb outside the read-only set regardless of host, `kubectl` exempted only by a `--dry-run` other than `none`; read-only verbs enumerated and every other verb convicted for the verb-taking tools), the same negative-space `sudo` rule, the same first-command-head-only sanctioned set with the committed-playbook path rule, the same read-only allowance, the same host-identity rule with the same documented fallback and the same stated limits, the same payload-carrier inspection, the same fail-closed rule for a hazard-hinted segment whose target or command head is an unresolvable shell expansion, the same one-record-per-in-scope-command telemetry that never changes a verdict, the same out-of-scope statements (local mutation on the control node; unprivileged scratch on a fleet host), and a deny reason routing to the repository's `.ai/gitops-deployment*.md` topic and naming the sanctioned apply. Like the Codex footgun guard, the implementation and its tests live in the Driver repo; this section states only the required surface and its behavioral discipline. The fail-open discipline above applies: a hook failure MUST be a silent pass-through, and the guard acts only when it POSITIVELY identifies a mutating reach to a fleet-managed host.

> **pi fleet-host mutation guard (required).** The pi Driver (`livespec-driver-pi`) MUST carry, in the same sanctioned first-party extension that registers its footgun guard's `tool_call` handler, the behavioral port of the Claude Driver's fleet-host mutation guard: the same mutation posture, the same negative-space `sudo` rule, the same first-command-head-only sanctioned set with the committed-playbook path rule, the same read-only allowance, the same host-identity rule with the same documented fallback and stated limits, the same payload-carrier inspection, the same fail-closed rule for a hazard-hinted segment whose target or command head is an unresolvable shell expansion, the same telemetry discipline, the same out-of-scope statements (local mutation on the control node; unprivileged scratch on a fleet host), and a block decision whose reason routes to the repository's `.ai/gitops-deployment*.md` topic and names the sanctioned apply. Like the pi footgun guard, the implementation and its tests live in the Driver repo; this section states only the required surface and its behavioral discipline. The fail-open discipline above applies, delivered the way the pi footgun guard delivers it: because a pi `tool_call` handler error blocks the tool by default, the guard MUST catch its own errors internally so that a failure is a silent pass-through, and it acts only when it POSITIVELY identifies a mutating reach to a fleet-managed host.

**Change 2 — the Claude bundle's hook count** (clause lockstep: the section's opening paragraph counts the bulleted Claude hooks, and this proposal adds a required Claude guard stated outside that list). In the section's opening paragraph, replace the sentence fragment, verbatim:

> The bundle carries four hooks:

with:

> The bundle carries the four hooks listed below, plus the Claude fleet-host mutation guard stated in a bold paragraph after the list:

**Change 3 — the runtime-specific-hooks enumeration** (drift sweep: the cross-Driver single-sourcing paragraph enumerates the hooks that are NOT byte-identity-bound, and the new guards are per-runtime). In the paragraph that begins "**Cross-Driver single-sourcing (no-shadow-ledger).**", replace the sentence, verbatim:

> Runtime-specific hooks — the per-runtime auto-memory guards, the Codex footgun guard, the Claude-only plan-persistence WARN hook, and the Claude-only primary-checkout Playwright guard — share behavior where their contracts say so, not bytes, and are NOT byte-identity-bound.

with:

> Runtime-specific hooks — the per-runtime auto-memory guards, the Codex and pi footgun guards, the per-runtime fleet-host mutation guards, the Claude-only plan-persistence WARN hook, and the Claude-only primary-checkout Playwright guard — share behavior where their contracts say so, not bytes, and are NOT byte-identity-bound.

(The pi footgun guard is a runtime-specific hook already ratified two paragraphs below this sentence and was absent from the enumeration; naming it is a same-sentence consistency repair, not a behavior change.)

**Change 4 — the pi Driver's one-extension sentence** (drift sweep: the pi footgun-guard clause states that guard is the ONE sanctioned first-party pi extension, and the pi fleet-host mutation guard is carried by that same extension rather than contradicting the sentence). In the paragraph that begins "**pi footgun guard (required for mutating pi automation).**", replace the sentence, verbatim:

> This guard is the ONE sanctioned first-party pi extension in the pi Driver — the eight operation bindings themselves MUST remain SKILL.md skills, never extensions — because the guard is a hook, and each Driver ships its hooks in its runtime's native hook mechanism (pi's is the extension `tool_call` event).

with:

> This guard's extension is the ONE sanctioned first-party pi extension in the pi Driver, and the pi fleet-host mutation guard below MUST be carried by that same extension rather than by a second one — the eight operation bindings themselves MUST remain SKILL.md skills, never extensions — because the guards are hooks, and each Driver ships its hooks in its runtime's native hook mechanism (pi's is the extension `tool_call` event).

**Change 5 — the scenario.** In SPECIFICATION/scenarios.md, append the following `## ` section at the end of the file, immediately AFTER the closing ``` fence of the section `## A fleet CI host is rebuilt from bare metal by the committed procedure` (currently the file's last section). The appended section, verbatim:

> ## A hand change to a fleet host is refused outside the committed apply
>
> ```gherkin
> Feature: Keep fleet hosts changed only by the committed automation
>
> Scenario: A mutating ssh to a fleet-managed host is denied and routed to the topic
>   Given a livespec-governed project whose Driver bundle carries the fleet-host mutation guard
>   And a host named in the provisioning inventory
>   When the agent's shell tool attempts an `ssh` to that host whose remote command installs a package, writes under `/etc`, or restarts a service
>   Then the Driver denies the call before it runs
>   And the denial reason names the repository's `.ai/gitops-deployment*.md` topic and the sanctioned apply
>
> Scenario: The sanctioned apply and read-only reaches pass through
>   Given the same project and host
>   When the agent runs `just ansible-apply <playbook>`, `just ansible-drift <playbook>`, or an `ssh` to that host whose remote command only inspects state
>   Then the Driver allows the call
>
> Scenario: A host outside the inventory or a command with no hazard hint passes through
>   Given an `ssh` whose target is not in the provisioning inventory, or a command carrying no remote-reach, `kubectl`, or mutation token
>   When the agent's shell tool attempts it
>   Then the Driver allows the call
>   And the guard emits no decision
>
> Scenario: A hazard-hinted reach through a shell expansion is denied
>   Given an `ssh` whose target is a shell expansion the guard cannot resolve and whose remote command escalates privilege
>   When the agent's shell tool attempts it
>   Then the Driver denies the call
>   And the denial reason names the unresolvable target as the cause
> ```

**Change 6 — the heading-coverage co-edit** (ratification mechanics: Change 5 adds one `## ` heading to scenarios.md, so the revise MUST co-edit tests/heading-coverage.json in the same `resulting_files[]`, spelled `../tests/heading-coverage.json` against the main `SPECIFICATION/` spec target). Append the following entry to the tests/heading-coverage.json array (a scenarios.md entry whose `reason` names the integration tier, as `check-heading-coverage` direction 4 requires for a scenario heading):

```json
{
  "heading": "## A hand change to a fleet host is refused outside the committed apply",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Ratifies the fleet-host mutation guard (epic livespec-qurhq2). A scenario describes end-to-end behavior, so its test MUST resolve to the integration tier or above: the mapped test is an integration-tier lockstep test in this repository asserting that the contracts.md clause, this scenario, and this coverage entry stay in step (the shape of tests.test_plugin_distribution.test_primary_checkout_playwright_guard_contract_is_ratified), while the executable deny and allow behavior is exercised by livespec-driver-claude's hook suite under livespec-ggs36t; this TODO is replaced by that test id when it lands.",
  "work_item": "livespec-qurhq2"
}
```

**Ratification note.** The revise payload's `resulting_files[]` for this proposal therefore carries three files: `contracts.md`, `scenarios.md`, and `../tests/heading-coverage.json`. No `### ` heading changes; the single `## ` heading change is the scenario in Change 5. The `Hook failure discipline` paragraph is unchanged: the new guards follow its default fail-open posture on hook failure, and their fail-closed rule for a hazard-hinted segment with an unresolvable target or command head is a POSITIVE-identification rule (the hazard hint is the identified gating condition), not a change to the hook-failure posture — the same relationship the Claude Driver's tmux fleet guard has to that paragraph.
