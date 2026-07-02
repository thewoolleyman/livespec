# Handoff — github-app-auth

The single resumable entry point for the **fleet GitHub App-token auth**
coordination epic. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** The coordination anchor for standardizing the fleet on
  GitHub **App installation tokens** for ALL automated GitHub operations —
  factory dispatch AND standalone agent worktree commits — **retiring the fleet
  PAT** (`LIVESPEC_FAMILY_GITHUB_TOKEN`) and **removing the human OAuth token
  from the agent path**. See `research/01-design.md` for the why + the four
  pillars.
- **Epic anchor:** `livespec-2ef0` (core tenant). GROOMED 2026-07-02 into
  dependency-layered slices (ids below). Status is READ from the ledger, never
  from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-2ef0
  ```
- **Groomed slice ids (cite read-only; status lives in the ledger).**
  - `livespec-gwjnes` (core, filed `ready`) — impl-plugin template
    `github-auth-guard` hook + core test.
  - `livespec-u67wdb` (**livespec-runtime tenant**, `backlog`) — the App-token
    provider + git credential helper primitive (first-class remint; Pillar 1).
    Read: `bd -C /data/projects/livespec-runtime show livespec-u67wdb`.
  - `livespec-in7snc` (**livespec-orchestrator-beads-fabro tenant**, `backlog`)
    — factory dispatch routes GitHub auth via target `credential_wrapper` →
    provider; retires the fleet-PAT export. Supersedes-edge to `bd-ib-gsl`
    (absorbed; closes when this lands). Blocked by `livespec-u67wdb` (sibling
    dep). Read: `bd -C /data/projects/livespec-orchestrator-beads-fabro show livespec-in7snc`.
  - Epic children (core, `backlog`, maintainer-gated — deliberately NOT
    `ready` so the Dispatcher never drains them): `livespec-orslcm` (standalone
    agent-context wiring, Pillar 3), `livespec-uotocj` (retire the fleet PAT +
    restrict fleet App install scope; superseded `bd-ib-p2e` is CLOSED),
    `livespec-p3icf6` (openbrain adopter dogfood, Pillar 2; folds
    fleet-followups C16, gated on its D17 decision).
- **Spec side.** The groom's spec-change slice is FILED as a pending proposed
  change: `SPECIFICATION/proposed_changes/github-app-token-standardization.md`
  (extends non-functional-requirements §"Fleet secrets" with the GitHub
  automation-credential rule).
- **Working model.** This is a **CORE coordination thread** — resume it from a
  core session. The code slices are **cross-tenant**: each is admitted + built
  from ITS OWN repo's session (livespec-runtime, then beads-fabro). Factory
  changes are careful **self-modifications** — human-approved admission, never
  auto-dispatch blind.
- **⚑ Golden rule.** FILE + GROOM ripe work; DISPATCH ready, factory-safe slices
  through the factory under the janitor gate; NEVER hand-code inline. Every repo
  change is worktree→PR→merge, never `--no-verify`.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan github-app-auth`.

## The next action

**Process the pending proposed change** (spec leads, impl follows) from a core
session:

```
/livespec:revise
```

Accepting `github-app-token-standardization` lands the fleet
automation-credential contract the impl slices build against. After the revise
pass, the parallel fronts (status from the ledger, per-tenant sessions): admit
+ build `livespec-u67wdb` (livespec-runtime — the critical-path primitive),
then `livespec-in7snc` (beads-fabro), while the Dispatcher may drain
`livespec-gwjnes` (core, `ready`); the maintainer-gated children follow their
dependency edges.

## Read-first chain (in order)

1. `research/01-design.md` — the why, the decision, the research basis, the four
   pillars + mechanics, and open questions. The only companion; everything else
   needed is in this handoff.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan github-app-auth
```
