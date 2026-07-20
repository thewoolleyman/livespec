---
topic: fleet-control-plane-tool-repo-class
author: claude-opus-4-8
created_at: 2026-07-20T03:56:19Z
---

## Proposal: Add the control-plane-tool fleet repo class

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The §"Fleet membership contract" **Fleet manifest** paragraph enumerates the six repo classes a fleet member may carry. This proposal adds a seventh, `control-plane-tool`, for a Control-Plane member that ships an operator TOOL rather than the cockpit APPLICATION — a peer of `console`, never a component of it. The enumeration MUST be amended to include the new value, and a short defining sentence MUST be added distinguishing it from `console`. The pin-and-bump consequence is deliberately NOT restated here: `livespec-dev-tooling`'s `contracts.md` §"Bump-pin policy" already carves out non-pin-consuming members by naming `console` specifically, so a class absent from that carve-out is pin-consuming by construction, and restating the rule in core would duplicate it and invite drift.

### Motivation

The livespec overseer is moving out of livespec core into its own dedicated repo, `livespec-overseer`, registered under the manifest's `fleet` array as a full member (maintainer ruling, 2026-07-20). An earlier ruling in the same thread established that the overseer is a Control-Plane artifact, so its class must be a Control-Plane one. The existing `console` class cannot be reused. `livespec-dev-tooling`'s `_contract_rows.py` defines `_PIN_WEB_CLASSES` as a SUBTRACTION set — every class except `console` — so classing the overseer as `console` would either deny it the automatic bump-pin PRs it needs, or, if that subtraction were rewritten to admit it, drag the pure-Rust `livespec-console-beads-fabro` into the bump web alongside it. The overseer specifically needs auto-bump because its ruff, pyright-strict, coverage, and Result-railway gates all come FROM `livespec-dev-tooling`, so a dev-tooling release directly determines whether its repo stays green — precisely the case auto-bump exists to serve, and precisely the case the console's exemption was designed to avoid for a repo that consumes dev-tooling thinly (its `just check` runs two dev-tooling check modules; its remaining Python check comes from livespec core). None of the five existing pin-consuming classes fits either: the overseer ships an operator tool, so it is not a `library`, and it is neither a plugin nor the `enforcement-suite`. Core is the correct and only spec surface for this change: core's §"Fleet membership contract" states that livespec core owns fleet-level facts, and `livespec-dev-tooling`'s own SPECIFICATION does not enumerate the classes at all — its `contracts.md` mentions `console` solely in the non-pin-consuming-member context.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, §"Fleet membership contract", the **Fleet manifest** paragraph, the class enumeration MUST be amended to carry the new value:

```diff
-enumerates every fleet member in a `fleet` array, each carrying its repo class (core / enforcement-suite / impl-plugin / driver-plugin / library / console), and MAY carry an `adopters` array (see **Adopters**).
+enumerates every fleet member in a `fleet` array, each carrying its repo class (core / enforcement-suite / impl-plugin / driver-plugin / library / console / control-plane-tool), and MAY carry an `adopters` array (see **Adopters**).
```

A defining sentence for the new class MUST be added to the same paragraph, immediately after the sentence carrying the enumeration:

```diff
+A `control-plane-tool` member is a Control-Plane member that ships an operator TOOL rather than the cockpit APPLICATION the `console` class carries; the two are PEERS, and a `control-plane-tool` member MUST NOT be described as a component of, or a sidecar within, a `console` member. Unlike `console`, a `control-plane-tool` member is an ordinary pin-and-bump consumer — it is absent from the non-pin-consuming carve-out in `livespec-dev-tooling`'s `contracts.md` §"Bump-pin policy" and so inherits that policy's default, which the carve-out text itself governs; this contract MUST NOT restate the pin policy.
```

### Required ride-along co-edits (added after independent review)

An independent adversarial review found TWO further live enumerations of the
closed class set that this change would leave contradicting the amended
contract. Both MUST be co-edited in the same revise payload's
`resulting_files[]`.

**Spell both paths EXACTLY as written here.** `resulting_files[].path` is
**spec-target-relative**, not project-root-relative, because the wrapper joins
`spec_target / path`. So a project-root spelling
(`.livespec-fleet-manifest.jsonc`) is the spelling that FAILS — it would join to
`SPECIFICATION/.livespec-fleet-manifest.jsonc`, which is not a file. The two
required literal values, following the established `../tests/heading-coverage.json`
precedent, are:

- `../.livespec-fleet-manifest.jsonc`
- `../.claude/skills/needs-attention-fleet/SKILL.md`

A wrong spelling fails CLOSED rather than mis-applying — the require-existing-target
check raises `PreconditionError` (exit 3) before any write, leaving the spec tree
byte-identical — but it costs a ratification round, so get it right the first time.

1. `.livespec-fleet-manifest.jsonc` — the manifest's own header comment
   enumerates the closed set. This is the very artifact the amended paragraph
   defines, so leaving it stale is precisely the drift livespec exists to
   catch. The comment MUST be amended:

```diff
-// `fleet` entries are { repo, class } where `class` is one of:
-// core / enforcement-suite / impl-plugin / driver-plugin / library / console.
+// `fleet` entries are { repo, class } where `class` is one of:
+// core / enforcement-suite / impl-plugin / driver-plugin / library / console /
+// control-plane-tool.
```

2. `.claude/skills/needs-attention-fleet/SKILL.md` — carries the same stale
   closed-set enumeration. It is a LOCAL-ONLY, unsynced maintainer skill and is
   behaviorally class-independent, so the stakes are lower, but it is still a
   contradicting statement and MUST be amended:

```diff
-- **`fleet`** — `{repo, class}` entries (core / enforcement-suite / impl-plugin /
-  driver-plugin / library / console). These contribute product `needs-attention`
+- **`fleet`** — `{repo, class}` entries (core / enforcement-suite / impl-plugin /
+  driver-plugin / library / console / control-plane-tool). These contribute product `needs-attention`
```

Neither co-edit is premature relative to the implementation ordering below: a
JSONC comment is stripped before parsing and the SKILL.md line is prose, so
neither is read by any validator and neither can break while
`livespec-dev-tooling` still lacks the class value.

### ⚠️ Ratification ordering constraint — the failure mode is TOTAL, not soft

`livespec-dev-tooling`'s `contract.py` `_parse_member` rejects any entry whose
`class` is absent from `REPO_CLASSES`, and `_parse_members` returns `None` for
the WHOLE array on a single bad entry. So if
`.livespec-fleet-manifest.jsonc` ever REGISTERS a member with
`"class": "control-plane-tool"` before dev-tooling's `REPO_CLASSES` change has
merged AND been RELEASED — fleet pins track releases, not master — the entire
manifest becomes unparseable and every manifest consumer breaks at once:
`fleet_conformance`, the merged-branch sweep, `wire-fleet-member`, and the
release fan-out workflow.

(An earlier revision of this sentence also named `ensure-plugins`. That was
WRONG and is corrected here: `ensure_plugins.py` derives its plugin set from the
invoking repo's `.claude/settings.json` — its own docstring calls that "the
single source of truth" — and never reads the fleet manifest at all.)

The strict order therefore MUST be: (1) ratify this spec change; (2) land and
RELEASE the `REPO_CLASSES` addition in `livespec-dev-tooling`; (3) only then
register `livespec-overseer` in the manifest. This proposal registers no
member and so cannot itself trigger the failure, but whoever carries the
dev-tooling work-item MUST carry this ordering with it.

Two deliberate non-changes, recorded so a later reader does not read them as omissions:

1. The pin-and-bump consequence MUST NOT be restated normatively in core. `livespec-dev-tooling`'s `contracts.md` §"Bump-pin policy" defines the non-pin-consuming-member carve-out and names `console` as its first and only member; a class absent from that carve-out is a pin-and-bump consumer by construction. Duplicating the rule in core would create two sources of truth for one policy.

2. No `## ` heading is added, renamed, or removed by this change — it amends prose inside the existing §"Fleet membership contract" section — so `tests/heading-coverage.json` requires NO co-edit under `spec.md` §"Self-application". A reviewer SHOULD verify this rather than assume it.

The paired implementation change is OUT OF SCOPE for this proposal and MUST land separately in `livespec-dev-tooling`: adding `control-plane-tool` to that repo's `REPO_CLASSES` tuple. No partition rework is required there, because both `_PIN_WEB_CLASSES` and `_DEV_TOOLING_PIN_CLASSES` are subtraction sets over the full class set and so admit a newly-added class automatically. Independent review confirmed that the one ADDITIVE set, `_TEMPLATE_BORN_CLASSES`, is `frozenset({"impl-plugin"})`, so the new class is correctly excluded from the template-born rows automatically as well.

### Noted, deliberately NOT changed here

`spec.md`'s three-plane definition glosses the Control Plane as "the operator
console; reference: `livespec-console-*`". A `control-plane-tool` member such as
`livespec-overseer` matches neither that gloss nor that wildcard. This is NOT a
flat contradiction — the parenthetical is a role gloss plus a reference
implementation, not a closed membership enumeration — so amending it is not
required for this change to be coherent, and bundling a `spec.md` plane-model
edit into a fleet-membership amendment would widen this proposal's blast radius
past its topic.

**The eventual follow-up is BIGGER than that one gloss**, and a later reader
MUST NOT scope it to the parenthetical alone. Independent review found the
sharper contradiction is `spec.md`'s statement that the Control Plane runs "a
**single operator interface**", plus the `CONTROL PLANE: operator console`
Mermaid subgraph labels — all of which read as console-only once a second,
non-console Control-Plane member exists. `tests/test_workflow_planes_terminology.py`
scopes to the planes section and those Mermaid labels, so the follow-up MUST
re-check it. This SHOULD be revisited as its own proposal once the
`livespec-overseer` repo is registered; it is ALSO recorded in
`plan/overseer-productization/handoff.md`, because this file becomes a frozen
`history/` record at ratification and would otherwise carry the only copy.
