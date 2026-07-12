# CI-runner supervisor — ephemeral JIT runner pool (Phase 0 productionization)

The **general-fleet** ephemeral-runner supervisor for the `thewoolleyman-ci-runners`
GitHub App. Serves any repo the maintainer owns (personal account → repo-level
runners, so pools are per-repo). Authored + credential-layer verified 2026-07-12.
Permanent home per design: **`livespec-dev-tooling`** (relocate).

## Pieces

| File | Role | Install to |
|---|---|---|
| `mint-jitconfig.sh` | Mints a one-shot JIT config via the App (JWT → installation token → `generate-jitconfig`). Key from `APP_KEY` (file) or `APP_KEY_PEM` (env). **Verified: exits 0, mints a real ephemeral registration.** | `/usr/local/lib/ci-runner/` |
| `ci-runner-supervisor.sh` | The loop: per (repo, slot) mint JIT → `systemctl start runner@<id>` → wait → relaunch. Repo list via `CI_RUNNER_REPOS`. | `/usr/local/lib/ci-runner/` |
| `runner@.service` | Templated **ephemeral** runner unit; `User=ci-runner`; JIT staged via `LoadCredential` (root → ci-runner-only); runs one job then exits. | `/etc/systemd/system/` |
| `run-jit-runner.sh` | `ExecStart` wrapper: reads the JIT credential, execs `run.sh --jitconfig`. | `/usr/local/lib/ci-runner/` |
| `ci-runner-supervisor.service` | Hardened supervisor unit; `User=ci-sup`; App key injected ONLY here. | `/etc/systemd/system/` |
| `49-ci-runner-supervisor.rules` | Narrow polkit bridge: `ci-sup` may start/stop **only** `runner@*.service`. Nothing else. | `/etc/polkit-1/rules.d/` |

## Credential model (verified)

- **App** `thewoolleyman-ci-runners` (App ID `4278168`), `Administration: read+write` only, installed on selected repos (currently `livespec`). One key (fingerprint `SHA256:mR4QpknOUHIjN/90xKsFGlfWVpB9+5UuECGhOO+/iL4=`).
- The **App private key** (mints unlimited registrations) is read ONLY by the `ci-sup` supervisor, from the dedicated `github-ci-runners` 1Password environment.
- The **runner** receives ONLY a one-shot **JIT config** (one runner, one job) — never the App key.
- Job containers (via the sanitize-hook mounts) never see the JIT config or the App key.

## Maintainer action required before first start

1. Create a **dedicated `github-ci-runners` 1Password environment** (NOT the shared
   `livespec` one) holding: `GITHUB_APP_ID_CI_RUNNER=4278168`,
   `GITHUB_APP_INSTALLATION_ID_CI_RUNNER=146033367`,
   `GITHUB_APP_CLIENT_ID_CI_RUNNER=Iv23liMDgGWXDVWMYC07`,
   `GITHUB_PRIVATE_KEY_CI_RUNNER` = the PEM with **real newlines** (matches the
   `GITHUB_PRIVATE_KEY_E2E` convention). Source values staged at
   `/tmp/livespec-ci-app.env` + `/tmp/livespec-ci-app.pem` (delete after loading).
2. Provide `/usr/local/bin/with-github-ci-runners-env.sh` (a wrapper injecting that
   environment, analogous to `with-livespec-env.sh`) — the supervisor unit's
   `ExecStart` uses it.

Then: create the `ci-sup` + confirm `ci-runner` users, install the files above,
`systemctl enable --now ci-runner-supervisor.service`, and verify one ephemeral
runner picks up a `runs-on: [self-hosted, local-ci]` job and auto-deregisters.
