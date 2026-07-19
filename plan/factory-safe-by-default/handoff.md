# factory-safe-by-default — planning handoff

**Thread summary:** invert livespec's factory doctrine to **factory-safe by
default** — assume any work-item runs in the factory, require a machine-readable
admission-enforced opt-out for a small enumerable host-only residue, widen
factory capability so that residue stays tiny, and give the residue a home as a
distinct needs-attention host-only-action kind. Reshaped **2026-07-17** into a
**two-orthogonal-axes** model (`admission_policy` = permission vs. `factory_safety`
= runnability). **As of 2026-07-18 the model is fully realized in code across the
fleet** — Slices A, B, and C are all merged; only the human accept legs and Slice
D (coordinated under `z2ctra`) remain. See `research/design.md` §"Reshape
(2026-07-17)".

The single resumable entry point: a fresh session executes the next action from
this file via the read-first chain — no chat history required.

## Read-first chain (open these, in order, before acting)

1. **The ledger epic `livespec-nrdk`** (livespec core tenant) — read status AND
   its comments **LIVE from the ledger**; never trust a status copied into this
   file. The 2026-07-18 comments record the full Slice-B/C build-out, the two
   findings (self-refusal + legacy-fallback), and the remaining chain:
   ```bash
   source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-nrdk
   ```
2. **`research/design.md`** §"Reshape (2026-07-17)" — the settled two-axis design.

## Current state (derived from the ledger — read it live)

**Slice A — spec contract. COMPLETE + RATIFIED (2026-07-17).** Two-axis model live
on `livespec-orchestrator-beads-fabro` master (`SPECIFICATION/history/v040/`, PR
#733). Nothing left.

**Slice B — mechanical field + gate. COMPLETE (2026-07-18).** All three sub-slices
merged, in `acceptance` (ai-then-human; human accept legs pending — maintainer's):
- **B1 `livespec-runtime-vkqer3`** — `factory_safety` field on the shared
  `WorkItem`. Shipped in runtime **v0.10.0**.
- **B2 `bd-ib-qcnbbp`** (beads-fabro) — store encode/decode + admission gate reads
  `factory_safety`; **replaced the `is_host_only_item` regex with a field read**
  (`return item.factory_safety is not None`); refusal message fixed; doctor
  invariant updated. PR #755.
- **B3 `bd-gj-7adugd`** (git-jsonl) — store persists `factory_safety` (implementer
  chose *persist*). PR #308, release 0.5.5.

**bd-gj-9sj — git-jsonl janitor fix. COMPLETE (2026-07-18).** P1 bug surfaced by
B3's janitor: `just check` called an untracked `./dev-tooling/branch-protection.sh`
in fresh checkouts. PR #312 ("install worktree pack before branch check"). In
`acceptance`. Unblocks all git-jsonl factory dispatch.

**bd-ib-y2o1 — legacy-fallback retirement. COMPLETE (2026-07-18).** B2's
implementer had kept the old prose regex as a *read-fallback* in the store decode
(`_factory_safety_from_labels_or_legacy`), which mis-flagged any factory-safe item
that merely *named* the marker token as not-factory-safe (bit B2's and C1's first
dispatches). Migration-safety verified (only 1 incidental match, no genuine
dependent). PR #763 removed it — the store now derives `factory_safety` **only**
from the explicit `factory-safety:` label. In `acceptance`.

**Slice C — host-only needs-attention kind. GROOMED + (near) COMPLETE (2026-07-18).**
`bd-ib-i6wfum` regroomed out into three tenants (prose deps, bj9x model):
- **C1 `livespec-runtime-o96`** — added the value to the shared `AttentionKind`.
  Merged (PR #253). NOTE: C1 first shipped the value as `factory-safety`
  (deviating from design/epic "host-only" + colliding with the `factory_safety`
  field); **maintainer-decided to correct to `host-only`**.
- **C1b `livespec-runtime-76j`** — renamed the value `factory-safety` → `host-only`.
  Merged (PR #258). Shipped in runtime **v0.11.0** (release PR #254 merged). So
  `AttentionKind = human-valve|impl|spec|plan|hygiene|internal|host-only`.
- **C2 `bd-ib-ayga`** (beads-fabro) — needs-attention surfaces not-factory-safe
  items + `factory_safety` refusals as `host-only` AttentionItems w/ `shell`
  handoff. Merged (PR #768); beads-fabro pin now v0.11.0. In `acceptance`.
- **C3 `bd-gj-5u8`** (git-jsonl) — same, items only (git-jsonl runs no dispatcher).
  First dispatch (PR #324) hit a merge conflict — the v0.11.0 runtime fan-out bump
  (`3d975f9`) landed on git-jsonl master concurrently, so both bumped the vendored
  files. #324 closed; **re-dispatched on top of the now-stable v0.11.0 master**.
  **CONFIRM its status live** — if merged + `acceptance`, Slice C is complete.

**Slice D — capability-widening (move #3). STAYS under `z2ctra`**, coordinated not
absorbed. Covers per-toolchain target-local workflows, `bd-gj-9sj` (now done), and
the Fabro GitHub-App-token 60-min-TTL candidate. No action from this thread.

## Next actions (in order)

1. **Confirm C3 (`bd-gj-5u8`) merged + in `acceptance`** (re-dispatch was in flight
   at handoff write). If it failed, diagnose (git-jsonl master is stable v0.11.0,
   so a re-dispatch should merge cleanly). Once green, **Slice C is complete and
   the epic's implementation is done.**
2. **Human accept legs (maintainer's).** B1/B2/B3, bd-gj-9sj, bd-ib-y2o1, C1(/C1b),
   C2, C3 are all parked in `acceptance` (ai-then-human), NOT force-accepted. The
   operator triggers `accept:<id>` with live-exercise evidence. B2's live exercise
   = the admission gate refusing a REAL not-factory-safe item; C2/C3's = a
   not-factory-safe item appearing as a `host-only` needs-attention item.
3. **Slice D** stays under `z2ctra` — nothing here.
4. **Optional:** reap the stale git-jsonl janitor worktrees (`janitor-bd-gj-5i1`,
   `-cn4`, `-7adugd`) and the closed C3 branch `feat/bd-gj-5u8` — only when no
   git-jsonl dispatch is active.

## Golden rule + standing constraints

- FILE ripe work + GROOM it; build ripe work factory-side (Dispatcher / `drive
  --action impl:<id>`) under the janitor gate — never hand-code inline.
- Status derived from the ledger, never stored here.
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never
  `--no-verify`; doc-only plan edits use `docs(plan): ...`.
- **Watch out:** a work-item whose title/description names the bare `host-only`
  token USED to be refused at admission by the legacy fallback — that fallback is
  now retired (bd-ib-y2o1), so naming it is safe again.
- **Watch out:** dispatching a slice that bumps a runtime pin can race the release
  fan-out's own bump PR (C3/#324). If master already bumped, re-dispatch on top.
