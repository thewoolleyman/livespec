# Charter — rop-railway-enforcement (livespec)

Opened 2026-09-12 at the maintainer's direction. This is the livespec realization of the
fleet ROP (Result-Oriented-Programming) railway enforcement campaign. The MAINTAINER drives
this plan directly, per-repo; it is NOT driven by the livespec-dev-tooling backlog drain.

## What this plan owns

Arm the ROP result-typed railway (`check-public-api-result-typed` / the railway conversion)
in this repository, converting this repo's off-railway public-API functions to the
Result/IOResult railway and arming the check in `just check` + CI.

- **This repo's scope, as of the coordinating campaign:** 15 off railway (universe 132).
- **Coordinating campaign (authoritative ledger):** livespec-dev-tooling epic
  `livespec-dev-tooling-8o8e`, arming child `livespec-dev-tooling-8o8e.12` for this repo.
  Read that epic's timeline and the `plan/rop-railway-enforcement/research/` directory in
  the livespec-dev-tooling checkout for the fleet method, the offender inventory, and the
  `8zv3.5`/clause-(c) basis question (does the railway reach FLAT-layout pure functions or
  only a designated `pure_trees` subtree).

## The standing sequencing constraint

**Adoption BEFORE arming.** The fleet decoupling once armed the check ahead of adoption
(`46c5dab`), reddened five repos, and was reverted (`f4247110`). Convert this repo's
offenders to the railway FIRST; arm the check only once this repo is at zero offenders on
the chosen basis.

## Status

Freshly opened scaffold. Re-derive the offender count for this repo before acting (the
counts drift; quote every figure with its date). Work through this repo's own factory
(Red -> Green), never a hand PR for product `.py`.
