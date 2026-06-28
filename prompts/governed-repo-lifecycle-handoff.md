# Handoff: governed-repo lifecycle (livespec-zs22.8)

**Track:** governed-repo lifecycle · **Ledger:** livespec **`zs22.8`**
(Increment 6; **sibling of the Conformance Pattern `zs22.7`**, under
parent `zs22`). The drift-check half is a SUPERSET that includes
conformance. This file carries durable *design + plan*; the
*authoritative status* lives in the ledger, never here.

## ROLE GATE — read this BEFORE anything else

**If your session is the OVERSEER** (its name contains `overseer`, or you were
launched via the `overseer` skill): **STOP — do NOT run this inline.** This file
is a *track to dispatch*, not a runbook for you to execute. Your only actions are
(a) dispatch this prompt into a dedicated `livespecN` **worker** session and (b)
watch that worker via the three-pane monitor. The overseer NEVER does this
track's work itself (no product edits, no `just check`, no TDD/Red-Green commits,
no track worktrees/PRs) — see `.claude/skills/overseer/SKILL.md` §"STEP 0". The
ONE exception is fixing THIS prompt's orchestration apparatus (e.g. this gate),
which the overseer may land doc-only.

**Only proceed past this gate if you ARE the dedicated worker session** assigned
to drive the `zs22.8` track. The rest of this file is written second-person to
that worker.

---

**M1 + M2 are DONE; this file now drives M3 → M6 AUTONOMOUSLY** (the
maintainer delegated the cut 2026-06-28). The OVERSEER dispatches this into a
dedicated worker session; **that worker — not the overseer — executes M3 → M6**
(see §"Autonomous execution plan — M3 → M6" below).

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

## Autonomous execution plan — M3 → M6 (drive this track to completion)

**Status (verify via FIRST ACTION; do not trust this line):** M1
(`zs22.8.1`, unified entry point specified) and M2 (`zs22.8.2`, the local
first-touch reconcile verb + core `just bootstrap` delegation) are **DONE +
merged**. The verb lives in `livespec-dev-tooling`
`livespec_dev_tooling/fleet/local_reconcile.py` (+ `_rows_local.py`,
`_local_context.py`, `contract.py`), shipped in **dt v0.29.0**; core's `just
bootstrap` runs `uv run python -m livespec_dev_tooling.fleet.local_reconcile`.
**Remaining: M3 → M6.**

**Mandate (maintainer-delegated 2026-06-28):** the maintainer has handed the
M3–M6 cut to **autonomous execution** — the earlier "human owns the cut" gate is
LIFTED for these milestones. Run M3 → M6 as ONE cross-repo epic. **File each
child** (`zs22.8.3` … `zs22.8.6`) under epic `zs22.8` via `capture-work-item` as
it ripens, implement it, and proceed — no per-cut gate. Decide-and-inform;
surface only the genuine gates listed at the end.

**M3 — `.livespec.jsonc` generate/complete + close the vacuous-pass hole.**
- Extend the verb so reconcile GUARANTEES a complete `.livespec.jsonc`: ensure
  `harnesses` is present; fill `connection` from the env wrapper, or emit a
  `manual_hint` TODO when it can't be derived (never fabricate it).
- Close the hole: add the assert-side guard that **a governed member (in the
  fleet manifest) with no / incomplete `.livespec.jsonc` is a FINDING**, not a
  vacuous pass (`plugin_resolution.py:322-324, 426-428`).
- **Confirmed decision — guard rollout:** land the new finding **WARN-FIRST**
  (the established per-check env warn/fail lever), **backfill every fleet
  member's `.livespec.jsonc`** so each is complete, THEN flip the guard to
  hard-fail. Never let it red fleet CI before the configs exist (a required-key
  change is itself a cross-repo backfill epic — see CLAUDE.md).
- Acceptance: verb fills/guards config; guard flipped to fail with all fleet
  configs complete; `just check` green fleet-wide.

**M4 — beads-runtime detect-and-guide rows.** Add obligation rows that PROBE the
ledger backend — the `bd` binary (`$LIVESPEC_BD_PATH`), the Dolt server
(`127.0.0.1:3307`), the tenant secret (`BEADS_DOLT_PASSWORD`, presence only), and
the `.beads/` pointers (`config.yaml` committed, `metadata.json` regenerable) —
emitting a `manual_hint` per unmet seam. Secrets stay **probe-only** (`printenv
NAME | wc -c`, never echo). Additive rows in `contract.py`; no new mechanism.

**M5 — fleet dogfood + the deferred fleet-wide bootstrap rewire.** Rewire every
fleet member's `just bootstrap` to the thin delegator (the M2 pattern, now
fanned out — one PR per repo, pin bump, `just check` green each), then run the
unified verb end-to-end against a fleet member: set one up from a fresh clone,
and verify drift-detection on an already-configured one.

**M6 — adopter dogfood (disposable scratch repo).**
- **Confirmed decision:** create a **DISPOSABLE scratch repo** (not a real
  adopter), onboard it from config-less to fully set-up via the verb, verify
  drift-detection, confirm the vacuous-pass hole is closed for a non-fleet repo,
  then **DELETE the scratch repo**.
- **Confirmed decision — beads for the dogfood:** do NOT provision a new tenant.
  **Reuse an existing fleet repo's tenant auth/connection** (the existing
  `/data/projects/1password-env-wrapper/with-livespec-env.sh` wrapper) to run the
  test. The scratch repo gets its own beads `project_id` in that tenant, so every
  item the dogfood creates is scoped to it; after the test **PURGE every test
  item** and **verify the tenant's real-item set is unchanged** (capture a
  count + id list before and after; confirm only the scratch project_id's items
  were added and removed). Secrets probe-only throughout.

**Sequencing:** M3 → M4 → M5 → M6. dev-tooling changes cut a dt release; core +
every fleet repo's pin bumps to it; `just check` stays green in EVERY touched
repo within this one epic (no "follow-up in another session").

**Surface only these (else decide-and-inform):**
- A genuinely NEW host/secret mutation BEYOND the pre-authorized test-reuse
  (e.g. creating a real new beads tenant, rotating a secret).
- Pushing/force-pushing to any repo/branch this session did NOT create (the
  scratch repo it creates for M6 is fine; deleting that scratch repo is fine).
- A real product/architecture fork not covered by the locked framing above.

Hand off at ~50% context by refreshing THIS file to the then-current state and
landing it via the worktree → PR → merge flow.

**Close-out:** when M3–M6 land, dogfood is green, and the vacuous-pass hole is
closed, close `zs22.8.3…6` and the epic `zs22.8`, then archive this file (see
**Archive condition**). **Report:** reply `DONE` with the merged PRs + closed
epic, or `BLOCKED <one-line diagnosis>` on a genuine blocker.

## Resolved design decisions (were open at M0; now locked)

- **Verb home — RESOLVED:** `livespec-dev-tooling`, beside `wire_fleet_member`
  (extends the same `contract.py` table); thin `just` delegators per repo. Built
  in M2.
- **Local vs. central vantage — RESOLVED:** single-vantage **LOCAL** rows run in
  the checkout (`_rows_local.py`); central rows (secrets, branch protection,
  topic, shim PRs) stay in `wire_fleet_member`. No row needs both.
- **Adopter not-yet-in-manifest — RESOLVED (for the dogfood):** M6 uses a
  disposable scratch repo created + onboarded + deleted by this track;
  registration of a real adopter remains a deliberate human-gated step outside
  this epic.

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
