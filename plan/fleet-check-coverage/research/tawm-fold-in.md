# tawm fold-in — the final epic piece before archival

Record of the 2026-07-12 (SESSION 15) maintainer decision to keep the
`fleet-check-coverage` epic (`livespec-i5ebqd`) OPEN after it reached
8/8 flipped/resolved, and fold `livespec-tawm` in as the last work
before archival.

## Why the epic is not archived yet

The epic's original done-definition was "every structural check covers
every tracked first-party `.py` in every in-scope repo, and `file_lloc`
is flipped to a hard gate per repo." That is **DONE** — all 8 in-scope
repos are flipped/resolved with independent Fable NO-BLOCKERS reviews
and fleet-wide green CI (see the epic's SESSION-15 completion comment
and the closed tracks).

The driver work SURFACED a real pre-existing bug (`livespec-tawm`): the
Driver-shipped `no_shadow_ledger.py` hook is documented as byte-identical
single-sourced across `livespec-driver-claude` and `livespec-driver-codex`
(livespec core `SPECIFICATION/contracts.md` §"Driver-shipped hooks"), but
the two copies have **already drifted** (a ~2-line docstring diff), the
contract is **unenforced** (no live byte-identity guard), and the shared
body lacks `__all__` (leaving one residual `all_declared` Phase-0 WARN on
BOTH drivers — the single thing keeping each driver from 100% warning-clean).

The maintainer chose (SESSION-15) to **keep the epic open and fold this fix
in as the final piece** rather than archive with it tracked only as a
separate item — expanding the epic slightly beyond its original
file_lloc-coverage scope so the drivers end genuinely warning-clean and the
byte-identity contract is enforced. **Archival is AUTHORIZED once tawm lands
+ is independently Fable-reviewed.**

## The tawm fix (coordinated cross-driver change) — scope for the next session

1. **Reconcile** the two `no_shadow_ledger.py` bodies to genuine byte-identity
   (pick the canonical wording; align the drifted docstring).
   - `livespec-driver-claude`: `.claude-plugin/hooks/no_shadow_ledger.py`
   - `livespec-driver-codex`: `livespec/hooks/no_shadow_ledger.py`
   - Drift-causing commits (per the Fable side-observation): claude `9283b68`,
     codex `16c5c65` (each dropped a §-citation divergently).
2. **Add `__all__`** (the real export list, or `list[str] = []`) to the shared
   body, byte-identically in BOTH drivers → clears the residual `all_declared`
   WARN on both.
3. **Add a mechanical byte-identity guard** so the contract stops being
   aspirational. Per livespec `.ai/no-circular-dependency.md`, a cross-repo
   consistency check lives on the CONSUMER side reading the producer — FIRST
   determine the canonical source (does livespec core already ship/own the
   canonical `no_shadow_ledger.py` body? if so the drivers assert their copy
   matches core's; otherwise decide a canonical home) BEFORE adding a new guard.

## Execution notes (carry into the next session)

- **HOST-SIDE** (touches the shared hook contract + possibly a new enforcement
  check) — NOT factory-safe. Author via scoped agents in worktrees under
  review, same lane as the Phase-0 mechanism / `livespec-iily`.
- Editing `.github/workflows/` (if the guard is wired into driver CI) needs
  the `workflows`-permission wall workaround proven this epic (host-side push
  with maintainer creds, not the factory bot).
- **Groom `livespec-tawm` into ready slices first** (it is a small cross-repo
  epic: per-driver body edits + `__all__` + a guard). Independent Fable review
  before accepting each slice.
- Driver PRs AUTO-MERGE on green CI → review-the-merged-commit + fix-forward.
- **Then archive:** close `livespec-i5ebqd` and `git mv plan/fleet-check-coverage/
  → plan/archive/fleet-check-coverage/` (the plan-thread lifecycle: archived iff
  the epic is closed). The maintainer pre-authorized archival-after-tawm; a fresh
  session should confirm tawm is genuinely done + reviewed before archiving.
