# Kickoff brief — L0 foundation track (livespec-runtime)

You are the **L0 foundation track** of the fleet-wide work-item-lifecycle
epic (the design is locked; you implement the shared core every other track
vendors). You work **only in `/data/projects/livespec-runtime`**. This brief
is cold-startable — read the chain below, then execute. The fleet anchor epic
is **`livespec-35s3zo`** (livespec core tenant).

## Read first (cross-repo, already on disk)

1. `/data/projects/livespec/plan/work-item-state-machine/research/04-slice-plan.md`
   — the execution structure. Your slice is the **"L0 — livespec-runtime"**
   section; also read **"The reframe"** and **"Execution model"**.
2. `/data/projects/livespec/plan/work-item-state-machine/research/02-design.md`
   — the design of record (§2 states, §3 `lane_of`, §5 `rank`, §6 schema).
3. `/data/projects/livespec/plan/work-item-state-machine/research/03-decision-log.md`
   — authoritative decisions 1–46.
4. This repo's own `SPECIFICATION/contracts.md` (the `### livespec_runtime.work_items.*`
   headings) and `livespec_runtime/work_items/{types,reduce,store}.py`.

## Your slice (L0 — the critical path the orchestrators vendor)

1. **Spec (propose-change → `livespec-runtime/SPECIFICATION/contracts.md`):**
   - `### livespec_runtime.work_items.types`: `status` → the 7-state enum
     (`backlog · pending-approval · ready · active · acceptance · blocked ·
     done`); **add** `rank: str` (required, non-null — no default); **drop**
     `priority: int`; **add** `admission_policy` / `acceptance_policy` /
     `blocked_reason` (`| None`, optional-on-read); the `active ⟹ assignee`
     invariant.
   - **new** `### livespec_runtime.work_items.lifecycle` — `lane_of(*, item,
     index, manifest) -> Lane` + `Lane`/`LaneName`/`BlockedReason`;
     `is_item_ready` (= `lane_of(...).name == "ready"`); `ready_sort_key`
     (keyed on `rank`); the dependency determination moved in as a **pure
     predicate with injected status-lookup callables** (no `runtime → beads`
     back-edge — decision 42).
   - **new** `### livespec_runtime.work_items.rank` — the `rank.py` wrapper
     API (`key_between` / `n_keys_between`), the ported module, and the shared
     bottom-sentinel constant.
   - **Fix the drift:** `contracts.md:131` claims the record schema is
     "codified upstream in `livespec/SPECIFICATION/contracts.md`" — but CORE
     hosts no such schema. The home is THIS repo's own `### …work_items.types`.
     Correct the cross-reference (decision 44).
   - Co-edit this repo's `tests/heading-coverage.json` for every `## `/`### `
     heading you add/change.
2. **Code (this repo):** PORT the CC0-1.0 `httpie/fractional-indexing-python`
   module verbatim to `livespec_runtime/work_items/_fractional_indexing.py`
   (attribution header) + a thin `rank.py` wrapper + a `NOTICES` entry;
   net-new `lifecycle.py` (relocate `is_item_ready`/`ready_sort_key` from the
   beads-fabro orchestrator's `commands/_cross_repo.py` with DI; `lane_of` is
   net-new); the `types.py` schema edits; the shared bottom-sentinel constant;
   paired tests mirroring the source tree.
3. **Cut a `livespec-runtime` release** — the artifact L1a/L1b vendor. (A
   `feat:` push triggers release-please.)

## How (the plan operation + the gates)

- Run `/livespec-orchestrator-beads-fabro:plan` to **create** a thread with
  slug `work-item-state-machine` and **anchor a runtime-tenant epic** for the
  L0 slice, **prose-linked** (a description reference, NOT a typed
  cross-tenant `depends_on`, which would dangle) to `livespec-35s3zo`.
- **Draft** the propose-change payload + your code-slice breakdown, then
  **SURFACE both to the maintainer** for `revise` (spec ratification) and
  `groom` (the slice cut) — those are **maintainer-owned**. Do NOT auto-ratify
  the spec or auto-merge code past those gates.

## Discipline (non-negotiable)

- Every change via **worktree → PR → rebase-merge**; `mise exec -- git …`;
  **never `--no-verify`**; halt and report on any hook failure.
- Product `.py` follows **this repo's red-green-replay TDD ritual**.
- Operate **only in worktrees you create**; never touch another track's
  worktree/branch.
- Secrets probe-only; no human-scale time framings.

## Report

When your thread + epic + drafts are ready (or at ~50% context), refresh your
own thread's handoff and report back. **Start now.**
