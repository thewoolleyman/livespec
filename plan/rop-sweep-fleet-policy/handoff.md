# rop-sweep-fleet-policy — audit ROP enforcement fleet-wide, set the BLE policy, fix the scaffold drift

**Part of the `rop-sweep-*` coordinated set (do these ASAP, together).** Sibling
plans, findable fleet-wide via `plan/rop-sweep-*`:
- **`rop-sweep-consumer-cleanup`** (in `livespec-orchestrator-beads-fabro`) — the
  drifted consumer's local catch-up.
- **`rop-sweep-library-checks`** (in `livespec-dev-tooling`) — config-drive the 6
  scope-hardcoded checks + add a drift-guardrail check.

**Not started — a drafted plan for a fresh session.** Authored 2026-07-16. This is
the `livespec` core slice: the fleet-universal concerns that are neither one
consumer's cleanup nor the shared check code — the discipline text, the
enforcement audit across all consumers, the lint policy, and the scaffold fix that
**prevents** the drift the other two plans clean up and detect.

---

## Why a core slice exists

The trigger was one consumer's blind-except bulkheads, and the mechanical fixes
split cleanly into "this consumer" (`rop-sweep-consumer-cleanup`) and "the shared
check library" (`rop-sweep-library-checks`). What is left is genuinely
fleet-universal and lives in core:

1. **The discipline is core's** — `SPECIFICATION/constraints.md` already mandates
   the `returns` railway (`:65` lists `Result`/`IOResult`/`@safe`/`@impure_safe`/
   `bind`/`lash`; `:147` "Everywhere else stays on the railway"; `:34` "the railway
   requires unconditional importability"). But the *observability* half of the
   rule — the part this whole thread turned on — is not written down anywhere
   normative.
2. **No one has audited whether every consumer actually enforces it.** I deeply
   audited only `beads-fabro`. The same dormancy could exist elsewhere.
3. **The drift is preventable at scaffold time** — and prevention belongs in core's
   consumer template, not in any single consumer.

---

## Part A — audit ROP enforcement across every consumer

Known state (verified for three repos; the rest need the same pass):

| Repo | `except Exception` | `source_trees` scope | `returns` vendored | Verdict |
| --- | --- | --- | --- | --- |
| `livespec` (core) | 0 | correct (own pkg) | yes, used | full railway — the reference |
| `livespec-orchestrator-git-jsonl` | 0 | correct (own pkg) | **no** | clean of blind-catches, but **not** on the railway (lighter convention) |
| `livespec-orchestrator-beads-fabro` | 10 files / 13 sites | ✗ core's `livespec` | no | drifted — `rop-sweep-consumer-cleanup` |
| `livespec-console-beads-fabro` | — | no scripts package yet | — | N/A until it has one (must scaffold correctly) |

**Action:** run the beads-fabro-style dormancy audit against **every** consumer
(git-jsonl, console, and any others), producing a per-repo list of DORMANT /
WARN-only / correctly-enforced checks. git-jsonl is the important case: its config
is correct, yet it has not vendored `returns`, so it may be satisfying
"no blind catch" without being on the railway at all — decide whether the fleet
target is "no `except Exception`" (met) or "full ROP with `returns`" (not met).
That decision sets the bar for every consumer.

---

## Part B — write the observability rule into the spec

The corrected guidance from this thread must become normative, not live only in a
plan. Add to `SPECIFICATION/constraints.md` (or non-functional-requirements) the
observability rule:

- Observability/side-effects are `.map(tap(effect))` pass-through steps.
- **Unexpected** failures propagate to the supervisor; "the call can throw" is
  never itself a reason to catch (everything can throw). Only a **named, expected**
  failure a path deliberately tolerates rides the railway, via a **narrowed**
  `@impure_safe(exceptions=(…))` — never a blanket lift.
- A critical downstream step is protected from an observability failure by
  **ordering** (commit before the tap), not by catching.

This is the rule that distinguishes ROP-done-right from a relocated bulkhead; core
is where it becomes binding on the whole fleet.

---

## Part C — the lint / type policy (belt-and-suspenders)

- **Ruff `BLE` (flake8-blind-except) is off in all three repos checked.** Even
  where `no_except_outside_io` bans `try/except` structurally, `BLE001` is a
  cheap, direct ban on the exact `except Exception` construct. Decide whether the
  shared config the consumer template emits should `select` `"BLE"` fleet-wide.
- **`reportUnusedCallResult = "error"`** (pyright) is the load-bearing guardrail
  against silently discarding a `Result`/`IOResult` (`constraints.md:65` — there is
  no pyright plugin for `returns`, so this diagnostic *is* the enforcement). Audit
  that every consumer's `[tool.pyright]` sets it; a consumer that vendors `returns`
  without it can drop Results silently.

---

## Part D — fix the scaffold template (prevent future drift)

The root cause of `beads-fabro`'s drift: its `[tool.livespec_dev_tooling]` block
was set to core's `livespec` layout and never re-pointed at its own package. The
consumer scaffold template lives here:
`templates/orchestrator-plugin/{% if ecosystem == 'python' %}pyproject.toml{% endif %}.jinja`
(+ `templates/orchestrator-plugin/copier.yml`).

**Fix:** ensure the template emits a `[tool.livespec_dev_tooling]` block whose
source-tree paths are **parameterized by the consumer's package name** (a copier
variable), so a freshly scaffolded consumer points at its own package, not
`livespec`. This is the *prevention* half; `rop-sweep-library-checks`'s
drift-guardrail is the *detection* half. Together they make this class of drift
impossible to introduce silently. Confirm the current template state first —
whether it omits the block (consumers hand-write it, which is how the drift
entered) or hardcodes `livespec` — and fix accordingly.

---

## Coordination / sequence

1. **Core (this plan):** land the spec observability rule (Part B) + the template
   fix (Part D); decide the BLE / pyright policy (Part C); run the fleet audit
   (Part A).
2. **`rop-sweep-library-checks` (dev-tooling):** land the config-driven checks +
   drift-guardrail; the guardrail then enforces Part D's intent on existing repos.
3. **`rop-sweep-consumer-cleanup` (beads-fabro):** the drifted consumer catches up;
   its Phase 3 consumes the dev-tooling fix.

The three are independent to *start* but interlock: Part D + the drift-guardrail
prevent recurrence, the library fix unblocks the consumer's Phase 3, and the audit
may surface more consumers needing their own cleanup slice.

## Decisions for the implementing session

1. **Fleet target bar:** "no `except Exception`" (git-jsonl already meets) vs
   "full ROP with vendored `returns`" (only core meets). Recommend the latter as
   the stated target, phased.
2. **Ruff `BLE` fleet policy:** add to the shared template (recommended) vs leave
   to `no_except_outside_io` alone.
3. **Template fix shape:** parameterize an emitted block (recommended) vs document
   a required post-scaffold manual step (rejected — that is exactly what drifted).

## Evidence / references (file:line — this repo)

- ROP mandate: `SPECIFICATION/constraints.md:65` (`returns` primitives +
  `reportUnusedCallResult`), `:147` ("stays on the railway"), `:34`.
- Consumer scaffold template: `templates/orchestrator-plugin/…pyproject.toml….jinja`,
  `templates/orchestrator-plugin/copier.yml`, `copier.yml`.
- The drifted consumer + its inventory: `rop-sweep-consumer-cleanup` in
  `livespec-orchestrator-beads-fabro`.
- The shared-check fixes this depends on / enables: `rop-sweep-library-checks` in
  `livespec-dev-tooling`.
