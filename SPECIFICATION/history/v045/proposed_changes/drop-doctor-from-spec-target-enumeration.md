---
topic: drop-doctor-from-spec-target-enumeration
author: livespec-bootstrap-phase12
created_at: 2026-05-06T17:18:25Z
---

## Proposal: drop-doctor-from-spec-target-enumeration

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The prose paragraph in §"Sub-spec structural mechanism" enumerates four sub-commands as accepting `--spec-target`, but the wrapper-CLI table earlier in the same file lists `--spec-target` only on `propose-change`, `critique`, and `revise`; the `doctor (static)` row carries only `--project-root`. The prose enumeration is wrong and contradicts the table directly above it. Drop `doctor` from the prose enumeration so it agrees with the table and with the shipped `bin/doctor_static.py` impl.

### Motivation

Bootstrap residue closure (decisions.md 2026-05-04T23:30:00Z capture-for-revisit). The drift was discovered during Phase 7 sub-step 6.a's cascading-impact scan but deferred at the time per the one-finding-per-gate discipline. Phase 12.1 closes it via a dogfooded propose-change/revise cycle.

### Proposed Changes

In `SPECIFICATION/contracts.md`, the prose paragraph currently reading

  > The `propose-change`, `revise`, `critique`, and `doctor` sub-commands all accept `--spec-target <path>` to scope their operation to one specific spec tree. `--spec-target <project-root>/SPECIFICATION/templates/livespec/` targets the `livespec` template's sub-spec; `--spec-target <project-root>/SPECIFICATION/` targets the main spec; etc.

becomes:

  > The `propose-change`, `revise`, and `critique` sub-commands accept `--spec-target <path>` to scope their operation to one specific spec tree. `--spec-target <project-root>/SPECIFICATION/templates/livespec/` targets the `livespec` template's sub-spec; `--spec-target <project-root>/SPECIFICATION/` targets the main spec; etc. The `doctor` sub-command takes only `--project-root`; its multi-tree enumeration is internal (see §"Per-sub-spec doctor parameterization").
