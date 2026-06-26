# Follow-up: fleet-wide doctor-static enforcement + reference-discipline sweep (livespec-6jfq)

**Goal.** Make the doctor-static reference-discipline + out-of-band invariants
enforced in EVERY livespec-governed repo, and clear the pre-existing
violations. Today they run only in core.

## Source of truth = the beads ledger, NOT this file

Start by reading the epic + its children (status lives in beads, never here):

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd show livespec-6jfq
/data/projects/1password-env-wrapper/with-livespec-env.sh bd list --parent livespec-6jfq
```

(`bd` needs the livespec env wrapper for the tenant password — see CLAUDE.md
"Beads runtime prerequisites".) Read 6jfq's comments: they carry the corrected
plan. The earlier "depends on livespec-zodb" note is VOID — zodb (make the
out-of-band check read-only) was rejected and closed.

## Background

e58y authored two doctor-static checks — `doctor-no-cross-spec-reference` and
`doctor-no-spec-section-citation-in-code` (PR #620) — alongside the existing
`doctor-out-of-band-edits`. These run only in core's CI (`check-doctor-static`).
The SIX governed siblings run ZERO doctor-static checks, so each carries
unenforced reference-discipline violations and undetected spec drift:

- livespec-console-beads-fabro
- livespec-driver-claude
- livespec-driver-codex
- livespec-orchestrator-beads-fabro
- livespec-orchestrator-git-jsonl
- livespec-runtime

Confirmed examples (verify the other four with `git show`, NOT by running tools
against primaries):

- orchestrator-beads-fabro: SPECIFICATION/README.md:6 cites
  §"Implementation plugin ecosystem" (cross-repo, un-allowlisted);
  scripts/.../__init__.py:1 has a §-citation in its docstring.
- driver-claude: SPECIFICATION/contracts.md:26 cites §"Plugin distribution"
  (cross-repo); hooks/no_shadow_ledger.py:2 has a §-citation in its docstring.

## Per-sibling approach (one child per repo, in that repo's beads tenant)

1. **Sweep SPECIFICATION/*.md cross-repo `§"…"` citations** — convert to a
   file-level reference, OR add an `external_references` allowlist entry in
   `.livespec.jsonc` (per core constraints.md §"Reference discipline" /
   §"Allowlist mechanism"; core's own `.livespec.jsonc` block is the shape).
2. **Sweep in-code/docstring `§"…"` citations** to file-level references
   (core's e58y sweep removed ~385 of these).
3. **Heal any pre-existing out-of-band drift FIRST** — running the out-of-band
   check produces a `history/v(N+1)/` backfill and fails; commit that backfill
   to heal (driver-claude's was already healed in besm.6 B4).
4. **Wire `check-doctor-static` into the sibling's `just check` aggregate + CI
   matrix** (always-wired, per the enforcement-suite discipline). core's
   `check-doctor-static` recipe is the reference pattern.

Use `/livespec:doctor` as the cross-repo consistency check after each sweep.

## Load-bearing facts / gotchas

- **`doctor-out-of-band-edits` ALWAYS writes on detection — intended; do NOT
  re-propose making it opt-in** (livespec-zodb filed that, rejected/closed). It
  is a self-healing gate: it writes only when the active spec has drifted from
  history (discipline already broken), and the write IS the heal, committed
  along the track. In a clean flow it never fires.
- **NEVER point a tool (doctor_static.py, etc.) at a PRIMARY checkout** — the
  out-of-band write is orphaned there (commits refused). To inspect any
  checkout you're not actively working in, read canonical state with
  `git -C <clone> show origin/master:<path>`. Do all work in worktrees.
- If any sweep changes a `## ` heading, co-edit `tests/heading-coverage.json`
  in the same revise (core's revise co-edit discipline).

## Discipline

Worktree → PR → rebase-merge per repo; `mise exec -- git …`; never
`--no-verify`. Drive as ONE epic (livespec-6jfq) with per-repo children +
cross-repo `depends_on` links; don't defer pieces to "another session." Keep
git in hand for governed-spec work (no auto-merging sub-agents). End on master
in every touched repo (refresh primary to origin/master, remove worktrees).

## Done when

Every governed sibling runs `check-doctor-static` in `just check` + CI and is
clean (violations fixed or allowlisted), and each sibling's out-of-band state
is reconciled. Then close livespec-6jfq + its children, and delete this file.
