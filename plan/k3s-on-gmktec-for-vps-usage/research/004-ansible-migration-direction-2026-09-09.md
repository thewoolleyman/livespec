# 004 — The Ansible migration: directive, rationale, bounds, and the stop-and-summarize gate (2026-09-09)

Created 2026-09-09 by the session that closed R4.S2/S3/S5/S6 and the drift-detector
item (fdse), at the maintainer's direction, after a conversation in which he
challenged the home-grown provisioning as a reinvention of configuration management.
Read first: `003` (the R4 design), then this. The work-item this note specifies is
**`livespec-sab5gn.4`** (P0), which now outranks every other open item under the epic.

## 1. The directive, verbatim in substance

> I do want to do the ansible migration now. Add a work item that handles migrating
> everything to ansible instead of our home-grown plumbing that reinvents ansible,
> and make that the first task of your handoff, and the highest priority to complete.
> Then when complete, I want you to stop and present me a summary of everything in
> the original goals, what we've done, and what's left.

Three consequences bind the successor: the migration comes before R4.S4/S7/S8; the
migration ends with a **mandatory stop** and a written summary against this plan's
original goals (§7); and nothing about the Kubernetes desired state moves into Ansible
(§4).

## 2. How we got here — recorded so it is not repeated

The fleet's host provisioning is a home-grown configuration-management system built by
LLM sessions across three repositories:

| Repo | What it hand-rolls |
|---|---|
| `livespec-dev-tooling` `ci-runner/k3s/phase2/` | `install-converge-unit.sh` (copy ~46 files to `/usr/local/lib/ci-runner-k3s/`, install a systemd unit), `converge-ci-stack.sh` (boot-time converge: helm/kubectl apply plus host glue such as rendering kubeconfigs), `install-node.sh` (per-node runbook with role-based `STEP_SKIP`), a dozen `install-*.sh` for host tools, observability units, storage sweep, log archive, node budgets, secret re-injection, and — as of 2026-09-08 — `verify-installed-tree.sh`, a bespoke digest drift check |
| `vps-info` `services/<name>/` | ~20 services, each an idempotent `install.sh` + README + AGENTS.md section, including the R4.S8 `gates-kubeconfig` installer (authored, unrun) |
| `fabro-hosts` `services/` | the same convention for `hp-xubuntu` |

Every one of those primitives — copy/template a file, install a unit, pin a download
by published checksum, keep it idempotent, report drift — is what Ansible provides out
of the box (`copy`, `template`, `systemd`, `get_url` with `checksum`, and
`--check --diff`). The per-change tax was measured on 2026-09-08 at roughly **3–5×**:
the drift detector was ~230 lines of shell plus tests, an installer change, a gate cycle
and a PR, where Ansible's equivalent is zero lines; the S8 installer was ~100 lines plus
docs where a role is ~20.

The sessions that built this never asked whether it should exist. The maintainer's
standing instruction — present the library option fully rather than reflexively
hand-rolling — was in front of every one of them and was not applied, because each
slice was optimized locally. The maintainer's own words: an experienced engineer "would
have asked many times if I'm reinventing the wheel." That is the failure this note
records, and the directive above is its correction.

## 3. What the long-term fleet is, and why Ansible does not interfere with it

The homelab repository's ratified `SPECIFICATION/` (v005, read at `origin/main`
`d9e1359`, 2026-09-06) defines the destination: a Git-governed **Talos/Kubernetes**
fleet — Talos on every Kubernetes server node, Hosted Omni for machine lifecycle, Flux
for workloads, control plane on AWS in `us-east-1`, a hard ceiling of ten managed
machines. **NixOS is permitted only for site gateways**; the NixOS server fleet is
retired. **That fleet is currently empty** — zero machines provisioned; the live plan
there (`fleet-substrate-boot-identity-and-network`) has its remaining children gated on
hardware that does not yet exist.

The rollout document (`docs/talos-omni-architecture-and-rollout.md`, which that repo's
AGENTS.md classifies as *input, never authority*) states the intent for the machines
this plan runs on: *"Existing Xubuntu installations remain independent and manually
managed while their workloads migrate"*; every non-Talos disk is *"protected and outside
Talos and Omni reconciliation"*; *"The PowerEdge is deliberately migrated last."* None of
`poweredge-xubuntu`, `gmktec-xubuntu`, `hp-xubuntu` or the VPS appears in the new spec.
They will run alongside the new fleet for a long time.

The maintainer asked how much Ansible would interfere with that migration; his instinct
was "no more than a home-grown approach." The assessment recorded here, which he
accepted by issuing the directive:

- **No overlap surface, structurally.** Ansible is an SSH-and-shell tool. Talos exposes
  an API and no shell, and the constraints forbid anything depending on shell access to
  a Talos node. Ansible cannot reach a Talos node even by accident.
- **Both approaches are disposable on a sunset substrate.** Nothing about host
  provisioning survives the migration — Omni replaces it. So the only question is
  cost-per-change during a long coexistence, and that is the 3–5× above.
- **One real risk, one fence.** An inventory that grows to include a Talos node, or a
  playbook managing something Flux/Omni owns, would violate the spec's "exactly one
  declared owner." The fence: the inventory is named and scoped **legacy-only** and
  never lists a Talos node.
- **The reinvention with a real migration cost is not Ansible — it is Flux.**
  `converge-ci-stack.sh` is an imperative GitOps reconciler (`helm upgrade --install`,
  `kubectl apply`, `kubectl wait`, ordering in shell). When the CI-pool role moves onto
  the Talos cluster, the Kueue queues, ARC scale sets, gate Jobs and RBAC are the
  portable asset — only if they are Flux-shaped. Keeping them as plain
  manifests/kustomizations is the durable investment, and it is independent of Ansible.

## 4. Scope bounds — what migrates and what does not

| Migrates to Ansible | Stays, unchanged in kind |
|---|---|
| File distribution to `/usr/local/lib/…`, `/usr/local/bin/…`, `/etc/…` | Kubernetes manifests, kustomizations, helm releases |
| systemd units, timers, enable/start | `kubectl apply -k` / `helm upgrade --install` invocations (Ansible or a boot unit may *call* them; the desired state lives in the manifests) |
| Pinned downloads with published checksums (kubectl, tools) | The Kueue/ARC/gates cluster objects themselves |
| Rendering kubeconfigs and other host-side files from cluster state | Anything on a Talos node (none exist; none ever targeted) |
| Per-host role switching (`install-node.sh` `STEP_SKIP`) → inventory groups/vars | Repo-side tooling that is not host plumbing (e.g. the R4.S7 `gate-remote` client in `check-pre-push`) |
| Drift reporting (`verify-installed-tree.sh` → `--check --diff`) | |

Execution model requirement: playbooks run **from committed source** — push over ssh
from a control node, or `ansible-pull` that clones fresh before running. Never a stale
installed copy of the logic on the target; that is the exact defect fdse closed
(2026-09-08: a host ran a converge script from before the gates queue existed, exited
`Result=success`, and the queue never appeared).

## 5. The phases, as filed on `livespec-sab5gn.4`

0. **Size the estate** (one session, before any role): inventory every installer /
   converge / render script and unit across the three repos per host; classify each as
   host glue (migrates), Kubernetes-declarative (stays), or dead; decide **where the
   Ansible tree lives** (recommendation: one tree, one inventory, one convention — the
   fragmentation is the point).
1. **Skeleton**: legacy-only inventory; run-from-committed-source; `ansible-lint` +
   syntax check in the owning repo's `just check`; `--check --diff` as the drift report.
   Prove it on one real change first: re-express `vps-info/services/gates-kubeconfig`
   (R4.S8, authored, unrun) as a role and apply it — that discharges S8 and sizes the
   path on a real change.
2. **CI hosts**: the host glue of `ci-runner/k3s/phase2`; keep the boot-time Kubernetes
   apply as `kubectl apply -k` of Flux-shaped kustomizations, not shell control flow.
3. **VPS and hp-xubuntu**: `vps-info/services/*`, `fabro-hosts/services/*`.
4. **Retire the shell**: delete migrated `install-*.sh`, converge host glue,
   `verify-installed-tree.sh` and their exit-test suites, citing pre-deletion SHAs;
   update each repo's AGENTS.md and docs.

Applying playbooks to the fleet hosts is authorized by the directive as the codified
mechanism: `--check --diff` first, then apply; idempotent; secrets probe-only.

## 6. R4 status at the time of the directive (baseline for the final summary)

| Slice | State |
|---|---|
| S1 `vlku` tailnet SAN | closed |
| S2 `y8em` gate-submitter credential | closed, live-exercised (`auth can-i` against the real API server) |
| S3 `ewyx` gates Kueue queue | closed and actually converged (had been closed while unconverged — the fdse defect) |
| S4 `2hno` in-cluster mirror + git daemon | open; stranded `fabro` claim, no worktree/branch/PR/process; **the sole blocker of a running delegated gate** |
| S5 `sk8f` gate Job template + renderer | closed |
| S6 `ul61` fail-instead-of-warn in a gate pod (P1) | closed, behaviourally proven |
| S7 `2u2c` gate-remote client | open, blocked on S4 only |
| S8 `livespec-sab5gn.1` VPS kubectl + kubeconfig | merged as shell, unrun; **becomes the first Ansible role (Phase 1)** |
| fdse drift detector | closed; superseded by `--check --diff` in Phase 1 |

End-to-end, 2026-09-08: a real gate Job rendered from master was admitted by Kueue on
`gates-lq`, scheduled onto `gmktec-xubuntu`, and failed closed at exactly S4's missing
daemon. The plane works up to the one unbuilt component.

## 7. The mandatory stop

When Phase 4 lands, the session **stops** and presents the maintainer a summary of the
plan's **original goals** — join `gmktec-xubuntu` to the poweredge k3s cluster; delegate
the VPS pre-push gate to cluster Jobs; grow the CI pool past poweredge's CPU ceiling —
against what has been done (§6 plus the migration) and what is left (S4, S7, and the
capacity-derivation work R5 the R3 taint defers to). No R4 work resumes before that
report is delivered. This is the maintainer's explicit instruction, not a courtesy.
