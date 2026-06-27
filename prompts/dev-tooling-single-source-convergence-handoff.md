# Handoff: dev-tooling single-source convergence (livespec-zs22.7.9)

**Track:** dev-tooling single-source convergence · **Ledger:** livespec
**`zs22.7.9`** (child of the Conformance Pattern epic **`zs22.7`**). This
ABSORBS the retired ob-0x5 worktree-pack distribution (its handoff is archived at
`archive/prompts/worktree-discipline-pack-handoff.md`). This file carries durable
*design + plan*; the *authoritative status* lives in the ledger, never here.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.7.9
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.7
```

Derive "what's done / what's next" from that plus `git log` in each target repo.
**No shadow ledger** — re-verify every per-repo claim below directly (the fleet
is non-uniform).

## Read first

1. This file (design + plan, below).
2. `research/factory-conformance/cross-repo-conformance-pattern.md` — the
   Conformance Pattern and its **DELIVERY RULE** ("reuse by default, pin+import
   from livespec-dev-tooling, byte-identical, no copies") that this work enforces.
3. `livespec-dev-tooling`'s `livespec_dev_tooling/install_commit_refuse_hooks.py`
   — the **from-package precedent**: a `CANONICAL_HOOK_BODY` string constant +
   a `python -m …` installer that writes it straight to `.git/hooks/`. This is
   the single-source pattern to MIRROR for the worktree-pack scripts.
4. `archive/prompts/worktree-discipline-pack-handoff.md` — the retired ob-0x5
   handoff (history/context only).

## The problem (why this exists)

Fleet-wide `dev-tooling/` **shell** artifacts are vendored as per-repo COPIES
that violate the "reuse, no copies" rule and have **already drifted, undetected**
— the `primary_checkout_commit_refuse_hook_installed` check verifies only a loose
FINGERPRINT of the *installed* hook, not byte-identity vs a canonical source.

Audit (2026-06-26, git blob-SHA across fleet `origin/master`):

- **commit-refuse hook `git-hook-wrapper.sh` — 3+ divergent versions:**
  {core, git-jsonl, impl-plugin template} = `433f5c5`; {driver-claude,
  driver-codex} = `067414e`; {beads-fabro} = `972576c` (dead dispatch-only stub);
  livespec-runtime carries the OLD `livespec-commit-refuse-hook.sh` = `0123665`.
  Single source ALREADY EXISTS (`CANONICAL_HOOK_BODY`). console + beads-fabro
  already install from-package; the rest file-copy.
- **`check_plugin_structure.py` — 2 divergent versions:** driver-claude
  `4153e6a` vs driver-codex `6e781e6`.
- **worktree pack `worktree-lib.sh` (`cd21441`) + `branch-protection.sh`
  (`dda7b9c`):** copy-based (copier template → consumers); byte-identical now,
  drift-prone by construction.

## Scope (the convergence — `zs22.7.9` is authoritative)

(a) **commit-refuse hook → from-package fleet-wide:** every repo installs via
    `python -m livespec_dev_tooling.install_commit_refuse_hooks`; DELETE every
    vendored `git-hook-wrapper.sh` (core, both drivers, beads-fabro stale,
    git-jsonl, the impl-plugin template) + runtime's
    `livespec-commit-refuse-hook.sh`.
(b) **`check_plugin_structure.py` → the livespec-dev-tooling package;** both
    drivers import; delete the two vendored copies.
(c) **worktree pack scripts (`worktree-lib.sh`, `branch-protection.sh`) →
    single-source delivery** (from-package/pin+import, mirroring the hook
    precedent). Convert git-jsonl's interim copy; deliver to beads-fabro +
    console + any consumer via reuse. `worktree-hydrate.sh.jinja` STAYS
    templatized (legitimately per-ecosystem). This is ob-0x5's Phase-7
    distribution, done right.
(d) **worktree LIFECYCLE recipes** (`just worktree-{create,hydrate,land,reap}`)
    via the single-source mechanism, not copier-copy.
(e) **byte-identity Verifier** wired into `just check` fleet-wide — fails CLOSED
    on any vendored copy that drifts from its canonical source (closes the gap
    that hid the current drift).
(f) **fix the release fan-out's `copier_answers_commit` poisoning:** the
    `bump-pin-rewrite` action rewrites `.copier-answers.yml _commit` to the new
    tag WITHOUT running `copier update`, desyncing the render-provenance marker
    (a later update diffs newtag→newtag = empty and skips template content).
    Drop `copier_answers_commit` from the bump-pin autodiscovery (the other
    three pin formats ARE version pins; `_commit` is render-provenance). Also
    un-poison beads-fabro's current `_commit: v0.4.0` (tree is v0.3.0-rendered
    after fan-out PR #174).

## Current state — read from the ledger, not here

This file is durable **design**. The authoritative, current status lives in the
**ledger** — run the FIRST ACTION query and read the `zs22.7.9.N` slices (the
groom). Do **not** trust any prose snapshot here for status; the FIRST ACTION
query is the single source of truth (**no shadow ledger**), and each slice
carries its own scope, decisions, blockers, and per-repo notes. The epic has
been groomed into per-artifact slices `.1`–`.7`; scope `(a)` (the commit-refuse
hook fan-out) has landed across the operating repos. Re-verify every per-repo
claim directly (`git log` / `git show origin/master:<path>`) — the fleet is
non-uniform.

## Next concrete action — derive from the ledger

The plan IS the open `zs22.7.9.N` slices (FIRST ACTION query); read them rather
than reconstructing a checkbox queue here. Cross-slice facts the ledger carries:
the `red_green_replay` `.py`-DELETION prerequisite (`.7`) **blocks** the slices
that delete `.py` files (`.2`, `.3`); each shared-artifact change bumps every
consumer's pin and stays green in the **same** epic; and the design decisions
below are settled.

## Resolved design decisions

- **Worktree-pack delivery = package-data** in livespec-dev-tooling (mirror
  `CANONICAL_HOOK_BODY` + an installer module), **not** a shared `just` module —
  for consistency with the proven hook precedent. APPROVED — do not re-litigate.
- **Sequencing = fan-out-before-verifier**: retire vendored copies first (the
  pre-existing fingerprint check guards the migration), then land the strict
  byte-identity Verifier so it needs no migration-tolerance branch. APPROVED.

## Constraints / non-negotiables

- **Dogfood the discipline.** All work in `~/.worktrees/<repo>/<branch>`;
  worktree → PR → rebase-merge; never commit on a primary checkout;
  `mise exec -- git …`; never `--no-verify`; halt and report on any hook failure.
- **Shared-artifact change = one cross-repo epic.** When you move an artifact
  into the package or retire a vendored copy, bump EVERY consumer's pin and
  verify `just check` stays green fleet-wide in the SAME epic — the fleet shares
  one validator over independent stores.
- **The byte-identity Verifier fails CLOSED** and is wired into `just check` at
  every repo — a fingerprint check is NOT enough (that's what hid the drift).
- **Pins track the latest RELEASE, not master** (zs22 locked decision).
- **No shadow ledger.** Status comes from the FIRST ACTION query.

## Archive condition

When `zs22.7.9` closes (every shared dev-tooling artifact single-source, zero
vendored duplicates fleet-wide, byte-identity Verifier green), `git mv` this file
to `archive/prompts/` with a completion banner. Durable history then lives in the
spec, the commits, and the ledger.
