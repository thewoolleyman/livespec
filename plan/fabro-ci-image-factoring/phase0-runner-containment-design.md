# Phase 0 — local-runner containment & security design

**Status:** design artifact, drafted 2026-07-12, grounded in a read-only host
survey + the `handoff.md` threat model. **NO host was mutated.** This design is
**gated**: it must pass the dual adversarial review (§"Gate") before ANY host
change (user creation, runner install, registration) is made. Companion to
`handoff.md`; tracked as epic child `livespec-3lev.3`.

## Why this is the highest-risk phase

The repos are **PUBLIC** (`livespec`, `livespec-dev-tooling`,
`livespec-console-beads-fabro`). GitHub explicitly warns against self-hosted
runners on public repos: a **fork PR can run attacker-controlled workflow code
on the host**. So the design is not "install a runner" — it is "contain an
adversary who can execute code as the runner."

### The host as it is today (survey, 2026-07-12)

- `ubuntu` (uid 1000) is in **both `docker` and `sudo`** and has **passwordless
  sudo**. The runner must therefore **never** run as `ubuntu`.
- Only one uid≥1000 user exists (`ubuntu`) — Phase 0 creates the runner user.
- `/var/lib/doltdb` is `0750 dolt:dolt` (untraversable by a non-`dolt` user).
- The 1Password wrapper secret (`/data/projects/1password-env-wrapper/.env.local`)
  is `0600 ubuntu` (unreadable by a non-`ubuntu` user).

**Isolation backbone:** run everything job-related as a dedicated unprivileged
user that is in **none** of `docker` / `sudo` / `dolt`. That single fact makes
the Kind-2 secrets structurally unreadable.

## Kind-2 secret inventory the runner user MUST NOT reach

The 1Password/systemd-creds token, the Dolt tenant password (`BEADS_DOLT_PASSWORD`
source), the GitHub App private key, `/var/lib/doltdb`, and the **runner
registration credential** (below). Verification tests (§"Isolation tests")
assert each is unreadable by the runner user.

## Runner design

1. **Dedicated unprivileged user** `ci-runner` (name TBD), created with **no**
   membership in `docker`, `sudo`, or `dolt`, no sudoers entry, its own home +
   cache dirs. This is the primary containment boundary.
2. **The runner IS the baked image, one job per fresh container, NO docker
   socket.** The ephemeral GitHub Actions runner is launched inside a **rootless
   container** (recommended: rootless **podman** / user-namespaced) instantiated
   from the baked toolchain image — so CI runs the *exact* image the Fabro
   sandbox uses, jobs execute directly in it (no nested per-step containers),
   and **`/var/run/docker.sock` is never mounted** (socket access is
   root-equivalent and would expose every host secret). Rootless means even a
   container escape lands in an unprivileged user namespace, not host root.
   - *Alternative considered:* install the toolchain directly in `ci-runner`'s
     host environment (no container). Rejected as the default: it drops the
     image-parity + throwaway-filesystem guarantees. Recommend the rootless
     container.
   - **Image builds do NOT run here** — building needs a privileged builder;
     it stays GitHub-hosted / on the trusted builder (see `handoff.md`).
3. **Ephemeral execution:** `--ephemeral` runner — one job per registration,
   auto-deregisters after that job; fresh filesystem each job.

## Trusted-event routing (fork PRs must never reach the runner)

- **Workflow gate:** self-hosted jobs run only on trusted events — `push` to
  `master`, `merge_group`, and **same-repo** PRs. Concretely, gate the moved
  jobs on `github.event.pull_request.head.repo.full_name == github.repository`
  (a fork PR has a different head repo). Fork PRs keep `runs-on: ubuntu-latest`.
- **Repo setting:** require approval to run workflows for **all outside
  collaborators / all fork PRs**.
- **Verification:** a test fork PR MUST NOT trigger any self-hosted-labeled job
  (part of the isolation tests).

## Supervisor + registration credential (a new Kind-2 secret)

The owner is a personal account, so runners are **repo-level, ephemeral**; a
**supervisor** re-registers after each job using short-lived registration
tokens.

- **Credential:** a **GitHub App** with repo-administration scope (recommended
  over a PAT — App tokens are short-lived, scoped, auditable). Its private key
  lives in **systemd-creds** (`LoadCredential=`), readable ONLY by the
  supervisor service — never by `ci-runner`, never mounted into the job
  container.
- **Flow:** the supervisor mints a **short-lived registration token**, hands
  ONLY that token to a freshly-launched ephemeral runner container, which uses
  it once and dies. The job never sees the App key or a long-lived token.
- The supervisor runs as its own hardened systemd service (own low-priv user or
  `DynamicUser=`, `LoadCredential=` for the key, no shell for `ci-runner`).

## Caches — trust-tiered, secret-free

Persistent local-disk cache dirs (`~/.cache/uv`, `~/.cargo/registry`) owned by
`ci-runner`, carrying **no secrets**. **PR / untrusted-lane jobs get read-only
(or throwaway-overlay) mounts**; write-back happens ONLY from trusted-branch
(post-merge) runs. Per-repo namespaces so a poisoned object from one repo can't
flow into another's build. (`sccache` stays trusted-tier-only / deferred.)

## Isolation tests (Phase 0 exit criteria — must all pass)

1. `ci-runner` is in NONE of `docker` / `sudo` / `dolt`; has no sudoers entry.
2. As `ci-runner`: cannot read `/var/lib/doltdb`, the 1Password wrapper
   `.env.local`, the GitHub App private key, or the Dolt-password source
   (`test ! -r <path>` for each).
3. As `ci-runner`: `sudo -n true` fails.
4. The job container has **no** `/var/run/docker.sock`.
5. The registration credential / App key is **absent** from the job environment
   (`printenv` in a job shows neither).
6. A **fork PR** opened against a public repo does **not** trigger any
   self-hosted-labeled job (routed to `ubuntu-latest`).

## Gate — dual adversarial review before ANY host mutation

**Maintainer-declared 2026-07-12.** Before creating the user, installing the
runner, or registering anything, this design passes a **separate adversarial
review by (a) a Fable-model agent AND (b) a Codex agent**, each running
independently and READ-ONLY, each tasked to find **serious security blockers**
— fork-PR code-execution escape, secret leakage into the job env, privilege
escalation, socket/host-filesystem exposure, registration-credential exposure —
**not nitpicks**. Iterate the design until **BOTH** return **no serious
blockers**. A no-serious-blockers verdict from both is the precondition for
implementation. Record each round's findings + resolutions on `livespec-3lev.3`.

## Rollback

Each step is reversible and reversal is written into the Phase 0 work-item:
deregister the runner (short-lived token), stop + disable the supervisor
service, delete the `ci-runner` user + its caches, and (in CI) revert the moved
jobs' `runs-on` to `ubuntu-latest`. A partial state (runner built but CI not
yet cut over — Phase 2) is a valid pause point.

## Sequencing

Phase 0 is a **non-gating shadow lane** (one repo's `just check` green on the
runner, not blocking merges) and is NOT gated by any P-host baseline (that was
retired — see `handoff.md`). It IS gated by the dual adversarial review above.
