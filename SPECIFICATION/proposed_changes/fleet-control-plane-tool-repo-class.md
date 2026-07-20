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

The livespec overseer is moving out of livespec core into its own dedicated repo, `livespec-overseer`, registered under the manifest's `fleet` array as a full member (maintainer ruling, 2026-07-20). An earlier ruling in the same thread established that the overseer is a Control-Plane artifact, so its class must be a Control-Plane one. The existing `console` class cannot be reused. `livespec-dev-tooling`'s `_contract_rows.py` defines `_PIN_WEB_CLASSES` as a SUBTRACTION set — every class except `console` — so classing the overseer as `console` would either deny it the automatic bump-pin PRs it needs, or, if that subtraction were rewritten to admit it, drag the pure-Rust `livespec-console-beads-fabro` into the bump web alongside it. The overseer specifically needs auto-bump because its ruff, pyright-strict, coverage, and Result-railway gates all come FROM `livespec-dev-tooling`, so a dev-tooling release directly determines whether its repo stays green — precisely the case auto-bump exists to serve, and precisely the case the console's exemption was designed to avoid for a repo that consumes dev-tooling for only three thin Python checks. None of the five existing pin-consuming classes fits either: the overseer ships an operator tool, so it is not a `library`, and it is neither a plugin nor the `enforcement-suite`. Core is the correct and only spec surface for this change: core's §"Fleet membership contract" states that livespec core owns fleet-level facts, and `livespec-dev-tooling`'s own SPECIFICATION does not enumerate the classes at all — its `contracts.md` mentions `console` solely in the non-pin-consuming-member context.

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

Two deliberate non-changes, recorded so a later reader does not read them as omissions:

1. The pin-and-bump consequence MUST NOT be restated normatively in core. `livespec-dev-tooling`'s `contracts.md` §"Bump-pin policy" defines the non-pin-consuming-member carve-out and names `console` as its first and only member; a class absent from that carve-out is a pin-and-bump consumer by construction. Duplicating the rule in core would create two sources of truth for one policy.

2. No `## ` heading is added, renamed, or removed by this change — it amends prose inside the existing §"Fleet membership contract" section — so `tests/heading-coverage.json` requires NO co-edit under `spec.md` §"Self-application". A reviewer SHOULD verify this rather than assume it.

The paired implementation change is OUT OF SCOPE for this proposal and MUST land separately in `livespec-dev-tooling`: adding `control-plane-tool` to that repo's `REPO_CLASSES` tuple. No partition rework is required there, because both `_PIN_WEB_CLASSES` and `_DEV_TOOLING_PIN_CLASSES` are subtraction sets over the full class set and so admit a newly-added class automatically.
