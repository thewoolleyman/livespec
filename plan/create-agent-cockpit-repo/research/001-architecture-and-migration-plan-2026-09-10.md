# Agent cockpit repository: architecture and migration plan

Date: 2026-09-10

Plan epic: `livespec-livyxu`

Target repository: `agent-cockpit-info` (new)

Coordination repository: `livespec` only because this repository already has a
working durable plan ledger. This placement does **not** decide that the new
repository is a LiveSpec fleet member.

## Executive decision

Create `agent-cockpit-info` as a standalone, fleet-scoped GitOps repository for
all numbered Ubuntu cockpit hosts. It owns the inventory, bootstrap entrypoint,
Ansible roles, declarative repository manifest, tests, acceptance checks, and
migration/deprecation runbook for hosts named `agent-cockpit-{n}`.

Do not put these hosts into `livespec-dev-tooling/ansible`. That tree explicitly
describes the existing Ubuntu hosts as a legacy, pre-Talos sunset substrate; it
also assumes Python and passwordless sudo already exist and therefore does not
meet the bare-host bootstrap requirement. Do not create one repository per
numbered host: the cockpit is one replicated machine role with per-instance
values, not unrelated pets.

Do not make the new repository a full LiveSpec fleet member initially. The
cockpit does not fit the fleet's product/release classes, and membership would
add specification, ledger tenant, release/pin fanout, plugin conformance, and
branch-policy obligations without improving machine convergence. Reconsider a
lightweight LiveSpec adopter profile after the cockpit has passed a second-host
rebuild and has a genuinely independent governed backlog.

The repository remains standalone in operation while consuming a small set of
versioned external seams:

- `1password-env-wrapper` for the credential-loader implementation;
- `otel-collector` for the shared collector distribution and normalization;
- `tailscale-admin` for tailnet policy and administrative receipts;
- official/pinned distributions of Tailscale, Chrome, 1Password, Claude Code,
  Codex, Pi, GitHub CLI, AWS CLI, and supporting tools;
- narrowly selected shared utilities when they have a published revision and a
  stable interface.

The repository must not depend at runtime on a checkout of
`livespec-dev-tooling`, `livespec`, or the full agent-flywheel/ACFS installer.
Proven behavior may be ported, but the resulting cockpit role has one canonical
owner. Temporary duplication during migration is allowed only until the new
host is accepted and the old copies are removed.

## Independent critique

Two independent review seats examined the trade-offs and the live repositories.
The Fable review seat was not backed by a verifiably distinct Fable model in
this runtime, so its value is independent task framing rather than model
provenance. The Sol seat ran on the available Sol model. Both reached the same
core recommendation: standalone fleet owner, pinned reuse, no legacy Ansible
inventory membership, and optional LiveSpec adoption later.

The reviews identified these corrections to the initial framing:

1. ACFS is not a safe bootstrap dependency as-is. It hard-codes
   `/data/projects` in filesystem setup, aliases, tmux working directories,
   starter projects, and smoke tests. Either parameterize and release that
   behavior upstream or provision only an explicit, pinned subset in the new
   repository. The first implementation should own the selected subset.
2. The installed AWS wrapper is not presently backed by the tracked source that
   `vps-info` documentation claims. Current `homelab` documentation says that
   source was deleted and survives in an old tag/installed copies. Recover,
   review, and rehome it before claiming AWS identity reproducibility.
3. Existing host roles embed `vps`, `100.89.189.118`, `/data/projects`, and a
   provider kernel hostname. All four must become inventory values or runtime
   discoveries.
4. Pi and Cloudflare MCP coverage are incomplete in the migrated role set.
5. Existing observability is primarily Claude-shaped. Codex has only partial
   normalization and Pi has no exporter. “All agent activity” is new work, not
   a configuration-copy task.
6. A first rebuilt host proves recovery; a second numbered host proves the
   fleet abstraction.

## Scope boundary

### The new repository owns

- bare supported-Ubuntu bootstrap to an Ansible-capable `ubuntu` account;
- the asserted local and Tailscale hostname `agent-cockpit-{n}`;
- base packages, shell, terminal, tmux, agent CLIs, and operator utilities;
- declarative Claude, Codex, Pi, plugin, hook, and MCP desired state;
- GitHub/GitLab CLI and credential-helper configuration, without credentials;
- AWS CLI installation and an optional separately gated AWS workload identity;
- Tailscale client installation, health checks, and manual enrollment receipts;
- the 1Password CLI wrapper integration and 1Password Desktop;
- Xvfb, XFCE, x11vnc, Chrome, shared D-Bus, and VNC/Chrome launch wiring;
- cockpit-specific OpenTelemetry launchers, attributes, canaries, and tests;
- repository reconciliation into the real directory
  `/home/ubuntu/workspace`;
- state classification, persistent-disk layout, doctor command, and rebuild
  acceptance;
- migration from `vps` and cross-repository deprecation after acceptance.

### Explicitly excluded from the new repository

- Dolt server, databases, beads-web, and database-native backups;
- VPS filesystem backups: Arq SMB/snapshot and `vps-restic-backup`;
- local Fabro server instances (owned by `fabro-hosts`);
- VS Code, code-serve-web, code-pwa-proxy, or any editor/PWA replacement;
- VPS-specific Honeycomb recipient checks for bespoke services;
- any service whose purpose is serving the old VPS rather than driving agents.

The old VPS continues to own and run those services. Their presence must not be
used as a reason to copy a whole home directory or service tree into the new
cockpit.

### Deferred, with reconsideration points

- **Provider IaC:** defer Terraform/provider modules until the target VPS
  provider is selected. The host bootstrap contract and cloud-init interface
  are in scope now; provider-specific resource creation is reconsidered before
  provisioning `agent-cockpit-0`.
- **Kubernetes/container execution:** defer implementation until two bare-host
  rebuilds pass. Reconsider as a worker execution layer, not as a containerized
  copy of the entire interactive desktop/identity host.
- **LiveSpec adoption:** defer until the second-host acceptance review. Adopt
  only if its governance benefits an independent backlog.
- **Cockpit data backup service:** do not copy VPS backup services. Define the
  persistent-state contract now; choose its new backup owner before retiring
  the old cockpit.
- **Prompt/response content capture:** do not inherit the current full-content
  setting. Resolve the privacy decision before telemetry configuration is
  implemented.

## Desired repository layout

Prefer Ansible-native YAML over a single `ai-cockpit-config.jsonc`. JSONC is not
natively consumed by Ansible, and one mixed file would combine fleet defaults,
host identity, and mutable repository inventory. Use this split instead:

```text
agent-cockpit-info/
├── README.md
├── bootstrap/
│   ├── bootstrap.sh
│   └── cloud-init.yaml.tmpl
├── ansible.cfg
├── site.yml
├── inventory/
│   ├── hosts.yml
│   ├── group_vars/
│   │   └── agent_cockpits.yml
│   └── host_vars/
│       └── agent-cockpit-0.yml
├── config/
│   ├── repos.yml
│   ├── agent-config.yml
│   ├── mcp.yml
│   └── telemetry.yml
├── schemas/
│   ├── repos.schema.json
│   └── cockpit.schema.json
├── roles/
│   ├── cockpit_base/
│   ├── cockpit_identity/
│   ├── cockpit_shell/
│   ├── cockpit_tmux/
│   ├── cockpit_agent_clis/
│   ├── cockpit_agent_config/
│   ├── cockpit_repo_reconcile/
│   ├── cockpit_vnc/
│   ├── cockpit_chrome/
│   ├── cockpit_1password/
│   ├── cockpit_aws/
│   └── cockpit_telemetry/
├── files/
│   └── tmux.conf
├── scripts/
│   ├── cockpit-doctor
│   ├── reconcile-repos
│   └── verify-rebuild
├── tests/
└── docs/
    ├── bootstrap.md
    ├── manual-gates.md
    ├── state-model.md
    ├── migration-from-vps.md
    └── rollback.md
```

`inventory_hostname` is the single host identity. A host variable
`cockpit_instance: 0` must derive `agent-cockpit-0`, and Ansible must fail when
the derived value, inventory name, kernel hostname, or requested Tailscale
hostname disagree. Never store a Tailscale IP: discover the current IPv4 at
runtime after `tailscaled` is healthy.

Every external input carries a version, checksum or signed repository channel,
and an update policy. CI rejects unpinned ad-hoc `curl | sh`, moving branches,
and URLs without verification.

## State model

The cattle goal requires explicit state classes rather than pretending all
state is declarative.

| Class | Examples | Rebuild behavior |
|---|---|---|
| Git desired state | roles, units, tmux config, package/version policy, repo manifest | cloned and converged |
| Re-mintable identity | Tailscale enrollment, 1Password/AWS seals, gh/glab and agent login | newly authenticated per host; receipt recorded |
| Durable work state | repositories, dirty/untracked files, unpushed refs, selected agent transcripts/handoffs, Atuin history | lives on an attached encrypted/persisted disk and is backed up |
| Ephemeral runtime | tmux sockets/processes, running agents, caches, browser process | recreated; active work is drained to durable handoffs |

Never clone or restore these as machine identities:

- Tailscale state or node keys;
- `/var/lib/systemd/credential.secret` from another host;
- `/etc/credstore.encrypted` blobs sealed on another host;
- 1Password, gh/glab, Claude, Codex, Pi, Chrome, or desktop auth blobs by
  default;
- tmux sockets and running processes.

The persistent disk should mount at a cockpit-owned path and expose
`/home/ubuntu/workspace` as a real directory, not `/data/projects` and not a
symlink. If other durable paths are placed on the disk, declare them one by one
and prohibit whole-home persistence by default because it mixes credentials,
caches, and work product.

## Bare-host bootstrap DAG

The bootstrap is restartable and deliberately includes human identity gates:

1. Create or verify `ubuntu`, SSH-key access, passwordless sudo, time sync,
   locale, supported architecture/Ubuntu release, Python, Git, and CA roots.
2. Authenticate enough GitHub access to clone the private control repository,
   or use a one-use scoped deploy credential supplied by the operator. Persist
   neither bootstrap token nor cloud-init secret.
3. Run pinned Ansible locally and assert the inventory/hostname invariant.
4. Install base packages, shell, tmux, Atuin Ctrl-R integration, and pinned
   toolchains/utilities.
5. Install Tailscale and pause for ordinary untagged member enrollment with
   hostname `agent-cockpit-{n}`. Explicitly set Tailscale SSH true, verify empty
   tags, and record the separate admin-console key-expiry-disable receipt.
6. Install the 1Password CLI/wrapper and pause to mint and seal a fresh
   per-instance systemd credential. A copied sealed blob is an error.
7. Install AWS CLI. If workload AWS access is required, run a second,
   separately documented re-mint/reseal gate for the recovered AWS wrapper.
8. Authenticate gh and glab, then Claude, Codex, Pi, 1Password Desktop, and any
   optional Chrome account. These gates must report “manual pending” rather
   than false Ansible convergence.
9. Reconcile private repositories only after their provider credentials pass.
10. Install VNC/desktop, agent configs, MCPs, hooks, notifications, collector,
    telemetry launchers, and acceptance probes.
11. Run `cockpit-doctor`, a second Ansible convergence, reboot recovery, and
    remote acceptance.

## Identity and credential decisions

| Identity | Desired model | Git contains | Manual receipt |
|---|---|---|---|
| Linux | user `ubuntu`; no `cwoolley` account assumption | user/group/sudo policy | initial SSH proved |
| Tailscale | ordinary untagged member; unique node `agent-cockpit-{n}` | package and assertions only | enrolled, tags empty, SSH true, expiry disabled |
| 1Password service account | prefer one credential per cockpit for independent revocation | wrapper revision and environment identifiers, never token | fresh host seal and smoke test |
| AWS workload | distinct from installing AWS CLI; fresh host-bound seal | wrapper source/revision and parameter names | STS identity proved |
| GitHub/GitLab | per-user auth via `gh`/`glab`; helpers configured | hosts, repo paths, scopes required | provider API + private clone proved |
| Agent providers | interactive per-host login unless a scoped service identity is explicitly adopted | desired config only | one real invocation per agent |
| VNC | per-instance password, tailnet-only | unit/template only | remote login + listener negatives |
| Honeycomb | scoped ingest/config credentials loaded through the secret layer | dataset/service/attribute policy | real spans and dead-man query proved |

Current GitHub authentication is healthy. Current GitLab authentication returns
HTTP 403/account blocked, so GitLab repositories need a visible failed/manual
gate rather than being silently skipped.

### Immediate credential incident prerequisite

During the independent read-only review, a gitignored local environment file in
`1password-env-wrapper` was accidentally exposed to internal tool/model logs.
No value is copied into this plan. Before using the affected credential to
bootstrap a new host, rotate the affected 1Password service-account credential
and reseal every host that consumes it. This is a separate authorized recovery
action; the planning session must not rotate it implicitly.

## Workstation behavior to preserve

The new repository owns a merged, explicit tmux file rather than sourcing ACFS.
Preserve the measured current behavior: mouse, extended keys/CSI-u,
`screen-256color`, 50,000-line history, the existing copy-mode binding, the
expanded left status width, and `detach-on-destroy on`. Add an automated tmux
configuration parse/smoke test.

Preserve Ctrl-R as the Atuin-backed history search and test the binding in an
interactive zsh shell. Install only the useful cockpit baseline, including
zsh, Atuin, fzf, zoxide, mise, Bun/Node, uv, just, ripgrep, jq, fd, keyutils,
`systemd-creds`, gh, glab, AWS CLI, `op`, and the selected agent-driving tools.
NTM, caam, cass, cm, `bd`/`bv`, `hl`, notifications, and factory clients need an
explicit keep/drop/version decision; absence must not be hidden under “ACFS”.

Claude, Codex, and Pi must be pinned, installed independently, and exercised.
Desired settings are rendered structurally. Do not copy whole current settings
trees: they contain path-scoped trust, auth, caches, histories, project IDs, and
`/data/projects` assumptions. Manage declared MCP/plugin/hook entries while
preserving unrelated user-managed keys.

The MCP inventory starts with the current shared capabilities, including
Honeycomb, Cloudflare where still relevant to agent work, Bright Data,
Playwright/Chrome CDP, Google connectors, and agent mail. Each entry declares
agent compatibility, package/revision, credential source, health probe, and
whether it is required. MCP registration is not evidence of runtime telemetry.

## VNC and desktop contract

Preserve the complete measured stack:

- Xvfb display `:1` with XFCE, not a full display manager;
- x11vnc with authentication, dynamically bound to the runtime Tailscale IPv4
  on `5900` and refused when Tailscale is not healthy;
- an explicit IPv6 wildcard mitigation and negative checks for public/wildcard
  listeners;
- shared D-Bus state for desktop services;
- Chrome with a separate `google-chrome-vnc` profile and loopback-only CDP
  `127.0.0.1:9222` for Playwright MCP;
- 1Password Desktop launched in the VNC D-Bus session after an authenticated
  VNC connection, with the current bounded runtime behavior;
- no VS Code packages or services.

Acceptance must prove remote tailnet VNC, Chrome rendering, 1Password Desktop,
CDP from localhost, and rejection from public/wildcard interfaces. The unit
must rediscover a changed Tailscale IP after re-enrollment or reboot.

## Repository reconciliation contract

`config/repos.yml` is schema-validated and contains at least:

```yaml
repos:
  - destination: livespec
    origin: https://github.com/thewoolleyman/livespec.git
    auth: github
    required: true
    update: clone-only
```

The reconciler is non-destructive:

- create `/home/ubuntu/workspace` as a real `ubuntu:ubuntu` directory;
- clone a missing destination;
- verify an existing destination's normalized origin;
- never reset, clean, discard, or overwrite an existing worktree;
- by default do not pull; an opt-in fast-forward update may run only on a clean
  worktree with no unpushed commits;
- distinguish authentication failure, unavailable origin, dirty divergence,
  and manifest mismatch;
- allow the same origin at two destinations only when explicitly declared;
- treat a no-origin directory as unmanaged state requiring a migration
  decision, not as cloneable desired state.

### Initial snapshot from the current workspace

The live `~/workspace` is currently a symlink to `/data/projects`. Its 42
top-level Git repositories are the seed list below. Preserve destination names
in the initial manifest, then prune deliberately. The two Tailscale destinations
share one origin and must be explicitly declared as such. `myproject` has no
origin and therefore goes into the migration exception list, not the clone
manifest.

```text
1password-env-wrapper
OB1
agent-flywheel                         (GitLab)
agentic_coding_flywheel_setup
beads
beads-web
claude-code-ntfy
cxdb
cxdb-graph-ui
dolt-server
fabro
fabro-hosts
gdk-in-a-box-agent-flywheel-wrapper    (GitLab)
gmktec-xubuntu-info
homelab
hp-xubuntu-info
interactive-resume.gitlab.io           (GitLab)
kilroy
livespec
livespec-console-beads-fabro
livespec-dev-tooling
livespec-driver-claude
livespec-driver-codex
livespec-driver-pi
livespec-orchestrator-beads-fabro
livespec-orchestrator-git-jsonl
livespec-overseer
livespec-runtime
local-llm
macbook-m4-max-info
myproject                               (no origin; migration exception)
openbrain
openclaw-info
otel-collector
personal-knowledge-base
poweredge-xubuntu-info
resume
tab-groups-windows-list
tailscale-admin
tailscale-admin-thread09-hetzner-issuer (same origin as tailscale-admin)
tsvmtunnel
vps-info
```

The implementation task that writes `repos.yml` must capture the full normalized
origin URLs from this measured snapshot and must mark provider/manual-auth
requirements explicitly.

## Observability contract

Reuse the `otel-collector` project through a pinned cockpit deployment shape;
do not fork a static collector config into the new repository. Cockpit-owned
roles install that pinned artifact and render only host/secret inputs.

Minimum telemetry, independent of content capture:

- a session/lifecycle span for every Claude, Codex, and Pi invocation;
- native provider/model/tool/token spans where the harness exposes them;
- wrapper-level fallback spans where it does not, especially Pi;
- stable attributes for `host.name`, `cockpit.instance`, harness, session/tmux
  identity, repository, model, tool, outcome, duration, error category, token
  counts, and cost when actually available;
- delivery/failure counters and collector self-observability;
- one ungrouped dead-man/canary query per numbered host, because grouping only
  present hosts cannot detect a silent host;
- infrastructure-as-code ownership for boards/triggers/recipients, or an
  explicit external owner and reconciliation test;
- one real accepted trace from each agent after bootstrap and reboot.

Do not label an MCP API key or MCP registration as agent telemetry. Codex
version-sensitive instrumentation must be verified against the pinned CLI's
supported configuration/schema; the current local CLI alone is not a durable
contract.

### Required privacy decision

Before implementing collector/launcher configuration, ask whether actual
prompts, responses, system instructions, tool definitions, tool arguments, and
tool results may be exported. The current host has full-content capture enabled,
but that is evidence of current state, not consent to a fleet default.

The safe provisional default is content capture off, with operational metadata,
errors, timing, token counts, and redacted/allowlisted tool dimensions on. If
content capture is approved, define filtering, truncation, Honeycomb access
control, retention, environment-specific policy, and secret/PII tests before
enabling it.

## Implementation phases

### Phase 0 — contain and ratify

1. Rotate the credential exposed to internal review logs and reseal consumers.
2. Confirm the standalone/pinned-seam architecture.
3. Decide per-cockpit versus shared 1Password service accounts (recommended:
   per-cockpit), whether AWS workload identity is required, and the content
   capture policy.
4. Select supported Ubuntu release(s)/architecture, initial VPS provider, disk
   encryption/backup owner, and instance-number allocation authority.
5. Decide the explicit ACFS-derived utility keep/drop list.

Exit: decisions and security receipt are recorded; no implementation child
assumes unresolved credential/privacy policy.

### Phase 1 — create the repository and executable contract

1. Create private `agent-cockpit-info` with README, license/security posture,
   Ansible layout, schemas, CI, dependency pinning, and changelog policy.
2. Add a bootstrap contract that works from supported bare Ubuntu with only
   provider SSH/cloud-init and an ephemeral way to clone the private repo.
3. Add lint/schema/unit tests and a container/VM syntax tier that does not
   pretend to validate Tailscale/VNC/systemd end-to-end.
4. Add `cockpit-doctor` with machine-readable and human output.

Exit: CI is green, bootstrap reaches Ansible, and sample inventories validate.

### Phase 2 — converge the base cockpit

1. Implement base OS, user/sudo, package repositories, hostname assertions,
   time/locale, SSH hardening, firewall/listener policy, and persistent-disk
   layout.
2. Implement the explicit shell/toolchain set, merged tmux config, Atuin Ctrl-R,
   Git identity/helpers, gh/glab, AWS CLI, and `op` CLI.
3. Implement pinned Claude, Codex, and Pi installations without ACFS runtime
   dependency.
4. Run Ansible twice and require zero changes on the second run except tasks
   explicitly documented as probes.

Exit: local non-secret cockpit checks pass on a clean Ubuntu VM.

### Phase 3 — identity and secrets gates

1. Implement Tailscale installation/dynamic discovery and the untagged
   enrollment/SSH/key-expiry receipt workflow.
2. Integrate a pinned 1Password wrapper release with a fresh per-host seal.
3. Recover/review/rehome the AWS wrapper source; implement an optional separate
   reseal and STS check.
4. Implement explicit gh/glab and agent-login gates with actionable pending
   states.

Exit: no host-bound blob was copied; every identity has a positive remote/API
check and a recorded manual receipt.

### Phase 4 — desktop and agent-driving surface

1. Implement VNC/Xvfb/XFCE/D-Bus, Chrome/CDP, and 1Password Desktop behavior.
2. Render structural Claude/Codex/Pi configs, plugins, MCPs, hooks,
   notifications, keyring safeguards, and selected factory utilities.
3. Sweep every rendered file/script for `/data/projects`, `/workspace`, `vps`,
   `vmi3006760`, and `100.89.189.118`.
4. Prove tmux key behavior, Ctrl-R, each CLI, each required MCP, and desktop
   functionality.

Exit: the cockpit is usable through Tailscale SSH and VNC with no public
cockpit listeners.

### Phase 5 — repositories and durable state

1. Commit the measured repository manifest and schema.
2. Implement and test non-destructive clone/reconciliation semantics.
3. Define encryption, mount, ownership, backup, restore, and replacement-host
   attachment for durable work state.
4. Quarantine `myproject` and any dirty/unpushed current work until each has a
   recorded migration disposition.

Exit: a blank workspace is populated; a dirty workspace is preserved and
reported; restore is rehearsed.

### Phase 6 — all-agent observability

1. Land the pinned cockpit collector shape in `otel-collector` and its consuming
   pin in `agent-cockpit-info`.
2. Add Claude, Codex, and Pi native or wrapper instrumentation under one common
   semantic contract.
3. Apply the ratified content policy and redaction tests.
4. Provision/reconcile canaries, boards/triggers/recipients, and one ungrouped
   dead-man condition per host.
5. Verify real agent work produces inspectable traces and that exporter failure
   is visible locally.

Exit: all three agents have accepted evidence; “configured” alone is not a pass.

### Phase 7 — provision and dogfood `agent-cockpit-0`

1. Provision a new VPS with a fresh attached persistent disk.
2. Run bootstrap from committed/pinned source, complete manual identity gates,
   and run Ansible twice.
3. Reboot and prove unattended service recovery, then run the full remote
   acceptance matrix.
4. Dogfood several real work cycles across Claude, Codex, and Pi. Record defects
   in the new repository rather than patching the host.
5. Destroy and rebuild the compute instance while preserving only the declared
   disk/work-state inputs; prove recovery.

Exit: one host has passed convergence, reboot, real use, and destroy/rebuild.

### Phase 8 — migrate active work from `vps`

1. Inventory every tmux session/pane, current working directory, child process,
   dirty/untracked file, unpushed ref, active task, agent transcript/handoff,
   Atuin state, and selected browser state.
2. Push normal Git state. For unpushable work, create encrypted bundles/rsync
   transfers with hashes and restore tests. Never migrate live tmux processes.
3. Write durable handoffs for active agent sessions, freeze creation of new VPS
   cockpit sessions, and resume them on `agent-cockpit-0`.
4. Keep the old cockpit unchanged through a rollback window while verifying
   daily use, reboot recovery, repository state, VNC, credentials, and telemetry.

Exit: no active cockpit work depends on the old VPS and rollback evidence is
still available.

### Phase 9 — prove fleet semantics with `agent-cockpit-1`

Provision a second fresh host with only a new instance number and credentials.
Repeat bootstrap, idempotence, reboot, remote acceptance, and telemetry tests.
Any host-specific code or copied identity is a release blocker.

Exit: the same commit produces two independently enrolled cattle instances.

### Phase 10 — deprecate old owners

After the rollback window and second-host proof, remove or redirect duplicated
cockpit material from:

- `vps-info` services/docs/installers;
- `livespec-dev-tooling` dev-host playbook, roles/host vars, and hard-coded
  checkout references;
- `otel-collector` VPS-only cockpit documentation/config after the shared shape
  is live;
- `tailscale-admin` inventories/docs that treat `vps` as the cockpit;
- 1Password wrapper consumer docs and any reconciliation job pointing to the
  old checkout;
- agent configs, hooks, and scripts with `/data/projects` or VPS literals.

Preserve Dolt, beads-web, both VPS backup systems, `fabro-hosts`-owned services,
and other intentional server/CI workloads. Before deleting old cockpit units,
prove zero relevant tmux sessions/processes and keep a reviewed removal list.

Exit: `vps-info` describes the bespoke server that remains, not a deprecated
agent cockpit; no canonical cockpit role exists in two repositories.

## Acceptance matrix

The migration is not complete until all of the following are evidenced:

- fresh supported Ubuntu reaches a converged cockpit from committed pins;
- second Ansible run is clean; reboot restores enabled services;
- kernel, inventory, and Tailscale names equal `agent-cockpit-{n}`;
- Tailscale is Running, untagged, SSH-enabled, key expiry disabled, and remotely
  reachable;
- VNC is tailnet-only; no cockpit listener binds public IP, `0.0.0.0`, or `[::]`;
- XFCE, Chrome, loopback CDP, and 1Password Desktop work in the VNC session;
- tmux configuration and Atuin Ctrl-R match the preserved behavior;
- Claude, Codex, and Pi each complete a real task with required MCPs/plugins;
- gh can access private GitHub repositories; glab either passes or reports its
  explicit blocked gate; AWS CLI works and workload STS passes if enabled;
- all declared repositories clone into `/home/ubuntu/workspace`; dirty state is
  never destroyed;
- each agent emits the agreed telemetry and each host has a working silence
  detector;
- no secret or host identity appears in Git, logs, cloud-init, or another
  host's sealed state;
- compute destroy/rebuild with declared persistent state succeeds;
- `agent-cockpit-1` proves there are no hidden `-0` assumptions;
- old VPS cockpit activity reaches zero before deprecation changes merge.

## Rollback

The rollback unit is operational traffic, not copied identity. Until final
deprecation, leave the old VPS cockpit services and worktrees intact, prohibit
new state divergence where practical, and retain a session/state inventory.
If dogfood fails, stop creating work on the new host, write handoffs, sync only
verified work product back, and resume on the old VPS. Do not copy new Tailscale
or systemd credential state backward.

After old cockpit units are removed, rollback means reverting the deprecation
commits and reconverging the old VPS; bespoke VPS services remain untouched
throughout. The persistent cockpit disk and its independent backup are the
recovery source for work product, while every machine identity is re-minted.

## Decisions required before implementation children are filed

1. Confirm the standalone `agent-cockpit-info` recommendation, with optional
   adopter review only after two-host proof.
2. Confirm per-instance 1Password service accounts, or explicitly accept a
   shared credential's larger revocation/blast radius.
3. Decide whether AWS workload authentication is a cockpit requirement or only
   AWS CLI installation is required.
4. Decide the Honeycomb content policy. Recommended default: operational
   metadata on, prompt/response/tool content off until explicitly approved.
5. Choose the initial VPS provider, supported Ubuntu release/architecture,
   persistent-disk encryption/backup owner, and instance-number allocator.
6. Confirm that selected ACFS conveniences will be re-expressed and pinned in
   the cockpit repository rather than installing ACFS wholesale.

Once these are confirmed, record the scope event on `livespec-livyxu` and file
dependency-layered implementation children for Phases 1–10. Do not file one
giant “build cockpit” item.
