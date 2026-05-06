---
topic: live-spec-self-containment-archive-refs-removed
author: livespec-bootstrap-phase12
created_at: 2026-05-06T18:26:08Z
---

## Proposal: live-spec-self-containment-archive-refs-removed

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md

### Summary

Removes the six brainstorming/bootstrap path references from the live SPECIFICATION/ tree (5 in spec.md, 1 in constraints.md) per the LIVESPEC self-containment principle. After Phase 12 archives bootstrap/ and brainstorming/, those paths no longer exist at repo root, so any reference to them from the live spec is broken; the spec must stand on its own as the authoritative live oracle. Each removed reference's substantive content is already captured in adjacent spec prose (non-goals enumeration, lifecycle diagram, prior-art citations, subdomain-routing conclusion); this revise drops the external pointers without losing intent.

### Motivation

Bootstrap residue closure (Phase 12.7). Closes the original-issue: production-permanent files must contain no references to archive-bound content. The live spec is the central case — LIVESPEC's whole purpose is the self-contained living specification.

### Proposed Changes

Five edits in `SPECIFICATION/spec.md`:

1. Drop the entire genesis paragraph at line 9 ("The seeded `SPECIFICATION/` tree at this revision (v001) derives from the brainstorming archive at..."). The Phase 8 migration is done; the spec body that follows IS the canonical post-migration content.

2. In §"Non-goals" (line 174), drop the trailing sentence " See the seeded `goals-and-non-goals` material...and the deferred-items archive at `brainstorming/.../deferred-items.md` for the long-form non-goal rationale." The non-goals enumeration immediately below IS the spec-level statement.

3. In §"Lifecycle" (line 190), drop the trailing sentence " The following diagram and terminology summary are archived from the brainstorming phase in `brainstorming/.../`; this section is the living-spec record." The diagram + terminology IS in this section as the living-spec record.

4. In §"Prior Art" (line 232), drop the trailing sentence " Each entry is archived in full at `brainstorming/.../prior-art.md`; this section records the key citation and its design relevance." The prior-art section below records the key citations directly.

5. In §"Subdomain routing" (line 255), drop the entire trailing paragraph "The brainstorming analysis in `brainstorming/.../subdomains-and-unsolved-routing.md` is preserved for context; its conclusion is that this is a genuine open problem in spec-governance tooling, not a limitation unique to `livespec`." The conclusion is already stated in the spec section above.

One edit in `SPECIFICATION/constraints.md`:

6. In §"Self-application bootstrap exception" (line 656), drop the trailing paragraph "The bootstrap scaffolding under `bootstrap/` is removed at Phase 11 per the plan; once removed, this constraint operates without the bootstrap-window carve-out." Bootstrap is permanently closed (Phase 11 + Phase 12); the carve-out is permanently retired.
