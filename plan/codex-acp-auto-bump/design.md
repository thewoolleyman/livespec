# Design — codex-acp version auto-bump (factory-gated freshness)

**Status:** design draft for maintainer review (2026-07-13). No code
written; no repo mutated beyond this doc. Spin-off from
`fabro-ci-image-factoring` Phase 1 (epic `livespec-3lev.4`); **supersedes**
that plan's "orchestrator Codex version-less adapter" NEXT ACTION, whose
premise was disproven (see §"Why not version-less").

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
2. **Bump PR** (`livespec-dev-tooling`). Rewrites `CODEX_ACP_VERSION`; the
   existing `fabro-sandbox-image.yml` builds a **candidate image** on the PR
   (immutable `…-sha-<short>` layer tags — no release needed to test).
3. **Factory gate** (`livespec-orchestrator-beads-fabro`, triggered
   cross-repo). The dev-tooling PR **dispatches** (the existing
   `repository_dispatch` fan-out) an orchestrator job that runs a **Codex-mode
   golden-master** against the **candidate** sandbox image. The golden-master
   already provisions Codex credentials (`require_codex_auth_file` /
   `provision_codex_auth`); run with the Codex adapter it exercises the real
   `project_codex_auth_snapshot` credential projection end-to-end (green
   implement→review→pr→janitor, merged PR, greeting asserted). The job posts a
   **commit status** back to the dev-tooling PR's head sha.
4. **Merge gate** (`livespec-dev-tooling`). Branch protection requires that
   live-Codex status green. Merge → release → the new image bakes the new
   codex-acp → the orchestrator (`--no-install` baked global) picks it up with
   no pin to sync.

### No-Circular-Dependency compliance

Per `.ai/no-circular-dependency.md`, `livespec-dev-tooling` (the foundational
image builder) must never read INTO the orchestrator:

- The version lives in dev-tooling; the credential test is orchestrator-side.
- The gate is an **event dispatch + a commit-status callback** — NOT dev-tooling
  reading orchestrator code. This is the established fan-out pattern.
- The orchestrator's `--no-install` baked-global consumption is a
  **consumer→producer** read (it uses the producer's baked artifact),
  cycle-free.

### Golden-master Codex mode — the two additions it needs

The golden-master (`orchestrator-image/acceptance-live-golden-master.sh`) today
dispatches with the **default Claude** adapter and pulls the **released**
sandbox image from the orchestrator's `workflow.toml`. Two bounded additions:

- **Provider selection.** A `--provider codex` (or `--input acp_adapter=<codex>`)
  path so the dispatch runs the Codex implementer adapter. Codex credential
  provisioning already exists; this just routes the implementer nodes to it.
- **Candidate-image override.** A way to point the *sandbox* image at the
  candidate tag (`…:python-sha-<short>` from step 2) instead of the released
  pin in `workflow.toml` — e.g. an env/flag the Dispatcher's per-dispatch
  overlay honors. **Open mechanic** (see below): confirm the Dispatcher overlay
  can override `[environments.livespec-ci.image] docker`.

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

## Open decisions (for the maintainer)

1. **Single-SoT (image) vs keep-two-pins + equality check** — recommended
   single-SoT; confirm.
2. **Cadence + threshold** — how often the freshness scan runs, and whether it
   bumps on *any* new codex-acp release or only when N releases behind.
3. **Gate topology** — a NEW dedicated Codex-bump gate workflow, or extend the
   existing golden-master workflow with a provider/candidate-image switch.
4. **Candidate-image override mechanic** — confirm the Dispatcher overlay can
   point the sandbox image at the candidate tag for the test (the one
   unverified mechanic above).
5. **Cost** — each bump runs a real Codex factory dispatch (~5–10 min + LLM
   spend). Acceptable given codex-acp releases are infrequent; note it.

## Cross-references

- Parent epic: `livespec-3lev` (`fabro-ci-image-factoring`), Phase 1 `.4`.
- Credential-projection tracker: `bd-ib-ss7rkr`.
- No-Circular-Dependency Directive: `.ai/no-circular-dependency.md`.
- The disproven version-less proposal: `plan/fabro-ci-image-factoring/handoff.md`
  (NEXT ACTION, now pointing here).
