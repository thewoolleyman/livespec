# Child review and autonomous-delivery authorization — 2026-09-08

Five independent Fable reviewers were commissioned against every remaining open
child of epic `livespec-n33rwg` before the maintainer's autonomous-delivery
authorization was acted on. Two children needed amendment BEFORE build, one was
already fixed elsewhere, one is one green from closing, two were clean.

The single most important result is that **this plan's own work-item contained a
verified-false claim about release behaviour, copied from `AGENTS.md`, and had
already propagated it into a second repo's work-item as an acceptance
criterion.** That is recorded first.

## Finding 1 — the R6 "trap" was backwards, and doctrine was its source

`livespec-n33rwg.4` warned implementers NOT to derive the releasing commit-type
set from `release-please-config.json` `changelog-sections`, asserting that
`perf`/`refactor`/`revert` are `hidden: false` yet cut no release, and that the
true releasing set is `feat`/`fix`/breaking only.

**That is inverted.** Measured on livespec's own history and re-verified
directly rather than taken from the reviewer:

| Range | Composition | Release cut? |
|---|---|---|
| `v0.28.2..v0.28.3` | 36 commits: 5 `refactor`, 5 `chore`, 26 `docs`. Zero `feat`, `fix`, `revert`, breaking. | **Yes — v0.28.3** |
| range for `v0.21.3` | only non-docs commit was a single `revert`, no breaking footer; changelog lists only "Reverts" | **Yes — v0.21.3** |
| 2026-08-30 → 2026-09-08 | 30+ commits, all `docs`/`chore` | **No** — latest stayed v0.38.2 |

So a refactor-only window cut a release and a revert-only window cut a release,
while a docs/chore-only window did not. On livespec's config the empirical
releasing set **is** the `hidden: false` set, and deriving from
`changelog-sections` gives the *right* answer.

### How the error got in, which matters more than the fact

The item measured the hidden **flags** correctly and then took the releasing
**behaviour** claim from `AGENTS.md` doctrine instead of from observed releases.
It is this plan's own `.ai/verifying-against-the-right-source.md` lesson turned
on the plan itself — the right file, the wrong field, and a doctrine sentence
trusted in place of the producer's actual output.

### What it invalidated, all corrected together

1. `livespec-n33rwg.4`'s trap paragraph and one acceptance bullet — amended.
2. `AGENTS.md`'s seam sentence — corrected in this change, with the measurement
   inline so the next reader cannot re-derive the wrong set from prose.
3. **`livespec-dev-tooling-ys2i`**, slice A of the guard in the sibling tenant,
   whose acceptance required *"the SAME function returns False for perf,
   refactor, and revert (THE TRAP), with a test asserting exactly that."* It had
   already been dispatched twice (2026-08-30), both runs producing no
   checkpointed diff. **Had it succeeded, a correctly-executing agent would have
   shipped a wrong guard and locked the wrongness in with a passing test.**
   Amended, and retitled away from "the trap".

### The releasing set is per-repo, not a fleet constant

release-please **defaults** hide `refactor`, so a repo declaring no
`changelog-sections` does not release on it. The set must be derived per repo
from that repo's own config, with the defaults as fallback — the opposite of
what the item previously instructed.

### One real conflict this surfaced

livespec-dev-tooling already ships `release_bump_classification` (2026-08-26),
whose patch types are `fix` and `perf` — treating `perf` as releasing, matching
the evidence and contradicting `ys2i`'s old acceptance. Two checks in one package
would have modelled `perf` in opposite directions. It does **not** supersede R6:
it asks whether a *declared* bump is strong enough for a Python public-surface
delta, so a `docs:` change to shipped prose moves its inventory by nothing and
passes straight through the R6 defect.

## Finding 2 — `.5` shipped a detector with no reader

Every technical premise re-verified (overseer's three watcher files unchanged
with zero commits since 2026-08-21; `lane_state` still pure; propagation not
started; shim pattern current; the two-of-fourteen `release-tag.yml` scope claim
still exact). But the watcher reports by **redding its own cron job**. Signal 1
will not read that — it still hardcodes the workflow name `CI`. Signal 9 will
not — it reads release lanes. And the acceptance named no reader.

That is this epic's own thesis one level up: propagating the *detection* half of
the overseer's "scheduled job + operator surface" ruling without the surface.

Where the value actually is, stated honestly: for `release-tag` lanes the delta
over Signal 9 is **depth only** (streak, last-green, truncation) in exactly two
repos, one of which already has the watcher. The real detection value is in
lanes with **no release object**, which Signal 9 structurally cannot see because
it reads the latest release's tag commit — a daily readiness canary failing for
two weeks, the console's `release-binary` lane, a driver's `release-dispatch`
lane. Acceptance now requires a named reader and that the derived set include
those lanes.

## Finding 3 — `.7` was already fixed upstream

livespec-dev-tooling `9e5a1ea1` (2026-09-07) under `livespec-dev-tooling-xdyh`,
with a 293-line executed collision test. The composite now probes with
`git ls-remote` and resets a pre-existing branch with a scoped
`--force-with-lease` naming one ref plus an explicit refspec — never a bare
force, every other push-failure class still fails loudly.

**Live for livespec without a pin bump**: the reusable workflow checks out
livespec-dev-tooling with no `ref:` (master HEAD) and runs the composite from
that checkout.

**The green lane proved nothing** — all eight green scheduled runs
(2026-08-31 → 09-07) ran pre-fix code and were green because the *condition* was
absent, the colliding branch having been hand-deleted when PR #2502 closed.
Condition passed, defect unfixed, until `9e5a1ea1`. Closed as fixed-upstream.

## Finding 4 — `.3` is one scheduled green from closing

The 2026-09-07 scheduled run concluded **success** — the first of two. The fix
is intact on master and the only commit since 2026-09-02 touching the
ratification gate, the e2e tree, or the workflow is the fix commit itself. Title
corrected: it had said "3/3 red since 2026-08-03" against a recorded reality of
fourteen consecutive failures since 2026-06-01.

Residual: the workflow installs the CLI **unpinned** by design as the drift
canary, so 2026-09-14 could go red on a new, unrelated CLI change.

## Finding 5 — `.1`/`.2` clean, with two driver notes

Still 227 and 230 LLOC, markers intact, untouched since the marker-add commit,
and the check in the currently pinned dev-tooling `v1.58.5` is **byte-identical**
to the `v1.31.1` they were written against. No open PR touches either file.

- **A new per-commit tripwire** landed with the markers: an *unowned* soft-band
  file now fails per-commit. An extraction module landing at 201–250 LLOC fails
  immediately unless it gets its own marker. Aim extractions well under 200.
- **Red-Green-Replay friction**: a behaviour-preserving extraction has no
  naturally failing behavioural test, so the driver needs a module-shape Red via
  the new-module stub technique.

## The autonomous-delivery authorization, and the gate map

The maintainer authorized promoting every remaining open child to ready and
delivering them autonomously, stopping only on a blocking question. Measured
rather than assumed:

- **Item status is the only real blocker.** Lifecycle statuses are exactly
  `backlog`, `pending-approval`, `ready`, `active`, `acceptance`, `blocked`,
  `closed` (authoritative in the bd guard at `/usr/local/bin/bd`). Because
  `ready` *is* a lifecycle status, `bd update --status ready` is a conformant
  transition; the guard blocks only non-lifecycle statuses and
  `--claim`/`reopen`/`defer`.
- **Admission and acceptance were already automatic** — `auto_approve_ready:
  true` and `acceptance_mode: "ai-only"`, verified to actually parse, because an
  unparseable `.livespec.jsonc` silently reverts the Dispatcher to human-gated
  admission with nothing reported (`bd-ib-lmi5`).
- **No per-item holds existed** — all children carried only `origin:freeform`.

**One gate deliberately left on**, and surfaced rather than flipped:
`merge_on_review_cap` resolves to its safe default `false`, routing a review that
*cannot converge* to a human. That is a quality gate, not an approval-ceremony
gate — turning it off would auto-merge work whose review never converged.

### A wrong instrument, corrected

An earlier report in this plan claimed "`bd ready` is empty, so nothing is
dispatchable." **False.** The `bd ready` subcommand looks for the beads-native
`open` status, which this tenant never uses, so it is structurally always empty
here. The orchestrator's own ranked `next` enumeration showed eight ready items
at the same moment. Read the factory queue with the orchestrator's surface,
never with `bd ready`.
