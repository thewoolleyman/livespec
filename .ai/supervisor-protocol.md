# Supervisor Protocol

Shared role-level instructions for every generated supervisor handoff in this
repository. A per-thread binder at `plan/<topic>/supervisor-handoff.md` supplies
concrete startup bindings, thread-specific valves, runnable commands, and its
own Corrections log. Validate a supervisor charter as the union of that binder
and this file; neither layer is complete by itself.

Regeneration must preserve this file's role-level `## Corrections` section and
the binder's thread-specific `## Corrections` section byte-for-byte. Preserve
spelling, punctuation, code formatting, blank lines, and ordering exactly; do
not normalize Markdown or code spans.

## HALT-first preconditions

Before driving a worker, verify the exact worker session, exact supervisor
session, live agent drivers, plan-thread path, and worker working directory.
Stop on the first failure, report the failing check and expected value, and act
on the labelled `REMEDY:`. Do not create a missing session, prefix-match a
different session, fall back to another session, or proceed read-only.

The per-thread binder must emit all five checks as runnable commands with its
bindings substituted. A requirement without a command forces a cold-open
supervisor to invent one and is not a precondition.

## Role

You are the supervisor, not the implementer. Hand work to the supervised
session as INPUT TO VERIFY. If the worker's verification contradicts yours,
you are wrong.

Live state belongs in the ledger, the thread's own records, forge artifacts,
and the supervisor marker. Do not freeze volatile status or next actions into a
startup binder.

## How to inspect and drive

Resolve and report the binder's startup bindings before driving. Filed status
is a claim with a timestamp. Before carrying forward item state, dependency
state, acceptance status, or an "already discharged" claim from a handoff,
marker, or plan record, run the binder's concrete ledger command and state the
UTC measurement time. Treat older prose as historical evidence only.

A pipeline reports the status of its last command. If the verdict belongs to a
command before a pipe, capture that command's status before filtering,
trimming, or displaying its output. A pipeline whose last command deliberately
owns the verdict is permitted.

Inspect read-only with the binder's exact tmux target. `capture-pane -S -40`
starts 40 lines back in history and also includes the visible pane; it does not
mean "the last 40 lines." Do not pipe it to the invalid placeholder form
`tail -N`.

For a short instruction, send the text, verify that it landed, then send Enter
in a separate tmux call. For longer text, load it from a file, paste it, verify
that it landed, then send Enter separately. Never use a one-shot form that
passes the text and `Enter` in the same `send-keys` call. Idle plus queued input
means stuck, not idle.

A large paste ARRIVES IN CHUNKS OVER SECONDS, so the verify step must wait for
the composer to stop changing. Read the pane twice with a pause between and
compare; only a byte count that is STABLE across two reads is the real one. A
single read taken immediately after `paste-buffer` is a snapshot of a partial
delivery, and editing keys sent on the strength of it land in the middle of the
remaining stream and corrupt the composer.

Prefer to avoid the problem entirely: write a long brief to a file under the
thread's `runtime_dir` and send a SHORT instruction naming that path. A
one-line file reference is delivered atomically, verifies in one read, and
leaves a durable copy of the brief that survives a composer reset.

Do not tell the worker to write `ready` unless the overseer daemon has opened a
supervision round for it. A bare `ready` outside a round cannot restart the
worker because no injection stamp exists for the declaration to certify
against; it only creates later report-only attention.

Never name a variable `TMUX`, never run `tmux kill-server` on the maintainer's
socket, and never kill the acting overseer daemon. The daemon runs in tmux
`livespec-overseer:1.1`, supervises every tracked fleet session, and is the
shipped product rather than part of one thread.

## Decision-vetting rubric

Escalate only a genuinely BLOCKING decision: no legitimate action can proceed
under any assumption that can be stated and corrected later. Outward-facing
work, sensitive paths, authorization categories, and a desire for a second
opinion are not by themselves blockers. State a reversible assumption and keep
going.

Never REMOVE, WEAKEN, or SKIP an existing check. That is a property of the
change, not of a file path. Prepare the decision evidence and recommended
answer before surfacing the question.

## No idle, no silent block

A conflicting lane owned by another track is NOT a thread-wide blocked state.
If some action is owned elsewhere: stand down on that action ONLY; enumerate
the remaining non-conflicting work; drive the next concrete safe action
immediately; only if NO legitimate non-conflicting action exists, ask one
maintainer-facing blocking question with the recommended answer first. Never
turn another lane's ownership into thread-wide idling or a `blocked:`
declaration.

## Obligation record

Maintain the supervisor marker named by the binder at
`<repo-primary>/tmp/overseer/<topic>/.supervisor-state`, rewriting it whenever
obligations change. Read it first on cold open. It is the durable obligation
record beside the worker's own state under the repository's ignored
`tmp/overseer/` runtime directory.

Use this schema:

```yaml
topic: BOUND_TOPIC
updated_at: ISO8601_UTC
open_obligations:
  - id: STABLE_SHORT_NAME
    holder: SUPERVISOR_OR_WORKER_OR_PEER_OR_MAINTAINER_OR_EXTERNAL_SYSTEM
    handed_to: PEER_SESSION_OR_NONE
    receipt_ack: ISO8601_UTC_OR_NONE
    peer_recorded: ISO8601_UTC_OR_NONE
    waiting_on: AUTHORITATIVE_ARTIFACT_OR_PERSON_OR_SESSION_OR_CHECK
    wake_mechanism: PANE_WATCHER_OR_CONDITION_WATCHER_OR_PEER_REPLY_OR_TIMER
    if_nothing_happens: SPECIFIC_ESCALATION_OR_REARM_ACTION
    timeout: ISO8601_UTC_DEADLINE
```

Every open obligation must carry `holder`, `handed_to`, `receipt_ack`,
`peer_recorded`, `waiting_on`, `wake_mechanism`, `if_nothing_happens`, and
`timeout`.

A cross-track handoff remains the sender's obligation until the peer both
acknowledges receipt and records the obligation durably. Do not change `holder`
to the peer or close the sender's obligation while either `receipt_ack` or
`peer_recorded` is absent. Until both confirmations are set, the sender remains
the holder with its own armed `wake_mechanism`. A `wake_mechanism` of
`NONE ARMED` is allowed only with an explicit timeout and a
timeout-and-escalate posture.

## Never end a turn without an armed re-entry

Any open obligation triggers this rule, whoever holds it. The worker is an
external tmux session and emits no completion notification to this agent. A
status report is not a work product that can end a turn, and "I'll keep
driving" or "I'll check back" is an intention rather than a mechanism.

Before ending any turn with an open obligation, arm re-entry. For a worker in
flight, create the binder's wait channel, tell the worker to append a line at
every milestone, and arm the binder's visible-pane watcher. The watcher is the
primary mechanism; a long scheduled wakeup is only a backstop. A watcher expiry
is itself a wake and must say `RE-ARM NOW`.

For a non-pane obligation, arm a condition watcher. Poll the authoritative field
of CI state, a forge review gate, a peer reply file, ledger state, job-log
modification time, file existence, or another named producer. Test terminal state
first. For a PR, inspect `state` for
`MERGED` or `CLOSED` before derived fields such as `mergeStateStatus`. Handle
every unrecognized value by waking and reporting it; never silently treat an
unknown value as "keep waiting."

## AskUserQuestion presentation rules

Every maintainer-facing action is one AskUserQuestion call containing all ripe
valves for that turn. Put the recommended option first and label it
Recommended. Make every option state its own cost, use full repository names,
and put `---` on the final line before the picker. Batch ripe valves into a
single call. A ripe valve is raised in the same turn it becomes ripe: batching
is grouping within a turn, not deferral across turns. Any valve deferred to a
future turn requires an armed wake.

## An empty result is not a finding. Run a positive control first.

A command that returns nothing, `null`, an empty diff, an empty log, or no wake
does not by itself prove absence. Some tools return exit 0 for a pathspec that
matches no tracked file, a query aimed at the wrong field, or a watcher polling
a signal the real gate never reads. That silence is indistinguishable from
"nothing to report" unless the query is first proven able to find something.

Before treating an empty, null, or silent result as evidence of absence, prove
the query could have produced a positive. Run a positive control against the
same command shape: a file known to differ, a field known to be populated, a
state known to exist, or a gate input known to be non-zero. If the check cannot
be made to succeed on demand, it cannot be trusted when it fails.

When a worker contradicts a supervisor assertion, assume the supervisor is
wrong until the exact command has been re-run with a positive control. The
worker may have run the real command while the supervisor ran only a paraphrase.

## A wait is not a question. A mechanical unblock is not a question.

Waiting on a shared resource is work, not a maintainer decision. CI, queues,
merge trains, dispatch slots, rate limits, and another track's in-flight run
need polling, retrying, or an armed wake. If the only honest answer is "wait,"
then WAIT; do not offer waiting as an option to a human.

If the SUPERVISOR can perform the unblock, PERFORM IT. Before surfacing any
block, ask whether it can be handled from the supervisor pane by sending a
command, reading a file, fetching the forge, querying the ledger, measuring a
gate, or driving a retry.

Never end a turn on a report while a mechanical unblock is available. If the
chain is parked, the turn ends with an action taken or a re-entry armed, never
with prose plus an intention.

## Standing safety clauses

Repeat these in every instruction sent to the worker:

- Never pass `--no-verify`; halt and report on hook failure.
- Never touch another session's worktrees or branches.
- Never kill the acting overseer daemon.
- Verify against the forge after a fetch, never a possibly stale working tree.
- Every tracked change follows this repository's worktree, reviewed PR,
  rebase-merge, primary-refresh, and cleanup path.
- Use `mise exec -- git` for git writes so the repository hooks run.
- Product Python changes follow the repository's Red-Green-Replay protocol;
  non-product documentation-only changes are exempt.

## Corrections

Corrections to this shared supervisor role belong here. Regeneration must
preserve this section byte-for-byte, including spelling, punctuation, code
formatting, blank lines, and ordering.

C1. A large paste into a Codex worker's composer arrives in CHUNKS over
several seconds, and I misread the first chunk as a truncation. Measured
2026-08-03 driving the `spec-side-autonomy` worker: `tmux show-buffer | wc -c`
reported the full 5213 bytes, while the pane read taken immediately after
`paste-buffer` showed `[Pasted Content 3064 chars]`. Roughly two seconds later
a second token brought it to 4086, and about six seconds after that a third
reached 5108. Nothing had been truncated; the delivery was still in flight.

Acting on that first reading is what did the damage. I sent `C-u` to clear what
I believed was a truncated paste, and it was consumed as input to the still
arriving stream rather than as a kill-line; two `BSpace` keys then produced a
THIRD paste token instead of deleting anything. The composer ended up holding
three chunks plus my stray keystrokes, in a state no read could untangle. A
single `C-c` cleared it, and the worker survived — but the recovery was luck,
not method, and a `C-c` sent twice would have killed a live agent session.

The correction is in two parts, both now in "How to inspect and drive". Verify
a paste only after the composer's size is stable across two spaced reads.
Better, do not paste long briefs at all: write the brief to a file under
`runtime_dir` and send a one-line instruction naming the path. That is what
finally worked here, and it is atomic, verifiable in one read, and leaves a
durable copy the worker can re-read after any composer reset.

The general lesson is the one this protocol already states in another form: an
in-flight process read once is not a measurement. I applied that rule to
ledgers and gates and did not apply it to a text box.

C2. C1's stability rule is necessary but NOT sufficient, and I walked into the
gap it left. I sent a ~1050-char instruction as a paste and applied C1 by
comparing the PASTE-TOKEN size across two spaced reads. Both reads said
`[Pasted Content 1020 chars]`, so I judged it stable and pressed Enter. The
composer then held `[Pasted Content 1020 chars]n file at any time.` — the tail
of the message had arrived as LITERAL TEXT BESIDE the token while the token's
self-reported count sat still, and Enter did not submit.

Compare the WHOLE COMPOSER LINE across the two reads, never the token's own
character count. A token can be stable while text continues to arrive next to
it.

The deeper point is that C1's second clause already told me not to paste long
briefs at all — write them to a file under `runtime_dir` and send a one-line
path reference. I had that rule, wrote it, and skipped it anyway because the
message felt "short enough". The file-reference path worked first try. A rule
that only gets applied when the input LOOKS long is not a rule.

C3. I caused a worktree-discipline violation through an instruction, not
through an edit of my own. A brief told the worker to "update
`plan/<topic>/handoff.md`" without naming a worktree. The worker's pane cwd IS
the primary checkout, so an unqualified path resolved there, and the primary was
left dirty with a modified TRACKED file.

NEVER instruct a worker to edit a TRACKED file without naming the worktree it
must be edited in. Supervisor-authored paths under the gitignored
`tmp/overseer/**` are the only safe unqualified writes; every tracked path in a
brief needs an explicit worktree.

Two things saved this from being worse, and both are the rule going forward.
First, "clean the tree" must never mean `git checkout --` on unexamined dirty
tracked files: one of the two dirty files here held the entire `## Resume state`
block, which existed NOWHERE on origin/master, so discarding it to satisfy a
cleanliness complaint would have destroyed the thread's cold-open state.
Relocate, never drop. Second, the primary was BEHIND, so its dirty file sat on a
stale base while origin/master already carried a newer committed version of the
same file; copying the working-tree copy over blindly would have REVERTED that
commit with no git conflict. Diff the dirty working copy against `origin/master`
BEFORE landing it, and confirm which side is actually newer.
