# Session handoff — Phase 0 implementation (2026-07-12)

Full detail is on beads **`livespec-3lev.3`** (multiple dated comments). This is
the resume map. Everything below is DONE + verified unless marked TODO.

## What's done + verified live

**Phase 0 containment — PROVEN LIVE** (livespec run `29183111924`, job
"mechanism + live isolation" = success). A real GitHub Actions job ran on the
local self-hosted `ci-runner`, inside the baked image via rootless podman, and
asserted: no `/var/run/docker.sock`; Dolt `:3307` / host-loopback / cloud-metadata
denied; no runner creds in the job fs; container-root → ci-runner (not host root);
AppArmor sysctls stayed `=1`. Tasks 1–4, 6 done.

**Host state (persists across sessions):**
- Rootless stack installed (podman 5.4.2, crun, uidmap, slirp4netns, passt,
  fuse-overlayfs, netavark, **aardvark-dns**). AppArmor sysctls untouched (`=1`).
- `ci-runner` (uid 1001) — none of docker/sudo/dolt, nologin, subuid 165536,
  linger on, rootless podman socket enabled, `~/.config/containers/containers.conf`
  (public DNS + private netns), `~/actions-runner/` = runner v2.335.1 +
  container-hooks v0.8.1 + **`sanitize-hook.js`** (strips docker.sock + host-ns
  create-options), `.env` points ACTIONS_RUNNER_CONTAINER_HOOKS at the sanitizer.
- `livespec` repo: fork-PR approval tightened to `all_external_contributors`;
  runner `livespec-ci-pilot` registered but **OFFLINE** (relaunch: as ci-runner,
  `run.sh` with XDG_RUNTIME_DIR + DOCKER_HOST + ACTIONS_RUNNER_CONTAINER_HOOKS).

**4 findings fixed** (each in the beads record): docker.sock→sanitizer;
in-container DNS→containers.conf resolvers; netavark teardown→aardvark-dns;
mise 100%-CPU busy-loop→`mise trust` + MISE_NOT_FOUND_AUTO_INSTALL=0.

**GitHub App (productionization) — created + verified.** `thewoolleyman-ci-runners`
App ID **4278168**, Administration:write only, installed on livespec (installation
**146033367**), one key (fp `SHA256:mR4QpknOUHIjN/90xKsFGlfWVpB9+5UuECGhOO+/iL4=`).
`mint-jitconfig.sh` verified (rc=0, real JIT). **General-fleet** scope decided;
runner label **`local-ci`**; dedicated **`github-ci-runners`** 1Password env.
Credential deliverables staged: `/tmp/livespec-ci-app.env` + `/tmp/livespec-ci-app.pem`
(real-newline PEM matching GITHUB_PRIVATE_KEY_E2E). Maintainer CREATED the
`github-ci-runners` 1Password environment.

**Artifacts pushed** to branch `phase0-selfhosted-shadow-lane`
(`plan/fabro-ci-image-factoring/phase0-artifacts/`): provision-ci-runner.sh,
sanitize-hook.js, containers.conf, isolation-exit-tests.sh (11 tests),
pregate-verify.sh, and `supervisor/` (mint-jitconfig.sh, ci-runner-supervisor.sh,
runner@.service, run-jit-runner.sh, ci-runner-supervisor.service,
49-ci-runner-supervisor.rules, README). Also the shadow workflow
`.github/workflows/ci-selfhosted-shadow.yml`. Nothing merged to master yet.

## NEXT ACTIONS (in order)

1. **Generate `with-github-ci-runners-env.sh`.** Blocked ONLY on the new
   environment's ID: `op environment` has no `list` (only `read`), so get the
   `ONEPASSWORD_ENVIRONMENT_ID` from the maintainer (1Password desktop: Developer →
   View Environments → Manage → Copy environment ID). Then, from
   `/data/projects/1password-env-wrapper`, ensure a Linux group `github-ci-runners`
   exists and run `create-1password-env-wrapper.sh` with
   `IDENTIFIER=github-ci-runners`, the env ID, and an `OP_SERVICE_ACCOUNT_TOKEN`
   with read access (test whether the existing livespec token at
   `/etc/credstore.encrypted/1password-env-wrapper-livespec` can `op environment
   read` the new env first; if not, ask for a token). Verify it injects the four
   `GITHUB_*_CI_RUNNER` vars (probe names/structure only — never print the key).
2. **Install supervisor host plumbing** (maintainer chose "wait for env first"):
   create `ci-sup` user; install supervisor scripts → `/usr/local/lib/ci-runner/`;
   `runner@.service` + `ci-runner-supervisor.service` → `/etc/systemd/system/`;
   polkit rule → `/etc/polkit-1/rules.d/49-ci-runner-supervisor.rules`.
3. **Test the ephemeral JIT flow live**: `systemctl enable --now
   ci-runner-supervisor.service`; confirm it mints a JIT → an ephemeral `runner@`
   picks up a `runs-on: [self-hosted, local-ci]` job (push a `ci-shadow/**` branch)
   → runs in-container → auto-deregisters → slot relaunches. Delete `/tmp` creds.
4. **`just check` green** (was blocked on cold caches): wire persistent
   uv/npm+pyright/cargo cache mounts into job containers (pyright cold-downloads
   its Node CLI). Then re-run the shadow full-check.
5. **Relocate** all `phase0-artifacts/` + the 11-test suite into
   **`livespec-dev-tooling`** as a PR (their permanent home); land the shadow
   workflow on master (non-gating).
6. Then Phase 1 (baked images) / Phase 2 (CI cutover) / fleet fan-out.

## Open worktree (record, not orphaned)

- Worktree: `~/.worktrees/livespec/phase0-selfhosted-shadow-lane`, branch
  `phase0-selfhosted-shadow-lane` (pushed, no PR yet). Clean. Also branch
  `ci-shadow/pilot-1` (throwaway trigger branch, pushed). Primary
  `/data/projects/livespec` clean on `master`.
