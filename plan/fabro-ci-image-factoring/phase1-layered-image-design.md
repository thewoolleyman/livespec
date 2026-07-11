# Phase 1 — layered sandbox image design (`base` → `python` → `python-rust`)

**Status:** design artifact, drafted 2026-07-11 from the verified current
state of `livespec-dev-tooling/docker/fabro-sandbox/Dockerfile` (a single
96-line image), the console's `rust-toolchain.toml`, and the two consumers'
`workflow.toml` pins. No image was built and no repo was mutated. Companion
to `handoff.md`; tracked as epic child `livespec-3lev.4` (Phase 1).

## Goal

Split today's single `livespec-fabro-sandbox` image into three layers so
each consumer pulls the smallest image it needs and the Rust toolchain is
baked once (removing `livespec-console-beads-fabro`'s per-run `rustup`
install):

```
base          buildpack-deps:noble + bubblewrap + mise + just/lefthook/node/gh
              + BOTH ACP adapters (claude-agent-acp + codex-acp) + system git identity
  └─ python   FROM base  + uv + uv-managed CPython
       └─ python-rust  FROM python  + rustc/cargo/clippy/rustfmt (rust-toolchain pin)
```

Consumers: `livespec-orchestrator-beads-fabro` → `python`;
`livespec-console-beads-fabro` → `python-rust` (and DELETE its per-run
`rustup` script step).

## Where each line of today's Dockerfile goes

Mapping the current single Dockerfile's steps onto the three layers (order
preserved within each layer):

| Current step | Layer | Note |
|---|---|---|
| `FROM buildpack-deps:noble` | **base** | |
| `apt-get install bubblewrap` | **base** | Hard codex-acp requirement; keep the single-layer apt-clean. |
| `ARG MISE/JUST/LEFTHOOK/NODE/GH_VERSION` + mise install + `mise use -g just lefthook node gh` | **base** | Node is needed by the ACP adapters, so it lands in base with them. |
| `npm install -g @agentclientprotocol/claude-agent-acp@…` | **base** | |
| `npm install -g @zed-industries/codex-acp@…` | **base** | |
| `git config --system` neutral identity | **base** | All layers inherit it. |
| `ARG UV_VERSION` + `mise use -g uv` | **python** | |
| `ARG PYTHON_VERSION` + `uv python install` | **python** | |
| `COPY pyproject.toml uv.lock` + `uv sync` pre-warm | **DROP** | See "Pre-warm demotion" below — do NOT carry it into any layer. |
| *(new)* `ARG RUST_VERSION` + rustup (channel + clippy + rustfmt) | **python-rust** | Match `livespec-console-beads-fabro/rust-toolchain.toml`: currently **channel 1.92.0, components clippy + rustfmt**. |

## Build model — three Dockerfiles, a `FROM`-chain, one matrix

Layers are separate *published images*, each `FROM` the previous layer's
published tag (not build-stage `AS`, because consumers pull different
tags):

- `docker/fabro-sandbox/base/Dockerfile` — `FROM buildpack-deps:noble`
- `docker/fabro-sandbox/python/Dockerfile` — `FROM ghcr.io/<owner>/livespec-fabro-sandbox:base-<tag>`
- `docker/fabro-sandbox/python-rust/Dockerfile` — `FROM ghcr.io/<owner>/livespec-fabro-sandbox:python-<tag>`

`fabro-sandbox-image.yml` becomes a **matrix** over `[base, python,
python-rust]`, built **in dependency order** (base → python → python-rust,
each pinned to the digest just built — not a floating tag, to keep the
build hermetic). It **stays GitHub-hosted / on a privileged builder** (the
local runner is unprivileged — see the threat model in `handoff.md`) and
keeps `cache-from/to: type=gha`.

**Tag scheme (recommended):** one GHCR repo, layer-prefixed immutable tags —
`:base-sha-<short>`, `:python-sha-<short>`, `:python-rust-sha-<short>` (and
`:base-v<X.Y.Z>` etc.). One repo keeps the Docker daemon image store simple
and matches "matrix emitting the layered tags." (Alternative: three GHCR
repos `-base`/`-python`/`-python-rust`; more registry objects, no benefit
here.)

## Pin-lockstep implications (the ARGs now span layers)

`fabro_image_pin_lockstep.py` today parses `ARG NAME=value` from THE
Dockerfile and binds `UV_VERSION`/`JUST_VERSION`/`LEFTHOOK_VERSION` ↔
`.mise.toml [tools]` and `PYTHON_VERSION` ↔ `.python-version`. After the
split those ARGs live in different layer files:

- `JUST_VERSION`/`LEFTHOOK_VERSION` → **base** Dockerfile.
- `UV_VERSION` → **python** Dockerfile; `PYTHON_VERSION` → **python**.
- new `RUST_VERSION` → **python-rust** Dockerfile.
- `CODEX_ACP_VERSION` → **base**.

So the in-repo lockstep parser must learn to read ARGs from the *set* of
layer Dockerfiles, not a single path. Keep each ARG in exactly one layer.

**No cross-repo lockstep in `dev-tooling` (2026-07-12 correction).** An
earlier draft here proposed binding `RUST_VERSION` ↔ the console's
`rust-toolchain.toml` and `CODEX_ACP_VERSION` ↔ the orchestrator's pin *from
inside this check*. That is a **circular dependency**: `livespec-dev-tooling`
is the foundational repo those consumers depend ON, so it must not read into
them. Correct approach: for **Codex**, design the drift away — make the
orchestrator's adapter command version-less so it resolves the baked global
(no check needed); for **Rust**, any match-check lives on the **console**
side reading the image ARG (consumer→producer), never here. See
`handoff.md` (2026-07-12 correction) and `livespec-3lev.4`.

## Pre-warm demotion (carry nothing stale)

Do **not** reproduce the `COPY pyproject.toml uv.lock` + `uv sync` pre-warm
in any layer. Per `handoff.md` ("Image pre-warm demotion"): the current
pre-warm reads `livespec-dev-tooling`'s OWN lockfile, and the image's
`paths:` trigger watches only dev-tooling files, so consumer-lockfile
changes never rebuild the image and the warm layer silently rots. The
persistent local-disk `~/.cache/uv` (Phase 0) is the primary dep cache;
image layers carry base tools only.

## What stays the same

- Builds stay GitHub-hosted, `cache-from/to: type=gha`, immutable
  `sha-<short>` + `v<X.Y.Z>` tags, triggered on image-affecting `paths:`.
- No secrets baked; credentials still arrive per-run via the Fabro env
  table.
- bubblewrap + both ACP adapters remain mandatory in `base` (dropping
  either silently breaks Codex-driven runs).

## Consumer switch + the manual-pin gap

- `livespec-orchestrator-beads-fabro` `workflow.toml`: `…:v0.38.1` →
  `…:python-<tag>`.
- `livespec-console-beads-fabro` `workflow.toml`: `…:sha-ea684ad` →
  `…:python-rust-<tag>`, and **delete** the `curl … rustup.rs` script step.
- Both image refs are **manual pins** (the workflow.toml PIN SURFACE NOTE:
  workflow.toml docker images are not covered by the `.github/workflows
  uses:` pin-bump automation). The two consumers also currently use
  *different* pin styles (console `:sha-<short>`, orchestrator
  `:v<X.Y.Z>`) — reconcile to one style during the switch. The
  autodiscovery-vs-manual-pin decision (`handoff.md` open decisions) applies
  here.

## Sequencing note

Nothing in THIS design is gated by a P-host baseline — that "multi-day
baseline" was over-engineered and is dead (see `handoff.md`, 2026-07-12);
the layer split, build matrix, and consumer switch are all authorable now,
and P-host no longer gates them. The Codex version-less-command fix (which
removes any need for a Codex pin check) waits behind the orchestrator
`dispatcher.py` refactor. The image split + Rust bake + console rustup
removal are the unblocked core.
