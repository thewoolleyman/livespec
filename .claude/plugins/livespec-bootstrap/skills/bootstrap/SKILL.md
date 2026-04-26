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
5. **Consistency scan (mandatory).** After loading the phase
   section, scan it for any term that appears in:
   (a) `bootstrap/open-issues.md` entries (open or resolved),
   (b) `bootstrap/decisions.md` entries,
   (c) any session-established convention or interpretation from
   earlier turns of the current conversation.
   For each match, assess whether the plan-text is consistent with
   the recorded entry / convention. If ANY inconsistency is found,
   immediately auto-log a `blocking` open-issues entry per the
   §"Plan/PROPOSAL drift is automatically blocking" rule in step 3,
   then route directly to the halt-on-blocking sub-flow (skip the
   main-loop gate of step 3). Do NOT present "Proceed" as an option
   when a known plan/PROPOSAL contradiction exists.

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
| Report an issue first | Capture severity + disposition + description via AskUserQuestion; append to `bootstrap/open-issues.md`. On `blocking` severity, route to the halt-on-blocking sub-flow described below; on non-blocking severity, loop back to step 2. |
| Record a decision first | Open AskUserQuestion to capture decision text + rationale; append to `bootstrap/decisions.md`; loop back to step 2. |
| Something else | Open-text input; act on free-form direction (e.g., "show me the open issues", "back up to the prior sub-step", "run the exit-criterion check without advancing", "skip to phase N", etc.). |

Never auto-proceed. The "proceed" branch is gated by the user's
explicit selection in this question — never by inference from prior
context.

#### "Report an issue first" branch

When the user selects this option (or when step 1's consistency
scan / step 4's cascading-impact scan auto-routes here):

**Plan/PROPOSAL drift is automatically blocking.** Any drift whose
description references text in
`brainstorming/approach-2-nlspec-based/PROPOSAL.md` or in
`brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
is automatically severity `blocking` and disposition
`halt-and-revise-brainstorming`. The executor MUST NOT present
`non-blocking-*` severities or `defer-to-spec-propose-change`
disposition for these entries — skip the severity / disposition
AskUserQuestions and write those fields directly. Rationale: the
plan is throwaway scaffolding deleted at Phase 11; PROPOSAL.md is
frozen at v022. Neither has a post-Phase-6 codification target in
`SPECIFICATION/`. Plan/PROPOSAL inconsistencies have no escape
valve — halt-and-revise is the only resolution path, and the
bootstrap MUST NOT advance until the plan/PROPOSAL is internally
consistent.

**Carve-out: plan-internal text-correction drift.** When the
detected drift is entirely within the plan (PROPOSAL.md is
unchanged) AND consists of stale text references that contradict
an authoritative table or diagram elsewhere in the plan (e.g.,
§8's directory-shape diagram), AND the correction is purely
mechanical (rewriting the stale references to match the
authoritative source, with no decision to make), the executor
MAY fix the references directly in a regular commit instead of
running halt-and-revise. The bootstrap is still gated on a
clean plan, but the resolution path is a direct edit + commit
rather than a vNNN snapshot. Required steps for this carve-out:
(a) confirm PROPOSAL.md has zero matches for the stale terms;
(b) confirm an authoritative diagram/table inside the plan
unambiguously shows the correct text; (c) record a decisions.md
entry naming the stale references, the authoritative source,
and the chosen correction; (d) apply the edits and commit
(commit message starts with `phase-N: align stale plan ...` or
similar). If ANY of (a)-(c) cannot be satisfied — including any
ambiguity about which version is authoritative — fall back to
the standard halt-and-revise walkthrough.

For all other drift kinds:

1. Open AskUserQuestion to capture **severity**:
   - `blocking` — executor cannot satisfy the current phase's exit
     criterion, OR continuing would knowingly produce wrong output.
   - `non-blocking-pre-phase-6` — drift discovered before the seed,
     and the drift is NOT in plan/PROPOSAL text (those are
     auto-blocking per the rule above); executor can carry an
     interpretation forward; codification happens via post-Phase-6
     propose-change against `SPECIFICATION/`.
   - `non-blocking-post-phase-6` — drift discovered after the seed;
     codification can happen immediately via the dogfooded propose-
     change mechanism.
2. Open AskUserQuestion to capture **disposition** (intent):
   `halt-and-revise-brainstorming`, `defer-to-spec-propose-change`,
   or `resolved-in-session`.
3. Capture description text via AskUserQuestion's free-text input.
4. Append the entry to `bootstrap/open-issues.md` with `**Status:**
   open` per the format below.

**On `blocking` severity, do NOT return to the main loop.** Enter
the halt-on-blocking sub-flow:

- Print: "This issue is flagged blocking. The bootstrap will not
  advance until it is resolved."
- AskUserQuestion: "How do you want to proceed?" — options:
  1. **Open the halt-and-revise walkthrough** (Recommended when
     `current_phase < 6` or when a PROPOSAL.md change is needed).
     Routes to the §"Halt-and-revise walkthrough (pre-Phase-6)"
     sub-flow below.
  2. **Open the propose-change walkthrough** (only valid when
     `current_phase >= 6` and the change targets a `SPECIFICATION/`
     tree). Routes to the §"Propose-change walkthrough
     (post-Phase-6)" sub-flow below.
  3. **Downgrade severity** — user reconsiders and decides the
     issue isn't blocking after all. Capture the reconsideration
     rationale to `bootstrap/decisions.md`; mutate the open-issues
     entry's severity field; resume the main loop at step 2.
     **NOT VALID for plan/PROPOSAL drift entries** — those have no
     non-blocking severity by rule. If a plan/PROPOSAL drift entry
     is in error (the contradiction was misread), supersede the
     entry by appending a new entry that points back at it, rather
     than downgrading.
  4. **Pause for now** — clean STATUS update; print resume
     message; stop. The blocking entry remains open and will gate
     advancement until resolved on a later invocation.

**On non-blocking severity**, append the entry and return to step 2
of the main loop. The entry will surface again at phase exit (step
5a's drift-review checkpoint).

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
2. **Cascading-impact scan (mandatory).** If the executed sub-step
   established a convention, decision, interpretation, or any state
   that diverges from the plan's literal text — including any
   open-issues entry just written, any decisions.md entry just
   written, or any change to a working assumption agreed with the
   user — grep both
   `brainstorming/approach-2-nlspec-based/PROPOSAL.md` and
   `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`
   for terms relevant to the established change (the noun, path,
   tool name, file name, or concept at issue). For every match,
   assess whether the plan/PROPOSAL text is consistent with the
   established change. If ANY match is inconsistent, immediately
   auto-log a `blocking` open-issues entry per the §"Plan/PROPOSAL
   drift is automatically blocking" rule in step 3, then route
   directly to the halt-on-blocking sub-flow BEFORE returning to
   step 1. The bootstrap MUST NOT advance past a known
   plan/PROPOSAL contradiction. Skip this scan only when the
   executed sub-step was purely mechanical with no convention or
   interpretation established (e.g., a verbatim file move from the
   plan).
3. After successful execution (and after the cascading-impact scan
   is clean):
   - Update `bootstrap/STATUS.md`: increment `current_sub_step` (or
     advance `current_phase` only via the phase-boundary flow in
     step 5 below); update `last_updated` with the current UTC
     timestamp; update `last_commit` with the current HEAD sha if
     a commit landed.
   - Loop back to step 1.

### 5. At phase exit

When the next sub-step would advance past the last sub-step of the
current phase, do NOT auto-advance. Phase boundaries always require
two gates: drift review FIRST, then exit-criterion check, then
advancement confirmation.

#### 5a. Drift-review checkpoint (new)

Run BEFORE the exit-criterion check.

1. Read `bootstrap/open-issues.md`. Filter to entries whose phase
   header matches the current phase AND whose `Status:` field is
   `open`.
2. If zero unresolved entries: print "No drift logged for Phase N";
   proceed to step 5b.
3. Otherwise: print a summary, grouped by severity:

   ```
   Drift discovered during Phase N (3 unresolved entries):
     blocking: 1
       - <timestamp>: <one-line description>
     non-blocking-pre-phase-6: 2
       - <timestamp>: <one-line description>
       - <timestamp>: <one-line description>
   ```

4. AskUserQuestion: "What now?" — options:
   - **Open the halt-and-revise walkthrough** for blocking entries
     (Recommended when any blocking entries exist; required if any
     remain unresolved after this gate).
   - **Open the propose-change walkthrough** to drain entries
     post-seed (only valid when `current_phase >= 6`).
   - **Resolve a specific entry now** — open AskUserQuestion to
     pick which entry; capture resolution text; mutate that entry's
     `Status:` to `resolved` and append a `**Resolved:** <UTC> —
     <text>` line; loop back to 5a (re-read, re-summarize).
   - **Defer all remaining non-blocking entries to post-Phase-6
     drain** (only valid if zero blocking entries remain;
     mutates each non-blocking entry's disposition to
     `defer-to-spec-propose-change` if not already set).
   - **Carry forward as-is** (only valid if zero blocking entries
     remain AND no remaining entries reference plan or PROPOSAL
     text; plan/PROPOSAL drift can never be carried forward — by
     the §"Plan/PROPOSAL drift is automatically blocking" rule it
     is auto-`blocking` and must be halt-and-revised in this
     session before phase exit; non-plan-non-PROPOSAL entries
     persist; skill warns again at the next phase exit).

5. **Gate condition.** Do NOT proceed to 5b until zero blocking
   entries remain unresolved. If the user pauses or routes to a
   walkthrough that doesn't fully resolve them, the skill remains
   parked at this checkpoint on next invocation.

#### 5b. Exit-criterion check

1. Run the phase's exit-criterion check verbatim from the plan.
   Typically a `just <target>` invocation or a manual file-
   existence check. Capture the output.
2. Show the result to the user: pass / fail and any relevant
   output.

#### 5c. Advance gate

AskUserQuestion: "Phase N exit criterion shows <pass | fail>. What
now?" — options:

- **Advance to Phase N+1** (Recommended, only if pass).
- **Hold here** (do not advance; allow more work in this phase).
- **Re-run the check** (loops back to 5b).
- **Report the failure as a new issue** (routes to step 3's
  "Report an issue first" branch; if user flags it `blocking`,
  the halt-on-blocking sub-flow takes over).

#### 5d. Advance

On advance: update STATUS to `current_phase: N+1`,
`current_sub_step: 1`, `last_completed_exit_criterion: phase N`.
Commit STATUS change with message `phase-N: complete`. Loop back
to step 1.

### 6. At Phase 10 exit

When Phase 10's exit criterion passes and the `v1.0.0` tag lands,
the bootstrap is functionally complete but Phase 11 (cleanup) is
still ahead. Update STATUS to `current_phase: 11`,
`current_sub_step: 1`,
`last_completed_exit_criterion: phase 10`. Print "Phase 10
complete; v1.0.0 tag landed. Phase 11 (cleanup) is next." Loop
back to step 1.

### 7. Phase 11 — Cleanup

Phase 11 is bookkeeping that removes the production-facing
references to the bootstrap scaffolding. Sub-steps:

1. **Remove the bootstrap plugin and its marketplace.** Three
   removals, each gated by AskUserQuestion since these are
   committed files:
   - `rm -r .claude/plugins/livespec-bootstrap` (the plugin
     contents)
   - `rmdir .claude/plugins` (only if empty after the previous
     removal)
   - `rm .claude-plugin/marketplace.json` (the marketplace
     manifest at repo root)

   Do NOT remove `.claude/skills/` (production plugin's symlink),
   `.claude-plugin/plugin.json` (production manifest), or
   `.claude/settings.local.json` (machine-local, gitignored).

   After committing, optionally suggest the user run in Claude
   Code:
   ```
   /plugin uninstall livespec-bootstrap@livespec-marketplace
   ```
   (cleans up the local installed-plugin state; not required for
   the cleanup to be complete, since the marketplace manifest is
   gone).

2. **Remove the repo-root orientation file:** `rm AGENTS.md`. The
   per-directory `AGENTS.md` files inside `bootstrap/` and
   `brainstorming/` stay — they describe directories that
   themselves stay.

3. **Verify isolation.** Run the grep from Plan Phase 11 step 3:

   ```
   grep -rn "bootstrap/\|brainstorming/" \
     .claude-plugin/ dev-tooling/ tests/ SPECIFICATION/ \
     pyproject.toml justfile lefthook.yml .mise.toml \
     .github/ NOTICES.md .vendor.jsonc 2>/dev/null \
     | grep -v _vendor
   ```

   Expected output: empty. If any output: route through the
   "Report an issue first" gate to file a blocking issue; the
   skill's halt-and-revise sub-flow handles the fix before the
   Phase 11 commit lands.

4. **Commit and push.** Suggested message:
   `phase-11: remove bootstrap-skill symlink and root AGENTS.md`.
   Gate the push on AskUserQuestion confirmation.

5. **Update STATUS one last time** with the cleanup commit sha.
   Print the final "bootstrap complete; livespec is now
   self-governing via /livespec:* commands" message and stop.

The next invocation of `/livespec-bootstrap:bootstrap` after
Phase 11 will fail to find the slash command (its symlink is
gone). That is intentional — the production app uses
`/livespec:*` slash commands for its own operations; the
bootstrap scaffolding has finished its job.

## Drift-correction sub-flows

These two sub-flows are entered from step 3's halt-on-blocking
branch or step 5a's drift-review checkpoint. They are NOT invoked
from the main-loop step 3 gate directly.

### Halt-and-revise walkthrough (pre-Phase-6 path)

Drives a formal `vNNN/` revision against PROPOSAL.md, mirroring
the v018 → v022 process. Triggered when blocking drift requires
PROPOSAL or plan-level changes that cannot be deferred.

1. **Determine next vNNN:**
   - `ls brainstorming/approach-2-nlspec-based/history/` and parse
     `vNNN` directory names. Find max NNN; next vNNN = NNN + 1
     (zero-padded to 3 digits).

2. **Choose revision shape** via AskUserQuestion:
   - **Direct overlay (Recommended for narrow fixes)** — author a
     single `critique-fix-v<prev>-revision.md` documenting the
     decisions; matches v022's pattern when changes are small and
     uncontested.
   - **Full critique-and-revise** — author both
     `proposal-critique-v<prev>.md` (the critique input) and
     `proposal-critique-v<prev>-revision.md` (the structured
     revision); matches v018-v021 pattern. Use when the change
     involves multiple architectural decisions that need explicit
     option-picker discussion.

3. **Author revision file(s).** Walk the user through the
   relevant sections via AskUserQuestion:
   - For overlay path: capture each decision (D1, D2, ...) with
     description, rationale, and source-doc impact list. Compose
     into `critique-fix-v<prev>-revision.md` and write it.
   - For full path: walk through the critique-and-revise iteration
     (load relevant PROPOSAL section, identify ambiguities via
     AskUserQuestion picker, accumulate decisions). Author both
     files when the user signals iteration complete.

4. **Apply revision to PROPOSAL.md.** Use Edit operations to
   apply the changes, one decision at a time. Show each Edit's
   old_string / new_string preview before invoking.

5. **Snapshot.** Create `history/vNNN/` directory; copy current
   PROPOSAL.md to `history/vNNN/PROPOSAL.md`; move the revision
   file(s) authored in step 3 into
   `history/vNNN/proposed_changes/`.

6. **Update plan.** Surgical edits to
   `brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`:
   - "Version basis" section: bump version label; add decision
     summary for vNNN.
   - Phase 0 step 1: bump byte-identity check's reference to vNNN.
   - Execution prompt block: bump the "Treat PROPOSAL.md vXXX as
     authoritative" line.
   - Apply any plan-level changes the revision implies (Phase
     edits, work-item-list updates, etc.).

7. **Mark originating issue resolved.** Edit the originating
   `bootstrap/open-issues.md` entry's `Status:` to `resolved`;
   append `**Resolved:** <UTC> — codified in vNNN; see
   history/vNNN/proposed_changes/...` line.

8. **Commit and push.** Show the user the staged diff. Gate with
   AskUserQuestion: "Commit + push the vNNN revision?" — options:
   commit-and-push (Recommended), commit-only, hold (let user
   review more first).
   - On commit-and-push: `git add` the modified files; `git commit
     -m "Revise proposal to vNNN: <one-line summary>"`; `git push`.
   - On commit-only: same `git add` + `git commit`; skip `git push`.
   - On hold: stop the sub-flow; STATUS update; user resumes when
     ready.

9. **Resume.** Update STATUS: refresh `last_updated` and
   `last_commit`. Print "Revision vNNN complete; resuming Phase
   N at sub-step M". Return to main-loop step 1.

### Propose-change walkthrough (post-Phase-6 path)

Drives a dogfooded propose-change/revise cycle against the
seeded `SPECIFICATION/`. Only valid when STATUS shows
`current_phase >= 6`. Triggered when blocking drift can be
codified inside `SPECIFICATION/` rather than requiring a
PROPOSAL revision.

1. **Choose target spec tree** via AskUserQuestion:
   - Main spec: `SPECIFICATION/`
   - `livespec` template sub-spec:
     `SPECIFICATION/templates/livespec/`
   - `minimal` template sub-spec:
     `SPECIFICATION/templates/minimal/`
   - Other (free-text path; verify it's a spec tree)

2. **Author propose-change content.** Walk the user through
   composing the propose-change file:
   - Topic name (must be canonical per the propose-change rules)
   - Front-matter (target spec files, author, intent, etc.)
   - Body (proposal sections per PROPOSAL.md §"Proposed-change
     file format")

3. **Invoke `/livespec:propose-change`.** Use the Skill tool to
   invoke `propose-change` against the chosen spec tree:
   - Pass `--spec-target <chosen path>`
   - Pass the authored propose-change content
   - Confirm the propose-change file lands at
     `<spec-target>/proposed_changes/<topic>.md`

4. **Invoke `/livespec:revise`.** After confirming the
   propose-change is in place:
   - Use the Skill tool to invoke `revise --spec-target <chosen
     path>`
   - Walk the user through the per-proposal accept/reject
     decision via the revise sub-command's normal flow
   - Confirm a new `<spec-target>/history/vNNN/` lands

5. **Mark originating issue resolved.** Edit the originating
   `bootstrap/open-issues.md` entry's `Status:` to `resolved`;
   append `**Resolved:** <UTC> — codified via <spec-target>/
   history/vNNN/<topic>.md` line.

6. **Resume.** Update STATUS: refresh `last_updated` and
   `last_commit` (the propose-change/revise cycle should have
   produced its own commits via the dogfooded mechanism). Print
   "Propose-change cycle complete; resuming Phase N at sub-step
   M". Return to main-loop step 1.

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

### bootstrap/open-issues.md (append-only-with-status-mutation)

New entries are appended. Existing entries' bodies are written
once; only the `Status:` field MAY be mutated in place, and a
`**Resolved:** ...` line MAY be appended on resolution. Never
rewrite or delete entries without explicit user direction.

Severity is one of: `blocking`, `non-blocking-pre-phase-6`,
`non-blocking-post-phase-6`. Disposition (intent) is one of:
`halt-and-revise-brainstorming`, `defer-to-spec-propose-change`,
`resolved-in-session`. Status (lifecycle) is one of: `open`,
`resolved`, `superseded`.

```markdown
## <UTC ISO 8601> — phase N — <severity> — <disposition>

**Status:** open

**Description:** <description, 1-3 sentences>
```

When an entry is resolved (via the halt-and-revise walkthrough,
the propose-change walkthrough, or step 5a's "Resolve a specific
entry now" path), the skill mutates `Status:` to `resolved` and
appends one line:

```markdown
**Resolved:** <UTC ISO 8601> — <one-line resolution summary,
e.g., "codified in v023; see history/v023/...">
```

Filtering "unresolved entries for phase N" at step 5a means:
`phase header == N` AND `Status: open`. Skill scans the file
linearly; no SQL, no schema validator.

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
  you discover the plan or PROPOSAL.md is wrong (literal text
  contradicts an established convention, the current repo state, a
  prior open-issues entry, or a session-established interpretation),
  the only resolution path is halt-and-revise. There is no
  defer-to-post-phase-6-spec-propose-change path for plan/PROPOSAL
  drift: the plan is throwaway scaffolding deleted at Phase 11 and
  PROPOSAL.md is frozen at v022 with no `SPECIFICATION/` analog. The
  bootstrap MUST NOT advance past a known plan/PROPOSAL
  inconsistency. Step 1's consistency scan and step 4's
  cascading-impact scan are the executor's two mandatory detection
  hooks. Do NOT modify the plan ad-hoc — always go through the
  halt-and-revise walkthrough.
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
