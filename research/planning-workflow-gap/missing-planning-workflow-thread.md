# Missing planning workflow thread

Captured from the Open Brain meta-orchestrator session on 2026-06-23.
This is research, not specification text. If any part becomes a rule
for livespec itself, it still needs to move through
`/livespec:propose-change` and `/livespec:revise`.

## Bottom line

Livespec has strong mechanisms for specification change, implementation
work tracking, and implementation execution. The missing piece is a
durable planning thread for work that is more structured than a chat
conversation but not yet ready to become normative spec text or a set of
ripe implementation items.

The interim answer is a simple two-artifact workflow:

- Use `research/<topic>/...md` files to preserve the reasoning,
  options, trade-offs, and open questions.
- Use `prompts/<id-or-topic>-handoff-<track>.md` files for active,
  resumable session instructions once a track is being executed across
  multiple sessions.

This does not replace the beads ledger. The ledger remains the system of
record for implementation work once the work is concrete enough to file.
The research and prompt files fill the gap before and around ledger
items: they preserve context, planning intent, and session continuity.

## Problem observed

The Open Brain session was driven by a handoff prompt that acted as a
meta-orchestrator. It carried an epic-level objective, child work-item
status, constraints, session-start and session-close rituals, and
instructions for when to refresh handoff state. That worked because
Open Brain already has a `prompts/` convention.

Livespec does not yet have an equivalent planning surface. It has:

- spec-side lifecycle commands for normative behavior
  (`seed`, `propose-change`, `critique`, `revise`, `doctor`,
  `prune-history`, `next`, `help`);
- implementation-side orchestrator skills and a beads/Dolt ledger for
  ready work;
- research files for durable but non-normative thinking;
- a Dispatcher for unattended concrete implementation work.

What is missing is the connective tissue for "this is an active planning
thread that should survive context compaction and session boundaries,
but it is not yet a spec change and not yet a clean implementation item."

Without that layer, agents tend to choose one of three imperfect
surfaces:

- leave the thread in chat context, which disappears or compacts;
- prematurely file implementation work-items before the shape is known;
- prematurely push thinking into the specification before it is stable
  enough to be contractual.

## What the Open Brain handoff pattern showed

The Open Brain prompt files were useful because they made a session
resumable without making chat history the only source of truth. The
pattern had several important properties:

- It named a track and tied it to a ledger item or epic.
- It printed live status at session start and close.
- It named the authoritative ledger but did not duplicate it as a
  markdown task list.
- It carried the session's current intent, constraints, and completion
  conditions.
- It made handoff refresh an explicit obligation before context
  exhaustion.
- It allowed implementation to continue autonomously while still
  preserving operator-level decisions and open questions.

That pattern is stronger than a normal research note when active work is
underway, because it tells the next session exactly how to resume. It is
also safer than an ad hoc TODO list because it points back to the
ledger, tests, and specification lifecycle instead of becoming a second
work queue.

## Brainstormed surfaces

### Research files only

Research files are the lowest-friction capture mechanism. They are good
for preserving a conversation, trade-offs, and unsettled ideas.

Pros:

- They already exist in livespec.
- They are versioned, reviewable, and easy to cite.
- They are explicitly non-normative, so they do not bypass the spec
  lifecycle.
- They are suitable for broad thinking that should not become work yet.

Cons:

- They do not naturally encode current status, next action, or resumption
  protocol.
- They can become stale unless an active workflow updates or supersedes
  them.
- They do not give an agent a crisp "start here and do this" entrypoint.

### Prompt files only

Prompt files are useful once work is active and spans sessions.

Pros:

- They provide a concrete entrypoint for the next session.
- They can carry operational instructions, current state, and handoff
  criteria.
- They are well suited to context-window management.

Cons:

- If they contain their own unchecked task lists, they can become a
  shadow ledger.
- They are less appropriate for open-ended exploration that should be
  read as durable research rather than an instruction to execute.
- They need conventions so completed prompts are archived or removed.

### Beads ledger only

The ledger is the right place for concrete work.

Pros:

- It is queryable and status-bearing.
- It supports dependencies and readiness.
- It is already the implementation work source of truth.

Cons:

- It is too concrete for early planning if the work is still a bundle of
  questions.
- It captures "what to do" better than "why the shape was chosen".
- Filing fuzzy planning as implementation work can make `/next` rank
  ambiguous or non-ripe items.

### Spec lifecycle only

The spec lifecycle is the right place for contractual behavior changes.

Pros:

- It is the authoritative mechanism for normative change.
- It preserves an audit trail through proposed changes and revise
  history.
- It prevents research notes from becoming accidental requirements.

Cons:

- It is too heavy for early brainstorming.
- It encourages premature precision when the problem is still being
  framed.
- It does not, by itself, carry an implementation-session handoff.

### Dedicated planning command

A future `/livespec:plan` or orchestrator-side planning command could
formalize the capture and handoff workflow.

Pros:

- It could generate a research note, seed a prompt, and file only the
  concrete work-items that are ready.
- It could prevent shadow TODO lists by linking prompt checklists back
  to ledger items.
- It could make planning a first-class bridge between spec and
  implementation.

Cons:

- It risks over-specifying the workflow before the convention has been
  exercised.
- It adds another command surface and another place for runtime drivers
  to bind behavior.
- It needs clear boundaries with `next`, `capture-work-item`, `groom`,
  and `propose-change`.

## Recommended interim workflow

Use a lightweight convention before designing a command.

1. Capture the thinking in `research/<topic>/`.

   The research file should include context, problem statement,
   constraints, options considered, pros and cons, open questions, and
   recommended next action. It should say explicitly that it is not
   normative.

2. Add or update an active handoff prompt only when a track needs to span
   sessions.

   Livespec does not currently have `prompts/`, but this capture assumes
   one will be added. The directory should start with `.gitkeep` so the
   convention has a concrete landing spot.

3. Keep the prompt instruction-oriented and the research note
   reasoning-oriented.

   The prompt should answer: what is the current objective, where is the
   reasoning, which ledger/spec artifacts are authoritative, what is
   done, what remains, and when should the prompt be refreshed or
   archived.

4. File beads work-items only when the work is concrete enough to rank,
   depend on, implement, or verify.

   Prompt files may list relevant work-item ids, but should not replace
   the ledger. If the prompt needs a checklist, each item should either
   be a session-local instruction or point at a real ledger item.

5. Promote research into the spec lifecycle only when it becomes a
   contractual rule.

   A research conclusion can become a proposed change, but it does not
   become authoritative by living under `research/`.

6. Archive or remove prompt files when the active track ends.

   A prompt is an active session handle, not permanent design history.
   The durable history should live in research, spec history, commits,
   or ledger records.

## Suggested prompt anatomy

A future livespec handoff prompt should probably include:

- Title and track id.
- Objective.
- Current status, with links to the research note, spec proposal, and
  ledger items where applicable.
- Required startup checks.
- Constraints and non-negotiables.
- Concrete next actions.
- Verification and close criteria.
- Open questions, limited to questions that truly require maintainer
  judgment.
- Handoff refresh rule for context pressure or partial completion.
- Archive/removal condition.

The important distinction is that the prompt should be operational. It
should not try to be the full design rationale; it should point to the
research file for that.

## The "missing planning workflow thread"

The phrase names a real process gap:

- Specification work has a lifecycle.
- Implementation work has a ledger and dispatcher.
- Planning work has research files, but no active-thread handle.

The gap matters because planning is often where the costly decisions
are: choosing what should become spec, what should become
implementation, what should remain research, and what is not worth doing
yet. If that thread lives only in chat, future sessions either repeat
the same reasoning or skip it and file poorly shaped work.

The interim `research/` plus `prompts/` convention gives livespec a
small planning lane without claiming a new product surface yet.

## Notes from the session's back-and-forth

One important exchange was whether a sub-agent should capture the
planning thread. The conclusion was no for this kind of capture. A
sub-agent can do bounded implementation or independent analysis, but it
would only know the parts of the brainstorming explicitly passed into
its prompt. Since the goal was to preserve nuance from the current
conversation, the main agent carrying the context was the better writer.

Another exchange was about stopping unrelated background work before
switching tasks. The reason was not that writing research required a
quiet machine. The reason was that a background deploy can keep mutating
production state after the operator has redirected the session. For
planning capture, unrelated active production work should either be
finished deliberately or stopped before the agent changes focus.

The broader lesson is that "use sub-agents" is not the same as "delegate
context-sensitive memory." Sub-agents are strongest when the task can be
specified cleanly from artifacts. Session-brain capture is strongest
when written by the agent that still has the conversation in context.

## Potential next formalization

If this convention proves useful, the future spec change should decide:

- whether `prompts/` is a first-class livespec convention or only a
  repository-local pattern;
- whether prompt naming should require a ledger id, allow a topic slug,
  or support both;
- where completed prompts should go, if anywhere;
- whether a planning command should generate research and prompt
  skeletons;
- how a planning command would avoid competing with the beads ledger;
- what minimum contents a handoff prompt needs to be safe for another
  agent to resume.

The recommended next step is not to design the command yet. The
recommended next step is to use the convention manually for one or two
tracks, then formalize only the parts that survive contact with actual
work.
