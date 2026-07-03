# Handoff — fleet-followups

The single resumable entry point for the **fleet follow-ups & lingering cleanup**
coordination epic. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** The coordination anchor that gathers ALL post-lifecycle
  follow-ups + lingering cleanup across the fleet into one runnable point. It
  succeeds the (closed + archived) `work-item-state-machine` fleet epic. Items
  span multiple tenants (core, beads-fabro, dev-tooling, driver-codex,
  git-jsonl, runtime), so — per the fleet pattern — this anchor carries only a
  few **same-tenant (core) ledger children** (`livespec-jcc6.1/.2/.3` filed
  2026-07-01 + `.4` filed 2026-07-03; **`.1` + `.2` DONE** via factory dispatch
  (PRs #736/#734), **`.3` DONE via relocation** → beads-fabro `bd-ib-syb`,
  PR #254 — §"Session 13"; **`.4`** = reaper dead-plugin-entry pruner, `backlog`,
  held under `livespec-c1k9`, §"Session 12" — **unhold recommended**, since c1k9's
  finalized design does not cover its domain, §"Session 14"); every **cross-tenant** item
  is **prose-linked** in the inventory and its status is composed from the ledger
  (no shadow queue).
- **⚑ GitHub App-token auth — ✅ CLOSED + ARCHIVED (2026-07-03).** The GH_TOKEN
  factory-auth blocker grew into its own fleet-wide credential-model thread; epic
  **`livespec-2ef0`** is **CLOSED** with all four pillars delivered and dogfooded
  (first-class remint via livespec-runtime v0.8.0 `github_auth` + per-subprocess
  re-mint in the factory; tenant-scoped resolution + adopter isolation fail-closed;
  one primitive for factory AND standalone on all 8 clones; enforcement — fleet PAT
  `LIVESPEC_FAMILY_GITHUB_TOKEN` deleted + revoked, `gho_` OAuth out of every agent
  path, github-auth-guard hook). It absorbed `bd-ib-gsl`, superseded `bd-ib-p2e`,
  and folded in `C16`. Full record: **`plan/archive/github-app-auth/`** (do not
  resume; it succeeded the credential-wrapper epic `livespec-zd8h`).
- **⚑ FACTORY-HARDENING — ✅ COMPLETE (Session 10, 2026-07-02).** The FOUR P0
  factory-hardening threads (all `livespec-orchestrator-beads-fabro` tenant, dispatcher
  self-modifications) ALL landed and both epics (`bd-ib-mxr`, `bd-ib-fqh`) are CLOSED —
  see §"Session 10 (2026-07-02) — factory-hardening COMPLETE". The map below is retained
  as history (do NOT re-run it):
  1. **`bd-ib-fqh`** (EPIC) — factory context-completeness, re-groomed as an
     **Option-B cross-repo epic** (`acceptance_criteria`+`notes` become first-class
     `WorkItem` fields, both backends): **S1 `livespec-runtime-00u` DONE** (contract
     MERGED to `livespec-runtime` master; **v0.7.0 CUT** 2026-07-02 — release-please
     **PR #105** merged, latest release now v0.7.0; CORE already re-vendored it via
     `bump-pin` commit `4d08972`). **S2 `bd-ib-fqh.1` (beads store+`render_goal`) is
     UN-GATED** — beads-fabro's re-vendor landed (fan-out **PR #233** MERGED
     2026-07-02 01:45Z); promote `backlog→ready` from a beads-fabro session. **S3
     `bd-gj-lxr` (git-jsonl store/schema) has an INVERTED gate** — its re-vendor
     (fan-out **PR #158**) is terminally BLOCKED: v0.7.0 serializes
     `acceptance_criteria`+`notes` and git-jsonl's own schema validator rejects them
     (87 test failures, `check-coverage` red), and that schema extension IS S3's
     work — implement S3 from a git-jsonl session and land it WITH the pin bump
     (same PR or S3-first). S4 `bd-ib-fqh.2` + S5 `bd-ib-fqh.3` show `ready` in the
     ledger but carry `depends_on → bd-ib-fqh.1` edges, so dispatch stays correctly
     gated behind S2 (§"Session 8").
  2. **`bd-ib-asp`** — merge-poll fail-fast on a terminally-BLOCKED PR. `ready`.
  3. **`bd-ib-mxr`** (EPIC) — **E2E dispatch acceptance**: prove the REAL janitor +
     dispatch path green **by execution** (not mocks). Children **`bd-ib-cyv`**
     (janitor green-by-execution + provision livespec core) + **`bd-ib-mxr.1`**
     (broader real-dispatch E2E). **THE UNBLOCKER** for reliable non-core dispatch.
  All careful self-modifications — human-approved admission, never auto-dispatch blind.
- **Epic anchor:** `livespec-jcc6` (core tenant, `backlog`). Status is READ from
  the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-jcc6
  ```
- **Working model.** THIS core session **coordinates**; per-tenant grooming +
  factory dispatch happen in **each owning repo's own session** — launch the
  session from the repo that owns the work (its tenant selects via cwd, its
  `plan/` threads, its code + `just check`). Core is the anchor because the set
  is cross-tenant, not because the work lives here.
- **⚑ Golden rule.** FILE ripe work + GROOM it; DISPATCH ready, factory-safe
  slices through the factory (`/livespec-orchestrator-beads-fabro:orchestrate`
  → Codex/Fabro under the janitor gate) — NEVER hand-code inline.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan fleet-followups`.

## The next action

**✅ FACTORY-HARDENING IS COMPLETE (Session 10, 2026-07-02) — the maintainer-directed
autonomous run finished.** All four P0 threads landed and both epics (`bd-ib-mxr`,
`bd-ib-fqh`) are CLOSED; full detail + outcomes in §"Session 10 (2026-07-02) —
factory-hardening COMPLETE". The ordered plan that WAS here (cyv → asp → fqh.1 →
fqh.2/.3 → S3 → mxr.1) is retained below as the execution record — do NOT re-run it.
**The active next action: an attended `/livespec:revise` accepting/shaping
`SPECIFICATION/proposed_changes/readme-contract.md`** (the `livespec-127o.1` slice;
content is maintainer-gated — include the `tests/heading-coverage.json` co-edit in
the revise payload's `resulting_files[]`, since the proposal adds a `## README
contract` heading: one added entry in the TODO + `reason` shape the existing
entries use, path spelled `../tests/heading-coverage.json` so the wrapper's
`spec_target / path` join resolves it from the main `SPECIFICATION/` tree)
**→ then close `livespec-127o.1` in the ledger** (so the `depends_on` edge
un-gates `.2`; bd's ledger vocabulary is `--status closed` — the runtime
literal `done` recorded in §"Session 13" is a different layer, the
`WorkItemStatus` model, not the bd CLI) **→ then promote + dispatch `livespec-127o.2`** (the factory
README rewrite; it ALREADY carries a full autonomously-verifiable acceptance
block — verified §"Session 14" — so promotion is just `backlog→ready` +
`--add-label admission:auto --add-label acceptance:ai-only`) via the Session-12
dispatch mechanics (bare repo NAME `livespec`). A SECOND attended decision is queued: **unhold `livespec-jcc6.4`**
(recommended) — `livespec-c1k9`'s finalized Phase-4 design does not cover its
orphan-registry-entry domain, so the Session-12 hold condition has resolved
(§"Session 14"). The block after the `---` is patched with per-item dispositions —
most are DONE/FILED; do NOT re-run its items as originally written.

The completed plan, retained for the record:

The threads span TWO tenants — **beads-fabro** (`/data/projects/livespec-orchestrator-beads-fabro`)
and **git-jsonl** (`/data/projects/livespec-orchestrator-git-jsonl`). A driving session
orchestrates cross-tenant via `bd -C <repo>` (promote/admission, under
`with-livespec-env.sh`) + `real-work-dispatch.sh --target-repo <repo> --item <id>` (the
factory implements the self-mod in a Fabro sandbox → PR → janitor → merge). Execute in
this order:

**1. `bd-ib-cyv` (+ its epic `bd-ib-mxr`) FIRST — the janitor E2E unblocker.**
[beads-fabro; snapshot `backlog`] WHY FIRST: until it lands, EVERY non-core dispatch
(all items below are non-core) merges-but-marks-`failed:janitor-post-merge` — the
post-merge janitor doesn't provision livespec core → false-fails `check-doctor-static`;
and it's only ever MOCKED green in tests, so the gap ships invisibly. Fix = provision
core + a top-of-pyramid test running the REAL janitor to green. Promote `backlog→ready`
(+ acceptance, `admission:auto`, `acceptance:ai-only`, scope-guard) and dispatch. ⚠
BOOTSTRAPPING WRINKLE: cyv's OWN dispatch (a non-core target) hits the pre-fix janitor
false-fail → its PR merges but the run reports `failed:janitor-post-merge` →
hand-reconcile (verify PR merged + CI green on master, then `bd -C … update bd-ib-cyv
--status closed`). Once cyv lands, the janitor works for every dispatch after it. Then
dispatch **`bd-ib-mxr.1`** (broader real-dispatch E2E; `depends_on bd-ib-cyv`).

**2. `bd-ib-asp`** [beads-fabro; snapshot `ready`, ungated] — dispatcher merge-poll
fail-fast on a terminally-BLOCKED PR (today a blocked PR burns the full ~76-min poll
then exits `failed:merge-poll`). Admission-approve + scope-guard + dispatch.

**3. `bd-ib-fqh.1` (S2)** [beads-fabro; snapshot `backlog`, UN-GATED — re-vendor
**PR #233** merged] — beads store map + `render_goal` carrying
`acceptance_criteria`+`notes` + stage audit. This is the ROOT-CAUSE fix that lets DoR
scope reach the implement/review agents, RETIRING the per-dispatch scope-guard
workaround. Promote `backlog→ready` + work it. When S2 lands, **`bd-ib-fqh.2` (S4)** +
**`bd-ib-fqh.3` (S5)** un-gate (both snapshot `ready`, `depends_on bd-ib-fqh.1`) →
dispatch them.

**4. `bd-gj-lxr` (S3)** [git-jsonl; snapshot `backlog`; the trickiest] — INVERTED gate:
its v0.7.0 re-vendor **PR #158 is terminally BLOCKED (still OPEN, `mergeStateStatus:
BLOCKED`)** because v0.7.0 serializes `acceptance_criteria`+`notes` and git-jsonl's OWN
schema validator rejects them — and that schema/store extension IS S3's scope. So
implement S3 (git-jsonl store + schema carry the two fields, consistent with beads) and
land it WITH the pin bump (same PR, or S3-first then #158 goes green). Work from the
git-jsonl repo.

**5. Close the epics.** `bd-ib-mxr` + `bd-ib-fqh` close once their children are all done.

**Dispatch mechanics** (proven — `yonx` PR #762, `ek6e` #764, `yc8e` #742; reuse for
every item above):
- Admission + DoR: `bd -C <repo> update <id> --add-label admission:auto --add-label
  acceptance:ai-only` (+ a coherent autonomously-verifiable acceptance +
  `backlog→ready`). [Corrected §"Session 14": bd v1.0.5 has NO `--labels` flag —
  `--add-label` (repeatable) is the real form, verified via `bd update --help`.]
- SCOPE-GUARD (MANDATORY until `bd-ib-fqh` lands): `bd -C <repo> comment <id> "modify
  ONLY <exact files>; do NOT edit README/docs/…"` — the ONLY item-specific channel the
  Fabro brief reads today (the acceptance field is NOT in the brief; that's what
  `bd-ib-fqh` fixes). Enumerate the REAL file set yourself (grep; the item text's
  examples undercount — yonx named 2 callsites, the true set was 11).
- Dispatch:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh \
    bash /data/projects/livespec-orchestrator-beads-fabro/orchestrator-image/real-work-dispatch.sh \
    --target-repo <repo> --item <ready-id> --run
  ```
  Secrets come from `with-livespec-env.sh` (`LIVESPEC_FAMILY_GITHUB_TOKEN`,
  `ANTHROPIC_API_KEY_LIVESPEC_E2E`, `CLAUDE_CODE_OAUTH_TOKEN`, `BEADS_DOLT_PASSWORD`,
  `HONEYCOMB_INGEST_KEY_LIVESPEC`) + host `~/.codex/auth.json`; runs in
  `livespec-orchestrator:dev` (Fabro sandbox → PR → janitor `just check` + doctor →
  rebase-merge → acceptance → `done`, ~20 min). `--preflight` (no `--item`) checks
  inputs. ⚠ Until `bd-ib-asp` lands, a red-required-check PR polls the full ~76 min
  then exits `failed:merge-poll` — if a run overruns ~25 min, `gh pr checks <n>`; a red
  required check = close/fix + re-dispatch. ⚠ Until `bd-ib-cyv` lands, every non-core
  dispatch merges-but-marks-`failed:janitor-post-merge` — hand-reconcile per the cyv
  wrinkle above.

**A note on the driving session.** Most work is beads-fabro tenant; only S3 is
git-jsonl. A driving session can orchestrate ALL of it via `bd -C <repo>` +
`--target-repo <repo>` (the code work happens inside the Fabro sandbox, not the driving
session), EXCEPT S3, whose schema fix must land coupled to the blocked pin-bump PR #158
— do S3 from the git-jsonl repo. `bd-ib-cyv`/`bd-ib-asp`/S2 are careful dispatcher
self-mods: review each Fabro PR before/at merge even though admission is pre-approved.

---

**⚑ NEXT ACTIONS — factory-hardening is COMPLETE (Session 10); these formerly-deferred
items are now the active priority. Compose LIVE status before acting:**

1. **Grooming — core DONE.** `livespec-127o` (README epic) **GROOMED (Session 12
   continued)** into `livespec-127o.1` (spec README contract; propose-change FILED →
   the pending attended revise named above) + `livespec-127o.2` (factory rewrite,
   dep-gated on `.1`) — do NOT re-groom.
   **`livespec-m0xu` (template rename) is DONE (Session 11)** — groomed + landed
   (history/v155 + PR #782); m0xu + child `livespec-pzrvzm` CLOSED. See §"Session 11".
   `livespec-jcc6.3` (prose refresh) is DONE — relocated to beads-fabro `bd-ib-syb` +
   landed (PR #254, §"Session 13").
   `needs-regroom` `livespec-nylyhi` + `livespec-rmew4k` are CROSS-TENANT — groom from those repos.
2. **Cross-tenant items — FILED/DISPOSED (Session 12 continued, from the core session
   via `bd -C <repo>`; do NOT re-file):** **B4** → `bd-ib-09c` (beads-fabro
   `migrate-tenant` CLI), **C7** → `livespec-driver-codex-wqo` (driver-codex "DEFERRED"
   wording), **D9** → `livespec-dev-tooling-5kv` (dev-tooling `hydrate` worktree-pack;
   supersedes the narrow git-jsonl instance `bd-gj-hew`), **C8** disposed
   already-fixed (git-jsonl contracts.md already documents it — no filing), **D10**
   decided no-change (checks-only branch protection stands). Groom + dispatch the
   three FILED items in their owning repos' sessions.
   Plus TWO **new findings from the Session-10 run**, also FILED (`backlog`; status read
   from the ledger): (a) git-jsonl **`bd-gj-hew`** (worktree-hydration gap, a concrete
   instance of D9) — `just worktree-create` does
   NOT install the Worktree Discipline Pack (`dev-tooling/branch-protection.sh`), so `.py`
   commits fail `check-pre-commit` until `just install-worktree-pack`; fix: hydrate
   installs the pack as `bootstrap` does. (b) beads-fabro **`bd-ib-24l`**
   (self-update-canary under-trigger) — on the asp dispatch the canary logged "merge did not touch the
   dispatcher's own scripts" though asp modified `_dispatcher_engine.py`/`_dispatcher_plan.py`;
   the full janitor validated asp, but the canary's path-detection may under-fire (relates
   to the now-closed `bd-ib-mxr` E2E epic).
3. **Client-side ops** (inventory group **E**) — ✅ **DISPOSED (Session 12)**: dead plugin
   registry entries pruned (8); items 11/12 self-heal on each repo's next SessionStart
   (cwd-bound CLI, no cross-repo action); item 13 a no-op (core ledger clean). A proactive
   reaper-pruner was filed as **`livespec-jcc6.4`** (groom + dispatch via factory). See
   §"Session 12".
4. **Cross-links** (group **F**) — resume in their own repo's thread, not here.
5. **Close `livespec-jcc6`** when factory-hardening + the deferred items are done and
   nothing lingers → archive this thread to `plan/archive/`.

The two core spec-side drifts (C15, gap-dg2rdlsf) are DONE — revised in at v154
(§"Session 9 (continued 2)"). Full factory-hardening map: inventory
`research/01-followup-inventory.md` group **0**.

## Already-filed items to fold in (cite read-only; details in the inventory)

**⚑ TOP PRIORITY (all `livespec-orchestrator-beads-fabro`, P0, careful self-mods):**
`bd-ib-fqh` EPIC (context-completeness, Option-B cross-repo: S1 `livespec-runtime-00u`
DONE, v0.7.0 CUT (PR #105 merged), **S2 `bd-ib-fqh.1` UN-GATED** (re-vendor PR #233
merged — promote from a beads-fabro session), **S3 `bd-gj-lxr` INVERTED gate** (its
re-vendor PR #158 is BLOCKED on S3's own schema work — land together from a git-jsonl
session), S4 `bd-ib-fqh.2` + S5 `bd-ib-fqh.3` dep-gated on S2); `bd-ib-asp`
(merge-poll fail-fast, `ready`); `bd-ib-mxr` EPIC
(E2E dispatch acceptance — children `bd-ib-cyv` janitor-green-by-execution +
`bd-ib-mxr.1` broader E2E; THE UNBLOCKER for non-core dispatch).
Core epic children (this thread): `livespec-jcc6.1` (B2, **DONE** PR #736),
`livespec-jcc6.2` (B3, **DONE** PR #734), `livespec-jcc6.3` (C6, **DONE** via
relocation → `bd-ib-syb`, PR #254, §"Session 13").
Other core: `livespec-yc8e` (B1 reaper, **DONE** PR #742), `livespec-yonx` (io
facade, **DONE** PR #762), `livespec-ek6e` (io facade, **DONE** PR #764),
`livespec-mpkaz4` (reaper sibling), `livespec-127o` (README, GROOMED — slices
`.1`/`.2`, §"Session 12 (continued)"), `livespec-m0xu` (template rename, **DONE**
Session 11), `livespec-aava` (B5, Codex skill-picker).
Cross-tenant: `bd-ib-2wq` (beads-fabro); `livespec-dev-tooling-9j8` +13 children
(dev-tooling); `livespec-8kip` (dev-tooling gap).

## Session 2 (2026-07-01) — DoR triage + factory-boundary findings

Ran Revise / Gap / Groom / Orchestrate over the thread; the durable outcomes:

- **Revise — no-op.** `SPECIFICATION/proposed_changes/` holds only the README
  placeholder; spec-side `next` surfaces only `prune-history` (151 history
  versions, low urgency). No pending proposal to revise.
- **DoR triage (the effective "make items dispatchable" step).** The clean,
  single-coherent-done, autonomously-test-verifiable core items were promoted to
  dispatchable `ready` with acceptance + autonomy tier: **`livespec-jcc6.1`** and
  **`livespec-jcc6.2`**. `impl next` went 0 → 2 candidates. `livespec-jcc6.3`
  (prose refresh) was **held at `backlog`** — its acceptance ("the rewrite is
  correct") is not autonomously verifiable (a grep confirms old terms dropped,
  not that the new prose is right), so its honest DoR verdict is
  `not-yet-actionable`. `livespec-m0xu` moved `open` → `backlog`.
- **Gap — detection ran, capture deferred (scope).** `detect-impl-gaps` emits
  **~370 mechanical candidate gap-ids** and **0** are captured (`origin:gap`
  is empty). Blind-capturing 370 over 151 accreted spec versions would be noisy;
  capture needs a scoped pass (e.g. `--since-version <recent>` or a focused
  subtree). Deferred, not skipped.
- **Groom — targets are cross-tenant.** The only two `needs-regroom` items,
  `livespec-nylyhi` (fixes land in `livespec-driver-codex` +
  `livespec-orchestrator-beads-fabro`) and `livespec-rmew4k` (cross-repo,
  spec-gated; overlaps `livespec-4dzbcv`), groom into route-out slices, not
  core-local dispatchable work — groom them from those repos' sessions.
- **Orchestrate — ⚠️ THIS FINDING WAS WRONG; corrected in §"Session 3".** (Struck
  for the record.) The claim was that dispatch can't run from this session
  because App-token/Fabro creds are absent. That was a mis-probe: I checked the
  wrong env-var names (`LIVESPEC_APP_ID`/`FABRO_API_KEY`) and hadn't found
  `orchestrator-image/real-work-dispatch.sh`. Dispatch DOES run from this session
  via that containerized script; the real gate is the `admission:auto` approval,
  not credential absence. See §"Session 3" for the proven mechanism.

## Session 3 (2026-07-01) — factory dispatch PROVEN + scoped gap capture

- **Dispatch works from this session (Session-2 finding corrected).** The
  mechanism is the containerized `orchestrator-image/real-work-dispatch.sh` under
  the `with-livespec-env.sh` wrapper (see the command in "The next action" step
  3). The one real gate beyond `status: ready` is the **admission valve**: an item
  with the default `admission_policy: manual` is HELD ("surfaced for the
  maintainer to approve into ready, never auto-dispatched") until it carries the
  label `admission:auto`. That is the designed human-approval gate, realized at
  admission (not at status). `acceptance:ai-only` closes the loop without a final
  human sign-off; `DEFAULT_DOER = fabro` auto-assigns.
- **`livespec-jcc6.2` DONE end-to-end.** admission held → added
  `admission:auto` + `acceptance:ai-only` → re-dispatched → Fabro implemented
  (`fix: add doctor static spec target coverage`) → **PR #734** → post-merge
  janitor `just check` green (58 targets) → rebase-merge → ai-only acceptance →
  ledger **CLOSED** (`resolution:completed`). ~20 min wall-clock.
- **`livespec-jcc6.1` dispatched** the same way (admission approved).
- **Gap capture — scoped `--since-version 150`.** 236 clause candidates (201 in
  `non-functional-requirements.md`, 35 in `spec.md`); 5 parallel triage agents
  checked each against the repo. **3 genuine gaps filed** (`origin:gap-tied`,
  `backlog`): **`livespec-yonx`** (`io/fastjsonschema_facade.py` absent, core),
  **`livespec-ek6e`** (`io/structlog_facade.py` absent, core), **`livespec-8kip`**
  (`check-mutation` structured-JSON fail-summary missing; fix lands in
  `livespec-dev-tooling`). The other 233 clauses verified as genuinely
  implemented/enforced. One spec-drift note (`gap-dg2rdlsf`: coverage `source`
  clause stale vs a deliberate omit-only impl choice) → route to
  `capture-spec-drift`/`propose-change`, not a gap.

## Session 4 (2026-07-01) — yc8e DONE + factory root-cause found + two P0 items filed

- **`livespec-jcc6.1` CLOSED** (PR #736) since Session 3; epic now 2/3 children.
- **Promoted three ripe core items to `ready` + admission-approved.** `yonx`,
  `ek6e`, `yc8e` got `admission:auto` + `acceptance:ai-only` (yc8e also an
  acceptance criteria + `open→backlog→ready`). Verified the `admission:auto` label
  maps to the `admission_policy=auto` field the valve reads (`store.py:525`), so
  none are held. Preflight green (5 secrets + Codex auth + image).
- **`yc8e` FIRST dispatch FAILED at merge-poll (~76 min) — a NEW failure mode.**
  Fabro implemented the reaper fix correctly (PR #740) but ALSO deleted README.md's
  mermaid lifecycle state-diagram (out of scope; that diagram is deliberate per
  `ccd0bce` and is NOT the architecture diagram the single-source test forbids).
  Its removal starved `test_architecture_diagram_single_source.py` → coverage
  99.91% < 100% → `check-coverage` (required) failed → PR `BLOCKED` → auto-merge
  couldn't fire → the dispatcher polled the full 80-attempt budget for a merge that
  could never happen, then exited `failed:merge-poll`.
- **ROOT CAUSE traced → two P0 beads-fabro items filed (maintainer-directed TOP
  priority).** (A) The per-item brief `render_goal()` includes ONLY
  id/title/description + ledger comments — NOT the acceptance field, NOT notes — so
  DoR scope never reaches the implement/review agents. → **`bd-ib-fqh`** (P0):
  holistic context-completeness audit + fix across ALL stages. (B) The merge-poll
  loop polls only for MERGED and can't detect a terminally-BLOCKED PR, wasting the
  full budget. → **`bd-ib-asp`** (P0): fail-fast + surface the failing check. Both
  `backlog`, careful self-modifications (groom from a beads-fabro session; do NOT
  auto-dispatch blind). Anchored on `livespec-jcc6` via a ledger comment.
- **`yc8e` re-dispatched with a SCOPE-GUARD ledger comment → DONE.** A `bd comment`
  naming the exact files (the only item-specific channel the brief reads today)
  worked: PR #742, 2 files (reaper + test), janitor green (58 targets), AI
  acceptance → CLOSED, ~20 min. **Interim workaround until `bd-ib-fqh` lands:
  hand-write a scope-guard comment on each dispatch.** The review stage even
  self-reported "only touches the two files in the scope guard."

## Session 4 (part 2, 2026-07-01) — cross-repo re-groom, S1 landed, janitor E2E gap

Factory-hardening deepened from two items to **four P0 threads** (all
`livespec-orchestrator-beads-fabro`):

- **`bd-ib-fqh` re-groomed to Option B (cross-repo), maintainer-directed.** The
  "acceptance not in the brief" root cause is deeper: `acceptance_criteria` + `notes`
  aren't even on the shared `WorkItem` model, so `render_goal` can't carry them. The
  holistic fix makes them first-class `WorkItem` fields in **`livespec-runtime`**,
  propagated to BOTH orchestrator backends + the git-jsonl schema. 5 slices, 3 tenants:
  - **S1 `livespec-runtime-00u` (livespec-runtime) — DONE.** WorkItem +=
    `acceptance_criteria`/`notes` (optional-on-read); PR #104 merged, master CI green.
    ⚠ *(SUPERSEDED by §"Session 7" — v0.7.0 WAS cut 2026-07-02.)* At the time of this
    session the **v0.7.0** release was NOT cut yet — release-please **PR #105** was
    still OPEN (latest release v0.6.0); merging it was the re-vendor gate for S2/S3.
  - S2 `bd-ib-fqh.1` (beads store map + `render_goal` + audit) — `backlog`, release-gated.
  - S3 `bd-gj-lxr` (git-jsonl store + schema fields, consistent with beads) —
    `backlog`, release-gated.
  - S4 `bd-ib-fqh.2` (implement.md scope rule + review checks acceptance) — gated behind S2.
  - S5 `bd-ib-fqh.3` (remaining audited gaps) — gated behind S2.
- **`bd-ib-asp` groomed** — single `ready` slice (fail-fast on a REQUIRED
  terminal-failure check; keep polling on pending/BEHIND).
- **NEW: the janitor E2E gap (`bd-ib-mxr` epic).** Dispatching S1 exposed that the
  post-merge janitor doesn't provision livespec core → `check-doctor-static` errors
  core-not-found → the dispatch reported `failed:janitor-post-merge` even though
  PR #104 merged + CI was green (I hand-reconciled S1 to `closed`). Deeper cause: the
  janitor is only ever MOCKED green in dispatcher tests, so the gap was invisible.
  `bd-ib-mxr` (E2E dispatch acceptance) folds **`bd-ib-cyv`** (provision core + run
  the REAL janitor to green) + **`bd-ib-mxr.1`** (broader real-dispatch E2E). The
  unblocker for reliable non-core autonomous dispatch (S2/S3, `bd-ib-asp` all target
  non-core repos).
- **Dispatch scope-guard workaround (until `bd-ib-fqh` lands):** hand-write a
  `bd comment <id>` naming the exact files before each dispatch (the only
  item-specific channel the Fabro brief reads). Proven by `yc8e` (PR #742) +
  `livespec-runtime-00u` (both landed in scope).

## Session 5 (2026-07-01) — credential-wrapper epic closed; its tail relocated here

The **`credential-wrapper`** planning thread (epic `livespec-zd8h`, CORE) closed at
**100%** — all 4 children done, self-heal **PROVEN by execution** (a bare `next.py`
re-execs through the configured `credential_wrapper` → valid result). Shipped: the
`credential_wrapper` schema key + doctor callability **warn-vs-fail lever** + the
generalized beads-access-guard template, the `livespec_runtime` v0.6.0
`ensure_credentials`/`decide_credentials` helper + orchestrator `_bootstrap`
re-exec wiring, and the config key rolled out across every fleet repo. That thread
was archived to `plan/archive/credential-wrapper/` (its handoff is the completion
record). Per **relocate-never-drop**, its still-live deferred tail moved INTO this
thread's inventory as prose-linked entries (status read from the ledger, no shadow
queue):

- **`C15`** (inventory group C) — **CORE spec-side**: `contracts.md` callability
  **warn-vs-fail lever** prose refinement (impl→spec drift — the clause still says
  an unresolvable wrapper "fires `fail`", but the shipped lever WARNS so CI stays
  green). The exact drop-in clause is in the inventory entry. File from a CORE
  session via `/livespec:propose-change` → `/livespec:revise` (no ledger child).
- **`C16`** (group C) — **adopters** (openbrain, dolt-server): add
  `credential_wrapper` + install the guard, from each adopter's OWN session; gated
  on `D17`.
- **`D17`** (group D) — **fleet / core decision**: reconcile
  `.livespec-fleet-manifest.jsonc` `adopters: []` — decide whether openbrain +
  dolt-server register as adopters (each brings its own wrapper + tenant password).
- **`D18`** (group D) — **livespec-runtime**: refresh the stale `uv.lock`
  (self-pin 0.4.0 → 0.6.0), from the runtime session.

**Disposed, not relocated:** the epic's 5th tail item — fleet CORE-pin bumps to
carry the callability check outward — is **auto-resolving**: `bump-pin` rewrites
every sibling's `compat.pinned` to the latest CORE release on the next
`feat:`/`fix:` fan-out (self-heal does NOT need the pin bumps). No action item.

## Session 6 (2026-07-02) — GH_TOKEN factory-auth → dedicated github-app-auth thread

A console canary (`livespec-console-beads-fabro`) failed pre-launch needing `GH_TOKEN`;
investigation + a cited deep-research pass (primary GitHub docs) established the fix, which
grew into a fleet-wide credential-model track and was spun out to its **own dedicated
thread** `plan/github-app-auth/` (epic **`livespec-2ef0`**, core; PR #752). Scope:
standardize the fleet on GitHub **App installation tokens** for BOTH factory dispatch AND
standalone agent worktree commits; retire the fleet PAT (`LIVESPEC_FAMILY_GITHUB_TOKEN`) +
remove the human `gho_` OAuth from the agent path. Four pillars — first-class remint
(survives >1h), tenant-scoped resolution + adopter isolation (fleet = adopter #0,
fail-closed), one primitive for factory + standalone, OS/VPS enforcement. It **absorbs
`bd-ib-gsl`** (factory slice), **supersedes `bd-ib-p2e`** (PAT-grant stopgap → close
obsolete on groom), and **folds in `C16`** (openbrain adopter wrapper). Successor to the
closed credential-wrapper epic `livespec-zd8h`. Resume via
`/livespec-orchestrator-beads-fabro:plan github-app-auth`.

## Session 7 (2026-07-02) — v0.7.0 cut; `bd-ib-fqh` S2/S3 un-gated

Resumed to unblock the `bd-ib-fqh` cross-repo chain. Verified LIVE (not from prose):
`livespec-runtime` **v0.7.0 was NOT yet cut** — release-please **PR #105** was still
OPEN, latest release v0.6.0 (the handoff's earlier correction was right; an older
`livespec-jcc6` ledger comment claiming "released v0.7.0" was stale). Maintainer
authorized the cut.

- **Merged PR #105 (rebase) → v0.7.0 CUT** (2026-07-02 01:44Z); release-please
  immediately created the v0.7.0 tag/release.
- **CORE already re-vendored v0.7.0** via the `bump-pin` fan-out commit `4d08972`
  ("chore(deps): bump livespec-runtime pin to v0.7.0" — updated the vendored
  `work_items/types.py`, `.vendor.jsonc`, `pyproject.toml`, `uv.lock`).
- **`bd-ib-fqh` S2 (`bd-ib-fqh.1`, beads-fabro) + S3 (`bd-gj-lxr`, git-jsonl) are no
  longer release-gated** — they now wait ONLY on their OWN tenants' `bump-pin`
  re-vendor of v0.7.0. Next: from a beads-fabro / git-jsonl session, verify the
  re-vendor landed and promote each `backlog→ready`, then S4/S5.
- **Untouched finding:** an in-flight, uncommitted refresh of
  `plan/github-app-auth/handoff.md` sits on the PRIMARY checkout (another track's
  work; stuck because the primary-checkout commit-refuse hook blocks committing it
  there — it must be moved into a worktree by that track). NOT touched here.

## Session 8 (2026-07-02) — S2 un-gated / S3 gate inverted; both io facades dispatched

Resumed to execute next-action steps 2–3. Composed status LIVE and found the
`bd-ib-fqh` chain had moved:

- **S2 (`bd-ib-fqh.1`, beads-fabro) is UN-GATED.** Its v0.7.0 re-vendor landed —
  fan-out **PR #233** (`chore(deps): bump livespec-runtime pin to v0.7.0`) MERGED
  2026-07-02 01:45Z. Next: promote `backlog→ready` + work it from a beads-fabro
  session. (A stale local clone can hide this — verify against GitHub, not the
  checkout.)
- **S3 (`bd-gj-lxr`, git-jsonl) has an INVERTED gate.** Its re-vendor, fan-out
  **PR #158**, sits terminally BLOCKED: required check `check-coverage` fails with
  **87 test failures** — v0.7.0's `WorkItem` now serializes `acceptance_criteria` +
  `notes` on every record and git-jsonl's OWN schema validator rejects them
  (`unexpected extra keys`). That schema/store extension IS S3's scope, so S3 isn't
  waiting on the re-vendor — the re-vendor is waiting on S3. Implement S3 from a
  git-jsonl session (`/data/projects/livespec-orchestrator-git-jsonl`) and land it
  WITH the pin bump (same PR or S3-first). PR #158 is
  also a live specimen of the terminally-BLOCKED-PR state `bd-ib-asp` will
  fail-fast on.
- **S4/S5 (`bd-ib-fqh.2`/`.3`) read `ready` in the ledger** — not premature: both
  carry explicit `depends_on → bd-ib-fqh.1` edges, so dispatch stays gated behind
  S2. No action needed.
- **`livespec-yonx` DONE via factory** — scope-guard comment enumerated the facade
  + the REAL callsite set (11 `fastjsonschema.compile` callsites across
  `validate/`; the acceptance text had named only 2 as examples) + 1 test file →
  **PR #762** merged, diff exactly the 13 scoped files, post-merge janitor green
  (58 targets), ai-only acceptance, ledger CLOSED (~31 min).
- **`livespec-ek6e` DONE via factory** the same way (scope guard: facade +
  `__init__.py` + `commands/revise.py` — a second structlog callsite the item text
  missed — + 1 test file) → **PR #764** merged, diff exactly the 4 scoped files,
  post-merge janitor green, ai-only acceptance, ledger CLOSED (~28 min).
- With both io facades landed, the three `--since-version 150` capture-pass gaps
  are 2/3 closed (core); the remaining one is `livespec-8kip` (dev-tooling tenant).
  Core's dispatchable-`ready` queue is now EMPTY — the remaining core items need
  grooming (`127o`, `m0xu`) or aren't autonomously verifiable (`jcc6.3`).

## Session 9 (2026-07-02) — live status re-verified; C15 confirmed ripe-to-file

Resumed and composed status LIVE from the core ledger (never from this file). The
Session-8 picture held, with two durable outcomes:

- **Core-tenant LIVE snapshot.** Epic `livespec-jcc6` **backlog · 2/3 (66%)**
  (`.1`/`.2` closed, `.3` held). **Core dispatchable-`ready` queue: EMPTY** (`bd
  list --status ready` → "No issues found") — nothing is factory-dispatchable from
  this core session without grooming first. `livespec-127o` + `livespec-m0xu` +
  `livespec-jcc6.3` + `livespec-aava` + `livespec-mpkaz4` all `backlog` (minor
  drift since Session 8: `m0xu` completed its `open→backlog` move; `mpkaz4` also
  `open→backlog` — both harmless). The FOUR P0 factory-hardening threads
  (`bd-ib-mxr`/`bd-ib-cyv`, `bd-ib-asp`, `bd-ib-fqh` S2/S3) remain the top priority
  but are ALL cross-tenant — unworkable from this core session (the `bd` cwd-tenant
  trap); work them from beads-fabro / git-jsonl / runtime sessions.
- **⚑ C15 (contracts.md warn-vs-fail lever) VERIFIED live in code + spec — ripe to
  file in ONE step.** Confirmed against origin/master (not the memo): the shipped
  check `.claude-plugin/scripts/livespec/doctor/static/config_named_cli_callability.py`
  (`_evaluate`, the `_CREDENTIAL_WRAPPER_KEY` + `_RESOLVE_UNRESOLVABLE` branch)
  **warns** on an unresolvable `credential_wrapper` first token (host wrapper
  legitimately absent on CI) and keeps **`fail`** only for a resolved-but-not-executable
  token. But `SPECIFICATION/contracts.md` still says the opposite in **TWO** spots:
  **line 135** (the `config-named-cli-callability` invariant paragraph) — "*a missing
  or non-executable resolution fires `fail`*" — and the **line 61** parenthetical —
  "*(its first token MUST resolve to an executable)*". Both must be reconciled to the
  warn-vs-fail lever. The exact drop-in clause is already drafted in
  `research/01-followup-inventory.md` group C item **15**. **Next-session action:**
  route C15 via `/livespec:propose-change` (a spec proposal the maintainer accepts
  later via `/livespec:revise`; no ledger child) — targeting the line-135 paragraph
  with the drafted clause and softening the line-61 parenthetical to match. Left
  UNFILED here deliberately: filing is an outward-facing spec-contract change the
  maintainer was mid-deciding when this session composed status; it is now fully
  de-risked and one step from filing.

The core-session-actionable set is otherwise unchanged: **groom `livespec-127o`**
(README epic) / **groom `livespec-m0xu`** (template rename) to produce dispatchable
slices (both maintainer-owned cuts — `groom` files nothing until approval). `jcc6.3`
stays held (acceptance not autonomously verifiable). Everything else is cross-tenant
or client-side.

## Session 9 (continued, 2026-07-02) — C15 + gap-dg2rdlsf filed as spec proposals

Under a maintainer directive to continue autonomously, the two verified CORE
spec-side drifts were filed as pending proposals (both reversible — a `revise` pass
accepts/rejects them; no live-spec edit yet, no ledger children):

- **C15 FILED → `SPECIFICATION/proposed_changes/callability-warn-fail-lever.md`**
  (**PR #769**, merged). Reconciles the `credential_wrapper` callability drift
  (`contracts.md` line 135 invariant paragraph + line 61 parenthetical) to the
  shipped warn-vs-fail lever. Inventory item 15 marked FILED.
- **gap-dg2rdlsf FILED → `SPECIFICATION/proposed_changes/coverage-omit-only-not-source-allowlist.md`**
  (**PR #770**, merged). Reconciles the coverage `source`-allowlist drift
  (`non-functional-requirements.md` §"Code coverage thresholds" + `contracts.md`
  §"Python-rule compliance") to the shipped `omit`-only blocklist, restating the
  invariant + the load-bearing no-`source`-allowlist constraint (architecture-not-
  mechanism). This was the last known CORE spec-side drift from the Session-3
  `--since-version 150` capture pass.

**Both proposals were REVISED IN** (see §"Session 9 (continued 2)" below) — the queue
is back to README-only; do NOT re-run `/livespec:revise` (it would exit 3 on an empty
queue) and do NOT re-file either via `propose-change`.

## Session 9 (continued 2, 2026-07-02) — revise v154 landed; thread spec-side drift work COMPLETE

Ran `/livespec:revise` (maintainer-invoked) over the two pending proposals; both
**accepted** → history **v154** cut (**PR #772**, merged; full `just check` +
pre/post-step doctor static green):

- **C15 landed** — `contracts.md` now carries the shipped `credential_wrapper`
  warn-vs-fail lever (invariant paragraph + §"Spec-side CLI contract" parenthetical).
- **gap-dg2rdlsf landed** — `non-functional-requirements.md` §"Code coverage
  thresholds" + `contracts.md` §"Python-rule compliance" now describe the shipped
  `omit`-only blocklist + the no-`source`-allowlist constraint.

Both proposals moved to `history/v154/proposed_changes/` with paired `-revision.md`
files; `proposed_changes/` is README-only. No `##`/`###` heading changes (payload
builder asserted it; heading-coverage untouched). The non-gating LLM post-steps
(`capture-impl-gaps` per-gap consent; doctor LLM objective/subjective) were NOT run
in this unattended pass — both changes make the spec match already-shipped impl, so
by construction they introduce no new spec→impl gap; run `/livespec:doctor` anytime.

**⚑ THREAD SPEC-SIDE DRIFT WORK IS COMPLETE.** No pending proposals remain. The
remaining CORE work is maintainer-owned grooming (`livespec-127o` README epic,
`livespec-m0xu` template rename) or held (`livespec-jcc6.3`); the top-priority
factory-hardening threads (`bd-ib-mxr`/`bd-ib-cyv`, `bd-ib-asp`, `bd-ib-fqh` S2/S3)
stay cross-tenant (work from beads-fabro / git-jsonl / runtime sessions). Consider
closing `livespec-jcc6` once the two remaining core items are groomed + dispatched
and nothing lingers.

## Session 9 (continued 3, 2026-07-02) — priority reset: factory-hardening FIRST; grooming DEFERRED

Maintainer directive (mid-session, interrupting a `groom livespec-127o` start):
**"autonomously complete all the factory-hardening ones as the first priority, leave
grooming until after those are complete. Update that as your plan and handoff to a
fresh session."** Acted on:

- **Groom of `livespec-127o` ABORTED** — clean (groom is read-only until approval;
  nothing was filed). It stays `needs-regroom`-eligible for later.
- **"The next action" REWRITTEN** to make the factory-hardening threads the singular
  autonomous top priority with a full ordered execution plan (cyv/mxr janitor
  unblocker FIRST → asp → fqh.1 S2 → fqh.2/.3 S4/S5 → git-jsonl S3), and to move
  grooming + all other core work into an explicit DEFERRED block.
- **LIVE cross-tenant status composed this session** (verify again on resume; do not
  trust): beads-fabro `bd-ib-asp`=`ready` (ungated), `bd-ib-fqh.1`/`bd-ib-fqh.2`/`bd-ib-fqh.3`
  present (fqh.1 `backlog` un-gated; fqh.2/.3 `ready` but dep-gated on fqh.1),
  `bd-ib-cyv`/`bd-ib-mxr`/`bd-ib-mxr.1`/`bd-ib-fqh`=`backlog`; git-jsonl `bd-gj-lxr`=`backlog`.
  Blocking-PR states: beads-fabro **PR #233 MERGED** (S2 un-gated); git-jsonl **PR #158
  still OPEN + BLOCKED** (S3 pending). Nothing dispatched this session — the maintainer
  asked for a handoff, and this is a core session; execution is for the fresh session.
- **`admission:auto` is pre-authorized** for these threads by the directive above, but
  each is a careful dispatcher self-mod — keep the scope-guard + PR review.

**⚑ RESUME = execute "The next action" factory-hardening plan autonomously.** A fresh
session resumes via the command below and drives the cross-tenant dispatches (bd -C /
--target-repo); grooming does NOT start until every factory-hardening thread is done.

## Session 10 (2026-07-02) — factory-hardening COMPLETE (all 7 items landed autonomously)

Under the maintainer's standing "autonomously complete all factory-hardening first"
directive, all four P0 threads were driven to done in ONE session — six items via factory
dispatch (`real-work-dispatch.sh --target-repo`), one (S3) hand-implemented via a fork.
Both epics closed. Every merged PR was reviewed for scope; all held (no docs/spec
over-reach).

- **`bd-ib-cyv` DONE (PR #237).** The janitor E2E unblocker: the host-side post-merge
  janitor now provisions livespec core (clones core at the target's `.livespec.jsonc`
  `compat.pinned` ref into `<janitor-checkout>/.livespec-core`, runs `just check` with
  `LIVESPEC_CORE_PLUGIN_ROOT` set), so `check-doctor-static` passes for non-core dispatches;
  a core-clone failure degrades green (not false-fail). Plus a top-of-pyramid E2E test that
  runs the REAL janitor to green. Its OWN dispatch hit the expected pre-fix janitor
  false-fail → hand-reconciled + closed. **After it landed, every subsequent non-core
  dispatch went fully green with no reconcile** (proven by asp/fqh.*/mxr.1, all exit 0).
- **`bd-ib-asp` DONE.** Merge-poll now fail-fasts on a REQUIRED check with a terminal-failure
  conclusion (surfacing the check name via `statusCheckRollup`), keeps polling on
  pending/BEHIND — no more ~76-min burn. (A self-contradictory pre-existing scope-guard
  comment on the item — "edit parse_pr_view but do NOT edit _dispatcher_plan.py", where those
  live — was corrected with a superseding comment before dispatch.)
- **`bd-ib-fqh` EPIC DONE (all 5 slices).** S1 `livespec-runtime-00u` (v0.8.0 WorkItem
  fields, prior); S2 `bd-ib-fqh.1` (beads store map + `render_goal` emits acceptance+notes,
  PR #243); S3 `bd-gj-lxr` (git-jsonl, below); S4 `bd-ib-fqh.2` (implement.md
  scope-minimalism + review.md checks acceptance, PR #244); S5 `bd-ib-fqh.3` (spec_id in the
  goal + pr.md-from-acceptance + audit closed, PR #245). **`render_goal` now carries full
  work-item context (acceptance/notes/spec_id) into every stage AND implement/review enforce
  scope-minimalism — the per-dispatch scope-guard workaround is RETIRED** (kept as cheap
  insurance for the remaining careful self-mods, but no longer load-bearing).
- **`bd-ib-mxr` EPIC DONE.** `bd-ib-cyv` + `bd-ib-mxr.1` (PR #246: extended the E2E to the
  full merge→janitor→accept→done path + backstopped the two mocked scenario stubs). The real
  janitor + accept path is proven by execution, not mocks.
- **`bd-gj-lxr` (S3) DONE (git-jsonl PR #160).** git-jsonl now carries
  `acceptance_criteria`+`notes`: schema widened 17→19 canonical keys through the livespec
  lifecycle (history/**v014**) + `store.py` map + v0.8.0 vendor bump — one coherent PR.
  **Targeted v0.8.0 via #159, NOT the handoff's #158/v0.7.0 (stale)**; both #158 + #159
  closed as superseded. This was a git-jsonl-only spec change (livespec core does not
  enumerate the record schema; it leaves it to each backend — verified).

**Drifts corrected (were stale in this handoff — do not trust the retained record on these):**
- **Dispatch auth migrated PAT → GitHub App tokens.** `real-work-dispatch.sh` now requires
  `GITHUB_APP_ID` + `GITHUB_PRIVATE_KEY` (installation tokens minted in-container,
  remint-capable); the fleet PAT `LIVESPEC_FAMILY_GITHUB_TOKEN` is retired (github-app-auth
  track landed, PR #235). Preflight is green with the App env from `with-livespec-env.sh`.
- **livespec-runtime is now v0.8.0** (was v0.7.0; `priority` removed for `rank`); beads-fabro
  + git-jsonl both vendored on v0.8.0 (still carries acceptance_criteria+notes).

**Dispatch pattern confirmed (reuse for grooming's dispatchable slices):** promote
`backlog→ready` + `--add-label admission:auto` + `--add-label acceptance:ai-only` + a
coherent autonomously-verifiable acceptance (+ optional scope-guard `bd comment`, now that
fqh landed) → `real-work-dispatch.sh --target-repo <repo> --item <id> --run`. **Gotcha:** the
pre-dispatch ledger-conformance gate BLOCKS the whole dispatch if ANY ledger item has a
non-livespec status (beads-native `open`); normalize stragglers to `backlog` first (4 such
github-app-auth follow-ups blocked the first cyv attempt). **Observed:** concurrent activity
on beads-fabro + core master from another session (spec critiques, plan-archive) —
non-conflicting (the dispatcher fresh-clones master per dispatch).

## Session 11 (2026-07-02) — livespec-m0xu (template rename) GROOMED + COMPLETED

Resumed fleet-followups; re-verified LIVE that factory-hardening is complete (both epics
closed) and core CI is green. Maintainer directed grooming `livespec-m0xu` (the
impl-plugin→orchestrator-plugin copier-template rename), then "run it all autonomously."
Executed end-to-end; **m0xu + its Slice-2 child `livespec-pzrvzm` are CLOSED**, the rename
is fully landed and verified.

- **Groomed m0xu via the `groom` operation** (maintainer-approved **PATH-ONLY** cut).
  Grooming CORRECTED m0xu's own premise: its description said to "backfill `_subdirectory`
  in every sibling's `.copier-answers.yml`", but the siblings carry NO `_subdirectory` key —
  it lives ONCE in core's root `copier.yml`. So the cross-repo work COLLAPSED to a
  verification, not per-sibling edits. Also disambiguated the overloaded term `impl-plugin`:
  the **template PATH** (renamed) vs the **repo-class/role** term (deliberately KEPT — a
  separate future rename). Two slices filed; m0xu regroomed out.
- **Slice 1 — spec path-rename (human-gated) DONE.** `/livespec:propose-change` →
  `/livespec:revise` renamed `templates/impl-plugin/` → `templates/orchestrator-plugin/`
  across the live spec (contracts.md + non-functional-requirements.md), preserving the 3
  repo-class/role refs. **history/v155** (PRs #780/#781, merged; full just check + doctor green).
- **Slice 2 — core code rename DONE.** `git mv` the template dir + `copier.yml`
  `_subdirectory` + the dev-tooling/doctor checks + tests + the drift workflow + the
  fleet-manifest path comment. **PR #782** merged (`a304b09`, `fix:` — Red-Green-Replay
  ritual). Verified on origin/master: dir renamed, 0 residual real path refs, role/class refs
  intact, CI green. **Sibling `copier update --vcs-ref=master` resolves the renamed subdir
  (exit 0** from an isolated git-jsonl clone) — siblings safe on next update.
- **⚑ FLEET FINDING surfaced + filed + FIXED: the factory App token lacked `workflows`
  permission.** Slice 2's FIRST attempt was a factory dispatch; Fabro implemented the rename
  correctly but GitHub REJECTED the push because the diff touches
  `.github/workflows/copier-update-drift.yml` and the fleet App installation token lacked
  `workflows: write`. This blocks ANY factory dispatch touching `.github/workflows/**`. Filed
  **`livespec-2ef0.1`** (github-app-auth epic); the github-app-auth track FIXED it at source
  (App now carries Workflows: Read/write, verified on installation 131208965; openbrain
  adopter App too) and **CLOSED `2ef0.1`**. Future workflow-touching dispatches now work
  through the factory. For THIS slice, since the operator session's `gh` token carried the
  `workflow` scope, Slice 2 was completed as OPERATOR work (worktree → PR → merge, full just
  check + doctor + CI gates).
- **Execution lesson:** a `fork` subagent is UNRELIABLE for a delegated TASK — it inherits
  the parent's context and acts AS the parent (the first Slice-1 fork did nothing but echo a
  status message). Use a fresh `general-purpose` agent for delegation; verify its claims
  against canonical committed state (`git show origin/master`).

**Remaining fleet-followups priorities** (unchanged except m0xu now done): groom
`livespec-127o` (README); file the still-unfiled CROSS-TENANT items (B4/C7/C8/D9/D10) from
their own repos' sessions; client-side ops (group E); then close `livespec-jcc6`.

## Session 12 (2026-07-03) — group E client-side ops DISPOSED; dead plugin-entries pruned; pruner filed (jcc6.4)

Resumed fleet-followups; maintainer chose **Client-side ops (group E)**. Composed core
ledger status LIVE (epic `livespec-jcc6` backlog · 2/3 before this session; core `ready`
queue EMPTY; **0** open/in_progress/blocked/deferred stragglers). Established plugin
execution context FIRST (`claude plugin marketplace list` + `installed_plugins.json` map)
rather than assuming. Full group-E disposition:

- **Item 11 (plugin cache stale fleet-wide) — self-heals; no cross-repo action possible.**
  4 active repos (`livespec-console-beads-fabro`, `openbrain`,
  `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-beads-fabro`) carry stale
  project-scope pins, but each **auto-refreshes at its own next SessionStart** (this core
  session did `055ce0ea→f79abb88` at startup). `claude plugin update --scope project` is
  **cwd-bound** — no cross-repo targeting — so pre-refreshing from core gains nothing
  durable (the next session in each repo does the identical update).
- **Item 11b (dead-path entries) — PRUNED (8 removed).** `installed_plugins.json` held **8
  inert project-scope entries** pointing at gone paths: 2 removed worktrees
  (`…/livespec-console-beads-fabro-wt-bootstrap-rust-infra`,
  `~/.worktrees/livespec/factory-conformance-capture`) + 1 `/tmp` scratchpad
  (`…/scratchpad/lsr-clean`). They never load (no active cwd matches) and never self-heal.
  Backed up (`…installed_plugins.json.bak.predeadprune-20260703052501`), then dropped every
  `scope==project` entry whose `projectPath` is missing → 8 removed, 21 kept, valid JSON,
  core's own scope (latest) preserved, 0 remaining dead.
- **Item 12 (openbrain pin bump) — same self-heal.** openbrain scope = `livespec 0.2.0`
  (stale); refreshes on openbrain's next session, or operator `/plugin install`+restart
  *in an openbrain session*. Not doable from core.
- **Item 13 (open-item status reclassification) — NO-OP for core.** Core ledger is clean
  (0 beads-native `open` stragglers; all 32 non-closed are `backlog`). Any stragglers would
  be cross-tenant.

- **⚑ Maintainer Q: "how do we proactively prune these?" → root-caused + FILED
  `livespec-jcc6.4`.** There is **no built-in** proactive mechanism: Claude Code's own
  sweep (`~/.claude/plugins/.last_inuse_sweep`) GC's unused cache dirs but leaves dead
  registry entries (all 8 persisted through it); `claude plugin prune|autoremove` only
  removes auto-installed *dependencies*; the worktree reaper has no plugin-registry
  knowledge. Root cause: ephemeral project dirs (worktrees + `/tmp` scratchpads) get
  project-scope plugin installs via SessionStart, then the path is deleted, orphaning the
  entry. **Maintainer chose the shape: fold a path-gone sweep into the worktree reaper**
  (`dev-tooling/reap_stale_worktrees.py`) — a general "scope==project AND path gone → drop"
  end-of-run pass (backup + `--dry-run`, catches `/tmp` too). Filed as **`livespec-jcc6.4`**
  (core, P3, `backlog`, child of the epic; autonomously-verifiable acceptance = a unit test
  over a synthetic registry in a temp HOME). Per the golden rule this was FILED, not
  hand-coded — groom + dispatch it via the factory. Epic is now **2/4** (`.1`/`.2` closed,
  `.3` held, `.4` new).

## Session 12 (continued, 2026-07-03) — cross-tenant items FILED from core; 127o GROOMED; jcc6.4 held under c1k9; D10 decided

Maintainer directed finishing the remaining fleet-followups work autonomously (after clearing
gates up front). Proved cross-tenant filing FROM THE CORE SESSION works: `bd -C <repo> create`
routes to any fleet tenant (the "cwd-tenant trap" is avoidable, not absolute — shared fleet
password authenticates each tenant's SQL user; dry-run confirmed). Each item was VERIFIED live
against the owning repo's origin/master (via parallel sub-agents) before filing.

- **Cross-tenant filings (B4/C7/C8/D9):**
  - **C7 FILED → `livespec-driver-codex-wqo`** (driver-codex, P3). Verified: the beads tenant
    IS wired + connected (bd list ok; `.beads/config.yaml` committed, server-mode
    user/db=livespec-driver-codex) but `.livespec.jsonc:24-29` + `AGENTS.md:27,38` still say
    "DEFERRED". (The item said CLAUDE.md; it's the AGENTS.md symlink.)
  - **B4 FILED → `bd-ib-09c`** (beads-fabro, P3, feature). Verified no `migrate-tenant` command
    exists; primitives `register_custom_statuses` (store.py:319) + `legacy_seed`
    (rebalance_ranks.py:74) live in beads-fabro (runtime is substrate-neutral). Built factory-side.
  - **D9 FILED → `livespec-dev-tooling-5kv`** (dev-tooling, P3). Verified: `worktree_create`/
    `worktree_hydrate` (worktree-pack/worktree-lib.sh:114/:150) run only the ecosystem hook, not
    `install-worktree-pack`, so fresh worktrees lack the pack (gitignored in consumers) →
    `just check` fails until manual install; bootstrap DOES install it. Single-source dev-tooling
    fix; prose-links to (supersedes) the narrow git-jsonl instance **`bd-gj-hew`**.
  - **C8 DISPOSED as already-fixed** (no filing). git-jsonl's shipped `contracts.md:406-411`
    already documents the policy-fields-drop-on-write deliberately; the only stale cell is in a
    FROZEN livespec `plan/archive/` design doc (do-not-edit). Verification saved a redundant item.
- **`livespec-127o` (README) GROOMED** into two dependency-layered slices (maintainer-authorized):
  **`livespec-127o.1`** (spec README contract in `contracts.md`, CORE-only scope, adjacent to
  Fleet-agent-instruction-core) and **`livespec-127o.2`** (rewrite README to conform, factory,
  `depends_on .1`). **Slice-1 propose-change FILED** this PR →
  `SPECIFICATION/proposed_changes/readme-contract.md` (drafted via a sub-agent; the CONTENT is
  maintainer-gated at `/livespec:revise` — do NOT auto-revise). Next: run `/livespec:revise` to
  accept/shape it (adds the `## README contract` heading → needs the `tests/heading-coverage.json`
  co-edit in the revise payload's `resulting_files[]`), then dispatch Slice 2.
- **`livespec-jcc6.4` HELD under `livespec-c1k9`** (NOT dispatched). Discovered while dispatching
  jcc6.4: the ledger-conformance gate blocked it on a lone core straggler — **`livespec-c1k9`**, a
  **P0 epic another session filed today** ("Fleet plugin currency: every new session runs the
  latest released plugin builds", thread `plan/fleet-plugin-currency/`) that SUBSUMES jcc6.4's
  dead-entry-cleanup domain ("coherent cache"). Maintainer decision: link jcc6.4 under c1k9 and
  HOLD standalone dispatch until c1k9's investigation decides how orphan-cleanup ships (avoids
  pre-empting the active P0 design). Normalized c1k9 `open→backlog` (unblocks all core dispatch;
  transparency comment) and demoted jcc6.4 `ready→backlog` with a held-pending-c1k9 comment.
  ⚑ **Dispatch mechanics learned:** `real-work-dispatch.sh --target-repo` takes the bare repo
  NAME (`livespec`), NOT a filesystem path (a path becomes `thewoolleyman/<path>` → 404). Preflight
  passes with App tokens (`GITHUB_APP_ID`+`GITHUB_PRIVATE_KEY`) + image `livespec-orchestrator:dev`.
- **D10 (branch-protection review policy) DECIDED — no change.** Keep checks-only / 0 required
  reviews: requiring human reviews would break the dark factory's unattended auto-merge. Revisit
  only when external human contributors arrive. No config change; no ledger item.

**Remaining fleet-followups priorities:** run `/livespec:revise` to accept `readme-contract.md`
(Slice-1 content gate) → then dispatch Slice 2 (`livespec-127o.2`); the cross-tenant items are now
filed (groom + dispatch each in its owning repo's session); `jcc6.4` stays held under `c1k9`;
**`jcc6.3` is DONE — executed in §"Session 13"** (relocated to `bd-ib-syb`, landed PR #254).
Close `livespec-jcc6` once its remaining child resolves (`.4` held-under-c1k9) and the README
slices land — not yet.

## Session 12 (continued 2, 2026-07-03) — jcc6.3 researched: proper repo = beads-fabro; reframed as a fable-judged small fix

Maintainer directed researching jcc6.3's proper repo and reworking it so the NEXT session
**judges the rewrite itself** (via a fable-model sub-agent), asking the maintainer only where
necessary — instead of leaving it indefinitely held on "acceptance not autonomously verifiable".
Researched live against origin/master:

- **Proper repo = `livespec-orchestrator-beads-fabro`.** The `capture-work-item` + `plan` prose
  lives ONLY at that repo's `.claude-plugin/prose/{capture-work-item,plan}.md`. Core ships NO such
  prose (only the 8 spec-side ops); **`livespec-orchestrator-git-jsonl` ships NO prose at all**; the
  drivers ship SKILL.md bindings, not prose. So **`livespec-jcc6.3` is a beads-fabro-tenant item
  mis-filed as a core child** → relocate it there when picked up (relocate-never-drop).
- **Scope is MUCH smaller than the 2026-07-01 premise** ("old schema: status=open + priority, no
  rank"). The prose was refreshed since: `capture-work-item.md` already uses `rank` (3×) and has NO
  `priority`; `plan.md` has no work-item-schema field references at all (its "open" matches are
  English — "open thread"). The ONE residual stale marker is **`capture-work-item.md:72`
  `status="open"`** — and `open` is NOT a valid status in the current model, so it should be
  `"backlog"` (the intake entry state). Plus a consistency pass to confirm nothing else drifted.
- **Schema source of truth (judge the rewrite against this):**
  `livespec-runtime/livespec_runtime/work_items/types.py` —
  `WorkItemStatus = Literal["backlog","pending-approval","ready","active","acceptance","blocked","closed"]`
  (NO `"open"`), `rank` as the SOLE ordering key (`priority` retired), the 22-field record; and
  `lifecycle.py` `LaneName` for the derived lanes. The prose already imports
  `from livespec_runtime.work_items.rank import key_between`.

**Next-session plan for jcc6.3 (judge in-session; escalate only where necessary):**
1. Work it FROM a beads-fabro session (`cd /data/projects/livespec-orchestrator-beads-fabro`).
   Relocate the ledger item: file a beads-fabro `origin:freeform` item for the prose refresh and
   dispose the mis-filed core child `livespec-jcc6.3` as relocated (cite this finding).
2. Draft the fix: reconcile `capture-work-item.md:72` `status="open"` → the correct valid status
   (likely `"backlog"`); scan BOTH prose files for any other drift vs `types.py`/`lifecycle.py`.
3. **Judge correctness with a fable-model sub-agent** — this is how the "not autonomously
   verifiable" DoR blocker is resolved (delegated model judgment, not a standing human gate).
   Dispatch a sub-agent **running the `fable` model** to independently read the drafted prose + the
   schema source of truth (`livespec-runtime work_items/types.py` + `lifecycle.py`) and verdict
   whether the new prose accurately + completely describes the current 7-state + `rank` model,
   flagging any residual drift. The driving session reconciles the verdict.
4. **Ask the maintainer ONLY where necessary** — where the fable judge is genuinely uncertain or a
   real wording/product call arises (e.g. whether the capture example should show the raw
   beads-native create-then-normalize vs. the 7-state value directly). Otherwise self-resolve and
   land via the beads-fabro worktree → PR → janitor path.

## Session 13 (2026-07-03) — jcc6.3 EXECUTED: relocated to bd-ib-syb, prose fix landed (PR #254), fable-judge loop proven

Resumed fleet-followups; the maintainer was away at the activity picker, so the session
proceeded under the §"Session 12 (continued 2)" standing directive ("the NEXT session judges
the rewrite itself … asking the maintainer only where necessary"). The maintainer-gated
`/livespec:revise` of `readme-contract.md` was deliberately NOT run (content gate — it stays
the top action for an attended session). Executed the jcc6.3 plan end-to-end:

- **Relocated:** filed **`bd-ib-syb`** (beads-fabro, P2, `origin:freeform`, normalized
  `open→backlog`) carrying the full research findings; closed core child `livespec-jcc6.3`
  as relocated with a citation comment. Epic `livespec-jcc6` is now **3/4** (`.4` held
  under `c1k9` is the only open child).
- **Live re-verification (one correction to §"Session 12 (continued 2)"):** the
  `WorkItemStatus` literal's terminal state is **`"done"`, not `"closed"`** as recorded
  there (verified in livespec-runtime origin/master AND the beads-fabro vendored copy).
  Unchanged conclusion: `"open"` is invalid; `"backlog"` is the intake entry state.
- **Drafted + fable-judged (the DoR-blocker resolution, proven):** drafted
  `capture-work-item.md` `status="open"` → `"backlog"` in a beads-fabro worktree; a fresh
  `general-purpose` sub-agent on the **fable model** (NOT a fork — Session-11 lesson)
  independently judged the prose against the vendored schema + store signatures. Verdict
  **REVISE**: the core change confirmed correct, kwargs/signatures all verified, but THREE
  real residual drifts surfaced that the draft missed — (a) Pre-requisites still said
  "JSONL store path" (beads has no on-disk JSONL; now "the resolved beads tenant
  connection"), (b) the Depends-on bullet hardcoded `li-` ids contradicting the same
  file's prefix-decoupling comment (now the tenant's configured `<prefix>-XXXXXX` form),
  (c) `plan.md` offered a "parent link" the capture path cannot express (`parent_id=None`
  always; now "linked via `depends_on`"). Applied all three; a re-judge pass on the
  amendments returned **APPROVE (high confidence)**.
- **Landed:** beads-fabro **PR #254** (`docs(prose):` — no product `.py`, TDD-exempt;
  sibling-precedent subject per `fa190ab`) merged `ec5a598`, all required checks green;
  primary refreshed, worktree + branch cleaned; `bd-ib-syb` CLOSED with the completion
  record.
- **Side observation (logged as a `bd-ib-syb` comment, not expanded into scope):** the
  beads-fabro package `types.py:11-12` docstring says "unified 20-field shape" but the
  vendored model is 22 fields — a stale count in a `.py` docstring (TDD-ritual territory);
  fix opportunistically on the next `types.py`-touching change.

**Method note for future not-autonomously-verifiable items:** the fable-judge loop
(draft → independent fable-model judge with the source-of-truth file list → reconcile →
re-judge the amendments) resolved a DoR blocker that had held jcc6.3 since Session 2, and
the judge caught real drift the drafting session missed — reuse it.

## Session 14 (2026-07-03) — unattended status pass: no drift; c1k9's FINAL design does NOT cover jcc6.4 (unhold surfaced)

Resumed fleet-followups; the maintainer was away (the activity picker timed out), so —
per the Session-13 precedent — the content-gated `/livespec:revise` of
`readme-contract.md` was again deliberately NOT run; it remains the top action for an
attended session. This pass composed status LIVE and refreshed this handoff only:

- **No drift from the Session-13 record.** Epic `livespec-jcc6` **3/4** (`.4` the only
  open child, still `backlog`); `SPECIFICATION/proposed_changes/` still holds only
  `readme-contract.md` (+ the README placeholder); nothing new in the core queue.
- **Cross-tenant Session-12 filings unchanged** — all three still `backlog` in their
  owning tenants, awaiting groom + dispatch from those repos' sessions (as designed;
  no core-session action): beads-fabro `bd-ib-09c` (migrate-tenant CLI), driver-codex
  `livespec-driver-codex-wqo` (stale "DEFERRED" docs), dev-tooling
  `livespec-dev-tooling-5kv` (worktree-pack hydration).
- **⚑ NEW FINDING — `livespec-c1k9`'s Phase-4 design is FINAL and does NOT cover
  jcc6.4's domain.** c1k9 now carries 10 filed children (0/10 complete) and its design
  decisions are recorded final in `plan/fleet-plugin-currency/handoff.md` (D1 =
  verified release-branch marketplace ref, D2 = warn+fail lever, D3 = host-level
  pre-session sweep DEFERRED). Neither the child set nor that handoff mentions the
  orphaned `installed_plugins.json` dead-entry cleanup `livespec-jcc6.4` implements —
  the D3 "sweep" is a different mechanism (pre-session plugin-UPDATE sweep, not
  registry-entry pruning). So the Session-12 hold condition ("until c1k9's
  investigation decides how orphan-cleanup ships") has effectively resolved to
  "c1k9 does NOT ship it". **Attended decision surfaced (recommended): UNHOLD
  `livespec-jcc6.4`** — promote `backlog→ready` (+ `admission:auto`,
  `acceptance:ai-only`; its unit-test-over-synthetic-registry acceptance is already
  autonomously verifiable) and dispatch it standalone via the factory. The
  alternative — refiling it as a c1k9 child — has no home in the finalized design.
  Left undispatched here: the hold was an explicit Session-12 maintainer decision,
  so reversing it is the maintainer's call.
- **Cold-open gate repairs (verified live, then folded into "The next action"):**
  (a) `livespec-127o.2` ALREADY carries a full autonomously-verifiable acceptance
  block (7-sections-in-order, no embedded diagrams, link resolution, `just check` +
  doctor green) — no acceptance authoring needed at promote time. (b) bd v1.0.5's
  `update` has NO `--labels` flag — the real form is repeatable `--add-label`
  (verified via `bd update --help`); the retained Dispatch-mechanics block was
  corrected in place. (c) The heading-coverage co-edit shape + path spelling and
  the close-`.1`-to-un-gate-`.2` step are now explicit in the next-action text.

## Read-first chain (in order)

1. **`research/01-followup-inventory.md`** — the full grouped catalog. (This is
   the only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-followups
```
