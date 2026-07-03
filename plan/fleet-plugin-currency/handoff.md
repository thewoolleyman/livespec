# Handoff — fleet-plugin-currency

The single resumable entry point for the **fleet plugin currency** root-cause
investigation + permanent fix. A fresh session can execute the next action
from this file alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** Root-cause investigation and permanent fix for the
  stale-plugin-build failure class: fleet repos keep starting sessions on
  outdated livespec-ecosystem plugin snapshots (concrete trigger 2026-07-03:
  `livespec-console-beads-fabro`'s `/next` routed to stale cache build
  `06e3e080ae19` lacking the credential self-heal while the fixed `0.4.0`
  build sat in cache). Target invariant + phased plan:
  `plan/fleet-plugin-currency/research-plan.md` — read it before acting.
- **Epic anchor:** `livespec-c1k9` (core tenant, P0). Status is READ from
  the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-c1k9
  ```
- **⚑ Golden rules.**
  - Investigation phases (0–3) are **READ-ONLY toward every plugin cache,
    registry, marketplace cache, and settings file** — no updates,
    reinstalls, or pruning until Phase 3 closes; controlled experiments run
    only in scratch projects. Evidence first; a "helpful fix" destroys it.
  - Ready, factory-safe implementation is **factory-dispatched**
    (`/livespec-orchestrator-beads-fabro:orchestrate`) — never hand-coded
    inline. Host-only self-machinery stays maintainer-side.
  - Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
  - The overseer session **rotates before ~50% context**: refresh THIS file
    (state, in-flight agents, next action), print the resume command
    verbatim as the recap's last line.
- **Evidence + research homes.** Raw Phase 0 capture:
  `tmp/fleet-plugin-currency/evidence/` (untracked maintainer-scratch,
  agent-scoped subdir). Curated, durable findings are now committed under
  `plan/fleet-plugin-currency/research/`:
  - `research/semantics.md` — Phase 1 resolution mechanics + H1–H7 verdicts.
  - `research/fleet-audit.md` — Phase 2 fleet × plugin × surface matrix.
  The `tmp/fleet-plugin-currency/drafts/` files
  (`semantics-draft.md`, `fleet-audit-draft.md`) are now **SUPERSEDED** by
  those committed `research/` docs — read `research/` as authoritative.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-plugin-currency`.

## The next action

**Phase 4 design review PASSED** (2026-07-03, maintainer decisions via
structured picker — all three recommendations accepted):

- **D1 = SHA-pin to releases:** every fleet catalog entry converts from the
  relative-path source to a git-based source pinned at `sha` = the latest
  release-tag commit; CI auto-bumps the pin on each release (rides the existing
  `bump-pin` discipline); the freshness guard extends to a parked pin-bump; the
  staleness gate compares running snapshot vs the catalog's pinned sha.
  Preserves the research-plan's ORIGINAL "latest released pin" invariant.
- **D2 = Warn + fail lever on Unknown:** confirmed-Stale ALWAYS fails hard;
  Unknown (offline / clone missing / unpinned-transition / legacy snapshot)
  warns loudly and proceeds interactively, with `LIVESPEC_CURRENCY_GATE=fail`
  set in CI and factory dispatch making Unknown fail hard there.
- **D3 = Host-level pre-session sweep DEFERRED:** rely on the uniform
  SessionStart hook + `/reload-plugins` lag-closing nudge + the hard gate;
  revisit only if the reload lag proves painful.

Next actions, in order:

1. **Sha-pin verdict — REFUTED (empirical, Claude Code 2.1.199; log at
   `tmp/fleet-plugin-currency/scratch/experiment-log.md`).** Catalog-level SHA
   pinning is NOT honored by the shipped runtime:
   - `git-subdir` sources are **rejected at runtime** ("source type your Claude
     Code version does not support" — may ship in a newer CC).
   - `github` plugin sources **VALIDATE** `commit`/`branch`/`path`
     (`claude plugin validate` accepts them) but the installer **SILENTLY
     IGNORES all three**, always installing default-branch HEAD (verified
     against real livespec release tags, with clean-cache repeats).
   - Cache dirs are keyed by the resolved `version` field (`plugin.json`
     version if present, else `sha12`); `gitCommitSha` always records the clone
     HEAD.
   - Operational gotcha: `github` PLUGIN sources clone over SSH
     (`git@github.com:`), unlike the HTTPS marketplace clones.
   - The docs (`plugin-marketplaces.md` §"Plugin sources") describe a
     capability the shipped runtime does not deliver. Upstream docs-vs-behavior
     report **filed this session** (see the new work-item, session log below).

   **Maintainer decision (2026-07-03, via picker) — D1 mechanism revised to
   "verify release-branch marketplace-ref first".** Run a scratch experiment
   (`ref-pin-experiment`, **IN FLIGHT**; log will land at
   `tmp/fleet-plugin-currency/scratch/ref-exp/`) verifying (a) `claude plugin
   marketplace add <src>#<ref>` registers at the ref, (b) marketplace update
   holds the ref, (c) plugin update installs clone-at-ref content.
   - **If VERIFIED:** each plugin repo carries a CI-fast-forwarded `release`
     branch pinned to the latest release tag, and the fleet marketplaces
     register `@release` — the release-pinning invariant realized via
     primitives we control.
   - **If REFUTED:** fall back to master-HEAD tracking now, and revisit when
     Claude Code ships working pin support.

   EITHER WAY, the upstream docs-vs-behavior report is filed (below).

   **Maintainer directive (same answer):** the invariant AND its verification
   MUST cover the **CODEX driver path** too. Codex plugin versioning is being
   mapped in the SAME in-flight experiment (help/config/clone semantics, ref
   support, release-branch viability); the finalized design must give Codex an
   equivalent currency + gate story.
2. **Finalize `research/design-draft.md` → `research/design.md`** —
   incorporate D1–D3 + the experiment findings, drop the DRAFT banner.
3. **Re-groom the filed defect items to the decided design, and file the NEW
   implementation items.**
   - Re-groom: `c1k9.2` resolution = reload nudge; `c1k9.3` target = catalog
     pinned sha + D2 severity; `c1k9.5` largely mitigated by sha-pinning;
     `c1k9.6` executable.
   - File NEW implementation items: per-repo catalog sha-pin conversion + CI
     pin-bump automation; release-park freshness guard (reusable workflow in
     `dev-tooling` + per-repo wiring); hook-presence check; hook rollout
     already filed per-repo.
4. **Phase 5 — factory-dispatch the ready, factory-safe items;** host-only +
   spec-side stays maintainer-side. Exit gate = the mechanized fleet-wide
   fresh-session assertion + the negative test (a deliberately-staled cache
   fails loudly).

## Session log

### Session 1 (2026-07-03) — thread opened

- Trigger: maintainer-reported failure in `livespec-console-beads-fabro`
  (`/next` → stale `06e3e080ae19`, raw `Access denied`, self-heal absent);
  maintainer directive: root-cause deeply and make staleness structurally
  impossible — every new session, every fleet repo, every surface, latest
  released pin, 100%.
- Filed epic `livespec-c1k9` (core, P0).
- Authored this thread scaffold (`research-plan.md` + `handoff.md`).
- Dispatched `phase0-evidence` agent (read-only forensic capture →
  `tmp/fleet-plugin-currency/evidence/`).
- Observed live corroboration of H1 in core: this session's own
  SessionStart hook updated `livespec` f79a→db76 and orchestrator
  6df3→1954 with "Restart to apply changes" — the running session stayed
  on the previous fetch.

### Session 1 (continued, 2026-07-03) — Phases 0–2 complete

- **Phase 0 complete.** Forensic evidence frozen in
  `tmp/fleet-plugin-currency/evidence/` (cache trees, registries, config +
  hooks, Codex config, marketplace caches, remote release/master truth).
- **Phase 1 + Phase 2 complete.** This PR lands the two curated research docs:
  `research/semantics.md` (resolution mechanics + H1–H7 verdicts) and
  `research/fleet-audit.md` (fleet × plugin × surface matrix). The
  `tmp/.../drafts/` files are superseded.

- **Finding A — the release pipeline is stalled fleet-wide (load-bearing).**
  release-please opens a green release PR on every master push, authored by the
  `livespec-pr-bot` GitHub App, but the `auto-enable-merge` workflow's gate is
  `contains(["thewoolleyman"], pull_request.user.login)` — the App bot is not in
  it, so auto-merge is SKIPPED on every release PR and each sits open until a
  human merges (historically `mergedBy=thewoolleyman`). That manual merge lapsed
  after ~Jun 30/Jul 1. Consequence: the self-heal fix (`860f671`, Jul 1) is in
  the OPEN orchestrator release PR #228 and in NO release; the latest release
  (v0.4.0 = `06e3e080`) predates it. "Latest release" was therefore the BROKEN
  build, and only master carried the fix — inverting the plan's invariant.

- **Finding B — the currency mechanism is non-uniform and lagged (the console
  failure).** Only 4 of 10 governed repos run the SessionStart `just
  ensure-plugins` updater, and even those carry a built-in one-session lag
  (`claude plugin update` = "restart to apply"). `ensure-plugins` tracks
  marketplace **master** (github default branch), not release tags. The console
  has NO updater hook at all, so its orchestrator active-snapshot pointer never
  moved off the stale `06e3e080` (pre-self-heal) build installed Jun 30 — while
  the fixed build sat unreferenced in cache.

- **H1–H7 verdicts (one-liners).**
  - H1 (one-session lag) — **CONFIRMED.** Update applies only at next session.
  - H2 (stale activation despite fetch) — **PARTIAL / not primary.** Console
    never fetched (no updater); frozen pointer is H5 + H1, not a broken flip.
  - H3 (scope shadowing) — **REFUTED.** No livespec plugin has a user-scope entry.
  - H4 (master-vs-release mismatch) — **CONFIRMED (deepest).** ensure-plugins
    tracks master; pin discipline targets release tags; pipeline stalled so
    master ≫ latest release, and the fix is master-only.
  - H5 (fleet non-uniformity) — **CONFIRMED.** Only 4/10 repos run the hook;
    the console is not one.
  - H6 (unmanaged surfaces) — **CONFIRMED for Codex; REFRAMED for Fabro.** Fabro
    uses a fresh clone + pinned docker image + uv pins (no host plugins); Codex
    is host-wide with no updater/gate.
  - H7 (cache hygiene) — **PARTIAL/CONFIRMED.** `.in_use/<pid>` sweep retains
    many snapshots; semver dirs are content-ambiguous (manifest-version trap).

- **Exact console causal chain.** console has no SessionStart `ensure-plugins`
  hook → its `livespec-orchestrator-beads-fabro` active-snapshot pointer was set
  at install time (Jun 30) to `06e3e080` = the v0.4.0 release-tag commit, which
  PREDATES the self-heal → nothing ever ran a scoped `update` to move the
  pointer → `/next` resolved `06e3e080` → that build's `_bootstrap.py` lacks
  `_self_heal_credentials()` → died with the raw `Access denied` the self-heal
  exists to prevent, while a fixed `0.4.0`-with-self-heal build sat in cache but
  unreferenced by any active pointer.

- **openbrain is intentionally `posture: "pinned"`.** The adopter repo's stale
  snapshot is a deliberate adopter choice, not a defect — RESPECT it; it is out
  of scope for the currency fix and must not be "helpfully" updated.

### Session 1 (continued) — release train unstalled; Phase 3 filed (2026-07-03 ~05:30–05:45Z)

- **Release train unstalled (maintainer directive: "merge whatever is
  stalled").** The four stalled release PRs were each verified green — every
  check rollup carried the smoking-gun `enable-auto-merge: SKIPPED` step — and
  merged: **livespec #733 → v0.6.0**, **livespec-orchestrator-beads-fabro #228 →
  v0.5.0** (carries the credential self-heal `860f671`), **livespec-driver-claude
  #58 → v0.2.1**, **livespec-driver-codex #25 → v0.3.0**. All four releases
  confirmed cut and marked Latest.
- **Two more stalled release PRs surfaced in the fleet scan (same cause):**
  `livespec-orchestrator-git-jsonl` #156 → 0.4.0 and `livespec-dev-tooling` #224
  → 0.31.1. Both were armed with rebase auto-merge (land on green) rather than
  merged by hand; confirm they landed and cut their releases (next-action item 4).
- **Fan-out is unaffected — the stall is RELEASE-PR-specific.** bump-pin PRs are
  also App-authored, yet they arm their OWN auto-merge (evidence:
  `livespec-runtime` #111, "bump livespec pin to v0.6.0", automerge=ON). Only
  release-please's release PRs hit the allowlist gate.
- **Root cause of the stall (established + first-hand verified).**
  `auto-enable-merge.yml`'s gate is `contains(["thewoolleyman"],
  pull_request.user.login)` — only the maintainer. Release PRs are authored by
  the fleet's own GitHub App `app/livespec-pr-bot`, which is not in the
  allowlist, so auto-merge is SKIPPED on every release PR. The workflow header
  documents bot PRs as out-of-scope by design (it predates release-please
  authoring via the App). Every past release shipped only via manual maintainer
  merges (author = App, mergedBy = `thewoolleyman`); that manual cadence lapsed
  after ~Jun 30 with ZERO red anywhere — no check asserts that a green release PR
  must not age open.
- **Phase 3 work-items filed** (all tenants probed present; the epic had zero
  children before). Core children under `livespec-c1k9`:
  - `livespec-c1k9.1` (P0) — auto-merge allowlist fix + fleet audit.
  - `livespec-c1k9.2` (P1) — one-session-lag design gap.
  - `livespec-c1k9.3` (P1) — staleness gate.
  - `livespec-c1k9.4` (P1) — Codex host-wide surface updater/gate.
  - `livespec-c1k9.5` (P2) — semver cache-dir content-ambiguity trap.

  Cross-tenant (filed in each owning repo, descriptions referencing the core
  epic):
  - `livespec-console-beads-fabro-vfd` (P0) — console SessionStart hook +
    active-pointer refresh (the concrete trigger repo).
  - `bd-ib-mwz` (P1) — Fabro sandbox docker-image pin (orchestrator tenant).
  - `livespec-driver-claude-nm9` / `livespec-driver-codex-045` /
    `livespec-dev-tooling-6da` / `livespec-runtime-m2u` (P1) — SessionStart
    `ensure-plugins` hook adoption.
- **Research docs landed on master via PR #788** (`research/semantics.md` +
  `research/fleet-audit.md`) — the curated Phase 0–2 findings referenced above.
- **Phase 4 design draft delivered + landed.** Design draft delivered by the
  `phase4-design` agent and landed via this PR (`research/design-draft.md`,
  banner-marked DRAFT); maintainer AFK at review time, so the three open
  decisions (§"The next action" item 1) remain PENDING; gate held (no
  implementation dispatched from the draft).

### Session 1 (continued) — D1 premise corrected (2026-07-03)

- Maintainer challenged the "tag-tracking is unsatisfiable" claim; a Claude Code
  docs check refuted it (catalog plugin-entry sources support `ref`+`sha`);
  correction landed in `research/design-draft.md`; scratch verification of
  `git-subdir`+`sha` dispatched; the three decisions still pending.

### Session 1 (continued) — Phase 4 design review PASSED (2026-07-03)

- Design review passed with all three recommendations accepted: D1 = sha-pin
  to releases, D2 = warn + `LIVESPEC_CURRENCY_GATE=fail` lever on Unknown,
  D3 = defer the host-level pre-session sweep. Decisions recorded via this PR.

### Session 1 (continued) — sha-pin REFUTED; D1 revised; Codex scope added (2026-07-03)

- **Sha-pin refuted empirically** (Claude Code 2.1.199; log
  `tmp/fleet-plugin-currency/scratch/experiment-log.md`) → maintainer revised D1
  to **verify-release-branch-ref-first** with a **master-HEAD fallback**, and
  extended the invariant's scope to **Codex** plugin versioning. The
  `ref-pin-experiment` was dispatched (log target
  `tmp/fleet-plugin-currency/scratch/ref-exp/`), and the upstream
  docs-vs-behavior report work-item was filed under the epic. See §"The next
  action" item 1 for the full verdict + decision.
- **Side observation (correct-by-design upstream behavior; no action taken).**
  During the sha-pin experiment window, Claude Code's own reconcile (NOT the
  experiment) auto-pruned the **DELISTED** `livespec-impl-plaintext`
  plugin+marketplace registration — the upstream catalog no longer lists it,
  though the `openbrain` settings still enable it. The pre-prune registry
  snapshot is preserved at
  `tmp/fleet-plugin-currency/scratch/before/installed_plugins.json`.
