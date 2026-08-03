---
topic: railway-dependency-supply-for-a-source-copied-library
author: claude-opus-5
created_at: 2026-08-03T04:12:31Z
---

## Proposal: Railway dependency supply is shape-dependent: a source-copied library declares and imports bare rather than nesting a vendor tree

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The fleet-wide ROP railway clause in `non-functional-requirements.md` §"Shared content provenance" states flatly that ``dry-python/returns` is vendored under `_vendor/``. That fragment is written from the plugin-repo vantage — a repo whose Python is run out of its own checkout — and does not answer how the requirement is satisfied by a repo whose own package is ITSELF copied verbatim into other governed repos' `_vendor/` trees. This proposal replaces the flat fragment with a two-shape supply rule: a directly-consumed repo vendors `returns` under its own `_vendor/` root as today; a source-copied library MUST instead declare `dry-python/returns` as a real `pyproject.toml` `dependencies` entry and import it BARE, and MUST NOT nest a `_vendor/` tree inside its own package. It further states the closure obligation the source-copied shape depends on: a repo that vendors a first-party livespec library source-only MUST itself supply that library's declared third-party dependencies, because an import satisfied only by the host interpreter's ambient environment is not satisfied by the repo.

### Motivation

`livespec-runtime`'s 27 first-party functions cannot be converted onto the railway because the literal reading of this clause has no answer for that repo's shape, and the two available readings differ in blast radius by roughly 115 files across three consumers.

`livespec-runtime` is consumed two ways at once: installed as a wheel via a uv git source (`[build-system]` + `packages = ["livespec_runtime"]`), AND copied verbatim into three governed consumers at `.claude-plugin/scripts/_vendor/livespec_runtime/` (`livespec`, `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl` — 33 files each, re-synced by the release fan-out's `just vendor-update`). Measured on `livespec-runtime` `67bc22d`: `git ls-files | grep _vendor` returns nothing, and `returns` appears nowhere in `pyproject.toml`.

Read literally, satisfying the clause means vendoring at `livespec_runtime/_vendor/returns/` — the only placement inside the wheel, and therefore the only one serving the installed path. That manufactures the fleet's first nested `_vendor`-inside-`_vendor`: `.claude-plugin/scripts/_vendor/livespec_runtime/_vendor/returns/`, duplicated into three consumers on the next fan-out. Each of those three ALREADY vendors `returns` at its own `_vendor/` root, so two copies of the same library would sit on one `sys.path` with the winner decided by insertion order, pinned by two different `.vendor.jsonc` manifests and free to drift apart silently. That is the class of defect that broke the fleet's release fan-out for seven hours on 2026-07-30.

The repo already answers this question for its other third-party dependency, and answers it the other way. `typing_extensions` faces the identical dual-consumption problem and is resolved as: a real `pyproject.toml` `dependencies` entry (`typing_extensions>=4.4.0`), imported BARE (`from typing_extensions import assert_never` at `cross_repo/types.py:23` and `cross_repo/resolve.py:38`, with no vendor-path preamble), and supplied on the source-copied path by each consumer's own `_vendor/` root. The vendored `livespec_runtime` copy inside `livespec` carries ZERO nested `_vendor` files. So the established in-repo pattern is already 'the consuming repo's vendor root supplies the dependency', and the clause's flat wording is the only thing that makes this look like an open question.

The closure half is not decoration; it is the measured hole in that pattern. On `livespec-orchestrator-git-jsonl` `b100e7e`, first-party code imports `livespec_runtime.cross_repo.types` at three module-top-level sites (9 references in total); the vendored copy of that module does `from typing_extensions import assert_never`; and git-jsonl vendors ZERO `typing_extensions` files and declares it in neither `dependencies` nor `[dependency-groups]`, while `bin/_bootstrap.py` puts only `.claude-plugin/scripts` and `.claude-plugin/scripts/_vendor` on `sys.path`. The import resolves today solely because this host's system Python (3.13.7) ships `typing_extensions` at `/usr/lib/python3/dist-packages/`. Stated precisely, that is a latent HOST-DEPENDENT fragility rather than a confirmed live break — and its two siblings (`livespec` 2 files, `livespec-orchestrator-beads-fabro` 1) vendor the dependency explicitly, so git-jsonl is an outlier rather than a convention. Nothing noticed, because `check-vendor-manifest` validates each entry's SHAPE (url/ref/date) and never that a vendored library's own imports resolve against the consumer's `_vendor/` plus stdlib. Ratifying the source-copied shape without also stating whose job the transitive dependency is would ship `returns` into exactly that hole; the only thing making `returns` safer today is that all three consumers happen to vendor it, which is three independent decisions and not a rule.

Scope notes for the reviser, not text to ratify. (a) This proposal is deliberately confined to the supply question. It does not restate, narrow, or widen any other part of the ROP railway clause — the boundary-handler rule, the enumerated-narrow-catch rule, and the zero-first-party-Python exemption are untouched. (b) It states the closure OBLIGATION normatively and does not specify the mechanical gate that would enforce it; that check belongs to `livespec-dev-tooling`'s enforcement suite and is tracked there. (c) No `scenarios.md` entry is owed. This is a governed-repo shape requirement enforced by consumer CI, not observable behavior of any livespec spec-side operation, which is the same shape as the adjacent fleet-wide red-green-replay clause in the same bullet list; `#### Shared content provenance` carries no `tests/heading-coverage.json` entry and this proposal adds no heading.

### Proposed Changes

In `non-functional-requirements.md` §"Orchestrator plugin ecosystem" → `#### Shared content provenance`, amend the existing bullet that begins **The ROP railway is fleet+adopter-wide.** Replace the inline fragment

```
`dry-python/returns` is vendored under `_vendor/`
```

with

```
`dry-python/returns` is supplied to that repo's first-party code per the bullet below
```

leaving the remainder of that bullet — the failure-track routing, the single-outermost-boundary-handler rule, the forbidden blanket lift, the foreign-code isolation carve-out, the no-thin-repo-exemption sentence, the zero-first-party-Python exemption, and the copier-template inheritance sentence — unchanged.

Immediately after that bullet, add one new sibling bullet to the same list:

- **Railway dependency supply depends on how a repo's own code reaches its consumers.** `dry-python/returns` MUST be importable by the first-party Python of every governed repo bound by the railway requirement above. HOW it is supplied is determined by that repo's consumption shape, and the two shapes MUST NOT be conflated:
  - **Directly-consumed repo** — a plugin, application, or tool whose Python is executed from its own checkout. It MUST vendor `returns` under its own `_vendor/` root per `constraints.md` §"Vendoring procedure" and import it from there. This is the default shape and the one the clause above has always described.
  - **Source-copied library** — a repo whose package is BOTH distributed for installation AND copied verbatim into other governed repos' `_vendor/` trees (`livespec-runtime` is the reference instance). It MUST declare `dry-python/returns` as a real `pyproject.toml` `dependencies` entry, which serves the installed path, and it MUST import `returns` BARE — no vendor-path prefix, no `sys.path` manipulation, no import-time fallback — so that on the source-copied path the import resolves against the CONSUMING repo's own `_vendor/` root. Such a repo MUST NOT carry a `_vendor/` tree nested inside its own package. A nested vendor tree places two copies of one library on a single `sys.path`, decides between them by insertion order rather than by declaration, and pins them through two independent `.vendor.jsonc` manifests that MAY drift apart with nothing reading both; the source-copied shape is therefore satisfied by declaration plus a bare import, and is NOT satisfied by nesting. This is the shape `typing_extensions` already occupies in the same repo for the same reason.
  - **Dependency closure is the CONSUMING repo's obligation.** A repo that vendors a first-party livespec library source-only MUST itself supply every third-party distribution that library declares in its `pyproject.toml` `dependencies`, by whichever mechanism that consuming repo uses for its own third-party code — its `_vendor/` root for a vendoring repo, or its own `pyproject.toml` `dependencies` for an installed distribution. An import that resolves ONLY because the host interpreter's ambient environment happens to carry the distribution MUST NOT be treated as satisfied: the resolution MUST be reachable from what the repo itself declares or vendors. A source-copied library MUST keep its `pyproject.toml` `dependencies` list complete and accurate for exactly this reason — it is the list its consumers are obligated to close over.
