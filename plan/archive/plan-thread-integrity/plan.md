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

1. **The file was rescued.** Zero bytes lost, then or since. **No plan file has
   ever been deleted or permanently lost.** Two other `plan/`-tree hits mention
   loss and neither is this class: `plan/fleet-pin-propagation/research/recovered/README.md`
   records three sub-agent research reports that never reached their driver
   session and were then RECOVERED from agent transcripts (a report-delivery
   failure, not a file-durability one, and no mechanism here or cut would touch
   it); `plan/fabro-ci-image-factoring/handoff.md` records a host-CPU incident.
   The tmux-kill incidents destroyed processes, not files.
2. **The cause was a false belief, not a missing guard.** The session did not
   fail to commit because something stopped it. It did not try, because it
   wrongly believed a red gate blocked all commits. Doc-only work is not gated
   **by `check-doctor-static`** at either step — not the commit
   (`justfile:518`) and not the push (`justfile:548`, which delegates a
   zero-`.py` push to the same seven-target subset). Both steps do run that
   seven-target subset; it is the doctor check specifically that is absent.

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
evidence supports: a dirty plan file on the main branch becomes visible —
**after the fact if necessary**, which is the stated bar.

**Be exact about the detection surface; an earlier draft was not.** The check
enumerates only worktrees of the checkout it runs in
(`io/_git_worktrees.py`, `git -C <project_root> worktree list --porcelain`),
so it fires on **any full `just check` or doctor run in the affected
checkout** — and **NOT in CI**, whose fresh clone by construction cannot carry
another host's uncommitted state, and **not on doc-only hook runs**, which take
the seven-target subset that excludes this check. Both reviewers flagged the
"visible to CI" claim as structurally false; it is struck here and in
`design.md` and `handoff.md`.

That surface is still exactly the one that failed. In the incident, a local
`check-doctor-static` run reported `pass` while scanning the very worktree
holding the dirty file. W3 converts that false pass into a warn.

Constraints:

- **Spec-backed.** `contracts.md:105` cites this check BY NAME as the canonical
  `warn` example, so it routes propose-change → independent Fable review →
  revise.
- **Severity stays `warn`.** A dirty handoff must not block unrelated work. This
  layer detects; it is not enforcement and must not be described as enforcement.
- **Default-branch worktrees only**, unchanged. That is exactly the "not
  orphaned on the main branch" bar, and widening to feature-branch worktrees is
  explicitly not in scope.
- **Do NOT rename the slug.** An earlier draft recommended renaming
  `master-direct-uncommitted-spec-edits`. **Reversed on review.** The live
  footprint is ~10 files — `contracts.md:105` and the `### ` heading at `:153`,
  the registry in
  `.claude-plugin/scripts/livespec/doctor/static/__init__.py`, the module
  filename, the `check_id`, **four** test files, plus cosmetic mentions in
  `io/git.py` and `tests/heading-coverage.json` — and that is the one place
  this plan still over-spends. A widened check under the old name UNDER-claims
  its scope, which is the safe direction: the incident's mechanism was a reader
  assuming coverage the name never promised, so the name was honest. The
  contract text will state the real scope. Maintainer may overturn; the
  recommendation is to keep the name.
- **Fix the corrective narration — this is an acceptance criterion, not a
  check-in-passing.** `contracts.md:159` mandates narration directing the user
  to commit into a feature branch *or* "to discard the edits if they were
  unintentional (`git checkout -- <files>`)". Once `plan/` is in scope, that
  text prints **against a dirty handoff that may be the only copy** — the
  near-miss was literally "one `git checkout` from oblivion", and a handoff is
  almost never "unintentional edits". Left inherited, the warn finding itself
  becomes the prompt that destroys the file. For `plan/` paths the narration
  MUST lead with commit-into-a-feature-branch and MUST NOT present discard as a
  symmetric option.

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
- **Name the whole path, do not just say "commit" — and include the copy
  step.** The handoff lives in the PRIMARY checkout, where the structural
  commit-refuse hook refuses commits, so a bare "commit it" sends a low-context
  session into a refusal. And a fresh worktree cut from `master` **will not
  contain the dirty edits**, which live in the primary's working tree — so a
  session told only "use a worktree" stalls at "my worktree doesn't have my
  changes." The text must name: create the worktree, **copy the handoff into
  it**, commit, push, PR. Doc-only commits take the fast seven-target subset at
  both steps, so this is quick.
- `marker-protocol.md` documents the wrap-up contract and must stay in sync.

---

## Considered and cut

Recorded so a later session does not re-derive them. The unifying reason is
that each **prevents a loss that has not happened** — but the individual
reasons differ, and the bullets below give each its own, because a flattened
"all cut for one reason" would misrepresent two of them.

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
  independent adversarial reviews found bypasses at the guard's own parsing
  layer, and the mechanism is checkable in the source rather than on their
  say-so: `.claude/hooks/livespec_footgun_guard.py:146-148` splits segments on
  `&&`/`;`/`|`, so `cd plan && git checkout -- .` severs and the discard segment
  carries no `plan` reference; `:195` requires `tokens[0]` to be `git`, so
  `sh -c`, `bash -lc`, `python3 -c`, command substitution, `xargs`,
  `find -exec`, and `command git` all pass through. The non-git class (`rm`,
  `mv`, `truncate`, redirection, `sed -i`, Write/Edit,
  `git worktree remove --force`) is untouched entirely. Enumerating destroyers
  is unbounded; a string classifier can be an honest tripwire but not a
  root-cause fix, and this thread does not need a tripwire for a loss that has
  not occurred.
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
- **The corrective narration for a `plan/` finding leads with
  commit-into-a-feature-branch and does not offer `git checkout -- <files>` as
  a symmetric option.** The finding must never be the thing that destroys the
  file it is reporting.
- The renamed check (if renamed) is consistent across `contracts.md`, the static
  registry, the module filename, the `check_id`, and the tests, with
  `tests/heading-coverage.json` co-edited for any `## ` heading change.
- The overseer wrap-up text instructs a commit AND names the worktree path; the
  escalation gradient is intact; `marker-protocol.md` matches.
- **Nothing in this plan blocks a commit, a session end, or a tool call.**

---

## Review outcome

This plan was cut from four workstreams to two after a maintainer challenge:
*is this something that actually happened, that a plan file got deleted?* It
had not. Two independent adversarial reviewers (Fable and Codex) then judged
the cut in **both** directions — adequate, or still overdesigned — each
required to write the strongest case for cutting further even if they
disagreed with it.

**Both committed to the same verdict: W3 + W4 is correctly proportioned.**

Their strongest case for cutting further, recorded because it is a real
argument and a later session may want to revisit it: the detection already
exists ambiently — the mutation protocol requires `git status` at the primary
before editing, and the rescue happened precisely because a session looked. W3
adds a `warn` finding (wrapper exit 0) that fires only on a full aggregate run
in the affected checkout, for the price of a propose-change cycle and
narration re-work, while W4 is free and removes the conflation from the one
instruction every overseer-managed wind-down actually receives.

**Why that case was rejected:** ambient visibility is exactly the mechanism
that almost failed. The rescue was luck-shaped — one unlooked `git status`
from loss — and the check that exists to formalize that looking reported
`pass` while scanning the very worktree holding the file. W4 alone leaves zero
codified detection, which does not meet the stated bar.

Fixes applied from both reviews: the false "visible to CI" claim struck here
and in `design.md` and `handoff.md`; the overbroad "no other loss" sentence
scoped to plan files with the two unrelated hits named; the doc-only gating
sentence given back its subject; the discard-narration hazard promoted from a
passing note to an acceptance criterion; the slug rename reversed to
do-not-rename; and W4's flow extended to name the copy-into-worktree step.
