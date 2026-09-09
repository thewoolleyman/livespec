# Inventory: `livespec-dev-tooling/ci-runner/k3s/phase2/` (Ansible-migration Phase 0 sizing)

Source: repository `livespec-dev-tooling`, committed tree at `master` HEAD (clean checkout at `/data/projects/livespec-dev-tooling`), read 2026-09-09. Read-only; no host was contacted.

## How the host column was derived

`install-node.sh` is the ordered per-node runbook. It parses `CLUSTER_ROLE` from `../phase0-bare-metal/profiles/<node>.env`:

| Profile | `CLUSTER_ROLE` |
|---|---|
| `poweredge-xubuntu.env` | `server` |
| `gmktec-xubuntu.env` | `agent` |

Its step table (`STEP_IDS`, in order) and role plan:

| Step | Runs on | Installer invoked | Notes |
|---|---|---|---|
| 1 k3s-config | both | `k3s-config/install-k3s-config.sh --role ROLE` | server installs `config.yaml` + skip marker; agent installs `config.agent.yaml`, no marker, then waits for `k3s-agent.service` + containerd |
| 2 kernel-budgets | both | `node-inotify-budget/install-inotify-sysctl.sh`, `node-keyring-budget/install-keyring-sysctl.sh` | |
| 2b storage-layout | both | `storage-layout/install-storage-layout.sh` | |
| 2c host-thermal | server only (`STEP_SKIP`) | `host-thermal/install-host-thermal.sh` | role used as a proxy for PowerEdge hardware |
| 2d host-tools | both | `host-tools/install-host-tools.sh` | |
| 3 apparmor | both | `apparmor/install-apparmor-profile.sh` (`--profile-only` on agent) | ConfigMap half is server only |
| 4 churn-slot | server only (`STEP_SKIP`, `STEP_STALE_UNITS`) | `node-extended-resource/install-reapply-unit.sh --role ROLE CAPACITY` | agent run removes `reapply-node-extended-resource.{timer,service}` |
| 5 wedged-runner | server only (`STEP_SKIP`, `STEP_STALE_UNITS`) | `wedged-runner/install-wedged-runner-scan.sh --role ROLE MODE` | agent run removes `scan-wedged-runners.{timer,service}` |
| 5b runner-pod-lifecycle | server only (`STEP_SKIP`, `STEP_STALE_UNITS`) | `runner-pod-lifecycle/install-runner-pod-lifecycle-scan.sh --role ROLE` | agent run removes `scan-runner-pod-lifecycle.{timer,service}` |
| 6 arc-log-archive | server only (`STEP_SKIP`, `STEP_STALE_UNITS`) | `arc-log-archive/install-arc-log-archive.sh --role ROLE` | agent run removes `archive-arc-logs.{timer,service}` |
| 7 secret-reinjection | server only (`STEP_SKIP`) | `../secret-reinjection/install-secret-reinjection-unit.sh` | OUTSIDE this slice |
| 7b sccache | both | `sccache/install-sccache-binary.sh`, `cache-telemetry/install-cache-telemetry.sh` | |
| 7c container-hook | both | `container-hook/install-container-hook.sh` | |
| 8 reconstruct | server only (`STEP_SKIP`) | `reconstruct/install-converge-unit.sh` | the only step that puts Kueue + ARC on a node's plan |
| 9 datastore-tmpfs | server only (`STEP_SKIP`) | `datastore-tmpfs/install-datastore-tmpfs.sh` | |
| 10 storage-sweep | both | `storage-sweep/install-storage-sweep.sh PROFILE` | agent gets `agent-ordering.conf` drop-in, no tmpfs pre-gate |

On an agent, `remove_stale_server_only_units` hands the four `STEP_STALE_UNITS` sets to `remove-server-only-units.sh` (disable, delete, one daemon-reload, `reset-failed` per named unit).

NOT run by `install-node.sh` (documented as separate attended/maintainer-gated steps): `warm-cache/install-warm-cache.sh` (attended initial populate), `warm-cache/registry-mirror/*` and `warm-cache/sandbox-image-prune/install-sandbox-image-prune.sh` (item `livespec-h96p`, "none of this is live yet"), `storage-layout/migrate-tier.sh` (media migration), `arc/recycle-scale-set-runners.sh` (post-`helm upgrade` operator step), `reconstruct/verify-installed-tree.sh` (drift audit from the checkout).

Column key for the table below. **host(s)**: which of the two in-scope hosts the artifact ends up on or acts from: `server` = poweredge-xubuntu, `agent` = gmktec-xubuntu, `both`, `none` (never lands on a host). **class**: (a) HOST GLUE → Ansible; (b) KUBERNETES-DECLARATIVE → stays, Ansible only applies; (c) DEAD / ONE-SHOT; (d) REPO-SIDE, not host plumbing.

## Classification table

### `phase2/` (top level)

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `README.md` | Phase-2 design and operations document (210 KB) | none | nothing | (d) | Documentation. |
| `VALIDATION_CHECKLIST.md` | Record of the 2026-08 live validation of the Kueue/ARC design (items 1,3,5,7 confirmed; 4 superseded by `kueue/DERIVATION.md`; 2 open) | none | nothing | (c) | Historical validation record; only cited by README, DERIVATION.md and two script comments. |
| `install-node.sh` | THE ordered per-node runbook: parses the profile, selects the step plan by `CLUSTER_ROLE`, removes stale server-only units on an agent, invokes each installer in order | both | Nothing directly; orchestrates every installer below; exports `KUBECONFIG=/etc/rancher/k3s/k3s.yaml` on a server | (a) | This IS the per-host role switch; it becomes the playbook/role ordering plus `when: cluster_role == ...` conditions. |
| `install-node-exit-tests.sh` | Off-host assertion that the server and agent `--dry-run` plans are exactly the expected ones | none | nothing | (d) | Exit-test suite. |
| `k3s-runtime-ready.sh` | Sourced library: bounded waits for a k3s unit to be active and for containerd at `/run/k3s/containerd/containerd.sock` to answer `ctr version` (120 s, 2 s cadence) | both (sourced by k3s-config installer and extract-externals) | nothing; a wait | (a) | Becomes an Ansible `wait_for`/`until` task on the agent path. |
| `remove-server-only-units.sh` | Disable + delete named server-only units, one daemon-reload, `reset-failed` on every named unit still failed | agent | Removes `/etc/systemd/system/{reapply-node-extended-resource,scan-wedged-runners,scan-runner-pod-lifecycle,archive-arc-logs}.{timer,service}` and clears their failed state | (a) | Agent-role cleanup of units; `systemd` module with `state: absent`-style tasks plus a `reset-failed` command. |
| `remove-server-only-units-exit-tests.sh` | Off-host proof that reset-failed covers named-but-absent units | none | nothing | (d) | Exit-test suite. |

### `apparmor/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `apparmor/ci-runner-workflow` | AppArmor profile for hook-generated workflow pods (fixes the stacked-label `signal`/`ptrace` denial) | both | `/etc/apparmor.d/ci-runner-workflow` (0644), loaded with `apparmor_parser -r -W`, enforce mode verified via `aa-status` | (a) | Kernel-state file on every node that runs pods. |
| `apparmor/install-apparmor-profile.sh` | Installs + loads the profile; without `--profile-only` also converges the `arc-hook-pod-template` ConfigMap via `../arc/converge-hook-pod-template.sh` | both (profile); server (ConfigMap) | Host: the profile above. Cluster (server only): ConfigMap `arc-runners/arc-hook-pod-template` | (a) | Profile copy + parser load is host glue; the ConfigMap half is (b) and is already covered by converge step 8. |

### `arc-log-archive/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `arc-log-archive/archive-arc-logs.service` | Oneshot unit running the archive script with the admin kubeconfig | server | `/etc/systemd/system/archive-arc-logs.service` (`After=network-online.target`, `Environment=KUBECONFIG=/etc/rancher/k3s/k3s.yaml`, `ExecStart=/usr/local/lib/ci-runner-k3s/archive-arc-logs.sh`) | (a) | systemd unit install. |
| `arc-log-archive/archive-arc-logs.sh` | Pulls ARC controller/listener pod logs (`kubectl logs`) incrementally into an on-host archive | server | `/usr/local/lib/ci-runner-k3s/archive-arc-logs.sh` (0755); writes `/var/log/arc-archive/` (0750) and state in `/var/lib/ci-runner-k3s/arc-log-archive/` | (a) | Copied script backing a timer; reads the cluster with the admin kubeconfig only a server holds. |
| `arc-log-archive/archive-arc-logs.timer` | Every 2 min, 1 min after boot | server | `/etc/systemd/system/archive-arc-logs.timer` (enabled `--now`) | (a) | systemd timer install. |
| `arc-log-archive/install-arc-log-archive-exit-tests.sh` | Off-host proof of role-awareness (server sequence, agent refusal + cleanup, dry-run) | none | nothing | (d) | Exit-test suite. |
| `arc-log-archive/install-arc-log-archive.sh` | Copies the script, creates the two dirs, installs service + timer, `daemon-reload`, `enable --now` timer, starts the service once; on `--role agent` refuses and removes any copy | server (refuses on agent) | The four items above | (a) | Copy + unit + enable; agent branch is the cleanup `remove-server-only-units.sh` also performs. |

### `arc/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `arc/converge-hook-pod-template.sh` | `kubectl create configmap arc-hook-pod-template --from-file=hook-pod-template.yaml --dry-run=client -o yaml \| kubectl apply -f -` in `arc-runners` | server (runs from converge step 8; copied to installed tree) | Cluster: ConfigMap `arc-runners/arc-hook-pod-template`. Host: the copy at `/usr/local/lib/ci-runner-k3s/arc/converge-hook-pod-template.sh` (installed-tree set) | (b) — control flow to be replaced by a kustomization/apply step (a `configMapGenerator` fits exactly) | No host side effects. |
| `arc/hook-pod-template.yaml` | ARC Kubernetes-mode hook pod-spec extension: `hostUsers: false`, AppArmor `Localhost/ci-runner-workflow`, warm uv cache env, read-only hostPath of `/usr/local/lib/ci-runner-k3s/bin` at `/opt/ci-runner/bin`, postStart/preStop cache telemetry, crates-proxy and sccache opt-in | server (ConfigMap); consumed by workflow pods on both | Cluster: content of the ConfigMap above; DEPENDS on host files from (a) rows: the AppArmor profile, `/usr/local/lib/ci-runner-k3s/bin/{sccache,ci-cache-span}` | (b) | Kubernetes pod-spec data; copied to installed tree at `arc/hook-pod-template.yaml`. |
| `arc/recycle-scale-set-runners.sh` | Deletes a scale set's IDLE runner pods after `helm upgrade` (skips pods with a live `-workflow` companion) | none (run from a checkout with a kubeconfig; not installed, not on the boot path) | Cluster: `kubectl delete pod -n arc-runners` | (b) — control flow; cluster-only operator step | Post-upgrade cluster action; Ansible may invoke it as a handler after the helm step; no host side effects. |
| `arc/values-EXAMPLE-repo.yaml` | Template for a new per-repo scale-set values file; excluded from the installed tree and from `SCALE_SETS` | none | nothing (kept in lockstep by `runner-image.sh assert_values_pins_agree`) | (d) | Authoring template, never applied. |
| `arc/values-livespec-console-beads-fabro.yaml` | Helm values for scale set `livespec-console-beads-k3s` | server (helm from converge step 7) | Cluster: `helm upgrade --install livespec-console-beads-k3s` (chart `gha-runner-scale-set` 0.14.2). Depends on host file `/usr/local/lib/ci-runner-k3s/hooks/2.336.0/index.js` (hostPath) | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-dev-tooling.yaml` | Helm values for `livespec-dev-tooling-k3s` | server | same shape as above | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-driver-claude.yaml` | Helm values for `livespec-driver-claude-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-driver-codex.yaml` | Helm values for `livespec-driver-codex-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-driver-pi.yaml` | Helm values for `livespec-driver-pi-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-orchestrator-beads-fabro.yaml` | Helm values for `livespec-orchestrator-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-orchestrator-git-jsonl.yaml` | Helm values for `livespec-orchestrator-git-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-overseer.yaml` | Helm values for `livespec-overseer-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec-runtime.yaml` | Helm values for `livespec-runtime-k3s` | server | same shape | (b) | Helm values; copied to installed tree. |
| `arc/values-livespec.yaml` | Helm values for `livespec-local-ci-k3s`; ALSO the reference file `runner-image.sh` reads the runner image pin from | server | same shape; pin `ghcr.io/actions/actions-runner:2.336.0@sha256:0cfdcc70…` | (b) | Helm values; copied to installed tree. |
| `arc/values-poweredge-xubuntu-k3s.yaml` | Helm values for the host-unique scale set `poweredge-xubuntu-k3s` (supersedes phase-1 `values-host-unique.yaml`) | server | same shape | (b) | Helm values; copied to installed tree. |

### `cache-telemetry/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `cache-telemetry/README.md` | Pod-side cache-span telemetry design | none | nothing | (d) | Documentation. |
| `cache-telemetry/ci-cache-span.sh` | POSIX-sh emitter of `cache.warm-copy` / `cache.job-summary` spans, called from the hook template's lifecycle hooks inside every job container; posts to the node's keyless OTLP listener on port 4319 | both | `/usr/local/lib/ci-runner-k3s/bin/ci-cache-span` (0755 root), mounted read-only into every job pod at `/opt/ci-runner/bin` | (a) | Pool-provided file copied to every node that runs pods. |
| `cache-telemetry/install-cache-telemetry.sh` | Idempotent copy of the emitter into the bin dir | both | the file above | (a) | Plain `copy`. |

### `container-hook/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `container-hook/README.md` | Fleet-patched hook + externals pre-seed design | none | nothing | (d) | Documentation. |
| `container-hook/build-patched-hook.sh` | Developer-host reproducible build: fetches upstream hook release, rebuilds unpatched (byte-identical check), applies `externals-skip.patch`, writes `bundle/<runner-version>/` | none | nothing on any CI host; produces `bundle/2.336.0/{index.js,index.js.sha256,BUILD-INFO}` | (d) | Build tooling; the bundle's consumer is `install-container-hook.sh`, which copies it from the checkout. |
| `container-hook/bundle/2.336.0/BUILD-INFO` | Provenance record of the committed bundle (image digest, hook version 0.7.0, upstream sha, patch sha, Node v20.19.5) | both | `/usr/local/lib/ci-runner-k3s/hooks/2.336.0/BUILD-INFO` (0644 root) | (a) | Payload of a copy task. |
| `container-hook/bundle/2.336.0/index.js` | The 8.9 MB patched ARC k8s container hook (ncc bundle) | both | `/usr/local/lib/ci-runner-k3s/hooks/2.336.0/index.js` (0644 root); every values file hostPath-mounts it at `/home/runner/fleet-hook/index.js` | (a) | Payload of a copy task (checksum-gated). |
| `container-hook/bundle/2.336.0/index.js.sha256` | Manifest for the bundle (`6a91cc48…`) | both | `/usr/local/lib/ci-runner-k3s/hooks/2.336.0/index.js.sha256` | (a) | Payload of a copy task; the checksum an Ansible `copy`/`get_url` can assert. |
| `container-hook/externals-skip.patch` | The ONE diff against upstream hook v0.7.0 | none | nothing | (d) | Build input. |
| `container-hook/extract-externals-exit-tests.sh` | Off-host proof that extract waits for containerd | none | nothing | (d) | Exit-test suite. |
| `container-hook/extract-externals.sh` | Mounts the pinned runner image read-only via `ctr -n k8s.io images mount` (pulls if absent), verifies runner version + hook sha, `cp -a` `/home/runner/externals` into a staging dir, writes marker + per-file sha256 manifest, atomic `mv`, publishes relative symlink `current` | both | `/var/lib/rancher/k3s/storage/.externals/2.336.0/` (+ `.externals-seeded-2.336.0` marker), `/var/lib/rancher/k3s/storage/.externals/2.336.0.MANIFEST.sha256`, `/var/lib/rancher/k3s/storage/.externals/current -> 2.336.0` | (a) | Host-side seed rendering from a pinned image; stays a script Ansible invokes (idempotent on its manifest) or becomes a role with `ctr` commands. |
| `container-hook/install-container-hook.sh` | Verifies the bundle against its manifest, asserts every values file agrees on the version, copies the three bundle files, then runs `extract-externals.sh --expect-hook-sha256` | both | the `hooks/2.336.0/` files + the externals tree above | (a) | Copy + invoke. |
| `container-hook/runner-image.sh` | Sourced library: reads the image pin from `../arc/values-livespec.yaml`, derives runner version and digest ref, `assert_values_pins_agree` over every values file | both (sourced on host by the installer) | nothing | (a) | Becomes a fact/variable derivation (runner version, digest) in the role; the lockstep assertion becomes an `assert` task. |

### `crates-proxy/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `crates-proxy/README.md` | Crates proxy design | none | nothing | (d) | Documentation. |
| `crates-proxy/converge-crates-proxy.sh` | `kubectl apply -f crates-proxy.yaml`, annotate deployment with the manifest hash, bounded `rollout status` | server (converge step 8b; copied to installed tree) | Cluster: Namespace `ci-crates-proxy`, ConfigMap `crates-proxy-nginx`, Deployment `crates-proxy`, Service `crates-proxy` | (b) — control flow to be replaced by a kustomization/apply step | No host side effects (the hostPath dir is `DirectoryOrCreate`). |
| `crates-proxy/crates-proxy.yaml` | nginx proxy_cache in front of crates.io; hostPath store, `hostPort 3080`, nodeSelector on the cache-tier carrier | server (applied); pod lands on the cache-tier carrier node | Cluster objects above; hostPath `/var/cache/ci-runner/crates-proxy` | (b) | Manifest; copied to installed tree. |

### `datastore-tmpfs/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `datastore-tmpfs/20-requires-datastore-mount.conf` | k3s drop-in `RequiresMountsFor=/var/lib/rancher/k3s/server/db` | server | `/etc/systemd/system/k3s.service.d/20-requires-datastore-mount.conf` | (a) | systemd drop-in. |
| `datastore-tmpfs/install-datastore-tmpfs.sh` | Pre-gates on `inject-github-app-secret.service` and `converge-ci-stack.service` being enabled; installs mount unit + drop-in; `enable` (never `--now`) | server | the two files; `systemctl enable var-lib-rancher-k3s-server-db.mount` | (a) | Unit install + enable with a precondition assert. |
| `datastore-tmpfs/var-lib-rancher-k3s-server-db.mount` | tmpfs (2G, 0700, noexec,nosuid,nodev) over the k3s SQLite datastore, `Before=k3s.service` | server | `/etc/systemd/system/var-lib-rancher-k3s-server-db.mount` | (a) | systemd mount unit. |

### `gates/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `gates/gate-credentials.yaml` | Documents the operator-created Secret `gates/gate-forge-credential` (key `GH_TOKEN`); the file itself is deliberately never applied (would create an empty secret) | none | nothing; the header's `kubectl create secret generic … --from-literal=GH_TOKEN=…` is an attended one-shot | (c) | One-shot operator step recorded as a manifest header; not in the installed tree, not applied by converge. |
| `gates/gate-job-template.yaml` | Kueue-gated `batch/v1 Job` TEMPLATE with `@@PLACEHOLDER@@` markers (`suspend: true`, queue `gates-lq`) | server (copied); consumed by the remote gate client | Host: `/usr/local/lib/ci-runner-k3s/gates/gate-job-template.yaml` (installed-tree set). Cluster: nothing until rendered and submitted by the client | (b) | Kubernetes Job template; its host copy is part of the (a) installed-tree copy. |
| `gates/gates-credential-exit-tests.sh` | Off-host proof of the render-sa-kubeconfig `--server` default and the gates kubeconfig shape | none | nothing | (d) | Exit-test suite. |
| `gates/gates-rbac.yaml` | ServiceAccount/Role/RoleBinding `gate-submitter` in `gates` + its token Secret | server (converge step 10b) | Cluster: the RBAC objects; the token Secret is then read to render `/etc/ci-runner/gates.kubeconfig` (see reconstruct rows) | (b) | Manifest; copied to installed tree. |
| `gates/render-gate-job-exit-tests.sh` | Off-host proof of the renderer's requirements | none | nothing | (d) | Exit-test suite. |
| `gates/render-gate-job.sh` | Renders the template for one repo/tree, reading the image from the gated repo's `.github/workflows/ci.yml`; writes to stdout, applies nothing | server (copied); run by the gate client | Host: `/usr/local/lib/ci-runner-k3s/gates/render-gate-job.sh` (installed-tree set) | (b) | Client-side manifest render; host copy is part of the (a) installed-tree copy. |

### `host-thermal/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `host-thermal/apply-idrac-thermal.service` | Oneshot at boot, `ConditionPathExists` on the script | server | `/etc/systemd/system/apply-idrac-thermal.service` (enabled) | (a) | systemd unit. |
| `host-thermal/apply-idrac-thermal.sh` | Converges iDRAC: fan loop automatic + third-party PCIe response off (ipmitool raw 0x30), thermal profile "Minimum Power" (racadm); read-then-write | server | `/usr/local/lib/ci-runner-k3s/apply-idrac-thermal.sh` (0755); iDRAC attribute state | (a) | Copied script + firmware-state convergence; PowerEdge only. |
| `host-thermal/install-host-thermal.sh` | Runs `install-racadm.sh`, copies the apply script + unit, enables, applies now | server | the above | (a) | Copy + unit + enable. |
| `host-thermal/install-racadm.sh` | Downloads two pinned Dell .debs, verifies SHA-256, `apt-get install` them (plus `libargtable2-0`), verifies `racadm` answers in-band | server | Packages `srvadmin-hapi` 11.0.0.0, `srvadmin-idracadm7` 11.0.0.0 (binary at `/opt/dell/srvadmin/…`) | (a) | Pinned package download + install. |

### `host-tools/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `host-tools/btop-loop` | Operator wrapper restarting btop after its SIGABRT stall | both | `/usr/local/bin/btop-loop` (0755) | (a) | Plain file copy. |
| `host-tools/install-host-tools.sh` | `install` each tool into `/usr/local/bin` | both | the above | (a) | Plain `copy`. |

### `isolation/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `isolation/cache-negative-tests.sh` | Negative tests of the cache tiers, run INSIDE a routed job by `.github/workflows/ci-cache-negative-tests.yml` (every 6 h) | none (runs in a workflow pod) | nothing on a host | (d) | Repo-side test suite executed by CI, not host plumbing. |
| `isolation/negative-control-job.yaml` | Deliberately misconfigured `Job cache-negative-control` (writable warm root + writer credential) proving the negative tests can go red; hand-applied | none | Cluster (by hand only): Job in `ci-warm-cache` referencing a hand-made ConfigMap `cache-negative-tests` | (c) | Diagnostic one-shot; not applied by anything. |

### `k3s-config/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `k3s-config/config.agent.yaml` | Agent k3s config: `kubelet-arg: max-pods=200` only | agent | `/etc/rancher/k3s/config.yaml` (0600) | (a) | Rendered host config; one template with role-conditional keys replaces both files. |
| `k3s-config/config.yaml` | Server k3s config: `max-pods=200`, `disable: [local-storage]`, `tls-san` (tailnet name + `100.78.140.72`), `write-kubeconfig-mode 0644` | server | `/etc/rancher/k3s/config.yaml` (0600) + skip marker `/var/lib/rancher/k3s/server/manifests/local-storage.yaml.skip` | (a) | Rendered host config. |
| `k3s-config/install-k3s-config-exit-tests.sh` | Off-host proof of role behaviour and agent repair | none | nothing | (d) | Exit-test suite. |
| `k3s-config/install-k3s-config.sh` | Installs the role's file; server writes the skip marker, agent removes one; on an agent with a CHANGED config and `k3s-agent.service` active/activating, waits (via `k3s-runtime-ready.sh`) for the unit and containerd; never restarts k3s | both | the above | (a) | Template + marker file + conditional wait. |

### `kueue/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `kueue/DERIVATION.md` | The quota arithmetic behind every `cluster-queue-*.yaml` | none | nothing | (d) | Documentation; explicitly skipped by the installer. |
| `kueue/cluster-queue-gates.yaml` | Namespace `gates`, ResourceFlavor `gates-flavor`, ClusterQueue `gates-cq` (15 cpu / 24Gi), WorkloadPriorityClass `gate-priority`, LocalQueue `gates-lq` | server (converge step 5 glob) | Cluster objects named | (b) | Manifest; copied to installed tree. |
| `kueue/cluster-queue-livespec-console-beads-fabro.yaml` | ClusterQueue + LocalQueue (`arc-runners`) for that repo | server | Cluster objects | (b) | Manifest; copied to installed tree. |
| `kueue/cluster-queue-livespec-dev-tooling.yaml` | ClusterQueue + LocalQueue for that repo | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-driver-claude.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-driver-codex.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-driver-pi.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-orchestrator-beads-fabro.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-orchestrator-git-jsonl.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-overseer.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec-runtime.yaml` | ClusterQueue + LocalQueue | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-livespec.yaml` | ClusterQueue `livespec-cq` (quota 5 churn-slots, cohort `fleet-ci-runner-pool`) + LocalQueue `livespec-lq` | server | Cluster objects | (b) | Manifest; copied. |
| `kueue/cluster-queue-phase1-proof.yaml` | Phase-1 proof objects re-declared at `v1beta2` (flavor/CQ `phase1-proof-*`, 2 cpu / 4Gi, LocalQueue in `arc-runners`) | server | Cluster objects (still applied by the glob; carries no real traffic) | (b) | Manifest; copied. Candidate for retirement but currently live. |
| `kueue/core/deployment-ha-patch.yaml` | Kustomize patch: 2 replicas, 5 s probe timeouts | server | Cluster: patches `kueue-system/kueue-controller-manager` | (b) | Kustomization member; copied. |
| `kueue/core/kustomization.yaml` | Resources = upstream `kueue/releases/download/v0.19.1/manifests.yaml` + the two patches; applied as ONE `kubectl apply --server-side --force-conflicts -k` | server | Cluster: Kueue core v0.19.1 | (b) | Kustomization; copied. Pin is asserted against `KUEUE_VERSION` in converge. |
| `kueue/core/manager-config-patch.yaml` | ConfigMap `kueue-manager-config` (leader-election tolerances, concurrency) | server | Cluster ConfigMap; converge restarts the deployment only when its content hash changes | (b) | Kustomization member; copied. |
| `kueue/resource-flavor.yaml` | ResourceFlavor `churn-slot-flavor` on nodeLabel `k3s-role=arc-runner-host` | server (converge step 5, applied first) | Cluster object | (b) | Manifest; copied. |

### `local-path-provisioner/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `local-path-provisioner/local-path-provisioner.yaml` | Fleet-owned copy of k3s's bundled provisioner (`rancher/local-path-provisioner:v0.0.36`, path `/var/lib/rancher/k3s/storage`) + tuning args + a `setup` script that reflink-seeds `_warm/uv` and `externals` into every new work volume | server (converge step 3); the seed runs in helper pods on whichever node the volume lands | Cluster: SA/ClusterRole/Binding, Deployment `kube-system/local-path-provisioner`, StorageClass `local-path`, ConfigMap `local-path-config` | (b) | Manifest; copied to installed tree. The bundled component is disabled host-side by the (a) k3s-config rows. |

### `node-extended-resource/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `node-extended-resource/install-reapply-unit-exit-tests.sh` | Off-host proof of role-awareness | none | nothing | (d) | Exit-test suite. |
| `node-extended-resource/install-reapply-unit.sh` | Copies the patch script, substitutes `CAPACITY_PLACEHOLDER` (from the profile's `ADMISSION_CAPACITY_C`) into the service, installs service + timer, enables both, starts once, verifies node allocatable; refuses + cleans up on agent | server (refuses on agent) | `/usr/local/lib/ci-runner-k3s/patch-node-churn-capacity.sh`, `/etc/systemd/system/reapply-node-extended-resource.{service,timer}` | (a) | Copy + templated unit + enable. |
| `node-extended-resource/patch-node-churn-capacity.sh` | `kubectl patch node --subresource=status` setting `ci-runner.io/churn-slot: <C>` on EVERY node labeled `k3s-role=arc-runner-host` | server (copy; act is cluster-wide) | Host: the copy above (also invoked by converge step 1b for self-heal). Cluster: node status capacity | (a) | Copied script backing a unit; the act it performs is cluster-side but is only reachable from the server's kubeconfig. |
| `node-extended-resource/reapply-node-extended-resource.service` | Oneshot, `Requires=k3s.service`, `Before=converge-ci-stack.service`, `ExecStart=… CAPACITY_PLACEHOLDER` | server | `/etc/systemd/system/reapply-node-extended-resource.service` (placeholder substituted at install) | (a) | Templated systemd unit. |
| `node-extended-resource/reapply-node-extended-resource.timer` | Every 5 min (`OnCalendar=*:0/5`, 1 min after boot) | server | `/etc/systemd/system/reapply-node-extended-resource.timer` | (a) | systemd timer. |

### `node-inotify-budget/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `node-inotify-budget/99-ci-runner-inotify.conf` | `fs.inotify.max_user_instances = 8192` | both | `/etc/sysctl.d/99-ci-runner-inotify.conf` | (a) | sysctl drop-in. |
| `node-inotify-budget/install-inotify-sysctl.sh` | Copy + `sysctl -p` + verify | both | the above | (a) | `ansible.posix.sysctl`. |

### `node-keyring-budget/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `node-keyring-budget/60-k3s-container-keyring.conf` | `kernel.keys.maxkeys = 2000`, `kernel.keys.maxbytes = 200000` | both | `/etc/sysctl.d/60-k3s-container-keyring.conf`; installer also removes legacy `/etc/sysctl.d/60-ci-runner-keyring.conf` | (a) | sysctl drop-in. |
| `node-keyring-budget/install-keyring-sysctl.sh` | Copy + remove legacy + `sysctl -p` + verify | both | the above | (a) | `ansible.posix.sysctl` + `file: absent`. |

### `reconstruct/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `reconstruct/converge-ci-stack.service` | Boot oneshot: `After=k3s.service reapply-node-extended-resource.service inject-github-app-secret.service`, `Requires=k3s.service`, `Wants=` the other two, `KUBECONFIG=/etc/rancher/k3s/k3s.yaml`, `ExecStart=/usr/local/lib/ci-runner-k3s/converge-ci-stack.sh` | server | `/etc/systemd/system/converge-ci-stack.service` (enabled, never started by the installer) | (a) | systemd unit. |
| `reconstruct/converge-ci-stack.sh` | The boot converge: wait for API + node Ready; 1b assert churn-slot capacity (self-heal via `patch-node-churn-capacity.sh`); 1c label this node as cache-tier carrier; 2 fail-closed on `arc-runners/arc-github-app-installation` Secret; 3 apply provisioner; 4 `kubectl apply -k kueue/core` (+ rollout restart on ConfigMap change, wait for webhook endpoints); 5 apply flavor + every `cluster-queue-*.yaml`; 6 `helm upgrade --install arc` (controller chart 0.14.2, `arc-systems`); 7 `helm upgrade --install` 11 scale sets (`arc-runners`); 7b delete stale AutoscalingListeners; 8 hook ConfigMap; 8b crates proxy; 8c sccache redis (WARN on failure); 9 warm cache; 10/10b apply probe + gates RBAC and render two kubeconfigs; 11 informational reads | server | Host side effects that are (a): `kubectl label node <this> <cache-tier-carrier label>`; renders `/etc/ci-runner/kueue-webhook-probe.kubeconfig` (root:root 0600) and `/etc/ci-runner/gates.kubeconfig` (root:root 0600, server `https://poweredge-xubuntu.perch-rudd.ts.net:6443`) via `render-sa-kubeconfig.sh`; via 8c, `/etc/ci-runner/sccache-redis-writer.pass` + `/var/cache/ci-runner/sccache-redis/`. Everything else is cluster apply/helm | (b) — control flow to be replaced by a kustomization/apply step | Body is kubectl/helm apply + wait ordering, with the listed host-side side effects that migrate as (a) tasks. |
| `reconstruct/install-converge-unit.sh` | Copies the whole artifact tree (see "Installed-tree set") into `/usr/local/lib/ci-runner-k3s/`, installs + enables the unit, warns if the reapply unit/patch script are absent; `--stage-to DIR` copies without root | server | the installed tree + `/etc/systemd/system/converge-ci-stack.service` | (a) | The canonical copy role. |
| `reconstruct/render-sa-kubeconfig.sh` | Waits ≤60 s for a `kubernetes.io/service-account-token` Secret to populate, renders a static kubeconfig (CA + token) atomically to `--dest` with `--mode/--group`, default server `https://127.0.0.1:6443` | server | `/usr/local/lib/ci-runner-k3s/render-sa-kubeconfig.sh` (copy); at run time `/etc/ci-runner/*.kubeconfig` | (a) | Host-side file rendered from cluster state. |
| `reconstruct/verify-installed-tree-exit-tests.sh` | Off-host proof the verifier detects stale/missing and stays quiet on clean | none | nothing | (d) | Exit-test suite. |
| `reconstruct/verify-installed-tree.sh` | From the checkout: stages the canonical tree via `--stage-to`, sha256-compares against `/usr/local/lib/ci-runner-k3s/` on a host (over ssh), reports STALE/MISSING | none (runs from a checkout; reads the host) | nothing (read-only) | (d) | Repo-side drift audit; Ansible `--check --diff` on the copy role supersedes it. |

### `runner-pod-lifecycle/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `runner-pod-lifecycle/install-runner-pod-lifecycle-scan-exit-tests.sh` | Off-host proof of role-awareness | none | nothing | (d) | Exit-test suite. |
| `runner-pod-lifecycle/install-runner-pod-lifecycle-scan.sh` | Copies the scan, installs service + timer, `enable --now` timer; refuses + cleans up on agent | server (refuses on agent) | `/usr/local/lib/ci-runner-k3s/scan-runner-pod-lifecycle.sh`, `/etc/systemd/system/scan-runner-pod-lifecycle.{service,timer}` | (a) | Copy + unit + enable. |
| `runner-pod-lifecycle/scan-runner-pod-lifecycle.service` | Oneshot, `Requires=k3s.service`, admin kubeconfig, `TimeoutStartSec=240`, `RPL_DEADLINE_SECONDS=240` | server | `/etc/systemd/system/scan-runner-pod-lifecycle.service` | (a) | systemd unit. |
| `runner-pod-lifecycle/scan-runner-pod-lifecycle.sh` | Report-only cluster-wide diagnosis of lifecycle stalls (PVC binding, StartError, listener staleness, capacity-absent, populator stalled, api-unavailable); emits `livespec.ci_lifecycle.*` gauges to `http://127.0.0.1:4319/v1/metrics` | server | copy above; state files `/var/lib/ci-runner-k3s/runner-pod-lifecycle-streak`, `/var/lib/ci-runner-k3s/warm-cache-last-emitted-run`; reads `/var/lib/rancher/k3s/agent/containerd/containerd.log`, `/var/lib/rancher/k3s/storage/.warm/last-run.json` | (a) | Copied script backing a timer. |
| `runner-pod-lifecycle/scan-runner-pod-lifecycle.timer` | Every 5 min, 4 min after boot | server | `/etc/systemd/system/scan-runner-pod-lifecycle.timer` | (a) | systemd timer. |

### `sccache/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `sccache/README.md` | Shared Rust compilation cache design | none | nothing | (d) | Documentation. |
| `sccache/converge-sccache-redis.sh` | Ensures the host-held writer credential (generated on first run), ensures the RDB snapshot dir on the `ci-cache` tier (REFUSES if `/var/cache/ci-runner` is not a mountpoint), renders the ACL into Secret `ci-sccache/sccache-redis-acl`, projects the password into Secret `ci-warm-cache/sccache-redis-writer`, `kubectl apply -f sccache-redis.yaml`, annotate, bounded rollout wait | server (converge step 8c; copied to installed tree) | Host side effects that are (a): `/etc/ci-runner/sccache-redis-writer.pass` (root 0600, generated), `/var/cache/ci-runner/sccache-redis/` (999:1000 0750). Cluster: the two Secrets + Namespace `ci-sccache`, Deployment/Service `sccache-redis` | (b) — control flow to be replaced by a kustomization/apply step | The credential file and snapshot dir are (a) tasks (`password` lookup/`copy` + `file`); the Secrets become `kubernetes.core.k8s` with the file's content. |
| `sccache/install-sccache-binary.sh` | Downloads `sccache-v0.17.0-x86_64-unknown-linux-musl.tar.gz` from GitHub releases, sha256-verifies, installs the binary; skips when `--version` already matches | both | `/usr/local/lib/ci-runner-k3s/bin/sccache` (0755), mounted read-only into every job pod and the populator | (a) | Pinned binary download (`get_url` + `unarchive`). |
| `sccache/sccache-redis.yaml` | Namespace `ci-sccache`, redis `8.8.2-alpine` by digest (16 GB LRU, RDB to hostPath, non-root, read-only rootfs, `hostPort 6379`), Service | server (applied); pod pinned to the cache-tier carrier | Cluster objects; hostPath `/var/cache/ci-runner/sccache-redis` | (b) | Manifest; copied to installed tree. |

### `storage-layout/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `storage-layout/10-requires-storage-mounts.conf` | k3s drop-in `RequiresMountsFor=/var/lib/rancher/k3s/agent/containerd /var/lib/rancher/k3s/storage` | both | `/etc/systemd/system/k3s.service.d/10-requires-storage-mounts.conf` (NOTE: the installer writes under `k3s.service.d` on BOTH roles, while an agent runs `k3s-agent.service`; the drop-in is inert there. Observation only, not fixed here) | (a) | systemd drop-in. |
| `storage-layout/install-storage-layout-exit-tests.sh` | Off-host proof of fresh-host / live-host / repair plans | none | nothing | (d) | Exit-test suite. |
| `storage-layout/install-storage-layout.sh` | Resolves the three LABELs (`ci-cache` ext4, `ci-containerd` ext4, `ci-workvols` xfs) to exactly one device each, unmounts foreign automounts, mounts the cache tier, ensures the FIVE byte-exact fstab lines (three LABEL mounts under `/var/cache/ci-runner`, two binds onto `/var/lib/rancher/k3s/agent/containerd` and `/var/lib/rancher/k3s/storage`), migrates a live containerd/local-path store onto the tier with `rsync -aHAX` (stopping/starting `k3s.service` or `k3s-agent.service`), repairs a bind laid over a store, `findmnt --verify`, installs the drop-in; refuses to exit 0 unless all five are mounted | both | `/etc/fstab` (5 managed lines, backup first), the mounts, the drop-in above | (a) | `mount` module (LABEL=) + drop-in; the live-store migration branch is a one-time bootstrap behaviour to carry as guarded tasks. |
| `storage-layout/migrate-tier.sh` | Attended media migration / in-place filesystem replacement by copy + relabel (`prepare`, `cutover`, `switch-live`, `drain-status`, `finish-live`, `reclaim`); LVM + mkfs + rsync; ends by running the installer | server (has only been run on poweredge-xubuntu) | LVs/filesystems/labels on the tier media; `/mnt/migrate-tier/<role>` staging mounts | (c) | One-shot operator procedure (used 2026-09-04 and 2026-09-06); not converge state, stays a script. |

### `storage-sweep/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `storage-sweep/agent-ordering.conf` | Drop-in re-ordering the sweep `Before=k3s-agent.service`, clearing `After=` | agent | `/etc/systemd/system/sweep-runner-scratch.service.d/agent-ordering.conf` | (a) | systemd drop-in (agent only). |
| `storage-sweep/install-storage-sweep-exit-tests.sh` | Off-host proof of the two role plans | none | nothing | (d) | Exit-test suite. |
| `storage-sweep/install-storage-sweep.sh` | Reads `CLUSTER_ROLE` from the profile; server pre-gates on `var-lib-rancher-k3s-server-db.mount` enabled; copies the sweep, installs the unit (+ agent drop-in), `enable` (never `--now`) | both | `/usr/local/lib/ci-runner-k3s/sweep-runner-scratch.sh`, `/etc/systemd/system/sweep-runner-scratch.service`, agent drop-in | (a) | Copy + unit + conditional drop-in. |
| `storage-sweep/sweep-runner-scratch.service` | Boot oneshot `Before=k3s.service`, `After=var-lib-rancher-k3s-server-db.mount`, `ConditionPathExists=!/var/lib/rancher/k3s/server/db/state.db` | both (ordering overridden on agent) | `/etc/systemd/system/sweep-runner-scratch.service` | (a) | systemd unit. |
| `storage-sweep/sweep-runner-scratch.sh` | Removes every `pvc-*` dir under `/var/lib/rancher/k3s/storage` before k3s starts; refuses if `k3s.service` or `k3s-agent.service` is active or a mountpoint exists below the root | both | copy above; deletes orphaned PVC dirs at boot | (a) | Copied script backing a boot unit. |

### `warm-cache/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `warm-cache/README.md` | Warm uv cache design (70 KB) | none | nothing | (d) | Documentation. |
| `warm-cache/converge-warm-cache.sh` | `kubectl apply -f pypi-proxy.yaml` (+ annotate, bounded rollout), `kubectl apply -f warm-cache-cronjob.yaml`, derives ConfigMap `warm-cache-repos` from every `../arc/values-*.yaml` `githubConfigUrl`, creates ConfigMap `warm-cache-populate` from the populate script + the two `.py` files, patches the CronJob budget | server (converge step 9; copied to installed tree) | Cluster only: Namespace `ci-warm-cache`, proxy objects, CronJob, three ConfigMaps | (b) — control flow to be replaced by a kustomization/apply step | No host side effects; the derived ConfigMaps map to `configMapGenerator`s. |
| `warm-cache/install-warm-cache.sh` | Attended superset: runs the converge, creates ONE populate Job from the CronJob and waits for it (timeout), then converges the hook ConfigMap | server (attended; not in `install-node.sh`) | Cluster: the above + one `Job` | (b) — control flow; attended one-time populate | Cluster-side only; Ansible may run it once after first converge. |
| `warm-cache/pypi-proxy/README.md` | PyPI files proxy design | none | nothing | (d) | Documentation. |
| `warm-cache/pypi-proxy/pypi-proxy.yaml` | nginx `1.28.3-alpine` (digest) proxy of files.pythonhosted.org; hostPath store; ConfigMap; Service | server (applied); pod on cache-tier carrier | Cluster objects in `ci-warm-cache`; hostPath `/var/cache/ci-runner/pypi-proxy` | (b) | Manifest; copied to installed tree. |
| `warm-cache/registry-mirror/converge-registry-mirror.sh` | `kubectl apply -f registry-mirror.yaml` + annotate + bounded rollout; NOT wired into the boot converge (`livespec-h96p`, "none of this is live yet") | server (not yet run anywhere; not in installed tree) | Cluster: Namespace `ci-registry-mirror`, ConfigMap, Deployment, Service | (b) — control flow to be replaced by a kustomization/apply step | Cluster-only; currently unapplied. |
| `warm-cache/registry-mirror/install-registry-mirror.sh` | Renders `registries.yaml.template` (server: `http://127.0.0.1:5001`; agent: host of the profile's `CLUSTER_JOIN_ADDRESS`), refuses to overwrite a non-marker file, writes atomically; never restarts k3s. NOT run by `install-node.sh`; not yet applied on any node | both (planned) | `/etc/rancher/k3s/registries.yaml` (0644) | (a) | Templated host file (`template` module with role-conditional endpoint). Currently unapplied. |
| `warm-cache/registry-mirror/registries.yaml.template` | `mirrors: ghcr.io: endpoint: ["@MIRROR_ENDPOINT@"]` | both (planned) | the rendered file above | (a) | Jinja-ready template. |
| `warm-cache/registry-mirror/registry-mirror.yaml` | `registry:3.0.0` (digest) pull-through cache of ghcr.io, hostPath store, `hostPort 5001`, Recreate strategy | server (planned; unapplied) | Cluster objects; hostPath `/var/cache/ci-runner/registry-mirror` | (b) | Manifest; unapplied. |
| `warm-cache/sandbox-image-prune/install-sandbox-image-prune.sh` | Scans every YAML in the repo for `ghcr.io/thewoolleyman/livespec-fabro-sandbox` pins, refuses on zero hits or on `--role agent`, copies the prune + rendered `prune-sandbox-images.repo-pins`, installs service + timer, `enable --now` timer. NOT run by `install-node.sh` (maintainer-gated step 3 of `livespec-h96p`); not yet installed | server (planned) | `/usr/local/lib/ci-runner-k3s/prune-sandbox-images.sh`, `/usr/local/lib/ci-runner-k3s/prune-sandbox-images.repo-pins`, `/etc/systemd/system/prune-sandbox-images.{service,timer}` | (a) | Copy + rendered data file + unit + enable; the repo scan becomes a lookup at play time. |
| `warm-cache/sandbox-image-prune/prune-sandbox-images-exit-tests.sh` | Off-host proof of the prune's five gates | none | nothing | (d) | Exit-test suite. |
| `warm-cache/sandbox-image-prune/prune-sandbox-images.service` | Oneshot `--apply`, `Requires=k3s.service`, admin kubeconfig | server (planned) | `/etc/systemd/system/prune-sandbox-images.service` | (a) | systemd unit. |
| `warm-cache/sandbox-image-prune/prune-sandbox-images.sh` | Keeps newest N sandbox tags per family; `crictl images`/`ps` + cluster-wide PodSpec read + repo-pins file as gates; `crictl rmi` | server (planned) | copy above; removes images from this node's containerd | (a) | Copied script backing a timer. |
| `warm-cache/sandbox-image-prune/prune-sandbox-images.timer` | Every 6 h, 30 min after boot | server (planned) | `/etc/systemd/system/prune-sandbox-images.timer` | (a) | systemd timer. |
| `warm-cache/uv_cache_layout.py` | uv 0.9.x cache-layout knowledge module imported by the verifier (stdlib only) | server (copied); runs inside the CronJob pod | Host: `/usr/local/lib/ci-runner-k3s/warm-cache/uv_cache_layout.py` (installed-tree set). Cluster: a key of ConfigMap `warm-cache-populate` | (b) | ConfigMap payload; host copy is part of the (a) installed-tree copy. |
| `warm-cache/verify-uv-cache.py` | Verifies a built generation against the union of routed `uv.lock`s before publish | server (copied); runs in the CronJob pod | Host copy at `warm-cache/verify-uv-cache.py`; ConfigMap key | (b) | ConfigMap payload; host copy is part of the installed tree. |
| `warm-cache/warm-cache-cronjob.yaml` | Namespace `ci-warm-cache`, SA + ClusterRole/Binding `warm-cache-populate-kueue-reader`, ConfigMaps `warm-cache-populate` (placeholder) and `warm-cache-budget`, CronJob `warm-cache-populate` (`*/30 * * * *`, image `livespec-fabro-sandbox:python-rust-fuzz-v1.46.0`), pinned to the tier-carrier node | server (applied); pod on cache-tier carrier | Cluster objects; hostPaths `/var/lib/rancher/k3s/storage/.warm` (rw), `/usr/local/lib/ci-runner-k3s/bin` (ro), `/var/cache/ci-runner/pypi-proxy`; reads Secret `sccache-redis-writer` | (b) | Manifest; copied to installed tree. |
| `warm-cache/warm-cache-populate.sh` | The one trusted writer: builds each routed repo's uv cache generation through the PyPI proxy, verifies, publishes atomically to `.warm`; pre-warms the crates proxy; runs sccache writer builds | server (copied); runs inside the CronJob pod | Host copy at `warm-cache/warm-cache-populate.sh` (0644); ConfigMap key; at run time writes `/var/lib/rancher/k3s/storage/.warm/` from inside the pod | (b) | ConfigMap payload executed in-cluster; host copy is part of the installed tree. |

### `wedged-runner/`

| path | one-line purpose | host(s) | what it puts on the host / applies to the cluster | class | reason |
|---|---|---|---|---|---|
| `wedged-runner/install-wedged-runner-scan-exit-tests.sh` | Off-host proof of role-awareness and the timer-active verify | none | nothing | (d) | Exit-test suite. |
| `wedged-runner/install-wedged-runner-scan.sh` | Copies the scan, substitutes `MODE_PLACEHOLDER` (`report`/`clear`, default `clear` from `install-node.sh`) into the service, installs service + timer, `enable --now` timer, starts once, verifies the timer is `active`; refuses + cleans up on agent | server (refuses on agent) | `/usr/local/lib/ci-runner-k3s/scan-wedged-runners.sh`, `/etc/systemd/system/scan-wedged-runners.{service,timer}` | (a) | Copy + templated unit + enable. |
| `wedged-runner/scan-wedged-runners.service` | Oneshot, `Requires=k3s.service`, admin kubeconfig, `ExecStart=… MODE_PLACEHOLDER` | server | `/etc/systemd/system/scan-wedged-runners.service` (substituted) | (a) | Templated systemd unit. |
| `wedged-runner/scan-wedged-runners.sh` | Finds runner pods looping on `Registration … was not found` and (in `clear` mode) deletes idle ones | server | copy above; state file `/var/lib/ci-runner-k3s/wedged-runner-streak` | (a) | Copied script backing a timer. |
| `wedged-runner/scan-wedged-runners.timer` | Every 5 min, 2 min after boot | server | `/etc/systemd/system/scan-wedged-runners.timer` | (a) | systemd timer. |

## Row counts

| class | rows |
|---|---|
| (a) HOST GLUE | 61 |
| (b) KUBERNETES-DECLARATIVE | 48 |
| (c) DEAD / ONE-SHOT | 4 |
| (d) REPO-SIDE | 27 |
| total | 140 |

(Counts re-derived mechanically from the table rows; every one of the 140 committed paths under `phase2/` has exactly one row.)

(c) rows: `VALIDATION_CHECKLIST.md`, `gates/gate-credentials.yaml`, `isolation/negative-control-job.yaml`, `storage-layout/migrate-tier.sh`, and no others. Of the six (b) rows that are converge SCRIPTS, two carry host-side side effects that migrate as (a) tasks — `reconstruct/converge-ci-stack.sh` and `sccache/converge-sccache-redis.sh` (each row lists them) — and four carry none: `arc/converge-hook-pod-template.sh`, `crates-proxy/converge-crates-proxy.sh`, `warm-cache/converge-warm-cache.sh`, `warm-cache/registry-mirror/converge-registry-mirror.sh`.

## 1. SECRETS

Never printed here; only names and locations.

| script | secret | read from / written to |
|---|---|---|
| `reconstruct/converge-ci-stack.sh` (step 2) | `arc-runners/arc-github-app-installation` Secret (GitHub App installation) | READ presence only (`kubectl get secret`), fail-closed. It is WRITTEN by `../secret-reinjection/inject-github-app-secret.service` from the host credstore (outside this slice; seeded once by `../secret-reinjection/seed-github-app-creds.sh`). |
| `reconstruct/converge-ci-stack.sh` (10, 10b) via `reconstruct/render-sa-kubeconfig.sh` | ServiceAccount tokens `kueue-system/kueue-webhook-probe-token` and `gates/gate-submitter-token` (+ `ca.crt`) | READ from the k8s token Secrets with the admin kubeconfig; WRITTEN into `/etc/ci-runner/kueue-webhook-probe.kubeconfig` and `/etc/ci-runner/gates.kubeconfig` (root:root 0600, atomic mktemp+mv, token never echoed). The gates file is consumed by a REMOTE driver host (delivery is R4.S8, not this tree). |
| `reconstruct/converge-ci-stack.sh` / every installer and unit | k3s admin kubeconfig `/etc/rancher/k3s/k3s.yaml` | READ (env `KUBECONFIG`); server only. Units carry `Environment=KUBECONFIG=/etc/rancher/k3s/k3s.yaml`. |
| `sccache/converge-sccache-redis.sh` | sccache-redis writer password | GENERATED on first run and WRITTEN to `/etc/ci-runner/sccache-redis-writer.pass` (root 0600); READ back to render the ACL into Secret `ci-sccache/sccache-redis-acl` and projected into Secret `ci-warm-cache/sccache-redis-writer` (`password` key). Host-local machine secret, not a 1Password item. |
| `warm-cache/warm-cache-cronjob.yaml` (+ `warm-cache-populate.sh` at run time) | `sccache-redis-writer` Secret | READ via `secretKeyRef` into the populator pod's env. |
| `warm-cache/warm-cache-populate.sh` | In-cluster ServiceAccount token | READ from `/var/run/secrets/kubernetes.io/serviceaccount` (Kueue reader). |
| `gates/gate-credentials.yaml` (header only) | `gates/gate-forge-credential` Secret, key `GH_TOKEN` | Created out of band by an operator with `kubectl create secret generic … --from-literal=GH_TOKEN="${GH_GATE_TOKEN}"`; the env var's provenance is not stated in this tree. Never applied from the file. |
| `isolation/cache-negative-tests.sh` / `isolation/negative-control-job.yaml` | `SCCACHE_REDIS_*` writer credential | The test asserts ABSENCE in a job pod (probes env and the paths `/var/run/secrets/sccache-redis-writer`, `/etc/sccache-redis-writer`, `/etc/ci-runner/sccache-redis-writer.pass`); the control Job deliberately injects `SCCACHE_REDIS_WRITER_PASSWORD` from the Secret. |
| `warm-cache/registry-mirror/install-registry-mirror.sh` | none written; REFUSES to overwrite a hand-written `registries.yaml` because it may carry private-registry credentials | — |

No script in this slice invokes a 1Password wrapper (`op`, `with-livespec-env.sh`); the only fleet secret on the boot path (the GitHub App installation) enters through `../secret-reinjection/` outside the slice.

## 2. DOWNLOADS

| script | what | pin | checksum source |
|---|---|---|---|
| `sccache/install-sccache-binary.sh` | `https://github.com/mozilla/sccache/releases/download/v0.17.0/sccache-v0.17.0-x86_64-unknown-linux-musl.tar.gz` | `SCCACHE_VERSION=0.17.0` (env-overridable) | Hard-coded `SCCACHE_SHA256=67c4a96dd237c1f518f6b36083f270f9976d516f1e57fce891755ea782e50006` (copied from the release's `.sha256` asset 2026-09-04); `sha256sum -c`. |
| `host-thermal/install-racadm.sh` | `https://linux.dell.com/repo/community/openmanage/11000/jammy/pool/main/s/srvadmin-hapi/srvadmin-hapi_11.0.0.0_amd64.deb` and `…/srvadmin-idracadm8/srvadmin-idracadm7_11.0.0.0_all.deb`; then `apt-get install` (also `libargtable2-0` from Ubuntu apt, unpinned) | `PIN_VERSION=11.0.0.0` | Hard-coded `HAPI_SHA256=13e74ab9…`, `RACADM_SHA256=9db342a4…` (from Dell's `Packages` index); `sha256sum -c`. |
| `container-hook/extract-externals.sh` (via `install-container-hook.sh`) | Runner image `ghcr.io/actions/actions-runner@sha256:0cfdcc701ce933c6d243c6b0b2da767366dc9f2e99961d4c3754b0b78084cdda` via `ctr -n k8s.io images pull` (only if absent) | Digest read from `arc/values-livespec.yaml` by `runner-image.sh`; runner version 2.336.0 cross-checked inside the image | Image digest; bundled hook sha256 `ab92729b…` asserted via `--expect-hook-sha256` from `BUILD-INFO`; per-file manifest `2.336.0.MANIFEST.sha256` of the copied tree. |
| `container-hook/install-container-hook.sh` | No network; copies the COMMITTED bundle | `index.js.sha256` = `6a91cc4882c0d6ec97c687add2a6d13609b08856d598972c0d66c807f650919a` | `sha256sum -c` before and after copy. |
| `container-hook/build-patched-hook.sh` (developer host only) | actions/runner `images/Dockerfile` at `v2.336.0` (raw GitHub), hook release zip `actions-runner-hooks-k8s-0.7.0.zip`, `git clone` of `actions/runner-container-hooks` at `v0.7.0`, npm registry (`npm ci`), optionally `docker cp` from the image | hook 0.7.0 derived from the Dockerfile; Node v20.19.5 via mise | Byte-identical rebuild vs release asset; recorded in `BUILD-INFO`. |
| `reconstruct/converge-ci-stack.sh` (step 4, via `kueue/core/kustomization.yaml`) | `https://github.com/kubernetes-sigs/kueue/releases/download/v0.19.1/manifests.yaml` (fetched by `kubectl apply -k`) | `KUEUE_VERSION=v0.19.1`, asserted to match the kustomization URL | None (no checksum; version-pinned URL only). |
| `reconstruct/converge-ci-stack.sh` (steps 6, 7) | Helm OCI charts `oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller` and `…/gha-runner-scale-set` | `ARC_CHART_VERSION=0.14.2` | None (chart version only). |
| Manifests pulling images at apply time (no host download by a script) | `rancher/local-path-provisioner:v0.0.36` (tag only) and `ubuntu:24.04@sha256:33ceb719…` (provisioner helper); `redis:8.8.2-alpine@sha256:96cb544f…`; `nginx:1.28.3-alpine@sha256:a8b39bd9…` (pypi proxy; crates proxy uses the same pattern); `registry:3.0.0@sha256:6c5666b8…`; `livespec-fabro-sandbox:python-rust-fuzz-v1.46.0` (tag only, populator); runner image by digest in every values file | as listed | Image digests where present. |

## 3. INSTALLED-TREE SET

Exactly what `reconstruct/install-converge-unit.sh` copies under `/usr/local/lib/ci-runner-k3s/` (the `--stage-to` output that `verify-installed-tree.sh` treats as canonical), with source and mode. Files marked * come from OUTSIDE `phase2/`.

```
converge-ci-stack.sh                                  0755  reconstruct/converge-ci-stack.sh
render-sa-kubeconfig.sh                               0755  reconstruct/render-sa-kubeconfig.sh
arc/converge-hook-pod-template.sh                     0755  arc/converge-hook-pod-template.sh
arc/hook-pod-template.yaml                            0644  arc/hook-pod-template.yaml
arc/values-livespec-console-beads-fabro.yaml          0644  arc/  (glob values-*.yaml minus values-EXAMPLE-repo.yaml)
arc/values-livespec-dev-tooling.yaml                  0644
arc/values-livespec-driver-claude.yaml                0644
arc/values-livespec-driver-codex.yaml                 0644
arc/values-livespec-driver-pi.yaml                    0644
arc/values-livespec-orchestrator-beads-fabro.yaml     0644
arc/values-livespec-orchestrator-git-jsonl.yaml       0644
arc/values-livespec-overseer.yaml                     0644
arc/values-livespec-runtime.yaml                      0644
arc/values-livespec.yaml                              0644
arc/values-poweredge-xubuntu-k3s.yaml                 0644
kueue/core/deployment-ha-patch.yaml                   0644  kueue/core/*.yaml
kueue/core/kustomization.yaml                         0644
kueue/core/manager-config-patch.yaml                  0644
kueue/resource-flavor.yaml                            0644  kueue/resource-flavor.yaml
kueue/cluster-queue-gates.yaml                        0644  kueue/cluster-queue-*.yaml (glob; DERIVATION.md skipped)
kueue/cluster-queue-livespec-console-beads-fabro.yaml 0644
kueue/cluster-queue-livespec-dev-tooling.yaml         0644
kueue/cluster-queue-livespec-driver-claude.yaml       0644
kueue/cluster-queue-livespec-driver-codex.yaml        0644
kueue/cluster-queue-livespec-driver-pi.yaml           0644
kueue/cluster-queue-livespec-orchestrator-beads-fabro.yaml 0644
kueue/cluster-queue-livespec-orchestrator-git-jsonl.yaml   0644
kueue/cluster-queue-livespec-overseer.yaml            0644
kueue/cluster-queue-livespec-runtime.yaml             0644
kueue/cluster-queue-livespec.yaml                     0644
kueue/cluster-queue-phase1-proof.yaml                 0644
local-path-provisioner/local-path-provisioner.yaml    0644  local-path-provisioner/local-path-provisioner.yaml
warm-cache/converge-warm-cache.sh                     0755  warm-cache/converge-warm-cache.sh
warm-cache/warm-cache-cronjob.yaml                    0644  warm-cache/warm-cache-cronjob.yaml
warm-cache/warm-cache-populate.sh                     0644  warm-cache/warm-cache-populate.sh
warm-cache/verify-uv-cache.py                         0644  warm-cache/verify-uv-cache.py
warm-cache/uv_cache_layout.py                         0644  warm-cache/uv_cache_layout.py
warm-cache/pypi-proxy/pypi-proxy.yaml                 0644  warm-cache/pypi-proxy/pypi-proxy.yaml
crates-proxy/converge-crates-proxy.sh                 0755  crates-proxy/converge-crates-proxy.sh
crates-proxy/crates-proxy.yaml                        0644  crates-proxy/crates-proxy.yaml
sccache/converge-sccache-redis.sh                     0755  sccache/converge-sccache-redis.sh
sccache/sccache-redis.yaml                            0644  sccache/sccache-redis.yaml
observability/kueue-webhook-probe-rbac.yaml           0644  * ci-runner/observability/kueue-webhook-probe-rbac.yaml
gates/gates-rbac.yaml                                 0644  gates/gates-rbac.yaml
gates/gate-job-template.yaml                          0644  gates/gate-job-template.yaml
gates/render-gate-job.sh                              0755  gates/render-gate-job.sh
```

That is 47 files (46 from `phase2/`, 1 from `ci-runner/observability/`). Directories created: `arc/`, `kueue/`, `kueue/core/`, `local-path-provisioner/`, `warm-cache/`, `warm-cache/pypi-proxy/`, `crates-proxy/`, `sccache/`, `observability/`, `gates/` (all 0755). Plus, outside the copy loop, `/etc/systemd/system/converge-ci-stack.service` (0644) and `systemctl enable`.

Deliberately NOT in this set, though they share `/usr/local/lib/ci-runner-k3s/` and are owned by other installers (so a full "copy" role must union them): `patch-node-churn-capacity.sh`, `archive-arc-logs.sh`, `scan-wedged-runners.sh`, `scan-runner-pod-lifecycle.sh`, `sweep-runner-scratch.sh`, `apply-idrac-thermal.sh`, `bin/sccache`, `bin/ci-cache-span`, `hooks/2.336.0/{index.js,index.js.sha256,BUILD-INFO}`, and (planned) `prune-sandbox-images.sh` + `prune-sandbox-images.repo-pins`. Also excluded by design: `arc/values-EXAMPLE-repo.yaml`, `kueue/DERIVATION.md`, `warm-cache/install-warm-cache.sh`, `sccache/install-sccache-binary.sh`, `warm-cache/registry-mirror/*`, `warm-cache/sandbox-image-prune/*`, `gates/gate-credentials.yaml`.
