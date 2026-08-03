---
topic: fleet-shell-discipline-corrections
author: codex
created_at: 2026-08-03T00:56:17Z
---

## Proposal: Bind shell discipline scope and CI inventory source

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Correct two post-ratification ambiguities in the fleet shell-discipline policy: bind the Conformance Pattern member to an explicit fleet/adopter profile scope, and make CI matrix completeness compare against the tracked static check-target inventory reached by the one-line `just check` recipe instead of inferring an aggregate from that recipe body.

### Motivation

An independent Fable review of the exact ratified proposal found that the current `ci_matrix_completeness` wording becomes vacuous once `check:` is a one-line runner invocation, and that the registry member does not explicitly state how its baseline obligation reaches fleet members and opted-in adopters. The maintainer authorized these post-ratification corrections and required them to pass through the normal propose-change/revise lifecycle.

### Proposed Changes

Amend `SPECIFICATION/non-functional-requirements.md` without adding or renaming an H2 heading. In `Conformance Pattern`, define `Shell-and-Justfile-discipline` as a `baseline` concern binding every fleet repository and, mirroring Pin-freshness and Plugin-currency, extending to opted-in adopters through their `posture`, bound where an adopter's posture is `released`. Preserve the existing five-slot reference to `Shell and Justfile discipline`. In `CI as a merge gate (branch protection)`, replace the `ci_matrix_completeness` source-of-truth clause so that CI's canonical `just check` slugs MUST be a superset of the tracked static check-target inventory reached by the one-line `just check` recipe, excluding the declared pre-push-only world-gate checks. The check MUST NOT infer the inventory from the one-line recipe body. Preserve the independent requirement that the gate job's `needs:` covers every gating job. These are scope and verifier-source corrections to the ratified behavior; they create no new H2 and require no heading-coverage co-edit.
