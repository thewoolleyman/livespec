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
  few **same-tenant (core) ledger children** (`livespec-jcc6.1/.2/.3`, filed
  2026-07-01; **`.1` + `.2` DONE** via factory dispatch (PRs #736/#734), `.3`
  held at `backlog` — see §"Session 3"/§"Session 4"); every **cross-tenant** item
  is **prose-linked** in the inventory and its status is composed from the ledger
  (no shadow queue).
- **⚑ TOP PRIORITY (Session 4, maintainer-directed): FOUR P0 factory-hardening
  threads** (all `livespec-orchestrator-beads-fabro` tenant, all dispatcher
  self-modifications) outrank everything else. Status is READ from the ledger; see
  §"Session 4 (part 2)" for the full map + the janitor discovery:
  1. **`bd-ib-fqh`** (EPIC) — factory context-completeness, re-groomed as an
     **Option-B cross-repo epic** (`acceptance_criteria`+`notes` become first-class
     `WorkItem` fields, both backends): **S1 `livespec-runtime-00u` DONE** (contract
     MERGED to `livespec-runtime` master; a **v0.7.0** release is QUEUED but NOT yet
     cut — release-please **PR #105** is still OPEN, latest release is v0.6.0); S2
     `bd-ib-fqh.1` (beads store+`render_goal`) + S3 `bd-gj-lxr` (git-jsonl
     store/schema) **release-gated** (merge PR #105 → v0.7.0 → `bump-pin`); S4
     `bd-ib-fqh.2` + S5 `bd-ib-fqh.3` gated behind S2.
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

**⚑ SESSION-4 TOP PRIORITY (maintainer-directed): the FOUR P0 factory-hardening
threads** — all in `livespec-orchestrator-beads-fabro`, all dispatcher
self-modifications, all GROOMED (full map in the "For a fresh session" bullet above
+ §"Session 4 (part 2)"). Work them from a **`livespec-orchestrator-beads-fabro`
session**; careful — human-approved admission, never auto-dispatch blind. **Order:**

1. **`bd-ib-mxr` / `bd-ib-cyv` FIRST — the janitor E2E unblocker.** The post-merge
   janitor doesn't provision livespec core → false-fails `check-doctor-static` for
   EVERY non-core target (the dispatch merges the change but reports
   `failed:janitor-post-merge`; hand-reconcile). The janitor is also only ever MOCKED
   green in tests, so the gap shipped invisibly. Fix = provision core + a
   top-of-pyramid test running the REAL janitor to green (`bd-ib-cyv`) + the broader
   real-dispatch E2E (`bd-ib-mxr.1`). Until it lands, every non-core dispatch below
   merges-but-marks-failed.
2. **`bd-ib-asp`** — merge-poll fail-fast on a terminally-BLOCKED PR (`ready`).
3. **`bd-ib-fqh` cross-repo epic** — S1 (`livespec-runtime-00u`) DONE (merged to
   `livespec-runtime` master). ⚠ The **v0.7.0** release is NOT cut yet —
   release-please **PR #105** is OPEN. **Merge PR #105** to cut v0.7.0; then
   `bump-pin` propagates it and S2 (`bd-ib-fqh.1`) + S3 (`bd-gj-lxr`) unblock
   (re-vendor gate) → promote `backlog→ready` → then S4/S5.

Dispatch mechanics + scope-guard discipline: see step 3 below. ⚠ Non-core targets
currently false-fail the post-merge janitor (that's `bd-ib-cyv`) — verify via
`gh pr view <n>` / CI-green-on-master and hand-reconcile (`bd update <id> --status
closed`) a change that actually merged.

Then the remaining thread work (core tenant, from this session):

1. **Read `research/01-followup-inventory.md`** — the full grouped catalog (ids,
   tenants, one-line actions, live ledger id / FILED marker). The map for below.
2. **Two `ready` core gap-facade items are admission-approved but HELD** pending
   scope guards: **`livespec-yonx`** (`io/fastjsonschema_facade.py`) +
   **`livespec-ek6e`** (`io/structlog_facade.py`), both `admission:auto` +
   `acceptance:ai-only`. ⚠ Before dispatching each, add a **SCOPE-GUARD ledger
   comment** (`bd comment <id> "modify ONLY <files>; do NOT edit README/docs/..."`)
   — that comment is the ONLY item-specific channel the Fabro brief includes today
   (the acceptance field is NOT in the brief; that's what `bd-ib-fqh` fixes), and it
   is what made `yc8e`'s re-dispatch land cleanly.
3. **Dispatch a `ready`, scope-guarded core item through the factory FROM THIS
   SESSION** (proven — `yc8e` PR #742, `jcc6.1` #736, `jcc6.2` #734). (a) admission
   is approved via the `admission:auto` label (+ `acceptance:ai-only`); (b) run the
   containerized dispatcher:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh \
     bash /data/projects/livespec-orchestrator-beads-fabro/orchestrator-image/real-work-dispatch.sh \
     --target-repo livespec --item <ready-id> --run
   ```
   Secrets come from the SAME `with-livespec-env.sh` wrapper
   (`LIVESPEC_FAMILY_GITHUB_TOKEN`, `ANTHROPIC_API_KEY_LIVESPEC_E2E`,
   `CLAUDE_CODE_OAUTH_TOKEN`, `BEADS_DOLT_PASSWORD`, `HONEYCOMB_INGEST_KEY_LIVESPEC`)
   plus the host `~/.codex/auth.json`; it runs in `livespec-orchestrator:dev` (Fabro
   sandbox → PR → janitor `just check` + doctor → rebase-merge → acceptance →
   `done`, ~20 min). `--preflight` (no `--item`) checks inputs. ⚠ Until `bd-ib-asp`
   lands, a dispatch whose PR fails a required check POLLS the full ~76 min then
   exits `failed:merge-poll` — if a run overruns ~25 min, check `gh pr checks <n>`
   (a red required check = the poll can never succeed; close/fix + re-dispatch).
4. **Groom the remaining core items** (`groom <id>` from a core session):
   `livespec-127o` (README — epic-shaped: spec-contract slice →
   `/livespec:propose-change` + README-authoring slice → factory), `livespec-m0xu`
   (template rename — copier-ref ripples; `backlog`). `livespec-jcc6.3` (prose
   refresh) stays `backlog` (acceptance not autonomously verifiable). `needs-regroom`
   `livespec-nylyhi` + `livespec-rmew4k` are CROSS-TENANT — groom from those repos'
   sessions.
5. **Still-unfiled CROSS-TENANT items** (file from each owning repo's OWN session —
   the `bd` cwd-tenant trap): **B4** (beads-fabro/runtime `migrate-tenant` CLI),
   **C7** (driver-codex "DEFERRED" wording), **C8** (git-jsonl §6 doc-reconcile),
   **D9** (fleet/dev-tooling `hydrate` worktree-pack), **D10** (fleet/core
   review-policy decision).
6. **Client-side ops** (inventory group **E**) — operator actions, done directly.
7. **Cross-links** (group **F**) resume in their own repo's thread, not here.
8. **Close `livespec-jcc6`** when the gathered items (incl. the two P0 factory
   items) are groomed + dispatched/reassigned and nothing lingers → archive this
   thread to `plan/archive/`.

## Already-filed items to fold in (cite read-only; details in the inventory)

**⚑ TOP PRIORITY (all `livespec-orchestrator-beads-fabro`, P0, careful self-mods):**
`bd-ib-fqh` EPIC (context-completeness, Option-B cross-repo: S1 `livespec-runtime-00u`
DONE, v0.7.0 release QUEUED via PR #105, S2 `bd-ib-fqh.1` + S3 `bd-gj-lxr` release-gated, S4 `bd-ib-fqh.2` + S5
`bd-ib-fqh.3` gated); `bd-ib-asp` (merge-poll fail-fast, `ready`); `bd-ib-mxr` EPIC
(E2E dispatch acceptance — children `bd-ib-cyv` janitor-green-by-execution +
`bd-ib-mxr.1` broader E2E; THE UNBLOCKER for non-core dispatch).
Core epic children (this thread): `livespec-jcc6.1` (B2, **DONE** PR #736),
`livespec-jcc6.2` (B3, **DONE** PR #734), `livespec-jcc6.3` (C6, `backlog` — held).
Other core: `livespec-yc8e` (B1 reaper, **DONE** PR #742), `livespec-mpkaz4`
(reaper sibling, `open`), `livespec-127o` (README, `backlog`), `livespec-m0xu`
(template rename, `backlog`), `livespec-yonx` + `livespec-ek6e` (io facades,
**`ready`** — HELD pending scope guards), `livespec-aava` (B5, Codex skill-picker).
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
    ⚠ The **v0.7.0** release is NOT cut yet — release-please **PR #105** is still OPEN
    (latest release v0.6.0). Merging PR #105 cuts v0.7.0, the re-vendor gate for S2/S3.
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

## Read-first chain (in order)

1. **`research/01-followup-inventory.md`** — the full grouped catalog. (This is
   the only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-followups
```
