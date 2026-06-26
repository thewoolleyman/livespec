# Handoff: Formalize the livespec blessed workflow (epic livespec-zs22)

**Track:** planning-lane · **Epic:** `livespec-zs22` · **Tenant:** livespec

This is the resumable runbook for the Planning Lane + Conformance Pattern
formalization. It carries *instructions*; the *rationale* lives in
`research/planning-workflow-gap/planning-lane-design.md`, and the
*authoritative status* lives in the ledger — never in this file.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd show livespec-zs22
```

Derive every "what's done / what's next" answer from that, plus
`bd ready` and `git log`. This file lists the *plan*, not the *state*.

## Read first

1. `research/planning-workflow-gap/planning-lane-design.md` — the design,
   the three planes, the locked decisions, the increment sequence, and the
   three FINAL diagrams (§"Architecture diagrams") ready to land in the spec.
2. `research/factory-conformance/cross-repo-conformance-pattern.md` — the
   companion Conformance Pattern (files its milestones through this lane).
3. `research/planning-workflow-gap/missing-planning-workflow-thread.md` —
   the original gap note.

## Objective

Re-adopt livespec's own deferred planning design as a codified, disciplined
convention, place each piece on the plane that owns it (Spec /
Orchestrator / Control), and mechanically enforce the no-shadow-ledger
rule — then build the Conformance Pattern on top of it. Locked decisions
(see the design doc): handoff skill **orchestrator-side**; **`baseline`**
profile (not "factory"); **`just` mandated non-functionally only** (never
in core's public functional surface); fleet pins track **latest RELEASE**
not HEAD; the **console** is the Control-Plane runner.

## Status (refreshed 2026-06-26 session 2, M6 IN PROGRESS — foundation cleared; M6-e next)

**Run this track autonomously.** Standing maintainer directive (2026-06-25):
own the cuts (file children, draft, execute, land per increment), gate only
on a genuine architectural/intent question, and hand off to a fresh session
when context approaches budget. This supersedes the design doc's
per-cut approval gate for this track.

### M6 (zs22.7.7) — session-2 progress (2026-06-26): foundation cleared

M6 is CLAIMED (`bd update livespec-zs22.7.7 --status in_progress`). Its full
decomposition + the recon'd four-tier state live in the **`zs22.7.7` ledger
notes** (read them: `bd show livespec-zs22.7.7`) — not re-listed here, to avoid
a shadow ledger. What session 2 LANDED (all on master):

- **dev-tooling `v0.21.0` + `v0.21.1` CUT.** v0.21.0 (PR #174) is the lowest
  release carrying `check-plugin-resolution` (concern #2's Verifier); v0.21.1
  (PR #178) also carries the fan-out fix below. These are the pin-able releases
  M6's plugin-resolution wiring needs.
- **`livespec-zimq` (P1, CLOSED) — live dispatch regression fixed.** The v148
  `members→fleet` manifest rename left the orchestrator's `parse_fleet_members`
  reading the removed `members` key, so EVERY dark-factory dispatch failed at
  sibling-clone provisioning (`_resolve_sibling_clones` refused on `None`).
  Fixed via `livespec-orchestrator-beads-fabro` PR #177 (master `e979d41`):
  reads `fleet` with a `members` fallback (matches dev-tooling's
  `(.fleet // .members)`); the canned test fixture now mirrors the real `fleet`
  shape so the autouse dispatch tests exercise it (the gap that hid the bug).
- **`livespec-2rab` (P1, CLOSED) — release fan-out fixed.** The fan-out's
  `discover-siblings` step failed post-v148 (jq `Cannot iterate over null` —
  the authenticated `gh api .../contents` read returned content lacking
  `fleet`/`members` under the workflow's App token, though the identical
  pipeline worked with a normal token). Fixed via `livespec-dev-tooling`
  PR #177 (merged): reads the PUBLIC manifest via `raw.githubusercontent.com`
  (no auth, always raw), drops the App-token mint, echoes the fetched head on
  parse failure. The v0.21.1 fan-out runs the FIXED workflow — confirm it went
  green and opened bump-pin PRs (the self-healing pin-propagation chain).

**Self-healing pin chain now in motion:** v0.21.1's fixed fan-out should
auto-bump every sibling's dev-tooling pin to `v0.21.1` (a release carrying
`check-plugin-resolution`). That is the prerequisite M6-e's commit-time wiring
needs. FIRST NEXT-SESSION ACTION (after the FIRST ACTION ledger query): confirm
the v0.21.1 fan-out went green + the bump-pin PRs merged across siblings; if the
fan-out still failed, read its `discover-siblings` log (now self-diagnosing) and
re-open `2rab`.

**⚠ CONCURRENCY — multiple sessions work this epic's ready queue (RECURRING;
has now bitten TWICE).** M3 (`livespec-zs22.7.4`) was landed by a CONCURRENT
session as console commit `76c9fc2` while a parallel interactive session
independently implemented the SAME milestone (the parallel PR was closed). M4
(`livespec-zs22.7.5`) collided AGAIN: a runaway duplicate session (tmux
`livespec-runtime`) independently produced byte-identical adopter-schema work,
then its subagents rebased the active session's `v148` commit and
force-pushed/merged it through PR #631 — INSIDE the active session's shared
worktree. It CONVERGED (nothing lost; #631 carried the correct `v148` = master
`fb8abd5`; the duplicate was then stopped + the contended worktree cleaned up),
but it was chaotic. Likely cause: the dark-factory Dispatcher and/or stray tmux
sessions poll the Beads ledger and work ready items in parallel with any
interactive session. BEFORE implementing ANY item: (1) re-run the FIRST ACTION
ledger query AND `bd ready`, (2) `git fetch` + read each target repo's
`origin/master` tip, (3) confirm the item is still open + unstarted, and (4)
`bd update <id> --status in_progress` to CLAIM it. Re-check master freshness
immediately before EACH commit AND before EACH push (a push may be rejected
non-fast-forward if a concurrent session pushed the same branch name). If a
concurrent session is actively pulling this epic, prefer to let it.

Landed: increment 0 + design refinements (PRs #568, #572; `livespec-zs22.1`
closed). **Increment 1** (`livespec-zs22.2`, PR #575, cut `v137`): the
`## Workflow planes and the Planning Lane` framing + planes/skills diagrams.
**Increment 2** (`livespec-zs22.4`, PR #577, cut `v138`): the NON-normative
`#### Planning Lane guidance` block in `non-functional-requirements.md`.
**Increment 3a** (orchestrator PR `livespec-orchestrator-beads-fabro#167`,
cut `v016`; core PR `livespec#579`, cut `v139`): the orchestrator-side
`plan` skill (`prose/plan.md` + Claude/Codex bindings + e2e-cli fixture) and
the `## Planning Lane realization` contract — `plan` is the SIXTH heavyweight
op — PLUS the core NFR `Handoff self-sufficiency` pattern paragraph.
`livespec-zs22.3` (the 3a acceptance harness: cold-open test, one path,
fail-closed dangling-reference) is **CLOSED**. Epic is **4/5 children
complete**.

**Increment 3 COMPLETE** (`livespec-zs22.5` CLOSED). 3a = the orchestrator
`plan` skill (landed earlier). 3b = the no-shadow-ledger WARN-only `Stop` hook,
now landed in BOTH Drivers byte-identical: core contract `livespec#584` (`v140`);
`livespec-driver-claude#42` (master `06044b4`); `livespec-driver-codex#17`
(master `d6a4f88`); both bodies sha256 `5beb62c5…` (= the canonical source, noqa
preserved). Maintainer chose option A (identical copies now via the gate's
suite-green `chore:` path; the mechanical byte-identity Verifier is increment-5
Conformance work). The hooks landed via suite-green, not Red→Green, because the
red-green classifier doesn't impl-classify Driver hook paths (`livespec-kvzt`).

**Increment 4 COMPLETE** (`livespec-zs22.6` CLOSED) — the console control-plane
contract, landed as one cross-repo epic. CORE (`livespec` PR #598, cut `v142`):
a NEW NON-normative top-level `### Control-Plane console guidance` section in
`non-functional-requirements.md` — a PEER of `### Orchestrator plugin ecosystem`,
NOT nested under it (the console is the Control Plane, a plane distinct from the
Orchestrator; nesting would contradict the plane separation this track codifies;
the earlier "sibling under Orchestrator plugin ecosystem" wording was imprecise —
an H3 peer respects the planes and, since heading-coverage tracks H2 only, costs
nothing mechanically). It records what the console reads / composes / coordinates
/ never owns, that it is not a required dependency, not a Driver, and the `just`
boundary — framed identically to the Dispatcher / grooming / Planning Lane
guidance blocks. CONSOLE (`livespec-console-beads-fabro` PR #34, cut `v006`): a
`Control-Plane realization` paragraph in `spec.md` §"Scope Boundary" plus the
Scope-Boundary mermaid diagram extended to the three-plane framing (console =
CONTROL PLANE; livespec core under a SPEC PLANE subgraph; orchestrator + Fabro
under an ORCHESTRATOR PLANE subgraph; GitHub a host source). Both landed via the
governed propose-change → revise lifecycle.

**Increment 5 FILED + M0/M1 COMPLETE — the Conformance Pattern.** Increment 5 is
now a filed SUB-EPIC `livespec-zs22.7` (under `livespec-zs22`, which is now 6/7
children) holding milestones **M0–M6** (`livespec-zs22.7.1`…`.7`), chained
M0→M6, with see-also links to the fold-in follow-ups (`gcp2`, `kvzt`, `i6rc`,
`8njn` on the epic; `qtjd`↔M2; `mjnv`↔M5). **M0** (`zs22.7.1`) CLOSED — decisions
locked in the design docs + `zs22.1`, no code. **M1 COMPLETE** (`zs22.7.2`, PR
#602, rebase merge `9c7c87c`, cut `v143`): a NEW NON-normative top-level
`### Conformance Pattern` section in `non-functional-requirements.md` (after
`### Control-Plane console guidance`, before `### Codex dogfooding compatibility`)
— the five-slot anatomy (Contract / Mechanism / Installer / Verifier / Exemption),
the reuse-by-default delivery rule, the consolidated `just` keystone + its
functional/non-functional boundary, the profile + declarative
`.livespec-fleet-manifest.jsonc` `adopters`/`posture` boundary, the four-tier
enforcement, the explicit-exemptions/default-fail-closed hard rule, and the
concern registry (concern #1 worktree-discipline + concern #2 cross-harness
plugin-resolution in full five-slot form; No-shadow-ledger / Terminology-guard /
Ledger-closure / Pin-freshness / Archive-on-epic-close named). It NAMES +
GENERALIZES existing fleet machinery (§Fleet membership contract, copier,
dev-tooling, pin-and-bump) rather than duplicating it. `just check` green;
doctor-static green. The pattern is now SPEC; the machinery is M2→M6.

**Mid-increment-3 detour, DONE — epic `livespec-gcp2` (red-green-replay
fleet+adopter-wide).** Maintainer directive (2026-06-25): red-green-replay MUST
be enforced fleet+adopter-wide, regardless of any "no product Python"
self-classification. LANDED: both Python Drivers wired at lefthook **and**
authoritative CI (`livespec-driver-claude#40`; codex `8abbea1`+`356aabc`); core
policy `livespec#589` (`v141`); adopters covered by the `templates/impl-plugin/`
copier; `h3e7` (commit-pairs no-op) fixed in both Drivers. gcp2 was RE-OPENED as
the **Driver-hook enforcement umbrella** to hold the conformance follow-ups this
session surfaced (below).

**Open conformance follow-ups (filed this session; status from the ledger, not
here; mostly increment-5 Conformance-Pattern work).**
`livespec-co9h` (block-auto-memory deny-reason reword — claude part LANDED
`ee8ec92`; codex has no such hook; part-3 = `livespec-8njn`, the family AGENTS.md
durable-memory capture convention, default-tracked pending a maintainer draft-now
call); `livespec-kvzt` (`red_green_replay._IMPL_PREFIXES` hardcoded → Driver hook
changes dodge Red→Green; make impl-classification config-driven); `livespec-i6rc`
(`lint-autofix-staged` mutates ruff-excluded files → `--force-exclude` needed in
the canonical orchestrator + copier template, not just the Drivers);
`livespec-qtjd` (fresh clones can have dormant local git gates until
`just bootstrap`); `livespec-mjnv` (live codex picker fails-on-timeout vs
skips-on-unavailable); `livespec-1t17` (Rust red-green analogue for the console).

## Next concrete action

**M6 (`livespec-zs22.7.7`) is CLAIMED + IN PROGRESS (session 2).** Its
foundation landed (see §"M6 — session-2 progress"): `check-plugin-resolution`
is now pin-able (dev-tooling `v0.21.1`), both v148-rename collateral regressions
are fixed (`zimq`, `2rab`), and the self-healing pin chain is in motion. The
remaining M6 work is the cross-repo wiring, in this order (own the cuts; each its
own PR; full state in the `zs22.7.7` ledger notes):

0. **Confirm pins propagated.** After the FIRST ACTION query: verify the v0.21.1
   fan-out went green and the per-sibling bump-pin PRs (dev-tooling `→v0.21.1`)
   merged. If the fan-out is still red, read its now-self-diagnosing
   `discover-siblings` log and re-open `2rab`. (Laggards to watch: `livespec-runtime`
   was on `v0.14.0`, `livespec-console-beads-fabro` on `v0.19.0`/`compat.pinned
   "master"` — the fan-out may not reach console; bump those manually if needed.)

1. **M6-e — commit-time backfill (the bulk, cross-repo epic).** Per governed repo:
   declare `harnesses` + (where not class-derived) `profile` in `.livespec.jsonc`,
   and wire `check-plugin-resolution` into `just check`. Per-repo harness
   declarations follow each repo's ACTUAL command/skill surface: orchestrators →
   claude+codex `supported` (canonical_command e.g. `livespec-orchestrator-…:next`);
   `driver-claude` → claude supported / codex exempt; `driver-codex` → already
   declares codex supported / claude exempt; libraries (`dev-tooling`, `runtime`)
   → no command surface, declare all harnesses `exempt` (reason: library); core
   (`livespec`) → judgment call (the `/livespec:*` surface resolves via the
   Drivers — likely claude+codex supported or a documented exemption). ALSO fix
   the two Drivers + console to wire `check-primary-checkout-commit-refuse-hook-installed`
   via the canonical mechanism (they wire NEITHER today). Delegate per-repo to
   sub-agents; sequence file conflicts; re-check master freshness before each push.

2. **M6-d — author-time (core template).** Add `check-plugin-resolution` to
   `templates/impl-plugin/canonical-slugs.yml` (commit-refuse already wired) and
   scaffold a `.livespec.jsonc.jinja` declaring `profile`/`harnesses` for a
   generated repo. COUPLED to M6-e: only land after the impl-plugin siblings are
   on `v0.21.1` + wired, else their `copier update --dry-run` drift CI reddens.
   Update the `copier-template-workflow-coverage`/canonical-slugs doctor coverage
   if needed.

3. **M6-c — fleet-time reporting (dev-tooling, spec cycle).** Extend
   `fleet/fleet_conformance.py` to derive per-repo BASELINE obligations from
   `profile` (members via class→profile; `adopters` via declared profile —
   currently PARSED but IGNORED), asserting each governed repo wires the baseline
   verifiers + declares `harnesses` + pins a carrying release. REUSE the existing
   `OBLIGATION_ROWS` mechanism (add a `baseline-profile-wired` row); start the new
   row at `warning` severity during backfill, flip to `error` after. This is the
   "fleet-time sweep reports per-repo conformance" acceptance item. dev-tooling
   `contracts.md` propose-change → revise.

4. **M6-f — dispatch-time gate (orchestrator, spec cycle).** Add baseline Verifier
   step(s) to the Fabro prepare chain in
   `.fabro/workflows/implement-work-item/workflow.toml` — RIGHT AFTER the existing
   `install-commit-refuse-hooks` + `git config livespec.sandboxExempt true` steps —
   running `check-primary-checkout-commit-refuse-hook-installed` and
   `check-plugin-resolution` (mock = declaration-integrity). A failing prepare
   step aborts the run = the gate ("conformant by construction"). Codify the
   dispatch-time gate in the orchestrator's OWN `SPECIFICATION/` (governed cycle).
   NOTE: `uv sync --all-groups` runs earlier in prepare, so `livespec_dev_tooling`
   resolves. (Side note logged this session: the janitor runs `just check` only —
   `/livespec:doctor` is NOT in the dispatch path despite prose claiming it; out
   of M6 scope but worth a separate look.)

5. **M6-g — flip + close.** Once every governed repo declares `harnesses`, flip
   `check-plugin-resolution` absent→fail (the `load_harnesses` `_LOAD_SKIP` path
   already flags "M6 will make it required fleet-wide"); dev-tooling `v0.22.0`;
   bump pins. Then verify all four tiers run the shared verifiers, CLOSE
   `zs22.7.7` + `zs22.7` + `livespec-zs22`, and `git mv` this handoff to
   `archive/prompts/` per §"Archive condition".

Carry-over notes: (1) `harnesses` required is the cross-repo backfill of M6-e→M6-g
("A required-key schema change is a cross-repo epic"); (2) `check-plugin-resolution`
ships in dev-tooling `v0.21.0`+ — pin `v0.21.1` (also carries the fan-out fix);
(3) codex's GENUINE live resolution smoke is the repo-local `check-codex-skill-picker`
(the dev-tooling check DELEGATES codex via `DelegatedResolutionRunner`) — M6 MAY
unify the per-harness smokes or keep the delegation.

**M5 (`livespec-zs22.7.6`) — DONE + CLOSED (2026-06-26).** Concern #2
(cross-harness plugin-resolution) shipped through the five slots and proven
repeatable (reused the dev-tooling check-registry + `baseline` accessor + the
`cli_e2e` `CliRunner` seam — added ONE check + ONE declaration, no framework).
Three PRs, all merged + master CI green: **PR-1** `livespec-dev-tooling#175`
(`80dab47`) — the NEW `check-plugin-resolution` Verifier (always-on
declaration-integrity gate reading optional `.livespec.jsonc` `harnesses`,
fail-closed on malformed; env-gated `LIVESPEC_E2E_HARNESS=real` live resolution
smoke; registered as the SECOND `_BASELINE_CHECK_SLUGS` concern; `contracts.md`
inventory entry; 22 tests incl. the **ob-4ts fail-closed PROOF** — a raw `bd`
fallback "works" but the slash command is unresolved ⇒ exit 4). **PR-2a**
`livespec-dev-tooling#176` (`a31eb4f`) — per-harness runner routing: a `supported`
codex harness was mis-routing through the claude `RealCliRunner` (`claude -p`) in
`real` mode; now codex delegates to its repo-local smoke (`DelegatedResolutionRunner`
⇒ SKIP); Red→Green proof that the claude-backed runner is never invoked for codex.
**PR-2b** `livespec-driver-codex#22` (`1f1e7bd`) — the **`mjnv`** fold-in:
`test_codex_skill_picker.py` now distinguishes codex-unavailable (SKIP: codex
absent / TUI exit / bring-up-phase timeout) from genuine non-resolution (FAIL:
final skill-row timeout); PROVEN LIVE (`check-codex-skill-picker` SKIPPED after
the 125s startup timeout — codex present-but-unauthenticated — instead of
failing); PLUS driver-codex `.livespec.jsonc` declares `harnesses` (codex
supported / claude exempt) = the dogfood. DOGFOOD verified end-to-end: dev-tooling
master `check-plugin-resolution` vs the driver-codex declaration ⇒ mock:
well-formed, exit 0; real: codex `decision=skip` (delegated, NO mis-route), claude
`decision=pass` (exempt), exit 0. `livespec-mjnv` CLOSED (fixed by PR-2b). The
epic `livespec-zs22.7` is now 6/7 children complete; M6 is the last.

**M4 (`livespec-zs22.7.5`) — DONE + CLOSED (2026-06-26).** Re-scoped by maintainer
directive to the LIVESPEC-SIDE adopter-enablement machinery ONLY; the heavy Open
Brain migration (just-as-sole-runner + hook reconciliation + adopter registration
+ baseline-green) was split out to OB-tenant epic **`ob-23p`** — the deferred
FINAL track deliverable, ideally driven by Open Brain's OWN first-class autonomous
work-item-dispatch factory once stood up (ob-coq delivered OB's deploy factory but
NOT work-item dispatch; no `.fabro/` loop yet). What landed: core spec **v148**
(master `fb8abd5`, PR #631) — NFR §"Fleet membership contract" defines the
manifest's `fleet` + `adopters` arrays (the legacy `members` array RENAMED to
`fleet` per the locked design + the family→fleet convergence; the umbrella term
for fleet+adopters is **`governed repo`**, defined in
`research/factory-conformance/cross-repo-conformance-pattern.md` §"Ubiquitous
language"), §"Conformance Pattern" reconciled; the manifest renamed
`members`→`fleet` + added an empty `adopters: []` (NO adopter registered). PLUS
**dev-tooling v0.20.0** (PR #171) — `fleet/contract.py` parser accepts BOTH
`fleet`/`members` keys + parses `adopters` (`Adopter` dataclass, `PROFILE_LAYERS`,
`ADOPTER_POSTURES`), and the release fan-out `jq` reads `(.fleet // .members)`;
landed FIRST so the runtime manifest-fetch never broke during the rename. The
PR #631 cross-session COLLISION (see §concurrency) was RESOLVED: the duplicate's
work converged with this session's, #631 carried the correct `v148`, nothing was
lost, and the contended worktree was cleaned up.

**M3 (`livespec-zs22.7.4`) — DONE on console master via `76c9fc2`** (a CONCURRENT
session; live status from the ledger). The Rust Control-Plane console now carries
`baseline`: the canonical STRUCTURAL commit-refuse hook + the shared dev-tooling
verifier wired into `just check` + CI, REUSED not re-implemented — `76c9fc2`
consumes dev-tooling via a minimal `pyproject.toml` `[tool.uv.sources]` git+tag
v0.19.0 pin (+ `.python-version`, `uv.lock`), the bump-automatable approach.
Fail-closed proven (a commit on the console primary master is refused, HEAD
unchanged, primaryPath unset); console master CI green. Console work-item
`livespec-console-beads-fabro-d5c` CLOSED. Two follow-ups: `zs22.7.8` was REFINED
— the console now HAS a pyproject `[tool.uv.sources]` dev-tooling pin, so the
eventual `console` repo class should INCLUDE (not exclude) the `dev-tooling-pin`
obligation; and `livespec-console-beads-fabro-e8y` (P3) — remove the
now-redundant lefthook `00-no-commit-on-master` that `76c9fc2` left (the
structural hook is the single Mechanism).

**M2 (`livespec-zs22.7.3`) — what landed (mechanism FLEET-MIGRATED; live status
from the ledger, not here):** the maintainer-confirmed **Option A** (one uniform
commit-refuse wrapper installed everywhere + an explicit `livespec.sandboxExempt`
marker the hook BODY reads; structural refuse when `git-dir == git-common-dir`;
armed-on-install; `primaryPath` retired) is now the single canonical Mechanism
for concern #1, migrated across the fleet:
- **M2-1 `livespec-dev-tooling#165` (MERGED, v0.18.0)** — canonical structural
  body + verifier accepts BOTH structural and legacy bodies through migration.
- **PR-1 `livespec-orchestrator-beads-fabro#169` (MERGED)** — Fabro prepare arms
  `livespec.sandboxExempt true` (folds `livespec-qtjd`).
- **M2-2 core `livespec#609` (MERGED, `4c7849a`, cut v144)** — core wrapper →
  structural body; shared `install-commit-refuse-hooks` recipe + bootstrap
  delegate; `primaryPath` retired; governed NFR/contracts spec cycle.
- **Template `livespec#612` (MERGED, `4f37f75`)** — RESOLVED the architectural
  divergence: the single-wrapper is canonical (it is the latest + the deliberate
  M2 Mechanism + has `sandboxExempt` + satisfies the canonical check + is
  armed-on-install). Template now installs the structural body via
  `install-commit-refuse-hooks`; `refuse-primary-commit.sh` deleted + unwired;
  KEPT `worktree-lib.sh` lifecycle pack + ecosystem profiles + branch-protection
  (orthogonal, adopter-proven).
- **M2-3 orchestrator `livespec-orchestrator-beads-fabro#171` (MERGED, `1bd35b5`)**
  — orchestrator body → structural at pre-commit/pre-push/commit-msg; `primaryPath`
  retired; recipe aligned.

**M2-1b — the reusable installer MODULE — is DONE (dev-tooling v0.19.0, `#167`
+ spec cycle `#169`).** `livespec_dev_tooling.install_commit_refuse_hooks` is the
single wheel-shipped canonical-body carrier (installs pre-commit/pre-push/
commit-msg), and `canonical_checks.baseline_check_slugs()` ships the `baseline`
check-profile accessor. **MODULE ADOPTION:** dev-tooling, the orchestrator
(`#173`, which retired its vendored `.sh`), and the console (`#43`) now REUSE the
module; **core + the copier template still `cp` the interim body (core M2-1b
DEFERRED per maintainer call)**. So M2's "no per-repo copies" goal is met for the
repos on the module; core/template adoption is the remaining tail. (Do NOT
re-build the module — it exists in v0.19.0.)

**Still open / deferred under M2 (live status in the `zs22.7.3` ledger notes):**
- **`baseline` tag** — the accessor SHIPS (v0.19.0) but the full profile/partition
  + manifest wiring is deferred to M4 (where Open Brain first imports it).
- **git-jsonl follow-up** — `livespec-orchestrator-git-jsonl` does NOT dispatch
  into Fabro (no `.fabro/`), has NO `sandboxExempt` arming, and still carries the
  LEGACY body. Do NOT migrate it to structural until its dispatch path is
  confirmed to arm `sandboxExempt` (a structural body would refuse legitimate
  in-sandbox commits). The verifier still accepts its legacy body, so not urgent.
- **dev-tooling structlog runtime deps (NEW)** — dev-tooling vendors structlog
  but declares no `[project.dependencies]`, so a minimal consumer (the console)
  had to add `typing-extensions` on Python <3.11; the systemic fix is for
  dev-tooling to declare structlog's transitive runtime deps so every consumer
  gets them.

**Side observation (NOT acted on):** the two pre-migration planning docs
`prompts/worktree-discipline-pack-{epic,prompt}.md` still reference the now-deleted
`refuse-primary-commit.sh` (the only remaining stale refs in core). Candidate to
archive to `archive/prompts/` (the pack landed; the refuse half is superseded) —
maintainer's call.

M5 is DONE (concern #2 cross-harness plugin-resolution; folded `mjnv`); M6
(four-tier wiring) is the last milestone. M4 itself seeds the `baseline` tag (the
partition deferred from M2, where Open Brain first imports it). Each is its own
PR. The remaining fold-in follow-ups (`kvzt`, `i6rc`, `qtjd` [folded by M2's
armed-on-install], the gcp2 byte-identity Verifier, `8njn`) are see-also-linked
to `zs22.7` and its milestones — pull each into the milestone whose concern it
sharpens; do NOT re-parent them off `gcp2`. (`mjnv` is now CLOSED, folded into M5.)

**Also pending a maintainer call:** `co9h` part-3 (`livespec-8njn`) — document
the durable-memory capture convention in the family AGENTS.md (impl-plugin
template + core). Default-tracked; the maintainer may opt to draft it now (it has
a design element on the AGENTS.md-section vs. referenced-instruction-file
mechanism).

## Pinned canonical body (`no_shadow_ledger.py`)

**LANDED — historical reference** (now committed byte-identical at sha256
`5beb62c5…` in `livespec-driver-claude/.claude-plugin/hooks/no_shadow_ledger.py`
and `livespec-driver-codex/livespec/hooks/no_shadow_ledger.py`; read those for
the live copy). It was the single source for the two 3b Driver hooks. Authored
+ smoke-tested 2026-06-25
(WARN on a `*handoff*.md` / `plan/` / `prompts/` `.md` write carrying ≥3 `[ ]`/`[x]`
checkbox items; SILENT on clean artifacts incl. inline `` `[ ]` `` in prose, on
non-planning paths, on malformed stdin, on `stop_hook_active`). It lives here
(not as a committed `.py`) because core runs pyright-strict on tracked `.py`; the
Driver repos run neither pyright nor ruff on their ruff-excluded hook dirs, so it
ships verbatim there.

```python
#!/usr/bin/env python3
"""
livespec no-shadow-ledger — Stop hook warning on planning artifacts that
embed a checkbox task queue instead of deriving status from the ledger.

Shipped BYTE-IDENTICALLY by both Drivers (livespec-driver-claude at
.claude-plugin/hooks/, livespec-driver-codex at livespec/hooks/) as the
single-sourced neutral body; each Driver's hooks.json Stop entry is the
thin per-runtime adapter that invokes it. Codex consumes the Claude Stop
hook I/O format, so this one body serves both runtimes.

Declared on the `Stop` event. Scans the agent's last turn (the transcript
entries after the last REAL user message — tool-result deliveries do NOT
reset the window) for file-persisting tool calls (Write / Edit /
MultiEdit) that wrote a PLANNING ARTIFACT — a handoff, or any markdown
file under a plan/ or prompts/ directory. When such an artifact's written
content carries markdown checkbox task-list items ([ ] / [x]) at or above
a mechanical threshold, it emits a `systemMessage` WARNING on stdout.

WARN-ONLY BY CONTRACT (livespec core non-functional-requirements
§"Planning Lane guidance" → "No shadow ledger"; contracts.md
§"Driver-shipped hooks"): this hook NEVER blocks the stop — it never
emits a `decision` key and never exits non-zero — and it never auto-edits
anything. The mechanical detection internals (the planning-artifact path
predicate, the checkbox threshold, the persisting-tool set) are Driver
implementation detail and MAY be tuned without a core spec cycle, per the
contract, provided the WARN-only Stop posture holds.

Fail-open contract: ANY failure (no python3 on PATH, malformed stdin,
missing/unreadable transcript, malformed transcript lines) is a silent
pass-through with exit 0.
"""

import json
import re
import sys
from pathlib import Path

# Mechanical "shadow-ledger smell" threshold: number of markdown checkbox
# task-list items in a single persisted planning artifact.
CHECKBOX_THRESHOLD = 3

# Tool calls that persist content to disk (NotebookEdit is excluded — a
# planning handoff is never a notebook).
PERSISTING_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})

# A markdown task-list item: a list bullet followed by a [ ] / [x] box. The
# anchor at line start keeps inline prose like `[ ]` (e.g. a rule quoting
# the forbidden syntax) from matching — only real list items count.
_CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\]")


def _is_real_user_entry(*, entry: dict) -> bool:
    """A user entry typed by the human — NOT a tool_result delivery."""
    if entry.get("type") != "user":
        return False
    message = entry.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if not isinstance(content, list):
        return False
    has_text = False
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_result":
            return False
        if block.get("type") == "text":
            has_text = True
    return has_text


def _written_text(*, name: str, tool_input: dict) -> str:
    """The content a persisting tool call wrote, aggregated to one string."""
    if name == "Write":
        text = tool_input.get("content")
        return text if isinstance(text, str) else ""
    if name == "Edit":
        text = tool_input.get("new_string")
        return text if isinstance(text, str) else ""
    if name == "MultiEdit":
        edits = tool_input.get("edits")
        parts: list[str] = []
        if isinstance(edits, list):
            for edit in edits:
                if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
                    parts.append(edit["new_string"])
        return "\n".join(parts)
    return ""


def _last_turn_writes(*, entries: list[dict]) -> list[tuple[str, str]]:
    """(path, written-text) pairs persisted after the last real user message."""
    start = 0
    for index, entry in enumerate(entries):
        if _is_real_user_entry(entry=entry):
            start = index + 1
    writes: list[tuple[str, str]] = []
    for entry in entries[start:]:
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if name not in PERSISTING_TOOLS:
                continue
            tool_input = block.get("input")
            if not isinstance(tool_input, dict):
                continue
            path = tool_input.get("file_path")
            if not isinstance(path, str) or not path:
                continue
            writes.append((path, _written_text(name=name, tool_input=tool_input)))
    return writes


def _is_planning_artifact(*, path: str) -> bool:
    """A handoff, or any markdown file under a plan/ or prompts/ directory."""
    lowered = path.lower()
    if not lowered.endswith(".md"):
        return False
    name = lowered.rsplit("/", 1)[-1]
    if "handoff" in name:
        return True
    segments = lowered.split("/")
    return "plan" in segments or "prompts" in segments


def _checkbox_count(*, text: str) -> int:
    return sum(1 for line in text.splitlines() if _CHECKBOX_RE.match(line))


def _warning() -> str | None:
    """Return the systemMessage JSON, or None for a silent pass-through."""
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict) or payload.get("stop_hook_active"):
        return None
    transcript_path = payload.get("transcript_path")
    if not isinstance(transcript_path, str) or not transcript_path:
        return None
    transcript = Path(transcript_path)
    if not transcript.is_file():
        return None
    entries: list[dict] = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue  # fail-open per line: skip malformed transcript lines
        if isinstance(parsed, dict):
            entries.append(parsed)
    for path, text in _last_turn_writes(entries=entries):
        if not _is_planning_artifact(path=path):
            continue
        count = _checkbox_count(text=text)
        if count >= CHECKBOX_THRESHOLD:
            message = (
                "livespec no-shadow-ledger WARN: this turn wrote a planning "
                f"artifact ({path}) carrying {count} checkbox task items "
                "([ ]/[x]). The no-shadow-ledger rule (livespec "
                'non-functional-requirements §"Planning Lane guidance") '
                "requires a handoff to derive status from the work-item ledger "
                "as its first action: each checklist item is a session-local "
                "step OR a pointer to a real ledger id, never a parallel work "
                "queue that shadows the ledger. Replace the embedded checkbox "
                "queue with ledger-id pointers and a ledger-status query."
            )
            return json.dumps({"systemMessage": message})
    return None


try:
    warning = _warning()
except Exception:  # noqa: BLE001 — fail-open by contract
    warning = None
if warning is not None:
    sys.stdout.write(warning + "\n")
sys.exit(0)
```

## Recon — cross-repo facts for increments 3-5 (verified 2026-06-25)

Baked in so a fresh session does not re-run the survey. Verify before relying
(repos move; this is a snapshot).

**3b currency note (post-gcp2):** the no-shadow-ledger approach is now SETTLED —
see §"Pinned canonical body" and Status, not the warn-plan-persistence-shape
framing below. The driver-layout facts below remain useful for wiring the new
`Stop` hook, but BOTH Drivers now ALSO carry the red-green-replay gate (gcp2:
lefthook + CI), so the hook PRs run under the Red→Green ritual. The footgun-guard
reconciliation (228 vs 365) named below is explicitly increment-5 Conformance
work, NOT part of 3b.

**Driver repos (both exist; NOT DRY — the increment-3b gap).**

- `livespec-driver-claude`: skills at `.claude-plugin/skills/<name>/SKILL.md`;
  plugin hooks at `.claude-plugin/hooks/hooks.json` (PreToolUse:Write →
  `block-auto-memory.sh`; Stop → `warn-plan-persistence.sh`, 6 KB) PLUS
  repo-scoped `.claude/settings.json` whose PreToolUse:Bash CHAINS
  `livespec_dev_tooling.agent_hooks.pretooluse_background_guard` THEN
  `.claude/hooks/livespec_footgun_guard.py` (228 lines), and whose
  SubagentStop wires `…agent_hooks.subagent_stop_guard`. (Re-verified
  2026-06-25 post-3a.) 3b's no-shadow-ledger Stop hook must chain AFTER any
  existing Stop hook and preserve exit status per NFR §"Hook chaining".
- `livespec-driver-codex`: skills at `livespec/skills/<name>/SKILL.md`; hooks at
  `livespec/hooks/hooks.json` wiring ONLY PreToolUse:Bash →
  `livespec_footgun_guard.py`. NO `.sh` hooks (no block-auto-memory, no
  warn-plan-persistence).
- The two footgun guards are NOT byte-identical (228 vs 365 lines) — the
  cross-Driver DRY defect. Mirror the orchestrator's `prose/<name>.md` +
  thin-binding single-sourcing and core NFR §"Codex dogfooding constraints".
- `warn-plan-persistence.sh` is the literal shape to extend for the
  no-shadow-ledger hook: a Stop hook, WARN-ONLY (emits a `systemMessage`, never
  a decision key, never non-zero, fail-open), scanning the last turn for a
  planning artifact written with no persisting/ledger call.

**Orchestrator (`livespec-orchestrator-beads-fabro`).** 9 skills under
`.claude-plugin/skills/`; prose for the 5 heavyweight ops under
`.claude-plugin/prose/`. NO `plan`/`handoff` skill, NO `plan/` or `prompts/`
dir yet. `groom` is the closest analogue (heavyweight, stateful, re-entered):
copy its `SKILL.md` frontmatter; `groom` is `allowed-tools: Bash, Read, Grep,
Glob`, `capture-work-item` adds `Write` — `plan` needs `Write` too.

**Console (`livespec-console-beads-fabro`).** EXISTS (Rust), full
`SPECIFICATION/` tree. Already control-plane content in `spec.md`:
owns/does-not-own lists (`/livespec:* spec mutation semantics` is in
does-not-own) + a mermaid diagram. Increment 4's console side LANDED
(PR #34, cut `v006`): added the `Control-Plane realization` paragraph +
extended the Scope-Boundary diagram to the three-plane framing. The console
runs its OWN spec-refinement track (`prompts/spec-refinement-critique-handoff.md`)
and a `prompts/` dir with handoff files; drive the lifecycle against fixed core
with `LIVESPEC_CORE_PLUGIN_ROOT=/data/projects/livespec/.claude-plugin`.

**Core NFR integration.** The zs22.4 Planning Lane guidance sits as a `####`
under `### Orchestrator plugin ecosystem`, sibling to `#### Orchestrator-internal
Dispatcher guidance` (the NON-normative template). Increment 4's core side uses
the SAME template. `just` is referenced piecemeal (`### Toolchain pins`,
`### Enforcement-suite invocation`, `### Developer-tooling layout`) but has NO
consolidated mandate — increment 5 lands the "`just` keystone" NFR mandate.
`### Hook chaining` constrains 3b.

**Conformance Pattern (increment 5) skeleton**
(`research/factory-conformance/cross-repo-conformance-pattern.md`). Five slots:
**Contract / Mechanism / Installer (`just` recipe) / Verifier (fail-closed, in
`just check`) / Exemption**. `baseline` profile (every governed repo) + additive
layers (`fleet-infra`, `orchestrator-plugin`, `app`); declarative `adopters`
manifest in `.livespec-fleet-manifest.jsonc` (`fleet`/`adopters` arrays, each
`profile` + `posture` = `released`/`pinned`/`none`). Four tiers: author-time
(copier) / commit-time (lefthook→`just check`) / dispatch-time (orchestrator
runs installer+verifier pre-dispatch) / fleet-time (`just conformance` + drift
CI). Named concerns: Plugin-resolution, Terminology-guard, Worktree-discipline,
No-shadow-ledger, Ledger-closure, Pin-freshness. Milestones M0-M6 (M3 dogfoods
on `livespec-console-beads-fabro`; M4 on Open Brain).

## Constraints / non-negotiables

- **Dogfood the discipline.** All work in a worktree under
  `~/.worktrees/livespec/<branch>`; land via PR → rebase-merge; never
  commit on the primary checkout. `mise exec -- git …`; never
  `--no-verify`; halt and report on any hook failure.
- **No shadow ledger.** This handoff and every artifact point at ledger
  ids for status; they never embed a `[ ]`/`[x]` task queue.
- **Respect the planes.** The handoff/coordination skill is
  orchestrator-side; the reasoning capture is a Spec-Plane convention; the
  console is the Control Plane. `just` never leaks into core's functional
  surface or the `/livespec:*` skills.
- **Increment discipline.** Small, cohesive, independently mergeable,
  nothing breaks. One increment per PR.

## Handoff refresh

If context approaches budget mid-increment: wrap the in-flight increment
to a committed+pushed state, update the ledger (`bd`), print the closing
status table, and refresh this file (same epic id) with the exact
remaining work. End every session by naming the literal next-session
command.

**Literal next-session command (one path — per the self-sufficiency rule
this track codified):**

```
run prompts/livespec-zs22-handoff-planning-lane.md
```

That single path is sufficient: a fresh session opening only this handoff
and its Read-first chain can execute the next action (increment 5 / M6,
`livespec-zs22.7.7`) without re-deriving anything — AFTER confirming via the
FIRST ACTION ledger query + `bd ready` + a `git fetch` that M6 is still open and
unstarted (other sessions work this epic; see the concurrency warning in
§Status). Status comes from the FIRST ACTION ledger query, never from this file.

## Archive condition

When `livespec-zs22` closes (all increments landed, the Planning Lane
guidance in core NFR, the Conformance Pattern shipped), `git mv` this file
to `archive/prompts/` with a completion banner. The durable history then
lives in the spec, the spec history, the commits, and the ledger.
