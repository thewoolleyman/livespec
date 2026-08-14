---
topic: vendored-set-enumeration-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-14T22:42:19Z
---

## Proposal: Record livespec_runtime in the vendored-set enumerations

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md

### Summary

Three live statements in the spec tree are inconsistent with
`.vendor.jsonc` and with each other about the vendored `livespec_runtime`
package. `spec.md` enumerates the vendored runtime dependencies as four items and
omits it; `constraints.md` §"Locked vendored libs" enumerates five entries under
an intro saying each is "pinned to an exact upstream ref recorded in
`<repo-root>/.vendor.jsonc`" and likewise omits it; and `constraints.md` records
that "physical removal of the still-present vendored tree and its `.vendor.jsonc`
entry is Phase-2 implementation work" — scheduling removal of the very tree that
v206 just named as the spec-governance manifest's home. Meanwhile `.vendor.jsonc`
carries `livespec_runtime` pinned at `v0.19.0`, and core imports from it at
runtime. This proposal brings all three into line with the shipped architecture.

### Motivation

Surfaced by the independent adversarial review of the
`spec-governance-manifest-authority-drift` proposal (ratified 2026-08-14 as
v206), which found that proposal's new "owned by the vendored `livespec_runtime`
package" clause collided with these three statements. The maintainer directed on
2026-08-14 that it be filed separately rather than folded in, because it turns on
whether the vendored tree is permanent — an architecture question a terminology
correction had no business settling. v206's archived record names this filing as
owed.

Re-derived here rather than inherited from that review:

- `.vendor.jsonc` carries SIX entries — `returns`, `fastjsonschema`, `structlog`,
  `jsoncomment`, `typing_extensions`, `livespec_runtime` (pinned `v0.19.0`,
  vendored 2026-08-13).
- `spec.md`'s enumeration names FOUR; `constraints.md` §"Locked vendored libs"
  names FIVE. `livespec_runtime` is absent from both.
- The vendored tree is NOT a `cross_repo`-only copy. It ships
  `api_configurable_keys.json`, `spec_governance.py`, `credentials.py`,
  `github_auth/`, `attention_item.py`, and `cross_repo/`.

That last fact is what settles the direction, and it is why the removal clause
cannot mean what it literally says. Removing "the vendored tree and its
`.vendor.jsonc` entry" wholesale would delete the spec-governance manifest that
v206 ratified as the single declarative source, plus the credentials and
github_auth subpackages core imports. The clause sits in a sentence scoped to
`livespec_runtime.cross_repo`, so its intent is plainly the `cross_repo/`
subtree; the wording generalised beyond that intent.

### Proposed Changes

THREE EDITS, each replacing or extending text that exists verbatim
and exactly once in the live files today.

**Edit 1 — `spec.md`, the vendored-dependency enumeration.** Replace exactly:

```
Vendored runtime dependencies are: `fastjsonschema`, `returns` (+ vendored upstream `typing_extensions` per v027 D1), `structlog`, and a hand-authored JSONC shim per v026 D1.
```

with:

```
Vendored runtime dependencies are: `fastjsonschema`, `returns` (+ vendored upstream `typing_extensions` per v027 D1), `structlog`, a hand-authored JSONC shim per v026 D1, and `livespec_runtime`.
```

**Edit 2 — `constraints.md`, the removal clause.** Replace exactly:

```
The cross-repo work-item dependency machinery (`livespec_runtime.cross_repo`) is deliberately absent from this set: the orchestrator that uses `livespec_runtime.cross_repo` owns its own vendoring or dependency declaration per its own specification (physical removal of the still-present vendored tree and its `.vendor.jsonc` entry is Phase-2 implementation work).
```

with:

```
The cross-repo work-item dependency machinery (`livespec_runtime.cross_repo`) is deliberately absent from this set: the orchestrator that uses `livespec_runtime.cross_repo` owns its own vendoring or dependency declaration per its own specification (physical removal of the still-present `cross_repo/` SUBTREE is Phase-2 implementation work; the `livespec_runtime` vendored package and its `.vendor.jsonc` entry are NOT removed, because core consumes other subpackages of it at runtime).
```

**Edit 3 — `constraints.md`, §"Locked vendored libs".** Append an entry after the
`typing_extensions` one. Replace exactly:

```
The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.
```

with:

```
The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.
- **`livespec_runtime`** (thewoolleyman/livespec-runtime, first-party) — vendored from the fleet's own shared-runtime library. Supplies the spec-governance manifest resource and loader, `credentials`, `github_auth`, `attention_item`, and the `cross_repo` subtree. Core imports it at runtime, so it is a locked vendored lib on the same footing as the third-party entries, not a transient copy.
```

**Why this direction.** The section's own intro says each locked lib is "pinned to
an exact upstream ref recorded in `<repo-root>/.vendor.jsonc`". `livespec_runtime`
is pinned there, so its absence makes the enumeration contradict its own stated
membership rule. Adding it is the reading that makes the spec self-consistent.

**The alternative, recorded and judged untenable.** A ratifier could instead hold
that `livespec_runtime` is genuinely transient — still slated for removal — and
that the enumerations correctly exclude it pending that removal. That reading
fails on evidence rather than on taste: core imports `manifest_rows()` from the
vendored package on every spec-governance config read, v206 ratified its
`api_configurable_keys.json` as the single declarative source of policy keys, and
`credentials`/`github_auth` are consumed by shipped wrappers. A vendored tree that
core cannot start without is not transient. If a maintainer nonetheless wants it
removed, that is a real architecture change requiring its own proposal and an
implementation plan — not a documentation gap this proposal should paper over.

**Scope note.** This proposal does NOT re-open whether core SHOULD depend on
`livespec_runtime`, nor whether the `cross_repo/` subtree removal should still
happen. It records the vendoring as it IS, and narrows the removal clause to the
subtree its own sentence is about.
