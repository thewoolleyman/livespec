# Follow-up inventory — fleet-followups

The full catalog of post-lifecycle follow-ups + lingering cleanup, gathered from
the archived `work-item-state-machine` handoff (its "Post-L2 follow-ups" +
session-8b/8c/9 side-findings) and this session. Grouped by kind. **Status is
read from the ledger, never from this file.** Cross-tenant items are
prose-linked (the fleet pattern); file the UNFILED ones into their named tenant
as `origin:freeform`, 2-step to `backlog`, then groom + dispatch in that repo's
own session.

Epic anchor: **`livespec-jcc6`** (core tenant, `backlog`).

---

## 0. ⚑ TOP PRIORITY — factory-hardening (Session 4, maintainer-directed; all GROOMED)

Four P0 threads, all in **`livespec-orchestrator-beads-fabro`**, all dispatcher
**self-modifications** (human-approved admission, never auto-dispatch blind). Status
is READ from the ledger. Discovered dispatching `yc8e` + S1 (§ handoff "Session 4" /
"Session 4 (part 2)"). **Order:** fix the **janitor E2E unblocker** (`bd-ib-mxr`)
first — until it lands, every non-core dispatch merges-but-marks-failed on the janitor.

> **⚑ NEW #1 (2026-07-02) — spun out to its own thread: `plan/github-app-auth/`** (epic
> **`livespec-2ef0`**, core; resume `/livespec-orchestrator-beads-fabro:plan github-app-auth`).
> The GH_TOKEN factory-auth blocker grew into a fleet-wide credential-model track (GitHub
> **App installation tokens**; retire the fleet PAT + the human `gho_` OAuth from the agent
> path; first-class remint; adopter isolation, fleet = adopter #0, fail-closed; OS/VPS
> enforcement). It **absorbs `bd-ib-gsl`** (factory slice), **supersedes `bd-ib-p2e`**
> (PAT-grant stopgap → obsolete), and folds in **`C16`**. Successor to the closed
> credential-wrapper epic `livespec-zd8h`. Work it in that thread, not here — the P0
> threads below remain the factory-hardening set.

| id | kind | slices / status | what |
|---|---|---|---|
| `bd-ib-mxr` | EPIC · **UNBLOCKER** | `bd-ib-cyv` (janitor green-by-execution + provision livespec core) · `bd-ib-mxr.1` (broader real-dispatch E2E, deps `bd-ib-cyv`) | **E2E dispatch acceptance.** The post-merge janitor doesn't provision livespec core → false-fails `check-doctor-static` for every NON-CORE target (merges but reports `failed:janitor-post-merge`); and it's only ever MOCKED green in tests, so the gap shipped invisibly. Fix: provision core + a top-of-pyramid test running the REAL janitor to green, then the broader real-dispatch E2E. |
| `bd-ib-fqh` | EPIC · cross-repo (Option B) | **S1 `livespec-runtime-00u` DONE** (merged; **v0.7.0 CUT** 2026-07-02, PR #105 merged; CORE re-vendored via `bump-pin` `4d08972`) · **S2 `bd-ib-fqh.1` UN-GATED** (beads-fabro re-vendor PR #233 MERGED 2026-07-02 — promote from that session) · **S3 `bd-gj-lxr` INVERTED gate** (its re-vendor PR #158 BLOCKED on S3's own schema work — 87 test failures on `unexpected extra keys`; land S3 WITH the pin bump from a git-jsonl session) · S4 `bd-ib-fqh.2` + S5 `bd-ib-fqh.3` `ready` but dep-gated on S2 (`depends_on` edges) | **Factory context-completeness.** `acceptance_criteria`+`notes` weren't even on the shared `WorkItem` model, so `render_goal` couldn't carry them (root cause of PR #740 over-reach). Make them first-class `WorkItem` fields in **`livespec-runtime`** (S1 done), propagated to the beads store+`render_goal` (S2), the git-jsonl store+schema (S3), then the beads prompts (S4) + remaining audited gaps (S5). |
| `bd-ib-asp` | task · `ready` | single slice | **Merge-poll fail-fast.** `_await_merge` polls only for MERGED and burns the full ~76-min budget on a terminally-BLOCKED PR (a REQUIRED terminal-failure check, e.g. PR #740's `check-coverage`). Fail fast + surface the failing check; keep polling on pending/BEHIND. |

**Cross-repo dep (S2/S3 → S1):** release-ordering + prose (beads edges are
intra-tenant). S1 is MERGED and **v0.7.0 is CUT** (2026-07-02, PR #105 merged; CORE
already re-vendored via `bump-pin` `4d08972`). **Session-8 live check:** S2's
re-vendor **LANDED** (beads-fabro PR #233 merged 2026-07-02 01:45Z) → promote S2
`backlog→ready` from that session. S3's re-vendor (git-jsonl **PR #158**) is
**terminally BLOCKED** — v0.7.0 serializes `acceptance_criteria`+`notes` and
git-jsonl's own schema validator rejects them (87 failures) — that extension IS
S3's scope, so implement S3 from a git-jsonl session and land it WITH the pin
bump. **Scope-guard workaround** until `bd-ib-fqh`
lands: hand-write a `bd comment <id>` naming the exact files before each dispatch
(the only item-specific channel the Fabro brief reads today).

## A. Already filed — cite read-only; groom + dispatch in the owning repo's session

| id | tenant | what | next |
|---|---|---|---|
| `livespec-127o` | core | README rewrite (spec-driven): add a README-contract to `SPECIFICATION/` (purpose, audience = zero-knowledge newcomer, required structure, reference-not-duplicate), then author the README to conform. Supersedes the incrementally-grown README (PR #723). | groom |
| `livespec-m0xu` | core | rename `templates/impl-plugin/` → `templates/orchestrator-plugin/` (it scaffolds orchestrator plugins; the name misleads). Plain `open` item filed via raw `bd create` — **still `open`; needs the 2-step move to `backlog` before grooming.** | move to backlog, then groom |
| `bd-ib-2wq` | beads-fabro | doctor invariant: fail `just check` / `/livespec:doctor` when any LIVE work-item's status is outside the 7-state set (the enforcement gap — today it's pyright-only, no runtime/audit check). | groom |
| `livespec-dev-tooling-9j8` (+13 children) | dev-tooling | shell-logic hardening epic: substantive logic must live in tested, type-checked, importable code (no logic in shell OR `python -c`/heredocs). Rule + mechanical gates, NOT a ban. 2 ports ready: `9j8.1` (bump-pin rewriters → tested module), `livespec-gnjb` (`export-ci-telemetry.sh` → tested Python + re-stamp template). Doc PR #229 merged. | groom the epic |

## B. Unfiled — tooling / dev-ex bugs (file → groom → dispatch)

1. ✅ **DONE (PR #742)** — **Worktree reaper** (`dev-tooling/reap_stale_worktrees.py`) — **CORE** tenant — two bugs: (a) fails on a *relative* `--repo` run from the justfile dir — must pass an absolute path (**CONFIRMED hit 2026-07-01**; `just reap-stale-worktrees livespec` threw, `--repo /data/projects/livespec` worked); (b) skips rebase-merged branches whose remotes weren't deleted. → **`livespec-yc8e`** (P1) **CLOSED** via a scope-guarded factory re-dispatch (PR #742, 2 files: reaper + test, janitor-green; the fix resolves relative/bare repo names in the script itself). NOTE: the FIRST dispatch (PR #740, closed) over-reached (deleted README mermaid → coverage fail); that surfaced the two P0 factory-hardening items in group 0. Sibling reaper bug **`livespec-mpkaz4`** (P3, bare-name/sibling path) remains `open`.
2. ✅ **FILED** — **CORE `propose_change.py` / `revise.py` cwd resolution** — **CORE** tenant — resolve a relative `--spec-target` against **cwd**, not `--project-root`; honor `--project-root` (or document the absolute-path requirement). → **`livespec-jcc6.1`** (backlog, child of the epic).
3. ✅ **FILED** — **CORE `doctor_static.py` missing `--spec-target`** — **CORE** tenant — the flag exists on sibling wrappers; add it for consistency. → **`livespec-jcc6.2`** (backlog, child of the epic).
4. **No end-to-end `migrate-tenant` CLI** — **beads-fabro** (or runtime) — `legacy_seed` / `register_custom_statuses` are library primitives; wrap into one command so a future tenant onboards in one step (all 9 L2 tracks hand-composed the migration). *Still unfiled — file from the beads-fabro/runtime session.*
5. ≈ **COVERED** — **Codex TUI `check-codex-skill-picker` blocked by hooks-trust prompt** (CI self-skips) — **driver-codex** / dev-tooling — make it runnable locally or document the skip. → effectively **`livespec-aava`** (same test `test_codex_skill_picker.py`; that item's root cause is the non-TTY/no-controlling-terminal pre-push context — the "make it runnable locally / document the skip" thrust is the same). Related: **`livespec-nylyhi`** (Codex orchestrate help trips the primary-checkout guard).

## C. Unfiled — doc / config drift (file → fix)

6. ✅ **FILED** — **Stale `capture-work-item` / `plan` prose for v0.3.0** — **CORE** (`.claude-plugin/prose/`) — documents the OLD schema (`status=open` + `priority`, no `rank`); refresh to the 7-state + `rank` model. → **`livespec-jcc6.3`** (backlog, child of the epic).
7. **driver-codex `.livespec.jsonc` / `CLAUDE.md` say beads connection "DEFERRED"** — **driver-codex** — the tenant is migrated + connected; correct the stale "DEFERRED" wording. *Still unfiled — file from the driver-codex session.*
8. **git-jsonl §6 doc-reconcile** — **git-jsonl** — the policy-fields-dropped-on-write behavior is a slice-plan-vs-design §6 tension; reconcile in that repo's design doc. *Still unfiled — file from the git-jsonl session.*
15. **`contracts.md` callability warn-vs-fail lever prose (impl→spec drift)** — **CORE** (spec-side; `/livespec:propose-change` → `/livespec:revise`, no beads) — *relocated from the closed credential-wrapper epic `livespec-zd8h`, 2026-07-01.* `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" (the `config-named-cli-callability` paragraph) still says an unresolvable `credential_wrapper` first token "fires `fail`", but the SHIPPED lever (PR #746, `livespec-zd8h.3`) **warns** (non-fail) when the token does not resolve — the host-provisioned wrapper is legitimately absent on CI runners — and keeps `fail` only for a resolved-but-non-executable token. Refine the clause to match the code. **✅ VERIFIED live 2026-07-02 (Session 9):** the shipped `_evaluate` in `.claude-plugin/scripts/livespec/doctor/static/config_named_cli_callability.py` warns on `_RESOLVE_UNRESOLVABLE` for `credential_wrapper` and fails only on `_RESOLVE_NOT_EXECUTABLE`; the spec is stale in TWO spots — **line 135** (the invariant paragraph) AND the **line 61** parenthetical "(its first token MUST resolve to an executable)". Both need reconciling. **✅ DONE 2026-07-02 (Session 9): FILED (PR #769) → REVISED IN at history v154 (PR #772). The warn-vs-fail lever is now live in `contracts.md`; no further action.** **Original drop-in clause (from the crit-path-4 agent, for reference):**

    > When `credential_wrapper` is present and non-empty, its first token is resolved with the same semantics as every other named CLI, but the callability finding carries a severity lever unique to this OPTIONAL key: if the first token resolves to a file that is not executable (a real misconfiguration) the finding is `fail`; if the first token does not resolve at all — the host-provisioned wrapper is legitimately absent, e.g. on a CI runner that does not install it — the finding is `warn` (non-fail, so CI stays green); when the key is absent or empty the invariant is a no-op. The lever applies ONLY to `credential_wrapper`; the spec-side and orchestrator-side named CLIs keep their hard-fail semantics.
16. **Adopters `credential_wrapper` config + guard (openbrain, dolt-server)** — **adopters** — *relocated from the closed credential-wrapper epic `livespec-zd8h`, 2026-07-01.* Add `credential_wrapper` to each adopter's `.livespec.jsonc` (openbrain → `["/usr/local/bin/with-openbrain-env.sh","--"]`, its OWN 1Password env, NOT the fleet wrapper; dolt-server → its own wrapper) + install the generalized beads-access guard. Gated on the manifest-reconcile decision **`D17`** — only meaningful once openbrain/dolt-server register as adopters. *Still unfiled — file from each adopter repo's OWN session (the `bd` cwd-tenant trap).*

## D. Unfiled — env / infra

9. **`hydrate` doesn't provision the worktree-pack** (`branch-protection.just` etc.) into fresh worktrees (self-healed via `just install-worktree-pack`) — **fleet / dev-tooling** — make hydrate provision it. Also: the **git-jsonl PRIMARY checkout lacks `branch-protection.just`**.
10. **Branch protection requires checks but 0 reviews** — **fleet / core** — relevant once external contributions arrive; decide the review policy.
17. **Fleet manifest `adopters: []` reconcile — decide openbrain/dolt-server registration** — **fleet / core** — *relocated from the closed credential-wrapper epic `livespec-zd8h`, 2026-07-01.* `.livespec-fleet-manifest.jsonc` still carries `adopters: []`. Decide whether openbrain + dolt-server register as adopters (each brings its OWN credential wrapper + tenant password, not the fleet's). A fleet/core call, like #10; it gates the adopter config rollout **`C16`**.
18. **`livespec-runtime` stale `uv.lock` (0.4.0 → 0.6.0)** — **livespec-runtime** — *relocated from the closed credential-wrapper epic `livespec-zd8h`, 2026-07-01.* `livespec_runtime` released **v0.6.0** (the `ensure_credentials`/`decide_credentials` self-heal helper) but its committed `uv.lock` still pins the old `0.4.0` self-version; refresh the lockfile. Low-risk hygiene. *Still unfiled — file from the livespec-runtime session.*

## E. Client-side operator actions (NOT factory work-items — do directly)

11. **Orchestrator-plugin cache stale fleet-wide** — client-side `claude plugin update <plugin>@<marketplace> --scope project` (per repo) + restart. (This core session refreshed to `06e3e080ae19` at SessionStart; other scopes may lag.)
12. **openbrain pin bump** needs a client-side `/plugin install` + restart — cannot be done in-session.
13. **Open-item status reclassification** — per-item grooming; a bulk rewrite is available if wanted.

## F. Cross-links — existing threads (resume THERE, not here)

14. **Slice 4 + Slice 6** (`real-work-dispatch.sh` unattended substrate moving off its self-clone + an E2E acceptance proving enabled-plugin dispatch) — **beads-fabro / orchestrator repo** — captured in that repo's thread `plan/orchestrator-plugin-self-containment/handoff.md`; resume there.

---

### Filing note
Core-tenant items are filed from a core session (`cd /data/projects/livespec` +
the env wrapper, `bd create --type task --labels origin:freeform` then 2-step
`bd update --status backlog`). Cross-tenant items must be filed from their own
repo's session (the `bd` cwd-tenant trap).

**Filing progress (2026-07-01):** the still-unfiled CORE items were filed as
children of the epic — **B2 → `livespec-jcc6.1`**, **B3 → `livespec-jcc6.2`**,
**C6 → `livespec-jcc6.3`**; the **B1** reaper bugs were already filed
(`livespec-yc8e` + `livespec-mpkaz4`), with the B1(b) rebase-merged-skip sub-bug
appended to `yc8e`'s notes; **B5** is covered by `livespec-aava`. Remaining
unfiled: **B4** (beads-fabro/runtime), **C7** (driver-codex), **C8** (git-jsonl),
and the env/policy calls **D9/D10** — file each from its owning repo's session
(or as a core decision for D10).

**DoR triage (2026-07-01, session 2):** `jcc6.1` + `jcc6.2` promoted to
dispatchable **`ready`** (acceptance + autonomy tier added); `jcc6.3` held at
`backlog` (`not-yet-actionable` — acceptance not autonomously verifiable);
`m0xu` moved `open` → `backlog`. See `handoff.md` §"Session 2" for the full
Revise / Gap / Groom / Orchestrate findings (gap: ~370 uncaptured candidates
need a scoped pass; groom targets are cross-tenant; dispatch runs in the
dedicated Dispatcher env, not this interactive session).

**Session 4 (2026-07-01):** `jcc6.1` (PR #736), `jcc6.2` (PR #734), and
**`yc8e`** (PR #742, scope-guarded re-dispatch) all **DONE** via factory. `yc8e`'s
first dispatch over-reached (PR #740, closed) → surfaced the two **P0
factory-hardening** items now in **group 0** (`bd-ib-fqh` context-completeness,
`bd-ib-asp` merge-poll fail-fast; beads-fabro tenant, the epic's TOP priority).
`yonx` + `ek6e` promoted to `ready` + `admission:auto`/`acceptance:ai-only` but
**HELD** pending per-dispatch scope-guard comments (the interim workaround until
`bd-ib-fqh` lands). See `handoff.md` §"Session 4".

**Session 5 (2026-07-01):** the **`credential-wrapper`** epic (`livespec-zd8h`,
CORE) closed at **100%** (self-heal proven) and its thread archived to
`plan/archive/credential-wrapper/`. Its still-live deferred tail relocated here
(relocate-never-drop): **`C15`** (CORE `contracts.md` warn-vs-fail lever prose),
**`C16`** (adopter config), **`D17`** (manifest `adopters:[]` reconcile decision),
**`D18`** (runtime `uv.lock` refresh). The 5th tail item — fleet CORE-pin bumps —
was **disposed as auto-resolving** (`bump-pin` fan-out on the next CORE release;
self-heal does not need it). See `handoff.md` §"Session 5".

**Session 7 (2026-07-02):** `livespec-runtime` **v0.7.0 CUT** (release-please PR #105
merged; CORE re-vendored via `bump-pin` `4d08972`). This un-gates `bd-ib-fqh` S2
(`bd-ib-fqh.1`) + S3 (`bd-gj-lxr`) — no longer release-gated; they now wait ONLY on
their OWN tenants' `bump-pin` re-vendor of v0.7.0, then promote `backlog→ready` from
those sessions. See `handoff.md` §"Session 7".

**Session 8 (2026-07-02):** the two held io-facade items shipped via scope-guarded
factory dispatch — **`livespec-yonx` DONE** (**PR #762**, facade + the real
11-callsite set + test, exact-scope, janitor green) and **`livespec-ek6e` DONE**
(**PR #764**, facade + `__init__.py` + `commands/revise.py` + test, exact-scope,
janitor green). Live gate check on `bd-ib-fqh`:
**S2 un-gated** (beads-fabro re-vendor PR #233 merged); **S3 gate inverted**
(git-jsonl re-vendor PR #158 terminally BLOCKED on S3's own schema work — 87
`unexpected extra keys` failures; land S3 WITH the pin bump). S4/S5 read `ready`
but are dep-gated on S2 via `depends_on` edges. See `handoff.md` §"Session 8".

**Session 9 (2026-07-02):** re-composed core-ledger status LIVE (queue empty; the
four P0 factory-hardening threads remain top priority but are all cross-tenant), then
filed the two verified CORE spec-side drifts as pending proposals: **item 15 / C15
FILED** → `proposed_changes/callability-warn-fail-lever.md` (**PR #769**) and
**gap-dg2rdlsf FILED** → `proposed_changes/coverage-omit-only-not-source-allowlist.md`
(**PR #770**, the coverage `source`→omit-only reconcile — the last known CORE spec-side
drift from the Session-3 `--since-version 150` pass). **Both then REVISED IN** —
`/livespec:revise` accepted both → history **v154** (**PR #772**, merged; pre/post
doctor static + full `just check` green). Queue back to README-only; the thread's
CORE spec-side drift work is COMPLETE (do NOT re-run revise/propose-change). See
`handoff.md` §"Session 9 (continued)".
