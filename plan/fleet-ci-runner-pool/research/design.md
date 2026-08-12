# Fleet CI runner pool — design

Initial research note for the `fleet-ci-runner-pool` plan. Created
2026-08-13.

## The overriding goal, maintainer-declared

**Get GitHub Actions self-hosted CI runners serving the livespec fleet on
`poweredge-xubuntu` as fast as possible.** The maintainer declared this the
plan's overriding goal on 2026-08-13 and explicitly instructed that no
security-theatre or yak-shaving detour may displace it. Where this document
records a constraint, it is because the constraint is already binding — either
in `thewoolleyman/livespec`'s own specification or in the shipped provisioning
kit — not because this plan invented one.

Two things follow from that instruction, and they are recorded here so a later
session does not relitigate them:

- The containment properties below are **inherited, not chosen**. They come
  from `thewoolleyman/livespec`,
  [`SPECIFICATION/non-functional-requirements.md`](https://github.com/thewoolleyman/livespec/blob/master/SPECIFICATION/non-functional-requirements.md)
  §"Self-hosted CI runner host requirements". Re-deriving them is wasted work;
  the shipped kit already satisfies every one of them on a host it has been run
  against.
- Anything not required to make a runner take a job is **out of scope for the
  first green job** and belongs to a later slice.

## What this plan delivers

A **multi-host pool** of ephemeral self-hosted GitHub Actions runners serving
the livespec fleet, with `poweredge-xubuntu` as its first member, and a
documented join procedure that `thewoolleyman/homelab` can follow to add its own
hosts without re-deriving any of this.

The deliverable is not "a box with a runner on it". It is a pool contract plus
one proven member.

## The pool model, and why nothing supersedes anything

GitHub Actions assigns a job to a self-hosted runner by **label match, not by
host**. A job declaring `runs-on: [self-hosted, local-ci]` is dispatched to any
idle runner that carries every one of those labels, on whichever host that
runner happens to live. Hosts register runners independently; each host runs its
own supervisor minting its own registrations against the same repository. There
is no leader, no coordination protocol, and no exclusivity between hosts.

Capacity is therefore **additive**, and redundancy is real: with three hosts
registered, one going down reduces throughput rather than stalling the lane.

This corrects an earlier framing in which `poweredge-xubuntu` would *supersede*
the Hetzner host. It does not. The three known candidate hosts are co-members of
one pool:

| Host | Owner repository driving it | Status as of 2026-08-13 |
|---|---|---|
| `poweredge-xubuntu` | `thewoolleyman/livespec` (this plan) | Owned hardware, on the tailnet, online. Not yet provisioned. |
| `hetzner-prod` | `thewoolleyman/homelab` (`plan/05-hetzner-fleet-member/`, `plan/07-build-substrate/`) | Host build not complete. Blocking `livespec-h22nve`. |
| `gmktec` | `thewoolleyman/homelab` (`plan/11-3-add-ci-runners-to-gmktec/`) | Blocked on `hl-tvn7dd` (thread 11-1). |

What `poweredge-xubuntu` changes is **urgency, not validity**: it brings the
pool to one working member now, so fleet merges stop waiting on hosts that are
still being built. The plan
[`plan/livespec-ci-on-hetzner/`](https://github.com/thewoolleyman/livespec/tree/master/plan/livespec-ci-on-hetzner)
(ledger epic `livespec-h22nve`) stays live and un-demoted in substance; its host
joins this same pool when `thewoolleyman/homelab` finishes it. That thread's
handoff records thirteen consecutive census readings in which its gate did not
move, which is the concrete reason a second host is worth provisioning rather
than continuing to wait on the first.

## Label scheme

Every runner this pool registers carries **three** labels:

| Label | Purpose |
|---|---|
| `self-hosted` | Applied automatically by GitHub to every self-hosted runner. Present whether or not it is requested. |
| `local-ci` | The **shared pool label**. Fleet workflows target this. Any host in the pool can serve it, which is what makes the pool redundant. |
| `<hostname>` — e.g. `poweredge` | A **per-host label**, unique to the box. Never targeted by normal fleet CI. |

Normal jobs route on `[self-hosted, local-ci]` and land wherever there is
capacity. The per-host label exists so a specific box can be targeted
deliberately — to reproduce a host-specific failure, to validate a newly joined
host before it takes shared traffic, or to drain one host by routing away from
it. It costs nothing to add now and is painful to retrofit once several hosts
are registered, because retrofitting means re-minting every registration across
every repository.

The shipped supervisor already accepts this: `ci-runner-supervisor.sh` takes
`--labels` as a comma-separated list, defaulting to `self-hosted,local-ci`, and
passes it through to the just-in-time registration mint as a JSON array. Adding
a per-host label is a supervisor flag, not a code change.

**A recorded trap in that supervisor, which cost a previous session real time.**
Its README notes that the script's own CLI defaults silently win over a systemd
`Environment=` setting — a unit that sets `Environment=CI_RUNNER_SLOTS_PER_REPO=18`
never reaches the script, which keeps its built-in default. The bug went
unnoticed because the repository and label defaults happened to equal the unit's
values, while the slot count did not, so the pool stayed stuck at a single
runner. **Pass configuration as explicit `--repos` / `--slots` / `--labels`
flags in the unit's `ExecStart`, and verify the values in the supervisor's own
startup log line rather than in the unit file.**

## What already exists — do not rebuild it

The complete provisioning kit lives in `thewoolleyman/livespec-dev-tooling`
under [`ci-runner/`](https://github.com/thewoolleyman/livespec-dev-tooling/tree/master/ci-runner)
(32 files). It was authored and validated live against this VPS in July 2026.
Recreatability is its stated contract: re-running the provisioning script
converges a fresh host, and the exit-test suite proves the containment
invariants still hold.

| Path in `thewoolleyman/livespec-dev-tooling` | Role |
|---|---|
| `ci-runner/provision-ci-runner.sh` | Idempotently provisions a host: verifies the AppArmor unprivileged-user-namespace backbone without mutating it, installs the rootless container stack, creates the `ci-runner` service account in none of the `docker`, `sudo`, or `dolt` groups, installs the runner agent and container hooks, and creates the per-repository warm-cache lower directories. |
| `ci-runner/pregate-verify.sh` | Pre-gate verification: the subset of isolation tests that must pass before registration is attempted. |
| `ci-runner/isolation-exit-tests.sh` | The full eleven-test isolation suite, re-runnable against a live host using throwaway containers. Exits zero only if every non-skipped test passes. |
| `ci-runner/sanitize-hook.js` | Container-hook shim that strips the host container socket and host-namespace or privilege escalations from container create-options before delegating to the real hook. |
| `ci-runner/containers.conf` | The `ci-runner` account's rootless container defaults: private network namespace plus public DNS, so host loopback services stay unreachable from a job container. |
| `ci-runner/dockershim/docker` | A serialization shim ahead of the real container CLI. **Required for more than one concurrent slot** — without it a twelve-job matrix fails eight to ten of twelve in teardown, because every slot shares one rootless engine whose network prune scans a global container database. |
| `ci-runner/supervisor/` | The ephemeral just-in-time runner supervisor: systemd units, a narrow polkit bridge, and the mint and launch scripts. |
| `ci-runner/observability/` | Liveness heartbeat exporting a runner-count gauge to the fleet observability surface, plus an age-aware cache prune timer. |
| `ci-runner/gate-runner/` | A **separate, deliberately-privileged lane** for the golden-master gate. See the scope note below. |
| `ci-runner/warm-ci-cache.sh` | Host-side, trusted population of the warm caches. |

**Two lanes, not one.** The kit ships two independent runner lanes and this plan
concerns the first:

1. The **contained lane** (`ci-runner/supervisor/`) runs ordinary fleet CI as
   the unprivileged `ci-runner` account with no administrative escalation. This
   is what the pool is made of, and it is what §"Self-hosted CI runner host
   requirements" governs.
2. The **gate lane** (`ci-runner/gate-runner/`) runs the golden-master gate as
   the operator account with host privileges, because that gate's work cannot be
   carried by a stock hosted runner. The specification carves this out
   explicitly as a "deliberately-privileged, operator-triggered tier" whose
   containment boundary is the trigger filter deciding whether compute is
   granted at all, not the confinement of the runner.

**The gate lane is out of scope for this plan's first green job.** Provision the
contained lane, prove it, and only then consider whether the gate lane belongs
on this host too.

## The caching opportunity, which is why host capacity matters

The maintainer's instruction is to fully utilize the box's CPU and disk. The
kit's existing cache design is where that pays off, and it is already built.

`provision-ci-runner.sh` creates per-repository cache lower directories under
the runner account's home — `uv` for every repository, plus `cargo` and `target`
for Rust repositories. A job mounts these as the **lower** layer of an overlay
whose upper layer is per-job and discarded. That shape is trust-tiering by
construction rather than by a forgeable signal: a job can read the warm cache
but can never mutate it. The commentary in the script records that the `target`
cache is the large win, because without it the Rust matrix recompiles
dependencies ten redundant times and is a two-times regression against hosted
capacity rather than an improvement.

The existence of the cache root is the kill switch — remove it and the hook is a
byte-for-byte no-op of the uncached behavior. That makes cache enablement safe
to defer past the first green job and safe to disable if it misbehaves.

There is a hard external limit worth recording so it is not rediscovered:
`thewoolleyman/homelab`'s work-item `hl-4jl` establishes that GitHub's ten-gigabyte
Actions cache cap applies to self-hosted runners too. Local on-host caching is
not an optimization over the hosted cache; it is the only way past that cap.

## The inherited contract

From `thewoolleyman/livespec`,
`SPECIFICATION/non-functional-requirements.md` §"Self-hosted CI runner host
requirements". Every requirement is stated there as a host-observable property
rather than as a package name, deliberately, so a host may satisfy it by its own
native means. Restated here in the order a provisioning session meets them:

- **Platform.** x86_64 Linux with systemd and cgroups v2. The fleet's pinned
  toolchain and container images are x86_64.
- **Runner agent runtime.** The host must resolve the shared libraries the
  runner release itself declares. The authority is the release's own
  `bin/installdependencies.sh`, not any list copied into a document.
- **Workflow runtime.** `git`, `tar`, `gzip`, `curl`, and a JavaScript runtime
  must be resolvable by the runner identity, as must the pinned contributor
  toolchain at its pinned versions. A self-hosted host is **not** exempt from
  those pins, and a check must not be satisfied by a differently-versioned host
  tool.
- **Network.** Outbound HTTPS on port 443 to the forge's control plane, action
  download, artifact/cache/log receiver, agent self-update, and container
  registry endpoints. **No inbound reachability from the forge is required** —
  the agent dials out. This is why a box behind home NAT is a perfectly good
  runner host.
- **Execution identity.** A dedicated unprivileged service account with no
  administrative escalation, and **not** a member of any group conferring
  root-equivalent control of a container daemon. The specification names that
  membership as equivalent to host root and forbids granting it as a
  convenience, including as a way to make containerized jobs work.
- **Ephemeral registration.** Each registration serves at most one job and then
  deregisters, and a job must not be able to observe a previous job's workspace.
- **Credential separation.** The credential that mints registrations must be
  readable only by the supervising identity and never from a job. No fleet
  secret beyond a least-privilege read-scoped forge token may be injected into a
  self-hosted job's environment; a check needing more stays on hosted capacity.
- **Event routing.** Merge-gating self-hosted capacity is reachable only from
  same-repository pull-request events and pushes to a protected branch.
- **Containerized execution is optional.** Running jobs directly on the host
  under the execution identity conforms and is the simplest conforming shape. A
  host that does containerize must use a rootless engine.
- **Availability must not become a merge dependency.** See the next section.

**The fork-exclusion precondition.** The containment floor above is reduced
relative to a public-fork threat model, and that reduction is conditional. Self-
hosted capacity may carry a repository's merge gate only while no fork-originated
workflow can execute on it, and that exclusion must be enforced by the
repository's fork-pull-request approval setting at its **strictest tier** —
requiring approval for all outside collaborators, not merely first-time
contributors, because under weaker tiers a returning outside contributor's fork
pull request runs its own fork-controlled workflow definition with no approval
event. This must be verified per repository before that repository's routing is
flipped, and it is a live repository setting that no workflow can read from
within CI.

## The fail-closed routing property, which must not be broken

`thewoolleyman/livespec`'s `.github/workflows/ci.yml` resolves `runs-on` from the
repository variable `CI_RUNNER_LABELS`, defaulting to `["ubuntu-latest"]`
whenever that variable is absent or empty. **That default is a merge-gate safety
property, not a convenience.**

The reasoning, recorded in the workflow's own header: §"CI as a merge gate
(branch protection)" makes a single all-green gate the sole required check. A
matrix job routed to self-hosted capacity that is not there does not *fail* — it
sits queued, the aggregate gate never reports, and every merge in the repository
waits indefinitely on a check that will never arrive. Defaulting to the
self-hosted label made exactly that outcome the behavior of an absent variable.

Three consequences bind this plan:

1. **Flipping routing is a repository-variable edit in both directions**, and
   neither direction needs a specification revision. Setting `CI_RUNNER_LABELS`
   routes gating jobs to the pool; unsetting it or setting it to
   `["ubuntu-latest"]` returns them to hosted capacity. That reversibility is
   the emergency fallback.
2. **The routing flip comes last**, after a runner is proven to take a job.
   Flipping first produces the queue-forever failure the specification's
   availability clause exists to prevent.
3. The fallback literal `'["ubuntu-latest"]'` is repeated inline at each
   `runs-on` and in the lane-signal environment variable rather than
   single-sourced through a job output. **That repetition is deliberate and must
   be preserved**: the fleet's self-hosted routing guard parses `runs-on` values
   statically, so routing hidden behind a `needs.<job>.outputs.*` reference
   would read as "this workflow has no self-hosted job" and would silently
   disable the forbidden-trigger check. The three copies must stay in lockstep.

Related: `.ai/ci-gate-discipline.md` in `thewoolleyman/livespec` is load-bearing
for every slice that touches a merge-blocking gate. Its rule is **fix the gate,
never add a bypass** — no lever, no environment-variable escape, no demotion to
warning.

## The factory host must not carry this

§"Fleet CI execution posture" states that the shared factory host must not carry
a resident CI supervisor, listener pool, runner-liveness timer, or runner-cache
timer, and that this holds **unconditionally**, independently of the execution
posture. The reason given is that co-residency with the Fabro, Dolt, and
Dispatcher machinery — not self-hosted execution as such — is what made the
earlier resident pool untenable. The same clause then states the positive
obligation: *"Self-hosted CI capacity MUST therefore be separately provisioned
on a host dedicated to carrying it."*

`poweredge-xubuntu` is precisely that dedicated host, so **this plan is already
spec-blessed and needs no specification revision to proceed.**

A concrete consequence for provisioning: the factory host `vmi3006760` (tailnet
name `vps`) currently carries the gate-runner units disabled by a
`hosted-only.conf` systemd drop-in that gates them on a reboot-ephemeral path
existing. **Do not copy this host's live `/etc` state to `poweredge-xubuntu`.**
Provision from the kit in `thewoolleyman/livespec-dev-tooling`, which is the
source of truth; the drop-ins here are a posture applied to *this* host and must
not travel.

## Blocking input — SSH access to `poweredge-xubuntu`

Measured 2026-08-13 from the factory host:

- Tailscale reports the node online at `100.78.140.72`, and `tailscale ping`
  succeeds in roughly 30 milliseconds via a direct path.
- **TCP port 22 is closed or filtered**, as is 2222.
- Tailscale SSH is **not** enabled on the node — its peer record carries no SSH
  host keys.

So the box is reachable at the network layer and not reachable at the SSH layer.
The maintainer chose adding this host's public key to the target's authorized
keys over a reverse tunnel.

**Which account receives the key — state this explicitly.** The commands below
run **as that account**, not as root, because `~/.ssh/authorized_keys` is
per-account: appending the key to the wrong user's file leaves the box
correctly configured for a login nobody will attempt, and the resulting failure
looks like a network problem rather than a wrong-account problem. Two
requirements bind the choice:

- The account **must be able to escalate with `sudo`**, because
  `provision-ci-runner.sh` installs packages and creates a system account.
- **The connecting side defaults to `ubuntu`.** This host has no
  `~/.ssh/config` entry for `poweredge-xubuntu`, so an unqualified
  `ssh poweredge-xubuntu` connects as `ubuntu` — the factory host's own
  username. If the target account has any other name, either say so, so the
  connecting side uses `ssh <account>@poweredge-xubuntu`, or add a matching
  `Host poweredge-xubuntu` / `User <account>` stanza to this host's
  `~/.ssh/config`. **Do not assume `ubuntu` exists on the target.**

The one-time console action on `poweredge-xubuntu`, run as that account:

```bash
sudo systemctl enable --now ssh
mkdir -p ~/.ssh && chmod 700 ~/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIB4khw9ZVD9HI6xb4W+OIGCx6bxUSDEGp7+ANQQdG2MK ubuntu@vps.perch-rudd.ts.net' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
sudo ufw allow in on tailscale0 to any port 22 proto tcp 2>/dev/null || true
```

That key is the factory host's `~/.ssh/id_ed25519.pub`, reproduced verbatim and
verified byte-identical to the live file on 2026-08-13. Its **private half
carries no passphrase**, which is what makes the unattended claim below true
rather than aspirational — a passphrase-protected key would need an agent held
open across every later step.

Note the tailnet grant question is owned by `thewoolleyman/tailscale-admin`;
runner traffic is outbound-only and needs no widened grant, but SSH *to* the box
from the factory host does traverse the tailnet.

**Verify the step landed** before treating it as done — a successful append
proves nothing on its own, since the sshd and firewall legs can each fail
independently:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 <account>@poweredge-xubuntu 'hostname; id'
```

`BatchMode=yes` is what makes this a real test: it refuses any interactive
password fallback, so a success proves the *key* was accepted rather than
proving someone could have typed a password.

**Everything downstream of this step can be driven unattended over SSH.**

## What is not yet known

Deliberately unresolved until SSH lands, because guessing costs more than
measuring:

- The box's actual core count, memory, and free disk. The maintainer states it
  has substantially more capacity than the factory host, which has eighteen
  cores, ninety-four gigabytes of memory, and a six-hundred-and-seventy-eight-gigabyte
  volume at eighty-three percent used. Slot count and cache sizing are derived
  from the real numbers, not assumed.
- The distribution release, which decides whether the rootless stack package
  names in `provision-ci-runner.sh` (validated against Ubuntu 25.10) resolve
  unchanged. Xubuntu is Ubuntu with a different desktop, so the package set
  should resolve; the release version is what matters.
- Whether the AppArmor unprivileged-user-namespace backbone the provisioning
  script *verifies without mutating* is present. The script hard-fails if the
  two restriction sysctls are not set to one or if the shipped profiles are
  absent. On a desktop-flavored install this is the most likely first failure,
  and the correct response is to satisfy the property natively — **never to
  downgrade the sysctl**, which the script names as a hard invariant that is
  never traded away.

## Sequencing

Ordered so that the earliest possible step produces a runner taking a real job,
and so that nothing irreversible precedes proof.

1. **Access.** The maintainer's console step above. Verify by opening a
   non-interactive SSH session from the factory host and capturing the target's
   core count, memory, disk, and distribution release.
2. **Survey and pre-gate.** Run `pregate-verify.sh` against the target. Resolve
   whatever it reports — most likely the AppArmor backbone — by native means.
3. **Provision the contained lane.** Run `provision-ci-runner.sh`. It is
   idempotent, so a partial run is recoverable by re-running it.
4. **Prove containment.** Run the eleven-test isolation exit suite. It must exit
   zero before any registration is minted.
5. **Register one runner against one repository.** Stand up the supervisor with
   explicit `--repos`, `--slots`, and `--labels` flags carrying the per-host
   label. Prove that an ephemeral runner picks up a job and auto-deregisters,
   using a non-gating job targeting the per-host label so nothing that can block
   a merge is involved yet.
6. **Scale slots to the box.** Install the container serialization shim, which
   is required for more than one slot, then raise the slot count against the
   measured core count and verify a full matrix passes rather than failing in
   teardown.
7. **Enable the warm caches.** Populate the per-repository cache lower
   directories host-side and confirm a measured improvement against the hosted
   lane.
8. **Install observability.** The liveness heartbeat and the cache-prune timer,
   via the kit's own installer, which the kit names as the only sanctioned way
   to install or update the live copies. This discharges the specification's
   requirement that the fleet be able to *observe* that a host stopped taking
   jobs rather than infer it from a queue.
9. **Verify the fork-approval tier**, per repository, for every repository about
   to be routed.
10. **Flip routing, one repository first.** Set `CI_RUNNER_LABELS` to
    `["self-hosted","local-ci"]` on one repository, watch a real merge gate go
    green, and confirm the hosted fallback still works by unsetting it and
    watching the gate go green again.
11. **Roll out across the fleet.** Nine fleet repositories and four adopters are
    registered in `.livespec-fleet-manifest.jsonc`. Registration is per
    repository, because a personal account supports repository-level runner
    pools rather than organization-level ones, so each repository needs its own
    supervisor entry in `--repos`.
12. **Hand off to `thewoolleyman/homelab`.** See below.

## The handoff to `thewoolleyman/homelab`

The maintainer's instruction is that this plan hands off to `homelab` so it can
provision its own runners with everything learned here. `homelab` is an adopter
in `.livespec-fleet-manifest.jsonc` and already carries two blocked runner
plans, so the handoff is a join procedure rather than a new design.

The handoff must carry, at minimum:

- **The pool is join-only.** `homelab` adds hosts to the same label pool; it does
  not build a parallel one. Its hosts carry `self-hosted`, `local-ci`, and their
  own per-host label.
- **The kit is the shared implementation** and lives in
  `thewoolleyman/livespec-dev-tooling` under `ci-runner/`. `homelab` consumes it
  rather than forking it. A defect found while joining a host is fixed there,
  which benefits every member.
- **The contract is inherited and non-negotiable**, as
  `plan/11-3-add-ci-runners-to-gmktec/handoff.md` already records for the
  GMKtec: one-job ephemeral runners, no resident runner.
- **The measured findings from `poweredge-xubuntu`** — which package set
  resolved on which release, what the AppArmor backbone required, the slot count
  that a given core count sustained, the cache sizes that paid off, and every
  failure encountered with its resolution.
- **The recorded traps**, so they are not rediscovered: the supervisor's CLI
  defaults silently beating systemd `Environment=` settings; the serialization
  shim being mandatory above one slot; and the ten-gigabyte hosted-cache cap
  that makes a local store the only option.
- **The routing-flip discipline**: the flip comes last, and the fail-closed
  hosted default is a safety property to preserve rather than an inconvenience
  to route around.

Two existing `homelab` plans are the natural recipients:
`plan/11-3-add-ci-runners-to-gmktec/` for the GMKtec, and
`plan/05-hetzner-fleet-member/` together with `plan/07-build-substrate/` for
`hetzner-prod`. Both are currently blocked on host build work that this plan
does not touch and must not duplicate — the GMKtec thread's handoff states
plainly that no competing plan may be created from outside and that its host
must not be contacted from another thread.

## Scope boundary for this plan

**In scope:** the pool contract, `poweredge-xubuntu` provisioned and proven as
its first member, fleet repositories routed to it, observability installed, and
the join procedure handed to `thewoolleyman/homelab`.

**Out of scope, deliberately:** the privileged gate lane; building or contacting
`hetzner-prod` or `gmktec`; any change to the specification, which already
authorizes everything here; and any change to the factory host's posture, which
the specification pins unconditionally.
