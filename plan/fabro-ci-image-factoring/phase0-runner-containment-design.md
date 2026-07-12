# Phase 0 — local-runner containment & security design

**Status:** design artifact, drafted 2026-07-12, grounded in a read-only host
survey + the `handoff.md` threat model. **Revised through ROUND 2** of the dual
adversarial review (each round a fresh Fable-model agent AND a fresh Codex agent,
independent + read-only; rounds 1 and 2 BOTH returned SERIOUS-BLOCKERS-FOUND —
findings + resolutions in §"Round 1 dual-review record" and §"Round 2 dual-review
record"). **NO host was mutated** by any review or revision. This design remains
**gated**: it must pass a FRESH round-3 dual review (§"Gate") before ANY host
change (AppArmor-profile install, rootless-stack provisioning, user creation,
runner install, registration) is made. Companion to `handoff.md`; tracked as epic
child `livespec-3lev.3`.

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
   reach host-loopback services **by any path the container backend exposes**
   (the multi-tenant Dolt server binds loopback; see §"Network isolation").
3. **Injected secrets** — no Kind-2 secret is ever handed into a job's
   environment (containment of what the workflow *gives* the job, not only what
   it can read at rest).

All three planes ultimately depend on the **rootless, user-namespaced** execution
of the job — which, on this specific host, is **actively blocked by AppArmor**
and can only be enabled by a *scoped* profile, never a host-wide downgrade (round
2's central finding; see host survey + §"Provisioning pre-gate").

### The host as it is today (survey, 2026-07-12)

- `ubuntu` (uid 1000) is in **both `docker` and `sudo`** and has **passwordless
  sudo**. The runner must therefore **never** run as `ubuntu`. (`ubuntu` is in
  `dolt-admin`, **not** `dolt`; `/var/lib/doltdb` is `0750 dolt:dolt`, so
  `dolt-admin` grants no traversal — `ci-runner` will be in neither.)
- Only one uid≥1000 user exists (`ubuntu`) — Phase 0 creates the runner user.
- `/var/lib/doltdb` is `0750 dolt:dolt` (untraversable by a non-`dolt` user).
- The 1Password wrapper secret (`/data/projects/1password-env-wrapper/.env.local`)
  is `0600 ubuntu` (unreadable by a non-`ubuntu` user).
- **(round-2 verified — the load-bearing host fact) Unprivileged user-namespace
  creation is ACTIVELY BLOCKED by AppArmor on this host.** The OS is Ubuntu 25.10;
  both `kernel.apparmor_restrict_unprivileged_userns=1` **and**
  `kernel.apparmor_restrict_unprivileged_unconfined=1` are set, and
  `unshare -Ur -- true` / `unshare -Urn -- true` **both fail with
  `Operation not permitted`** writing `/proc/self/uid_map` (the textbook
  unprivileged-userns-restriction signature — not a missing-`newuidmap` error).
  So a fresh unconfined `ci-runner` **cannot create a user namespace today**, and
  **installing the rootless stack does NOT change this** — the block is at the LSM
  layer, above the container runtime. This is the reason the provisioning pre-gate
  requires a **scoped AppArmor profile** and forbids the host-wide downgrade (§).
- **(round-1 verified) The rootless-container stack is NOT installed.** `podman`,
  `newuidmap`/`newgidmap` (the `uidmap` package), `slirp4netns`, and `crun` are
  all **absent**; the only container runtime present is **rootful `docker`**
  (socket `srw-rw---- root:docker /var/run/docker.sock`) + `runc`.
  `/etc/subuid` and `/etc/subgid` carry a range **only for `ubuntu`**, none for a
  future `ci-runner`. → The rootless backbone must be **provisioned and verified**
  before it can be relied upon (see §"Provisioning pre-gate"); until then the
  only working runtime is root-equivalent, which is why a docker-group / socket
  fallback is explicitly forbidden below.
- **(round-1 verified, round-2 expanded) Host-loopback listeners.** The
  multi-tenant Dolt SQL server listens on `127.0.0.1:3307` serving every tenant;
  the OTel collector also binds loopback; and a round-2 survey found the host
  additionally listens on `127.0.0.1:9222` (Chrome DevTools remote-debug —
  session/cookie theft if reachable), `:5432` (postgres ×2), `:445` (SMB), and
  `:8000/8001/8888`. → Containment must deny the job **all** of these by **every**
  backend path, not a named pair (see §"Network isolation").
- **Image base vs host OS:** the baked image base is `buildpack-deps:noble`
  (24.04) while the host is Ubuntu **25.10**. Harmless for the container itself
  (no host-OS match needed), but the provisioning packages
  (`podman`/`uidmap`/`slirp4netns`/`crun` availability) **and the AppArmor profile
  paths/format** MUST be validated against **25.10**, not 24.04.

**Isolation backbone:** the primary boundary is still a dedicated unprivileged
user in **none** of `docker` / `sudo` / `dolt` — but it is now one of three
planes (filesystem/user + network + injected-secret), each independently
verified by the exit tests, and all three rest on the scoped-AppArmor-enabled
rootless userns.

## Kind-2 secret inventory the runner user MUST NOT reach

The 1Password/systemd-creds token, the Dolt tenant password (`BEADS_DOLT_PASSWORD`
source), the GitHub App private key, `/var/lib/doltdb`, and the **runner
registration credential / agent material** (below). Verification tests
(§"Isolation tests") assert each is unreadable by the runner user **and** absent
from any job environment **and** (for the registration material) not visible from
inside a job.

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
   - **the user namespace is enabled ONLY via a scoped AppArmor profile** (§
     "Provisioning pre-gate") — never by disabling the host-wide
     `kernel.apparmor_restrict_unprivileged_userns` / `..._unconfined` sysctls,
     and never via a setuid-root `bwrap`/runtime;
   - container UID 0 maps to a subuid **that is NOT host uid 0** (a `ci-runner`
     subuid, or — for engines that map container-root to the invoking user — the
     unprivileged `ci-runner` uid; the security property is *not host root*,
     which is what the test asserts);
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
     acceptable alternatives **iff** they meet the same verified constraints
     **and** the scoped-AppArmor-profile requirement. Whatever the mechanism, it
     **MUST** be rootless + user-namespaced — a rootful fallback is forbidden.
   - *Alternative considered:* install the toolchain directly in `ci-runner`'s
     host environment (no container). Rejected: it drops the image-parity +
     throwaway-filesystem guarantees.
   - **Image builds do NOT run here** — building needs a privileged builder; it
     stays GitHub-hosted / on the trusted builder (see `handoff.md`).
3. **Ephemeral execution + registration material never exposed to the job.**
   `--ephemeral` runner — one job per registration, auto-deregisters after that
   job; fresh filesystem each job. **The job MUST NOT be able to read the runner
   registration token or agent credential material** (round-2 Codex B2: a token
   reusable within its validity window would let approved-fork attacker code
   register an attacker-controlled runner on the public repo). Concretely:
   - Prefer GitHub's **just-in-time (JIT) runner configuration** (`--jitconfig`),
     which yields true one-run semantics without a re-registerable token; OR
     **split the registration/agent material from job execution** so job code
     cannot read it (agent material owned by the supervisor / a separate user,
     unmounted or deleted before the job accepts work).
   - Verified by test 11 (no registration token / runner-credential files /
     revealing process args / systemd-credential mounts are visible from inside a
     job, and a reuse attempt of any exposed registration material fails).

## Provisioning pre-gate — AppArmor profile + rootless stack (host mutation, gated)

Because unprivileged userns is **AppArmor-blocked** and the rootless stack is
**absent** (host survey), Phase 0 implementation **begins** with provisioning —
itself gated behind this design's round-3 re-review + explicit maintainer
authorization. Order and MUST/MUST-NOT constraints:

1. **Author + install a SCOPED AppArmor profile** that grants unprivileged
   user-namespace creation **only** to the runner launcher (validated against
   Ubuntu **25.10** profile paths/format). This is the ONLY acceptable way to
   enable the userns on this host.
2. **MUST NOT** disable `kernel.apparmor_restrict_unprivileged_userns` or
   `kernel.apparmor_restrict_unprivileged_unconfined` host-wide — that removes a
   kernel hardening protecting **every** Dolt tenant, **every** Fabro sandbox, and
   the whole host, purely to run CI. **MUST NOT** use a setuid-root `bwrap` or
   container runtime (a classic privesc surface).
3. Install the rootless container stack: `podman` + `uidmap` +
   `slirp4netns`/`pasta` + `crun` (or the chosen mechanism's equivalents),
   package availability validated against Ubuntu 25.10.
4. Add `ci-runner` **subuid/subgid** ranges.
5. **Verify — before any runner registration:** (a) both sysctls above still read
   **`=1`** (host-wide hardening intact); (b) the container engine reports
   rootless mode for `ci-runner`; (c) a positive mapping test shows a container
   process maps to a value that is **NOT host uid 0** — and that this works **only
   via the scoped profile**, proving containment was achieved WITHOUT a host-wide
   downgrade.
6. **No runner registration precedes a passing rootless-verification test.**

## Network isolation

The job must have **no reachable route to any host-loopback service by ANY path
the container backend provides** — not merely a blocked container-`127.0.0.1`
(round-2 Codex B1: rootless backends expose host loopback through a gateway such
as `host.containers.internal` or the slirp/pasta gateway address, which reaches
the host-side listener even when plain `127.0.0.1` inside the container is
isolated).

- The job container runs in an **isolated network namespace**;
  `--network=host` / `--net=host` is **FORBIDDEN**.
- **The chosen backend is configured with host-loopback disabled** (no
  `host.containers.internal`, no host-gateway route), or the job runs with **no
  host-loopback route at all**. **Default-deny egress**; a check that genuinely
  must reach a host service gets exactly that one service via a narrow proxied
  port — never raw host loopback.
- The netns backend (`slirp4netns`/`pasta`) is part of the provisioning pre-gate.
- **Verified (test 8):** from inside a job, **every** host-loopback path the
  backend offers is denied — container `127.0.0.1`, the backend gateway IP(s),
  `host.containers.internal`, and any configured proxy path — against **all** host
  listeners (Dolt `:3307`, the OTel collector, and `:9222/:5432/:445/:8000/:8001/
  :8888`). Any reachable host-loopback route is a **failed** gate.

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
**supervisor** re-registers after each job using short-lived registration tokens
(or mints JIT configs, §"Runner design" item 3).

- **Credential:** a **GitHub App** with repo-administration scope (recommended
  over a PAT — App tokens are short-lived, scoped, auditable). Its private key
  lives in **systemd-creds** (`LoadCredential=`), readable ONLY by the supervisor
  service — never by `ci-runner`, never mounted into the job container.
- **Flow:** the supervisor mints a **short-lived registration token / JIT config**,
  hands ONLY that to a freshly-launched ephemeral runner, which uses it once and
  dies. The job never sees the App key or a re-registerable token.
- **Launch mechanism + privilege bridge (named, not left open).** A hardened,
  low-privilege (or `DynamicUser=`) supervisor cannot itself start a process **as**
  a different user (`ci-runner`) without an explicit privilege bridge — and that
  bridge MUST be narrow. The design specifies: the supervisor **starts a
  pre-installed, templated systemd unit** (`runner@<id>.service` with a fixed
  `User=ci-runner`) via a **narrowly-scoped polkit rule / systemd grant limited to
  exactly that unit** — **NOT** a broad `sudo`, a blanket `systemctl` grant, or
  the docker socket. Only the registration token / JIT config crosses to the unit,
  via a systemd credential or a `ci-runner`-only runtime path. (Leaving this
  bridge unspecified is what would otherwise be solved with a broad grant that
  reintroduces privilege.)
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
7. **(rootless + host-hardening intact)** the container engine runs **rootless as
   `ci-runner`**; container UID 0 maps to a value that is **NOT host uid 0**;
   `--privileged` is rejected; there are no broad host-filesystem mounts; a
   process inside the container cannot read any Kind-2 path; **AND** both
   `kernel.apparmor_restrict_unprivileged_userns` and `..._unconfined` still read
   **`=1`** with the userns working **only via the scoped AppArmor profile** (no
   host-wide downgrade, no setuid-root runtime).
8. **(network — all host-loopback paths)** from a job, **no** host-loopback route
   the backend provides is reachable — container `127.0.0.1`, the backend
   gateway IP(s), `host.containers.internal`, and any proxy path — against Dolt
   `:3307`, the OTel collector, and `:9222/:5432/:445/:8000/:8001/:8888`;
   `--network=host` is not in effect.
9. **(static workflow audit)** no self-hosted-labeled job is reachable from a
   forbidden trigger (`merge_group`, `pull_request_target`, `workflow_run`,
   `issue_comment`, label, `repository_dispatch`, `workflow_dispatch`);
   `merge_group` + privileged triggers are hosted-only.
10. **(cache write-denial)** an untrusted-lane job's cache mount is
    read-only / throwaway; only a supervisor-classified trusted post-merge run
    writes back.
11. **(registration material not exposed)** from inside a job, no registration
    token / runner-credential files / revealing process args / systemd-credential
    mounts are visible, **and** a reuse attempt of any exposed registration
    material fails.

## Gate — dual adversarial review before ANY host mutation

**Maintainer-declared 2026-07-12.** Before installing the AppArmor profile,
provisioning the rootless stack, creating the user, installing the runner, or
registering anything, this design passes a **separate adversarial review by (a) a
Fable-model agent AND (b) a Codex agent**, each running independently and
READ-ONLY, each tasked to find **serious security blockers** — fork-PR
code-execution escape, secret leakage into the job env, privilege escalation,
socket/host-filesystem exposure, network reach to host services,
registration-credential exposure — **not nitpicks**. Iterate the design until
**BOTH** return **no serious blockers**. A no-serious-blockers verdict from both
is the precondition for implementation. Record each round's findings +
resolutions on `livespec-3lev.3`.

**Round 1: COMPLETE (2026-07-12) — both SERIOUS-BLOCKERS-FOUND** (§"Round 1
dual-review record"). **Round 2: COMPLETE (2026-07-12) — both
SERIOUS-BLOCKERS-FOUND** (§"Round 2 dual-review record"); this revision resolves
every round-2 finding. **Round 3 (fresh Fable + fresh Codex over this revised
design) is REQUIRED and pending** before any host mutation.

## Round 1 dual-review record — findings & resolutions (2026-07-12)

Both reviewers ran independently, read-only, and verified claims against the live
host; **both returned SERIOUS-BLOCKERS-FOUND**. Six raw findings dedupe to four
themes, all resolved:

- **① Rootless containment backbone un-provisioned AND un-enforced** — *Fable B1*
  (host survey: `podman`/`uidmap`/`slirp4netns`/`crun` absent; only rootful
  `docker` present; exit tests never asserted rootlessness) **+ Codex B3**
  (rootless written as "recommended" not a MUST; a rootful/`--privileged`/
  host-mount fallback would silently invalidate the claim). → **Resolved:**
  rootless is a **MUST** with a **provisioning pre-gate** + verified constraints
  (test 7); the `docker`-group / socket fallback is explicitly forbidden.
- **② Network plane omitted** — *Fable B2*: the multi-tenant Dolt server is
  reachable on `127.0.0.1:3307`; `--network=host` opens a cross-tenant path. →
  **Resolved:** §"Network isolation" + test 8.
- **③ Trusted-event routing not deny-by-default** — *Codex B1* (`merge_group` can
  carry fork commits) **+ Codex B2** (privileged non-PR triggers not banned) **+
  Fable non-blocking** (the `head.repo == repository` predicate is
  attacker-controllable). → **Resolved:** §"Trusted-event routing" rewritten as a
  positive allowlist invariant; `merge_group` + privileged triggers hosted-only;
  approval-gate named as the boundary; static workflow-audit test 9.
- **④ Injected secrets, not just at-rest** — *Fable B3*: `just check` is not fully
  hermetic (`GH_TOKEN` reaches subprocesses). → **Resolved:** §"Injected-secret
  discipline" + generalized test 5.

Secondary folded in: supervisor→`ci-runner` launch specified without socket/sudo;
cache tiering supervisor-side keyed on the event + write-denial test 10;
least-privilege `permissions:` on moved jobs.

## Round 2 dual-review record — findings & resolutions (2026-07-12)

Fresh Fable + fresh Codex over the round-1-revised design; **both returned
SERIOUS-BLOCKERS-FOUND** (fewer, deeper findings — the gate is converging). Both
confirmed **Theme 3 (routing)** and **Theme 4 (injected secrets)** CLOSED. Three
serious items, all resolved in this revision:

- **① The rootless backbone is AppArmor-BLOCKED on this host, and the pre-gate
  would accept a host-wide downgrade** — *Fable B1* (host-verified: Ubuntu 25.10,
  both userns sysctls `=1`, `unshare -Ur`/`-Urn` EPERM; installing the stack does
  not help; the "verify rootless works" test would pass after
  `sysctl ...=0` or a setuid-root `bwrap`, silently trading away host-wide
  hardening). → **Resolved:** the provisioning pre-gate now requires a **scoped
  AppArmor profile** (the only acceptable path), forbids the host-wide sysctl
  downgrade and setuid-root runtimes, validates against Ubuntu 25.10, and test 7
  reads back both sysctls (`=1`) proving containment was achieved WITHOUT a
  host-wide downgrade; the host-facts section now records userns as actively
  AppArmor-blocked, not merely "absent."
- **② Network isolation under-tested — the backend host-loopback gateway** —
  *Codex B1* (serious) **+ Fable non-blocking**: a job blocked from container
  `127.0.0.1` can still reach host-side Dolt via `host.containers.internal` / the
  slirp/pasta gateway; and the host exposes more listeners than the tested pair
  (`:9222/:5432/:445/:8000/:8001/:8888`). → **Resolved:** §"Network isolation"
  now requires no host-loopback route by ANY backend path (host-loopback disabled
  on the backend), and test 8 denies every backend path against all host
  listeners.
- **③ Registration-token / runner-agent-material exposure to the job** — *Codex
  B2*: the job shares the container with the agent and could read its "single-use"
  registration token; if reusable within its window, attacker code registers its
  own runner. → **Resolved:** §"Runner design" item 3 now forbids exposing
  registration/agent material to the job (JIT config or split agent material),
  with a negative test 11 (no cred material visible from a job + reuse fails).

Secondary folded in: the supervisor's cross-user launch **privilege bridge** is
now named (a narrowly-scoped polkit/systemd grant limited to the templated
`runner@.service`, never broad `sudo`/`systemctl`); the `noble` (24.04) vs host
25.10 base mismatch is recorded with a MUST to validate provisioning packages +
AppArmor paths against 25.10; test 7's UID assertion is corrected to **"not host
uid 0"** (some engines map container-root to the invoking user, not always a
subuid); and the Phase-2 `/data/projects` sibling-clone plan is flagged against
the "no host-fs bind mounts" rule (§"Sequencing").

## Rollback

Each step is reversible and reversal is written into the Phase 0 work-item:
deregister the runner (short-lived token), stop + disable the supervisor service,
delete the `ci-runner` user + its caches, and (in CI) revert the moved jobs'
`runs-on` to `ubuntu-latest`. If the local-runner approach is abandoned entirely,
also uninstall the provisioned rootless stack **and remove the scoped AppArmor
profile** (leaving the host-wide sysctls untouched — they were never changed). A
partial state (runner built but CI not yet cut over — Phase 2) is a valid pause
point.

## Sequencing

Phase 0 is a **non-gating shadow lane** (one repo's `just check` green on the
runner, not blocking merges) and is NOT gated by any P-host baseline (that was
retired — see `handoff.md`). It **IS** gated by the dual adversarial review above.

Implementation order once the gate clears (each step behind its passing exit
tests): **provisioning pre-gate** (scoped AppArmor profile → rootless stack →
subuid/subgid → rootless-verification test with sysctls still `=1`) → `ci-runner`
user + supervisor + registration wiring (JIT / split agent material) →
trusted-event routing + network isolation (all-loopback-path deny) → one repo's
`just check` green on the runner as the non-gating shadow lane.

**Cross-phase flag (Phase 2).** Phase 2's plan to point checks at on-host
`/data/projects` sibling clones (for cross-repo consistency checks) must be
reconciled with this design's "no host-filesystem bind mounts except secret-free
cache dirs" rule: either keep full-history clones **inside** the job container, or
mount only explicit **public** repo paths **read-only** after a separate
no-secrets permission audit. Do not let Phase 2 reintroduce a broad host-fs mount
that this phase's containment forbids.
