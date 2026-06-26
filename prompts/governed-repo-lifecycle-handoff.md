# Handoff: governed-repo lifecycle (livespec-zs22.8)

**Track:** governed-repo lifecycle · **Ledger:** livespec **`zs22.8`**
(Increment 6; **sibling of the Conformance Pattern `zs22.7`**, under
parent `zs22`). The drift-check half is a SUPERSET that includes
conformance. This file carries durable *design + plan*; the
*authoritative status* lives in the ledger, never here.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.8
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.7
```

Derive "what's done / what's next" from that plus `git log`. **No shadow
ledger** — if any child (`zs22.8.*`) has been filed, the ledger is
authoritative for which milestones exist and their status, not the
"Milestone sketch" in the design doc.

## Read first

1. This file (the plan + next action, below).
2. `research/governed-repo-lifecycle/lifecycle-system-design.md` — the
   **durable design**: the gap, the two-mode framing (setup=reconcile /
   drift=assert), the current-scatter table, the locked framing, the
   reuse-vs-add delta, and the **Milestone sketch** (M0–M6) this track
   files children from.
3. `research/factory-conformance/cross-repo-conformance-pattern.md` —
   the Conformance Pattern (`zs22.7`), the five-slot anatomy, the
   `baseline` profile, and the **DELIVERY RULE** ("reuse by default,
   pin+import, no copies") this track is bound by.
4. In the **`livespec-dev-tooling` sibling repo**, the two-mode spine to
   reuse (do NOT re-implement):
   `livespec_dev_tooling/fleet/wire_fleet_member.py` (idempotent
   **reconcile** mode — "assert mode is CI; reconcile mode is wiring"),
   `livespec_dev_tooling/fleet/fleet_conformance.py` (**assert** mode —
   the CI sweep), and `livespec_dev_tooling/fleet/contract.py` (the one
   shared `OBLIGATION_ROWS` + `PROFILE_LAYERS` both walk).
5. `research/planning-workflow-gap/planning-lane-design.md` — the
   Planning Lane this track files milestones through, and the
   three-plane model.

## The problem (why this exists)

livespec can **check** whether a governed repo conforms (`zs22.7`, just
completed) but has nothing that **sets one up** or **keeps it set up**.
"Onboarding" is an undefined manual step, and the safety net has a hole:
the plugin-resolution Verifier *skips* a repo with no `.livespec.jsonc`
at all, so a config-less repo passes vacuously even after the M6-g
required-key flip (`plugin_resolution.py:322-324, 426-428`). Setup is
scattered across `just bootstrap` (this-repo-only), the copier template
(new-repos-only, ships `harnesses` stub but omits `connection`),
`wire_fleet_member` (central, fleet-members-only), the manual install
docs, and the manual beads runtime prereqs — none of which compose into
one idempotent "set up OR verify any governed repo" entry point.

The key reuse insight (read item 4 above): the conformance machinery
**already** has the two-mode shape — `wire_fleet_member` (reconcile) and
`fleet_conformance` (assert) walk the **same** obligation table, and
reconcile already detect-and-guides (`manual_hint` per unmet row) and
handles secrets safely (env→stdin, values never logged). This track is
the idempotent orchestrating layer over that pair, **extended** to the
setup dimensions outside it (local first-touch, `.livespec.jsonc`
generation incl. `connection`, beads-runtime guidance), closing the
vacuous-pass hole by guaranteeing a `harnesses`-bearing config exists.

## Locked framing (maintainer-approved — hold these)

1. **ONE idempotent command**, the generalized successor to `just
   bootstrap`, with setup + verify/drift modes (or one run that
   reports+repairs). `bootstrap` becomes its this-repo special case.
2. **Sit beside and REUSE the Conformance Pattern machinery** (manifest,
   `baseline` profile, `OBLIGATION_ROWS`, `wire_fleet_member`,
   `fleet_conformance`, `manual_hint`) — do NOT re-implement; add setup
   dimensions as new obligation rows / reconcile references.
3. **Human seams (secrets, tenant DB connection) — detect-and-guide with
   actionable TODOs, never fake.** Reuse the `manual_hint` seam; secrets
   stay probe-only (`printenv NAME | wc -c`, never echo).
4. **Surface: a runnable script + a `just` target** — host-mutation +
   install, NOT spec-side prose; never enters core's functional spec or
   the `/livespec:*` surface; callable by the conformance reporting.

## Next concrete action

The track is at **M0** (this PR landed: the design doc, this handoff,
and the `zs22.8` epic anchor). The next action is maintainer-gated
because **the human owns the milestone cut**:

> With the maintainer, lock the **M0–M6 decomposition** in the design
> doc's §"Milestone sketch" (adjust as directed), then file the first
> ripe child — **M1: specify the unified entry point** — under epic
> `zs22.8` via the `capture-work-item` operation, and begin M1 as a
> `/livespec:propose-change` into `non-functional-requirements.md`.

Likely follow-on: **groom `zs22.8`** into the per-milestone slices once
the cut is locked. Do NOT file children before the maintainer approves
the cut.

## Open design questions (decide early — see design doc §"Open questions")

- **Where the unified verb lives** — beside `wire_fleet_member` in
  `livespec-dev-tooling` (extends the same table) with thin `just`
  delegators per repo, vs. core. Gated on the `baseline`-tooling
  extraction sequencing.
- **Local setup vs. central wiring vantage** — `wire_fleet_member` works
  from a central GitHub vantage; first-touch local setup is in-checkout.
  Confirm the local/central row split (no row needs both).
- **Adopter not-yet-in-manifest** — `wire_fleet_member` exits 1 if
  `--repo` is not a declared member. Decide register-then-wire in one
  pass vs. registration as a deliberate human-gated first step.

## Constraints / non-negotiables

- **Reuse-first, no copies.** Extend `contract.py`'s obligation table and
  the reconcile/assert pair; never fork a parallel mechanism (the
  Conformance Pattern's DELIVERY RULE).
- **Never fake a human seam.** A missing secret / connection / runtime
  prereq is a surfaced `manual_hint`, never a placeholder value. Secrets
  are probe-only.
- **The surface is non-functional tooling**, not core's functional spec
  or the `/livespec:*` skills (the same boundary as the `just`-keystone
  mandate).
- **Dogfood the discipline.** All work in `~/.worktrees/<repo>/<branch>`;
  worktree → PR → rebase-merge; never commit on a primary checkout;
  `mise exec -- git …`; never `--no-verify`; halt and report on any hook
  failure.
- **Shared-artifact change = one cross-repo epic.** Moving anything into
  `livespec-dev-tooling` bumps every consumer's pin and keeps `just
  check` green fleet-wide in the SAME epic.
- **Pins track the latest RELEASE, not master** (zs22 locked decision).
- **No shadow ledger.** Status comes from the FIRST ACTION query.

## Archive condition

When `zs22.8` closes (the unified lifecycle verb exists; setup + drift
modes dogfooded on a fleet member AND an existing adopter; the
vacuous-pass hole closed), `git mv` this file to `archive/prompts/` with
a completion banner. Durable history then lives in the spec, the
commits, and the ledger.
