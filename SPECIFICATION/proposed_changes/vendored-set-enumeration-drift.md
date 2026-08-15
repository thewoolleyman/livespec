---
topic: vendored-set-enumeration-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-15T06:00:00Z
---

## Proposal: Supersede v104's livespec_runtime removal plan and record the package as vendored

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md
- SPECIFICATION/non-functional-requirements.md

### Summary

At **v104** (`a0601e6d`, 2026-06-10) this specification RATIFIED removing `livespec_runtime` from core's vendored set: that one accepted change deleted its `### Locked vendored libs` entry, pruned it from the re-vendoring enumeration, and added the clause scheduling "physical removal of the still-present vendored tree and its `.vendor.jsonc` entry". That plan was coherent when made, because the v104-era vendored package was substantially the `cross_repo` machinery core was shedding.

**The premise died.** Re-vendorings through `v0.19.0` (2026-08-13) grew the package well beyond `cross_repo`, and **v206** (2026-08-14) ratified `_vendor/livespec_runtime/api_configurable_keys.json` as the single declarative source of spec-governance policy keys. Core now cannot read its own policy config without the tree v104 scheduled for deletion.

This proposal therefore SUPERSEDES v104's removal plan on changed facts. It is not a wording repair, and a ratifier should read it as a reversal of a ratified decision, made deliberately and with the superseded record cited.

### Motivation

Surfaced by the independent adversarial review of the `spec-governance-manifest-authority-drift` proposal (ratified as v206), whose new "owned by the vendored `livespec_runtime` package" clause collided with the statements below. The maintainer directed on 2026-08-14 that it be filed separately, and on 2026-08-15 — after review established the true provenance — that it proceed as an explicit supersession of v104 rather than as a documentation fix.

**An earlier draft of this proposal claimed the removal clause's "intent is plainly the `cross_repo/` subtree; the wording generalised beyond that intent". That was FALSE and is retracted here.** `a0601e6d` shows the deletion, the enumeration pruning, and the clause landing together under a deliberate "drop core's vendoring mandate" heading. Whole-package removal was the plan, not a slip. The correction matters because a reader of the archived record must see that this reverses a ratified decision rather than repairing sloppy text.

**A second claim in that draft was also false and is retracted:** it said removal would delete "the `credentials` and `github_auth` subpackages core imports". Core imports NEITHER. Measured at `a11585a3`, excluding `_vendor/` and `history/`, core's importers of the vendored package are `livespec/parse/cross_repo.py` (`cross_repo`), `livespec/spec_governance/registry.py` and `default_block.py` plus two `dev-tooling/checks/` modules (`spec_governance`), and the worktree reaper (`hygiene_scan`, dev-time). The `credentials` and `github_auth` subpackages are consumed by the ORCHESTRATOR's separately-vendored copy, not by core. The runtime argument stands on `spec_governance` alone, and is stated that way below.

Measured state, re-derived rather than inherited:

- `.vendor.jsonc` carries SIX entries; `livespec_runtime` is among them, pinned `v0.19.0`, vendored 2026-08-13.
- `spec.md`'s enumeration names FOUR items; §"Locked vendored libs" carries FIVE bullets. `livespec_runtime` is absent from both.
- The vendored tree ships `api_configurable_keys.json`, `spec_governance.py`, `cross_repo/`, `hygiene_scan*`, `credentials.py`, `github_auth/`, `attention_item.py` and more.

### Proposed Changes

FIVE EDITS across three files, each replacing text that exists verbatim and exactly once in the live file today.

**Edit 1 — `spec.md`, the vendored-dependency enumeration.** Replace exactly:

```
Vendored runtime dependencies are: `fastjsonschema`, `returns` (+ vendored upstream `typing_extensions` per v027 D1), `structlog`, and a hand-authored JSONC shim per v026 D1.
```

with:

```
Vendored runtime dependencies are: `fastjsonschema`, `returns` (+ vendored upstream `typing_extensions` per v027 D1), `structlog`, a hand-authored JSONC shim per v026 D1, and `livespec_runtime`.
```

**Edit 2 — `constraints.md`, the removal clause (the v104 supersession).** Replace exactly:

```
The cross-repo work-item dependency machinery (`livespec_runtime.cross_repo`) is deliberately absent from this set: the orchestrator that uses `livespec_runtime.cross_repo` owns its own vendoring or dependency declaration per its own specification (physical removal of the still-present vendored tree and its `.vendor.jsonc` entry is Phase-2 implementation work).
```

with:

```
The cross-repo work-item dependency machinery (`livespec_runtime.cross_repo`) carries no locked-lib entry of its own: it ships inside the vendored `livespec_runtime` tree per §"Locked vendored libs", and the orchestrator that uses `livespec_runtime.cross_repo` owns its own vendoring or dependency declaration per its own specification. Removing the `cross_repo/` subtree from that tree remains implementation work, gated on first retiring core's own import of it at `livespec/parse/cross_repo.py` — until that import is retired, the subtree cannot be pruned without breaking core. The `livespec_runtime` package itself and its `.vendor.jsonc` entry are NOT removed regardless, because core consumes it at runtime beyond that one subtree — notably `livespec_runtime.spec_governance`, the loader for the manifest this specification names as the single declarative source.
```

**Edit 3 — `constraints.md`, §"Locked vendored libs".** Append an entry after the `typing_extensions` bullet, matching its siblings' shape (upstream, licence token, rationale). Replace exactly:

```
The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.
```

with:

```
The verbatim PSF-2.0 `LICENSE` is shipped at `_vendor/typing_extensions/LICENSE`.
- **`livespec_runtime`** (thewoolleyman/livespec-runtime, MIT) — the fleet's own shared-runtime library, vendored so core resolves it without a package install. Supplies `spec_governance` (the manifest resource and its loader), the `cross_repo/` subtree, `hygiene_scan`, `credentials`, `github_auth`, and `attention_item`. Core imports `spec_governance` on every spec-governance config read and `cross_repo` from `livespec/parse/`.
```

**Edit 4 — `constraints.md`, the re-vendoring enumeration.** v104 pruned `livespec_runtime` from this list in the same change that deleted the entry. Restoring the entry without restoring this leaves a locked lib with no blessed mutation path, and the direct-edit prohibition keys to this enumeration. Replace exactly:

```
**Re-vendoring** of upstream-sourced libs (`returns`, `fastjsonschema`, `structlog`, `typing_extensions`) MUST go through `just vendor-update <lib>`
```

with:

```
**Re-vendoring** of upstream-sourced libs (`returns`, `fastjsonschema`, `structlog`, `typing_extensions`, `livespec_runtime`) MUST go through `just vendor-update <lib>`
```

**Edit 5 — `non-functional-requirements.md`, the consumption-surface sentence.** Under v104's plan the vendored copy was temporary, so "one surface" was the end-state. Superseding that makes core permanently carry two. Replace exactly:

```
git = "https://github.com/thewoolleyman/livespec-runtime.git"` plus `tag = "vX.Y.Z"`.
```

with:

```
git = "https://github.com/thewoolleyman/livespec-runtime.git"` plus `tag = "vX.Y.Z"`. `livespec` core additionally VENDORS the package under `_vendor/` per `constraints.md` §"Locked vendored libs" — an instance of the source-copied shape §"Shared content provenance" describes — so core carries both surfaces.
```

**Why this direction.** §"Locked vendored libs" states that each lib is "pinned to an exact upstream ref recorded in `<repo-root>/.vendor.jsonc`". `livespec_runtime` is pinned there, so its absence makes the enumeration contradict its own membership rule. And the removal clause cannot be executed as written: deleting the package would remove the manifest v206 ratified as authoritative.

**The alternative, recorded and put to the maintainer.** v104 could be treated as still binding, closing the drift the other way — leave the enumerations excluding the package and file implementation work to unwind core's dependence so the removal can happen. That is coherent and respects the ratified plan, but it is a substantial reversal of v206 (the manifest would need a different home) and rebuilds core's spec-governance boot path. It was put to the maintainer on 2026-08-15 and DECLINED in favour of superseding v104.

**Deliberately out of scope.** Three live statements describe `_vendor/**` as third-party code — `constraints.md` §"Constraint scope" and its §intro, and `non-functional-requirements.md`'s exemption clause — while `livespec_runtime` is the fleet's own library. Whether the style and coverage exemption covers a first-party vendored package is a PRE-EXISTING question this proposal neither creates nor settles; the entry added by Edit 3 deliberately avoids introducing a "first-party" classification token so as not to widen into it. That question is owed, and no filing for it existed as of this proposal's last revision (2026-08-15).

**Also observed, not addressed here:** `.vendor.jsonc`'s own header comment states a vendored-entry count that no longer matches the file (a non-spec artifact, so outside a spec proposal's reach; `NOTICES.md` line 20 already states the correct six-entry count and needs no fix); and `_vendor/livespec_runtime/LICENSE` names tag `v0.3.0` while the pin is `v0.19.0`.
