---
topic: spec-governance-manifest-path-drift
author: claude-opus-5-spec-side-autonomy
created_at: 2026-08-14T08:01:46Z
---

## Proposal: Correct the spec-governance ConfigKey manifest path

### Target specification files

- SPECIFICATION/contracts.md

### Summary

`contracts.md` §"Spec-governance control wrapper" names the
committed `ConfigKey` manifest at
`.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json`.
No such file exists: the manifest was relocated to
`.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json` in
`d2ab3cbf` (2026-08-09), a commit that changed no specification file. The
contract therefore points a reader at a path that resolves to nothing. This
proposal corrects the path and changes nothing else — in particular it does NOT
touch the co-authoritative relationship the sentence asserts, because the
`ConfigKey` registry itself did not move.

### Motivation

Surfaced by the independent adversarial review of the
`spec-governance-flag-drift` proposal (ratified 2026-08-14 as v204), which
noticed the stale path in the SAME paragraph it was reviewing but correctly
declined to fold an unrelated correction into a ratification. It is filed here
as its own topic so it can be dispositioned on its own.

Verified independently before filing rather than inherited from that review:
`git ls-tree -r --name-only origin/master` finds
`api_configurable_keys.json` at exactly one path, and it is NOT the cited one;
the cited path resolves to nothing on `origin/master`; and the string appears
exactly once anywhere under `SPECIFICATION/`.

Drift dated by locating the relocation: the old path was deleted in `d2ab3cbf`
("fix: consume runtime spec governance defaults", 2026-08-09), a commit that
touched ZERO `SPECIFICATION/` files — the same implementation-moved-without-the-
contract pattern behind the two drifts ratified as v204 and v205.

That the new path is the one actually in force is confirmed by a consumer rather
than by the file listing alone: `dev-tooling/checks/spec_governance_manifest.py`
builds `_MANIFEST_PATH` from `.claude-plugin / scripts / _vendor /
livespec_runtime / api_configurable_keys.json` and compares the runtime loader's
projection against it, so a check inside `just check` reads exactly the path
this proposal writes into the contract.


### Proposed Changes

ONE EDIT TO `SPECIFICATION/contracts.md`, replacing text that exists verbatim
and exactly once in the live file today.

**Edit 1 — the manifest path in the control-wrapper paragraph.** Replace this
sentence exactly:

```
The single declarative `ConfigKey` registry and committed manifest `.claude-plugin/scripts/livespec/spec_governance/api_configurable_keys.json` are co-authoritative; a row carries the key, value type, safe default, per-proposal-override support, and allowed values.
```

with:

```
The single declarative `ConfigKey` registry and committed manifest `.claude-plugin/scripts/_vendor/livespec_runtime/api_configurable_keys.json` are co-authoritative; a row carries the key, value type, safe default, per-proposal-override support, and allowed values.
```

**Why this direction.** There is no alternative. The contract names a path that
does not exist, so the only question is which true path replaces it. The
manifest was relocated, not deleted, and the relocation is load-bearing rather
than incidental: the spec-governance defaults are now sourced from the vendored
`livespec_runtime` package, and `_vendor/` is a read-only vendored tree.

**What this proposal does NOT change, deliberately.** The `ConfigKey` registry
itself has NOT moved — it remains at
`.claude-plugin/scripts/livespec/spec_governance/registry.py`, in livespec's own
tree. Only the JSON manifest moved into the vendored tree. The sentence's
substantive claim therefore survives intact: a locally-owned registry and a
committed manifest remain co-authoritative, and a row still carries the same
five fields. This is a path correction, not a restatement of the
co-authoritative relationship, and it should not be read as one.

**Scope note.** The word "committed" is retained and remains accurate: vendored
files are committed to this repository, so the manifest is still a committed
artifact rather than a build-time or fetched one.

