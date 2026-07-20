# Handoff-durability — the plan

**Status**: DRAFT, under review. **Ledger anchor**: epic `livespec-nr5h`
(livespec CORE tenant). **Authored** 2026-07-19; **cut back to scope**
2026-07-19 after a maintainer challenge.

Read [`design.md`](./design.md) for the evidence trail and
[`handoff.md`](./handoff.md) for the thread's resume point. This file is
authoritative for what gets built.

---

## Start with the actual risk

**No plan file has ever been lost.** There is one recorded incident, and it was
a near-miss that was caught.

**MEASURED** — `plan/overseer-productization/handoff.md`, the §"This handoff was
rescued" note:

> "This handoff was **rescued** from the primary checkout on 2026-07-19. It had
> been left UNCOMMITTED on disk at `/data/projects/livespec` — 153 unversioned
> lines, one `git checkout` from oblivion — because the session that wrote it
> believed the push blocker 'prevents committing anything'. That belief was
> false at both the commit AND the push step."

Two facts in that passage govern this entire plan:

1. **The file was rescued.** Zero bytes lost, then or since. A search of the
   `plan/` tree surfaces no other incident and no actual loss.
2. **The cause was a false belief, not a missing guard.** The session did not
   fail to commit because something stopped it. It did not try, because it
   wrongly believed a red gate blocked all commits. Doc-only work is gated by
   neither the commit step (`justfile:518`) nor the push step (`justfile:548`,
   which delegates a zero-`.py` push to the same seven-target subset).

A near-miss with a known, already-corrected cause justifies **detection**, so
the condition is visible if it recurs. It does not justify prevention
machinery.

---

## Scope

Two workstreams. Both are detection or instruction; neither is a new
enforcement mechanism.

### W3 — Widen the uncommitted-edits invariant to `plan/`

`SPECIFICATION/contracts.md` §"master-direct-uncommitted-spec-edits" enumerates
worktrees whose HEAD is the default branch and fires `warn` on uncommitted
modifications, scoped to `<spec-root>/` only. Widen the scope to cover `plan/`.

This is the maintainer's recorded decision and it is the whole of what the
evidence supports: a dirty plan file on the main branch becomes visible to
`just check`, to CI, and to any other session — **after the fact if necessary**,
which is the stated bar.

Constraints:

- **Spec-backed.** `contracts.md:105` cites this check BY NAME as the canonical
  `warn` example, so it routes propose-change → independent Fable review →
  revise.
- **Severity stays `warn`.** A dirty handoff must not block unrelated work. This
  layer detects; it is not enforcement and must not be described as enforcement.
- **Default-branch worktrees only**, unchanged. That is exactly the "not
  orphaned on the main branch" bar, and widening to feature-branch worktrees is
  explicitly not in scope.
- **The slug would then misdescribe itself.** Renaming touches
  `contracts.md:105`, the `### ` heading at `:153`, the registry in
  `.claude-plugin/scripts/livespec/doctor/static/__init__.py`, the module
  filename, the `check_id`, and the tests. **Open — recommend renaming**, since
  a name that lies about its scope is how the next reader is misled.
- **Check the corrective narration while amending.** `contracts.md:159` mandates
  narration that directs the user to commit into a feature branch *or* "to
  discard the edits if they were unintentional (`git checkout -- <files>`)".
  That text is reasonable for spec files; confirm it reads sensibly once `plan/`
  is in scope, rather than inheriting it unexamined.

### W4 — Say "commit it" in the overseer wrap-up

**MEASURED** — `.claude/skills/overseer/supervisor.py:265-267`, the wrap-up body
step 1: *"Bring your OWN work to a clean, resumable stopping point, and UPDATE
{handoff} to match."* **MEASURED** — `grep -n 'commit' supervisor.py` returns
no hit in that text. The instruction that governs every overseer-managed
wind-down says update and never says commit.

Add the commit instruction to that step. Text-only, one file, no mechanism —
and it targets the exact behavior in the exact incident.

Constraints:

- **Does not violate overseer invariant 1.** That invariant forbids the overseer
  from *opening, writing, or stat-ing* a file under `plan/`
  (`.claude/skills/overseer/AGENTS.md`). Changing text the daemon *pastes*
  touches no file under `plan/`.
- **Keep the escalation gradient.** `_WRAPUP_SUGGEST_HEAD` /
  `_WRAPUP_INSIST_HEAD` sharpen with the band and that gradient is load-bearing
  now that nothing is force-killed.
- **Name the path, do not just say "commit".** The handoff lives in the primary
  checkout, where the structural commit-refuse hook refuses commits, so a bare
  "commit it" sends a low-context session into a refusal. The text must name the
  worktree → commit → push flow, and doc-only commits take the fast
  seven-target subset at both steps.
- `marker-protocol.md` documents the wrap-up contract and must stay in sync.

---

## Considered and cut

Recorded so a later session does not re-derive them. Each was drafted in this
thread and cut for the same reason: **it prevents a loss that has not
happened.**

- **A blocking session-end (`Stop`) hook.** Would stall overseer-managed tracks
  — the hook fires just after a session writes `ready`, and a commit cycle
  keeping the pane busy past `_MARKER_VOID_GRACE` (120s,
  `.claude/skills/overseer/supervisor.py:203`) causes `_void_if_stale`
  (`:1103-1123`) to delete the `ready` declaration and the injection stamp,
  stalling the track. It also hands a careless agent a destructive way to
  satisfy the block (`git checkout -- plan/`). Withdrawn.
  - An earlier draft also claimed exit `2` is ignored in `claude -p`. **That
    claim was unverified and is struck** — it was sourced from a research pass,
    not measured, and it sat under a header reading "Three measurements refute
    it". Anyone reinstating a `Stop`-based mechanism must measure the headless
    behavior first rather than inherit this.
- **A `PreToolUse` guard refusing commands that discard `plan/`.** Two
  independent adversarial reviews measured bypasses at the guard's own parsing
  layer — `cd plan && git checkout -- .` severs at the segment splitter, and
  `sh -c`, `bash -lc`, `python3 -c`, command substitution, `xargs`,
  `find -exec`, and `command git` all pass. The non-git class (`rm`, `mv`,
  `truncate`, redirection, `sed -i`, Write/Edit, `git worktree remove --force`)
  is untouched entirely. Enumerating destroyers is unbounded; a string
  classifier can be an honest tripwire but not a root-cause fix, and this thread
  does not need a tripwire for a loss that has not occurred.
- **Snapshotting `plan/**` content into git objects on every write.** Would make
  the artifact recoverable regardless of destruction path. Correct in principle
  and disproportionate in fact: a durability system for a file class with no
  recorded loss, adding a shadow store whose staleness and pruning then need
  their own rules.
- **A `SessionStart` surface.** Not wrong, and previously chosen alongside the
  check. Cut as redundant once the bar is detection-after-the-fact: W3 already
  makes the condition visible, and a second surface for the same signal earns
  its keep only if W3 proves insufficient in practice.

---

## Sequencing

1. **W4** — one text change, no spec cycle. Immediate.
2. **W3** — propose-change → independent Fable review → revise, carrying the
   slug-rename decision.

---

## Acceptance

- `just check` reports a dirty `plan/` file on a default-branch worktree, at
  `warn` severity, without blocking.
- A clean tree, and a dirty file outside `plan/` and `<spec-root>/`, produce no
  new finding.
- The renamed check (if renamed) is consistent across `contracts.md`, the static
  registry, the module filename, the `check_id`, and the tests, with
  `tests/heading-coverage.json` co-edited for any `## ` heading change.
- The overseer wrap-up text instructs a commit AND names the worktree path; the
  escalation gradient is intact; `marker-protocol.md` matches.
- **Nothing in this plan blocks a commit, a session end, or a tool call.**

---

## Review question

This plan was cut back from four workstreams to two after a maintainer
challenge: *is this something that actually happened, that a plan file got
deleted?* It had not. Reviewers should test the cut in both directions —
**is W3 + W4 adequate for the actual risk, and is it still overdesigned for a
single rescued near-miss with a known and already-corrected cause?**
