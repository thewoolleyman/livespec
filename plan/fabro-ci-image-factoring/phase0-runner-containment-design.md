# Phase 0 — local-runner containment & security design

**Status:** design artifact, drafted 2026-07-12, grounded in a read-only host
survey + the `handoff.md` threat model. **GATE PASSED at round 4 (2026-07-12):
both a fresh Fable-model agent AND a fresh Codex agent returned
NO-SERIOUS-BLOCKERS** over four iterative rounds (each round a fresh independent
pair; round 1 both SBF → round 2 both SBF → round 3 Fable clean / Codex 1 →
round 4 both clean). Findings + resolutions per round in the §"Round N
dual-review record" sections; this revision also folds the round-4 **non-blocking**
observations (a polish pass — no further review round required). **NO host was
mutated** by any review or revision. Implementation still requires **explicit
maintainer authorization for the first host mutation** (§"Provisioning pre-gate").
Companion to `handoff.md`; tracked as epic child `livespec-3lev.3`.

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

All three planes rest on **rootless, user-namespaced** execution of the job — and
on a fourth, process-level requirement round 3 surfaced: the job runs in a
**different UID + isolated PID namespace from the runner agent**, so job code
cannot read the agent's live credential material (§"Runner design" item 3).

### The host as it is today (survey, 2026-07-12)

- `ubuntu` (uid 1000) is in **both `docker` and `sudo`** and has **passwordless
  sudo**. The runner must therefore **never** run as `ubuntu`. (`ubuntu` is in
  `dolt-admin`, **not** `dolt`; `/var/lib/doltdb` is `0750 dolt:dolt`, so
  `dolt-admin` grants no traversal — `ci-runner` will be in neither.)
- Only one uid≥1000 user exists (`ubuntu`) — Phase 0 creates the runner user.
- `/var/lib/doltdb` is `0750 dolt:dolt` (untraversable by a non-`dolt` user).
- The 1Password wrapper secret (`/data/projects/1password-env-wrapper/.env.local`)
  is `0600 ubuntu` (unreadable by a non-`ubuntu` user).
- **(round-2/round-3 verified — the load-bearing host fact) Unprivileged
  user-namespace creation is AppArmor-restricted, but the host SHIPS enabling
  profiles for the container binaries.** The OS is Ubuntu 25.10; both
  `kernel.apparmor_restrict_unprivileged_userns=1` **and**
  `kernel.apparmor_restrict_unprivileged_unconfined=1` are set, so an
  **unconfined** `unshare -Ur`/`-Urn` fails EPERM on `/proc/self/uid_map`.
  **However**, Ubuntu 25.10 ships
  `/etc/apparmor.d/{bwrap-userns-restrict,podman,runc,unprivileged_userns}`, which
  grant userns to those binaries **by attachment** — so `bwrap --unshare-user`
  returns 0 **despite** the sysctls being `=1` (round-3 verified). The rootless
  path therefore works **via the shipped profiles**, with **no** bespoke profile
  needed and **without** touching the sysctls. The sysctls stay `=1` as
  whole-host hardening; the design's job is to **verify + rely on** the shipped
  profiled path and forbid the two shortcuts that would trade host-wide hardening
  away (disabling the sysctls host-wide; a setuid-root runtime). See
  §"Provisioning pre-gate".
- **(round-1 verified) The rootless-container stack is NOT installed.** `podman`,
  `newuidmap`/`newgidmap` (the `uidmap` package), `slirp4netns`, and `crun` are
  all **absent**; the only container runtime present is **rootful `docker`**
  (socket `srw-rw---- root:docker /var/run/docker.sock`) + `runc`.
  `/etc/subuid` and `/etc/subgid` carry a range **only for `ubuntu`**, none for a
  future `ci-runner`. → The rootless backbone must be **provisioned and verified**
  before it can be relied upon (see §"Provisioning pre-gate"); until then the
  only working runtime is root-equivalent, which is why a docker-group / socket
  fallback is explicitly forbidden below.
- **(round-1 verified, rounds 2–3 expanded) Host-loopback listeners.** The
  multi-tenant Dolt SQL server listens on `127.0.0.1:3307` serving every tenant;
  the OTel collector binds loopback (incl. OTLP/gRPC `:4317`); and surveys found
  the host additionally listens on `:9222` (Chrome DevTools remote-debug —
  session/cookie theft if reachable), `:5432` (postgres, on `127.0.0.1` **and**
  `[::1]`), `:445` (SMB), and `:8000/8001/8888`. → Containment must deny the job
  **all** of these by **every** backend path, verified by **dynamic enumeration**
  of the live IPv4 **and** IPv6 loopback listener set at test time, not a fixed
  port list (see §"Network isolation").
- **Image base vs host OS:** the baked image base is `buildpack-deps:noble`
  (24.04) while the host is Ubuntu **25.10**. Harmless for the container itself
  (no host-OS match needed), but the provisioning packages
  (`podman`/`uidmap`/`slirp4netns`/`crun` availability) **and the AppArmor profile
  paths/format** MUST be validated against **25.10**, not 24.04.

**Isolation backbone:** the primary boundary is still a dedicated unprivileged
user in **none** of `docker` / `sudo` / `dolt` — but it is one of several planes
(filesystem/user + network + injected-secret + agent/job process separation),
each independently verified by the exit tests, and all resting on the
shipped-profile-enabled rootless userns.

## Kind-2 secret inventory the runner user MUST NOT reach

The 1Password/systemd-creds token, the Dolt tenant password (`BEADS_DOLT_PASSWORD`
source), the GitHub App private key, `/var/lib/doltdb`, and the **runner
registration credential / live agent credential material** (below). Verification
tests (§"Isolation tests") assert each is unreadable by the runner user **and**
absent from any job environment **and** (for the runner agent's material) not
reachable from inside a job by file, process, or memory inspection.

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
   runner and its jobs execute inside a **rootless, user-namespaced** container
   instantiated from the baked toolchain image, launched by a container engine
   running **as `ci-runner`**. CI thus runs the *exact* image the Fabro sandbox
   uses, and **`/var/run/docker.sock` is never mounted**; the docker daemon /
   `docker` group is never used. Concrete constraints, all verified by exit tests:
   - **the user namespace is enabled via the host's shipped AppArmor userns
     profiles** (`bwrap-userns-restrict` / `podman`; see §"Provisioning pre-gate")
     — **never** by disabling the host-wide
     `kernel.apparmor_restrict_unprivileged_userns` / `..._unconfined` sysctls,
     and **never** via a setuid-root `bwrap`/runtime;
   - container UID 0 maps to a value **that is NOT host uid 0** (a `ci-runner`
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
     acceptable alternatives **iff** they meet the same verified constraints.
     Whatever the mechanism, it **MUST** be rootless + user-namespaced (via the
     shipped profiles) — a rootful fallback is forbidden.
   - *Alternative considered:* install the toolchain directly in `ci-runner`'s
     host environment (no container). Rejected: it drops the image-parity +
     throwaway-filesystem guarantees.
   - **Image builds do NOT run here** — building needs a privileged builder; it
     stays GitHub-hosted / on the trusted builder (see `handoff.md`).
3. **Ephemeral execution + agent/job separation + no exposed runner material — a
   hard MUST.** `--ephemeral` runner — one job per registration, auto-deregisters
   after that job; fresh filesystem each job. **The job MUST NOT be able to read
   the runner agent's registration OR live credential material — by file,
   process, or memory inspection** (round-3 Codex B1: in a naïve one-container
   model the job shares the agent's UID and PID namespace, so even with the token
   *files* hidden, job code can read `/proc/<agent-pid>/{environ,fd,mem}` or
   `ptrace` the agent and lift the live session/agent credential, then impersonate
   the runner on the public repo — receiving later trusted jobs, poisoning
   results, or capturing their secrets). Two independent controls, **both**
   required:
   - **JIT registration.** Use GitHub's **just-in-time (JIT) runner
     configuration** (`--jitconfig`) so there is no re-registerable registration
     token at all; the supervisor mints per-run JIT config (§"Supervisor").
   - **Agent/job process separation (the hard MUST — not an alternative to JIT).**
     The **job step process runs in an ISOLATED PID namespace from the runner
     agent, with no path to act as the agent's host UID**, so job code cannot see,
     `/proc`-inspect, `ptrace`, or `gcore` the agent. The load-bearing security
     property is stated on the **host-visible** identity: job code cannot become
     or act as the runner-agent's host UID, and cannot reach the agent process —
     achieved by separate **PID + user namespaces** (a separate PID namespace
     alone makes the agent PID unaddressable; cross-userns `ptrace` is denied) and
     no residual capability/setuid path back into the agent's UID boundary.
     Concretely: `/proc` protections (`hidepid=2` / `ProtectProc=invisible` /
     `ProcSubset=pid` or the container-equivalent), `ptrace` denied across the
     boundary, **no shared runner working directory**, and any JIT/session
     material deleted or unmounted from the job's reachable filesystem before job
     code starts. The job still runs from the **same baked image** (image parity
     preserved — the boundary is process/namespace isolation from the agent, not a
     different toolchain).
     - **Mechanism (named so an implementer does not build the naïve model and
       only discover at test 11 that it can't pass):** the stock GitHub Actions
       runner runs job steps as the **same UID + PID namespace** as the agent, so
       the separation needs an explicit interposition —
       **`ACTIONS_RUNNER_CONTAINER_HOOKS`** with a **rootless-podman / bwrap
       backend** running the baked image is the clean, constraint-compatible
       choice (it also covers JS and composite actions, which a "wrap the shell"
       hack does NOT). Because the shipped `bwrap-userns-restrict` profile strips
       the agent process's own caps, the job's namespaces must be created by a
       **fresh nested `bwrap` / rootless-engine invocation** (which carries the
       userns privilege via the shipped profile) — NOT by the agent calling
       `unshare`/`setuid` directly, which would `EPERM`.
     - **Either UID model is acceptable** so long as the host-visible property
       holds: **subuid-range mapping** (job maps to a distinct host subuid) OR a
       **single-uid two-sandbox** model (agent and job both map to the `ci-runner`
       host UID but run in separate PID + user namespaces). Test 11 asserts the
       security property, not a specific numeric-UID difference.
   - Verified by test 11 (a job actively attempts `/proc/<agent-pid>/{environ,
     cmdline,fd,mem}`, `ptrace`/`gcore` reads, runner-workdir credential reads,
     and a token/JIT reuse — all must fail — and asserts PID-namespace separation
     from the agent plus no reachable path to the agent's host-UID identity).

## Provisioning pre-gate — verify shipped AppArmor + rootless stack (host mutation, gated)

Because the rootless stack is **absent** and unprivileged userns is
**AppArmor-gated to profiled binaries** (host survey), Phase 0 implementation
**begins** with provisioning — itself gated behind this design's round-4
re-review + explicit maintainer authorization. Order and MUST/MUST-NOT
constraints:

1. **Verify + rely on the host's SHIPPED AppArmor userns profiles**
   (`/etc/apparmor.d/bwrap-userns-restrict`, `podman`) rather than authoring a
   bespoke exclusive profile — Ubuntu 25.10 already grants userns to those
   binaries (round-3 verified: `bwrap --unshare-user` returns 0 with the sysctls
   `=1`). Only if the chosen engine is **not** covered by a shipped profile does a
   scoped profile get authored (validated against 25.10 profile paths/format);
   it is still **launcher-scoped**, never host-wide.
2. **MUST NOT** disable `kernel.apparmor_restrict_unprivileged_userns` or
   `kernel.apparmor_restrict_unprivileged_unconfined` host-wide — that removes a
   kernel hardening protecting **every** Dolt tenant, **every** Fabro sandbox, and
   the whole host, purely to run CI. **MUST NOT** use a setuid-root `bwrap` or
   container runtime (a classic privesc surface). *(Note: the `uidmap` package's
   `newuidmap`/`newgidmap` ARE setuid-root helpers, but they are standard rootless
   practice for subuid-**range** mapping and are distinct from a setuid-root
   `bwrap`/runtime; single-uid `bwrap` mapping avoids even those — either is
   acceptable.)*
3. Install the rootless container stack: `podman` + `uidmap` +
   `slirp4netns`/`pasta` + `crun` (or the chosen mechanism's equivalents),
   package availability validated against Ubuntu 25.10.
4. Add `ci-runner` **subuid/subgid** ranges (if using subuid-range mapping).
5. **Verify — before any runner registration:** (a) both sysctls above still read
   **`=1`** (host-wide hardening intact); (b) the container engine runs rootless
   as `ci-runner` via the shipped/profiled path; (c) a positive mapping test shows
   a container process maps to a value that is **NOT host uid 0**; (d) the runtime
   binary is **not** setuid-root (`find … -perm -4000`). This proves containment
   was achieved WITHOUT a host-wide downgrade or a setuid runtime.
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
- **Verified (test 8):** the test asserts the **default-deny / isolated-netns
  principle** — from inside a job, **every** host-loopback path the backend offers
  is denied (container `127.0.0.1`, the backend gateway IP(s),
  `host.containers.internal`, any proxy path) against **the live loopback listener
  set enumerated dynamically at test time on both IPv4 and `[::1]`** (which today
  includes Dolt `:3307`, the OTel collector `:4317`, and `:9222/:5432/:445/:8000/
  :8001/:8888`). Any reachable host-loopback route is a **failed** gate.

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
only by the rootless / network / injected-secret / agent-separation planes above.
(For base-controlled contexts such as `pull_request_target` the predicate *is*
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
**supervisor** mints per-run **JIT config** (no re-registerable registration
token) and launches the runner after each job.

- **Credential:** a **GitHub App** with repo-administration scope (recommended
  over a PAT — App tokens are short-lived, scoped, auditable). Its private key
  lives in **systemd-creds** (`LoadCredential=`), readable ONLY by the supervisor
  service — never by `ci-runner`, never mounted into the job container.
- **Flow:** the supervisor mints a **JIT config** for one run, hands ONLY that to
  a freshly-launched ephemeral runner, which uses it once and dies. The job never
  sees the App key, and the JIT material is unreachable from the job step (§
  "Runner design" item 3).
- **Launch mechanism + privilege bridge (named, not left open).** A hardened,
  low-privilege (or `DynamicUser=`) supervisor cannot itself start a process **as**
  a different user (`ci-runner`) without an explicit privilege bridge — and that
  bridge MUST be narrow. The design specifies: the supervisor **starts a
  pre-installed, templated systemd unit** (`runner@<id>.service` with a fixed
  `User=ci-runner` + fixed `ExecStart`) via a **narrowly-scoped polkit rule /
  systemd grant limited to exactly that unit** — **NOT** a broad `sudo`, a blanket
  `systemctl` grant, or the docker socket. Only the JIT config crosses to the unit,
  via a systemd credential or a `ci-runner`-only runtime path. (The fixed
  `User=`/`ExecStart` means instance-name variation grants no new privilege, and
  neither `ci-runner` nor the job is authorized to invoke the unit.)
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
   registration/JIT material, 1Password token, Dolt password) **and** the
   `GITHUB_TOKEN` present is read-scoped.
6. An **honest fork PR** opened against a public repo does **not** trigger any
   self-hosted-labeled job (routed to `ubuntu-latest`).
7. **(rootless + host-hardening intact)** the container engine runs **rootless as
   `ci-runner`** via the shipped/profiled path; container UID 0 maps to a value
   that is **NOT host uid 0**; `--privileged` is rejected; there are no broad
   host-filesystem mounts; a process inside the container cannot read any Kind-2
   path; **AND** both `kernel.apparmor_restrict_unprivileged_userns` and
   `..._unconfined` still read **`=1`**; **AND** the runtime binary is **not**
   setuid-root (`find … -perm -4000` finds none in the launch path).
8. **(network — all host-loopback + link-local, dynamically enumerated)** from a
   job, **no** host-loopback route the backend provides is reachable — container
   `127.0.0.1`, the backend gateway IP(s), `host.containers.internal`, any proxy
   path — against the **live** loopback listener set enumerated at test time on
   IPv4 **and** `[::1]` (illustrative, **not** exhaustive: Dolt `:3307`, collector
   `:4317`/`:4318`, `:9222/:5432/:445/:8000/:8001/:8888`), **and** the link-local
   cloud-metadata endpoint `169.254.169.254` is unreachable (belt-and-suspenders,
   in case the VPS exposes one); `--network=host` is not in effect. The test
   asserts the isolated-netns / default-deny **principle**, not a fixed list.
9. **(static workflow audit)** no self-hosted-labeled job is reachable from a
   forbidden trigger (`merge_group`, `pull_request_target`, `workflow_run`,
   `issue_comment`, label, `repository_dispatch`, `workflow_dispatch`);
   `merge_group` + privileged triggers are hosted-only.
10. **(cache write-denial)** an untrusted-lane job's cache mount is
    read-only / throwaway; only a supervisor-classified trusted post-merge run
    writes back.
11. **(runner-agent material not reachable — files, process, OR memory)** from
    inside a job: (a) the job runs in an **isolated PID namespace** from the agent
    (the agent PID is not visible) and has **no path to act as the runner-agent's
    host UID** — whether the job maps to a distinct host subuid or runs in a
    separate user namespace under the same `ci-runner` host UID (the assertion is
    on the host-visible identity, not an in-container numeric-UID difference); (b)
    active attempts to read `/proc/<agent-pid>/{environ,cmdline,fd,mem}`,
    `ptrace`/`gcore` the agent, and read any runner working-directory credential
    file all **fail**; (c) a reuse attempt of any JIT/registration material fails.

## Gate — dual adversarial review before ANY host mutation

**Maintainer-declared 2026-07-12.** Before verifying/installing the AppArmor +
rootless stack, creating the user, installing the runner, or registering
anything, this design passes a **separate adversarial review by (a) a Fable-model
agent AND (b) a Codex agent**, each running independently and READ-ONLY, each
tasked to find **serious security blockers** — fork-PR code-execution escape,
secret leakage into the job env, privilege escalation, socket/host-filesystem
exposure, network reach to host services, registration-credential exposure —
**not nitpicks**. Iterate the design until **BOTH** return **no serious
blockers**. A no-serious-blockers verdict from both is the precondition for
implementation. Record each round's findings + resolutions on `livespec-3lev.3`.

**GATE STATUS: PASSED at round 4 (2026-07-12).** Round 1: both SBF. Round 2: both
SBF. Round 3: Fable NO-SERIOUS-BLOCKERS, Codex one serious blocker (agent/job
separation). **Round 4: BOTH NO-SERIOUS-BLOCKERS** (§"Round 4 dual-review record").
The no-serious-blockers-from-both precondition for implementation is **met**; the
refinements folded in this polish revision are the round-4 **non-blocking**
observations (no further review round is required). Implementation still requires
**explicit maintainer authorization for the first host mutation**
(§"Provisioning pre-gate").

## Round 1 dual-review record — findings & resolutions (2026-07-12)

Both reviewers, independent + read-only, host-verified; **both SBF**. Six raw
findings → four themes, all resolved: **①** rootless un-provisioned/un-enforced
(Fable B1 + Codex B3) → rootless a MUST + provisioning pre-gate + test 7,
docker-group/socket fallback forbidden; **②** network plane omitted (Fable B2) →
§"Network isolation" + test 8; **③** routing not deny-by-default (Codex B1
`merge_group` + B2 privileged triggers + Fable predicate-attacker-controllable) →
positive-allowlist invariant, approval-gate as boundary, static audit test 9;
**④** injected secrets (Fable B3) → §"Injected-secret discipline" + generalized
test 5. Secondary: supervisor launch without socket/sudo; cache tiering
supervisor-side keyed on event + test 10; least-priv `permissions:`.

## Round 2 dual-review record — findings & resolutions (2026-07-12)

Fresh Fable + fresh Codex over the round-1 revision; **both SBF** (deeper).
Themes 3 + 4 confirmed CLOSED. Three items resolved: **①** rootless backbone
AppArmor-blocked for the unconfined path + the pre-gate would accept a host-wide
downgrade (Fable B1, host-verified) → pre-gate constrained to the profiled path,
host-wide sysctl downgrade + setuid-root forbidden, test 7 sysctl-readback;
**②** network isolation under-tested via the backend host-loopback gateway (Codex
B1 + Fable) → no host-loopback route by ANY backend path, test 8 covers every
path; **③** registration-token/agent-material exposure (Codex B2) → JIT config +
no exposed material, negative test 11. Secondary: supervisor privilege bridge
named; `noble`/25.10 base reconciled; test-7 "not host uid 0"; Phase-2
sibling-clone flagged.

## Round 3 dual-review record — findings & resolutions (2026-07-12)

Fresh Fable + fresh Codex over the round-2 revision. Both confirmed **R2-1
(AppArmor)** and **R2-2 (network)** CLOSED.

- **Fable: NO-SERIOUS-BLOCKERS** (first clean verdict). Non-blocking observations,
  folded into this revision: **O1** — the host ALREADY ships enabling AppArmor
  profiles (`bwrap-userns-restrict`/`podman`/`runc`/`unprivileged_userns`), so
  `bwrap --unshare-user` works with the sysctls `=1`; **no bespoke profile need be
  authored** (host-facts + provisioning pre-gate corrected to "verify + rely on
  the shipped profiles"; test 7's sysctl-readback retained). **O2** — test 8 now
  asserts the default-deny *principle* + **dynamic** IPv4/`[::1]` listener
  enumeration (adds `:4317`, `::1:5432`). **O4** — test 7 now mechanically checks
  the runtime is not setuid-root (`-perm -4000`). **O5** — clarified that the
  `uidmap` `newuidmap`/`newgidmap` setuid helpers are standard rootless practice,
  distinct from the banned setuid-root `bwrap`/runtime.
- **Codex: SERIOUS-BLOCKERS-FOUND (1) — B1: runner-agent memory/proc exposure
  inside the job attack surface.** In a naïve one-container model the job shares
  the agent's UID + PID namespace, so even with JIT hiding token *files*, job code
  can read `/proc/<agent-pid>/{environ,fd,mem}` or `ptrace` the agent to lift its
  live session/agent credential and impersonate the runner on the public repo.
  Test 11 previously checked files only. → **Resolved:** §"Runner design" item 3
  now makes **agent/job process separation a hard MUST** (different UID + isolated
  PID namespace, `/proc` protections, `ptrace` denied, no shared workdir, JIT
  material deleted before job code) **in addition to** JIT, and test 11 is
  extended to actively attempt `/proc`/`ptrace`/`gcore`/workdir reads + a
  JIT-reuse, and to assert the UID + PID-namespace separation.

**Reviewer split, and the disposition:** Fable classified this same tension
(its O3) as *non-blocking* (JIT kills the re-registerable token; the residual live
cred is runner-scoped + ephemeral, no root/tenant reach); Codex classified it
*serious* (same-UID `/proc`/memory inspection lifts the live agent credential →
runner impersonation on a public repo). The design **adopts the conservative
Codex fix** — for a security-containment design the separation is low-cost and
matches the design's no-privilege stance.

## Round 4 dual-review record — GATE PASSED (2026-07-12)

Fresh Fable + fresh Codex over the round-3 revision (Codex run directly via
`codex exec --sandbox read-only`; Fable via an independent read-only agent).
**Both returned NO-SERIOUS-BLOCKERS — the gate is PASSED.** Both confirmed the
round-3 agent/job-separation fix (R3-B1) CLOSED and the R3-2/R3-3 folds accurate
and hole-free (Fable host-verified that the shipped `bwrap-userns-restrict`
profile stacks children under `unpriv_bwrap` with `audit deny capability`, so the
in-userns cap-stripping — hence the hardening — is genuine, not illusory; its
dynamic test-8 enumeration even surfaced a live `:4318` listener the illustrative
list omitted, validating the dynamic-enumeration choice).

The round-4 **non-blocking** observations (none gate the go-ahead) are folded into
this polish revision:

- **Name the R3-1 separation mechanism** (Fable): the stock GitHub Actions runner
  runs job steps as the **same UID + PID namespace** as the agent, so the
  separation needs an explicit interposition — `ACTIONS_RUNNER_CONTAINER_HOOKS`
  with a rootless-podman/bwrap backend running the baked image (covers JS +
  composite actions; a "wrap the shell" hack does not). Named in §"Runner design"
  item 3 so an implementer does not build the naïve model and only discover at
  test 11 that it can't pass.
- **Reconcile the UID-separation wording** (Fable + Codex): the single-uid
  two-sandbox option maps both agent and job to the same host UID, so "job UID
  differs from agent UID" was inconsistent. The property is restated on the
  **host-visible** identity (job code cannot become/act as the agent's host UID or
  reach the agent process), holding via **PID + user namespaces** under either a
  subuid-range or single-uid-two-sandbox model; test 11 now asserts the security
  property, not a numeric-UID difference.
- **Fresh-nested-`bwrap` requirement** (Fable): because `bwrap-userns-restrict`
  strips the agent's caps, the job's namespaces must be created by a fresh nested
  `bwrap`/rootless-engine invocation (which carries the userns privilege via the
  shipped profile), not by the agent calling `unshare`/`setuid` directly (would
  `EPERM`). Noted in the mechanism.
- **Test 8 link-local + illustrative label** (Fable): added the cloud-metadata
  endpoint `169.254.169.254` and `:4318`, and labelled the port list
  illustrative-not-exhaustive (the test is dynamic).
- **"different UID" = no path to regain the agent UID** (Codex): no residual
  capability/setuid route back into the agent's UID boundary — folded into item 3.

## Rollback

Each step is reversible and reversal is written into the Phase 0 work-item:
deregister the runner (JIT expires on its own), stop + disable the supervisor
service, delete the `ci-runner` user + its caches, and (in CI) revert the moved
jobs' `runs-on` to `ubuntu-latest`. If the local-runner approach is abandoned
entirely, also uninstall the provisioned rootless stack (leaving the host-wide
sysctls untouched — they were never changed; any launcher-scoped profile authored
is removed). A partial state (runner built but CI not yet cut over — Phase 2) is a
valid pause point.

## Sequencing

Phase 0 is a **non-gating shadow lane** (one repo's `just check` green on the
runner, not blocking merges) and is NOT gated by any P-host baseline (that was
retired — see `handoff.md`). It **IS** gated by the dual adversarial review above.

Implementation order once the gate clears (each step behind its passing exit
tests): **provisioning pre-gate** (verify shipped AppArmor profiles → rootless
stack → subuid/subgid → rootless-verification test with sysctls still `=1` + no
setuid runtime) → `ci-runner` user + supervisor + JIT wiring with **agent/job
UID+PID-ns separation** → trusted-event routing + network isolation
(all-loopback-path deny) → one repo's `just check` green on the runner as the
non-gating shadow lane.

**Cross-phase flag (Phase 2).** Phase 2's plan to point checks at on-host
`/data/projects` sibling clones (for cross-repo consistency checks) must be
reconciled with this design's "no host-filesystem bind mounts except secret-free
cache dirs" rule: either keep full-history clones **inside** the job container, or
mount only explicit **public** repo paths **read-only** after a separate
no-secrets permission audit. Do not let Phase 2 reintroduce a broad host-fs mount
that this phase's containment forbids.
