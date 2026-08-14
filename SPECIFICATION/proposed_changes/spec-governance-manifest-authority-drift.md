---
topic: spec-governance-manifest-authority-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-14T08:01:46Z
---

## Proposal: Correct the spec-governance manifest's path AND its authority claim

### Target specification files

- SPECIFICATION/contracts.md

### Summary

`contracts.md` §"Spec-governance control wrapper" ends with a sentence that is wrong in TWO independent ways. It names the committed `ConfigKey` manifest at `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json`, a path that resolves to nothing — the manifest is at `.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json`. And it asserts that a declarative `ConfigKey` registry and that manifest are CO-AUTHORITATIVE, which stopped being true in the same relocation: `registry.py` is now a compatibility projection DERIVED from the manifest, so there is one authority, not two in maintained agreement.

This proposal corrects both, because correcting only the path is worse than correcting neither: a freshly-accurate path signals to a reader that the sentence was reviewed, laundering the false architecture claim beside it.

### Motivation

The path half was surfaced by the independent adversarial review of the `spec-governance-flag-drift` proposal (ratified 2026-08-14 as v204), which noticed the stale path in the same paragraph it was reviewing and correctly declined to fold an unrelated correction into a ratification.

**The authority half was surfaced by the independent adversarial review of THIS proposal's first draft**, which filed the path swap alone on the stated premise that "the `ConfigKey` registry itself has NOT moved" and that the co-authoritative relationship therefore survived intact. That premise was false, and the way it was checked is the transferable lesson: the first draft verified that `registry.py` still EXISTS at the cited path. It does. But existence is the wrong instrument — the file stopped being an authority while staying exactly where it was.

Measured against `origin/master`, and against the pre-relocation tree:

- Before `d2ab3cbf`, `registry.py` was a genuine declarative registry: a hand-written `ConfigKey` frozen dataclass plus a literal `CONFIG_KEYS: tuple[ConfigKey, ...]` enumerating each key. Two independently-authored artifacts that had to be kept in agreement — which is exactly what "co-authoritative" described, and it was accurate then.
- On `origin/master` today, `registry.py`'s own module docstring reads "Compatibility projection for the runtime-owned spec-governance manifest," and its entire body is `ConfigKey: TypeAlias = ManifestRow` plus `CONFIG_KEYS: tuple[ConfigKey, ...] = tuple(manifest_rows())`.
- `manifest_rows()` lives in the vendored `livespec_runtime.spec_governance` and reads the JSON via `importlib.resources`. The vendored package ships no registry module.

So agreement between the two is now tautological rather than maintained. A projection definitionally equal to its source cannot be co-authoritative with it.

Corroborating this from the enforcement side rather than by reading alone: `dev-tooling/checks/spec_governance_manifest.py` compares the JSON file against the runtime LOADER's projection — not registry-against-manifest, which is the check the retired relationship would have required.

Drift dated: the vendored copy was added by `a59720f7` ("chore(deps): bump livespec-runtime pin to v0.18.0", 2026-08-09) and the old path was deleted, with consumers switched, by `d2ab3cbf` ("fix: consume runtime spec governance defaults", 2026-08-09). `d2ab3cbf` touched ZERO `SPECIFICATION/` files — the same implementation-moved-without-the-contract pattern behind v204 and v205.

Outside frozen `history/`, the stale path occurs exactly once in the spec tree (`contracts.md`). It also appears in 20 frozen `SPECIFICATION/history/` snapshots, which are conventionally exempt and are not touched.

### Proposed Changes

ONE EDIT TO `SPECIFICATION/contracts.md`, replacing text that exists verbatim and exactly once in the live file today.

**Edit 1 — the closing sentence of the control-wrapper paragraph.** Replace this sentence exactly:

```
The single declarative `ConfigKey` registry and committed manifest `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json` are co-authoritative; a row carries the key, value type, safe default, per-proposal-override support, and allowed values.
```

with:

```
The committed manifest `.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json`, owned by the vendored `livespec_runtime` package, is the single declarative source; `.claude-plugin/scripts/livespec/spec_governance/registry.py` re-exports it as a compatibility projection (`ConfigKey` / `CONFIG_KEYS`) preserving the former core import path. A row carries the key, value type, safe default, per-proposal-override support, and allowed values.
```

**Why this direction.** The wording was chosen by the maintainer on 2026-08-14 from two candidates. The alternative — stating only that the manifest is the single declarative source and saying nothing about `registry.py` — is also accurate and shorter, and was declined because the compatibility import path is real, still works, and is load-bearing for anyone reading livespec's own code; a contract that omits it sends a reader to an import the contract never mentions.

A third option, ratifying the path swap alone and filing the authority wording separately, was put to the maintainer and DECLINED. It buys minimal separable dispositions at the cost of knowingly ratifying a false clause, with the corrected path making the whole sentence read as freshly reviewed.

**What is preserved deliberately.** The five fields a row carries are unchanged, and the word "committed" is retained: vendored files are tracked in this repository, so the manifest is a committed artifact rather than a fetched or generated one. The `ConfigKey` name is retained because it remains the live exported symbol.

**Scope note.** This proposal does NOT re-open where the manifest should live, whether the compatibility shim should eventually be retired, or whether core should depend on `livespec_runtime` for policy defaults. It records the architecture as it IS on master. Any change to that architecture is a separate design question.
