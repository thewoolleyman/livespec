# Cache tier 2 — a local GitHub Actions cache service: design pass

Design pass for `livespec-s43svm.3`, tier 2 of the three cache tiers in
`design.md` §"Cache tiers, and the volume that holds them" ("A local Actions
cache — NOT built. `actions/cache` today resolves to GitHub's service, which
caps a repository at ten gigabytes ... A local cache service on this host
removes both the cap and the round-trip. This is the tier the maintainer's
instruction most directly names."). Written 2026-08-23 against live state; it
recommends, it does not decide — the build/no-build call is recorded on the
work-item for the maintainer.

## Bottom line

A local Actions cache service on the k3s/ARC lane is BUILDABLE but costs
running a THIRD-PARTY FORK of the GitHub runner binary in every scale set (or
hex-patching `Runner.Worker.dll` and pinning self-update off), and as of this
pass it has ZERO consumers: every fleet workflow deliberately skips
`actions/cache` on the self-hosted lane, tier 1 (`livespec-s43svm.2`, shipped
2026-08-23) now serves the one cache those skipped steps existed for, and the
fleet's only Rust repository measured cold cargo on this host as faster than
warm-cached hosted and deleted its cache steps on that evidence. Recommendation:
DO NOT BUILD until a consumer exists; leave `.3` open on the maintainer's word,
with this pass as the re-entry point.

## What `actions/cache` needs from a self-hosted server (the mechanism)

`actions/cache` v4 (toolkit `@actions/cache` ≥ 4) speaks the cache service
**v2** protocol — a twirp API the runner advertises to the step through
`ACTIONS_RESULTS_URL`, authenticated with `ACTIONS_RUNTIME_TOKEN`. The legacy v1
(`ACTIONS_CACHE_URL`) path is what older self-hosted servers emulated.

The leading drop-in server, `falcondev-oss/github-actions-cache-server`
(v9.7.0, 2026-07-29; filesystem/S3 storage, SQLite/Postgres metadata,
v2-only), documents the integration contract as (read from its getting-started
page 2026-08-23):

- the runner must be pointed at the server by `ACTIONS_RESULTS_URL` (trailing
  slash required), and
- **"the runner does not allow setting the `ACTIONS_RESULTS_URL` yourself, we
  need to patch the runner binary/source"** — the official runner hardcodes the
  results endpoint from the job message. Two sanctioned ways: run their forked
  image `ghcr.io/falcondev-oss/actions-runner` (reads
  `CUSTOM_ACTIONS_RESULTS_URL`, skips self-update while it is set), or hex-patch
  `Runner.Worker.dll` and keep the patch across updates.
- for ARC, `disableUpdate: true` so a runner self-update cannot revert the patch.

So on this pool the minimum shape is: a `ci-actions-cache` namespace running
the server (hostPath or PVC on `/var/cache/ci-runner`, the ~100 GB the design
record budgets), plus EVERY `phase2/arc/values-*.yaml` switched from
`ghcr.io/actions/actions-runner` to the fork (or a fleet-built patched image)
with the env var set — i.e. the fleet's gating CI executes inside a runner
binary the fleet does not build and GitHub does not ship. That is the cost the
design record's one-line "a local cache service on this host" did not price.

## Who would use it (consumer census, 2026-08-23)

| Repository | `actions/cache` on the self-hosted lane today |
|---|---|
| `livespec` | Skipped: `Restore uv cache (hosted lane only — self-hosted uses ~/.cache/uv)` is gated on `LIVESPEC_CI_LANE == 'hosted'` |
| `livespec-dev-tooling` | One `actions/cache` step, in `check-fleet-conformance` — a job pinned to `ubuntu-latest`; its k3s-lane jobs run `uv sync` with no cache step |
| `livespec-runtime`, `livespec-orchestrator-git-jsonl`, `livespec-overseer`, `livespec-driver-claude`, `-codex`, `-pi` | `uv sync` with no cache step on either lane (zero `actions/cache` in `ci.yml`, read 2026-08-23) |
| `livespec-console-beads-fabro` | Cache steps DELETED by measurement: cold `cargo clippy` 37 s here vs 53 s warm-cached hosted; "KEEPING actions/cache on a self-hosted runner would be actively worse: it would network-restore/save a multi-GB cache FROM this host every run — precisely the cost co-locating removes" |
| `livespec-orchestrator-beads-fabro` | Deliberately hosted-only; not routed to this pool |

Zero steps on the k3s lane would hit a local cache server today. The premise
the skipped steps rest on — a warm on-host uv cache — was false on ephemeral
ARC pods between the podman deletion (2026-08-21) and tier 1 (2026-08-23), and
is true again now: measured `uv sync` 7.9 s cold → 0.5 s warm from the tier-1
lower, with no workflow change and no runner-binary change.

## The 10 GB cap, priced for this fleet

The cap is per repository on GitHub's service. The fleet's hosted-lane uv
caches are ~0.4 GB per repository (the fleet-wide UNION of all nine locked
dependency trees is 379 MB); nothing in the fleet approaches 10 GB. The cap
binds for homelab-scale Nix/Rust artefacts — tier 3's domain — not for anything
this pool serves.

## What would change the recommendation

Any one of: a workflow that actually restores a multi-GB keyed cache on the
self-hosted lane and measures the network round-trip as its bottleneck; a
second Rust repository whose measurement contradicts the console's; homelab
routing Nix builds to this pool and asking for keyed artefact caching rather
than a served closure directory (tier 3). Then build it in this shape: server
in its own namespace on the dedicated volume, runner image switched fleet-wide
by the one values pattern, `disableUpdate: true`, and the first consumer's
before/after timings recorded on `.3` before the next repository adopts it.
