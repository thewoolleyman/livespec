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
  held at `backlog` — held rationale in §"Session 2"); every **cross-tenant** item
  is **prose-linked** in the inventory and its status is composed from the ledger
  (no shadow queue).
- **⚑ NEW #1 (2026-07-02): GitHub App-token auth — its OWN dedicated thread.** The
  GH_TOKEN factory-auth blocker (a `livespec-console-beads-fabro` canary hit it) grew
  into a fleet-wide credential-model track: retire the fleet PAT
  (`LIVESPEC_FAMILY_GITHUB_TOKEN`) + the human `gho_` OAuth from the agent path,
  standardize on GitHub **App installation tokens**, with **first-class remint**
  (survives >1h runs), **tenant-scoped** resolution + adopter isolation (fleet = adopter
  #0, fail-closed), and OS/VPS **enforcement**. Worked in **`plan/github-app-auth/`**
  (epic **`livespec-2ef0`**, core; resume
  `/livespec-orchestrator-beads-fabro:plan github-app-auth`) — successor to the closed
  credential-wrapper epic `livespec-zd8h`. It absorbs `bd-ib-gsl` as its factory slice,
  **supersedes `bd-ib-p2e`** (PAT-grant stopgap → obsolete), and folds in **`C16`**
  (openbrain adopter wrapper). Resume THAT thread for this work, not here.
- **⚑ TOP PRIORITY (Session 4, maintainer-directed): FOUR P0 factory-hardening
  threads** (all `livespec-orchestrator-beads-fabro` tenant, all dispatcher
  self-modifications) outrank everything else EXCEPT the github-app-auth track above.
  Status is READ from the ledger; see
  §"Session 4 (part 2)" for the full map + the janitor discovery:
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
3. **`bd-ib-fqh` cross-repo epic** — S1 (`livespec-runtime-00u`) DONE; **v0.7.0
   CUT** (PR #105; CORE re-vendored via `4d08972`). **S2 (`bd-ib-fqh.1`): re-vendor
   LANDED** (beads-fabro fan-out **PR #233** merged 2026-07-02) → promote
   `backlog→ready` from a beads-fabro session and work it. **S3 (`bd-gj-lxr`):
   INVERTED gate** — its re-vendor PR #158 is terminally BLOCKED because v0.7.0
   serializes `acceptance_criteria`+`notes` and git-jsonl's own schema validator
   rejects them (87 test failures); implement S3 from a git-jsonl session and land
   it WITH the pin bump. Then S4/S5 (`ready` in the ledger, correctly dep-gated on
   S2 via `depends_on`). Details: §"Session 8".

Dispatch mechanics + scope-guard discipline: see step 3 below. ⚠ Non-core targets
currently false-fail the post-merge janitor (that's `bd-ib-cyv`) — verify via
`gh pr view <n>` / CI-green-on-master and hand-reconcile (`bd update <id> --status
closed`) a change that actually merged.

Then the remaining thread work (core tenant, from this session):

1. **Read `research/01-followup-inventory.md`** — the full grouped catalog (ids,
   tenants, one-line actions, live ledger id / FILED marker). The map for below.
2. **The two core gap-facade items are DONE** (Session 8): **`livespec-yonx`**
   (`io/fastjsonschema_facade.py`, **PR #762**, exact-scope, janitor green, CLOSED)
   + **`livespec-ek6e`** (`io/structlog_facade.py`, **PR #764**, exact-scope,
   janitor green, CLOSED). ⚠ The scope-guard discipline they validated stays
   MANDATORY for every
   dispatch until `bd-ib-fqh` lands: add a **SCOPE-GUARD ledger comment**
   (`bd comment <id> "modify ONLY <files>; do NOT edit README/docs/..."`) naming the
   exact file set — that comment is the ONLY item-specific channel the Fabro brief
   includes today (the acceptance field is NOT in the brief; that's what `bd-ib-fqh`
   fixes). Enumerate the REAL callsite set yourself (grep, don't trust the item
   text's examples — yonx's acceptance named 2 callsites; the true set was 11).
3. **Dispatch a `ready`, scope-guarded core item through the factory FROM THIS
   SESSION** (proven — `yonx` PR #762, `ek6e` #764, `yc8e` #742, `jcc6.1` #736,
   `jcc6.2` #734). ⚠ As of Session 8 the core dispatchable-`ready` queue is
   EMPTY — this step is the mechanics reference for when step-4 grooming promotes
   new items. (For a non-core target substitute its repo name in `--target-repo`,
   but mind the janitor false-fail warning below.) (a) admission
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
DONE, v0.7.0 CUT (PR #105 merged), **S2 `bd-ib-fqh.1` UN-GATED** (re-vendor PR #233
merged — promote from a beads-fabro session), **S3 `bd-gj-lxr` INVERTED gate** (its
re-vendor PR #158 is BLOCKED on S3's own schema work — land together from a git-jsonl
session), S4 `bd-ib-fqh.2` + S5 `bd-ib-fqh.3` dep-gated on S2); `bd-ib-asp`
(merge-poll fail-fast, `ready`); `bd-ib-mxr` EPIC
(E2E dispatch acceptance — children `bd-ib-cyv` janitor-green-by-execution +
`bd-ib-mxr.1` broader E2E; THE UNBLOCKER for non-core dispatch).
Core epic children (this thread): `livespec-jcc6.1` (B2, **DONE** PR #736),
`livespec-jcc6.2` (B3, **DONE** PR #734), `livespec-jcc6.3` (C6, `backlog` — held).
Other core: `livespec-yc8e` (B1 reaper, **DONE** PR #742), `livespec-yonx` (io
facade, **DONE** PR #762), `livespec-ek6e` (io facade, **DONE** PR #764),
`livespec-mpkaz4` (reaper sibling, `open`), `livespec-127o` (README, `backlog`),
`livespec-m0xu` (template rename, `backlog`), `livespec-aava` (B5, Codex
skill-picker).
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

The core-session-actionable set is otherwise unchanged: **route C15 → spec**
(recommended, above), or **groom `livespec-127o`** (README epic) / **groom
`livespec-m0xu`** (template rename) to produce dispatchable slices. `jcc6.3` stays
held (acceptance not autonomously verifiable). Everything else is cross-tenant or
client-side.

## Read-first chain (in order)

1. **`research/01-followup-inventory.md`** — the full grouped catalog. (This is
   the only companion file; everything else needed is in this handoff.)

## Resume command

```
/livespec-orchestrator-beads-fabro:plan fleet-followups
```
