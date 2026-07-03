# Spec-vs-implementation line — workflow-process discussion

**Date captured:** 2026-05-09
**Branch:** `bootstrap/livespec-implementation` (PR #42)
**Status:** Open question. User is sitting with the framing before formalizing.
**Related artifacts:**
- Bootstrap PR #42 (the v058 implementation-layer scaffolding)
- Beads issue `li-jdq` (auto-memory migration audit)
- Future beads issue (this conversation's six-item enforcement list — to be filed separately after this doc is written)

## Why this conversation happened

After landing the bootstrap PR and discussing the auto-memory
migration into `SPECIFICATION/non-functional-requirements.md`, the
assistant proposed six enforcement mechanisms in a flat list (four
spec-content rules, two code/config items). The user's response
opened a deeper question about what *belongs* in the spec versus
what's purely implementation-level intent — and how the latter
should enter the issue-tracking system that drives all work.

The conversation below is captured for the user to sit with before
deciding whether and how to formalize the answer.

---

## Turn 1 — User

> Okay, that makes sense, but we still need to step back and think
> more about process. You are attempting to draw a line which is
> not clear and needs to be specified. I have not really thought
> it through myself, but this conversation is making it clear.
>
> The question is this: What draws the line between something that
> is directly a code change and does not warrant being added to the
> specification, even as a non-functional requirement? And if so,
> what is the workflow for those items? They are "intent" based on
> "observation", But how do they enter into the issue tracking
> system which drives all of the work?
>
> The realization is that some of the intent is inherently going
> to be captured only in the implementation and doesn't belong in
> the specification.
>
> Does this framing make sense?

---

## Turn 2 — Assistant

Yes, the framing makes sense and is important. Let me try to
articulate the line, then surface the questions that follow from
it rather than imposing a workflow.

### The line

**Spec content (requires propose-change):** introduces or changes
a *requirement* — a statement about what the system must / should
/ may do or be. The test is: if someone removed this from the
spec, would the project's contract change? Examples: "skills run
noninteractively", "every gap has exactly one beads issue",
"documentation treats Python as non-default audience."

**Implementation-only intent (does NOT require propose-change):**
realizes, improves, or maintains the system without changing any
requirement. The intent for the change is "this code/config
should look different" — but no contract is being declared,
redefined, or removed. Examples: "extract a helper", "add a
timeout to a subprocess call", "rename a variable", "refactor a
function that was getting unwieldy", "add an enforcement check
that mechanically realizes an already-spec'd rule."

A useful diagnostic: **if the change landed and you re-ran
refresh-gaps, would `current.json` change?** If yes, the change
is realizing or violating the spec — gap-tied work. If no, the
change is implementation-only — pure observation-driven intent
that lives outside the spec lifecycle.

### What this implies for the workflow

A few consequences fall out, and these are the questions worth
thinking through:

**1. Two kinds of beads issues coexist.** The check-gap-tracking
invariant only constrains *one direction*: every current `gap.id`
has exactly one tracking issue. It says nothing about issues that
lack a `gap-id:` label. So freeform issues — implementation-only
intent — already work in the system as designed. Open Brain's
plan skill explicitly distinguishes "freeform issue" from
"gap-tied issue" for exactly this reason.

**2. The source-of-intent differs.** Gap-tied issues come from
`refresh-gaps` running an automated comparison. Freeform issues
come from observation — human or agent notices something during
work. That's a different filing path, and it raises:

- *Who's allowed to observe?* (Both humans and agents — but agent
  observations need explicit user consent before filing, per the
  consent rule established earlier in this same conversation.)
- *What's the bar for filing?* (At what point does an observation
  become worth tracking, vs. fixing inline, vs. dropping?)

**3. Closure semantics differ.** Gap-tied issues require
re-running `refresh-gaps` and confirming the gap is gone.
Freeform issues are done when the work is done — no
spec-verification step. The implement skill's logic should branch
on the label: gap-tied closures need verification, freeform
closures don't.

**4. There's a third category your framing surfaces but doesn't
yet name: non-actionable observations.** "I noticed bd's export
throttles at 60s by default; might matter later if we hit
ordering issues" — that's a piece of context, not a work item.
Where does it live? A beads issue with `status:deferred` and a
`note:` label? A `research/` doc? A code comment? Your
auto-memory ban implies it shouldn't go to local memory — but it
doesn't yet specify where it *should* go. This category may not
need formalizing, but if it does, it belongs in this same
conversation.

**5. The line itself is fuzzy in practice.** Some changes look
like implementation but are actually requirement-changes in
disguise:

- "Add a timeout to subprocess.run" — implementation? Or is
  "every subprocess call MUST have a timeout" actually a
  constraint that should be in the spec?
- "Use JSONRenderer for structlog output" — implementation? Or is
  "all logs MUST be machine-readable JSON" a contract?

The architecture-vs-mechanism distinction the spec already
enforces is the same line, applied to a different question. So
this isn't a new problem — but you may want a heuristic /
examples in the spec itself for when a contributor is unsure.

### Questions worth deciding before formalizing

- Should freeform beads issues use a label namespace (e.g.,
  `obs:`, `improvement:`, `tech-debt:`) to distinguish them from
  "untriaged"? Or is the absence of a `gap-id:` label sufficient
  signal?
- Should the implement skill's closure rules formally branch on
  label, or is "if `gap-id` present, run verification; else
  don't" the implicit rule everyone already knows?
- For non-actionable observations: do they need a home, or do you
  trust contributors to either file as a deferred bd issue, write
  a code comment, or drop?
- Is the line "implementation-only" or "mechanism-only"? In other
  words: does *every* observation about "we should improve X"
  automatically count as implementation-only, or are there
  observations that are themselves new requirements?

The framing is right; the formalization can be a non-functional
requirement about beads-workflow scope (a complement to Proposal
6 in the migration audit, or its own proposal) once the answers
above are settled.

---

## Turn 3 — User

> What is current.json?

---

## Turn 4 — Assistant

`implementation-gaps/current.json` — the implementation-gap
report at the repo root. It's the machine-readable inventory of
every place the `SPECIFICATION/` tree and the actual repository
diverge.

It was created in Phase C/D of the bootstrap. Currently it has
six gap entries (gap-0001 through gap-0006), each describing one
missing or drifted piece of the implementation.

**Lifecycle:**

- **Written by:** the `refresh-gaps` skill
  (`/livespec-implementation:refresh-gaps`). Today the Python
  automation doesn't exist yet (gap-0001), so the file was
  hand-authored manually per the SKILL.md "Manual fallback"
  section. Once gap-0001 closes, refresh-gaps regenerates it
  programmatically.
- **Validated by:** `just implementation::check-gaps` against
  `implementation-gaps/current.schema.json` (also at repo root).
- **Read by:** the `plan` skill (to surface untracked gaps) and
  the `implement` skill (to verify a gap is gone before closing
  the corresponding beads issue with `--resolution fix`).
- **Linked to beads via:** the `gap-id:gap-NNNN` label
  convention. `just implementation::check-gap-tracking` enforces
  the 1:1 invariant — every `gap.id` in `current.json` has
  exactly one beads issue carrying the matching label.

This is why the diagnostic *"if the change landed and you re-ran
refresh-gaps, would `current.json` change?"* tells you whether
something is spec-driven (gap-closing) work vs. implementation-only
intent.

---

## Things to sit with

The user explicitly closed Turn 1 with "I have not really thought
it through myself, but this conversation is making it clear" and
the request to capture this for further reflection. The questions
deserving more thought:

1. **Where is the line, exactly?** The "would `current.json`
   change?" diagnostic is a useful first cut, but Turn 2 §5 flags
   that it's fuzzy in practice. Some implementation changes
   (timeouts, structured logging) might *deserve* spec entries
   even though they look mechanical. Is there a heuristic
   contributors can apply without re-litigating the boundary on
   each PR?

2. **Workflow for implementation-only intent.** Two kinds of
   beads issues coexist already (gap-tied and freeform). But the
   filing-path differs: gap-tied issues come from `refresh-gaps`;
   freeform issues come from observation. The bar for filing
   freeform issues isn't yet specified — when does an observation
   become worth tracking?

3. **Non-actionable observations.** Where do they live, if
   anywhere? Auto-memory is being banned. A research/ doc like
   this one is one possible home; deferred beads issues are
   another; code comments a third. Worth deciding which channel
   serves which observation type.

4. **Closure semantics on the implement skill.** Gap-tied
   closures verify via `refresh-gaps`. Freeform closures don't.
   Should the skill formalize this branch, or is it the implicit
   rule that needs no further codification?

5. **Label namespace.** Whether to give freeform beads issues a
   distinguishing label (`obs:`, `improvement:`, `tech-debt:`,
   `note:`) or leave the absence of `gap-id:` as the sole
   signal.

Once formalized, the answers most likely land as a new
non-functional-requirement section ("Beads-workflow scope" or
similar), authored via `/livespec:propose-change` like any other
spec change.
