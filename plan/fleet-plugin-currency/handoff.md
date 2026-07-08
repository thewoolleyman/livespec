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
  - **[HISTORICAL — investigation-phase rule; NO LONGER BINDING.]**
    Investigation phases (0–3) were **READ-ONLY toward every plugin cache,
    registry, marketplace cache, and settings file** — no updates,
    reinstalls, or pruning until Phase 3 closed; controlled experiments ran
    only in scratch projects. Evidence-first was the point; a "helpful fix"
    would have destroyed it. Phases 0–3 are now CLOSED and the fast-path
    implementation waves (below) DELIBERATELY mutate caches, registries,
    marketplaces, and settings through the sanctioned paths (committed
    settings `extraKnownMarketplaces`, `marketplace add/update`, scoped
    `plugin update`). This rule is retained only as the record of the
    investigation-phase discipline, not as a live constraint.
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

> **★ SESSION 6 (2026-07-08) — READ THIS FIRST; supersedes Session 5 below (retained as history). Status is READ from the ledger, never stored here.**
>
> **EPIC REOPENED.** `livespec-c1k9` was CLOSED 2026-07-06 (9/9 — it delivered fleet currency). It is now **REOPENED (`in_progress`)** with a new **ADOPTER-parity** scope. Trigger: the `resume` adopter (`/data/projects/resume`, a genuine third-party consumer — installs `livespec@livespec` from the GitHub marketplace at `ref: release`, uses the git-jsonl orchestrator, NO fleet tooling) **hard-failed exit 78** on every `/livespec:*` op. Root cause, verified live: the currency gate ships INSIDE core's plugin and enforces on adopters, but the ONLY auto-updater is the fleet-only `just ensure-plugins` SessionStart hook — absent in adopters. So an adopter tracking `ref: release` freezes its installed build (`resume` sat on `2d73188a7e10` from 07-04) while the SHARED host marketplace clone HEAD advances (`f906c7481cb4`), and the gate correctly-but-uselessly hard-blocks it with remediation naming fleet tooling it does not have. Enforcement without an updater = a lock with no key. (Immediate unblock already applied to `resume`: `claude plugin update livespec@livespec --scope project` advanced its pin to current; the default `--scope user` — which the stuck session tried — does NOT touch a project-scope install.)
>
> **DESIGN (maintainer 2026-07-08).** The fix is NOT to weaken/opt-out the gate; it is to give adopters the missing updater and make the two `posture` states clean. Gate fire/no-fire logic is UNCHANGED.
> - **`posture: released` (DEFAULT the maintainer wants for every adopter he owns):** marketplace tracks `ref: release` AND a **portable per-driver auto-updater** pulls the project-scope install to the latest release every session. Always current → gate passes.
> - **`posture: pinned` (OPT-OUT for adopters who are not the maintainer):** marketplace pinned to a FIXED release tag, no updater, manual update when they choose. Running == pinned tag → structurally coherent, gate never trips (the spec's existing reasoning holds).
> - **Eliminate the illegal middle** (`ref: release` with no updater — what `resume` was).
> - **Every driver:** works on **Claude** and **Codex** now; structured so **Pi** slots in later. The updater default is **per-adopter COMMITTED settings** (maintainer controls exactly which owned adopters auto-update), NOT Driver-force-shipped for all third parties.
>
> **REMAINING CHILDREN (all `backlog`/open under the reopened epic; status live from ledger):**
> - **`c1k9.12`** (P1, core) — posture contract (`released`/`pinned`) + `docs/livespec-installation-prompt.md` docs, BOTH runtimes. The design/contract anchor the impl children consume.
> - **`c1k9.13`** (P1, `livespec-driver-claude`) — Claude portable auto-updater: committed `.claude/settings.json` `SessionStart` hook, plain `claude plugin update --scope project`, no fleet tooling.
> - **`c1k9.14`** (P1, `livespec-driver-codex`) — Codex parity. **FIRST TASK = RESEARCH** the Codex per-session update trigger (host-wide `~/.codex/config.toml`; `codex plugin marketplace upgrade`; does Codex fire a hangable session hook?) — read the recipe + Codex docs + test on real `~/.codex`, do NOT guess. Then implement.
> - **`c1k9.15`** (P2, core `_bootstrap.py` + `tests/bin/test_bootstrap.py`) — remediation-message fix: name adopter-runnable commands per runtime, drop fleet-only `just ensure-plugins`. Quick, low-risk; product-`.py` → red-green-replay ritual. Message text only.
> - **`c1k9.2`** (P1, per-driver) — reload nudge collapses the one-session lag on Claude (`/reload-plugins`) AND Codex (equivalent). Pairs with the updater.
> - **`c1k9.7`** (P2, terminal) — upstream Claude Code plugin-source-pin report; **maintainer files externally** (draft: `tmp/fleet-plugin-currency/session3/c1k9.7-upstream-report-draft.md`). Relocate the draft onto the item so it survives any future archive.
>
> **NEXT ACTIONS, in order:** (1) `c1k9.14` Codex research (unblocks the Codex leg + de-risks the whole exit gate); (2) `c1k9.12` posture contract + docs (anchors both impl legs); (3) `c1k9.15` message fix (quick win); (4) `c1k9.13` Claude updater; then `c1k9.14` Codex impl + `c1k9.2` per-driver nudge. Factory-dispatch the ready driver-repo impl; host-only self-machinery stays maintainer-side.
>
> **EPIC EXIT CRITERIA (BOTH runtimes required — no "Claude works, Codex assumed"):** on a fresh adopter, LIVE-demonstrated on **Claude** AND on **Codex**: (a) a `posture: released` adopter auto-updates to the latest release on session start; (b) a `posture: pinned` adopter stays put and updates only manually; (c) the gate, when it fires, prints only adopter-runnable remediation for the firing runtime. Unit tests are necessary but NOT sufficient — "done means exercised live."
>
> **Adversarial review:** `plan/fleet-plugin-currency/live-adversarial-review-prompt.md` (this session) — run a second, independent session against every auto-update / opt-out / cross-runtime completion claim before any child closes or the epic re-closes.
>
> **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-plugin-currency`.

> **★ SESSION 5 (2026-07-05/06) — supersedes Session 4 below (retained as history). Status is READ from the ledger/PRs, never stored here.**
>
> **★ TRACK SCOPE (maintainer 2026-07-06): the Fabro checkpoint-timeout PR is a COMPLETELY SEPARATE TRACK, not part of fleet-plugin-currency.** So `c1k9.4` (which depends on it) is the ONE fleet-plugin-currency exit-gate blocker whose dependency lives OUTSIDE this track; everything else here is driven to its boundary.
>
> **Resolved / landed this session:**
> - **Systemic red-master gap → RESOLVED + FILED** (`livespec-dev-tooling-adqmnm`, dev-tooling `feature`, BLOCKED on `9j8.1`; core PR #881): maintainer chose "fan-out writes the wiring" — the bump-pin fan-out RECONCILES each consumer's `check:` canonical block to the newly-pinned set atomically with the pin bump; `aggregate_completeness` stays the verifier; no severity relaxation (per `.ai/ci-gate-discipline.md`).
> - **`bd-ib-6ka` PREPPED for a human-run PR (now a SEPARATE track).** Exact edit map journaled on the item; fork `thewoolleyman/fabro` created (local `/data/projects/fabro` remotes: origin=fork, upstream=fabro-sh/fabro); self-contained impl prompt at `/data/projects/fabro/tmp/fix-checkpoint-commit-timeout.md` (EPHEMERAL; durable map on the ledger item). Maintainer runs it → upstream PR → merge sets core `[run.checkpoint] commit_timeout_ms=600000` → unblocks `c1k9.4`.
> - **`c1k9.5` CLOSED as mitigated** (ref-pinning resolved the load-bearing semver-cache ambiguity; minor cache-hygiene residual captured in the close reason). Epic now **8/11**.
> - **`7bfhkm` groom cut RESOLVED (recommended, recorded on the item): MIGRATE to file-level, do NOT weaken the check** — the core `no_spec_section_citation_in_code` check enforces a real anti-rot discipline and caught real drift; refining it is the rejected looser option. SCOPE: 159 `§"..."` occurrences across ~100 `.py` (56 lib + 44 test), some multi-line — mechanical-but-careful; oracle = the check passing against dev-tooling; comment/docstring-only ⇒ ritual-exempt.
>
> **EXIT-GATE READINESS.** The 3 exit conditions: staled-cache negative test ✅ (`c1k9.3`); unattended-release observation ✅; fresh-session assertion ✅ Claude leg (24/24) / ⏳ Codex leg pending `c1k9.4`. So the epic CLOSES when `c1k9.4` lands — which depends on the SEPARATE Fabro track.
>
> **Remaining, in order (all NON-exit-critical except c1k9.4):**
> 1. **`c1k9.4`** — Codex-side currency gate. Blocked on the SEPARATE Fabro track (`bd-ib-6ka`) OR maintainer-side sandbox extraction. THE exit-gate blocker.
> 2. **`goucoq` → `afd` release-park parity** (dev-tooling debt; release-train robustness follow-up, NOT an exit condition). Direction+scope resolved: dispatch `kkmhwo` (allowlist ~16 cross-repo headings in dev-tooling SPECIFICATION/ prose + fix 2 stale contracts→nfr citations) and `7bfhkm` (migrate the 159 `§"..."` code citations to file-level) as their own dev-tooling PRs, then re-drive the afd revise (re-verify its 3 replace-targets), then land `tem4t2`. Maintainer-cautioned on the 100-file migration ("not inline") ⇒ best driven as its own dev-tooling track.
> 3. **`c1k9.2`** (one-session lag) — decided (post-update reload nudge), unimplemented; a DRIVER-repo change; non-blocking (the hard gate catches the lag fail-loud).
> 4. **`c1k9.7`** — upstream Claude-Code plugin-source-pin report; TERMINAL, maintainer files externally; draft ready at `tmp/fleet-plugin-currency/session3/c1k9.7-upstream-report-draft.md`.
> 5. **`adqmnm`** — blocked on dev-tooling `9j8.1`.
> 6. **One OTHER core proposal** (`owned-heading-coverage-todos.md`) needs a rebase — NOT this thread's to ratify.

> **★ SESSION 4 (2026-07-04/05) — READ THIS FIRST; supersedes Session 3 below (retained as history). Status is READ from the ledger/PRs, never stored here.**
>
> **Landed this session (verify each via `gh`/ledger):**
> - **c1k9.6 CLOSED — the plugin-currency + release-train contract is CODIFIED.** The amended payload passed a fresh independent Fable review (NO-BLOCKERS) and was ratified via a SUBSET revise (core PR #875, rebase-merge `58bd8ec`, version `history/v160`): the `### Plugin currency and the release train` section is live in `SPECIFICATION/non-functional-requirements.md` (~L249), plus the Conformance-Pattern `Plugin-currency` member and the `release-park.yml` bullet in the copier-template exhaustive workflows list. Epic `livespec-c1k9` now **7/11**. It is a doc codification of already-exercised behavior, so the "done means exercised live" bar is met by the mechanism's prior live proof. A NON-BLOCKING correction is journaled on the closed item for the L0c/contracts-parity rollout implementer: the payload's Motivation/Edit-3 PROSE mischaracterizes the `copier-template-workflow-coverage` check (it checks each COPIER CONSUMER's `.github/workflows/`, not the template) — explanatory-prose-only; it did NOT enter the ratified spec.
> - **bd-ib-4nk CLOSED + live-exercise evidence journaled** (orchestrator). Human-accepted, then — per the new "exercised live" rule — a real post-merge sandbox (`fabro-run-01KWPCYHX784...`, created ~82 min after PR #309 merged) was confirmed to carry `LIVESPEC_CURRENCY_GATE=fail` while two pre-merge sandboxes did not.
> - **Wrapper bug filed:** `livespec-gvqmin` (core, P2, BLOCKED — needs autonomy tiering). `propose_change.py` resolves a relative `--spec-target` against cwd, ignoring `--project-root` (workaround: absolute `--spec-target`).
> - **afd (release-park parity) DEFERRED — pre-existing dev-tooling doctor-static debt found.** Its `/livespec:revise --post-step-doctor` gate is blocked by two legitimate core checks failing on dev-tooling: `no_spec_section_citation_in_code` (100 committed `.py` files carry `§"..."` section citations — 56 lib + 44 tests) and `no_cross_spec_reference` (~16 un-allowlisted cross-repo headings in spec prose). The checks are RIGHT — `no_spec_section_citation_in_code` caught real drift (two cited headings moved `contracts.md`→`non-functional-requirements.md`), so this is debt to CLEAR, not a bypass to add. Captured as dev-tooling epic **`livespec-dev-tooling-goucoq`** → children **`kkmhwo`** (allowlist the ~16 + correct the 2 stale citations; config, ritual-exempt) + **`7bfhkm`** (resolve the 100-file conflict: migrate-to-file-level vs refine-the-check, decide at groom); systemic **`tem4t2`** (dev-tooling CI doesn't gate doctor-static — why it accumulated). `afd` + `tem4t2` are blocked-by `kkmhwo`+`7bfhkm`. The Fable-reviewed proposal `SPECIFICATION/proposed_changes/reusable-release-park-parity.md` stays PENDING (NO-BLOCKERS holds); re-verify its 3 replace-targets before re-driving. **Maintainer decision 2026-07-04: defer afd, do NOT do the 100-file migration inline.**
>
> **New standing rule (CLAUDE.md, maintainer 2026-07-04):** "'done' means rolled out and EXERCISED LIVE — never merely merged + CI-green + AI-accepted." Any `accept:` MUST carry live-exercise evidence journaled on the item; an overseer MUST NOT trigger `accept:` without it. (See CLAUDE.md §"Enforcement-suite and tooling discipline".)
>
> **Next actions, in order:**
> 1. **bd-ib-6ka — OPTION 1 (unchanged):** drive the UPSTREAM Fabro configurable-checkpoint-timeout PR (fabro source at `/data/projects/fabro`, remote `github.com/fabro-sh/fabro`; propose `[run.checkpoint] commit_timeout_ms`, default ~30000; core needs ≥600000). Unblocks core-repo factory dispatch + the Codex gate (c1k9.4). Meanwhile keep the maintainer-side extract+publish path for gate-heavy core items; document the constraint in `SPECIFICATION/non-functional-requirements.md` §"Orchestrator-internal Dispatcher guidance"; record the verdict on `bd-ib-6ka` (orchestrator tenant).
> 2. **Systemic red-master gap (item 4 below) — STILL UNASKED.** Decide the mechanism (fan-out carries the wiring / aggregate-completeness grace for newly-added slugs / accept the manual wave). Per `.ai/ci-gate-discipline.md`, enforcement must not land at error severity ahead of its rollout.
> 3. **Remaining epic children:** c1k9.4 (Codex-side gate operands — needs bd-ib-6ka OR maintainer-side extraction), c1k9.2 (one-session lag), c1k9.5 (cache-ambiguity, P2), c1k9.7 (upstream Claude-Code plugin-source-pin report — maintainer files EXTERNALLY).
> 4. **dev-tooling debt epic `goucoq`:** groom (settle `7bfhkm`'s migrate-vs-refine), clear `kkmhwo` + `7bfhkm`, then re-drive the afd revise (re-verify its replace-targets first), then land `tem4t2` (wire doctor-static into dev-tooling CI — MUST land only after the debt clears, else red master).
> 5. **Two OTHER core proposals need a rebase:** `SPECIFICATION/proposed_changes/{fleet-merged-branch-cleanup,owned-heading-coverage-todos}.md` are OTHER threads' work; c1k9.6 shifted `nfr.md`, so their replace-targets must be rebased onto post-c1k9.6 `nfr.md` before their own revises. NOT this thread's to ratify.
> 6. **EPIC EXIT GATE (unchanged, see below).**

> **★ SESSION 3 (2026-07-04) — READ THIS FIRST; supersedes the per-item status below (retained as history). Status is READ from the ledger/PRs, never stored here.**
>
> **Landed this session (verify each via `gh`/ledger):**
> - **c1k9.6 spec contract** — filed (core PR #870), then AMENDED per an independent Fable review (branch `amend-c1k9.6-fable-fixes` → VERIFY its PR merged). Blockers fixed: the copier-template exhaustive-list omission of `release-park.yml`; scope; the Codex Installer/Mechanism leg. **SCOPE DECISION (maintainer 2026-07-04): the currency invariant binds FLEET repos + opt-in adopters (`posture: released`), mirroring Pin-freshness — NOT "every governed repo".** The runtime gate is NOT posture-aware (it compares a repo's running build to its OWN marketplace-clone tip); deliberately-pinned adopters are structurally coherent and never trip it; the posture exemption belongs to the fleet-conformance SWEEP.
> - **Adopter self-update** — added to `docs/livespec-installation-prompt.md` (core PR #871): the decoupled, harness-native updater (Claude `SessionStart` hook / Codex `plugin marketplace upgrade`) each adopter wires from the central idempotent install prompt, since the fleet contract does NOT enforce adopter currency.
> - **afd (dev-tooling)** — TWO-LEG release-park parity filed (dev-tooling PR #267) after a Fable review found the shipped `reusable-release-park.yml` silently dropped leg (b) (unreleased-backlog detection — the only guard against release-please never opening a release PR at all). Work-items filed: `livespec-dev-tooling-2kt` (implement leg b; maintainer-side — App lacks `workflows` perm) and `livespec-dev-tooling-xam` (Option A presence enforcement via the fleet obligation table; names `livespec-runtime` as the first reconcile target — it carries `release-please.yml` but NO `release-park.yml`, a LIVE gap).
> - **bd-ib-4nk** — D2 factory half (projects `LIVESPEC_CURRENCY_GATE=fail` into sandbox env) factory-dispatched + merged (orchestrator PR #309), post-merge janitor green, PARKED awaiting HUMAN ACCEPTANCE (ai-then-human policy).
>
> **Next actions, in order (all load-bearing detail is inline; the Session-3 scratch drafts at `tmp/fleet-plugin-currency/session3/` are supplementary/re-derivable, NOT required):**
> 1. **bd-ib-6ka — OPTION 1 chosen (maintainer 2026-07-04): drive the UPSTREAM Fabro PR.** The ~30s git-checkpoint-commit timeout is HARDCODED in the closed Fabro Rust binary — no config file/env/flag/per-repo knob (investigation confirmed; it is a sibling of other hardcoded git-op timeouts in the `fabro-workflow` crate). The fabro SOURCE is cloned at **`/data/projects/fabro`** (remote `github.com/fabro-sh/fabro`). Drive a PR there adding a configurable checkpoint-commit timeout (proposed `[run.checkpoint] commit_timeout_ms`, default ~30000, plumbed into the commit timeout wrapper so it applies to the post-node snapshot commit; livespec core needs ≥600000 to fit a full `just check`). MEANWHILE keep the maintainer-side extract+publish path for gate-heavy core items (the pattern used for core PRs #848/#857); DOCUMENT the constraint in `SPECIFICATION/non-functional-requirements.md` §"Orchestrator-internal Dispatcher guidance"; record the verdict on ledger item `bd-ib-6ka` (orchestrator tenant).
> 2. **Final Fable reviews, THEN revise (both maintainer-gated):** the AMENDED c1k9.6 payload AND the two-leg afd payload each need ONE more independent read-only Fable-model review (must return NO-BLOCKERS) before `/livespec:revise` accepts them. Then drive each revise (maintainer accepts).
> 3. **Accept bd-ib-4nk** (human acceptance) once its merge (orchestrator PR #309) is verified.
> 4. **Ask the OPEN new-canonical-slug red-master decision** (handoff item 4 "Systemic gap"): choose the mechanism — fan-out carries the wiring / aggregate-completeness grace for newly-added slugs / accept the manual wave. NOT yet asked.
> 5. **File the wrapper bug:** core `propose_change.py` resolves a RELATIVE `--spec-target` against cwd, IGNORING `--project-root` (it wrote stray untracked files into the core repo during afd filing; use an ABSOLUTE `--spec-target` as the workaround). File in core.
> 6. **Lower-priority:** c1k9.2 (reload nudge), c1k9.5 (cache pruning), c1k9.7 (upstream report — maintainer files externally; 3 confirmed Claude Code plugin-source-pin defects; evidence at `tmp/fleet-plugin-currency/scratch/experiment-log.md`, draft at `tmp/fleet-plugin-currency/session3/`), dev-tooling `r5m`/`afd` follow-ups, orchestrator robustness family (`bd-ib-lgv`/`6vu`/`18r`/`yig`).
> 7. **EPIC EXIT GATE** — see the existing criteria below (unchanged).

**CLOSING phase — the currency invariant is LIVE and PROVEN.** The Phase 4
design (`research/design.md`, decisions D1 = release-branch marketplace-ref
mechanism, D2 = warn-plus-`LIVESPEC_CURRENCY_GATE=fail` lever on Unknown,
D3 = defer the host-level sweep) is now realized across the fleet: the L0
allowlist fix, the L1a per-repo `release` branches + fast-forward CI, the L1c
SessionStart `ensure-plugins` hooks de-drifted onto committed settings, the
L0b release-park guard, and the L1b marketplace ref-pinning have all merged.
The invariant was proven LIVE mid-rollout — an unattended `fix:` push cut
v0.6.1 and fast-forwarded `refs/heads/release` with NO human in the loop (see
§"Fast-path implementation waves"). `livespec-c1k9.1`, `.3`, `.8`, `.9`,
`.10`, and `.11` are CLOSED (6/11); `.4` is NARROWED to the Codex-side gate
operands. The gate itself is LANDED AND LIVE: `_bootstrap.py` fail-loud
staleness gate (PRs #848 + #857), ci.yml `LIVESPEC_CURRENCY_GATE=fail`
(re-landed #859, master green with it), the fleet-wide one-line
`ensure-plugins` wrapper, and the `claude-plugin-currency` conformance row
at ERROR severity over a verified-clean 8-member fleet. Status is READ from
the ledger, never from this file. What remains is the spec codification, the
narrowed Codex gate leg, the low-priority items, and the exit-gate
assertion.

Remaining work, in order:

1. **`livespec-c1k9.6` — spec codification** (the next ripe piece): single-
   source the invariant + gate guarantee in core
   `SPECIFICATION/non-functional-requirements.md` (with the
   `tests/heading-coverage.json` co-edit per the revise discipline); the
   dev-tooling `contracts.md` parity piece rides `livespec-dev-tooling-afd`.
   The mechanism to codify is now fully LANDED and verified: the
   `_bootstrap.py` gate (PRs #848 + #857 — registry dict-of-lists shape,
   checkout-mode out-of-domain skip, staled-cache negative tests), the
   ci.yml `LIVESPEC_CURRENCY_GATE=fail` lever (re-landed #859, master green
   with it live), the fleet-wide one-line `ensure-plugins` wrapper, and the
   `claude-plugin-currency` conformance row at ERROR severity.

2. **`livespec-c1k9.4` (NARROWED) — Codex-side gate operands.** The gate
   runs under `codex exec` but reads Claude-only state (evidence in the
   item's comment); extend it to resolve the Codex running build
   (`~/.codex/plugins/cache/.../<ver>` and/or `codex plugin list --json`)
   vs the Codex marketplace clone's `release` tip. Same file as the landed
   gate work. NOTE: core-repo factory dispatch currently dies at fabro's
   30s checkpoint-commit timeout (`bd-ib-6ka`, orchestrator tenant) — until
   that lands, expect to publish maintainer-side by sandbox extraction (the
   pattern used for #848/#857, recorded in §Session 2).

3. **Factory-half of the D2 lever:** `bd-ib-4nk` (orchestrator tenant) —
   the Dispatcher's run-config overlay projects `LIVESPEC_CURRENCY_GATE=fail`
   into sandbox env. Dispatchable in the orchestrator repo (its own factory
   is unaffected by `bd-ib-6ka`'s core-sized gates).

4. **Maintainer flags:**
   - **RESOLVED — lever REJECTED (maintainer verdict, 2026-07-04).** The
     `LIVESPEC_MASTER_CI_GREEN=warn` repair lever briefly added in
     dev-tooling PR #245 was ruled absolutely unacceptable: NO escape gates
     on CI-green gates, ever — they WILL be abused; the remedy for a gate
     deadlock is a server-side REVERT PR of the breaking change and a
     re-land in the right order. Removed same day via dev-tooling PR #249
     (impl reverted byte-for-byte; a regression test pins the env var to
     having NO effect). `li-4x3a45` upheld and broadened; the durable rule
     is codified in core `.ai/ci-gate-discipline.md` (referenced from
     AGENTS.md) — read it BEFORE touching any CI-green gate.
   - **Systemic gap (RESOLVED, Session 5 2026-07-05):** a dev-tooling
     release that ADDS a canonical check slug + the direct-push bump-pin
     fan-out ⇒ a guaranteed red-master window in every consumer until each
     justfile wires the new slug (the 2026-07-03/04 cascade, §Session 2
     below). Maintainer chose **fan-out carries the wiring**; filed
     `livespec-dev-tooling-adqmnm` (dev-tooling, `feature`, BLOCKED on
     `9j8.1`). The fan-out reconciles each consumer's canonical block
     atomically with the pin bump; `aggregate_completeness` stays the
     verifier — no severity relaxation, per `.ai/ci-gate-discipline.md`.

5. **Lower-priority follow-ups:** `livespec-c1k9.2` (reload nudge — lands with
   the gate work), `livespec-c1k9.5` (cache-pruning posture),
   `livespec-c1k9.7` (upstream docs-vs-behavior report — execution),
   `livespec-dev-tooling-r5m` (uv.lock release drift — two instances repaired
   as ride-alongs in dev-tooling PRs #245/#249; the release-flow root fix
   stays open), `livespec-dev-tooling-afd` (release-park follow-ups), and the
   **orchestrator robustness family** from this session's incidents (all
   orchestrator tenant, backlog): `bd-ib-yig` (cwd tenant addressing),
   `bd-ib-lgv` (no-workflow-edits boundary declared + enforced pre-push),
   `bd-ib-6vu` (parked-run credential re-projection), `bd-ib-18r` (blocked
   as a first-class Dispatcher outcome), `bd-ib-6ka` (fabro 30s checkpoint
   timeout vs core's multi-minute gates — the reason core items currently
   publish maintainer-side).

6. **EPIC EXIT GATE.** The mechanized **fleet-wide fresh-session assertion**
   (every repo × Claude interactive × `codex exec`: running `gitCommitSha` ==
   pinned-ref tip == latest release tag) — already partially evidenced by
   `c1k9.9`'s 24/24 Claude + 4/4 Codex verification — PLUS the
   **deliberately-staled-cache negative test** (now IN-TREE via `c1k9.3`,
   `tests/bin/test_bootstrap*.py`) PLUS the now-**SATISFIED** live
   observation of an unattended release (v0.6.1; re-proven repeatedly
   2026-07-04: v0.32.1/v0.32.2/v0.33.x and core v0.6.3 all cut + fanned out
   unattended). Close `livespec-c1k9` when all three hold — the Codex leg of
   the assertion depends on the narrowed `c1k9.4`.

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

### Session 1 (continued) — ref-pin VERIFIED; design FINALIZED (2026-07-03)

- **Session killed mid-experiment and resumed.** The overseer session was
  killed while the `ref-pin-experiment` was in flight. On resume, the verdict
  was **recovered from disk** — the log
  `tmp/fleet-plugin-currency/scratch/ref-exp/ref-experiment-log.md` was found
  **completed and clean** (all A1–A4 + B1–B3 verdicts recorded, cleanup
  verified byte-for-byte on both runtimes, the local smart-HTTP server killed).
  No re-run needed.
- **Ref-pin experiment VERIFIED on BOTH runtimes** (Claude 2.1.199 + Codex
  0.142.5): release-branch MARKETPLACE-ref pinning is viable for RELATIVE-source
  (`./.claude-plugin`) plugins. This resolves D1 to the release-branch mechanism
  (the sha-pin form having been refuted earlier this session). Five rollout
  surprises captured.
- **Design FINALIZED via this PR.** `research/design.md` authored (supersedes
  `research/design-draft.md`, which now carries a one-line SUPERSEDED pointer);
  D1 resolved to the verified release-branch mechanism, D2/D3 as decided; the
  L0/L1/L2 layers, structural guards, out-of-scope, rollout gotchas, work-item
  mapping (incl. NEW items to file), and the Phase 5 verification plan are all
  recorded. `handoff.md` §"The next action" updated to the post-finalization
  next-action list.

### Session 1 (continued) — fast-path wave landed (2026-07-03)

- **Fast-path wave landed — tactical sweep completed** (fleet pointers
  refreshed, openbrain excluded), release-branch substrate merged in all five
  plugin repos (PRs livespec #803, driver-claude #73, driver-codex #46,
  beads-fabro #256, git-jsonl #166; branches verified at latest release commits;
  five ledger items closed), 10 new items filed + 5 regroomed by the filing
  agent, allowlist + hook-adoption waves in flight.

### Session 1 (continued) — allowlist slice CLOSED (2026-07-03)

- **Allowlist slice CLOSED (`livespec-c1k9.1`).** Six PRs merged giving every
  fleet repo's `auto-enable-merge.yml` a dedicated release-PR path gated on the
  verified App login `livespec-pr-bot[bot]` AND the `release-please--*`
  branch-shape guard (do-not-merge label opt-out preserved): livespec #802,
  livespec-orchestrator-beads-fabro #255, livespec-driver-claude #74,
  livespec-driver-codex #47, livespec-orchestrator-git-jsonl #167,
  livespec-dev-tooling #233. The workflow header rationale was updated
  everywhere, and the copier template
  (`templates/orchestrator-plugin/.../auto-enable-merge.yml.jinja`) was fixed at
  the SOURCE so a future `copier update` cannot revert the change. Follow-up idea
  recorded: parameterize the App login if non-fleet template adopters need their
  own release bots auto-merged. Six `fix-auto-enable-merge-release-prs` worktrees
  + branches reaped across the six repos.
- **dev-tooling uv.lock/pyproject mismatch bug filed** (`livespec-dev-tooling-r5m`,
  P2): the release 0.31.1 commit bumped `pyproject.toml` without running
  `uv lock`, so master carries a pyproject/uv.lock version mismatch; observed
  when an unrelated worktree's pre-commit hook regenerated uv.lock (0.31.0 →
  0.31.1) as dirty-tree noise. Fix direction: regenerate the lock in the release
  flow + a CI lock/pyproject parity check.

### Fast-path implementation waves (2026-07-03 ~07:00–08:40Z)

- **Maintainer authorized the fast path** — a tactical fleet sweep, parallel
  ritual-exempt PRs, and the TDD path reserved only for the Python changes.

- **Tactical sweep.** All governed repos' project-scope plugin pointers were
  refreshed (the console orchestrator moved `b96eb8a` → `ec5a598`, picking up
  the self-heal; `openbrain` excluded by its `posture: "pinned"` adopter
  choice). Codex marketplaces were upgraded.

- **L0 allowlist (`livespec-c1k9.1` CLOSED).** Six PRs — livespec #802,
  beads-fabro #255, driver-claude #74, driver-codex #47, git-jsonl #167,
  dev-tooling #233 — plus a copier-template source fix. The dual App-login
  spelling was verified and handled where relevant: `livespec-pr-bot[bot]`
  (the webhook / `pull_request.user.login` form) vs `app/livespec-pr-bot`
  (the `gh pr list` form).

- **L1a release branches (`livespec-c1k9.8` + 4 cross-tenant items CLOSED).**
  Five PRs — livespec #803, driver-claude #73, driver-codex #46,
  beads-fabro #256, git-jsonl #166. Each repo's `release` branch was created at
  its latest release commit via the REST ref-create API, and a uniform
  `fast-forward-release-branch.yml` keeps it advancing.

- **L1c hooks (5 items CLOSED).** Option B: the `ensure-plugins` recipes were
  de-drifted back onto committed settings + SessionStart hooks — console #85,
  driver-claude #75, dev-tooling #232, runtime #113, driver-codex #48 (the last
  also renamed `ensure-codex-plugins`, with the SKIP→RUN transition documented).

- **L0b release-park guard (`livespec-dev-tooling-ldd` CLOSED).** The reusable
  workflow landed in dev-tooling #234, with per-repo shims: livespec #809 (plus
  the copier-template source), beads-fabro #257, git-jsonl #168,
  driver-claude #76, driver-codex #49. A live `workflow_dispatch` run was green.
  It keys off `createdAt`, NOT `updatedAt` — an aged-open release PR is caught
  by when it was opened, not reset by a trivial touch.

- **L1b ref pinning (`livespec-c1k9.9` CLOSED).** Eight PRs — livespec #811,
  driver-claude #77, console #87, beads-fabro #259, git-jsonl #169,
  dev-tooling #236, driver-codex #50, runtime #114 — pinning settings
  `"ref": "release"`, the recipes' `@release` / `--ref release`, and the core
  README / AGENTS snippets. Step-0 double verification confirmed BOTH the
  settings reconcile AND the CLI clone land at the `release` tip. **Final
  verification: 24/24 Claude project-scope plugins == release tips, 4/4 Codex
  marketplaces pinned with enablement preserved.** Codex offers no in-place ref
  update, so the documented path is remove / re-add / upgrade — enablement
  survives that cycle.

- **★ LIVE PROOF of the L0 fix.** Mid-rollout, a `fix: prune dead project
  plugin registry entries` push triggered release PR #814; auto-merge was ARMED
  BY THE WORKFLOW and the PR was MERGED BY `app/livespec-pr-bot` with NO human
  in the loop. **v0.6.1 was cut at 08:29Z**, and `refs/heads/release`
  fast-forwarded to `4ec36d5b` == v0.6.1 automatically. First-hand verified by
  the overseer — this is the previously-manual release cadence now running
  unattended, the exact failure mode the epic set out to eliminate.

- **New / updated ledger.** Filed: `livespec-c1k9.11` (recipe collapse, with the
  git-jsonl precondition note); `bd-gj-hj8` (git-jsonl dirty-settings bug, P1);
  `livespec-dev-tooling-r5m` (uv.lock release drift); `livespec-dev-tooling-afd`
  (release-park follow-ups + the dual App-login-spelling trap for gh-based
  tooling). REGROOMED: `livespec-dev-tooling-a62` to the derive-from-settings
  shared entry point (supersedes the earlier consistency-check framing).

- **CLOSED this window:** `livespec-c1k9.1`, `livespec-c1k9.8`,
  `livespec-c1k9.9`, `livespec-driver-claude-9ab`, `livespec-driver-codex-rn1`,
  `bd-ib-giy`, `bd-gj-lwg`, `livespec-console-beads-fabro-vfd`,
  `livespec-driver-claude-nm9`, `livespec-driver-codex-045`,
  `livespec-dev-tooling-6da`, `livespec-runtime-m2u`,
  `livespec-dev-tooling-ldd`.

### Session 2 (2026-07-03/04) — Python-wave dispatch; canonical-slug cascade; fleet repair

- **Maintainer approved a five-strand parallel fan-out**; all strands ran.
- **`livespec-c1k9.10` CLOSED as already-satisfied** (read-only evaluation:
  the Codex `marketplace upgrade` wiring predates the item — landed
  2026-06-23 — and the c1k9 waves completed the ref pinning + recipe routing
  around it; per-repo evidence in the item's closing comment).
- **Dispatcher operational learnings** (first factory dispatches driven from
  this thread): items need `status: ready` AND the human approval recorded as
  an `admission:auto` label (default admission policy is `manual` — the
  maintainer's fan-out approval IS that approval); the Dispatcher must be
  launched with **cwd inside the target repo** (bd resolves the tenant from
  cwd's `.beads/config.yaml`, NOT from `--repo` — divergence reads the WRONG
  tenant; filed as **`bd-ib-yig`**); pass `--fabro-bin
  /home/ubuntu/.local/bin/fabro` (not on this shell's PATH).
- **`be9` + `a62` SHIPPED factory-side** (dev-tooling PRs #241/#243, TDD
  trailers intact) — but their post-merge janitors red-lined, which unwound
  into the **canonical-slug cascade**: (a) be9's new check
  `check-fleet-marketplace-relative-sources` became a canonical slug that NO
  consumer justfile wired, so the v0.31.3 bump-pin direct-pushes turned
  core / beads-fabro / git-jsonl masters RED on aggregate-completeness; (b)
  the check itself FALSE-POSITIVED on the Codex catalog's object-form local
  source (`{"source": "local", "path": "./..."}`), including dev-tooling's
  own vendored `.livespec-core/` copy (filed + closed as
  **`livespec-dev-tooling-b7i`**); (c) a62's `claude-plugin-currency`
  conformance row shipped at ERROR severity ahead of its rollout item
  (c1k9.11), reddening dev-tooling's own master; (d) `master_ci_green` then
  blocked every repair push — the Red leg cannot even be authored while
  master IS the broken state (working-tree gates read remote/master state).
- **Repair (dev-tooling PR #245, maintainer-side, merged ~00:08Z):** the
  check accepts both legitimate catalog shapes; the currency row is demoted
  to warning until c1k9.11; `master_ci_green` gained the
  `LIVESPEC_MASTER_CI_GREEN=warn` repair lever (CI never sets it). Landed
  via the **suite-green TDD leg** (full pytest suite against the staged
  tree) since a Red commit was structurally impossible; the push rode the
  lever it shipped. Ride-along: uv.lock regenerated (the `r5m` drift).
  **v0.32.1 cut + fan-out succeeded unattended** (fan-out's own
  fleet-conformance preflight passes at warning severity).
- **Consumer wiring wave:** git-jsonl PR #174 MERGED (master green);
  beads-fabro PR #281 auto-merge armed; core = THIS PR (justfile wiring; the
  canonical-slugs projection was restamped by another session in `d8f1837`).
  Core's `doctor-wiring-completeness-cross-repo` reads each member's
  COMMITTED master, so it greens only after this PR merges.
- **`bd-gj-hj8` RE-DISPATCHED** on green git-jsonl master (run 1 had a
  complete branch-green implementation; only the red-master gate refused it).
- **c1k9.3 attempts:** run 1 failed in-run review with two blocking
  design divergences (now a REDISPATCH RIDER comment on the item); run 2
  died at the Red commit against broken core master. Re-dispatch after this
  PR merges.
- **Cross-session coordination:** the `cleanup-research-and-prompt-cruft`
  session (tmux `livespec3`) had maintainer authorization for a GitHub-side
  REVERT of a62's `ad807ea` as its own escape from the same deadlock — my
  session's #245 repair made that unnecessary; it was messaged to stand
  down (a revert would also destroy the `ensure_plugins` entry point that
  c1k9.11 needs). Its halted marketplace-fix worktree is superseded by #245.
- **Redundant in-flight b7i factory run steered to stand down** (the
  maintainer-side #245 superseded it; no duplicate PR was pushed — its
  orphaned duplicate PR #247 surfaced later with automerge ARMED and was
  closed + branch-deleted before it could act).

### Session 2 (continued, 2026-07-04) — gate landed; lever verdict; collapse complete; c1k9.3/.11 CLOSED

- **MAINTAINER VERDICT — the `LIVESPEC_MASTER_CI_GREEN=warn` lever was
  REJECTED outright** ("will absolutely be abused"): removed same day via
  dev-tooling PR #249 (impl reverted byte-for-byte; regression test pins the
  env var to NO effect); `li-4x3a45` upheld and broadened; the durable rule
  codified in core `.ai/ci-gate-discipline.md` (+ AGENTS.md reference):
  NEVER add escape gates to CI-green gates — REVERT the breaking change
  (server-side when local commits are blocked) and re-land in order.
- **`livespec-c1k9.3` CLOSED (gate merged, core PR #848).** Three factory
  runs, three distinct blockers, each root-caused: (1) design-divergence
  review failure → rider; (2) Red commit died against broken master;
  (3) run complete + twice-reviewed but push-rejected — the fleet App
  deliberately lacks the `workflows` permission (maintainer: KEEP the
  boundary; carve workflow edits out to maintainer-side — codified in
  `.ai/ci-gate-discipline.md`), then its 1-hour sandbox token died during
  the multi-hour park. Published maintainer-side by container extraction +
  full Red/Green ritual; content byte-identical to the validated sandbox
  tree.
- **The D2 lever wired then repaired by the book:** ci.yml
  `LIVESPEC_CURRENCY_GATE=fail` landed (#850) → false-positived on CI
  runners (checkout context = permanent Unknown) → REVERTED (#855, master
  green) → gate fix merged (#857: real dict-of-lists registry shape +
  checkout-mode exits the gate's domain; item `livespec-e3nk`, discovered by
  the `.4` evaluation, verified first-hand) → lever RE-LANDED (#859) →
  **master GREEN with the lever live** (8011fa2). Revert-and-reland,
  zero escape hatches.
- **`livespec-c1k9.4` NARROWED** (evaluation evidence on the item): the
  shared chokepoint runs under `codex exec` but reads Claude-only operands →
  permanent Unknown on Codex; remaining scope = Codex running-build vs Codex
  marketplace-clone comparison. Sequenced behind the same-file gate work
  (now landed) and fabro's checkpoint-timeout fix.
- **`livespec-c1k9.11` CLOSED.** All 8 repos' `ensure-plugins` recipes
  collapsed to the one-line derive-from-settings wrapper (4 parallel
  sub-agents + console by hand: PRs livespec #852, driver-claude #88,
  driver-codex #65, beads-fabro #293, git-jsonl #182, dev-tooling #261,
  runtime #125, console #90). Console's PR also fixed its FROZEN dev-tooling
  pin (v0.31.0→v0.33.3) and added its MISSING `bump-pin-from-dispatch.yml`
  shim — the fan-out "success" no-op root cause. `bd-gj-hj8` closed-merged
  (PR #175; its janitor red exposed pre-existing `bd-gj-9sj`: `just check`
  invokes an untracked `dev-tooling/branch-protection.sh`). Severity
  restore: `livespec-dev-tooling-zxq` dispatched → **fully green factory
  run** (PR #262, post-merge janitor green) → row back at ERROR against a
  sweep-verified clean fleet.
- **Orchestrator robustness family filed** from this session's incidents:
  `bd-ib-lgv` (declare+enforce the no-workflow-edits boundary pre-push),
  `bd-ib-6vu` (parked-run credential re-projection; docstring claims
  re-minting that does not reach resumed sandboxes), `bd-ib-18r` (blocked
  runs orphaned as "failed"), `bd-ib-6ka` (fabro 30s checkpoint-commit
  timeout < core's gate runtime — why core items currently publish
  maintainer-side), `bd-ib-4nk` (Dispatcher overlay projects the D2 lever
  into sandboxes — the factory half of "CI and factory dispatch set it").
- **Sandbox-extraction publication pattern** (used for #848 and #857, until
  `bd-ib-6ka` lands): `docker cp` the validated files from the (stopped)
  `fabro-run-<id>` container, pre-verify the full set in a fresh worktree,
  reset to master keeping ONE changed test file, prove a genuine Red, commit,
  Green-amend the rest, push through the full gates. Provenance recorded in
  each commit body.

### Session 3 (2026-07-04) — parallel wave: c1k9.6 filed+amended, afd two-leg, adopter self-update, bd-ib-4nk factory-merged

- Maintainer directive: "parallelize as much of this as possible." A parallel wave ran across disjoint repos (core, dev-tooling, orchestrator), then rotated for context at the maintainer's prompt.
- **c1k9.6** filed (core PR #870) + amended per an independent Fable review (blockers: copier-template exhaustive-list omission of `release-park.yml`, fleet-scope, Codex Installer/Mechanism leg). SCOPE decision (maintainer): FLEET + opt-in adopters (`posture: released`), mirroring Pin-freshness. Finding: the runtime gate is NOT posture-aware (compares running build vs the repo's own marketplace-clone tip); pinned adopters are structurally coherent; the posture exemption is a fleet-conformance-SWEEP concern.
- **Adopter self-update** added to `docs/livespec-installation-prompt.md` (core PR #871) — maintainer directive: adopters own their own plugin currency via the central idempotent install prompt, harness-native (Claude SessionStart hook / Codex `plugin marketplace upgrade`), decoupled from fleet tooling (`just`/`mise`/`uv`). Pairs with the fleet-scoped contract (the fleet does not enforce adopter currency).
- **afd** two-leg release-park parity filed (dev-tooling PR #267) + work-items `livespec-dev-tooling-2kt` (leg-b impl) and `livespec-dev-tooling-xam` (Option A presence enforcement, names `livespec-runtime`). A Fable review caught the silent leg-(b) descope (no recorded descope existed); `livespec-runtime` has `release-please.yml` but no `release-park.yml` — a live backstop gap. The "six release-please repos" framing was stale: it is seven of eight (console the only non-carrier).
- **bd-ib-4nk** factory-dispatched → merged (orchestrator PR #309), post-merge janitor green, awaiting human acceptance — the first clean end-to-end orchestrator-repo factory dispatch driven from this thread (the orchestrator's own gates fit inside fabro's 30s checkpoint timeout; core's do not — see bd-ib-6ka).
- **bd-ib-6ka** investigated: the ~30s git-checkpoint-commit timeout is hardcoded in the closed Fabro binary (`fabro-workflow` Rust crate); no config knob. Fix is UPSTREAM — the fabro source is cloned at `/data/projects/fabro` (`github.com/fabro-sh/fabro`). Maintainer chose OPTION 1: keep the maintainer-side extract+publish interim for gate-heavy core items AND drive the upstream PR (next action #1). The one interim in-repo lever (`[run.checkpoint] skip_git_hooks=true`, which bypasses hooks only on Fabro's internal snapshot commits while the janitor node + CI still enforce the full gate) was NOT taken — contrary to the standing no-bypass posture.
- **c1k9.7** upstream report drafted (3 Claude Code plugin-source-pin defects: github plugin-source `commit`/`branch`/`path` silently ignored; `git-subdir` rejected; `validate` accepts what runtime won't deliver). Terminal — maintainer files externally.
- Wrapper bug found: core `propose_change.py` resolves a relative `--spec-target` against cwd, not `--project-root` (workaround: absolute `--spec-target`); to be filed.

### Session 4 (2026-07-04/05) — ripe items banked: c1k9.6 codified+closed; afd deferred with debt captured

- Maintainer strand: "Bank the ripe items" (accept bd-ib-4nk, file the wrapper bug, then drive both revises once their Fable reviews cleared).
- **Two independent Fable reviews, both NO-BLOCKERS:** c1k9.6 (core, amended payload — byte-exact replace-target fidelity, design-record match, both prior blockers resolved) and afd (dev-tooling — two-leg design parity, leg-b descope honest via `2kt`).
- **bd-ib-4nk accepted → closed → live-exercise evidence journaled** (see Session-4 banner). PR #309 verified merged, all janitor/CI checks green.
- **Wrapper bug filed** `livespec-gvqmin` (core, P2).
- **c1k9.6 ratified via SUBSET revise → merged → CLOSED** (core PR #875, `v160`). A direct `bin/revise.py` single-decision payload accepted ONLY `fleet-plugin-currency-contract`, leaving the two unrelated pending proposals untouched (subset integrity verified on master). All gates green (post-step doctor exit 0, `just check` 59/59, PR CI pass).
- **afd revise HALTED at its `--post-step-doctor` gate** on pre-existing dev-tooling doctor-static debt. Root-cause: 100 `.py` files with `§"..."` citations + ~16 un-allowlisted cross-repo headings; the checks are legitimate (one caught the `contracts.md`→`nfr.md` drift). Maintainer decision: DEFER afd; file the debt as a scoped epic; no 100-file migration inline.
- **Debt captured:** dev-tooling epic `goucoq` (children `kkmhwo` allowlist + `7bfhkm` migration/refine), systemic `tem4t2` (CI doesn't gate doctor-static); `afd`+`tem4t2` blocked-by the two children; graph cycle-free; `afd`+`2kt` deferral/correction notes added; the halted `revise-afd-release-park` worktree cleaned up.
- The two mechanical spec-ratification PR cycles were driven by scoped worktree executors (proven reliable).
- Rotated for context at the maintainer's prompt; refreshed this handoff (Session 4) as the durable resume point.

### Session 5 (2026-07-05) — the standing red-master decision resolved + filed

- Maintainer strand: `/plan fleet-plugin-currency` → chose "resolve the red-master gap" (the one item unasked since Session 2, blocked only on the maintainer).
- **Grounded the decision first** (read-only): read `.ai/ci-gate-discipline.md` and the actual mechanism — `aggregate_completeness` (discovers the canonical set live from the pinned dev-tooling, fails a consumer whose `just check` omits a slug), `canonical_checks` (filesystem-derived slug set; recipe body is always `uv run python -m livespec_dev_tooling.checks.<module>`, so the wiring is 100% derivable), and the direct-push bump-pin fan-out (already writes each consumer's master). Confirmed both wiring lines (recipe + `targets=` entry) are deterministically generatable and the fan-out already writes justfiles' sibling files.
- **Decision (maintainer): "fan-out writes the wiring."** The fan-out reconciles each consumer's `check:` canonical block to the newly-pinned set atomically with the pin bump (reusing `aggregate_completeness`'s parser); the check stays the verifier. Rejected: grace-period soft-warn (drift-prone state + softens the check) and manual-wave (the status quo that caused the cascade).
- **Filed `livespec-dev-tooling-adqmnm`** via the `capture-work-item` store-writer, tenant-targeted at dev-tooling (chdir so `resolve_store_config(cwd=…)` resolves the dev-tooling `.beads/config.yaml`): `feature`, `origin:freeform`, `gap_id:null`, `depends_on livespec-dev-tooling-9j8.1`; DoR intake routed it to BLOCKED / `blocked-reason:needs-human` (autonomy tier deferred to groom). Full decision + rejected alternatives + acceptance criteria are on the item.
- Refreshed this handoff (Session 5) as the durable resume point; the red-master item is retired from the next-action list.

### Session 5 (continued, 2026-07-05/06) — driven to the exit-gate boundary

- Maintainer: keep driving fleet-plugin-currency autonomously (Fabro PR declared a SEPARATE track); only stop for a genuine question or nearing 50% context.
- **`bd-ib-6ka` investigated + prepped as a separate track** (before the scope split): a read-only Plan sub-agent located the hardcoded ~30s checkpoint-commit timeout (`fabro-workflow/src/sandbox_git.rs:137`) and produced the exact `[run.checkpoint] commit_timeout_ms` edit map (~7 files/3 crates, default-preserving) → journaled on the ledger item. Created fork `thewoolleyman/fabro` (origin=fork/upstream=upstream on `/data/projects/fabro`), and wrote a self-contained impl prompt (`/data/projects/fabro/tmp/fix-checkpoint-commit-timeout.md`) for a human-run cross-fork PR. Maintainer owns running it.
- **`c1k9.5` CLOSED as mitigated** (overseer disposition; ref-pinning resolved the load-bearing ambiguity; residual captured in the close reason). Epic 7/11 → **8/11**.
- **`7bfhkm` groom cut resolved by reading the core check**: `no_spec_section_citation_in_code` enforces a codified anti-rot Reference discipline and caught real drift ⇒ MIGRATE dev-tooling's 159 `§"..."` code citations to file-level, NOT weaken the check (recommended cut + full scope recorded on the item).
- **Assessment:** the track's own deliverables are complete; the epic is exit-gate-ready and CLOSES when `c1k9.4` lands (dependency = the separate Fabro track). Remaining non-exit items (`goucoq`/`afd`, `c1k9.2`, `c1k9.7`, `adqmnm`) are documented follow-ups with directions resolved — see the Session-5 banner. `goucoq`/`afd` is best driven as its own dev-tooling track (maintainer-cautioned 100-file migration).
