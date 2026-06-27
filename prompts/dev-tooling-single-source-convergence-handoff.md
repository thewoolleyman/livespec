# Handoff: dev-tooling single-source convergence (livespec-zs22.7.9)

**Track:** dev-tooling single-source convergence · **Ledger:** livespec
**`zs22.7.9`** (child of the Conformance Pattern epic **`zs22.7`**). This
ABSORBS the retired ob-0x5 worktree-pack distribution (its handoff is archived at
`archive/prompts/worktree-discipline-pack-handoff.md`). This file carries durable
*design + plan*; the *authoritative status* lives in the ledger, never here.

## FIRST ACTION — implement the two DECIDED tasks: i05g blocker-2 (Option B) + 7a4e

**CONVERGENCE CLOSED (2026-06-27).** The dev-tooling single-source convergence is
DONE and the epics cascaded: **`zs22.7.9` → `zs22.7`** (Conformance Pattern,
Increment 5) **→ `zs22`** (parent epic) are ALL CLOSED. Every shared dev-tooling
artifact is single-sourced from the package (dt **v0.28.0**): the commit-refuse
hook, the worktree pack (`worktree-lib.sh` + `branch-protection.sh`), and BOTH
recipe fragments (`worktree.just` + `branch-protection.just`) — ZERO vendored copies
fleet-wide; **MODEL B** (untracked-installed: gitignore + bootstrap/CI install,
mirrors the `.git/hooks` precedent); recipes via the OPTIONAL **`import?`** (a plain
`import` of the absent fragment bricks a fresh clone pre-bootstrap). The
byte-identity verifier (the existing `primary_checkout_commit_refuse_hook_installed`
slug, no new canonical slug) covers all 4 pack files and is PROVEN fail-closed.
`.6` is closed (part 1 dt #196; part 2 the `§Pin autodiscovery rules` revise-accept
dt #202; part 3 beads-fabro `_commit` → `v0.2.0` #185). Follow-ups **`livespec-jzpx`
CLOSED** (branch-protection.just: dt #203 + git-jsonl #136 + core template #670) and
**`livespec-usd3` CLOSED** (docstring `tracked` → untracked-installed). This file is
KEPT (not archived) as the entry point for the two DECIDED tasks below.

The sections below are durable **design + history**. A fresh session implements
these **two DECIDED tasks** — both are the maintainer's calls, already made;
implement, do NOT re-litigate or re-surface as forks:

### TASK 1 — `livespec-i05g` blocker-2 = OPTION B (re-enable the fan-out)

DECIDED: let each consumer's OWN CI gate the bump. The bump-pin fan-out's composite
Action (`livespec-dev-tooling` `.github/actions/bump-pin-rewrite/action.yml`)
currently runs each consumer's FULL `just check` in an INCOMPLETE CI env, so every
automated bump fails (3 modes; the consumers themselves are green on their OWN CI).
Implement:

- **DROP the bump-pin's local full-`just check` pre-test entirely.** The Action just
  rewrites the pin, commits, and opens the auto-merge PR — and lets each consumer's
  OWN CI (the authoritative branch-protection gate) decide whether to merge.
- **BUNDLE the worktree-pack-install sequencing constraint into the re-enabled
  bump.** When auto-bumping a consumer to a pack-carrying release (dt v0.26.0+), the
  SAME bump PR MUST also run `just install-worktree-pack` (writes the pack incl
  `worktree.just` + `branch-protection.just`) and swap the consumer's inline recipe
  stanzas for `import? 'dev-tooling/worktree.just'` /
  `import? 'dev-tooling/branch-protection.just'` — else the consumer's verifier fails
  `worktree_pack_file_missing`. (This is the Wave-2 consumer-sequencing constraint,
  now codified into the automated bump.)
- **FIX blocker 1 accordingly:** under Option B the bump-pin's hand-rolled inline
  hook-install step is DELETED (the consumer's own CI/bootstrap installs the
  canonical hook from-package; the strict byte-identity verifier then validates it).
- **CUT a dt release; verify** the fan-out auto-propagates on the next real
  shared-artifact release. (Mixed pins: git-jsonl + core impl-plugin template at
  **v0.28.0**; the other consumers at v0.25.1 — any bump crossing v0.26.0 MUST carry
  the pack-install bundle above.)
- **FILE the contract change** for `contracts.md`
  `§"Fallback-to-known-good-pin"` / `§"Cross-repo coordination automation surface"`
  via `/livespec:propose-change` (against the dev-tooling spec) and surface the
  `/livespec:revise`-accept — the contract today describes the bump running its OWN
  validation; Option B changes it to "the failure surfaces on the PR's status
  checks."

### TASK 2 — `livespec-7a4e` = INCLUDE (full fleet coverage)

DECIDED: deliver the worktree-discipline pack to BOTH
`livespec-orchestrator-beads-fabro` AND `livespec-console-beads-fabro` (they carry
NO worktree pack/recipes today). For EACH repo (mirror the consumer add-side from
git-jsonl #134/#135/#136): add an `install-worktree-pack` recipe + bootstrap call;
add `import? 'dev-tooling/worktree.just'` + `import? 'dev-tooling/branch-protection.just'`;
gitignore the 4 pack files (model B); bump the dt pin to the latest release; ensure
CI installs the pack before `just check` so the verifier VALIDATES (not skips). PLUS
author a PER-ECOSYSTEM `dev-tooling/worktree-hydrate.sh` for each (beads-fabro =
Python; console = Rust) — the `worktree-hydrate` recipe execs it, and it is NOT part
of the pack (it stays a per-ecosystem tracked script, like the impl-plugin
template's `worktree-hydrate.sh.jinja`).

**PARKED:** M2 (`zs22.8`) stays parked — out of scope for this file.

Print live status (do not trust this file for status):

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-i05g
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-7a4e
/data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec ready --limit 8
```

Derive "what's done / what's next" from that plus `git log` in each target repo.
**No shadow ledger** — re-verify every per-repo claim directly (the fleet is
non-uniform). As of the 2026-06-27 session: the convergence is COMPLETE —
`zs22.7.9` + `zs22.7` + `zs22` are CLOSED; all slices `.1`–`.7` + `.6` CLOSED;
follow-ups `livespec-jzpx` (#670 merged) + `livespec-usd3` CLOSED; `2exa`'s
plugin_structure relocation is DONE. dt is at **v0.28.0** with all 4 pack artifacts
(`worktree-lib.sh`, `branch-protection.sh`, `worktree.just`, `branch-protection.just`)
single-sourced + the verifier fail-closed. REMAINING = the two DECIDED tasks above:
`livespec-i05g` blocker-2 = **Option B** (re-enable the fan-out; bundle the
pack-install sequencing; delete the hand-rolled hook step; file the
`§Fallback-to-known-good-pin` contract revise) and `livespec-7a4e` = **full
coverage** (deliver the pack to beads-fabro + console with a per-ecosystem
`worktree-hydrate.sh` each). M2 (`zs22.8`) PARKED. Mixed dt pins: git-jsonl + the
core impl-plugin TEMPLATE are at **v0.28.0**; the other consumers at v0.25.1 (the
still-broken fan-out changed no pins — Task 1 re-enables it). The `.2` spec-prose
follow-up is `livespec-325j` (P3).

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
