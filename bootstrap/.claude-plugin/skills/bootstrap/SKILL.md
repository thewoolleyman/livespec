---
name: bootstrap
description: Walk the user through executing the livespec bootstrap plan one sub-step at a time, with confirmation gates at every step and persistent state across sessions. Invoked when the user types /livespec-bootstrap:bootstrap, /bootstrap, asks to "start the bootstrap", "continue the bootstrap", "resume bootstrap", or asks where they are in the bootstrap process.
allowed-tools: Read, Write, Edit, Bash, TaskCreate, TaskUpdate, TaskList, AskUserQuestion
---

# bootstrap

Throwaway skill that drives execution of the livespec bootstrap plan
documented at
`brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`.

The plan is the oracle. This skill is a shallow state-machine driver:
read state, find the current sub-step in the plan, present it, ask for
confirmation, execute, update state, loop. The skill does NOT encode
plan content — every invocation re-reads the plan, so plan corrections
flow into execution naturally.

## Loop on every invocation

### 1. Read state

1. Read `bootstrap/STATUS.md`.
   - If missing: this is the first invocation. Initialize a fresh
     `STATUS.md` with `current_phase: 0`, `current_sub_step: 1`,
     `last_completed_exit_criterion: none`,
     `next_action: "freeze brainstorming/ at current PROPOSAL.md state with the Phase 0 header note"`,
     `last_updated: <UTC>`, `last_commit: <current HEAD sha from git rev-parse HEAD>`.
2. Read `bootstrap/open-issues.md` to count unresolved entries.
3. Read `bootstrap/decisions.md` only if the user asks to review.
4. Open the relevant phase section of
   `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
   based on `current_phase`. Do NOT read the entire plan; load only
   the section for the current phase plus, when at a phase boundary,
   the next phase. Use `Read` with `offset` and `limit` to scope
   the load.

### 2. Present current state

One short paragraph, complete sentences:

- "You're on Phase N. Last completed exit criterion: <X | 'none — not
  started yet'>. Current sub-step: <verbatim text from the plan>.
  Next action: <one-sentence summary>."

If `bootstrap/open-issues.md` has unresolved entries, append:

- "There are M open issues logged from prior sessions; want to review
  them?"

Do not narrate internal deliberation. State results and decisions
directly.

### 3. Gate with AskUserQuestion

Always ask. Five mutually-exclusive options, single-select. Make
"proceed" the first option (Recommended) per the standard convention:

| Option | What it does |
|---|---|
| Proceed with the next sub-step (Recommended) | Execute the next sub-step described in the plan; mark progress in STATUS; loop back to step 1. |
| Pause for now | Update STATUS cleanly with current state; print a one-line "resume by invoking /bootstrap" message; stop. |
| Report an issue first | Open AskUserQuestion to capture issue text + severity; append to `bootstrap/open-issues.md`; loop back to step 2. |
| Record a decision first | Open AskUserQuestion to capture decision text + rationale; append to `bootstrap/decisions.md`; loop back to step 2. |
| Something else | Open-text input; act on free-form direction (e.g., "show me the open issues", "back up to the prior sub-step", "run the exit-criterion check without advancing", "skip to phase N", etc.). |

Never auto-proceed. The "proceed" branch is gated by the user's
explicit selection in this question — never by inference from prior
context.

### 4. Execute the sub-step

Only when the user selects "proceed":

1. Use the appropriate tool for the sub-step:
   - File creation / edits: `Write` or `Edit`. For substantial new
     content, show the user the content via a brief preview before
     writing.
   - Shell commands: `Bash`. Show the command before invoking. If
     it's destructive (rm, git reset, git push --force, branch -D),
     gate with AskUserQuestion before running.
   - In-session work tracking: `TaskCreate` / `TaskUpdate`.
2. After successful execution:
   - Update `bootstrap/STATUS.md`: increment `current_sub_step` (or
     advance `current_phase` only via the phase-boundary flow in
     step 5 below); update `last_updated` with the current UTC
     timestamp; update `last_commit` with the current HEAD sha if
     a commit landed.
   - Loop back to step 1.

### 5. At phase exit

When the next sub-step would advance past the last sub-step of the
current phase, do NOT auto-advance. Phase boundaries always require
explicit user confirmation:

1. Run the phase's exit-criterion check verbatim from the plan. This
   is typically a `just <target>` invocation or a manual file-existence
   check. Capture the output.
2. Show the result to the user: pass / fail and any relevant output.
3. Gate with AskUserQuestion: "Phase N exit criterion shows
   <pass | fail>. What now?" — options:
   - Advance to Phase N+1 (Recommended, only if pass)
   - Hold here (do not advance; allow more work in this phase)
   - Re-run the check
   - Report the failure as an issue (routes to step 3 of the main
     loop, "report an issue")
4. On advance: update STATUS to `current_phase: N+1`, `current_sub_step: 1`,
   `last_completed_exit_criterion: phase N`. Commit STATUS change
   with message `phase-N: complete`. Then loop back to step 1.

### 6. At Phase 10 exit

After Phase 10's exit criterion passes and the `v1.0.0` tag lands:

1. AskUserQuestion: "Bootstrap complete. What should happen to
   `bootstrap/`?" — options:
   - Archive to `brainstorming/bootstrap-archive/` (Recommended)
   - Delete entirely
   - Leave in place
2. On archive: `git mv bootstrap brainstorming/bootstrap-archive`;
   commit `bootstrap: archive scaffolding after v1.0.0`.
3. On delete: `git rm -r bootstrap`; commit
   `bootstrap: remove scaffolding after v1.0.0`.
4. Either way, print a final "bootstrap complete" message and stop.

## State file formats

The skill is the only writer for these files. Never ask the user to
hand-edit them.

### bootstrap/STATUS.md (rewritten on every update)

```markdown
# Bootstrap status

**Current phase:** N
**Current sub-step:** <verbatim text from plan>
**Last completed exit criterion:** <phase X | none — not started yet>
**Next action:** <one sentence>
**Last updated:** <UTC ISO 8601>
**Last commit:** <git HEAD sha or "none">
```

### bootstrap/open-issues.md (append-only)

Each new entry is appended; never rewrite or delete existing entries
without explicit user direction. Severity is one of: `blocking`,
`non-blocking-pre-phase-6`, `non-blocking-post-phase-6`. Disposition
is one of: `halt-and-revise-brainstorming`, `defer-to-spec-propose-change`,
`resolved-in-session`.

```markdown
## <UTC ISO 8601> — phase N — <severity> — <disposition>

<description, 1-3 sentences>
```

### bootstrap/decisions.md (append-only)

Captures judgment calls the executor made during phase work that
weren't pre-decided in the plan. Same append-only discipline.

```markdown
## <UTC ISO 8601> — phase N sub-step M

**Decision:** <one line>

**Rationale:** <one paragraph>
```

## Constraints

- The plan is the oracle. Never deviate from its phase content. If
  you discover the plan is wrong, route through option 3 (report an
  issue) — do NOT modify the plan ad-hoc during execution. Plan
  corrections during execution either halt-and-revise (high cost) or
  defer-to-post-phase-6-spec-propose-change (low cost), per the
  Plan §8 guidance.
- Never skip phases. Sub-step ordering within a phase is the plan's
  authority.
- Never run destructive git commands (`push --force`, `reset --hard`,
  `branch -D`, `commit --amend`) without explicit user confirmation
  via AskUserQuestion.
- Never advance a phase without the user explicitly confirming via
  step 5's gate.
- This skill is throwaway. It lives at
  `bootstrap/.claude-plugin/skills/bootstrap/` and is removed or
  archived at Phase 10 exit. Do not reference it from anything
  outside `bootstrap/` (the production livespec plugin under
  `.claude-plugin/` does not depend on this skill).
- Per the plan's session-handoff design: every invocation can pick
  up cleanly from STATUS.md without prior conversation context. Do
  not assume anything beyond what STATUS.md, the plan, and the two
  log files contain.
