# Handoff: dev-tooling single-source convergence (livespec-zs22.7.9)

**Track:** dev-tooling single-source convergence · **Ledger:** livespec
**`zs22.7.9`** (child of the Conformance Pattern epic **`zs22.7`**). This
ABSORBS the retired ob-0x5 worktree-pack distribution (its handoff is archived at
`archive/prompts/worktree-discipline-pack-handoff.md`). This file carries durable
*design + plan*; the *authoritative status* lives in the ledger, never here.

## FIRST ACTION — relay i05g blocker-2 (then implement); WAVE 2 de-dup is DONE

**`2exa`'s NAMED blocker is DONE.** The driver-only `plugin_structure` check was
relocated out of the canonical `checks/` set into a non-canonical `driver_checks/`
package (dt PR #193, released **dt v0.25.1**); both drivers point their recipe at
`livespec_dev_tooling.driver_checks.plugin_structure` (PRs #59/#32); and the WHOLE
fleet was hand-bumped to **dt v0.25.1** green — core #665, runtime #72, beads-fabro
#184, git-jsonl #133, plus both drivers — so the relocation AND the `.5` strict
byte-identity verifier are now propagated fleet-wide. `livespec-2rab`'s
discover-siblings `jq` bug is VERIFIED non-blocking (the source-side
release-dispatch run is green).

**TOP PRIORITY (do this FIRST): `livespec-i05g` (P1) — the fan-out AUTOMATION is
still broken.** The bump-pin composite Action runs each consumer's FULL `just check`
in an INCOMPLETE CI env, so every automated bump-pin run fails (3 modes: the
hand-rolled hook body ≠ the strict `CANONICAL_HOOK_BODY`; CORE's doctor rglob-scans
the `.livespec-dev-tooling/` support-module checkout and flags dt's own `§"…"`
citations; the orchestrator/runtime doctors error "livespec core not found"). The
consumers THEMSELVES are fine at v0.25.1 (proven: runtime #72's NORMAL CI was fully
green) — the failures are 100% the bump-pin's broken env.

i05g's **blocker 2 is a DESIGN FORK** that changes the documented `contracts.md`
`§Fallback-to-known-good-pin` / `§Cross-repo coordination automation surface`
contract, so it is SURFACED TO THE MAINTAINER (pending decision — do NOT pick an
approach unilaterally). Recommended = **option B**: the bump-pin STOPS running the
full `just check` and lets each auto-merge PR's OWN CI (the authoritative
branch-protection gate, properly set up) decide — fixes all 3 modes at once, matches
the spec's "the failure surfaces on the PR's status checks" language. **blocker 1**
(the hand-rolled hook install) is ENTANGLED with the fork (option B deletes that
step; option A fixes it) → it is HELD; do NOT fix it until the fork lands.

THE MOMENT the blocker-2 decision is relayed: implement it in dt's
`.github/actions/bump-pin-rewrite/action.yml` (+ blocker 1 per the chosen option),
cut a dt release, and verify the fan-out now auto-propagates. (Note: every consumer
is ALREADY at v0.25.1, so a bump of the *current* tag is a no-op — verify on the
NEXT real shared-artifact release, e.g. the one `.6` or `.3` produces.)

**WAVE 2 COMPLETE — the de-dup convergence is DONE (2026-06-27 session).** Every
single-source-able dev-tooling artifact is now reused from the package; ZERO
vendored worktree-pack copies remain fleet-wide; the byte-identity verifier is
proven fail-closed. Slices **`.3`, `.4`, `.5` are CLOSED**, plus `.6` part 1.

- **dt v0.26.0 → v0.27.0** ship the worktree pack as package-data
  (`livespec_dev_tooling/worktree_pack/{worktree-lib,branch-protection}.sh` +
  `worktree.just`) + `install_worktree_pack.py` + `just install-worktree-pack` + a
  3rd byte-identity-verifier arm on the EXISTING
  `primary_checkout_commit_refuse_hook_installed` slug (no new canonical slug).
- **Delivery = MODEL B (untracked-installed):** consumers gitignore the pack files
  and install them via bootstrap/CI (never tracked-committed) — mirrors the hook
  precedent; drift is structurally impossible. Recipe single-sourcing uses
  **`import? 'dev-tooling/worktree.just'`** (the OPTIONAL `import?` — a plain
  `import` of the absent fragment bricks a fresh clone pre-bootstrap).
- **Consumers converted:** git-jsonl (PR #135 → dt v0.27.0) + the core impl-plugin
  TEMPLATE (PR #668 — retired the 3 template scripts + the obsolete
  `test_git_hook_wrapper.py`, whose invariant relocated into dt PR #199).
  `worktree-hydrate.sh.jinja` stays the only templatized worktree artifact.
- **`.6` remainder (maintainer-gated):** part 2 = the dev-tooling `contracts.md`
  `§Pin autodiscovery rules` revise is FILED (proposal PR #195) awaiting
  `/livespec:revise`-accept; part 3 = beads-fabro `_commit` un-poison (recommend
  `_commit: v0.2.0`; non-blocking).

**REMAINING follow-up slice work (all FILED; independent; none block each other):**

- `livespec-7a4e` (P3) — deliver the worktree pack + recipes to **beads-fabro +
  console** (ADDITIVE — they carry no copies; deferred out of the de-dup; each also
  needs a per-ecosystem `worktree-hydrate.sh`).
- `livespec-jzpx` (P3) — single-source the **branch-protection** recipes via
  `branch-protection.just` (same package-data + installer + verifier + `import?`
  mechanism as `worktree.just`).
- `livespec-usd3` (P3) — fix the `install_worktree_pack` docstring
  (`tracked` → untracked-installed, model B).

Print live status (do not trust this file for status):

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-i05g
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-2exa
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-zs22.7.9
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec ready --limit 8
```

Derive "what's done / what's next" from that plus `git log` in each target repo.
**No shadow ledger** — re-verify every per-repo claim directly (the fleet is
non-uniform). As of the 2026-06-27 session: `zs22.7.9.1/.2/.3/.4/.5/.7` are
CLOSED — the **WAVE 2 de-dup convergence is DONE** (zero vendored worktree-pack
copies fleet-wide, single-sourced from dt **v0.27.0**, byte-identity verifier
proven fail-closed); `2exa`'s plugin_structure relocation is DONE; `.6` part 1 is
MERGED. REMAINING: the maintainer-gated `i05g` blocker-2 fork (recommend option
B), `.6` part-2 `/livespec:revise`-accept (proposal PR #195), and `.6` part-3
un-poison (recommend `_commit: v0.2.0`); plus three FILED follow-up work-items —
`livespec-7a4e` (deliver pack + recipes to beads-fabro + console — ADDITIVE
coverage, deferred), `livespec-jzpx` (`branch-protection.just` single-source),
`livespec-usd3` (`install_worktree_pack` docstring fix). git-jsonl + the core
impl-plugin TEMPLATE are at dt v0.27.0; the remaining consumers are unchanged (the
broken fan-out changed no pins). The `.2` spec-prose follow-up is `livespec-325j`
(P3).

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
non-uniform. Scope `(a)` (commit-refuse hook fan-out), `(b)` (`plugin_structure`
→ package, via the `2exa` relocation into `driver_checks/`), and `(e)` (the strict
byte-identity Verifier) have LANDED and propagated fleet-wide (every consumer at dt
v0.25.1). What remains: the fan-out-AUTOMATION repair (`i05g`) and scopes
`(f)`/`(c)`/`(d)` = slices `.6`/`.3`/`.4`.

## Next concrete action — derive from the ledger

The plan IS the open ledger items (FIRST ACTION query). **The first action is
`livespec-i05g` (P1)** — but its blocker-2 fix is a maintainer-gated DESIGN FORK
(recommended option **B**; see FIRST ACTION), so do NOT pick an approach
unilaterally. The moment the decision is relayed: implement it in dt's
`bump-pin-rewrite` composite Action → cut a dt release → verify the fan-out
auto-propagates on the next real shared-artifact release. MEANWHILE run the
fork-independent slices in parallel: `.6` (drop the copier autodiscovery code + the
governed `contracts.md` revise + the beads-fabro `_commit` decision), then `.3`
(worktree-pack package-data; absorbs the impl-plugin template hook conversion) +
`.4` (lifecycle recipes). `2exa`'s plugin_structure relocation and `.5`'s fleet-wide
propagation are DONE; `.1/.2/.7` are CLOSED; the design decisions below are settled.

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
