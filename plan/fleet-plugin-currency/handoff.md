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

1. **⚑ Maintainer decision PENDING — merge the four stalled release PRs.** The
   release pipeline is stalled fleet-wide (Finding A): each plugin repo has an
   open, unmerged release PR authored by the `livespec-pr-bot` GitHub App that
   the `auto-enable-merge` workflow refuses to auto-merge (App bot not in the
   `thewoolleyman` allowlist). The overseer session is asking the maintainer to
   merge them: **livespec #733 → 0.6.0, orchestrator-beads-fabro #228 → 0.5.0,
   driver-claude #58 → 0.2.1, driver-codex #25 → 0.3.0.** Until they merge,
   "latest release" is not even a currency floor.
2. **Phase 3 — file defect child work-items under `livespec-c1k9`.** Each
   independent defect that permits the staleness class becomes a child (same
   tenant in core; cross-tenant items filed in their owning repos and
   prose-linked, per the fleet pattern):
   - **Release-pipeline auto-merge allowlist excludes the `livespec-pr-bot`
     GitHub App** — fleet-wide, one work-item per plugin repo (livespec,
     orchestrator-beads-fabro, driver-claude, driver-codex).
   - **SessionStart `ensure-plugins` hook missing** in
     `console` / `dev-tooling` / `driver-claude` / `driver-codex` / `runtime`.
   - **One-session-lag design gap** — `claude plugin update` applies only at the
     next session; the current session always runs the prior fetch.
   - **Codex host-wide surface has no updater/gate** (`~/.codex/config.toml`, no
     SessionStart-hook analogue).
   - **Fabro sandbox docker-image pin outside `bump-pin` discipline** —
     `sha-ea684ad` is a floating master build the v013 pin_autodiscovery formats
     do not cover; orchestrator tenant.
   - **Semver cache-dir content-ambiguity trap** — post-release master commits
     reuse the same `plugin.json.version`, so an `install` lands in a semver dir
     that collides last-writer-wins with the release-tag content; only SHA-named
     dirs are content-stable.
3. **Phase 4 — design the guarantee** per `research-plan.md` §"Design
   constraints". **NOTE the invariant needs re-examination.** The research
   plan's stated invariant ("every session runs the LATEST RELEASED pin") was
   UNSATISFIABLE during the stall: the latest release (orchestrator v0.4.0 =
   `06e3e080`) was the BROKEN, pre-self-heal build, and tracking **master** is
   what actually delivered the fix to the repos that ran `ensure-plugins`. The
   Phase 4 design must therefore **fix the release pipeline FIRST** (auto-merge
   the App-bot release PRs so "latest release" becomes trustworthy and current),
   and only THEN decide release-tracking vs master-tracking for the currency
   mechanism. Do not design a release-tracking gate on top of a stalled
   pipeline.

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
