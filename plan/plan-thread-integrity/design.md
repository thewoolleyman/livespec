# plan-thread durability — design

**Bottom line.** A plan handoff written to disk is not saved. On 2026-07-19 a
handoff carrying 153 unversioned lines sat dirty in the primary checkout, one
`git checkout` from being lost, and every mechanism that could have noticed it
either did not cover `plan/`, ~~or did not run at the moment that mattered~~
**did not run at the moment that mattered, or ran at exactly that moment and
returned silent by construction** (corrected 2026-07-19 — see §"A `Stop` hook
already ships, already ran, and encodes the root cause"). The root cause is that
**"persisted to disk" was mistaken for "durable"** — by the session that wrote
it, by the gates that scanned right past it, and, it turns out, by a shipped
hook at a nameable line. This document proposes the mechanism that closes that
gap and is explicit about which parts prevent the failure and which parts merely
detect it.

## How to read the evidence labels

Claims below are labeled by how they were obtained. A **MEASURED** claim names
the command that produced it, so a reader can re-run it and disagree. An
**INFERRED** claim is reasoned from evidence rather than observed, and should be
re-verified before anything is built on it. This labeling exists because three
false claims on a single handoff page each cost a later session real time during
the incident that prompted this thread; the labels are what let a reader tell a
checked statement from a plausible one.

All measurements were taken against `thewoolleyman/livespec` at master
`38d86b59` unless another commit is named.

## The failure

**MEASURED** — `git status --short` in `/data/projects/livespec`, then
`git diff --stat plan/overseer-productization/handoff.md`:
`plan/overseer-productization/handoff.md` was modified and uncommitted,
carrying **153 insertions** — the Gate D writeup, the Gate B blocker diagnosis,
three verified daemon findings, and a resolved cross-thread decision. It
survived only because a session noticed it before running `git checkout`.

**MEASURED** — `git log -1 --format=%B 7107be6c | grep session_` returns
`Claude-Session: …session_01XybfmAK5sG5RugLNWcwUxm`, showing that committed work
carries an attributable session identifier. Running any equivalent query for the
dirty handoff returns nothing, because an uncommitted file has no commit to
carry a trailer. **The discipline failure destroyed its own audit trail**: there
is no way to attribute who left it dirty, which is a stronger argument for a
mechanism than any argument from tidiness.

**MEASURED** — `just check-doctor-static`, first run of the session, emitted:

> `"doctor-master-direct-uncommitted-spec-edits", "status": "pass", "message":`
> `"no worktrees on master carry uncommitted spec-tree edits (1 worktree(s) on`
> `master scanned)"`

The invariant that exists to catch exactly this ran, scanned the very worktree
holding the dirty file, and reported clean.

**MEASURED** — `sed -n '153,165p' SPECIFICATION/contracts.md`: the invariant
§"master-direct-uncommitted-spec-edits" is scoped to `<spec-root>/`. A handoff
lives under `plan/`, so it is out of scope by construction, not by accident.

**MEASURED** — `sed -n '518,530p' justfile`: `check-pre-commit-doc-only` runs
seven targets — `check-claude-md-coverage`, `check-heading-coverage`,
`check-vendor-manifest`, `check-no-direct-tool-invocation`,
`check-codex-no-repo-local-adapters`, `check-copier-template-smoke`,
`check-tools` — and `check-doctor-static` is not among them.

**MEASURED** — `sed -n '544,556p' justfile`: the same is true of PUSH.
`check-pre-push` detects a doc-only push (zero `.py` changes against the
upstream) and delegates to that identical seven-target subset; only a push
carrying `.py` changes runs the full aggregate, which is where
`check-doctor-static` lives (`justfile:254`). Confirmed live: pushing the
doc-only branch that rescued the lost handoff printed "All 7 doc-only targets
passed", while pushing a `.py`-carrying branch the same hour printed "All 71
targets passed".

So the session left the file dirty believing a then-red `check-doctor-static`
"prevents committing anything", and that belief was false at BOTH steps — the
gate blocked neither the commit nor the push of doc-only work. Four doc-only
commits and one doc-only push went through while it was still red, which
demonstrates the point rather than merely asserting it.

**MEASURED** — `just --summary | tr ' ' '\n' | grep plan-thread` returns
`check-plan-thread-anchor-declared` and `check-plan-thread-epic-parity`. The
`plan/` tree is already first-class to the check suite, so widening an invariant
to cover it is not a boundary violation.

## A `Stop` hook already ships, already ran, and encodes the root cause

Added 2026-07-19. This section corrects the bottom line above and materially
changes the decisions in §"Constraints that will waste a session if discovered
late". Layer 1 is **not** a greenfield build.

**MEASURED** — `cat /data/projects/livespec-driver-claude/.claude-plugin/hooks/hooks.json`:
the Claude Driver bundle registers **two** hooks on the `Stop` event —
`warn_plan_persistence.py` and `no_shadow_ledger.py`. The Driver is enabled at
project scope in this repo, so both fired at the end of the session that left
the handoff dirty.

**MEASURED** — `warn_plan_persistence.py:155-156`:

```python
if tool_names & PERSISTING_TOOLS:
    return None
```

where `PERSISTING_TOOLS = frozenset({"Write", "Edit", "MultiEdit",
"NotebookEdit"})` (`:47`). The session wrote the handoff, so `Write` was in the
turn's tool set, so the hook returned `None` and emitted nothing.

**The hook whose stated purpose is "completion includes persistence" treats a
single `Write` as proof of durability, and stayed silent for exactly that
reason.** The root-cause sentence of this thread is not just a description of
how a session behaved — it is encoded in shipped code at a nameable line. That
is the strongest available argument that the conflation is structural rather
than a lapse of discipline.

To be precise about blame: the hook is **correct as specified**. Its contract
(`SPECIFICATION/contracts.md` §"Stop plan-persistence WARN") is "planned but did
not write a file," and for that contract the early exit is right. The defect is
that the contract stops at *written*. Do not file this as a Driver bug.

## The home question has a third answer, and it is coupled to the posture

**MEASURED** — per-repo `hooks` keys in each `/data/projects/livespec*/.claude/settings.json`
(eight repos carry the file): **six** repos wire `PreToolUse` + `SessionStart` +
`SubagentStop` — `livespec`, `livespec-dev-tooling`, `livespec-driver-claude`,
`livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`,
`livespec-runtime`; the remaining two (`livespec-console-beads-fabro`,
`livespec-driver-codex`) wire `SessionStart` only. **Zero wire `Stop` locally**
(the Driver bundle supplies `Stop`). So the local-only option recommended below
would fix **one repo of eight** while leaving the same gap open in the other
seven.

> **CORRECTION, 2026-07-19.** This paragraph first shipped saying "seven repos",
> under a MEASURED label. The correct count is **six**; re-running the survey and
> counting the named repos gives six, and `grep -l 'SubagentStop'
> /data/projects/livespec*/.claude/settings.json | wc -l` returns `6`. The error
> was mine, in the same commit that added this section, and it is the third
> unverified claim this document has shipped — after two adversarial review
> rounds caught the first two. The conclusion is unchanged (six of eight still
> dwarfs one of eight), which is exactly why the error survived a re-read: a
> wrong number that does not change the answer is the kind this document's
> labeling convention exists to catch, and the label alone did not catch it.
> Enumerating the members, as the corrected text now does, is what makes the
> count checkable rather than merely asserted.

**MEASURED** — `livespec_dev_tooling/agent_hooks/` in the upstream
`livespec-dev-tooling` repo contains `subagent_stop_guard.py`,
`pretooluse_background_guard.py`, and their shared transcript helper. This repo's
committed `.claude/settings.json` invokes both by module path. This is a **third
home** the constraint below does not consider, and it is neither local-only nor
the Driver bundle.

**MEASURED** — `grep -rln 'agent_hooks\|SubagentStop'
/data/projects/livespec-dev-tooling/SPECIFICATION/` returns nothing.
`livespec-dev-tooling`'s own spec does not govern `agent_hooks` at all;
`subagent_stop_guard` landed under work-item `livespec-dev-tooling-7us.2` (its
docstring, `:5`). **A sibling hook there needs no propose-change cycle in any
repo.**

**MEASURED** — `subagent_stop_guard.py:304` returns `2`, blocking the turn-end
and feeding its reason back to the agent. The fleet has therefore **already
adopted the interruptive posture**, and already solved the trap risk that
motivates the surface-only recommendation below: `_MAX_BLOCKS_PER_SESSION = 3`
(`:84`) with a per-session counter file, plus fail-open on every error path
including a bare-`Exception` boundary (`:311`).

### The coupling

The design below treats "where does the hook live" and "what posture does it
take" as two independent open decisions. **They are not independent.**

| Home | Posture available | Spec cycle |
|---|---|---|
| Driver bundle | WARN-only **by contract** — both `Stop` bullets say the hook "MUST NOT block the stop," and `contracts.md:242` makes a posture change a propose-change cycle | Yes |
| `livespec_dev_tooling.agent_hooks` | Free; interruptive already precedented and shipped | No |
| livespec-core-local | Free, but covers 1 repo of 8 | No |

Choosing the home chooses the posture. Settle them as one decision.

### Why warn-only cannot achieve this thread's goal

**INFERRED**, from the Stop-hook protocol as used by the two existing hooks: a
WARN-only Stop hook emits a `systemMessage` and **allows the stop to proceed**.
The session then ends. Nothing commits the file. The warning lands in a
transcript that, by the shape of this incident, no one reads until the next
session — by which point the mechanism is recovery (layer 3), not prevention.

Only the blocking posture returns control to the agent while it can still act:
exit `2` blocks the stop and feeds stderr back, the agent commits, the next stop
succeeds. **A warn-only layer 1 would ship a mechanism structurally incapable of
producing the outcome this thread exists to produce** — and would repeat, in a
new place, the same error as calling a `warn` check enforcement.

This disposes of the "start surface-only and escalate if insufficient"
recommendation below: surface-only is not a weaker version of the fix, it is a
different layer (an earlier-firing detector). It is worth having, but it is not
layer 1.

## Prevention versus detection — the distinction this design turns on

The obvious fix is to widen the existing invariant to cover `plan/`. That is
worth doing, but on its own it does not prevent the failure, and saying
otherwise would repeat the error this thread exists to correct.

**MEASURED** — `sed -n '105p;161p' SPECIFICATION/contracts.md`: the check fires
`warn`, and a `warn` finding yields wrapper exit 0. It is also cited by name at
line 105 as the canonical example of the `warn` status.

So a widened check reports; it does not block. And it only runs when someone
invokes `just check` or doctor. **INFERRED**, from the shape of the incident:
the session that leaves a handoff dirty is the session that has already ended,
so any mechanism running at the *start* of the next session is recovery, not
prevention — by then an arbitrary number of `git checkout` invocations could
have destroyed the file.

The moment of prevention is **session end**: the last point at which the
authoring session can still commit what it wrote. That is where the primary
mechanism belongs.

## Proposed mechanism

Three layers, named honestly by what each actually does:

1. **Prevention — a session-end (Stop) check.** When a session is ending and a
   `plan/**/handoff.md` is dirty in a default-branch worktree, surface it while
   the authoring session can still act. This is the only layer positioned to
   prevent the incident rather than report it afterwards.

   **Its posture is an OPEN DECISION, and the word "prevention" is only earned
   under one of the answers.** A surface-only warning at Stop is
   detection-at-session-end: better than the other two layers, because it fires
   while the authoring session still exists, but a session can still end through
   it. Prevention in the strict sense requires the check to be interruptive —
   to hold the session until the handoff is committed or the condition is
   explicitly waived. Decide this before building, and do not let the layer keep
   the "prevention" label if the surface-only variant is chosen. ~~Recommend
   starting surface-only and escalating only if it proves insufficient, since an
   interruptive Stop hook that misfires can trap a session, which is a worse
   failure than the one being fixed.~~

   **SUPERSEDED 2026-07-19 — now recommend interruptive.** Two measurements
   overturned this. First, surface-only cannot produce the outcome: a WARN-only
   Stop hook lets the session end, so nothing commits the file. Second, the trap
   risk it was hedging against is already solved in-fleet — `subagent_stop_guard`
   blocks with exit `2` and caps blocks at three per session with fail-open on
   every error path. The hedge was reasonable before those were known; it is not
   a live objection now. See §"Why warn-only cannot achieve this thread's goal".
2. **Detection — widen the existing invariant to cover `plan/`.** This makes the
   condition visible to `just check` ~~, to CI,~~ and to every other session
   working in the affected checkout (**CORRECTED 2026-07-19: not CI** — the
   check enumerates only worktrees of the checkout it runs in, so a fresh CI
   clone cannot carry another host's uncommitted state), rather
   than only to the one that caused it. Severity stays `warn`: a dirty handoff
   should not block unrelated work, and the existing rationale (the violating
   work is not yet pushed, so the warning gives time to recover) still holds.
   This layer is detection, not enforcement, and should not be described as
   enforcement.
3. **Recovery — a session-start surface.** A secondary net that prompts the next
   session to rescue a file the previous one left behind. Lowest value of the
   three, and worth building only if layer 1 proves insufficient.

### Constraints that will waste a session if discovered late

- **Layer 2 is a spec change**, not an implementation tweak. The invariant is
  spec-backed and `contracts.md:105` cites it BY NAME as the canonical `warn`
  example, so it routes through propose-change → independent Fable review →
  revise.
- **Layer 2 carries an unsettled naming decision.** Widening scope makes the
  slug `master-direct-uncommitted-spec-edits` misdescribe its own behavior.
  Recommend renaming, accepting that it touches `contracts.md:105`, the `### `
  heading at `contracts.md:153`, the registry in
  `.claude-plugin/scripts/livespec/doctor/static/__init__.py`, the module
  filename, the `check_id`, and the tests. A name that lies about its scope is
  how the next reader is misled, so the rename is preferred despite costing
  more.
- **Layer 1's cost depends entirely on where the hook lives, and this is not
  settled.** **MEASURED** — `sed -n '242p' SPECIFICATION/contracts.md`: "Adding
  or removing a hook in the Driver bundle, renaming a hook surface, or changing
  a hook's posture (block vs. warn) requires a propose-change cycle against this
  section." So a hook shipped in the Driver bundle needs the full spec cycle,
  while a livespec-core-local hook in `.claude/settings.json` does not. Settle
  this BEFORE estimating layer 1. ~~Recommend local-only first: gate coverage and
  distribution are independent concerns, and the same reasoning already applied
  when the overseer folder was brought inside the gates without changing its
  local-only status.~~

  **SUPERSEDED 2026-07-19** — the framing was a false binary and the
  recommendation followed from it. A third home exists
  (`livespec_dev_tooling.agent_hooks`), it needs no spec cycle in any repo, and
  it is the only one of the three that both reaches all eight repos and permits
  the blocking posture. Local-only is now the WEAKEST option, not the cheapest
  one: it covers one repo of eight, and the "gate coverage and distribution are
  independent" reasoning does not transfer, because a hook that does not load in
  a repo does not gate it. See §"The home question has a third answer, and it is
  coupled to the posture".
- **A red `doctor-static` obstructs the spec lifecycle**, which affects layer 2
  specifically. **MEASURED** — `.claude-plugin/prose/propose-change.md:326` and
  `:380`: the propose-change CLI runs doctor static as BOTH a pre-step and a
  post-step, and `--skip-pre-check` suppresses only the pre-step.
  **INFERRED** — that a red gate therefore obstructs layer 2. Be precise about
  the failure shape rather than repeating the absolute version this document
  carried in an earlier draft: the CLI WRITES the proposed-change file before
  the post-step runs (`propose-change.md:371`), so the proposal lands on disk
  and the CLI then reports exit 3. The seed-recovery path at
  `propose-change.md:400` depends on exactly that shape. So a red gate makes the
  lifecycle report failure and abort its normal flow, not vanish — the artifact
  survives and can be committed, but the operation cannot complete cleanly.

## Sequencing

1. **Layer 1 (session-end check)** — highest prevention value, and free of the
   spec lifecycle if scoped local-only.
2. **Layer 2 (widen the invariant)** — blocked behind the spec lifecycle and the
   slug-rename decision.
3. **Layer 3 (session-start surface)** — build only if layer 1 proves
   insufficient.

## Considered and deliberately not included

Two further defects surfaced in the same incident. Both were drafted as part of
this thread and cut, because "noticed during the same incident" is not shared
architecture — the test this thread failed once already and should not fail
again.

- **Handoff claims not distinguishing measured from inferred.** Three false
  claims propagated on one page, and one of them also reached ledger item
  `livespec-fxxfq6`, so the cost compounded across artifact classes. This does
  not need a plan thread or a mechanism: it is a one-paragraph addition to
  `.ai/agent-disciplines.md` in livespec core saying that load-bearing claims
  cite the command that produced them. A label taxonomy enforced by a checker
  would decay into ritual, because no checker can tell a true claim from a false
  one. **This document applies the convention to itself as the entire case for
  it.**
- **No cross-session visibility of in-flight work.** Two sessions independently
  diagnosed the same blocker and a third's fix sat pushed with no pull request.
  A generalized session-start survey over pull requests, branches, worktrees,
  and ledger items is a PRODUCT SURFACE, not an integrity repair, and it is
  materially broader than the existing precedent it would claim to generalize
  (**MEASURED** — `.claude-plugin/prose/propose-change.md:162`, Step 2.5 covers
  spec branches and spec-touching pull requests only). If it is worth building
  it deserves its own thread and its own justification, not a ride-along here.

## Explicitly out of scope

- The `cross_repo_targets` dual-purpose defect and the CI/local sibling-set
  divergence — ledger item `livespec-fxxfq6` under epic `livespec-n4ptl2`
  (`plan/fleet-pin-propagation/`). Corrections were relayed to that thread on
  2026-07-19.
- The overseer gate work (Gate B, Gate E) — `plan/overseer-productization/`.
- The re-land of the cross-tenant linkage for
  `livespec-console-beads-fabro-tafkuw` — same fleet-pin-propagation thread.
