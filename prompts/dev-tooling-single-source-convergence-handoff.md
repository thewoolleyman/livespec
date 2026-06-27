# Handoff: dev-tooling single-source convergence (livespec-zs22.7.9)

**Track:** dev-tooling single-source convergence · **Ledger:** livespec
**`zs22.7.9`** (child of the Conformance Pattern epic **`zs22.7`**). This
ABSORBS the retired ob-0x5 worktree-pack distribution (its handoff is archived at
`archive/prompts/worktree-discipline-pack-handoff.md`). This file carries durable
*design + plan*; the *authoritative status* lives in the ledger, never here.

## FIRST ACTION — repair the fan-out FIRST, then derive status from the ledger

**TOP PRIORITY (do this FIRST): `livespec-2exa` (P1) — repair the dt-pin fan-out.**
`zs22.7.9.2` made the driver-specific `check-plugin-structure` a CANONICAL slug;
it CRASHES core, FAILS the orchestrator plugins (beads-fabro/git-jsonl), and is
unwired in every aggregate-enforced consumer, so `bump-pin-from-dispatch` fails
`check-aggregate-completeness` and consumers are stuck on stale dt pins (core
v0.22.0; others v0.23.0). That BLOCKS consumer propagation of `zs22.7.9.5` and
the rest of this epic. Recommended fix = `2exa` option **B** (relocate
`plugin_structure` out of `checks/` into a driver-only NON-canonical namespace +
update the 2 drivers' recipe; ~3 PRs). ALSO fix the SEPARATE pre-existing
fan-out bug `livespec-2rab` (discover-siblings `jq` error post-v148), then verify
a dt release auto-propagates pins to all consumers green.

Print live status (do not trust this file for status):

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-2exa
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.7.9
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec ready --limit 8
```

Derive "what's done / what's next" from that plus `git log` in each target repo.
**No shadow ledger** — re-verify every per-repo claim below directly (the fleet
is non-uniform). As of 2026-06-27: `zs22.7.9.1/.2/.7` are CLOSED; `.5` (strict
byte-identity verifier) is CODE-LANDED + RELEASED (dt v0.25.0) but its consumer
propagation is BLOCKED by `2exa`; `.6/.3/.4` remain (each slice's ledger notes
carry the plan, including `.6`'s beads-fabro `_commit` render-version decision —
the "restore v0.3.0" premise is VERIFIED WRONG — and its governed dt
`contracts.md` `/livespec:revise`-accept). The `.2` spec-prose follow-up is
`livespec-325j` (P3).

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
    un-poison beads-fabro's current `_commit: v0.4.0`. **NOTE (verified
    2026-06-27): the "tree is v0.3.0-rendered after PR #174" premise is WRONG —
    the whole v0.2.0→v0.3.0→v0.4.0 chain was bump-pin rewrites with zero template
    churn; the last GENUINE render was core `4f60277` (`v1.0.0-638-g4f60277`,
    contained in `v0.2.0`). So the un-poison is a maintainer decision (re-render
    via `copier update --vcs-ref=master`, or set `_commit: v0.2.0`, or the literal
    rendered ref) — see the `.6` ledger note.**

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

The plan IS the open ledger items (FIRST ACTION query). **The first action is
`livespec-2exa` (P1)** — repair the dt-pin fan-out (option **B**) so consumer
pins auto-propagate again; until then the "each shared-artifact change auto-bumps
every consumer's pin and stays green" assumption is **FALSE** (the fan-out's
`bump-pin-from-dispatch` fails on the canonical-but-incompatible
`check-plugin-structure`, plus the separate `livespec-2rab` discover-siblings
bug). After the fan-out is green: finish `.5` consumer verification (drift a hook
→ confirm fail-closed at a consumer), then `.6` (drop the copier autodiscovery
code + the governed `contracts.md` revise + the beads-fabro `_commit` decision),
then `.3` (worktree-pack package-data; absorbs the impl-plugin template hook
conversion) and `.4` (lifecycle recipes). `.1/.2/.7` are CLOSED; the design
decisions below are settled.

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
