---
topic: spec-governance-manifest-authority-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-14T08:01:46Z
---

## Proposal: Correct the spec-governance manifest's path AND its authority claim

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

`contracts.md` §"Spec-governance control wrapper" ends with a sentence that is wrong in TWO independent ways. It names the committed `ConfigKey` manifest at `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json`, a path that resolves to nothing — the manifest is at `.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json`. And it asserts that a declarative `ConfigKey` registry and that manifest are CO-AUTHORITATIVE, which stopped being true in the same relocation: `registry.py` is now a compatibility projection DERIVED from the manifest, so there is one authority, not two in maintained agreement.

Correcting only the path would be worse than correcting neither: a freshly-accurate path signals to a reader that the sentence was reviewed, laundering the false architecture claim beside it. For the same reason this proposal corrects the OTHER statements that call the projection declarative — two more clauses in the same `contracts.md` paragraph, and one sentence in `spec.md` that asserts the derivation runs the opposite way.

### Motivation

The path half was surfaced by the independent adversarial review of the `spec-governance-flag-drift` proposal (ratified 2026-08-14 as v204), which noticed the stale path in the same paragraph it was reviewing and correctly declined to fold an unrelated correction into a ratification.

**The authority half was surfaced by the independent adversarial review of THIS proposal's first draft**, which filed the path swap alone on the stated premise that "the `ConfigKey` registry itself has NOT moved" and that the co-authoritative relationship therefore survived intact. That premise was false, and the way it was checked is the transferable lesson: the first draft verified that `registry.py` still EXISTS at the cited path. It does. But existence is the wrong instrument — the file stopped being an authority while staying exactly where it was.

**The remaining contradicting clauses were surfaced by TWO independent adversarial reviews of the second draft, which found DISJOINT sets.** One found the same-paragraph clause; the other found the `spec.md` sentence, the miscount corrected below, and a vendoring-enumeration collision recorded under "Deliberately out of scope". Neither review alone was sufficient, and they graded the same-paragraph clause differently — one a blocker, one non-blocking. That disagreement is recorded rather than resolved silently, because a future reader deserves to know the finding was contested.

Measured against `origin/master`, and against the pre-relocation tree:

- Before `d2ab3cbf`, `registry.py` was a genuine declarative registry: a hand-written `ConfigKey` frozen dataclass plus a literal `CONFIG_KEYS` tuple enumerating each key. Two independently-authored artifacts that had to be kept in agreement — which is exactly what "co-authoritative" described, and it was accurate then.
- On `origin/master` today, `registry.py`'s own module docstring reads "Compatibility projection for the runtime-owned spec-governance manifest," and its entire body is `ConfigKey: TypeAlias = ManifestRow` plus `CONFIG_KEYS: tuple[ConfigKey, ...] = tuple(manifest_rows())`.
- `manifest_rows()` lives in the vendored `livespec_runtime.spec_governance` and reads the JSON via `importlib.resources`. The vendored package ships no registry module.

So agreement between the two is now tautological rather than maintained. A projection definitionally equal to its source cannot be co-authoritative with it.

Corroborating this from the enforcement side rather than by reading alone: `dev-tooling/checks/spec_governance_manifest.py` compares the JSON file against the runtime LOADER's projection — not registry-against-manifest, which is the check the retired relationship would have required.

Drift dated: the vendored copy was added by `a59720f7` ("chore(deps): bump livespec-runtime pin to v0.18.0", 2026-08-09) and the old path was deleted, with consumers switched, by `d2ab3cbf` ("fix: consume runtime spec governance defaults", 2026-08-09). `d2ab3cbf` touched ZERO `SPECIFICATION/` files — the same implementation-moved-without-the-contract pattern behind v204 and v205.

Outside frozen `history/`, the stale path occurs exactly once in the spec tree (`contracts.md`). It also appears in 20 files across 16 frozen `SPECIFICATION/history/` snapshots (v190–v205), which are conventionally exempt and are not touched.

### Proposed Changes

FOUR EDITS: three to `SPECIFICATION/contracts.md` and one to `SPECIFICATION/spec.md`, each replacing text that exists verbatim and exactly once in the live files today.

**Edit 1 — the closing sentence of the control-wrapper paragraph.** Replace this sentence exactly:

```
The single declarative `ConfigKey` registry and committed manifest `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json` are co-authoritative; a row carries the key, value type, safe default, per-proposal-override support, and allowed values.
```

with:

```
The committed manifest `.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json`, owned by the vendored `livespec_runtime` package, is the single declarative source; `.claude-plugin/scripts/livespec/spec_governance/registry.py` re-exports it as a compatibility projection (`ConfigKey` / `CONFIG_KEYS`) preserving the former core import path. A row carries the key, value type, safe default, per-proposal-override support, and allowed values.
```

**Edit 2 — the `--check-default-block` clause, same paragraph.** This clause survives Edit 1 and would otherwise call the projection declarative three clauses before Edit 1 calls it a projection. It is also imprecise about what the check compares: `verify_default_block(text=..., manifest=...)` builds `{row.key: row.safe_default for row in manifest}` and reports `missing`, `extra`, and `default_drift` — so it compares the documented block's KEY SET and its VALUES against the manifest. Replace exactly:

```
still matches the declarative `ConfigKey` registry,
```

with:

```
still matches the committed manifest's keys and safe defaults,
```

**Edit 3 — the `--show-effective` clause, same paragraph.** Residual registry-as-authority phrasing. Replace exactly:

```
emits the declarative registry manifest together with
```

with:

```
emits the declarative manifest together with
```

**Edit 4 — `spec.md` §"Spec-governance policy settings".** This sentence asserts the derivation direction that `d2ab3cbf` INVERTED: it makes the committed manifest a DRIVEN OUTPUT of a registry row, which is the pre-relocation architecture. Left unamended, the live spec would assert both derivation directions at once. Replace exactly:

```
One declarative registry row per key MUST drive parsing, type-strict coercion, allowed-value diagnostics, control-surface rendering, and the committed API-configurable-key manifest.
```

with:

```
One declarative manifest row per key MUST drive parsing, type-strict coercion, allowed-value diagnostics, and control-surface rendering.
```

The single-sourcing requirement the sentence exists to impose is preserved exactly; only the artifact it names as the source changes, and the manifest stops being listed as something the source drives.

**Why this direction.** The Edit 1 wording was chosen by the maintainer on 2026-08-14 from two candidates. The alternative — stating only that the manifest is the single declarative source and saying nothing about `registry.py` — is also accurate and shorter, and was declined because the compatibility import path is real, still works, and is load-bearing for anyone reading livespec's own code; a contract that omits it sends a reader to an import the contract never mentions.

A third option, ratifying the path swap alone and filing the authority wording separately, was put to the maintainer and DECLINED. It buys minimal separable dispositions at the cost of knowingly ratifying a false clause, with the corrected path making the whole sentence read as freshly reviewed.

**What is preserved deliberately.** The five fields a row carries are unchanged, and the word "committed" is retained: vendored files are tracked in this repository, so the manifest is a committed artifact rather than a fetched or generated one. The `ConfigKey` name is retained because it remains the live exported symbol.

**Deliberately out of scope, and filed separately.** The second review surfaced a collision between Edit 1's `livespec_runtime` ownership clause and three live statements about vendoring: `spec.md`'s enumeration of vendored runtime dependencies omits `livespec_runtime` although `.vendor.jsonc` carries it; `constraints.md` §"Locked vendored libs" likewise omits it; and `constraints.md` records that physical removal of that vendored tree and its `.vendor.jsonc` entry is Phase-2 implementation work — so the spec schedules removal of the tree Edit 1 names as the manifest's home.

That drift is PRE-EXISTING — this proposal surfaces it rather than creating it — and it turns on a question this proposal has no business settling: whether `livespec_runtime`'s vendored tree is permanent or still slated for removal. That is an architecture call. The maintainer directed on 2026-08-14 that it be filed as its own proposal rather than folded in here, precisely so a terminology correction does not silently decide a packaging question.

**Scope note.** This proposal does NOT re-open where the manifest should live, whether the compatibility shim should eventually be retired, or whether core should depend on `livespec_runtime` for policy defaults. It records the architecture as it IS on master.
