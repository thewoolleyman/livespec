# Ledger status-conformance cleanup + beads create-status adoption — plan handoff (livespec core)

> **Status: DRIVEN — all in-fleet work COMPLETE (2026-07-12 session).** Scopes
> 1–3 are landed; the one external piece (beads `status.default` PR #4738) is
> OPEN for upstream review. See "## Session close" for final states and the small
> set of open/deferred follow-ups. The "## Driven session progress" section holds
> the design narrative + corrected findings; the sections below it are the
> ORIGINAL seed framing (kept for context; superseded where noted).
>
> _Original seed note:_ spun off 2026-07-12 from the `autonomous-mode` track
> (during an attempt to factory-dispatch a `livespec-dev-tooling` work-item). Does
> NOT block autonomous-mode.

## Session close (2026-07-12) — final states

| Workstream | Repo | Outcome |
|---|---|---|
| Scope 1 — remediate 12 drifted items | fleet | ✅ done — 0 drift across all 8 members (verified) |
| Scope 2 — reflector `file_new` two-step | orchestrator | ✅ merged — PR #535 (`ea1e441`); reflections now file at `backlog` |
| Scope 3a — detect (needs-attention-internal Signal 5) | core | ✅ merged — PR #1107 |
| Scope 3b — auto-fix (`ledger-normalize` + generalize remap) | orchestrator | ✅ merged — PR #537 (`9ea4f1a`); LIVE-exercised (healed 3 fresh real `open` items → fleet 0 drift) |
| Scope 4 — beads `status.default` config | external `gastownhall/beads` | 🔎 PR #4738 OPEN for upstream review (not merged) — precedence flag>defer>status.default>open; 4 cases live-verified; upstream CI running |

**Live-verified end-to-end:** `ledger-normalize --dry-run` detects, the real run
heals `open`→`backlog` / `in_progress`→`active` and persists, residual (deferred/
hooked/ad-hoc) is report-only. The recurring-drift concern (any raw `bd create`/
`--claim` can still mint a non-conformant item) is now covered by detection +
auto-fix — proven when 3 new `open` items drifted in mid-session and were healed.

**Open / deferred follow-ups (none blocking):**
1. **beads #4738** — awaiting upstream review/merge. The sandbox embedded-Dolt
   test harness was too slow to run the new `TestEmbeddedCreate/default_status_*`
   subtests to completion; they are committed + compile-clean + the 4 behaviors
   were live-verified, and upstream CI runs the full suite. Contributor worktree
   kept at `/home/ubuntu/.worktrees/beads/feat-create-default-status-config`
   (branch `feat/create-default-status-config`) in case review requests changes.
2. **Fleet adoption of `status.default`** — once #4738 merges + releases, set
   `status.default = backlog` in each fleet tenant's `.beads/` config (the
   holistic PREVENTION layer: makes a bare/raw `bd create` land conformant).
3. **Single-step create** — once a beads release carries #4536 (`bd create
   --status`, currently 23 commits ahead of v1.1.0), collapse the store +
   reflector two-steps into single-step (pure simplification).
4. **Scheduling decision (for the maintainer)** — whether `ledger-normalize`
   should run on a SCHEDULE (fully hands-off self-heal) or only via the
   `needs-attention-internal` one-command handoff (current state). Mechanism
   exists; scheduling is a small add if wanted.

## Driven session progress (2026-07-12)

**Confirmed direction (maintainer):** the recommended holistic option — **detect +
auto-fix** — AND the upstream prevention is a REAL beads PR (not just an issue).
Rationale the maintainer surfaced: a create-time `--status` option is never
sufficient, because any code path / agent / human can forget it or run raw
`bd create`/`bd --claim` and still mint a non-conformant item. So create-time
correctness is defense-in-depth; the *guarantee* is detection + fix.

**Scope 1 — DONE.** Remapped 12 drifted items to lifecycle statuses and verified
0 status-conformance fails on all 8 members:
- core: `3lev, 3lev.1, 3lev.3, gqte, v74p` (all `in_progress` → `active`; all the
  live `fabro-ci-image-factoring` epic family).
- dev-tooling: `2kt, 65c, 800, fz4, g28, q9a, xam` (all `open` → `backlog`).
  `fz4` is the autonomous-mode top priority — flagged for possible `ready`/`active`
  promotion (left at `backlog` for now).

**Corrected Scope-2 finding (agent-verified).** The store's create path
(`_store_mutations.py` `create_work_item`) ALREADY does the two-step (create →
`update --status`), and all 5 create SKILLS route through it (statuses
`backlog`/`pending-approval`). The drift came from **raw `bd` usage bypassing the
store** (dev-tooling opens have no `origin:` label/rank metadata → raw
`bd create`; core `in_progress` → raw `bd --claim`). The ONE genuine code gap is
the **reflector filing path** `commands/_reflector_filing_store.py` `file_new()`
(calls `create_issue` with no follow-up status set → lands `open`). No `--claim`
or `in_progress` is emitted anywhere in code (root cause #2 is purely ad-hoc raw
bd usage, not wrapper-fixable → handled by detection).

**Beads version finding.** The maintainer's per-call `--status` PR is
`gastownhall/beads` **#4536** (feature commit `d641cd90a`), merged 2026-07-05 to
`main` — but it is **not in any tagged release**: latest release is **v1.1.0**
(2026-07-04), and #4536 is **23 commits ahead of v1.1.0**. Installed host `bd` is
**v1.0.5** (no create `--status`). Confirmed: beads has **no** tenant-level
default-create-status config on any release/main — the only lever is the per-call
flag. This is exactly why detection+auto-fix is the guarantee, and why a
tenant-default is a worthwhile second upstream contribution.

**The holistic design (4 workstreams, driven as one thread):**
1. **Reflector fix** (livespec-orchestrator-beads-fabro) — add the status-setting
   step to `file_new` so reflections file at `backlog`, not `open`. → DISPATCHED
   (TDD Red-Green + worktree PR). Branch `fix/reflector-filing-lifecycle-status`.
2. **Detect** (livespec core) — add a 5th signal (ledger status-conformance drift)
   to the local `needs-attention-internal` skill, running the cheap per-tenant
   `dispatcher.py ledger-check` status-conformance scan inline across the fleet
   manifest, emitting an `attention_item` per drifted member with the normalizer
   command as `handoff.command`. → prose change, IN PROGRESS.
3. **Auto-fix** (livespec-orchestrator-beads-fabro) — a normalizer entry point
   beside `ledger-check` (which already imports `ALLOWED_BEADS_STATUSES` from
   `_store_statuses.py`) that safely remaps the two unambiguous beads built-ins
   (`open`→`backlog`, `in_progress`→`active`) and REPORTS (never auto-touches)
   `deferred`/`hooked`/`pinned`/anything else. → queued behind the reflector PR
   (same repo; land sequentially to avoid PR churn).
4. **Beads upstream PR** (external `gastownhall/beads`) — implement a
   `status.default` DB config so a bare `bd create` uses a configured lifecycle
   status instead of `open`. Precedence `--status` flag > `--defer` > `status.default`
   > `open`; validate via `types.Status.IsValidWithCustom`; insertion point
   `buildCreateIssue` (`cmd/bd/create.go:754`) via a new `DefaultStatus` param.
   Opened as an UPSTREAM PR (fork `thewoolleyman/beads` → `gastownhall/beads:main`),
   NOT merged (upstream reviews). → DISPATCHED. Branch
   `feat/create-default-status-config`.

**Tracking decision.** This THREAD's `handoff.md` (this file) is the authoritative
cross-repo tracker for the 4 workstreams; the 2 dispatched PRs are self-tracking
on GitHub. A separate formal ledger EPIC was deliberately NOT filed this session:
filing it via raw `bd` would bypass the store two-step (the exact anti-pattern
this thread fixes), and the interactive store-routed path (`plan`/`capture-work-item`)
is disproportionate ceremony for in-session-driven work already tracked here. If
this work outlives the session or needs factory dispatch, anchor it then via
`/livespec-orchestrator-beads-fabro:plan ledger-status-conformance` (which files
the epic through the store, correctly).

**Deferred (release-gated):** once beads ships a release carrying #4536, collapse
the store + reflector two-steps into single-step `bd create --status` (pure
simplification). And once the `status.default` PR lands + releases, adopt it in
the fleet tenants' `.beads/` config (holistic prevention).

**Open question for a later turn:** whether the auto-fix normalizer runs on a
SCHEDULE (truly hands-off) or only via the `needs-attention-internal` handoff
(one-command). Built the mechanism first; scheduling is a small follow-up to
confirm with the maintainer.

## The finding (why this thread exists)

The Beads/Dolt+Fabro **dispatcher's `ledger-check` gate** rejects any work-item
whose status is outside the **livespec lifecycle**. The allowed lifecycle statuses
are exactly:

```
acceptance, active, backlog, blocked, closed, pending-approval, ready
```

A survey of all 8 fleet members (2026-07-12) found **2 members drifted**; the other
6 are clean:

| Member | Non-conformant items | Status seen | Root cause |
|---|---|---|---|
| `livespec-dev-tooling` | 7 (`fz4, 800, q9a, g28, xam, 2kt, 65c`) | `open` | `bd create` default |
| `livespec` (core) | 3 (`3lev, 3lev.1, 3lev.3`) | `in_progress` | `bd --claim` / `--status in_progress` |
| `livespec-driver-claude` | 0 | — | clean |
| `livespec-driver-codex` | 0 | — | empty ledger |
| `livespec-orchestrator-beads-fabro` | 0 | — | clean |
| `livespec-orchestrator-git-jsonl` | 0 | — | clean |
| `livespec-runtime` | 0 | — | clean |
| `livespec-console-beads-fabro` | 0 | — | clean (actively uses `ready`/`active`) |

**The tenants are NOT mis-provisioned** — every tenant accepts the lifecycle (all
carry `backlog`/`blocked` items). The drift is a handful of individual items left
at raw-beads statuses.

**Root causes (two distinct):**
1. `bd create` defaults new items to `open`, which is not a lifecycle status. Any
   item filed via a create path that doesn't set a status stays `open`.
2. `bd --claim` (and `bd update --status in_progress`) sets beads' built-in
   `in_progress`; the livespec lifecycle expresses "being worked" as `active`.

**Why it accumulated silently:** the ONLY thing that checks status-conformance is
the dispatcher's `ledger-check`, and it only runs at dispatch time. `core` and
`dev-tooling` are rarely dispatched, so their drift never surfaced.

⚠️ **The 3 core `in_progress` items are the LIVE `fabro-ci-image-factoring` epic**
(`3lev` + children, assignee `chad@thewoolleyman.com`, updated 2026-07-12). They
are genuinely in-flight — `in_progress` → `active` is semantically identical (both
mean "being worked"), so remapping is safe, but coordinate with whoever is driving
that thread so a status flip doesn't surprise them.

## New enabling fact (maintainer, 2026-07-12)

Beads just merged a PR (a livespec upstream contribution) that allows a custom
status to be specified at **create** time (`bd create --status <status>`). Adopting
this mechanically in the create wrappers is the durable fix for root cause #1.

## Reproduce the survey (run first — the numbers above may have moved)

```bash
/usr/local/bin/with-livespec-env.sh -- bash -c '
DISP=/data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/bin/dispatcher.py
for r in livespec livespec-dev-tooling livespec-driver-claude livespec-driver-codex \
         livespec-orchestrator-beads-fabro livespec-orchestrator-git-jsonl \
         livespec-runtime livespec-console-beads-fabro; do
  python3 "$DISP" ledger-check --project-root "/data/projects/$r" --json \
    | python3 -c "import sys,json; d=json.load(sys.stdin); \
      sc=[x for x in d if x.get(\"check\")==\"status-conformance\"]; \
      print(\"'"$r"'\", len(sc), \"status-conformance fails\", \
      [x[\"item_id\"] for x in sc])"
done'
```

## Scope 1 — remediate the drifted items (data-only, fast; do this first to green the fleet)

- **dev-tooling:** re-survey first (`fz4` may already be closed by its own fix PR),
  then for each remaining `open` item: `bd update <id> --status backlog` (or
  `--status ready` if it is genuinely groomed and ready), run from the dev-tooling
  checkout under `with-livespec-env.sh`.
- **core:** remap the 3 `in_progress` → `active` (`bd update <id> --status active`),
  after coordinating with the `fabro-ci-image-factoring` thread.
- **Verify:** re-run the survey above → 0 status-conformance fails on every member.

## Scope 2 — stop new drift (beads upgrade + wrapper adoption)

- **Bump the pinned `bd` host binary** (currently v1.0.5 at `/usr/local/bin/bd`,
  `LIVESPEC_BD_PATH`) to the release carrying the create-time `--status` PR.
  Confirm which release ships it (the PR landed 2026-07-12).
- **Adopt `--status` mechanically in the impl-beads CREATE wrappers** in
  `livespec-orchestrator-beads-fabro` so nothing defaults to `open`:
  `capture-work-item`, `groom` (epic anchor + slices), `capture-impl-gaps`,
  `capture-spec-drift`, `plan` (epic anchor). Grep the store-wrapper create path
  (`bd create`) for every call site; pass `--status backlog` by default.
- **Make the START/CLAIM path use lifecycle `active`**, not raw `bd --claim`
  (`in_progress`). The dispatcher already sets `active`; the gap is human/agent raw
  `--claim`. Wrap or guard it (root cause #2).

## Scope 3 — catch drift without a dispatch (the durable fix for the silent-accumulation gap)

Only the dispatcher's `ledger-check` catches non-lifecycle statuses, and only for
dispatch tenants. Wire ledger-status-conformance into a fleet-hygiene surface so
ANY tenant's drift surfaces without needing a dispatch:
- Fold it into `needs-attention-internal` (livespec core, LOCAL maintainer-only
  skill) which already composes "fleet-conformance drift"; **or**
- A periodic/scheduled conformance check that reddens on drift.

## First steps for the driving session

1. Open the ledger epic anchor for this thread in **livespec core** (dogfood
   `bd create --status backlog` if the pin is already bumped; else set the status
   right after create).
2. Re-run the survey (Scope 1 top) — the data above is a 2026-07-12 snapshot.
3. Scope 1 (data-only) → fleet green. Then Scope 2 + Scope 3.

## Done means

- Survey across all 8 members = 0 status-conformance fails.
- A new item created via the wrappers lands with a lifecycle status (never `open`).
- Ledger status drift surfaces in a fleet-hygiene surface WITHOUT requiring a
  dispatch.

## Repos touched

- `livespec` (core): this handoff; Scope 1 core-item remap; Scope 3 surface.
- `livespec-dev-tooling`: Scope 1 open-item remap; possibly a Scope 3 check.
- `livespec-orchestrator-beads-fabro`: Scope 2 create/claim wrapper adoption.
- host `bd` binary pin: Scope 2 upgrade.

## Cross-references

- Found during: `plan/autonomous-mode/` (the `fz4` dev-tooling dispatch attempt).
- The lifecycle status set is defined by the dispatcher's `ledger-check`
  (`livespec-orchestrator-beads-fabro`).
- Discipline: "Fix the gate, not the bypass" — the fix is create-time correctness +
  a fleet-hygiene surface, never skipping `ledger-check` or weakening the lifecycle.

---

# SESSION 2 (2026-07-12 → 13) — enforcement gate + bd guard wrapper + root-cause

**Read this section first; it supersedes the older sections where they conflict.**
This session extended the thread from "detect + auto-fix + upstream-prevent" into a
tool-boundary enforcement design after live exercise revealed the drift is
CONTINUOUS, not one-time.

## Landed this session (all merged unless noted)

| What | Repo | PR / state |
|---|---|---|
| Reflector `file_new` two-step fix | `livespec-orchestrator-beads-fabro` | #535 merged (`ea1e441`) |
| Auto-fix: `ledger-normalize` cmd + generalize remap (`open`→`backlog`, `in_progress`→`active`) | `livespec-orchestrator-beads-fabro` | #537 merged (`9ea4f1a`) — live-exercised |
| Detect: `needs-attention-internal` Signal 5 | `livespec` core | #1107 merged |
| Pre-push conformance gate (detect-and-fail prototype) | `livespec-orchestrator-beads-fabro` | #548 merged (`0fb66ed`) — `ledger-normalize --gate`, `check-ledger-conformance-live` recipe, always-run lefthook `ledger-conformance` cmd, fail-soft |
| Handoff updates | `livespec` core | #1101, #1104, #1110 merged |
| beads `status.default` config | `gastownhall/beads` (external) | **#4738 DRAFT — awaiting maintainer's Fable/Codex adversarial review** |
| bd guard wrapper (warn-first) | `livespec-orchestrator-beads-fabro` | **DISPATCHED this session — branch `feat/bd-guard-wrapper-warn-first`, PR left OPEN for review, NOT installed on host** |

## ROOT CAUSE (definitively established via `bd history`)

The drift is NOT from our code paths (we fixed the ONE buggy one — the reflector;
the store already did the two-step correctly). It is CONTINUOUS churn from **raw /
native `bd` usage by active sessions**, which our code cannot intercept:
- **`open`** ← raw `bd create` bypassing the store (dev-tooling opens had no
  `origin:`/rank fingerprint). The bare-create→open case can only be neutralized by
  the tenant `status.default` (our draft #4738) — NOT by the `--status` flag (raw
  callers don't pass flags).
- **`in_progress`** ← raw `bd update --claim` (the natural beads "start work"
  command; sets `in_progress`). Proven: `livespec-3lev.2` sat at `backlog` for hours
  then a raw claim flipped it to `in_progress`. **NOTHING upstream fixes this** —
  `status.default` only touches creates. The **guard wrapper is the only mechanism
  that can prevent the raw-claim drift.**
- Possible minor contributor: the store two-step is non-atomic, so an interrupted
  create can strand an item at `open` (single-step `bd create --status` would kill
  this sliver, once beads releases the flag).

## BEADS VERSION FACTS (verified live — settle any confusion)

- Installed/pinned `bd` = **v1.0.5** (`/usr/local/bin/bd`; `LIVESPEC_BD_PATH` is
  UNSET → falls back to it). **No `create --status`.**
- The `--status` flag is PR #4536, merged to beads `main` 2026-07-05 but **in NO
  tagged release/pre-release**: v1.1.0 is 23 commits behind it; rc.1/rc.2 are older
  still; v1.0.5 is 278 behind. There is NO canonical tag to pin to.
- **DECISION (maintainer): stay on canonical v1.0.5; do NOT build/pin from a fork —
  we gain little (store already lands conformant via the two-step). Wait for beads
  to cut a release with #4536 ("should be soon").** Once released: bump the pin,
  make the store single-step, and adopt `status.default`.

## DECISIONS made this session

1. **Do NOT dilute the livespec lifecycle** (rejected `in_progress`≡`active`). The
   lifecycle is LEDGER-AGNOSTIC — beads is one impl of many; never bend the generic
   contract to a beads idiosyncrasy. Fix upstream or guard the boundary. This is a
   core architecture principle for this thread.
2. **Fleet gate = auto-heal-LOUD** (not detect-and-fail). Live exercise showed
   `open`/`in_progress` appear CONTINUOUSLY (multiple active sessions creating +
   claiming; watched `3lev.2` flip `open`→`in_progress` between two commands). On a
   SHARED tenant, detect-and-fail blocks any session on any other session's fresh
   transient item → constant cross-session friction. So the fleet gate should
   auto-normalize the two definitionally-safe transient states (`open`→`backlog`,
   `in_progress`→`active`), **PRINT each remap** (loud, not hidden — this answers the
   original "no silent DB writes" objection), and block ONLY on residual
   (deferred/hooked/ad-hoc → human lane decision). **CONFIRMED, NOT YET BUILT.**
3. **bd guard wrapper (warn-first → fail)** as the version-independent stopgap that
   covers what no beads flag can — raw usage across ALL callers. Warn-first rollout
   (observe offenders, don't break), then flip to fail. DISPATCHED (see below).

## OPEN WORKSTREAMS / NEXT ACTIONS (for the new session)

1. **bd guard wrapper** — a background agent is building it in
   `livespec-orchestrator-beads-fabro` (branch `feat/bd-guard-wrapper-warn-first`).
   SCOPE this build: guards the EXPLICIT bad-status ops only — `bd update --status
   <non-lifecycle>` and `bd update --claim` (→ warn/fail); passes everything else
   (incl. `create`) through transparently. Create-guarding is deliberately OUT (a
   single-command wrapper on v1.0.5 can't tell the store's two-step from a raw
   create; that half is the normalizer + `status.default`). Deliverables: wrapper +
   codified installer + rollback + hermetic tests; **NOT installed on host** (host
   swap is maintainer-gated). **CHECK the PR when the agent reports; review; then
   the maintainer runs the installer in `warn` mode, observes offenders, fixes the
   raw-claim callers, then flips `LIVESPEC_BD_GUARD_MODE=fail`.** Host swap replaces
   `/usr/local/bin/bd` → moves real to `/usr/local/bin/bd-real` — blast radius is
   fleet-wide; one-command rollback required.
2. **Fleet gate → auto-heal-loud** — change the merged prototype gate (`--gate` /
   `check-ledger-conformance-live` in `livespec-orchestrator-beads-fabro`) from
   detect-and-fail to auto-heal-loud (heal the 2 safe transient states + print each,
   block only on residual), then ROLL OUT to all tenant-bearing fleet repos (each
   needs the lefthook `ledger-conformance` command + a recipe resolving its
   `.livespec.jsonc` `credential_wrapper` + the dispatcher path — note non-orchestrator
   repos invoke the dispatcher via the INSTALLED plugin, not local source; that
   resolution is an unsolved rollout detail).
3. **beads #4738 (`status.default`) review** — DRAFT, awaiting the maintainer's
   independent Fable + Codex adversarial review. Branch
   `feat/create-default-status-config` (`56adee21b`) is checked out in
   `/data/projects/beads`. After review passes + any fixes: `gh pr ready 4738
   --repo gastownhall/beads`. Then (once merged + released) adopt `status.default =
   backlog` in each fleet tenant's `.beads/` config (the holistic create-side
   prevention).
4. **Wait for beads release with #4536**, then: bump the `bd` pin, make the store
   `create_work_item` single-step (`bd create --status`), retire the two-step + the
   interrupted-two-step sliver.
5. **Tenant currently NOT clean** — expect fresh `open`/`in_progress` items on any
   survey (it's live churn). Heal on demand with
   `with-livespec-env.sh -- python3 <orch>/.claude-plugin/scripts/bin/dispatcher.py
   ledger-normalize --project-root /data/projects/<repo>` (dry-run first).

## Layered end-state (how the pieces fit)

- **Prevent (source):** store two-step (done) + reflector fix (done) + guard wrapper
  (raw claims, in progress) + `status.default` (raw creates, upstream, draft).
- **Detect:** `needs-attention-internal` Signal 5 (done) + the pre-push gate (done,
  → auto-heal-loud).
- **Heal:** `ledger-normalize` (done) — the safety net for anything that slips past
  prevention (bypass, pre-wrapper, `bd-real` direct use).
The guard wrapper + `status.default` are STOPGAP/durable prevention; both retire or
simplify once beads ships proper custom-status handling upstream.
