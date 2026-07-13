# Design — codex-acp version auto-bump (factory-gated freshness)

## Build outcome (2026-07-13)

**SHIPPED — all code merged; two maintainer-gated finalization steps remain.**
The full pipeline is built and merged across both owning repos:

- `livespec-orchestrator-beads-fabro` (released **0.30.0**): PR-A **#572**
  (version-less adapter `npx --no-install @zed-industries/codex-acp`), PR-C gate
  **#574** (`repository_dispatch` trigger + `--codex-acp-version` overlay +
  commit-status callback), PR-C-followup **#579** (green gate → enable the
  dev-tooling bump PR's auto-merge).
- `livespec-dev-tooling`: PR-B **#371** — propose `964cd49` + ratify contracts
  **v025** `2f1962c` + code `81b7da3` (autodiscovery walker + `codex_acp_pin_rewrite`
  + composite-action arm + `no_auto_merge` bump-PR mode + freshness scan over
  npm + cross-repo dispatch). `just check` 54 green; Red-Green-Replay trailers
  present. (Ratified as v025, rebuilt from v024 after a concurrent v024 —
  neutral-shared-hook-body — landed on dev-tooling master first.)

Two design mechanics were **corrected during build** (both disproven or refined
against the shipped world; the prose below reflects the corrected forms):

1. **Merge gate is FAIL-CLOSED, not a branch-protection required check.** An
   independent Fable review plus the build confirmed a required status check is
   unimplementable here: GitHub scopes required status checks to the *base
   branch*, so requiring the cross-repo `codex-acp-golden-master` status would
   deadlock every unrelated dev-tooling PR, and it would fail dev-tooling's own
   §"branch_protection_alignment check" (a required check with no matching
   `ci.yml` job). The ratified mechanism: the bump PR is opened **without
   auto-merge**, and only a **green** gate run enables its auto-merge (via the
   App's contents + pull-requests write); a red/errored gate leaves the PR open
   for a human. The cross-repo commit status is **informational**, never a
   required check.
2. **Topology is the OPTION-3 runtime overlay, and the golden-master was
   already Codex-mode.** No candidate *image* is built or overridden; the gate
   overlays the version at runtime with an `npm install -g
   @zed-industries/codex-acp@<ver>` prepare-step. The golden-master already
   dispatches through the Codex implementer adapter (the Dispatcher loop always
   routes implementer nodes to Codex), so PR-C added **no provider switch** —
   only the candidate-version overlay + the `repository_dispatch` handler + the
   status callback.

Remaining (maintainer-gated): (a) add `Commit statuses: write` to the
`livespec-pr-bot` App and approve on the dev-tooling install — the gate callback
403s until then, fail-closed so bump PRs simply stay open; (b) the credentialed
force-accept exercising the gate end-to-end; (c) close epic `livespec-3lev.4`.
See `handoff.md` for the exact resume procedure.

---

**Status (original design, retained for the record):** design **APPROVED — all
architecture decisions resolved by the maintainer 2026-07-13** (see
§"Decisions"). Spin-off from `fabro-ci-image-factoring` Phase 1 (epic
`livespec-3lev.4`); **supersedes** that plan's "orchestrator Codex
version-less adapter" NEXT ACTION, whose premise was disproven (see §"Why not
version-less").

**Owning repos of the eventual work:** `livespec-dev-tooling` (the image
ARG + the freshness scan + the bump PR) and `livespec-orchestrator-beads-fabro`
(the Codex-mode golden-master gate + the adapter command). `livespec` core
carries only this planning artifact.

## Goal

Keep an explicit **codex-acp version pin** (the safety anchor the credential
projection depends on) but make it **self-updating**: a scheduled robot
notices when `zed-industries/codex-acp` ships a newer release, opens a PR
bumping the pin, and — **before that PR can merge** — spins the real factory
with the **Codex agent** on the new version and verifies it still works. Merge
only if that live test is green. The pin auto-tracks upstream, but never
advances to an **unverified** version.

## Why not version-less (the finding that motivates this)

The parent plan proposed making the orchestrator's Codex adapter command
version-less (`npx -y @zed-industries/codex-acp`, dropping `@0.16.0`) to
"resolve the baked global and eliminate the per-run refetch." Rigorous
in-image testing (2026-07-13, against `python-rust-v0.43.1`) disproved the
premise:

- The image **bakes `codex-acp@0.16.0` globally** (`npm install -g` in the
  base Dockerfile). With network, BOTH `npx -y @…/codex-acp@0.16.0` (pinned)
  and `npx -y @…/codex-acp` (version-less) run the **baked** binary in ~1–2 s
  with **zero package downloads** (proven: the codex-acp binary itself ran and
  rejected `--version`; no `added N packages` from npm). So there is **no
  per-run refetch** to eliminate when the pin matches the baked version — which
  it does.
- Version-less is therefore a **no-op** for the (non-existent) download tax,
  and it is strictly **less safe**: the `@0.16.0` pin is load-bearing — it
  documents that the Codex credential-projection sentinel
  (`project_codex_auth_snapshot`) was empirically verified against exactly
  codex-acp 0.16.0 (tracked by `bd-ib-ss7rkr`). On a **drift** (someone bumps
  the baked `CODEX_ACP_VERSION` without re-verifying), the pinned form keeps
  using the verified 0.16.0 (re-fetching it if the baked copy differs — safe),
  whereas version-less would **silently run the new, unverified version** — the
  exact credential-projection break the pin guards against.

Conclusion: **keep the pin**; make it self-updating via a bump that is
**factory-gated**. The gate — a real Codex-provider golden-master run — IS the
credential-projection re-verification the pin's comment demands, so a *tested*
bump is safe where a *silent* one is not.

## Current state (two hand-synced pins)

The codex-acp version is duplicated across two repos, kept in sync by hand:

| Where | Value | Note |
|---|---|---|
| `livespec-dev-tooling` `docker/fabro-sandbox/base/Dockerfile` | `ARG CODEX_ACP_VERSION=0.16.0` → `npm install -g @zed-industries/codex-acp@${CODEX_ACP_VERSION}` | the ACTUAL install; the Dockerfile comment says it "mirrors the orchestrator's hardcoded pin" |
| `livespec-orchestrator-beads-fabro` `_dispatcher_fabro_argv.py` | `CODEX_IMPLEMENTER_ADAPTER = "npx -y @zed-industries/codex-acp@0.16.0"` | the adapter command Fabro launches for the implementer nodes |

codex-acp `@0.16.0` pins codex-core `rust-v0.137.0`; the sentinel behavior was
verified against it (`bd-ib-ss7rkr`).

## Architecture (recommended)

### Single source of truth: the image ARG

- **`CODEX_ACP_VERSION` (dev-tooling base Dockerfile) becomes THE pin.**
- The orchestrator adapter command drops its explicit version and consumes the
  baked global **fetch-free**: `npx --no-install @zed-industries/codex-acp`.
  `--no-install` uses the baked global with no registry round-trip (verified:
  it ran the baked binary even with `--network none`; `npx -y` without
  `--no-install` does a per-launch metadata round-trip that offline hangs), so
  it is both fetch-free and network-independent — aligned with this epic's
  hot-local-cache goal.
- One pin, one place, one bump. Safe **because** every image bump is now
  factory-gated.

**Credential-projection obligation relocates from a static comment to the
automated gate.** Today a code comment says "bumping requires re-verifying the
sentinel behavior." With this design the re-verification is **executed** by the
Codex-mode golden-master on every bump PR; the comment becomes a pointer to
that gate (and to `bd-ib-ss7rkr`), not a manual TODO.

### The auto-bump pipeline

1. **Detect** (scheduled, `livespec-dev-tooling`). Extend the existing
   `reusable-pin-freshness.yml` machinery — it already runs on a cron, queries
   each discovered pin source's latest release, and opens a bump PR per stale
   pin — to also watch `zed-industries/codex-acp`. This needs a new
   autodiscovery **pin format** for the `CODEX_ACP_VERSION` Dockerfile ARG with
   an **external** source (`zed-industries/codex-acp`, queried via
   `gh release view` / `npm view`, not a fleet release).
2. **Bump PR** (`livespec-dev-tooling`). Rewrites `CODEX_ACP_VERSION` and
   **dispatches** the cross-repo gate. The PR is opened in a `no_auto_merge`
   bump-PR mode — auto-merge is deliberately NOT enabled at open time, so the PR
   cannot merge until the gate turns it on (fail-closed; see step 4). **No
   candidate image is built** — the gate overlays the new version at runtime
   (OPTION 3, see step 3), so there is no per-PR image build to wait on.
3. **Factory gate** (`livespec-orchestrator-beads-fabro`, triggered
   cross-repo). The dev-tooling PR **dispatches** (the existing
   `repository_dispatch` fan-out) an orchestrator job that runs the **Codex-mode
   golden-master** with a **runtime version overlay** — an `npm install -g
   @zed-industries/codex-acp@<ver>` prepare-step installs the candidate version
   into the released sandbox image at run start (OPTION 3; no candidate *image*
   tag is built or overridden). The golden-master already dispatches through the
   Codex implementer adapter and already provisions Codex credentials
   (`require_codex_auth_file` / `provision_codex_auth`), so it exercises the real
   `project_codex_auth_snapshot` credential projection end-to-end (green
   implement→review→pr→janitor, merged PR, greeting asserted). The job posts a
   **commit status** (`codex-acp-golden-master`, success|failure) back to the
   dev-tooling PR's head sha via the `livespec-pr-bot` App token.
4. **Merge gate** (FAIL-CLOSED, cross-repo). The commit status is
   **informational only — NOT a branch-protection required check** (a required
   check is unimplementable here: GitHub scopes required checks to the base
   branch, so it would deadlock every unrelated PR, and it violates dev-tooling's
   §"branch_protection_alignment check"). Instead, the gate itself **enables the
   bump PR's auto-merge** only on a **green** run — using the App's
   contents + pull-requests write (PR-C-followup #579). A **red or errored** gate
   leaves the PR open for a human; nothing merges an unverified version. On green
   the PR auto-merges → release → the new image bakes the new codex-acp → the
   orchestrator (`--no-install` baked global) picks it up with no pin to sync.

### No-Circular-Dependency compliance

Per `.ai/no-circular-dependency.md`, `livespec-dev-tooling` (the foundational
image builder) must never read INTO the orchestrator:

- The version lives in dev-tooling; the credential test is orchestrator-side.
- The gate is an **event dispatch + a commit-status callback** — NOT dev-tooling
  reading orchestrator code. This is the established fan-out pattern.
- The orchestrator's `--no-install` baked-global consumption is a
  **consumer→producer** read (it uses the producer's baked artifact),
  cycle-free.

### Golden-master Codex mode — what PR-C actually added

**Correction (build finding).** The golden-master
(`orchestrator-image/acceptance-live-golden-master.sh`) was **already
Codex-mode**: it dispatches via the Dispatcher loop (`dispatcher.py`), which
always routes implementer nodes to the Codex implementer adapter. There is **no
"default Claude" adapter to switch off**, so PR-C added **no provider switch**.
It also pulls the **released** sandbox image from the orchestrator's
`workflow.toml`, and — per the OPTION-3 topology — that image is **not
overridden**; the candidate version is layered onto it at runtime. PR-C's real
additions were:

- **Candidate-version runtime overlay.** A `--codex-acp-version <ver>` flag whose
  value is installed at run start via an `npm install -g
  @zed-industries/codex-acp@<ver>` prepare-step **inside the released image**
  (OPTION 3). This replaces the abandoned "candidate-image override" idea — no
  `…:python-sha-<short>` image tag is built or pointed at; the released image is
  reused and the version is overlaid. No Dispatcher `[environments.…image]
  docker` override is needed.
- **`repository_dispatch` handler + status callback.** The gate is wired as a
  `repository_dispatch` handler (event_type `codex-acp-golden-master`) that reads
  the `codex_acp_version` from the payload, runs the golden-master with the
  overlay, and posts the `codex-acp-golden-master` commit status back to the
  dev-tooling PR's head sha via the `livespec-pr-bot` App token. On a green run a
  follow-up step (#579) enables the bump PR's auto-merge (the fail-closed merge
  gate — see §"The auto-bump pipeline" step 4).

## Alternatives considered

- **Keep both pins + a consumer-side equality check** (orchestrator asserts its
  `@X.Y.Z` == the baked ARG; consumer→producer, cycle-free). Preserves an
  explicit orchestrator pin but leaves two things to bump in lockstep.
  Rejected for the single-SoT simplicity — but viable if an explicit
  orchestrator-visible pin is wanted.
- **Version-less without a gate.** Unsafe (disproven premise + the
  credential-projection drift risk). Rejected.
- **`--prefer-offline` instead of `--no-install`.** `--no-install` is stricter
  (never touches the network; errors loudly if the baked copy is absent rather
  than silently fetching). Preferred.

## Rollback

Each bump is a normal PR revert of the image ARG; consumers pick up the
reverted image on the next release. The gate prevents a bad version from
merging in the first place, so rollback is a rare fallback, not the primary
safety.

## Decisions (resolved by the maintainer, 2026-07-13)

1. **Pin home → IMAGE ONLY.** The image's `CODEX_ACP_VERSION` is the single
   source of truth; the orchestrator drops its explicit version and consumes the
   baked global fetch-free (`npx --no-install @zed-industries/codex-acp`). No
   orchestrator pin to sync, no equality check needed.
2. **Cadence → WEEKLY, bump on ANY new release.** The scheduled scan runs
   weekly and opens a factory-gated bump PR on *any* new `zed-industries/codex-acp`
   release (not batched/N-behind). Cost is bounded — codex-acp releases are
   infrequent, and each bump is one ~5–10 min gated Codex dispatch.
3. **Gate topology → EXTEND the existing golden-master.** Reuse the proven
   harness (`acceptance-live-golden-master.sh`) rather than a new dedicated
   workflow; least new surface. **(Refined during build:** the golden-master was
   already Codex-mode, so NO provider switch was added; and the "candidate-image
   override" was replaced by the OPTION-3 runtime version overlay — a
   `--codex-acp-version` flag + `npm install -g …@<ver>` prepare-step on the
   released image, no candidate image built. See §"Golden-master Codex mode".)
4. **Build priority → NEXT.** Building this is the next-session priority (the
   last Phase 1 / `livespec-3lev.4` deliverable — closes Phase 1).

### Resolved during build (was: "still to verify")

- **Candidate-image override mechanic — RESOLVED by dropping it.** The build
  chose the OPTION-3 runtime overlay instead of overriding
  `[environments.livespec-ci.image] docker`: the released image is reused and the
  candidate version is layered on via an `npm install -g …@<ver>` prepare-step
  (the `--codex-acp-version` flag). No Dispatcher image override was needed, so
  the one unverified mechanic became moot. See §"Golden-master Codex mode".

## Cross-references

- Parent epic: `livespec-3lev` (`fabro-ci-image-factoring`), Phase 1 `.4`.
- Credential-projection tracker: `bd-ib-ss7rkr`.
- No-Circular-Dependency Directive: `.ai/no-circular-dependency.md`.
- The disproven version-less proposal: `plan/fabro-ci-image-factoring/handoff.md`
  (NEXT ACTION, now pointing here).
