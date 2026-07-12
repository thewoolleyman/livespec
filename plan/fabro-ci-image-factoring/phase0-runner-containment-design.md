# Phase 0 — local-runner containment & security design

**Status:** design artifact, drafted 2026-07-12, grounded in a read-only host
survey + the `handoff.md` threat model. **Revised 2026-07-12 to fold in ROUND 1
of the dual adversarial review** (a Fable-model agent AND a Codex agent, each
independent + read-only; BOTH returned SERIOUS-BLOCKERS-FOUND — findings +
resolutions in §"Round 1 dual-review record"). **NO host was mutated** by the
review or this revision. This design remains **gated**: it must pass a FRESH
round-2 dual review (§"Gate") before ANY host change (rootless-stack
provisioning, user creation, runner install, registration) is made. Companion to
`handoff.md`; tracked as epic child `livespec-3lev.3`.

## Why this is the highest-risk phase

The repos are **PUBLIC** (`livespec`, `livespec-dev-tooling`,
`livespec-console-beads-fabro`). GitHub explicitly warns against self-hosted
runners on public repos: a **fork PR can run attacker-controlled workflow code
on the host**. So the design is not "install a runner" — it is "contain an
adversary who can execute code as the runner."

Containment therefore spans **three planes**, not one. Round 1 of the review
showed that a files-at-rest model alone is incomplete on a shared multi-tenant
host:

1. **Filesystem / user** — run as a dedicated user in none of
   `docker` / `sudo` / `dolt`, so the at-rest Kind-2 secrets are structurally
   unreadable.
2. **Network** — the job runs in an isolated network namespace that cannot
   reach host-loopback services (the multi-tenant Dolt server binds loopback).
3. **Injected secrets** — no Kind-2 secret is ever handed into a job's
   environment (containment of what the workflow *gives* the job, not only what
   it can read at rest).

### The host as it is today (survey, 2026-07-12)

- `ubuntu` (uid 1000) is in **both `docker` and `sudo`** and has **passwordless
  sudo**. The runner must therefore **never** run as `ubuntu`.
- Only one uid≥1000 user exists (`ubuntu`) — Phase 0 creates the runner user.
- `/var/lib/doltdb` is `0750 dolt:dolt` (untraversable by a non-`dolt` user).
- The 1Password wrapper secret (`/data/projects/1password-env-wrapper/.env.local`)
  is `0600 ubuntu` (unreadable by a non-`ubuntu` user).
- **(round-1 verified) The rootless-container stack is NOT installed.** `podman`,
  `newuidmap`/`newgidmap` (the `uidmap` package), `slirp4netns`, and `crun` are
  all **absent**; the only container runtime present is **rootful `docker`**
  (socket `srw-rw---- root:docker /var/run/docker.sock`) + `runc`.
  `/etc/subuid` and `/etc/subgid` carry a range **only for `ubuntu`**, none for a
  future `ci-runner`. → The rootless backbone must be **provisioned and verified**
  before it can be relied upon (see §"Provisioning pre-gate"); until then the
  only working runtime is root-equivalent, which is why a docker-group / socket
  fallback is explicitly forbidden below.
- **(round-1 verified) The multi-tenant Dolt SQL server listens on
  `127.0.0.1:3307`** serving every tenant; the OTel collector and other admin
  surfaces also bind loopback. → Containment must include the **network** plane
  (see §"Network isolation").

**Isolation backbone:** the primary boundary is still a dedicated unprivileged
user in **none** of `docker` / `sudo` / `dolt` — but it is now one of three
planes (filesystem/user + network + injected-secret), each independently
verified by the exit tests.

## Kind-2 secret inventory the runner user MUST NOT reach

The 1Password/systemd-creds token, the Dolt tenant password (`BEADS_DOLT_PASSWORD`
source), the GitHub App private key, `/var/lib/doltdb`, and the **runner
registration credential** (below). Verification tests (§"Isolation tests")
assert each is unreadable by the runner user **and** absent from any job
environment.

## Injected-secret discipline (what the workflow HANDS the job)

The at-rest inventory above is necessary but not sufficient: `handoff.md`
§"Threat model" item 6 records that `just check` is **not fully hermetic** — some
targets need GitHub auth (`check-master-ci-green`,
`check-branch-protection-alignment`) and the factory `workflow.toml` passes
`GH_TOKEN` into `just check` subprocesses. Code executing in a moved job can read
whatever the workflow **injects** into its environment, so:

- Moved self-hosted jobs receive **only** a least-privilege Actions
  `GITHUB_TOKEN` with an explicit, read-scoped `permissions:` block (default-deny,
  granted per job).
- **Never** inject the 1Password token, a Dolt tenant password, or a long-lived
  PAT into a self-hosted job.
- Any target that genuinely needs a Kind-2 secret **stays on the GitHub-hosted /
  trusted lane** (recorded in the Phase 2 per-job disposition table).
- Verified by the generalized secret-env test (§"Isolation tests", test 5).

## Runner design

1. **Dedicated unprivileged user** `ci-runner` (name TBD), created with **no**
   membership in `docker`, `sudo`, or `dolt`, no sudoers entry, its own home +
   cache dirs. This is the primary containment boundary. **`ci-runner` MUST NOT
   be added to the `docker` group** as a convenience fallback — that group's
   socket is host-root-equivalent and would expose every Kind-2 secret,
   `/var/lib/doltdb`, and all tenants.
2. **Rootless, user-namespaced container — a MUST, not a recommendation.** The
   ephemeral GitHub Actions runner *and* the job it runs execute inside a
   **rootless, user-namespaced** container instantiated from the baked toolchain
   image, launched by a container engine running **as `ci-runner`**. CI thus runs
   the *exact* image the Fabro sandbox uses, jobs execute directly in it (no
   nested per-step containers), and **`/var/run/docker.sock` is never mounted**;
   the docker daemon / `docker` group is never used. Concrete constraints, all
   verified by exit tests:
   - container UID 0 maps to `ci-runner`'s **subuid** range, **not** host root;
   - `--privileged` is rejected; no added capabilities beyond the minimal
     default set;
   - **no** host-filesystem bind mounts except the explicitly-listed secret-free
     cache dirs;
   - a process inside the container cannot read any Kind-2 path.
   - **Mechanism (an implementation choice, validated at re-review — the design
     constrains the *property*, not the tool):** rootless **podman** (+ `uidmap`
     + `slirp4netns`/`pasta` + `crun`) is the recommended default; rootless
     **dockerd** scoped to `ci-runner`, or a **bubblewrap**-based user-namespace
     sandbox (bubblewrap is already baked into the images per `handoff.md`), are
     acceptable alternatives **iff** they meet the same verified constraints.
     Whatever the mechanism, it **MUST** be rootless + user-namespaced — a
     rootful fallback is forbidden.
   - *Alternative considered:* install the toolchain directly in `ci-runner`'s
     host environment (no container). Rejected: it drops the image-parity +
     throwaway-filesystem guarantees.
   - **Image builds do NOT run here** — building needs a privileged builder; it
     stays GitHub-hosted / on the trusted builder (see `handoff.md`).
3. **Ephemeral execution:** `--ephemeral` runner — one job per registration,
   auto-deregisters after that job; fresh filesystem each job. Because the runner
   agent and the job share the container, a job can read the agent's single-use
   registration token; `--ephemeral` bounds that blast radius to exactly one
   already-consumed registration. (Optional belt-and-suspenders: run the job in a
   nested container distinct from the agent; otherwise the ephemeral bound is
   accepted explicitly.)

## Provisioning pre-gate — the rootless stack (host mutation, gated)

Because the rootless backbone is **not present today** (host survey), Phase 0
implementation **begins** with a provisioning step — itself gated behind this
design's round-2 re-review + explicit maintainer authorization:

1. Install the rootless container stack: `podman` + `uidmap` +
   `slirp4netns`/`pasta` + `crun` (or the chosen mechanism's equivalents).
2. Add `ci-runner` **subuid/subgid** ranges.
3. **Verify rootless operation before any runner registration:** the container
   engine reports rootless mode for `ci-runner`, and a positive mapping test
   shows a container process maps to a `ci-runner` subuid on the host (not host
   uid 0).
4. **No runner registration precedes a passing rootless-verification test.**

## Network isolation

- The job container runs in an **isolated network namespace**;
  `--network=host` / `--net=host` is **FORBIDDEN**.
- **Default-deny egress.** A check that must reach a host service is granted
  exactly that one service via a narrow proxied port — never raw host loopback.
- The netns backend (`slirp4netns`/`pasta`) is part of the provisioning pre-gate.
- **Verified:** a job **cannot** open a TCP connection to `127.0.0.1:3307` (the
  multi-tenant Dolt server) or the OTel collector's port (§"Isolation tests",
  test 8).

## Trusted-event routing — a positive allowlist invariant

Routing is a **deny-by-default allowlist**, not a per-job convention. A
self-hosted label is allowed **only** for:

- `push` to the protected `master` branch, and
- `pull_request` where the head repo **equals** the base repo
  (`github.event.pull_request.head.repo.full_name == github.repository`).

Everything else stays on GitHub-hosted runners:

- **`merge_group` stays hosted.** A merge-queue entry can carry fork-originated
  commits, so it is **not** trusted for self-hosted execution unless every PR in
  the group is provably same-repo. Cache write-back is reserved for post-merge
  `push` to `master` (not `merge_group`).
- **All privileged / non-PR trigger classes stay hosted.** Explicitly **forbid**
  self-hosted labels on `pull_request_target`, `workflow_run`, `issue_comment`,
  label/comment-triggered, `repository_dispatch`, and manual (`workflow_dispatch`)
  workflows that could checkout, download, interpret, or execute fork-controlled
  content. (Verified: livespec's local workflows use none of these today —
  `ci.yml` is `pull_request` / `push` / `merge_group` only — so this is a
  preventive fleet-template invariant, not a live hole.)

**The `head.repo == repository` predicate is defense-in-depth, NOT the boundary.**
For a `pull_request` event a fork controls its **own** workflow YAML and can add
`runs-on: self-hosted` and strip the `if:` predicate. The **load-bearing
boundary** is therefore the **repo setting requiring approval to run workflows
for all outside collaborators / all fork PRs** (strictest tier). *Approving a
fork PR to get CI = running attacker-controlled code on the runner*, contained
only by the rootless / network / injected-secret planes above. (For
base-controlled contexts such as `pull_request_target` the predicate *is*
reliable — but those stay hosted regardless.)

**Repo setting:** require approval to run workflows for **all outside
collaborators / all fork PRs**.

**Verified two ways:** (a) a **static workflow-audit** exit test asserts no
self-hosted-labeled job is reachable from a forbidden trigger; (b) an honest test
fork PR does not trigger any self-hosted-labeled job — but this can only test an
*honest* fork; the adversarial-YAML case is carried by the approval gate +
containment, not by routing.

## Supervisor + registration credential (a Kind-2 secret)

The owner is a personal account, so runners are **repo-level, ephemeral**; a
**supervisor** re-registers after each job using short-lived registration tokens.

- **Credential:** a **GitHub App** with repo-administration scope (recommended
  over a PAT — App tokens are short-lived, scoped, auditable). Its private key
  lives in **systemd-creds** (`LoadCredential=`), readable ONLY by the supervisor
  service — never by `ci-runner`, never mounted into the job container.
- **Flow:** the supervisor mints a **short-lived registration token**, hands
  ONLY that token to a freshly-launched ephemeral runner container, which uses it
  once and dies. The job never sees the App key or a long-lived token.
- **Launch mechanism (no docker socket, no sudo — specified, not left open):**
  the supervisor triggers a systemd unit that runs the ephemeral runner container
  **as `ci-runner`** (e.g. a templated `User=ci-runner` service, or a
  `ci-runner`-scoped rootless-engine invocation), passing **only** the
  short-lived registration token via a systemd credential or a `ci-runner`-only
  runtime path. The supervisor never grants `ci-runner` `docker`/`sudo`, and
  never uses the docker socket to launch the container. (Leaving this
  unspecified is what would otherwise reintroduce the socket.)
- The supervisor runs as its own hardened systemd service (own low-priv user or
  `DynamicUser=`, `LoadCredential=` for the key, no shell for `ci-runner`).

## Caches — trust-tiered, secret-free, supervisor-enforced

Persistent local-disk cache dirs (`~/.cache/uv`, `~/.cargo/registry`) owned by
`ci-runner`, carrying **no secrets**. The trust tier is enforced
**supervisor-side, keyed on the EVENT** — **not** on a workflow-declared label
(a fork controls its own labels):

- The supervisor classifies each run from the triggering event; only a
  supervisor-classified **trusted post-merge** run gets a writable cache mount.
- **PR / untrusted-lane jobs get read-only (or throwaway-overlay) mounts** and
  never reach a writable cache.
- **Per-repo namespaces** so a poisoned object from one repo can't flow into
  another's build. (`sccache` stays trusted-tier-only / deferred.)
- Verified by a **mount-level write-denial** exit test (test 10).

## Isolation tests (Phase 0 exit criteria — must all pass)

1. `ci-runner` is in **NONE** of `docker` / `sudo` / `dolt`; has no sudoers
   entry; is explicitly **not** in the `docker` group.
2. As `ci-runner`: cannot read `/var/lib/doltdb`, the 1Password wrapper
   `.env.local`, the GitHub App private key, or the Dolt-password source
   (`test ! -r <path>` for each).
3. As `ci-runner`: `sudo -n true` fails.
4. The job container has **no** `/var/run/docker.sock`.
5. **(generalized)** `printenv` in a job shows **no** Kind-2 secret (App key,
   registration token, 1Password token, Dolt password) **and** the `GITHUB_TOKEN`
   present is read-scoped.
6. An **honest fork PR** opened against a public repo does **not** trigger any
   self-hosted-labeled job (routed to `ubuntu-latest`).
7. **(rootless)** the container engine runs **rootless as `ci-runner`**; container
   UID 0 maps to a `ci-runner` subuid on the host (not 0); `--privileged` is
   rejected; there are no broad host-filesystem mounts; a process inside the
   container cannot read any Kind-2 path.
8. **(network)** a job **cannot** open a TCP connection to `127.0.0.1:3307` (Dolt)
   or the OTel collector port; `--network=host` is not in effect.
9. **(static workflow audit)** no self-hosted-labeled job is reachable from a
   forbidden trigger (`merge_group`, `pull_request_target`, `workflow_run`,
   `issue_comment`, label, `repository_dispatch`, `workflow_dispatch`);
   `merge_group` + privileged triggers are hosted-only.
10. **(cache write-denial)** an untrusted-lane job's cache mount is
    read-only / throwaway; only a supervisor-classified trusted post-merge run
    writes back.

## Gate — dual adversarial review before ANY host mutation

**Maintainer-declared 2026-07-12.** Before provisioning the rootless stack,
creating the user, installing the runner, or registering anything, this design
passes a **separate adversarial review by (a) a Fable-model agent AND (b) a Codex
agent**, each running independently and READ-ONLY, each tasked to find **serious
security blockers** — fork-PR code-execution escape, secret leakage into the job
env, privilege escalation, socket/host-filesystem exposure, network reach to
host services, registration-credential exposure — **not nitpicks**. Iterate the
design until **BOTH** return **no serious blockers**. A no-serious-blockers
verdict from both is the precondition for implementation. Record each round's
findings + resolutions on `livespec-3lev.3`.

**Round 1: COMPLETE (2026-07-12) — both SERIOUS-BLOCKERS-FOUND** (see next
section). This revision resolves every finding. **Round 2 (fresh Fable + fresh
Codex over this revised design) is REQUIRED and pending** before any host
mutation.

## Round 1 dual-review record — findings & resolutions (2026-07-12)

Both reviewers ran independently, read-only, and verified claims against the live
host; **both returned SERIOUS-BLOCKERS-FOUND**. Six raw findings dedupe to four
themes, all resolved in this revision:

- **① Rootless containment backbone un-provisioned AND un-enforced** — *Fable B1*
  (host survey: `podman`/`uidmap`/`slirp4netns`/`crun` absent; only rootful
  `docker` present; the exit tests never assert rootlessness, so the tempting
  shortcut is the docker group = host root) **+ Codex B3** (rootless written as
  "recommended" not a MUST; a rootful/`--privileged`/host-mount fallback would
  silently invalidate the claim). Both hit the single load-bearing hole from
  different angles. → **Resolved:** rootless is now a **MUST** (§"Runner design"
  item 2) with a **provisioning pre-gate** (§) and concrete verified constraints
  (test 7); the `docker`-group / socket fallback is explicitly forbidden.
- **② Network plane omitted** — *Fable B2*: the design reasoned only about
  files/users while the multi-tenant Dolt server is reachable on
  `127.0.0.1:3307`; `--network=host` or a misconfigured netns opens a
  cross-tenant path. → **Resolved:** §"Network isolation" (isolated netns, host
  networking forbidden, default-deny egress) + test 8.
- **③ Trusted-event routing not deny-by-default** — *Codex B1* (`merge_group` can
  carry fork commits into the runner) **+ Codex B2** (privileged non-PR triggers
  — `pull_request_target`, `workflow_run`, `issue_comment`, label,
  `repository_dispatch`, manual — not banned) **+ Fable non-blocking** (the
  `head.repo == repository` predicate is attacker-controllable for
  `pull_request`; the approval gate is the real boundary). → **Resolved:**
  §"Trusted-event routing" rewritten as a **positive allowlist invariant**;
  `merge_group` + privileged triggers hosted-only; the approval-gate repo setting
  named as the boundary and the predicate demoted to defense-in-depth; static
  workflow-audit test 9.
- **④ Injected secrets, not just at-rest** — *Fable B3*: `just check` is not fully
  hermetic (`GH_TOKEN` reaches subprocesses); exit test 5 only checked the App
  key. → **Resolved:** §"Injected-secret discipline" (least-privilege
  `GITHUB_TOKEN` only; no Kind-2 secret into a self-hosted job; secret-needing
  targets stay hosted) + generalized test 5.

**Secondary items folded in:** the supervisor→`ci-runner` container-launch
mechanism is now specified without socket/sudo (§"Supervisor"); cache tiering is
enforced **supervisor-side, keyed on the event** (§"Caches") with a write-denial
test (test 10); least-privilege `permissions:` on moved jobs (§"Injected-secret
discipline"); the shared runner-agent/job container blast-radius is bounded and
noted explicitly (§"Runner design" item 3).

**Verdict shape both reviewers returned** is retained on `livespec-3lev.3` (the
epic child) as the round-1 record; this revision is the resolution half.

## Rollback

Each step is reversible and reversal is written into the Phase 0 work-item:
deregister the runner (short-lived token), stop + disable the supervisor service,
delete the `ci-runner` user + its caches, and (in CI) revert the moved jobs'
`runs-on` to `ubuntu-latest`. If the local-runner approach is abandoned entirely,
also uninstall the provisioned rootless stack. A partial state (runner built but
CI not yet cut over — Phase 2) is a valid pause point.

## Sequencing

Phase 0 is a **non-gating shadow lane** (one repo's `just check` green on the
runner, not blocking merges) and is NOT gated by any P-host baseline (that was
retired — see `handoff.md`). It **IS** gated by the dual adversarial review above.

Implementation order once the gate clears (each step behind its passing exit
tests): **provisioning pre-gate** (rootless stack + subuid/subgid +
rootless-verification test) → `ci-runner` user + supervisor + registration wiring
→ trusted-event routing + network isolation → one repo's `just check` green on
the runner as the non-gating shadow lane.
