# Ledger status-conformance cleanup + beads create-status adoption — plan handoff (livespec core)

> **SESSION 11 (2026-07-18) — close-out reconciliation + trigger fixes; thread ARCHIVED. No open work.**
>
> After the SESSION 10 close-out note merged (livespec core PR #1314), the
> maintainer flagged recurring "bd-guard failure" emails from Honeycomb over the
> prior ~3 days and asked to confirm they were transient noise before closing.
> Investigated in the `livespec` env / `bd-guard` dataset:
>   - **They were noise — the telemetry-stalled trigger firing on host-idle.**
>     Across 5 days there are only 3 `guard.warned=true` events total (2 test
>     probes + 1 *pre-flip* real `--status done` that passed through in warn
>     mode); in the last 3 days, exactly ONE — the deliberate `zzz-flip-probe`.
>     **Zero legitimate workflows were ever blocked.** The recurring mail was
>     `VrKJu9hrgr` (telemetry stalled) tripping whenever the host had no `bd`
>     traffic for 60 min (normal idle); the pipeline self-recovered every time
>     and is healthy (both triggers currently green).
>   - **Two trigger fixes landed (Honeycomb, `livespec` env):**
>     1. `nak9miYrs14` (raw-op-BLOCKED alert) had lost BOTH recipients — its
>        `updated_at` matched the SESSION-9 description edit, so that
>        `update_trigger` call inadvertently cleared them (the API drops
>        recipients on a partial update that omits them). **Restored** both team
>        emails — without this, a genuine fail-mode block would have paged nobody.
>        LESSON: always re-pass `recipients` on any Honeycomb `update_trigger`.
>     2. `VrKJu9hrgr` (telemetry-stalled) **widened 1h → 8h** (frequency raised
>        1h→2h to satisfy Honeycomb's duration ≤ 4×frequency rule) so normal
>        host-idle no longer false-alarms; a sustained dead pipeline still does.
>   - **This thread is now ARCHIVED** to `plan/archive/ledger-status-conformance/`
>     (moved out of the active `plan/` set). The two durable triggers remain the
>     standing safety net; external/upstream waits (beads #4738, a #4536-carrying
>     release) are unchanged and do not block closure.

> **SESSION 10 (2026-07-18) — ✅ TRACK CLOSED. Post-flip observation window is conclusively clean; nothing left to watch.**
>
> The SESSION 9 flip (bd-guard host-wide `fail` mode) has now run ~2.85 days
> under real load with zero incident. Honeycomb `livespec` env / `bd-guard`
> dataset, `guard.mode=fail` since the flip:
>   - **24,803** real `bd` ops flowed through the guard from **5** distinct
>     caller processes.
>   - **Exactly 1** was blocked (`guard.warned=true`) — the deliberate
>     `zzz-flip-probe-DELETEME --claim` test probe. **Zero legitimate workflows
>     blocked.**
>   - Diverse lifecycle mutations passed clean (`update` 206, `create` 59,
>     `close` 27, `dep` 21, `ready` 3, …), so the guard is discriminating
>     correctly — not waving everything past.
>   - This clears the original readiness bar (≥500 ops/24h, ≥3 callers, 0 real
>     blocks) by ~17×. In `fail` mode the guard is behavior-transparent on any
>     op it passes, so the ONLY way it can break a workflow is a block — and the
>     only block was our own probe.
>
> **The observation phase (SESSION 9's "only remaining work") is DONE.** The two
> durable Honeycomb triggers remain live as the standing, session-independent
> safety net: `nak9miYrs14` (raw op caught → in `fail` mode = BLOCKED; its
> description was updated to fail-mode semantics this session) and `VrKJu9hrgr`
> (telemetry-stalled). No polling loop or session heartbeat is needed; the
> transient session health monitor was stopped at close.
>
> **UNCHANGED external/upstream waits (do NOT block closure):** beads #4738
> (`status.default`) awaiting the `gastownhall/beads` maintainer; a beads release
> carrying #4536 (`bd create --status`) → then bump the pin, single-step the
> store, and eventually RETIRE the guard (it is a stopgap).
>
> The SESSION 9 flip narrative was committed in livespec core PR #1256; this note
> closes the track. Everything below is prior-session history.

> **SESSION 9 (2026-07-15) — ✅ THE GUARD IS FLIPPED TO `fail`, LIVE-VERIFIED. THE TRACK'S GOAL IS ACHIEVED. Do NOT re-do the flip.**
>
> The bd-guard now BLOCKS (enforces) host-wide in `fail` mode — the long-pending
> final step of this whole track. This session the maintainer demanded an
> independent **Codex + Fable adversarial review** to PROVE the flip would be
> incident-free BEFORE flipping. The reviews found **3 real defects** that 34h of
> clean telemetry never would have — the flip *as previously documented* (`export
> LIVESPEC_BD_GUARD_MODE=fail`) would have been a **SILENT NO-OP**:
>   1. that `export` is **scrubbed** by the credential wrapper
>      (`with-livespec-env.sh` does `env -i` / sudo `env_reset`) → never reached bd;
>   2. fail-mode blocks emitted **no telemetry** (exit 3 before the emit) → invisible;
>   3. `bd --format json update … --claim` **bypassed** the parser.
>   Plus 2 more argv-detectable non-lifecycle channels were unguarded: `bd ready
>   --claim` (→ in_progress) and `bd defer <id>` (→ deferred).
>
> **ALL FIXED + MERGED in `livespec-orchestrator-beads-fabro`** (both auto-merged, CI green):
>   - **PR #621** — host-wide mode **FILE** (`/usr/local/etc/livespec-bd-guard.mode`,
>     survives the env scrub) + emit-a-span-on-block + `--format` skip.
>   - **PR #628** — guard `bd ready --claim` + `bd defer`; harden the mode-file
>     read (a `fail` with no trailing newline used to silently degrade to warn).
>   Re-verified clean: Codex **SAFE** (no bypass across 12 flag prefixes, no
>   false-positive); Fable verified all fixes real vs the live wrapper/collector/
>   trigger/upstream bd source; plus my own **15/15** hermetic sweep.
>
> **INSTALLED + FLIPPED on the host, LIVE-PROVEN end-to-end (~05:25 UTC 2026-07-15):**
>   `sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/install.sh`
>   refreshed the wrapper + seeded the mode file = warn; then the flip. A `bd
>   update <bogus> --claim` **through the real credential-wrapper path returned
>   exit 3** and emitted a `guard.mode=fail / guard.warned=true / exit_code=3`
>   span; `bd --version` + `bd list` passed (exit 0). B1 (reaches callers) + B2
>   (observable) both proven live.
>
> **THE HOST-WIDE FLIP MECHANISM — THIS is the runbook; the old `export …=fail` is DEAD (scrubbed):**
> ```
> block:   echo fail | sudo tee /usr/local/etc/livespec-bd-guard.mode
> revert:  echo warn | sudo tee /usr/local/etc/livespec-bd-guard.mode
> full rollback (remove guard entirely):
>          sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/rollback.sh
> ```
> Current mode: **`fail`**. Guard blocks 5 channels: `update --claim`, `update
> --status <non-lifecycle>`, `reopen`, `ready --claim`, `defer`. Everything else
> (create / list / show / close / dep / config / conformant `--status` / …) passes.
>
> **ONLY REMAINING WORK — post-flip observation (LOW effort, mostly passive):**
>   - The Honeycomb trigger **`nak9miYrs14`** (`guard.warned=true COUNT>0`, emails
>     both team addrs) now means **"a raw op was BLOCKED."** Watch it + the board
>     https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/j2MHvDsuWry
>   - Query fail-mode blocks: `livespec` env, `bd-guard` dataset, filter
>     `guard.mode=fail AND guard.warned=true`, breakdown `bd.caller.cmd` +
>     `guard.op` + `bd.subcommand`.
>   - **IF a genuinely LEGIT workflow appears blocked** (a real caller, not a
>     probe): decide — fix that caller to use a lifecycle status, OR if it is a
>     legit pattern the guard should not touch, **revert to warn** (`echo warn |
>     sudo tee …`) and reassess. Baseline through the flip: **0 legit guarded-op
>     callers EVER** (only a test probe + one invalid `--status done`), so a
>     surprise is unlikely.
>   - **IGNORE** the one flip-probe I generated — `bd.caller.cmd` containing
>     `zzz-flip-probe-DELETEME --claim` (my deliberate exit-3 test; it tripped the
>     trigger once — benign).
>
> **HOUSEKEEPING:**
>   - **This handoff edit is UNCOMMITTED** on the livespec primary checkout (a
>     `plan/` doc; working tree shows `plan/ledger-status-conformance/handoff.md`
>     modified). Commit via a normal `docs(plan):` worktree PR when convenient.
>   - Orchestrator worktree `fix-bd-guard-flip-hardening` (PR #621) reaped this
>     session; `fix-bd-guard-ready-defer` (PR #628) self-reaped by its executor;
>     `chore-cross-track-handoffs` belongs to ANOTHER session — untouched.
>   - The hourly readiness `/loop` cron is **retired** (the flip happened; its
>     "wait for 24h" premise is moot). Do NOT re-arm it.
>
> **EXTERNAL / UPSTREAM (unchanged, pure wait — not this session's work):** beads
> #4738 (`status.default`) awaiting the gastownhall maintainer; a beads release
> carrying #4536 (`bd create --status`) → then bump the pin, single-step the
> store, and eventually RETIRE the guard (it is a stopgap).
>
> Everything below is prior-session history (SESSIONS 1–8) — the flip they were
> all building toward is now DONE.

> **Status: DRIVEN — all in-fleet work COMPLETE (2026-07-12 session).** Scopes
> 1–3 are landed; the one external piece (beads `status.default` PR #4738) is
> OPEN for upstream review. See "## Session close" for final states and the small
> set of open/deferred follow-ups. The "## Driven session progress" section holds
> the design narrative + corrected findings; the sections below it are the
> ORIGINAL seed framing (kept for context; superseded where noted).
>
> **SESSION 3 (2026-07-13):** the bd guard wrapper LANDED. PR #556 merged
> (`livespec-orchestrator-beads-fabro`, release 0.26.0) after review found + fixed
> 2 blockers (broken `rollback.sh`; `install.sh` self-exec-loop). Follow-up PR
> #561 merged (guard `bd reopen`; `install.sh` fresh-provision relocate). See
> "## SESSION 3" at the bottom. Host install of the guard remains maintainer-gated
> (warn → observe → flip to `fail`).
>
> **SESSION 4 (2026-07-13):** the fleet gate is now AUTO-HEAL-LOUD, and the
> fleet-wide ROLLOUT was CLOSED as not-worth-doing (maintainer-declared). The
> orchestrator's pre-push gate was converted from detect-and-fail to auto-heal-loud
> (`livespec-orchestrator-beads-fabro` PRs #566 + fix-forward #568, release 0.28.1).
> A rollout to other tenant repos was investigated and DECLINED: the No-Circular-
> Dependency directive forbids the two drift-prone upstream repos (`livespec` core,
> `livespec-dev-tooling`) from carrying it, the eligible downstream repos don't
> drift, and "catch drift without a dispatch" is already met fleet-wide by
> `needs-attention-internal` Signal 5 + on-demand `ledger-normalize`. See
> "## SESSION 4" at the bottom.
>
> **SESSION 5 (2026-07-13):** the next-action discipline was corrected: a
> maintainer-gated host install is NOT a blocker or "nothing to do"; it is a
> confirmation prompt. The NEXT ACTION on this track is to recommend installing
> the BD guard in warn mode, explain the host-wide `/usr/local/bin/bd` blast
> radius, show the exact install + rollback commands, and ask the maintainer to
> confirm before running it. See "## SESSION 5" at the bottom.
>
> **SESSION 6 (2026-07-13):** SESSION 5's designated next action is DONE — the
> BD guard is INSTALLED on the host in warn mode (maintainer-confirmed) and
> verified live end-to-end (passthrough intact; warn/fail/reopen behaviors
> correct; 8-member survey through the guard = 0 drift). Fleet 0 drift + master
> CI green on both repos. beads #4738 developed a merge conflict (upstream moved;
> left for the `gastownhall/beads` maintainer); beads #4536 still unreleased
> (`main` 230 ahead of v1.1.0). See "## SESSION 6" at the bottom.
>
> **SESSION 7 (2026-07-13):** the bd-guard now EMITS a `bd.invoke` OTel span per
> host `bd` call to Honeycomb (livespec env, `bd-guard` dataset) — a live "many
> callers / 0 guard-induced failures" proof surface + drift detection, answering
> "why not use Honeycomb observability?". Landed: collector HTTP receiver
> (`otel-collector` `95e57a1`), guard emit (`livespec-orchestrator-beads-fabro`
> PR #580 / `e30ada0`), routing to the livespec env (`otel-collector` `f741249`);
> host reinstalled. Built a Honeycomb board + two checkpoint triggers
> (telemetry-stalled; raw-op detected). Also healed fresh livespec drift (4
> `open`->`backlog`, 0 drift). Flip-to-`fail` stays gated. See "## SESSION 7" at
> the bottom.
>
> **SESSION 8 (2026-07-13, WRAP):** bd-guard telemetry (SESSION 7) is LIVE; the
> only active work is the hourly fail-mode readiness monitor. Current: NOT READY,
> gated on TIME (~21.5h more telemetry + a clean 12h raw-op window; only a leftover
> test probe sits in the window, no real raw op; 0 guard-induced failures across
> 161 calls / 4 callers). RESUME by re-arming the readiness `/loop` (verbatim
> command in "## SESSION 8"). Flip-to-`fail` stays maintainer-gated. See
> "## SESSION 8" at the bottom.
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

---

# SESSION 3 (2026-07-13) — bd guard wrapper reviewed, fixed, merged + hardened

**Read this after SESSION 2.** SESSION 2 DISPATCHED the guard wrapper and left it
as an OPEN PR for review. This session reviewed it, fixed the blockers review
found, merged it, then merged an approved hardening follow-up. The guard wrapper
is now MERGED + RELEASED; the only remaining guard step is the maintainer-gated
host install.

## Landed this session (all merged, `livespec-orchestrator-beads-fabro`)

| What | PR | Merge commit | Notes |
|---|---|---|---|
| bd guard wrapper (warn-first) — original | #556 | `65b2d68` (feat) | The SESSION-2 dispatched wrapper. |
| Fix: install/rollback self-recognition + claim/`--` holes | #556 | `299dc5e` (fix) | Review found 2 BLOCKERS the green suite missed. Shipped as **release 0.26.0**. |
| Guard `bd reopen` + `install.sh` fresh-provision relocate | #561 | `6635f22` (feat) | The maintainer-approved "do both now" hardening. |

## What the review caught (the 2 blockers — a real "green ≠ correct" case)

Both from ONE root cause: `install.sh`/`rollback.sh` recognized the guard via
`head -n 1 "$FILE" | grep -q 'bd-guard'`, but line 1 is the `#!/bin/sh` shebang, so
the check NEVER matched. Result: `rollback.sh` ALWAYS aborted (its "trivially
removable" guarantee was false) and a partial-install re-run could `mv` the guard
onto `bd-real` → infinite exec loop. Fixed by grepping the WHOLE file for a
distinctive `bd-guard-wrapper-sentinel` marker. Also fixed 2 review nits
(`--claim=true` `=`-form bypass; root-level `--` wrong-block in fail mode). ROOT
CAUSE of the miss: the test suite never exercised `install.sh`/`rollback.sh` —
now it drives them end-to-end (byte-identical restore, idempotency,
partial-install no-exec-loop). Both the initial review and a Fable delta review
were NO-BLOCKERS; full `just check` green.

## Guard scope now (3 ops)

`bd update --status <non-lifecycle>`, `bd update --claim`, `bd reopen` (all
warn/fail). Bare `bd create → open` remains deliberately out of scope (handled by
the store normalizer + upstream `status.default`).

## Open observation (optional future hardening, NOT a blocker)

Fable's #561 review flagged a LOW/theoretical case in `install.sh`: `! grep -q
sentinel` conflates a grep read-error (exit 2) with "no sentinel", so an
UNREADABLE file at `bd` would be relocated onto `bd-real`. Unreachable on the real
path (root reads mode-000 files; a non-root `mv` fails under `set -e` with zero
mutation), and the same shape pre-exists at `install.sh` step 1. Optional fix if
ever desired: gate on `[ -r "$WRAPPER_TARGET" ]` or distinguish grep exit 2.

## Also this session

- Healed 2 fresh ledger drift items (`livespec-uvgi`, `livespec-dev-tooling-74a`,
  both `open → backlog`) → fleet back to 0 status-conformance drift. Confirms the
  continuous-churn model: expect fresh `open`/`in_progress` on any survey; heal on
  demand with `ledger-normalize`.
- beads **#4738** (`status.default`) is now OUT OF DRAFT, all checks green,
  mergeable — waiting purely on the upstream `gastownhall/beads` maintainer.

## Still OPEN (unchanged from SESSION 2 — next-session candidates)

1. **Host install of the guard** (maintainer-gated): `sudo bd-guard/install.sh`,
   observe warn-mode offenders, fix raw-claim callers, then
   `export LIVESPEC_BD_GUARD_MODE=fail`. One-command rollback: `sudo
   bd-guard/rollback.sh` (now actually works).
2. ~~**Fleet gate → auto-heal-loud + rollout**~~ **RESOLVED (SESSION 4).**
   Gate CONVERTED to auto-heal-loud (`livespec-orchestrator-beads-fabro` #566 +
   fix #568, release 0.28.1). Fleet-wide rollout DECLINED — see "## SESSION 4".
3. **beads #4738 review/merge** → then adopt `status.default = backlog` in each
   tenant's `.beads/` config.
4. **Wait for a beads release carrying #4536** → bump the `bd` pin, make the store
   `create_work_item` single-step, retire the two-step + the guard.

---

# SESSION 4 (2026-07-13) — fleet gate → auto-heal-loud; rollout CLOSED

**Read this after SESSION 3.** This session resolved SESSION-2 workstream 2
("Fleet gate → auto-heal-loud + rollout"): the gate was converted, and the
fleet-wide rollout was investigated and DECLINED.

## Landed (all merged, `livespec-orchestrator-beads-fabro`, released 0.28.1)

| What | PR | Notes |
|---|---|---|
| Gate → auto-heal-loud (detect-and-fail → heal-in-place) | #566 | The pre-push `ledger-normalize --gate` now HEALS the two safe transient remaps (`open`→`backlog`, `in_progress`→`active`) in place, PRINTS each write (loud), and blocks ONLY on residual status-conformance drift a remap can't map. Pure-impl change (the pre-push gate is NOT codified in the orchestrator SPECIFICATION; only the unrelated "Dispatch-time baseline conformance gate" is). |
| Fix-forward: 2 review blockers | #568 | Independent Fable review (post-open, because this repo AUTO-MERGES green PRs — #566 merged ~1 min after CI green, before the review finished) found: **B1** a partial heal-write left already-written remaps UNPRINTED (silent DB write — violated the loud guarantee); **B2** the gate RELOADED the live tenant for residual, so a concurrent session's fresh mappable item in the heal window false-blocked the push with a wrong remedy. Fixed: apply+print each remap one at a time; compute residual over the in-memory PROJECTION of the initial snapshot (no reload window), filtered to status-conformance findings. |

Both PRs: TDD Red→Green single commit, full `just check` green (100% cov), live
pre-push gate exercised CLEAN against the orchestrator's real tenant on push.

## Rollout DECLINED (maintainer-declared 2026-07-13) — the reasoning

A terrain map (all fleet tenants) showed "roll out to all tenant repos" buys very
little, because the eligible set and the drift-prone set are disjoint:

- **The two drift-prone repos are architecturally EXCLUDED.** `livespec` core and
  `livespec-dev-tooling` are UPSTREAM of `livespec-orchestrator-beads-fabro` (which
  owns the dispatcher the gate runs). The No-Circular-Dependency directive
  (`.ai/no-circular-dependency.md`) forbids an upstream repo's hook from invoking
  the downstream orchestrator dispatcher. So the gate cannot go where the drift is.
- **The eligible downstream repos don't drift.** The drivers, `livespec-runtime`,
  `livespec-console-beads-fabro`, `livespec-orchestrator-git-jsonl` showed 0
  status-conformance drift in every survey (no raw `bd create`/`--claim` traffic).
- **"Catch drift without a dispatch" is already met fleet-wide** by the local
  `needs-attention-internal` **Signal 5** scan — legitimately, because it reads the
  dispatcher from the sibling clone as LOCAL maintainer tooling (not a committed CI
  coupling), so it covers even the excluded upstream repos — plus on-demand
  `ledger-normalize`. Prevention across all repos is the bd-guard wrapper
  (host-install pending) + upstream `status.default`.

So the auto-heal-loud gate is kept ORCHESTRATOR-LOCAL (self-hosted, no cross-repo
dependency). No template change, no per-repo justfile/lefthook edits, no
installed-plugin dispatcher-resolution mechanism — all avoided.

## Operational note — auto-merge on green is intended, and fix-forward is the flow

Every fleet impl-plugin repo's `.github/workflows/auto-enable-merge.yml` rebase-
auto-merges any non-draft, un-`do-not-merge` PR the moment CI goes green (via
`app/livespec-pr-bot`). Per `.ai/agent-disciplines.md` §"Auto-enable-merge opt-out
for review-before-merge dispatches", this is DELIBERATE, load-bearing autonomy that
keeps the release train + factory unattended, and it is NEVER to be disabled to
obtain a review gate. So fix-forward IS the intended model ("test in production"):
this session's #566 auto-merged on green and shipped B1/B2 in 0.28.0, and #568
corrected them in 0.28.1 — the flow working as designed, not a miss. Pre-merge
review is the EXCEPTION, reserved for a PR you specifically must review before it
merges (e.g. a factory-repair PR the broken factory can't carry itself); for those,
open the PR as a DRAFT or apply the `do-not-merge` label — a normal open PR does not
hold the merge.

## SESSION 5 (2026-07-13) — next action is a maintainer confirmation prompt

This session corrected the handoff/agent-discipline failure mode that treated
"maintainer-gated" as "blocked / nothing to do." The repo-level rule now says a
maintainer-gated action is the next actionable step that requires explicit
confirmation, not a dead end.

## NEXT ACTION — recommend BD guard install in warn mode

Ask the maintainer to confirm this action before executing it:

```bash
sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/install.sh
```

Plain-language blast radius: this is a host-wide change to the `bd` executable.
The installer moves the real `/usr/local/bin/bd` to `/usr/local/bin/bd-real` and
installs the guard wrapper at `/usr/local/bin/bd`. Default mode is warn, so the
guard prints warnings for non-lifecycle `bd update --status <bad-status>`,
`bd update --claim`, and `bd reopen`; it should not block commands unless
`LIVESPEC_BD_GUARD_MODE=fail` is set.

Rollback command if the host change misbehaves:

```bash
sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/rollback.sh
```

Do NOT close this track as blocked merely because the install is
maintainer-gated. The correct next session response is a recommended
confirmation prompt: install in warn mode now, inspect first, or defer.

## Still OPEN on this track

1. Host install of the BD guard in warn mode (maintainer confirmation required;
   this is the immediate next action).
2. beads #4738 (`status.default`) review/merge → then fleet `.beads/` adoption.
3. Wait for a beads release carrying #4536 → bump pin, single-step store, retire
   the two-step + the guard.

## SESSION 6 (2026-07-13) — BD guard INSTALLED in warn mode + verified live

**Read this after SESSION 5.** SESSION 5's designated NEXT ACTION — the
maintainer-gated BD guard host install — was CONFIRMED by the maintainer and
EXECUTED this session. The guard is now installed in warn mode and verified
end-to-end. The track's reactive layer remains green; the only still-open items
are external/upstream (beads #4738, #4536 release).

## Landed this session

| What | Where | State |
|---|---|---|
| BD guard host install (warn mode) | host `/usr/local/bin/bd` | ✅ DONE + live-verified |

**What was done.** `sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/install.sh`
ran cleanly: it relocated the real `bd` (v1.0.5, 135 MB ELF) to
`/usr/local/bin/bd-real` and installed the 10 KB guard shell wrapper at
`/usr/local/bin/bd` (sentinel `bd-guard-wrapper-sentinel` present, verified).
Default mode is warn (`LIVESPEC_BD_GUARD_MODE` unset); `LIVESPEC_BD_PATH` stays
unset so BOTH raw and store callers fall back to `/usr/local/bin/bd` = the guard.

**Live verification (all passed).**
- Passthrough: `bd --version` → `1.0.5` through the wrapper; `bd list` OK through
  the guard against the real backend.
- Hermetic behavior (installed wrapper, `LIVESPEC_BD_REAL=/bin/echo` stub, zero
  beads side effects): raw `--claim` → WARN + passthrough (exit 0, default warn);
  `--claim` with `MODE=fail` → WARN + BLOCK (exit 3, no passthrough); conformant
  `--status active` → no warn + passthrough; `--status in_progress` → WARN
  (suggests `active`) + passthrough; `bd reopen` → WARN + passthrough; `bd create`
  (out of scope) → no warn + passthrough.
- Real stack intact: re-ran the 8-member survey THROUGH the guarded path → 0
  status-conformance fails on every member (the guard does not break the
  dispatcher).

**Rollback (one command, verified working in SESSION 3):**
`sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/rollback.sh`.

## Current state snapshot (verified 2026-07-13)

| Signal | State |
|---|---|
| Fleet ledger drift | 0 status-conformance fails across all 8 members |
| Master CI (`livespec`, `livespec-orchestrator-beads-fabro`) | both green |
| BD guard on host | INSTALLED (warn mode) |
| beads #4738 (`status.default`) | OPEN but now `CONFLICTING`/`DIRTY` — upstream `main` moved under it; still awaiting the `gastownhall/beads` maintainer |
| beads #4536 (`bd create --status`) | merged, still in NO release; `main` is 230 commits ahead of latest release (v1.1.0, 2026-07-04) |

## Next steps (observation phase)

The guard is in warn mode — it now PRINTS a `livespec bd-guard: …` warning to
stderr whenever any caller runs a raw `bd update --claim` / `--status
<non-lifecycle>` / `bd reopen`. The observation phase: watch those warnings
surface across sessions, fix the raw-claim callers they name, then flip to block
with `export LIVESPEC_BD_GUARD_MODE=fail` (host-wide) once offenders are clean.

## Still OPEN on this track

1. ~~Host install of the BD guard in warn mode~~ **DONE this session** (warn mode,
   verified). Remaining guard step: observe warn-mode offenders, fix raw-claim
   callers, then flip `LIVESPEC_BD_GUARD_MODE=fail`.
2. **beads #4738 (`status.default`)** — developed a merge conflict (upstream moved).
   LEFT AS-IS: upstream-blocked with no `gastownhall/beads` review activity, so
   rebasing now is speculative (would likely re-conflict). Rebase the fork branch
   (`feat/create-default-status-config`, worktree
   `/home/ubuntu/.worktrees/beads/feat-create-default-status-config`) onto
   `gastownhall/beads:main` when the upstream maintainer engages. Then adopt
   `status.default = backlog` in each fleet tenant's `.beads/` config.
3. **beads release carrying #4536** — pure wait (nothing to run). When beads cuts a
   release with #4536: bump the `bd` pin, make the store `create_work_item`
   single-step (`bd create --status`), and retire the store two-step + the guard.

## SESSION 7 (2026-07-13) — bd-guard telemetry: bd.invoke spans to Honeycomb (livespec env) + board + checkpoints

**Read after SESSION 6.** This session answered "why not use Honeycomb
observability?" by BUILDING it: the host bd-guard wrapper now emits one
`bd.invoke` OTel span per call to Honeycomb, giving a live, queryable "many
callers / 0 guard-induced failures" proof surface plus drift detection —
superseding the earlier ad-hoc execsnoop/harness approach. The warn-mode guard
is UNCHANGED in behavior (flip-to-`fail` still gated on the maintainer);
telemetry is additive, default-on, and fail-open.

## The instrument (all landed + live)

```
any bd caller -> /usr/local/bin/bd (guard: enforce warn/fail + capture exit/duration)
   -> curl OTLP/HTTP -> local OTel collector 127.0.0.1:4319
   -> traces/bd_guard pipeline (filter service.name=bd-guard)
   -> livespec Honeycomb env -> bd-guard dataset
```

| Change | Repo / commit | What |
|---|---|---|
| OTLP/HTTP receiver on 127.0.0.1:4319 | `thewoolleyman/otel-collector` `95e57a1` | curl cannot speak gRPC (4317); added an HTTP door so the shell guard can POST spans. |
| Guard emits `bd.invoke` per call | `livespec-orchestrator-beads-fabro` PR #580 (`e30ada0`) | Default-on (`LIVESPEC_BD_GUARD_OTLP=off` disables), fail-open, runs bd in the FOREGROUND to capture exit+duration (TTY/signals preserved), fires a detached `setsid` OTLP span via `bd-guard-emit.py`. |
| Route bd.invoke -> livespec env | `thewoolleyman/otel-collector` `f741249` | Two filter processors split the otlp trace stream by service.name: bd-guard -> new `traces/bd_guard` pipeline -> livespec env (its own ingest key); everything else -> agent-activity. |

Host: `sudo bd-guard/install.sh` reinstalled the telemetry guard + laid down
`/usr/local/bin/bd-guard-emit.py`. Passthrough intact (`bd --version` -> 1.0.5).
Rollback unchanged (`sudo bd-guard/rollback.sh`).

## Proof captured (live, first 24h window)

69 `bd.invoke` spans from 4 distinct caller processes — `python3` (39, the
factory dispatcher + store), `op` (23, the 1Password env-wrapper path), `zsh`
(4), `bash` (3). Outcome: 68/69 `exit 0`; the ONLY non-zero is the 1 intentional
guarded bogus-id probe (`update`, exit 1, `guard.warned=true`). Real factory work
(`create`, `config`, `list`, `update`, `close`, `dep`, `note`) all passed through
cleanly. Latency P50 327ms / P95 1187ms. This IS the "many callers, 0
guard-induced failures" evidence; it accumulates as real traffic runs.

## Board + checkpoints (Honeycomb, livespec env)

- **Board** `bd-guard — host bd telemetry`:
  https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/j2MHvDsuWry
  (volume; calls-by-caller; outcome exit_code x guard.warned x subcommand; raw
  non-conformant ops; latency — filters: caller / subcommand / guard.warned /
  exit_code).
- **Trigger** `bd-guard telemetry stalled (no bd.invoke in 1h)` (`VrKJu9hrgr`,
  `COUNT < 1` over 60m) — the DATA-RECEIVED checkpoint: fires if the pipeline
  stops delivering spans.
- **Trigger** `bd-guard: raw non-conformant bd op detected` (`nak9miYrs14`,
  `guard.warned=true COUNT > 0` over 60m) — fires when a raw
  `--claim`/`reopen`/non-lifecycle-`--status` op passes through (the drift
  source). Both notify the two team emails.

## Secret handling

The livespec ingest key (`HONEYCOMB_INGEST_KEY_LIVESPEC`) was added to the
collector's gitignored, mode-600 `.env` (value never echoed; consistent with the
agent-activity key already there); only `config.yaml` + `.env.example` are
committed. This couples the collector to that key (it will not start without it)
— documented in `.env.example`.

## Also this session

Healed fresh livespec drift: `ledger-normalize` remapped 4 `open` -> `backlog`
(`9z8h.1, 2ua9, nj7d, vuy3`); livespec ledger-check back to 0 status-conformance
drift. (Continuous-churn model: the set had turned over from the SESSION-6 six.)

## Known limitation (minor, non-blocking)

`bd-guard-emit.py` derives `bd.subcommand` as the first non-flag argv token, so
`bd -C <dir> <cmd>` mis-attributes the `-C` PATH as the subcommand (a few board
rows show `bd.subcommand=/data/projects/...`). Cosmetic; the full argv is in
`bd.argv` and the real op in `bd.caller.cmd`. Fixable by skipping
`-C`/`--directory` + its value in the derivation.

## Still OPEN on this track

1. Flip guard to `fail` — GATED on the maintainer, now data-driven: watch the
   board / the raw-op trigger until raw callers are enumerated + fixed, then
   `export LIVESPEC_BD_GUARD_MODE=fail`.
2. beads #4738 (`status.default`) upstream review/merge -> fleet `.beads/`
   adoption. (Developed a merge conflict; left for the gastownhall maintainer.)
3. beads release carrying #4536 -> bump pin, single-step store, retire the
   two-step + eventually the guard.

## SESSION 8 (2026-07-13, WRAP) — RESUME POINT: bd-guard fail-mode readiness monitor

**Read this FIRST to resume, then SESSION 7 for instrument details.** Everything in
SESSION 7 (the bd-guard -> Honeycomb telemetry instrument, board, checkpoint
triggers) is LIVE and merged. The ONLY active work is the hourly readiness monitor
that decides when it is safe to flip the guard to `fail` mode. NEVER auto-flip — the
cutover is maintainer-gated.

## State at wrap (2026-07-13 ~21:40 UTC)

bd-guard telemetry is flowing to Honeycomb (livespec env, `bd-guard` dataset).
Fail-mode readiness snapshot:
- Volume: 161 `bd.invoke` in ~2.5h (~1,550/24h projected) — clears the >=500/24h bar.
- Callers: 4 distinct `bd.caller.comm` (`python3` factory/store, `op` 1Password
  wrapper, `zsh`, `bash`) — clears >=3.
- Raw ops (`guard.warned=true`) in last 12h: 1 — a LEFTOVER TEST probe
  (`zzz-route-probe --claim`), not a real caller. No real raw op has occurred.
- Guard-induced failures: 0. (One benign `exit 141` = SIGPIPE on a piped `bd show` —
  a genuine bd result, identical with or without the guard.)
- **VERDICT: NOT READY** — gated only on TIME: need ~21.5h more telemetry (>=24h
  bar), and the 12h raw-op window must go clean (the test probe ages out ~10h after
  ~19:40 UTC; a REAL raw op resets it until that caller is fixed).

## READINESS CRITERION (recommend cutover only when ALL hold)

(a) >=24h telemetry AND >=500 `bd.invoke`/24h; (b) >=3 distinct `bd.caller.comm`;
(c) `guard.warned=true` COUNT == 0 over the last 12h; (d) no unexpected
`guard.warned=false` non-zero exits attributable to the guard (SIGPIPE 141 on a
piped `bd show`, or `show` on a missing id, are benign — not guard-induced).

## NEXT ACTION for the resuming session — RE-ARM the hourly readiness loop

The SESSION-7/8 hourly cron was session-only and was STOPPED at wrap. Re-arm it
verbatim (paste this whole line):

    /loop 1h Assess bd-guard fail-mode readiness from Honeycomb and report (do NOT flip to fail — maintainer-gated). Query the Honeycomb `livespec` env, `bd-guard` dataset via honeycomb MCP run_query: (1) total bd.invoke COUNT over 24h + telemetry age; (2) distinct bd.caller.comm over 24h + top callers; (3) guard.warned=true COUNT over 1h/6h/12h by guard.op + bd.caller.cmd; (4) exit_code!=0 with guard.warned=false over 24h (SIGPIPE-141 on piped `bd show` and show-missing-id are benign). READY only when ALL: (a) >=24h AND >=500 calls/24h; (b) >=3 callers; (c) guard.warned==0 over 12h; (d) no guard-induced nonzero. Print the 4 numbers + verdict; if NOT READY say what is missing; if READY recommend `export LIVESPEC_BD_GUARD_MODE=fail` (do NOT run it); if guard.warned>0 name the caller (bd.caller.cmd + guard.op). Board: https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/j2MHvDsuWry

When the loop reports READY, present it to the maintainer and recommend they run
`export LIVESPEC_BD_GUARD_MODE=fail` host-wide. They decide — NEVER auto-flip.
Whole-guard rollback (if ever needed):
`sudo /data/projects/livespec-orchestrator-beads-fabro/bd-guard/rollback.sh`.

## Resume sanity checks (verify the instrument is still live)

    grep -c LIVESPEC_BD_GUARD_OTLP /usr/local/bin/bd           # 2 = telemetry guard installed
    systemctl is-active otel-collector; ss -ltn | grep 4319     # collector + HTTP door up
    bd --version                                                # passthrough intact -> 1.0.5

Honeycomb board (livespec env):
https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/j2MHvDsuWry
Checkpoint triggers: `VrKJu9hrgr` (telemetry-stalled), `nak9miYrs14` (raw-op detected).

## Still OPEN (unchanged from SESSION 7)

1. Flip guard to `fail` — gated on maintainer + the readiness monitor above.
2. beads #4738 (`status.default`) upstream review/merge -> fleet `.beads/` adoption.
3. beads release carrying #4536 -> bump pin, single-step store, retire two-step + guard.
