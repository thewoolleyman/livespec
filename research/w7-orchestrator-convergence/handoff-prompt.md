# W7 orchestrator convergence — COMPLETE (2026-06-20)

**W7 (`livespec-zkmn`) is DONE and CLOSED.** All steps landed; all
work-items closed; every family repo is clean on `master` with green CI.
This file is now a completion record, not an active handoff. The next
phase is the orchestrator rename wave (`livespec-4moata.4`), which is now
unblocked — but it is a FRESH-SESSION task; do NOT start it as a
continuation of W7. Its kickoff prompt is `tmp/orchestrator-rename-kickoff-prompt.md`.

## What landed

### Step 2 — golden-master acceptance (pre-existing)
Done before this session (`livespec-1oe9`, `livespec-b8od`, `livespec-ei4i`,
`livespec-zkmn.1.2`).

### Step 3 — memo kill (pre-existing)
Symmetric retirement of the memo surface across all four repos
(`livespec-gjn4`, `livespec-zkmn.1.3`, `livespec-d4j3`, `livespec-kfiz`);
`block-auto-memory` redirect retargeted `capture-memo` → `capture-work-item`.

### Step 4 — shared `Store` extraction (this session)
Design decision (user-confirmed): **Lift + conformance Protocol** — lift the
genuinely-duplicated WorkItem model + the canonical pure reducer into
`livespec-runtime`, plus a `WorkItemStore` `typing.Protocol` as a checked
conformance contract; each consumer ships a thin store facade; backend I/O
stays per-impl. Comments were NOT lifted (beads-only). No spec-schema change
(the 16-key schema is unchanged; the extraction only relocates the Python
definition).

- **`livespec-4jsi`** (CLOSED) — `livespec-runtime` PR #52 merged; new
  `livespec_runtime.work_items.{types,reduce,store}` surface; dogfooded spec →
  `SPECIFICATION/history/v006`; **released `v0.4.0`**.
- **`livespec-6a4n`** (CLOSED) — `livespec-impl-beads` PR #104 merged
  (`e031e6d`): re-exports the shared model, imports the canonical reducer,
  `BeadsWorkItemStore` facade; comments + backend I/O stay local. `supersedes`
  now additively emitted as `null` (no break).
- **`livespec-5g4i`** (CLOSED) — `livespec-impl-git-jsonl` PR #95 merged
  (`f19d932`): re-exports the model it donated, `JsonlWorkItemStore` facade;
  JSONL I/O + validators stay local.

Cross-repo pin fan-out was done manually with the canonical
`dev-tooling/vendor_update.py` (run from each consumer worktree), because the
family's automated release→bump-pin machinery errors in the consumers — see
the gap follow-up below.

### Step 5 — container real-work substrate (this session)
- **`livespec-pe9u`** (CLOSED) — `livespec-impl-beads` PR #105 merged
  (`873c970`): new `orchestrator-image/real-work-dispatch.sh` + `just
  w7-real-work-dispatch`. The orchestrator container is now the real-work
  substrate: NO host-checkout bind-mount; it fresh-`git clone`s impl-beads
  (dispatcher code + `.fabro/workflows/` graph) AND the dispatch target
  in-container; regenerates the target's gitignored `.beads/metadata.json`
  (server-stable `project_id`); the only host coupling left is explicit `-e`
  secret provisioning; byte-count-only secret hygiene preserved. The riskiest
  mechanics were live-validated in-container; two `bd init` production bugs
  (embedded-mode shadowing; auto-commit breaking post-merge `git pull`) were
  found and fixed. The full dispatch-and-merge leg remains operator-triggered
  (non-blocking live tier) by design — operator follow-up:
  `with-livespec-env.sh -- just w7-real-work-dispatch -- --target-repo <name> --item <id> --run`.

### Close-out
- `livespec-zkmn.1` (convergence) and `livespec-zkmn` (W7 epic) CLOSED.
- The stale-open W6 dependency `livespec-dw1t` was also CLOSED — it was a
  missed close from the user-declared 2026-06-15 cutover (all its deliverables
  were done or relocated to `4moata.4`; `a8bb` Layer-3 retirement already
  CLOSED). It was the only blocker on `zkmn`.

## Open follow-up filed this session

- **`livespec-9ixg`** (P2, OPEN) — wire a `vendor-update` recipe + script into
  the impl consumers so the family's cross-repo auto-bump re-vendoring works.
  Today `dev-tooling/vendor_update.py` + the `just vendor-update` recipe exist
  ONLY in livespec core (not the consumers, not the copier template), so a
  sibling release's auto-bump errors at the re-vendor step and leaves consumers
  un-bumped. Durable fix (fix the gate, not the bypass): relocate
  `vendor_update.py` into the installed `livespec_dev_tooling` package + add the
  recipe to `templates/impl-plugin/justfile.jinja` + both consumer justfiles.

## Next phase (do NOT start mid-session)

`livespec-4moata.4` — the orchestrator repo rename wave (drop `impl-` →
`orchestrator-`: `impl-beads` → `orchestrator-beads-fabro`,
`impl-git-jsonl` → `orchestrator-git-jsonl`; core repo `livespec` keeps its
name). Now unblocked (its only dependency `zkmn` is closed). Kickoff:
`tmp/orchestrator-rename-kickoff-prompt.md`.
