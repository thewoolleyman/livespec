# Handoff-durability mechanism — the plan

**Status**: DRAFT, under adversarial review. **Ledger anchor**: epic
`livespec-nr5h` (livespec CORE tenant). **Authored** 2026-07-19.

Read [`design.md`](./design.md) for the evidence and
[`handoff.md`](./handoff.md) for the thread's resume point. This file is the
buildable plan; it supersedes the three-layer sketch in `design.md`
§"Proposed mechanism", and says why.

---

## Maintainer intent — binding on this plan and on every review of it

Stated 2026-07-19. Every workstream below is answerable to all four clauses,
and every adversarial review of this plan MUST test against them:

1. **Fix the root causes** — not the symptom, and not one instance of it.
2. **Rock solid for all normal usage**, by interactive sessions **and
   non-interactive ones**. A mechanism that works in a tmux pane and wedges
   `claude -p` fails this clause.
3. **Best effort to prevent unwanted session kills / loss** — the mechanism
   must not itself destroy work, stall a track, or get a session killed.
4. **Without impairing usage otherwise, EVEN BY CARELESS AGENTS.** An agent
   that does the dumbest available thing in response to the mechanism must not
   end up worse off than with no mechanism at all. This clause is the reason
   W1 exists and the reason the session-end block was dropped.

Clause 4 is the sharpest constraint here, because the obvious mitigation
inverts under it: a mechanism that tells an agent "your handoff is dirty, deal
with it" hands a careless agent a motive to run the one command that destroys
the file.

---

## What this plan does NOT build, and why

`design.md` §"Proposed mechanism" proposed a **blocking session-end (`Stop`)
hook** as layer 1, and a revision on 2026-07-19 escalated the recommendation
from surface-only to interruptive. **That is withdrawn.** Three measurements
refute it, and a fourth finding makes it redundant.

- **It would stall overseer-managed tracks.** The `Stop` hook fires right after
  a session writes `ready`. If the resulting commit cycle keeps the pane busy
  longer than `_MARKER_VOID_GRACE` (120s,
  `.claude/skills/overseer/supervisor.py:203`), `_void_if_stale`
  (`supervisor.py:1103-1123`) deletes the `ready` declaration **and** the
  injection stamp, and the track sits unrestarted until a new wrap-up round
  opens. A handoff commit means worktree → commit → push → PR, which exceeds
  120s comfortably. This violates intent clause 3 directly.
- **It is inert in non-interactive sessions.** In `claude -p`,
  `stop_hook_active` is `false` and exit `2` / `decision: block` are **ignored**
  by the harness. Headless runs cannot be wedged — but they get no protection
  either. Half of intent clause 2 is unreachable by this mechanism.
- **In interactive sessions it is actively dangerous.** There is no documented
  user escape hatch from a repeatedly-blocking `Stop` hook (only the harness's
  8-consecutive-block override). Worse, a careless agent can satisfy the block
  by running `git checkout -- plan/`, which **destroys the file** — the exact
  incident, now caused by its mitigation. This is the clause-4 inversion.
- **It is aimed at the wrong event.** A `respawn-pane -k` restart destroys only
  the process; every file on disk survives it
  (`.claude/skills/overseer/AGENTS.md`, invariant 7). An uncommitted handoff is
  therefore **not** lost when a session ends or restarts. It is lost when a
  destructive git command runs. Guarding session-end guards a moment at which
  nothing is actually destroyed.

That last point reframes the whole thread and produces W1.

---

## The reframe

`design.md` argues the moment of prevention is session end, because "the
session that leaves a handoff dirty is the session that has already ended."
That reasoning holds for *attribution* and does not hold for *destruction*.

**The file is not destroyed by a session ending. It is destroyed by a specific
command.** Until that command runs, the file is still on disk, recoverable by
anyone who looks. This matches the maintainer's independently-recorded
reasoning in `plan/overseer-productization/handoff.md:689-696` — that session
start is "the one moment the damage is still preventable" — which the
plan-thread-integrity thread contradicted without citing.

So the mechanism set is: **guard the destroying command** (W1), **surface the
condition when a session can act on it** (W2), **make it visible to CI and
other sessions** (W3), and **tell sessions to commit while they still have
context** (W4).

---

## W1 — Guard the destroyer (PreToolUse). NEW, and the primary mechanism.

**MEASURED** — `grep -n 'checkout\|restore\|clean\|stash\|reset'
.claude/hooks/livespec_footgun_guard.py`: the fleet's `PreToolUse` footgun
guard refuses `--no-verify`, `LEFTHOOK=0`, `core.bare=true`, and Bash writes
into the auto-memory store. It does **not** refuse any command that discards
uncommitted work. The single `checkout` hit is inside a deny-message string.

Add a refusal class: a git invocation that **discards uncommitted changes**
under `plan/` — `git checkout`/`git restore` with a `plan/` pathspec, `git
clean` reaching `plan/`, `git stash` (which moves the file out of the tree),
and `git reset --hard`. Deny with a message naming the recovery path (commit it
in a worktree, or copy it aside first), never a way to force the discard.

Why this is the primary mechanism, against each intent clause:

- **Clause 1** — it blocks the actual loss event, not a proxy for it.
- **Clause 2** — `PreToolUse` fires in interactive *and* headless runs. It is
  the only proposed mechanism that covers `claude -p` at all.
- **Clause 3** — it cannot stall a track, cannot block a session end, cannot
  interact with the overseer's readiness protocol, and cannot get a session
  killed. It denies one tool call and returns.
- **Clause 4** — it is precisely the careless-agent guard. It removes the
  destructive shortcut rather than relying on the agent not to take it.

Design constraints inherited from the existing guard, which this must not
regress:

- Token/segment based, never substring. `_segments` splits on
  `&&`/`||`/`;`/`|`/newline and strips here-doc bodies; `_strip_leading_noise`
  strips env assignments plus `mise exec --`/`sudo`/`env`; `_git_subcommand`
  resolves the subcommand past git's global options. A `plan/` path mentioned
  in an `echo`, a commit message, a here-doc body, or a `git log --grep` must
  **not** be denied.
- **Fail-open on parse error**, matching the guard's git-footgun posture
  (`_check_segment` returns fail-open on `shlex` failure). The memory-write
  rule's fail-closed posture is the declared exception and this rule should not
  claim it: a guard bug that blocks legitimate `git checkout` across the fleet
  is a worse outcome than a missed discard, because the commit-refuse hook and
  branch protection remain as backstops for the things that matter most.
- Deny payload shape is `hookSpecificOutput.permissionDecision: deny`, exit 0.

**Open — the home question.** Three candidate homes, and they differ in reach
and in cost:

| Home | Reach | Spec cycle |
|---|---|---|
| `.claude/hooks/livespec_footgun_guard.py` (this repo) | `livespec` only | none |
| Claude Driver bundle | every governed repo | see below |
| Codex Driver's footgun guard | Codex runtime | `contracts.md` enumerates that guard's four refusal classes explicitly, so a fifth is arguably a contract amendment |

`SPECIFICATION/contracts.md:242` requires a propose-change cycle for *adding or
removing a hook* in the Driver bundle and for changing a hook's posture, while
"mechanical detection internals ... MAY be tuned Driver-side without a core
spec cycle." A new refusal class in an existing hook sits on that boundary.
**Recommendation**: land in this repo's project-local guard first, where it
needs no cycle and can be exercised; treat fleet propagation as a follow-on
decision once the classifier is proven. Reviewers should challenge this.

---

## W2 — SessionStart surface

The maintainer's recorded choice
(`plan/overseer-productization/handoff.md:689`). At session start, surface any
dirty `plan/**` file in the repo so the incoming session can rescue it. Needs
no spec change — project-local `.claude/settings.json` config — and is the part
that can move first.

Notes carried forward from that thread: it is a **surface**, not a block.
Nothing about session start should be interruptive; the session has just begun
and has full context to act.

Interaction to verify, not assume: the repo already runs a `SessionStart` hook
(`mise exec -- just ensure-plugins`). Adding a second entry must not slow
session start materially or mask the first hook's output.

---

## W3 — Widen the uncommitted-edits invariant to `plan/`

Also the maintainer's recorded choice, and the piece `design.md` already scoped
as layer 2. `SPECIFICATION/contracts.md`
§"master-direct-uncommitted-spec-edits" enumerates worktrees on the default
branch and fires `warn` on uncommitted modifications, scoped to `<spec-root>/`
only. Widen it to cover `plan/`.

Constraints, unchanged from `design.md`:

- **Spec-backed.** `contracts.md:105` cites the check BY NAME as the canonical
  `warn` example, so this routes propose-change → independent Fable review →
  revise.
- **The slug would then misdescribe itself.** Renaming touches
  `contracts.md:105`, the `### ` heading at `:153`, the registry in
  `.claude-plugin/scripts/livespec/doctor/static/__init__.py`, the module
  filename, the `check_id`, and the tests. Recommend renaming; a name that lies
  about its scope is how the next reader is misled. Not yet decided.
- Severity stays `warn`. A dirty handoff must not block unrelated work.
- **This layer detects; it does not enforce.** Do not describe it as
  enforcement. It fires `warn` (wrapper exit 0) and runs only when someone
  invokes `just check` or doctor.

---

## W4 — Say "commit it" in the overseer wrap-up

**MEASURED** — `.claude/skills/overseer/supervisor.py:265-267`, the wrap-up
body step 1: *"Bring your OWN work to a clean, resumable stopping point, and
UPDATE {handoff} to match."* The text tells the session to **update** the
handoff and never to **commit** it — the "persisted is durable" conflation
again, this time in the instruction that governs every overseer-managed
wind-down.

Add the commit instruction to that step. Text-only, one file, no mechanism.

Two constraints:

- **This does not violate overseer invariant 1.** That invariant forbids the
  overseer from *opening, writing, or stat-ing* a file under `plan/`
  (`.claude/skills/overseer/AGENTS.md`). Changing the text the daemon *pastes*
  touches no file under `plan/`.
- **Keep the escalation gradient.** `_WRAPUP_SUGGEST_HEAD` /
  `_WRAPUP_INSIST_HEAD` sharpen with the band, and that gradient is load-bearing
  now that nothing is force-killed. Do not flatten it.
- `marker-protocol.md` documents the wrap-up contract and must stay in sync.

---

## Sequencing

1. **W4** — one text change, no mechanism, no spec cycle. Immediate.
2. **W1** — the primary mechanism; project-local, testable, no spec cycle.
3. **W2** — no spec change; can land in parallel with W1.
4. **W3** — blocked behind the spec lifecycle and the slug-rename decision.

W1 before W2 deliberately: W2 tells a session about a dirty handoff, and W1 is
what makes the careless response to that news non-destructive. Landing W2 first
would create the clause-4 inversion this plan exists to avoid.

---

## Acceptance

- A `git checkout` / `restore` / `clean` / `stash` / `reset --hard` reaching
  `plan/` is denied by the guard, verified **payload-only** — the command
  travels as a JSON string on the hook's stdin and its verdict is read. Never
  execute a discard to see whether it is blocked.
- A `plan/` path appearing as DATA — in an `echo`, a commit message, a here-doc
  body, a `git log --grep` — is **not** denied. False positives are the failure
  mode that impairs usage.
- A legitimate `git checkout` of a non-`plan/` path is unaffected.
- The guard's existing four refusal classes still fire, and its fail-open
  posture on unparseable input is intact.
- Session start surfaces a dirty `plan/**` file, and does not block.
- `just check` reports a dirty `plan/` handoff on a default-branch worktree.
- The overseer wrap-up text instructs a commit, the gradient is intact, and
  `marker-protocol.md` matches.
- **No mechanism in this plan can block a session from ending, stall a track,
  or wedge a non-interactive run.**

---

## Open questions for review

1. **W1's home** — project-local first, or straight to the Driver bundle for
   fleet reach? Does a new refusal class in an existing hook cross
   `contracts.md:242`?
2. **W1's scope** — is `git stash` correctly in scope? It is recoverable, so
   denying it may be over-blocking. Is `reset --hard` in scope when no `plan/`
   pathspec is named, given it discards everything?
3. **W1's posture** — fail-open is recommended above. Is that right for a rule
   whose whole purpose is preventing destruction, when the sibling memory-write
   rule fails closed?
4. **W3's slug rename** — rename, or keep a name that now misdescribes its
   scope?
5. **Coverage honesty** — with the blocking `Stop` hook dropped, is there any
   remaining gap where a handoff is lost that none of W1–W4 covers?
