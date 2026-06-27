---
topic: console-fleet-repo-class
author: claude-opus-4-8
created_at: 2026-06-27T01:48:07Z
---

## Proposal: Add the console repo class to the fleet-membership class enumeration

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add `console` to the repo-class enumeration in §"Fleet membership contract" (the `Fleet manifest.` rule), so the Control-Plane operator console (livespec-console-beads-fabro) is a recognized fleet repo class. The class enumeration is the core-owned spec prose; the per-class obligation table that scopes the console as a non-pin-consuming member lives in livespec-dev-tooling's contracts.md §"Bump-pin policy".

### Motivation

Registering livespec-console-beads-fabro in the fleet manifest (livespec-zs22.7.8) requires the `console` class to be a recognized member of the core-owned class enumeration. Core already records the Control-Plane console architecturally in §"Control-Plane console guidance" and §"Obligations per repo class" already scopes shim-workflow obligations to `pin-consuming classes` (which correctly excludes the console); this change closes the gap by naming `console` in the class enumeration itself.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md §"Fleet membership contract", the `Fleet manifest.` rule, extend the repo-class enumeration `(core / enforcement-suite / impl-plugin / driver-plugin / library)` to `(core / enforcement-suite / impl-plugin / driver-plugin / library / console)`. No other prose changes: §"Obligations per repo class" already scopes the shim-workflow obligations to `pin-consuming classes`, which the non-pin-consuming console is correctly outside; the dev-tooling-pin obligation correctly applies (the console carries a [tool.uv.sources] pin); copier-answers applies only to template-born classes, which the console is not.
