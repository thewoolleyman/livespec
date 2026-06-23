# Factory-build kickoff: bd-ib-ogh2ls — harden the memory-write guard + retire the Claude-only memory store

You are driving the build of work-item **`bd-ib-ogh2ls`** (type: bug), filed in the
orchestrator beads ledger (`livespec-orchestrator-beads-fabro`, prefix `bd-ib`).
**Target repo for code changes: livespec CORE (`/data/projects/livespec`).**
Read the full work-item first: from the orchestrator repo,
`/data/projects/1password-env-wrapper/with-livespec-env.sh bash -c 'bd show bd-ib-ogh2ls'`.

It is **needs-regroom** (two distinct dones). **Groom it into slices before building**
(`/livespec-orchestrator-beads-fabro:groom bd-ib-ogh2ls`, or just track the two
slices below).

## Why this exists (the bug)
The memory-write guard is bypassable. The Write/Edit tool is intercepted (a
plugin-bundled PreToolUse hook redirects memory writes to capture-work-item), but
the project's ONLY Bash PreToolUse hook —
`/data/projects/livespec/.claude/hooks/livespec_footgun_guard.py` (matcher `Bash`)
— blocks only `--no-verify` / `core.bare=true` / `LEFTHOOK=0`, early-returns for
non-Bash tools (`if data.get("tool_name","") != "Bash": return`), and FAILS OPEN.
So a memory write via `cat >`/`tee`/`cp`/`sed -i`/heredoc into the memory dir slips
through. (Observed live: an agent blocked on the Write tool re-ran it via `cat >>`
and it succeeded — that is the hole.)

## Slice A — harden the guard (small, mechanical, factory-safe)
- Extend `livespec_footgun_guard.py` (or add a dedicated guard) so a write to the
  Claude memory dir `~/.claude/projects/-data-projects-livespec/memory/` via Bash
  (`>`/`>>`/`tee`/`cp`/`mv`/`dd`/`sed -i`/heredoc) is DENIED with an actionable
  message. **Fail-closed for memory writes** (the git-footgun checks may fail open;
  a memory-write block must deny on detection).
- Add hermetic tests for the deny path (the repo's hook tests live under
  `tests/` — mirror them). This is product `.py`, so use the **red-green-replay
  ritual** (Red: test staged alone, made to fail via a stub; Green: amend with the
  impl; one commit with TDD-Red/TDD-Green trailers). `mise exec -- just check`.
- This slice is a clean livespec-core worktree -> PR -> merge and is factory-safe:
  it can be dispatched through the Dispatcher OR hand-driven.

## Slice B — retire the Claude-only memory store into AGENTS.md (judgment-heavy; HAS HOST-ONLY parts)
The store `~/.claude/projects/-data-projects-livespec/memory/` is **98 topic files +
MEMORY.md**, Claude-only and invisible to Codex. Migrate to **harness-neutral
instructions**: **`AGENTS.md`** in livespec core is the single source of truth —
`.claude/CLAUDE.md` is a **symlink** to it and Codex reads `AGENTS.md` natively, so
one edit serves both agents.

For EACH memory, decide:
- **MIGRATE** durable, generally-applicable guidance -> fold into `AGENTS.md` as a
  concise instruction, merged/de-duplicated with what's already there.
- **REJECT** stale / one-off / session-specific / already-encoded-in-code-or-spec /
  `FIXED`/`COMPLETED` markers / dated cycles -> drop with a one-line rationale.
  Expect a HIGH reject rate; many memories are explicitly obsolete.

**END STATE:** the memory store is EMPTY (no topic files; MEMORY.md emptied/removed),
and every retained instruction lives in `AGENTS.md`.

**Host vs repo split (critical):**
- The reading of the 98 host memory files (to decide reject/migrate) and the final
  deletion of the store are **HOST operations** — a Fabro sandbox cannot reach
  `~/.claude/`. **You (the driving session) do these directly on the host.**
- The `AGENTS.md` additions are a livespec-core **worktree -> PR -> merge**.
- Sequence: do the host-side triage + draft the AGENTS.md additions, land the
  AGENTS.md PR, then (after merge) empty the host memory store.
- This slice is judgment-heavy over 98 files; chunk it (e.g. by memory `type:` —
  feedback / project / user / reference) if one pass is too large.

## Mechanics (livespec family)
- Repo: code changes land in **/data/projects/livespec** (core). Mutation protocol:
  `mise exec -- git -C /data/projects/livespec worktree add -b <branch> <wt> master`;
  `mise trust <wt>/.mise.toml`; `mise exec -- git ...` for all commits/pushes; NEVER
  `--no-verify`; product `.py` uses red-green-replay; config/docs use `chore(...)`;
  end commit bodies with the Co-Authored-By line. After merge: pull --ff-only,
  worktree remove, branch -D, prune.
- `just check` is the full gate (lint, pyright strict, tests, 100% coverage).
- Ledger ops via the orchestrator package under `with-livespec-env.sh` (the bd CLI
  alone omits labels/DoR). Close ogh2ls (or its groomed slices) with
  resolution=completed only when acceptance is met.
- NOTE: do NOT "test" the new guard by actually writing to the memory dir from an
  unguarded path — assert via the hook's unit tests, not by performing a real write.

## Acceptance (from the work-item)
1. The guard DENIES a Claude-memory-dir write via Bash (cat/tee/redirect/sed -i),
   not only via Write/Edit, with an actionable message; covered by a test.
2. `~/.claude/projects/-data-projects-livespec/memory/` has no topic files and
   MEMORY.md is empty/removed.
3. Every retained memory's guidance is present in `AGENTS.md`; rejected memories
   are listed with one-line rationale in the PR description.

## First moves
1. `bd show bd-ib-ogh2ls` (read it in full); groom into Slice A + Slice B.
2. Build Slice A (guard + tests) via core worktree -> PR -> merge.
3. Build Slice B: host-side triage of the 98 memories -> AGENTS.md PR -> empty the
   store. List reject/migrate decisions in the PR.
4. Verify acceptance; close the slices (resolution=completed).
