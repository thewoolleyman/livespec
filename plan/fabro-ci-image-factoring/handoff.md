# Plan — Minimal baked sandbox images + local hot CI runners + resource-health-gated fleet rollout

**Status:** draft for maintainer review; incorporates an independent
Fable-model adversarial review AND maintainer corrections (2026-07-11).
**Scope languages:** Python + Rust now. Haskell explicitly deferred.
**Owning session:** livespec core, 2026-07-11.

**Maintainer corrections folded in (2026-07-11):**
- **Disk is resolved, not a constraint.** ~41 GB of stale, unrelated
  Docker images were swept (91 GB free now, 74% used), and a disk-size
  DOUBLING is on order. Caches live on the LOCAL disk — there is NO
  separate/"Contabo cache volume" requirement (that was an unverified
  assumption; removed).
- **Load framing corrected.** The "2.4 vs 23" figures were MEASUREMENTS of
  the host's existing work at two moments — NOT a prediction of what this
  plan causes. On 18 cores, a load of 23 is mild, transient
  oversubscription, not overload.
- **Factory untouched (during authoring).** This plan was authored and
  updated entirely with local git; the Fabro factory was NOT used at the
  time (another session was upgrading it). **Update 2026-07-11: the factory
  is back up and usable (maintainer-confirmed) — the earlier do-not-use
  constraint is LIFTED (see Hard constraints).**

**Codex handling + collector rename folded in (2026-07-11, later):**
- **This plan is dual-runtime, not Claude-only.** The Fabro sandbox is
  runtime-agnostic (`acp.command={{ inputs.acp_adapter }}`); the
  Dispatcher routes each run to Claude OR Codex per provider. The baked
  image already carries BOTH ACP adapters + `bubblewrap` (a hard
  codex-acp requirement). Codex-specific obligations are now named
  explicitly below — image contents, adapter-version lockstep, and
  runtime-agnostic observability — rather than hidden behind the generic
  phrase "ACP adapters".
- **The collector was renamed `claude-collector` → `otel-collector`**
  (maintainer-approved 2026-07-11; VPS side LANDED 2026-07-11). It is
  functionally the host's shared OTel collector (Claude Agent-Timeline
  shaping is just one processor). The live systemd service is now
  `otel-collector.service` against
  `/data/projects/otel-collector/config.yaml`, stamping the
  `collector.otel-collector` marker. The macOS-side migration is still
  pending on the Mac (tracked in the collector repo's `AGENTS.md` +
  `plan/rename-to-otel-collector-macos-migration.md`). See
  `plan/collector-otel-rename/handoff.md`.

**Maintainer corrections (2026-07-12) — two framings below are WRONG; these supersede them:**
- **The "multi-day baseline" is DEAD — do not wait for days of data.** The
  resource health check is a **safety net**, not a precision instrument: its
  job is to PAUSE-and-bump only on *genuine* saturation, and those thresholds
  come from the **hardware**, not from a multi-day percentile window.
  Empirically confirmed by a load test (2026-07-12): 8 concurrent CI-style
  test-suite runs **on top of** a live factory dispatch held RAM-free at
  **65+ GiB throughout** (of 94 GiB), zero swap activity, zero OOM kills;
  CPU oversubscribed to run-queue 45 on 18 cores and handled it **gracefully**
  (jobs queue, nothing crashes). So: **memory (RAM) is a near-unreachable hard
  floor** (the swap=0 "OOM" fear is moot — RAM never approaches pressure), and
  the only signal that flexes is **sustained CPU-idle≈0% *duration*** (the
  "consider reducing concurrency" hint, which degrades softly). Set conservative
  hardware-derived thresholds NOW (RAM-available floor ≈ 8 GiB hard-stop;
  sustained-CPU-saturation duration as a soft hint; disk free floor as
  hygiene). **P-host is MET** (metrics flowing + headroom empirically shown);
  it **no longer gates Phases 0–1.** Everywhere below that says "capture a
  multi-day baseline / freeze percentiles / baseline-derived" is superseded by
  this.
- **The cross-repo pin lockstep as written is a CIRCULAR DEPENDENCY — do NOT
  build it.** Phase 1 below says to extend `livespec-dev-tooling`'s
  `fabro_image_pin_lockstep.py` to READ the orchestrator's Codex pin (and the
  console's `rust-toolchain.toml`). That is `dev-tooling → orchestrator/console
  → dev-tooling`: `livespec-dev-tooling` is the foundational enforcement-suite
  repo those consumers depend ON, so it must never reach INTO them. Fixes:
  (a) **Codex — design the drift away, no check:** make the orchestrator's Codex
  adapter command **version-less** (`npx -y @zed-industries/codex-acp`, dropping
  `@0.16.0`) so it resolves the baked global exactly as the Claude adapter
  already does — then the image's `CODEX_ACP_VERSION` is the single source of
  truth, nothing can drift, and there is no cross-repo read. (b) **Rust (and any
  belt-and-suspenders pin check):** the check lives on the **downstream/consumer
  side** (e.g. the console asserting its `rust-toolchain.toml` matches the baked
  image ARG — a legit consumer→producer read), **never** in `dev-tooling`. Both
  orchestrator/console edits wait behind the active `dispatcher.py` refactor
  (item `bd-ib-s7e`).

---

## Session handoff — where to start

**State (fresh-session entry point, 2026-07-13). CURRENT FOCUS: the
Observability completion track (section below) — front-loaded, maintainer-directed,
driven by this session, running parallel to the image work.** The plan is anchored by
the **beads epic `livespec-3lev`** (`livespec` tenant) with per-phase children
`.1`–`.8` (`.8` = Phase 5, the closing efficiency report, added 2026-07-12).
Done so far:
- **P-host (`.1`) — MET.** Host + per-container metrics (`hostmetrics` +
  `docker_stats`) flow to the **`livespec-host-metrics`** dataset (`agent-activity`
  Honeycomb env) via `otel-collector` PR #3 (commit `417e5d8`, marker `0.6`),
  verified live. The "multi-day baseline" was over-engineered and is **dead** (a
  load test confirmed the headroom); P-host **no longer gates Phases 0–1**.
  Follow-ons (non-blocking): wire the Honeycomb resource trigger at conservative
  hardware thresholds (needs an alert-destination decision), runner-liveness
  alert (waits for Phase 0), cache budget/prune.
- **Designs drafted** (read these companion docs before implementing a phase):
  `phase0-runner-containment-design.md`, `phase1-layered-image-design.md`,
  `phase2-ci-disposition-livespec.md`.
- **`bd-ib-s7e` (the blocking `dispatcher.py` refactor) is now CLOSED**
  (L2-f ratified, PR #504, release 0.17.21, master CI green; verified
  2026-07-12) — so P-factory (`.2`), the Codex version-less fix, and the
  Phase 1 consumer-switch are **no longer blocked by that item**. CAVEAT:
  `livespec-orchestrator-beads-fabro` still has other active worktrees
  (`retire-fabro-image-pin-lockstep`,
  `fix-embedded-ledger-credential-precheck`, `plan-codex-factory-telemetry`),
  so re-check for a LIVE dispatch before editing that repo or
  `livespec-console-beads-fabro`.
- **Phase 5 (`.8`) added 2026-07-12** — the closing post-rollout efficiency
  report (factory + CI, CPU + wall-clock). It hard-depends on P-factory
  (`.2`), which makes repairing the factory trace egress a precondition for
  the final report rather than an indefinitely-deferred follow-on. P-factory
  is itself now unblocked (its verification was waiting on `bd-ib-s7e`).
- **P-factory (`.2`) code LANDED + Defect A accepted LIVE (2026-07-13).** PR
  #539 (`livespec-orchestrator-beads-fabro`) fixed both defects; a real
  golden-master dispatch proved the dispatcher's own timing now flows
  (`livespec-dispatcher` 0→5 spans). The sandbox-agent side (`fabro-sandbox`)
  stayed dark because the factory runs Codex, which emits nothing — that is the
  Observability completion track below, NOT a P-factory failure.

## Observability completion track (front-loaded; maintainer-directed 2026-07-13)

**Decision (2026-07-13):** finish ALL factory observability, driven by the
maintainer's Claude session (not handed to the maintainer to run), front-loaded
and running in PARALLEL with the image work (they no longer touch the same
files). The closing efficiency report (Phase 5 / `.8`) DEPENDS on items 3 + 4a
below being done — we never claim to have measured a factory we cannot see.

Plain-English: "observability" = being able to open Honeycomb and see, per
factory run, which steps ran, how long each took, and what it cost. Four pieces:

1. **Machine + container resource usage** (CPU/mem/disk per container) — **DONE**
   (P-host; powers the resource-health safety gate).
2. **The orchestrator's own step timing** (dispatcher stages: post-merge check
   pass, total run wall-clock) — **DONE + PROVEN LIVE** (P-factory Defect A;
   `livespec-dispatcher` dataset).
3. **Setup/check timing INSIDE each sandbox run** ("install tools → sync deps →
   run the check suite") — **DONE + ACCEPTED LIVE (2026-07-13).** The
   prepare-step timing shims shipped as a stdlib-only `livespec-step-timer`
   wrapper baked into the fabro-sandbox image (WI-A `livespec-dev-tooling-bot`,
   `livespec-dev-tooling` PR #352, in image `v0.42.0`) + the 8
   `implement-work-item/workflow.toml` prepare-step shims (WI-B `bd-ib-l7c`,
   `livespec-orchestrator-beads-fabro` PR #554). A real golden-master dispatch
   emitted all 8 `prepare.*` spans to the `fabro-sandbox` dataset (was empty)
   with real durations — `uv-sync` 4219 ms (dominant), `mise-install` 214 ms
   (near-noop, confirming the baked toolchain), `sandbox-exempt` 4 ms. Both
   WI-A/WI-B and the P-factory anchor `livespec-3lev.2` are CLOSED. The
   in-sandbox setup timing is now MEASURED, not inferred.
4. **The AI agent's own activity + cost** — the real hole. The factory drives
   with Codex, which emits NO telemetry. Two layers:
   - **4a. Basic agent activity + rough token counts** — **TODO, medium.** Emit
     from the Fabro harness (not from Codex), via the fabro-side OTLP exporter
     that today exists only as unfinished/uncommitted work on a stale Fabro
     version (must be re-derived vs current Fabro), plus teaching the host
     receiver (`_otel_receive.py`) Fabro's protobuf wire format. This is the
     Codex-telemetry track's "Approach 2." Its receiver-side prerequisite (the
     `172.17.0.1` bind) is ALREADY landed by P-factory.
   - **4b. True per-run dollar cost** (`total_usd_micros`) — **UPSTREAM-BLOCKED,
     NO FORK (maintainer-declared 2026-07-13).** Requires a change to Codex
     itself + per-sandbox config + disabling Codex's default Statsig metrics
     egress to OpenAI. The maintainer explicitly does NOT want to carry a Codex
     fork. File/keep as an OPEN, BLOCKED tracking issue against upstream Codex
     spend-tracking support; the coarse token counts from 4a cover the near-term
     need. Do not build 4b until upstream lands.

**Build order — progress + remaining:**
1. ~~Groom items 3 and 4a into ready work-items.~~ Item 3 groomed + BUILT +
   ACCEPTED LIVE (2026-07-13; WI-A `livespec-dev-tooling-bot`, WI-B `bd-ib-l7c`,
   both closed). **DONE.** Item 4a still needs grooming under the Codex-telemetry
   epic `bd-ib-98c` (orchestrator ledger), reconciled with the existing
   fabro-OTLP-exporter item `bd-ib-i4r`.
2. ~~Build item 3 first.~~ **DONE** — see item 3 above; 8 `prepare.*` spans
   verified live in `fabro-sandbox`.
3. **NEXT — Build item 4a** (the real hole; medium): re-derive the fabro-side
   OTLP exporter against current Fabro + teach the receiver (`_otel_receive.py`)
   Fabro's protobuf wire format so Codex-driven runs emit agent node/turn spans
   + coarse token counts; accept by confirming agent-activity spans land on a
   real Codex dispatch. Its receiver prerequisite (`172.17.0.1` bind) is already
   landed. Groom `bd-ib-98c`'s Approach-2 spine (steps 1–4) first.
4. Ensure the 4b upstream-blocked tracking issue (`livespec-impl-beads-zbl`) is
   filed and cross-linked; do NOT fork.
5. The **setup-path** half of Phase 5 is now measurable (item 3 done); the full
   Phase 5 factory report still waits on item 4a (agent-activity spans) to
   measure the Codex-driven half end-to-end.

Full plain-English rationale is in the maintainer conversation of 2026-07-13; the
Codex-side technical detail is in
`livespec-orchestrator-beads-fabro/plan/codex-factory-telemetry/research/codex-otel-support.md`.

**Hard constraints:**
- **No-Circular-Dependency Directive** (`.ai/no-circular-dependency.md`,
  maintainer-declared 2026-07-12): a foundational/upstream repo
  (`livespec-dev-tooling`, `livespec` core) must NEVER read INTO a downstream
  consumer. Cross-repo checks live on the consumer side, or the coupling is
  designed away. This is why the Codex/Rust "cross-repo lockstep" was scrapped.
- The Fabro factory is up and usable; the next session MAY dispatch this track's
  implementation through it.
- All repo changes go through worktree → PR → merge (docs use `docs(...)`; the
  Red-Green-Replay ritual applies only to product `.py`).

**Phase 0 design gate — PASSED (2026-07-12); implementation BANKED / PAUSED
pending maintainer authorization.** The `phase0-runner-containment-design.md`
dual adversarial-review gate (maintainer-declared 2026-07-12) ran to completion:
FOUR rounds, each a fresh Fable-model agent + a fresh Codex agent, independent +
READ-ONLY, hunting serious blockers. Trajectory: r1 both SBF → r2 both SBF →
r3 Fable-clean/Codex-1 → **r4 BOTH NO-SERIOUS-BLOCKERS = GATE PASSED**. Every
round's findings + resolutions are on `livespec-3lev.3` (comments), and the
design landed as `docs(plan)` PRs **#1084** (r1) → **#1085** (r2) → **#1086**
(r3) → **#1087** (r4 gate-pass + non-blocking polish), all merged. **NO host was
mutated across the entire gate.** The design now carries a "GATE PASSED at round
4" status + all four §"Round N dual-review record" sections, and names the
concrete containment surfaced by the reviews: the host SHIPS the enabling
AppArmor userns profiles (`bwrap-userns-restrict`/`podman` — no bespoke profile
needed; sysctls stay `=1`); a provisioned rootless stack; `ci-runner` in none of
docker/sudo/dolt; a JIT runner with **agent/job UID+PID-ns separation via
`ACTIONS_RUNNER_CONTAINER_HOOKS`**; a supervisor polkit/systemd bridge;
all-host-loopback network isolation; and 11 isolation exit-tests.

**The maintainer chose to BANK the design here (2026-07-12) — NOT to authorize
implementation.** Phase 0 implementation is a HOST MUTATION on this shared,
multi-tenant host, so it needs an explicit maintainer go; do **not** self-start
it. Next-session options (surface as a decision to the maintainer):
1. **Phase 1 (baked images) next** — its `base`/`python`/`python-rust`
   image-split + Rust-bake + console-`rustup`-removal core is UNBLOCKED and needs
   NO host mutation (carries the concrete per-run wins). Consumer-switch + the
   Codex version-less fix wait on `bd-ib-s7e`.
2. **Authorize Phase 0 implementation** — run the pre-gate (verify shipped
   AppArmor → provision rootless stack) → `ci-runner` + supervisor + JIT runner
   with agent/job separation → trusted-event routing + network isolation → one
   repo's `just check` green as the non-gating shadow lane; each step gated by its
   exit tests. Reversible.
3. **Reconsider the local-runner track's cost/benefit** — the gate revealed the
   containment is non-trivial while Phase 0's payoff is mostly cost/hotness
   (Phase 1 carries the concrete wins).

**Already-settled facts (do not relitigate):** keep the CI matrix (tune
runner slots ≈18, do NOT collapse); full-history clones (no mirror, no
shallow); disk resolved (the doubling that was "on order" appears to have
LANDED — the live collector now measures ~157 GB free on the largest
filesystem vs the earlier ~91 GB; caches on the local disk — worth a
confirming glance); the runner must be socket-less + secret-isolated +
fork-PR-routed (public repos).

## Bottom line

The livespec factory and CI still pay a **live-work tax on every run**:
`livespec-console-beads-fabro` installs `rustup` per Fabro run; every
repo's `uv sync` is only partially warmed (the baked image pre-warms the
uv cache from `livespec-dev-tooling`'s OWN lockfile, not each consumer's);
and CI on GitHub-hosted runners re-runs `mise` setup + restores/saves
`actions/cache` every job. We replace that with **minimal, layered,
pinned images** (compilers baked, caches on persistent LOCAL-disk volumes)
and move CI onto **local self-hosted runners co-located on this host**, so
images and caches are hot, local, and free — and CI runs the SAME image
the Fabro sandbox uses, collapsing "green in CI, red in sandbox" drift.
Because everything converges on one host, the plan adds **host-resource
observability that does not exist yet** and a **resource health check**;
if CPU/memory genuinely saturate during rollout it **pauses so the
maintainer can bump resources**. It then fans out to **all 8 fleet
members** and seeds **work-items in every adopter repo**.

The Fabro factory itself already runs locally (Dispatcher on host, docker
sandbox local) — GitHub-hosted CI is the one component that leaves the
box, so baked images help Fabro immediately and the CI move closes the
loop.

## Confirmed design decisions

1. **Per-repo images, not per-step.** Fabro runs the entire work-item
   graph in ONE sandbox container per run (verified in
   `fabro-sandbox/src/docker.rs`: single container, `cpu_quota`/
   `memory_limit`; console `workflow.toml` sets `cpu = 4`). The unit of
   minimization is the per-repo (per-language) image, composed from
   shared layers.
2. **Layered composition.** `base → python → python-rust`.
   `livespec-console-beads-fabro` uses `python-rust` (it needs Python
   too — its janitor reuses the Python baseline verifiers +
   commit-refuse installer). No "Rust-only" image now.
3. **Local runners are IN this epic.** A hot, free, persistent cache is
   only reachable by co-locating; on GitHub-hosted runners "persistent
   cache" means `actions/cache` (10 GB/repo cap, LRU eviction, network
   restore+save each run) or a paid external cache.
4. **Containment is mandatory and multi-layered** (see Threat model).
5. **Resource observability is a hard prerequisite** — built FIRST; the
   rollout is watched by a continuous health check, not a point-in-time
   glance.

## Host baseline (measured 2026-07-11)

| Resource | Value | Read |
|---|---|---|
| vCPU | 18 | Generous; Fabro budget is 4 CPU/run |
| RAM | 94 GiB (84 GiB available) | Not a binding constraint |
| Swap | 0 B | Any memory breach is a hard OOM — no cushion |
| Load avg (15m) | bursty: same-day samples ranged 0.8–23 | These are MEASUREMENTS of existing work, not predictions. On 18 cores, load 23 ≈ 5 processes briefly waiting — mild, transient, not overload. |
| Disk | 91 GB free (74% used) after sweeping ~41 GB of stale non-Fabro Docker images; a disk-size **doubling is on order** | **Resolved — no longer a constraint** |
| OTel collector | `otelcol-contrib` already running | Host metrics = a config add |

**Recalibration:** CPU, RAM, and disk all have comfortable headroom (disk
resolved by the Docker sweep + the ordered upgrade). Load is bursty but
the box is strong; resource thresholds still come from real measurement in
Phase P, framed as a **health check** — not a tripwire we expect to hit.

## Architecture — layered images

```
base          buildpack-deps:noble + system libs + mise/just/lefthook/gh/node + BOTH ACP adapters (Claude claude-agent-acp + Codex codex-acp) + bubblewrap (HARD codex-acp requirement)
  └─ python   + CPython + uv  (base tools only; deps come from persistent volumes, not baked pre-warm)
       └─ python-rust  + rustc/cargo (rust-toolchain pin)
       └─ (later) python-haskell   + GHC/cabal   [OUT OF SCOPE]
```

- **Dual-runtime (Claude + Codex) is baked, and MUST stay baked.** The
  sandbox runs whichever ACP adapter the Dispatcher selects per provider
  (`acp.command={{ inputs.acp_adapter }}`; default Claude, Codex via
  `fabro run --input acp_adapter=…`). So the `base` layer bakes BOTH
  `@agentclientprotocol/claude-agent-acp` AND `@zed-industries/codex-acp`
  globally, plus `bubblewrap` (the codex-acp adapter needs it for
  `require_escalated` exec AND `apply_patch`). A "minimal image" pass MUST
  NOT drop the Codex adapter or bubblewrap — that silently breaks
  Codex-driven runs. And the Codex command pins a version
  (`…codex-acp@0.16.0`), so the baked `CODEX_ACP_VERSION` must match it or
  `npx -y …@0.16.0` re-fetches at runtime — see the adapter-version
  lockstep in Phase 1.
- Built by the EXISTING image CI track
  (`livespec-dev-tooling/.github/workflows/fabro-sandbox-image.yml`,
  `runs-on: ubuntu-latest`), generalized to a matrix emitting the layered
  tags. Immutable `sha-<short>` / `v<X.Y.Z>` tags; BuildKit layer cache
  already `type=gha`.
- **Image BUILDS stay on GitHub-hosted (or a dedicated trusted-only
  builder); they do NOT move to the CI runner** — building images needs a
  privileged builder, and the local runner is deliberately unprivileged
  (see Threat model). The image build keeps `type=gha` for its own layer
  cache. (This corrects an earlier draft that scheduled a local BuildKit
  cache in Phase 1 — a GitHub-hosted builder cannot reach a host-local
  cache.)
- Consumers pull immutable tags; on a single host the **Docker daemon
  image store already keeps every pulled tag hot** for both Fabro and the
  runner — so no local registry is needed for hotness. A registry/mirror
  is added ONLY if GHCR-outage resilience is wanted, and then as an
  explicit skopeo/crane sync with a stated disk budget (not
  `registry-mirrors`, which only mirrors Docker Hub).

## Threat model & runner isolation (expanded per review)

The isolation problem is bigger than "untrusted dependency build
scripts" — it includes **untrusted actors**, because the repos are
**PUBLIC** (`livespec`, `livespec-dev-tooling`,
`livespec-console-beads-fabro` confirmed public).

1. **Fork-PR execution (highest risk).** GitHub explicitly warns against
   self-hosted runners on public repos: a fork PR can run
   attacker-controlled workflow code on the host. **Mitigation (Phase 0
   prerequisite):** route only TRUSTED events (push to `master`,
   same-repo PRs) to self-hosted; keep fork PRs on GitHub-hosted; require
   approval for all outside collaborators; verify a fork PR cannot
   trigger a self-hosted-labeled job. (Taking repos private is the
   alternative, but is a product decision, not assumed here.)
2. **No Docker socket.** The runner IS the baked toolchain image running
   steps directly — NO nested containers, NO `/var/run/docker.sock` mount
   (socket access is root-equivalent and would let any job read the host
   secrets and `/var/lib/doltdb`). Jobs that need to build images
   therefore cannot run on it — they stay on the privileged/trusted
   builder.
3. **Ephemeral execution + secret-free cache volumes** — fresh runner per
   job; caches are mounted local-disk dirs carrying no secrets (see
   Caching trust tiers).
4. **Host-resident secret inventory (Kind 2)** the runner user must NOT
   reach: the systemd-creds 1Password token, the Dolt tenant password,
   the GitHub App private key, `/var/lib/doltdb`, **and the new runner
   registration credential** (below).
5. **Runner registration credential (new Kind-2 secret).** The owner is a
   personal account, so these are repo-level, ephemeral runners; a
   supervisor re-registers after each job using short-lived registration
   tokens minted by a PAT/App with **repo-administration scope**. That
   credential is powerful and lives on the host — it goes in the isolation
   inventory and the supervisor design is a Phase 0 deliverable.
6. **`just check` is NOT fully hermetic (correction).** Some targets need
   GitHub auth — e.g. `check-master-ci-green`,
   `check-branch-protection-alignment` — and the factory `workflow.toml`
   documents `GH_TOKEN` reaching `just check` subprocesses. Phase 0 audits
   which targets need a token and grants the MINIMAL one (Actions
   `GITHUB_TOKEN` where it suffices); the drift check "CI == sandbox
   `just check`" must compare like-with-like given this.

## Caching strategy (comprehensive — local co-located)

Local runners + local disk let us cache aggressively and eliminate live
downloads (the main flakiness source). Every cache is a **persistent
local-disk directory** surviving across ephemeral jobs — NOT
`actions/cache`.

| Layer | Kills | Mechanism | Phase |
|---|---|---|---|
| Python deps | wheel download + build | persistent `~/.cache/uv` dir (primary — replaces reliance on baked pre-warm) | 0 |
| Rust deps | crate index + source fetch | persistent `~/.cargo/registry` dir | 0 |
| Git | shallow-clone history limits + re-fetch | **full-history clone every run** — drop the current shallow (depth=10) + `git fetch --unshallow` dance; ~10 MB packed for `livespec`, so it is cheap AND hands agents complete history. NO bare mirror (a `--reference` clone creates a fragile alternates dependency for near-zero gain) | 0 |
| Rust compilation | recompiling across runs/repos | `sccache` local backend + persistent `target/` — **trusted-tier only** | 2 |
| Tool caches | re-analysis | persistent pyright/mypy/ruff/pytest/coverage dirs | 2 |
| Package fetch (residual) | anything the volumes miss | **per-ecosystem mirrors** (devpi / a crates mirror / npm proxy) IF measured worthwhile — a transparent MITM proxy is REJECTED (HTTPS/TLS). Likely deferred; the uv/cargo caches already remove most fetches | (defer) |

**Trust-tiered caches (non-negotiable — a job writes its cache as a side
effect, so "populate only from trusted sources" is otherwise
unenforceable):**
- **PR / untrusted-lane jobs get READ-ONLY (or throwaway overlay) cache
  mounts.** Write-back happens ONLY from trusted-branch (post-merge)
  runs.
- **Per-repo namespaces** for `target/` and sccache — a poisoned object
  from one repo cannot flow into another's build or release artifact.
- **`sccache` is trusted-tier-only, or skipped initially** — its object
  cache has no input-integrity binding (unlike lockfile-keyed uv/cargo
  registry caches).

**Cache-integrity guardrails:** content-addressed keys (lockfile/toolchain
hashes) on read; **a scheduled cold-cache validation run** (no-cache `just
check`, cadence a Phase-P decision) to catch cache-masked "false green";
per-cache size cap + LRU eviction, watched by the resource health check.

**Image pre-warm demotion (staleness fix).** The current Dockerfile
pre-warms uv from `livespec-dev-tooling`'s lockfile only, and
`fabro-sandbox-image.yml`'s `paths:` triggers watch only dev-tooling
files — so consumer-lockfile changes never rebuild the image and warm
layers silently rot. Therefore: **persistent local-disk caches are the
primary dep cache; image layers carry base tools only** (no per-repo dep
pre-warm unless the lockfile plumbing + rebuild triggers are built
explicitly).

**Disk (resolved).** Caches live on the **local disk** — no separate
volume needed. Breathing room was already made by sweeping ~41 GB of
stale, unrelated Docker images (91 GB free now), and a disk-size doubling
is on order. The only guardrail needed is a **per-cache size cap + prune
automation** (docker image GC, cache LRU) as a named `livespec-dev-tooling`
tool, watched by the resource health check. Cargo `target/` dirs are the
largest single consumer (the fleet's one Rust repo, the console, is ~2.7
GB — modest; the 45 GB `fabro/target` is the Fabro TOOL's own build, not
something we cache).

## Resource health check (spec — continuous, hardware-threshold-derived)

A phase-end point-in-time glance is the wrong shape on a bursty host
(same-day load ranged 0.8–23 purely from existing work). Instead:

- **Thresholds from the hardware, not a multi-day baseline (2026-07-12
  correction).** A safety net does not need normal-P95; it needs conservative
  absolute limits near the hardware ceiling. Set them from the box's specs +
  a quick load test (done), not a days-long window: RAM-available floor
  (≈ 8 GiB hard stop; swap=0 so there is no soft zone below it), sustained
  CPU-saturation *duration*, disk free floor. These sit far above real
  working load, so they will not false-fire.
- **Continuous sustained-duration trigger** (Honeycomb trigger + burn
  window), not a one-shot report — a phase "passes" only if no sustained
  breach occurred across its active window.
- **Signals** (provisional; finalize in Phase P): CPU utilization + PSI
  pressure (NOT bare load-avg — load > vCPU is normal for I/O-heavy
  builds), memory available + any swap-in, **CI queue-wait time** (on a
  single host, queue latency saturates before CPU does), and a lighter
  disk watch (disk is already resolved, so it is a hygiene check, not the
  binding signal).
- **Runner-liveness/absence alert** — the check watches resource EXCESS;
  nothing yet watches runner ABSENCE (a down runner queues jobs silently
  up to 24h). Add liveness alerting in Phase P.
- **PAUSE action:** on a sustained CPU/memory saturation breach, emit a
  report + per-container attribution (Fabro vs runner vs Dolt; prefer the
  `docker_stats` receiver over process-name matching) and **pause so the
  maintainer can bump host resources**. This is the maintainer-requested
  stop-to-provision gate; disk is already handled, so the realistic
  trigger is CPU/memory, not disk.

---

## Phases

### Phase P — Observability prerequisite (blocks everything)

Split so the host-resource half needs **NO factory** and can start
**immediately**. The running `otelcol-contrib`
(`/data/projects/otel-collector/config.yaml`) ALREADY exports to
Honeycomb (`otlp/honeycomb` exporter + a `metrics` pipeline); it just has
no host/container-metrics receiver yet. So the host half is a
two-receiver config add + a collector reload — nothing touches the Fabro
factory.

**P-host — factory-INDEPENDENT (START HERE, now):**
- Add a `hostmetrics` receiver (cpu, memory, disk, load, paging) + a
  `docker_stats` receiver (per-container attribution) and route them to a
  named metrics dataset via an explicit `x-honeycomb-dataset` header (NOT
  the bare `otlp/honeycomb` metrics export, which auto-routes — see the
  First-action routing caveat: the collector exports to the
  `agent-activity` env today; decide env + dataset). Scope scrapers +
  interval to control per-PID cardinality/cost.
- Capture a multi-day baseline; freeze thresholds; implement the
  continuous health-check trigger + runner-liveness alert.
- Set the local-disk cache budget + prune automation + the cold-cache
  validation schedule. (Disk breathing room already made by the Docker
  sweep; a disk doubling is on order — no separate cache volume needed.)
- **Where:** `otel-collector` (config); resource tooling in
  `livespec-dev-tooling`. **No factory, no orchestrator repo.**

**P-factory — factory-COUPLED (deferred).** All changes here are in OUR
code — NOT the Fabro codebase (`/data/projects/fabro` is the third-party
runner we never modify):
- Verify/repair the OTel TRACE egress — OUR Dispatcher's OTel emission
  (`livespec-orchestrator-beads-fabro`'s `_otel_*` + `dispatcher.py`) plus
  the `otel-collector` config; factory datasets `livespec-dispatcher`,
  `fabro-sandbox`, `livespec-rgr` have been silent since ~2026-06-13.
- Prepare-step timing span shims — wrap the prepare-step `script =` lines
  in OUR `.fabro/workflows/implement-work-item/workflow.toml`.
- **Deferral reasons (2026-07-11 update).** Originally deferred because (1)
  validating either needs a real factory RUN (a dispatch), which we were
  told not to use, and (2) the orchestrator repo was being actively edited
  by the factory-upgrade session. Both have eased: the factory is back up
  and usable, so a validating dispatch is now possible; confirm the
  orchestrator upgrade has landed before editing that repo. P-host remains
  the cleaner starting point — it touches only `otel-collector` +
  `livespec-dev-tooling`.

**Runtime-agnostic by construction (Claude + Codex).** Everything Phase P
measures sits BELOW the ACP adapter, so it is identical for Claude- and
Codex-driven runs: `hostmetrics`/`docker_stats` observe the sandbox
container the same way whichever adapter runs inside (`docker_stats` gives
per-container attribution), and the Dispatcher/prepare-step timing spans
are emitted by OUR code regardless of provider. The one thing that DOES
differ — agent-INTERNAL telemetry — is out of scope here: Claude Code
emits rich OTel (shaped by the collector) while Codex
(`@zed-industries/codex-acp@0.16.0`) emits NONE. That gap is owned by the
separate `livespec-orchestrator-beads-fabro/plan/codex-factory-telemetry/`
thread; this plan does NOT address it, and the resource health gating does
NOT depend on it (it runs on host/container metrics + Dispatcher spans, so
it gates Codex runs fine even while Codex is internally dark).

**Exit (P-host — the actual blocker):** host metrics flowing to the
chosen named dataset + env (per the First-action routing caveat); baseline
+ thresholds frozen; health check +
liveness alert live; cache budget + prune set. P-factory can complete
later WITHOUT blocking Phases 0–1.

### Phase 0 — Local-runner shadow lane (non-gating)

> **Full design + the mandatory dual adversarial-review gate:**
> `phase0-runner-containment-design.md`. Implementation MUST NOT begin until a
> Fable agent AND a Codex agent each find no *serious* security blockers.

**Deliverables**
- One ephemeral, unprivileged, secret-isolated runner (NO docker socket)
  running the baked image directly + a runner **supervisor** with the
  registration-credential design.
- **Trusted-event routing** so fork PRs cannot reach the runner.
- Persistent secret-free cache dirs (uv, cargo registry). Git:
  **full-history clones every run** (drop the current depth=10 shallow +
  `--unshallow`; ~10 MB packed — cheap, and hands agents complete
  history). No bare mirror.
- **CI runner-slot count (KEEP the matrix — do NOT collapse it):** the
  fleet's CI is a per-target MATRIX (~40 `just <target>` jobs) that gives
  per-check failure isolation + individual PR status checks + granular
  required-checks for FREE; collapsing into one job would force us to
  reinvent all of that (a real regression). Provision enough runner slots
  (≈18, ≈ core count) to run the matrix in parallel — the full matrix is
  only ~591 CPU-seconds/run (see Additional research), so 18 cores match
  GitHub's current wall-clock, and correct caching makes per-job setup
  near-free. Record the slot count the resource projections use.
- One repo's `just check` green on the runner as a NON-gating lane; verify
  the runner user cannot read the Kind-2 secret paths.

**Where:** `livespec-dev-tooling` (runner/supervisor/containment tooling);
pilot repo shadow lane.

**Exit:** green shadow run; isolation verified; concurrency number set;
**continuous resource signal shows no sustained breach**.

### Phase 1 — Baked layered images

**Deliverables**
- `base / python / python-rust` layered Dockerfiles + matrix build in
  `fabro-sandbox-image.yml` (builds STAY GitHub-hosted/trusted-builder).
- Pin/lockstep — **CORRECTED per the 2026-07-12 note; the original
  "cross-repo lockstep in `dev-tooling`" bullets were a circular dependency.**
  `livespec-dev-tooling` is upstream of the consumers, so its checks must NOT
  read the consumers' pins. Instead:
  - **Codex — design the drift away, no check.** Make the orchestrator's Codex
    adapter command **version-less** (`npx -y @zed-industries/codex-acp`,
    dropping the `@0.16.0` in `CODEX_IMPLEMENTER_ADAPTER`) so it resolves the
    baked global exactly as the Claude adapter command already does. Then the
    image's `CODEX_ACP_VERSION` is the single source of truth, nothing drifts,
    and no cross-repo read exists. (Edit is in the orchestrator; waits behind
    the `dispatcher.py` refactor, item `bd-ib-s7e`.)
  - **Rust — downstream-side check only.** If a guard is wanted that the baked
    rust matches `livespec-console-beads-fabro/rust-toolchain.toml` (channel
    1.92.0 + clippy/rustfmt), it lives in the **console** repo reading the
    image ARG (consumer→producer, cycle-free) — never in `dev-tooling`.
  - `CLAUDE_AGENT_ACP_VERSION`: its `workflow.toml` command already carries no
    version (resolves the baked global), so it is already drift-free by the
    same principle — nothing to add.
  - Still decide the `workflow.toml` image-tag autodiscovery gap (image pins
    are manual today — the console `workflow.toml` PIN SURFACE NOTE confirms
    this); that is a pin-bump-automation question, independent of the (now
    removed) cross-repo lockstep.
- Console `workflow.toml` → baked `python-rust` image; DELETE the per-run
  `rustup` step. Orchestrator `workflow.toml` → `python` image.

**Where:** `livespec-dev-tooling` (bulk); console + orchestrator (a
little).

**Exit:** images published + pinned + lockstep-green; console +
orchestrator dispatch green on baked images; no sustained resource breach.

### Phase 2 — Cut CI over to the local runner + baked image

**Deliverables**
- **Per-job disposition table for the pilot repo** — each `ci.yml` job
  labeled move / stay-GitHub-hosted / delete. Jobs that stay hosted:
  App-token minting (fleet-conformance), telemetry export, the
  release/auto-merge chain, and any GitHub-context-bound job. This table
  is the fan-out template ("switch `runs-on` + delete `actions/cache`" is
  NOT a per-file operation).
- Moved jobs run `just check` targets in the baked image on the runner;
  their `actions/cache` steps deleted (cache now local).
- **Merge-gate fallback mechanism designed** (not just named): a
  `workflow_dispatch`-switchable `runs-on` variable OR a gate meta-job
  that accepts either lane, so a down host does not silently stall merges
  for 24h. (Runner-liveness alerting from Phase P covers detection.)

**Exit:** pilot CI green on local runner in-image; drift check (CI ==
sandbox `just check`, like-with-like) passes; no sustained breach.

### Phase 3 — Fleet fan-out

**Members (8):** `livespec`, `livespec-dev-tooling`,
`livespec-driver-claude`, `livespec-driver-codex`,
`livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`,
`livespec-runtime`, `livespec-console-beads-fabro`.

**Deliverables:** per repo — apply the Phase 1 image pin + the Phase 2
disposition table; verify green.

**Exit per repo:** green on local runner in-image, AND the continuous
resource signal holds as load accumulates (a sustained CPU/memory breach
here pauses for a resource bump). A mid-fan-out pause leaves the fleet
temporarily split across two CI models — an acceptable interim steady
state.

### Phase 4 — Adopter work-items

**Deliverables:** a ready work-item filed in each adopter ledger —
`openbrain`, `resume` — for the same conversion, executed by them
(adopters are independent: own credential wrappers, tenants, GitHub Apps),
citing this epic's reference implementation.

### Phase 5 — Post-rollout efficiency report (closing measurement gate)

The epic's headline claim — baked images + local hot runners shave the
per-run and per-work-item tax — is a **projection** until measured on the
rolled-out fleet. Phase 5 is the closing gate that turns it into a
**measured** before/after report of how much the factory AND CI actually
improved, in **CPU-seconds and wall-clock time**.

**Depends on:** Phase 3 (the fleet's factory + CI are actually running the
baked-image + local-runner model) **AND P-factory (`.2`) as a HARD
prerequisite** (maintainer-decided 2026-07-12). The factory OTel trace
datasets (`livespec-dispatcher`, `fabro-sandbox`, `livespec-rgr`) have been
silent since ~2026-06-13, so without the P-factory egress repair the
factory half of this report is unmeasurable; the CI half (`github-ci`) is
independent of P-factory. **Independent of Phase 4** — adopter work-items
do not affect this fleet's own factory/CI efficiency.

**Measurement window — count-based, not clock-based.** Accumulate a real
post-rollout load window ("a day or two, or however long it takes") until
there are enough samples to be meaningful — a floor of some N factory
dispatches and M CI runs across the repo-classes, NOT a fixed calendar
duration. The factory has been quiet, so the window may need deliberate
load (real dispatches), not passive waiting.

**Deliverables**
- A comprehensive before/after report at
  `plan/fabro-ci-image-factoring/phase5-efficiency-report.md`, reported
  **PER repo-class** (Rust console vs Python repos), never one fleet-wide
  number (a 16-min P50 Fabro run is agent/LLM-dominated — see the
  Measurement section).
- **Factory** (from `livespec-dispatcher` / `fabro-sandbox` /
  `livespec-rgr`, now that P-factory restored egress + added prepare-step
  janitor spans): per-work-item critical-path `just check` time (in-sandbox
  janitor + fix loop — now MEASURED, not inferred — plus Dispatcher
  post-merge), `fabro-run` wall-clock, per-run CPU-seconds. Validate against
  the projection: ~3–5 min saved per work-item on the critical path,
  ~30–50% off each cold `just check`.
- **CI** (from `github-ci`): per-run wall-clock, per-run CPU-seconds (SUM
  of job durations), per-job setup tax (`mise install` → no-op, `uv sync` →
  cache-hit, full-history clone), and CI queue-wait — compared against the
  frozen before-baseline (30d snapshot: ~591 CPU-s/run, ~70 s wall-clock,
  ~40 jobs/run, avg 13 s/job).
- **Host trade-off** (from `livespec-host-metrics`): the HONEST cost side.
  Co-locating CI + factory on one host RAISES host CPU utilization; report
  that delta so the outcome reads as "wall-clock + $-cost per run DOWN vs
  host CPU utilization UP," never a one-sided win. Confirm the 2026-07-12
  load-test headroom held under real accumulated load (no sustained
  resource-health breach).
- **Both providers:** confirm the per-run-tax delta holds for BOTH Claude-
  and Codex-driven runs at a live dual-provider dispatch (the Phase 1 Codex
  version-less adapter fix is what keeps the per-run `npx` adapter fetch
  eliminated for Codex).

**Before baseline (already captured — reuse, do not re-derive):** the
"Additional research (2026-07-11)" numbers below ARE the frozen "before"
(30d `github-ci`: ~591 CPU-s/run, ~70 s wall-clock; `livespec-dispatcher`
janitor 93 s P50 / 175 s P95). Phase 5 re-runs the SAME Honeycomb queries
over the post-rollout window and diffs.

**Where:** measurement + report authoring in this plan thread (`livespec`
core); queries read Honeycomb (`github-ci`, `livespec-dispatcher`,
`fabro-sandbox`, `livespec-rgr`, `livespec-host-metrics`). No repo code
change beyond the report artifact.

**Exit:** the report is merged into the plan thread and summarized on the
epic; the headline efficiency claim is now MEASURED (with honest
CPU-vs-wall-clock framing), not projected — the epic's closing gate. The
epic can close once it lands.

---

## Where the work lives (summary)

| Repo | Share | What |
|---|---|---|
| `livespec-dev-tooling` | **bulk** | layered images + matrix build (both ACP adapters — Claude + Codex — baked), pin-lockstep extensions incl. the cross-repo Codex adapter-version lockstep, runner/supervisor/containment tooling, resource health-check + liveness tooling, cache prune automation, fan-out automation |
| `otel-collector` (renamed from `claude-collector`; VPS side landed 2026-07-11, Mac migration pending) | prerequisite | `hostmetrics` + `docker_stats` receivers + Honeycomb metrics pipeline |
| `livespec-orchestrator-beads-fabro` | a little | prepare-step span shims; own `workflow.toml` → `python`; shipped default |
| `livespec-console-beads-fabro` | a little | `workflow.toml` → `python-rust`; drop per-run `rustup` |
| each fleet repo | mechanical | image pin + per-job `ci.yml` disposition + `actions/cache` removal |
| `openbrain`, `resume` (adopters) | Phase 4 | work-items only |
| this plan thread (`livespec` core) + Honeycomb | Phase 5 | post-rollout efficiency report: before/after CPU-seconds + wall-clock for the factory (`livespec-dispatcher`/`fabro-sandbox`/`livespec-rgr` — needs P-factory) + CI (`github-ci`) + the host trade-off (`livespec-host-metrics`) |

## Measurement (before/after) — per repo class

Report savings PER CLASS, not one fleet-wide number (a 16-min P50 Fabro
run is dominated by agent/LLM time):
- **`livespec-console-beads-fabro` (Rust):** removes per-run `rustup`
  install + cold cargo builds — the real win.
- **Python repos:** the residual is the per-repo `uv sync` delta (already
  partially image-warmed) — likely well under 10%.
- **Both providers pay the same tax below the ACP layer.** The wins
  (baked toolchain, hot caches, no per-run `rustup`, warm `uv`) apply
  equally to Claude- and Codex-driven runs; the Codex adapter-version
  lockstep (Phase 1) is specifically what keeps the per-run `npx` adapter
  fetch eliminated for Codex. At the first live dual-provider dispatch,
  confirm the per-run-tax delta holds for both.
- Phase P's prepare-step spans set the headline number; do not justify the
  epic fleet-wide on the console's figures.
- **Phase 5 is where this becomes measured, not projected** — the closing
  gate re-runs these before/after comparisons over a real post-rollout
  window and produces the comprehensive report (see Phase 5).

## Additional research (2026-07-11) — parallelism + janitor critical path

### Parallelism — keep the matrix; caching (not collapsing) removes the overhead

Measured over 30d (`github-ci`), per CI run on `livespec`:
- **~40 jobs/run** (24,108 job-spans ÷ 598 runs).
- **~591 CPU-seconds of work/run** (SUM of job durations ÷ runs), avg
  **13 s/job**, P95 21 s.
- GitHub packs that into **~70 s wall-clock — ~8× parallelism, not 40×**;
  the jobs are short and mostly not CPU-saturating.
- On this host's **18 cores: 591 ÷ 18 ≈ 33 s floor, ~40–70 s realistic** —
  matches/beats GitHub.

**Conclusion (corrects an earlier draft that floated matrix-collapse):
KEEP the per-target matrix.** Collapsing 40 checks into one job would
force us to reinvent the per-check failure isolation, individual PR
status checks, granular required-checks, and per-check logs the matrix
gives for FREE — a real regression. The only motivation to collapse was
avoiding 40× per-job setup, and correct caching removes that anyway:
baked image → `mise install` is a no-op (tools pre-baked); hot
`~/.cache/uv` volume → `uv sync` is a cache-hit; a full-history clone is
~10 MB packed (a couple seconds; no mirror needed). Per-job setup drops from ~20–40 s to a
few seconds (an `actions/checkout` + a fresh `.venv` link + runner
workspace setup remain — small, not literally zero). So the Phase 0
concurrency knob is **"how many runner slots" (≈18, core count), NOT
"collapse vs matrix."**

### Janitor `just check` is on the critical path ~5–6× per work-item

Measured (`livespec-dispatcher`, mid-June shakedown, ~44 dispatches — the
factory has been quiet since, so this is a real but dated snapshot):
- `dispatcher.stage.janitor-post-merge` (one `just check`): **93 s P50,
  175 s P95**, cold.
- `dispatcher.stage.fabro-run`: **17 min P50** (LLM-agent-dominated).

Per work-item, `just check` runs on the critical path: in-sandbox janitor
+ fix loop (**1–4×**, inferred from the graph's 3-fix-visit cap) +
Dispatcher post-merge (**1×**, measured) + CI on branch and master
(**2×**) ≈ **~8–10 min of `just check` per work-item, almost all cold**.
Baked images + hot caches shave ~30–50% off EACH →
**~3–5 min saved per work-item on the critical path** (non-overlapping
time, so it directly shortens the loop and speeds agent iteration — the
leverage the per-PR CI figure understates). Caveat: the in-sandbox
janitor count is INFERRED from the workflow graph, not measured — Fabro's
internal nodes don't emit to Honeycomb, which is exactly why Phase P adds
janitor-node spans to make it measured.

## Rollback (per phase)

Each phase is cheaply reversible and reversal is written into its
work-item: image-pin revert (via lockstep/pins), `ci.yml` `runs-on` →
`ubuntu-latest` + restore `actions/cache`, runner deregistration, cache
dir teardown. A Phase-3 partial state (some repos local, some hosted) is a
valid pause point.

## Risks & open decisions

- **Public repos + self-hosted runners** — highest risk; trusted-event
  routing is a Phase 0 prerequisite (above).
- **Docker-socket vs. image builds** — runner stays socket-less; image
  builds stay on a privileged/trusted builder.
- **Cache poisoning** — trust-tiered caches; sccache trusted-only/deferred.
- **Single-host merge-gate** — fallback mechanism designed in Phase 2 +
  liveness alert in Phase P.
- **No swap cushion** — treat any sustained swap-in as an immediate
  PAUSE-for-provision; consider a swap safety net.
- **Bursty load** (0.8–23 same day, all from existing work) — RESOLVED as a
  non-issue: a 2026-07-12 load test (8 concurrent CI suites + a live factory
  dispatch) held RAM > 65 GiB free and merely oversubscribed CPU gracefully.
  Set conservative hardware thresholds (not a multi-day baseline); load is not
  a level the plan is expected to reach.
- **Disk (resolved)** — local-disk caches; ~41 GB swept from stale Docker
  images (91 GB free); disk doubling on order; keep a per-cache cap +
  prune.
- **CI matrix concurrency** — KEEP the matrix (free per-check failure
  isolation + reporting); tune the runner-slot count, NOT collapse (see
  Additional research).
- **Autodiscovery gap** — close now (auto-bump `workflow.toml` image tags)
  vs. keep manual per-repo pins guarded by lockstep.
- **Cache-warming strategy** — persistent local-disk cache (primary) vs.
  per-repo image pre-warm (demoted; needs lockfile plumbing + triggers if
  revived).
- **Codex adapter-version drift** — `CODEX_ACP_VERSION` (baked image) vs.
  the orchestrator's explicit `codex-acp@0.16.0` command pin: on drift,
  `npx` re-fetches the adapter every Codex run (the per-run tax returns).
  Close it by making the orchestrator's Codex command **version-less** (drop
  `@0.16.0` → resolves the baked global, like Claude already does) — NOT via a
  cross-repo lockstep in `dev-tooling`, which would be a circular dependency
  (2026-07-12 correction).
- **Collector renamed to `otel-collector` (was `claude-collector`).** The
  `hostmetrics`/`docker_stats` additions land in the host's shared OTel
  collector; the VPS-side rename landed 2026-07-11 (service
  `otel-collector.service`, `/data/projects/otel-collector/`), Mac
  migration pending. Tracked in `plan/collector-otel-rename/`.

## Dependency diagram

```mermaid
flowchart TD
    P["Phase P<br/>Observability + thresholds"] --> Z["Phase 0<br/>Local-runner shadow lane"]
    P --> I["Phase 1<br/>Baked layered images"]
    Z --> C["Phase 2<br/>Cut CI over (in-image, local)"]
    I --> C
    C --> F["Phase 3<br/>Fleet fan-out (8 members)"]
    F --> A["Phase 4<br/>Adopter work-items"]
    F --> M["Phase 5<br/>Post-rollout efficiency report"]
    P -. "P-factory trace-egress: hard prereq for Phase 5" .-> M
    P -. "continuous resource health check across all phases" .- F
```
