# 000 — GitOps deployment discipline: the failures, their root causes, and the fixes that bind (2026-09-12)

Written 2026-09-12 by the session that resumed plan `k3s-on-gmktec-for-vps-usage`
(epic `livespec-sab5gn`) and landed R5. The maintainer directed this as a SEPARATE
work item to be done FIRST and FULLY LANDED before that plan continues: record the
discipline in the repos' own instructions, enforce it mechanically wherever possible,
apply it to every GitOps-managed repo, and resolve the drift that exists. A promise
made only in a chat transcript is worth nothing; this note exists so the fixes are
traceable to the failures they answer.

## 1. What failed (observed in the R5 session)

1. **Acted on production before reading the model of it.** The session ssh'd into
   `poweredge-xubuntu` and `gmktec-xubuntu` and reasoned imperatively ("no checkout
   on the hosts, so deploy is manual") while
   `livespec-dev-tooling/ansible/README.md` — in the repository it had been editing
   for hours — states the control node is `vps` and playbooks run FROM committed
   source; there is deliberately no checkout on a target.
2. **Inverted the layers.** It treated the legacy shell `install-*.sh` as live and
   the Ansible roles as staged. The reverse is true: `ansible/roles/<role>` is the
   installer ("Replaces install-reapply-unit.sh, INCLUDING its agent branch"); the
   shell installers are what the migration retired. R5 (livespec-dev-tooling PRs
   #2260/#2261) therefore changed the runtime artifacts correctly but updated only
   the DEAD installer, and by renaming the unit's placeholders left the real
   installer's `CAPACITY_PLACEHOLDER` substitution a silent no-op.
3. **Filed a critical-path defect as future work.** The stale Ansible role was
   filed as `livespec-dev-tooling-9btv` "to fix at some future cutover" — but
   Ansible IS the apply path, so it blocked the R5 converge.
4. **Asked the maintainer to change hosts by hand.** The plan's founding directive
   (goal 0) is that no live host is changed by hand; that "you deploy manually"
   looked like a reasonable option is the clearest sign the GitOps premise was not
   load-bearing in the session's reasoning.
5. **Resumed the plan without its research.** `research/004–006` and the
   `ansible/` tree defined the current provisioning model and were in the
   read-first chain; the session read handoffs and what R5 needed.
6. **Treated "PR open" as a pause point** in repositories whose `enable-auto-merge`
   job merges on green, so a PR carrying a known blocker reached master.

Independent review did not catch 2: the review brief framed the shell tree as the
target, so the reviewer inherited the blind spot (the "reviewers sharing a flawed
instrument" class `.ai/spec-proposal-review.md` already names).

## 2. Root causes (the pattern, then the structural gap)

**Behavioral pattern:** act before reading the model of the system being acted on;
once a conclusion forms, fit evidence to it rather than re-derive; under infra
uncertainty, degrade to "hand it to the human."

**Structural gap that let the hosts drift unnoticed:** Phase 3 of the Ansible
migration (`livespec-sab5gn.4`, PR 2098) built the k3s-node roles and the
`ci_pool` inventory group (`poweredge-xubuntu` server, `gmktec-xubuntu` agent), but
NO playbook targets `ci_pool`, and the two nodes have no `host_vars`. The README's
own playbook table lists only `vps`/`hp-xubuntu` playbooks. The legacy drift check
(`verify-installed-tree.sh`) was retired in favour of `just ansible-drift`, which
cannot reach a host no playbook covers. So apply and drift both skipped the k3s
nodes, and they sat at 2026-09-08 code. `research/006` §"Left over from the Ansible
migration" does not record this gap. No periodic drift report exists anywhere; drift
is detected only when an operator runs it by hand before an apply.

**Coverage gap:** the seven host/deploy repositories — `vps-info`,
`poweredge-xubuntu-info`, `gmktec-xubuntu-info`, `hp-xubuntu-info`, `fabro-hosts`,
`otel-collector`, `local-llm` — are NOT livespec-governed (no `.livespec.jsonc`, no
`.claude/CLAUDE.md` symlink, not in `.livespec-fleet-manifest.jsonc`), so neither
fleet-conformance nor the Driver's hooks reach a session opened in them. `homelab`
and `livespec-dev-tooling` are governed. `vps-info` still carries 18 legacy
service installers beside the Ansible `dev-host.yml` that replaced them — the same
inverted-layer hazard; `fabro-hosts` retired its shell (PR 17) and is the model.

## 3. The fixes — instruction + mechanism, per failure

| Failure | Instruction (recorded in repos) | Mechanical enforcement |
|---|---|---|
| 1, 4: act on hosts before reading the model; hand changes | `.ai/gitops-deployment-discipline.md` (canonical, livespec) + per-repo `.ai/gitops-deployment.md`; `AGENTS.md` line: "read BEFORE any deployment, Ansible, GitOps, host-provisioning, kubectl, or ssh-to-a-fleet-host action" | **Fleet-host mutation guard** — Driver `PreToolUse` Bash hook denying positively-identified MUTATING `ssh`/`scp`/`rsync` to a fleet-managed host, and cluster-mutating `kubectl` (`apply`, `patch`, `taint`, `delete`, `cordon`, `drain`, `label`, `edit`, `scale`), unless the command is the sanctioned apply (`just ansible-apply` / `ansible-playbook` without `--check`); read-only reaches stay allowed; reason routes to the topic; fail-open on non-identification, deny on positive identification (the footgun-guard discipline). Host set read from the inventory, not hardcoded. Spec clause in livespec `contracts.md` §"Driver-shipped hooks"; Codex/pi sibling clauses. |
| 2: inverted layers | Same topic: "a mechanism change lands in the layer the automation APPLIES; ask *which role/playbook deploys this file?*"; `.ai/spec-proposal-review.md` gains an apply-layer check for mechanism changes; `.ai/verifying-against-the-right-source.md` gains the edited-tree-vs-apply-layer entry | **`ansible_replaced_installers_retired` check** (livespec-dev-tooling `just check`/CI): for every role task declaring `# Replaces <path>`, that path MUST NOT exist. The legacy layer cannot be edited by mistake once it is gone. Requires actually retiring the replaced `phase2/*/install-*.sh` (and `vps-info`'s replaced services), citing pre-deletion SHAs. |
| 3: critical-path defect deferred | Same topic; `9btv` corrected on the ledger | Follows from the two checks above: a stale role cannot coexist with a retired installer, and an uncovered host cannot exist. |
| drift root cause: uncovered hosts, invisible drift | `ansible/README.md` playbook table complete; per-host `*-info` records point at the playbook, not `install-node.sh` | **`ansible_inventory_hosts_covered` check**: every host in `ansible/inventory/legacy.yml` appears in the `hosts:` of at least one playbook (groups resolved). **`ansible_drift` signal** in `needs-attention-internal`: run `just ansible-drift` per playbook from the control node and raise an item on any non-empty diff. |
| 5: resume without research | Plan operation prose (`livespec-orchestrator-beads-fabro` `prose/plan.md`): a strict resume reads the read-first chain's research notes before acting | — (prose is the driver of that behavior) |
| 6: PR-open as pause under auto-merge | `.ai/agent-disciplines.md`: a review-gated change is opened as a DRAFT PR until the independent review returns NO-BLOCKERS; `enable-auto-merge` repos merge on green | candidate: guard on `gh pr create` without `--draft` in a governed repo while a review is pending — recorded, not built here |
| coverage gap: ungoverned host repos | Each gets the topic + `AGENTS.md` line now | Register the seven as adopters (`.ai/adding-an-adopter.md`) so conformance and the Driver hooks reach them; a **`gitops-deployment-topic` conformance row** (committed-file obligation, applies to members/adopters whose tree carries a deploy surface — derived from the tree: `ansible/`, `services/`, `install*.sh`, or a host record — never a new manifest key) requires the topic referenced from `AGENTS.md`. |

## 4. The children, and their order

Instruction + enforcement FIRST, drift resolution under the new rules SECOND, then
the parent plan resumes.

1. **C1 livespec (spec):** `propose-change` to `contracts.md` — §"Fleet
   agent-instruction core": required GitOps-deployment topic for deploy-surface
   members/adopters; §"Driver-shipped hooks": required fleet-host mutation guard
   (Claude; Codex/pi siblings). Independent Fable review → `revise`.
2. **C2 livespec (instructions):** canonical `.ai/gitops-deployment-discipline.md`;
   `AGENTS.md` hook line; `.ai/agent-disciplines.md` index + draft-PR rule;
   `.ai/spec-proposal-review.md` apply-layer check;
   `.ai/verifying-against-the-right-source.md` entry.
3. **C3 livespec-driver-claude:** `fleet_host_guard.py` + `_host_mutation.py`
   classifier + tests (in-process `main()` + one subprocess smoke, per
   `tests/hooks/test_tmux_fleet_guard.py`) + `hooks.json` registration. Built in
   parallel with C1; merges after C1 ratifies.
4. **C4 livespec-dev-tooling (instructions + checks):** `.ai/gitops-deployment.md`
   (the layer map: roles = installers; `ci-runner/k3s/phase2` runtime artifacts =
   what roles copy; `phase0-bare-metal` = rebuild-recipe stages) + `AGENTS.md`
   line; spec clauses under §"Runner-pool node rebuild recipe" for inventory
   coverage and replaced-installer retirement; checks
   `ansible_inventory_hosts_covered` and `ansible_replaced_installers_retired`
   wired into `just check` and CI (red-green-replay applies); conformance row
   `gitops-deployment-topic` in `fleet/_contract_rows.py`.
5. **C5 livespec-dev-tooling (drift resolution):** `ansible/ci-pool.yml` with full
   parity to `install-node.sh`; `node_extended_resource` rewritten to R5's
   per-node model (facts from the committed phase0 profile, both roles install,
   unit rendered placeholder-free); new `node_status_credential`, `node_taints`,
   `agent_rejoin`, `secret_reinjection` roles; RETIRE the replaced legacy
   installers with SHAs; then `just ansible-drift ansible/ci-pool.yml` → review →
   `just ansible-apply` → verify gmktec churn-slot 12 / untainted / quotas 44 /
   agent timer armed → drift clean; drift-check the other three playbooks too.
6. **C6 livespec:** `needs-attention-internal` `ansible_drift` signal.
7. **C7 host repos** (`vps-info`, `poweredge-xubuntu-info`, `gmktec-xubuntu-info`,
   `hp-xubuntu-info`, `fabro-hosts`, `otel-collector`, `local-llm`, `homelab`):
   `.ai/gitops-deployment.md` + `AGENTS.md` line; `poweredge`/`gmktec` records
   re-pointed at `ci-pool.yml`; `vps-info` retires its replaced service installers
   (its primary carries an in-flight uncommitted `honeycomb-mcp` change — coordinate,
   never clobber).
8. **C8 livespec:** register the seven host repos as adopters so enforcement
   reaches them.
9. **C9 livespec-orchestrator-beads-fabro:** `prose/plan.md` strict-resume reads
   research.
10. **C10 hygiene:** `9btv` was filed with a raw `bd create` (status `open`, outside
    the vocabulary — the Driver's `block_raw_bd_create` documents exactly this);
    normalize it through the sanctioned intake.

## 5. Acceptance (what "fully landed" means)

- Every child merged; `just check` green in every touched repo; each spec change
  ratified after an independent NO-BLOCKERS review.
- `just ansible-drift` is clean for `ci-pool.yml`, `dev-host.yml`, `fabro-hosts.yml`
  and `gates-kubeconfig.yml`; the two k3s nodes read the post-apply state live.
- The fleet-host mutation guard is installed in the Driver and proven by its tests
  AND by one live denial of a mutating `ssh` to a fleet host from a governed session.
- No path named by a `# Replaces` line exists in `livespec-dev-tooling` or `vps-info`.
- Every inventory host is covered by a playbook (the check is armed and green).
- Every GitOps-managed repo's `AGENTS.md` routes to a `.ai/gitops-deployment*.md`.
