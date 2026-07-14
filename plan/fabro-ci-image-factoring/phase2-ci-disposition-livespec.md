# Phase 2 — per-job CI disposition table (pilot repo: `livespec`)

**Status:** design artifact / fan-out template, drafted 2026-07-11 (read-only
analysis of `livespec`'s committed workflows; no CI or host was mutated).
Companion to `handoff.md`; tracked as epic child `livespec-3lev.5` (Phase 2).

## What this is

Phase 2 of the `fabro-ci-image-factoring` plan cuts CI over from
GitHub-hosted runners to the local self-hosted runner running the baked
image. The handoff calls the per-job disposition table "the fan-out
template" — the classification other fleet repos (Phase 3) reuse, each
verifying its own actual state (the fleet is non-uniform). This file is that
table for the pilot repo `livespec`, derived purely from what each job
*needs* (GitHub context, App tokens, secrets, network, full history), which
is knowable now and stable regardless of when the runner is built.

## Notation

Each row is one CI **job** (or, where noted, one **step** inside a job).
The **Disposition** column takes exactly one of three values:

| Disposition | Meaning |
|---|---|
| **MOVE** | Runs on the local self-hosted runner in the baked image. Its `runs-on:` changes from `ubuntu-latest` to the self-hosted label; its `actions/cache` step is deleted (the cache is a persistent local-disk dir); `mise install` becomes a near-no-op (tools baked); `uv sync` hits the hot local `~/.cache/uv`. |
| **STAY-HOSTED** | Keeps `runs-on: ubuntu-latest`. It needs something the unprivileged, secret-isolated local runner deliberately cannot or should not have: a repo/App admin token, an ingest/API secret, a privileged builder, or it is a zero-work GitHub-expression gate that must aggregate both lanes. |
| **DELETE-STEP** | A *step* (not a whole job) removed on the MOVE, because the local runner makes it redundant (e.g. an `actions/cache` restore, or CI's clone-siblings-to-temp hack that the on-host sibling clones replace). |

"GitHub-context-bound" below means the job depends on values only GitHub
provides for the triggering event (a minted App token, `github.run_id`, a
`repository_dispatch` payload, a `schedule` trigger) — NOT merely the
`github.*` env vars (`event_name`, `base_ref`, `repository`), which GitHub
injects into any runner, self-hosted included.

## `ci.yml` — the PR / push feedback loop (the primary target)

| Job (or step) | Disposition | Why |
|---|---|---|
| `setup` (detect-py-changes) | **MOVE** | Only uses env-injected `github.event_name` / `github.base_ref` + a `git fetch` + `git diff`. All available on the local runner. It gates every matrix job (`needs: setup`), so keeping it hot/local shortens the critical path. Minor judgment call — see Judgment calls below. |
| `check-python` matrix (~31 `just <target>`) | **MOVE** | Hermetic code checks (`check-lint`, `check-types`, `check-coverage`, …) run as `just <target>`. Nothing GitHub-context-bound. This is the bulk of the win. |
| ↳ `Restore uv download cache` (`actions/cache@v4`) | **DELETE-STEP** | Replaced by the persistent local-disk `~/.cache/uv` dir (Phase 0). |
| ↳ `Install pinned binaries via mise` | **DELETE-STEP** (or no-op) | Tools are baked into the image; `mise install` finds everything present. Keep as a cheap no-op or drop. |
| `check-metadata` matrix (~30 `just <target>`) | **MOVE** | Repo-metadata checks. Full-history needs (`check-red-green-replay`, `check-check-coverage-incremental`, `check-agents-ai-references-resolve`) are satisfied by the Phase 0 full-history clone. |
| ↳ `Restore uv download cache` | **DELETE-STEP** | As above. |
| ↳ `Clone sibling repos for cross-repo wiring check` (only `check-doctor-static`) | **KEEP** (~~DELETE-STEP~~ — **CORRECTED**) | ~~Point `check-doctor-static` at the on-host `/data/projects` clones.~~ **That would BREAK the containment and must not be done.** This row was written before the runner existed; the runner as BUILT executes jobs inside a rootless container that is PID/user/mount-namespace-isolated with **NO host mount** — `/data/projects` is unreachable from a job, by design, and reaching it would mean bind-mounting the host workspace (which also holds the Dolt data dir and the maintainer's checkouts) into code that a fork PR could influence. Keep cloning the **public** siblings fresh inside the container (as the shadow lane already does): no secrets, no host filesystem, still Path A. |
| ↳ `Install commit-refuse hook` (only `check-primary-checkout-commit-refuse-hook-installed`) | **MOVE** (keep) | Installs the hook from the package; runs fine on the local runner. |
| `export-telemetry` | **STAY-HOSTED** | Needs `secrets.HONEYCOMB_GITHUB_CI_INGEST_KEY_LIVESPEC` + `GH_TOKEN` (Actions API read) + `github.run_id`. push/merge_group-only, so it never affects PR feedback latency; keeping the ingest secret off the local runner preserves secret-isolation. |
| `ci-green` | **STAY-HOSTED** | Pure GitHub-expression gate (`needs: [check-python, check-metadata]`, fails if any `needs.*.result` failed). Branch protection requires ONLY this context. It does zero work, must aggregate BOTH lanes, and must stay reportable even if the local host is down — so it belongs on GitHub, not a scarce local slot. |

## The other workflows — all STAY-HOSTED

None of these belong on the unprivileged, secret-isolated local runner:

| Workflow | Trigger | Why STAY-HOSTED |
|---|---|---|
| `auto-enable-merge.yml` | `pull_request` | Mints an App token (`APP_ID` / `APP_PRIVATE_KEY`) to enable auto-merge. |
| `release-please.yml` | `push` master, `workflow_dispatch` | App-token release-PR automation. |
| `release-tag.yml` | `push` tags | Release gate (mutation testing, full heading coverage); `GITHUB_TOKEN` + Honeycomb ingest secret. |
| `release-dispatch.yml` | `repository_dispatch` / dispatch | Release chain orchestration. |
| `release-park.yml` | `schedule` (cron) | Scheduled release parking. |
| `release-readiness.yml` | `schedule` (cron) + secrets | Scheduled readiness report; `GITHUB_TOKEN` + Honeycomb secret. |
| `fast-forward-release-branch.yml` | dispatch | App-token branch fast-forward. |
| `bump-pin-from-dispatch.yml` | `repository_dispatch` | Cross-repo pin fan-out; GitHub-context-bound payload. |
| `pin-freshness.yml` | `schedule` (cron) | Scheduled pin-staleness check. |
| `copier-update-drift.yml` | `workflow_dispatch` | Template-drift check. |
| `e2e-real.yml` | `schedule` (weekly cron) + `workflow_dispatch` | Real-tier e2e; needs `ANTHROPIC_API_KEY_LIVESPEC_E2E`. Scheduled, not on the PR path. |

## The Phase 2 mechanical transformation (for `livespec`)

For each **MOVE** job in `ci.yml`:
1. `runs-on: ubuntu-latest` → the self-hosted runner label, plus a
   `container:` on the baked image (the SAME tag the Fabro sandbox runs — that
   sameness is the whole drift-collapse point).
2. Delete the `actions/cache@v4` (uv) step.
3. **KEEP** the `check-doctor-static` clone-siblings step, cloning the public
   siblings inside the container. (The original step 3 said to delete it and point
   at the on-host `/data/projects`; that is **corrected** — see the table above.
   The job container has no host mount, by design.)
4. Keep `uv sync` (it hits the hot local cache) and the `just <target>` step.
5. Add `mise trust` (a fresh container does not trust the repo `.mise.toml`) and
   set `MISE_NOT_FOUND_AUTO_INSTALL=0` so a missing shim fails fast instead of
   busy-looping — both learned live in the shadow lane.
6. Leave `export-telemetry` and `ci-green` on `ubuntu-latest`.

**Prerequisites that had to be true first (learned live, not on paper):**
- **The runner pool must be genuinely multi-runner.** The slot count IS the CI
  parallelism (each ephemeral runner takes exactly one job). At one slot the whole
  matrix serializes. Raising it surfaced two latent bugs — the credential wrapper's
  `env -i` scrub silently discarding the unit's `Environment=` config, and every
  runner sharing one runner root and so destroying each other's sessions. Both are
  fixed in `livespec-dev-tooling` `ci-runner/`; verified by a 12-job matrix running
  12-concurrent on 12 distinct runners.
- **The image tag must be the factory's**, not a stale pin, or "CI == sandbox" is
  not actually true and the drift the epic exists to collapse survives.

## Merge-gate fallback (Phase 2 deliverable — designed, not just named)

`ci-green` stays hosted and is the sole branch-protection context, but it
`needs:` the two MOVED matrices. If the local host is down, those matrices
never report and `ci-green` never goes green — merges would silently stall
(up to the 24h queue timeout). Fallback mechanism (pick one; recommend the
first):

1. **A `workflow_dispatch`-switchable `runs-on` variable** (a repo/org
   Actions *variable* holding the runner label, defaulting to the
   self-hosted label, flippable to `ubuntu-latest`): one toggle re-routes
   the moved matrices back to GitHub-hosted when the host is down. Simple,
   auditable, no new gate job.
2. A **gate meta-job that accepts either lane** (a matrix over
   `[self-hosted, ubuntu-latest]` with `if:` selection), so a hosted run
   satisfies `ci-green` when the local lane is absent. More moving parts.

Runner-liveness/absence detection is P-host's job (`livespec-3lev.1`); this
fallback is the *response* to that signal.

## Fan-out caveat (Phase 3)

This table is the TEMPLATE, not a fill-in-the-blank for every repo. Phase 3
must re-derive each fleet member's disposition from ITS OWN workflows: the
fleet is non-uniform (different matrices, different secrets, different
release wiring). In particular, `livespec-console-beads-fabro` (Rust) and
the Driver repos will each have a different check set. Confirm per repo;
never assume this `livespec` shape holds.

## Judgment calls (flagged, with recommendations)

- **`setup` MOVE vs STAY-HOSTED.** It reads only env-injected `github.*`
  context, so it CAN move, and it sits on the critical path (everything
  `needs:` it), which argues for local/hot. Recommend **MOVE**; the only
  argument to keep it hosted is uniformity with the two gate jobs, which is
  weak. Reversible either way.
- **`export-telemetry` MOVE vs STAY.** A local runner co-located with the
  collector could technically export, but it needs the Honeycomb CI ingest
  secret + Actions API token on the runner — which breaks secret-isolation
  for a job that has zero PR-latency impact (push-only). Recommend **STAY**.
