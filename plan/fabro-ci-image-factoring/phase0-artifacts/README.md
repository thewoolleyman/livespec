# Phase 0 containment artifacts (staged — relocate to `livespec-dev-tooling`)

These are the durable artifacts produced while implementing the Phase 0 local
CI-runner containment (`../phase0-runner-containment-design.md`), **validated
live 2026-07-12** on this host. They are staged here in the plan thread for
preservation; their permanent home per the design is **`livespec-dev-tooling`**
(runner/supervisor/containment tooling). Relocate them there (with a
work-item citing this commit) as part of finishing Phase 0.

| File | What it is | Status |
|---|---|---|
| `provision-ci-runner.sh` | Idempotent host provisioning: pre-gate verify → rootless stack → `ci-runner` (none of docker/sudo/dolt) → subuid/linger/caches → podman socket → runner + hooks + sanitizer + `.env`. | Live-derived; run as sudo-capable admin. |
| `sanitize-hook.js` | `ACTIONS_RUNNER_CONTAINER_HOOKS` wrapper: strips host-socket binds (`/var/run/docker.sock`) + host-namespace/privilege create-options before the real hook. | **Installed + live-verified** (fixes test 4). |
| `containers.conf` | `ci-runner` rootless podman config: public DNS resolvers + private netns. | **Installed + live-verified**. |
| `isolation-exit-tests.sh` | The 11 design isolation tests, runnable against the live host. | Tests 1–4,7,8,9,11 runnable; 5,6,10 skip-stubbed (need live-job/supervisor). |
| `pregate-verify.sh` | The provisioning pre-gate subset (tests 1,2,3,7) as run at gate time. | 11/11 green live. |

## What was proven live (run 29183111924, job "mechanism + live isolation" = success)

A real GitHub Actions job on the local self-hosted `ci-runner` ran its steps
**inside the baked image** via rootless podman (agent/job PID+user-ns separated),
and asserted: **no `/var/run/docker.sock`**; host-loopback Dolt `:3307` /
`host.containers.internal` / cloud-metadata **denied**; **no runner credentials**
reachable in the job fs; container-root → host `ci-runner` (**not** host root);
outbound internet OK. AppArmor userns sysctls stayed `=1` throughout.

## Known follow-ons (NOT containment — separable)

- **`just check` green** needs persistent cache mounts (uv / npm+pyright / cargo):
  pyright cold-downloads its Node CLI via `npm install pyright@…` each run, slow
  over the isolated NAT. This is the Phase 0 caching deliverable.
- **Productionization**: JIT/ephemeral registration + the supervisor
  (GitHub App key in systemd-creds + narrow polkit bridge). The pilot used the
  existing `gh` repo-admin to register a persistent runner.
- **Image freshness**: pilot pinned `livespec-fabro-sandbox:v0.38.1` (stale vs
  master); the Phase 1 layered images track current pins.
