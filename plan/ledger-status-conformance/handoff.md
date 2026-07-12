# Ledger status-conformance cleanup + beads create-status adoption — plan handoff (livespec core)

> **Status: DRIVING (2026-07-12 session).** Scope 1 remediation is DONE (fleet
> green, 0 status-conformance fails across all 8 members). The plan was reshaped
> after investigation into a **holistic detect + auto-fix + upstream-prevent**
> design — see "## Driven session progress" below for the current authoritative
> state, corrected findings, and dispatched work. The sections below the progress
> log are the ORIGINAL seed framing (kept for context; superseded where the
> progress log says so).
>
> _Original seed note:_ spun off 2026-07-12 from the `autonomous-mode` track
> (during an attempt to factory-dispatch a `livespec-dev-tooling` work-item). Does
> NOT block autonomous-mode.

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
