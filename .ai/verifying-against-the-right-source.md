# Verifying against the right source — when a green signal means nothing

Read this before treating a passing check, an empty query result, or a green
test suite as EVIDENCE that something is true — especially before reporting a
conclusion to the maintainer, filing a work-item, or deciding that work is
already done.

## The failure mode

**A green-looking signal read off the wrong source is not evidence.**

In every instance below, a real check genuinely passed. Nothing was broken, no
tool misbehaved, and nobody ignored a warning. The check was simply pointed at a
source that COULD NOT have shown the problem — so its passing carried no
information, while looking exactly like confirmation.

This is more dangerous than a failing check. A failure invites investigation; a
false pass terminates it.

The test to apply before trusting any passing signal:

> **Could this source have shown the failure?**

If the answer is no, the signal is not evidence, however green it looks.

## Twelve instances — 1-8 observed 2026-07-20, 9-12 on 2026-07-21, across four
## repos and three independent operators

These are recorded with their concrete mechanism and counter-move, because the
slogan alone is a platitude that gets skimmed. The pattern is ENVIRONMENTAL, not
personal: it hit two operators working independently on the same day, and struck
again the following day during work whose EXPLICIT PURPOSE was diagnosing a
signal that had misled everyone. Instances 9-12 come from that session; three of
the four were the recorder's own errors, caught before they were acted on.

### 1. A passing suite is not evidence a PATH is exercised

`dispatcher.auto_approve_ready` was inert on both admission paths — unlabeled
work-items never auto-approved, contradicting a ratified scenario. The module had
tests and they all passed. They passed because EVERY auto-approving test supplied
a per-item `admission:auto` label; not one drove the global-inherit path through
the live call site. The suite was green over the only input shape that could not
expose the bug.

**Counter-move:** check that the CALL SITE is covered, not that the module is. A
module with tests tells you nothing about a path through it that no test
constructs. Ask which input shape would fail, then ask whether any test builds
that shape.

### 2. A test can assert the wrong thing and still be green

A console integration test guarded the orchestrator-journal read leg and passed
throughout, while that leg was dead in production on three simultaneous wire
mismatches (wrong filename, wrong stage, wrong record schema). It passed because
its fixture encoded the RETIRED wire shape — the same assumption the code under
test held. The test and the code agreed with each other and both disagreed with
production.

**Counter-move:** when a test guards a behavior you care about, READ WHAT IT
ACTUALLY ASSERTS. A fixture that encodes the same assumption as the code cannot
falsify that assumption. Pin fixtures to the PRODUCER's real output — derive or
digest-stamp them against the producer rather than hand-writing the consumer's
expectation.

### 3. Tool defaults are scoped narrower than you assume

A dispatched agent completed its work and opened a pull request. Checking for it
with a bare `gh pr list` returned empty — because that command lists only OPEN
pull requests by default, and this one had already MERGED. The empty result was
read as "never happened", and a DUPLICATE pull request was opened for work
already on master.

**Counter-move:** pass `--state all` (or `--state merged`). More generally, when
ABSENCE is the thing being concluded, check the query's implicit filters first —
an empty result can mean the opposite of what it appears to mean.

### 4. A local `remotes/origin/*` ref is a CACHE, not remote state

In the same episode, `git branch -a` showed a `remotes/origin/<branch>` entry,
which was read as proof the branch had been pushed. It had not been.
`git ls-remote` returned nothing and `git fetch --prune` deleted the stale ref.

**Counter-move:** query the forge, or use `git ls-remote`, when remote existence
is load-bearing. Remote-tracking refs reflect the last fetch, not reality.

### 5. The default ledger listing HIDES CLOSED ITEMS

During an acceptance run, a tenant was swept for duplicate filings across its 28
VISIBLE work-items and reported clean. The sweep was wrong in method: that tenant
also held 61 CLOSED records that were never examined, and a duplicate filing did
in fact exist among them.

**Counter-move:** any dedup or "has this been filed / fixed already?" sweep MUST
request closed records explicitly. A default listing answers "what is open?", not
"what exists?" — and those are different questions whenever you are checking for
prior art.

### 6. A directory listing cannot distinguish "never existed" from "deleted"

A supervisor checked whether a plan thread existed, found the path absent from a
directory listing, and issued the directive "it does not exist active or
archived; you were pointed at a handoff that was never written." The thread DID
exist — it had been removed by a `git rm` an hour earlier and was restored
shortly after. Obeyed literally, that directive would have abandoned a 253-line
handoff holding findings recorded nowhere else.

The listing was accurate. The inference was not: an empty result was read as
proof of NON-EXISTENCE rather than as one observation, from one source, at one
moment.

**Counter-move:** when concluding that something never existed, check a source
that records HISTORY, not just current state — `git log --diff-filter=D -- <path>`
finds a deletion; a listing never will. More generally, absence in a
point-in-time view is evidence about that view, not about the past.

**Recorded deliberately as a supervisor's error.** Along with instance 5, it
shows the pattern reaching the person REVIEWING the work as readily as the person
doing it — which is the strongest available argument that it is environmental
rather than a matter of individual care.

### 7. An archived plan thread moves every path it owns

A fleet audit checked whether four confirmation artifacts existed, searched the
LIVE thread path (`plan/<topic>/`), found nothing, and concluded the dispatches
that would have produced them never ran. It then reported a work-item as wrongly
parked in the `acceptance` lane.

The artifacts existed — at `plan/archive/<topic>/`. The thread had been ARCHIVED
after those dispatches completed, which moved every path it owned. The items were
awaiting a legitimate acceptance of real work and belonged exactly where they
were. Acting on the wrong conclusion caused churn.

**Counter-move:** when checking whether a plan-thread artifact exists, search
`plan/archive/` as well as `plan/`. More generally, before concluding from a
path-based search that work never happened, ask whether the thing being searched
for could have MOVED — archival, renames, and reorganisations all silently
invalidate a path-shaped query while leaving it looking authoritative.

### 8. A squash-merged PR does not carry commits pushed after it merged

Instances 6 and 7 above were committed and pushed to the branch of an OPEN pull
request, on the assumption they would ride it to master. The pull request had
already been squash-merged. The later commits stayed on the branch, orphaned;
master carried only five instances. The gap was found when a ledger note written
elsewhere cited "instance 7" — a citation that pointed at nothing.

**Counter-move:** after pushing to a pull request's branch, confirm the pull
request is still OPEN before treating the push as delivered, and verify the
content on the target branch rather than on your own. A squash merge in
particular leaves your local branch looking healthy and fully-pushed while
sharing no commit with the merged result.

### 9. A job or run STATUS is not a health signal

Three separate times in one fleet-propagation investigation, a status artifact
was read as health and was wrong in BOTH directions:

- **Open bump-PR count.** A thread drove it 43 → 0 and read zero as healthy.
  Zero open bump PRs is indistinguishable from a DEAD FAN-OUT — the fleet looked
  its best at the moment propagation had stopped.
- **A run conclusion.** The v0.20.0 fan-out run reads `failure` to this day
  because a run's conclusion reflects its WORST ATTEMPT; attempt 4 was wholly
  green and dispatched to all eight siblings. "The run is red" and "the fan-out
  is broken" became different statements.
- **A scheduled job's colour.** The pin-freshness sweep failed on every member
  every day on a benign no-op. Red became the normal state, so red carried no
  information — and it concealed a second, real defect underneath it.

**Counter-move:** assert on the OUTCOME the job exists to produce, never on the
job. Here the outcome is PIN CURRENCY — each consumer's pin against the
producer's latest release — which caught the stall immediately and which no
status could have. When a status must be used, check WHICH attempt and WHICH job
produced it.

### 10. Absence in a log is not evidence when the path never ran

To re-check whether a defect still reproduced, seven fresh scan jobs were grepped
for its signature. Zero hits on all seven — and the result was worthless: the
scan `continue`s on a current pin BEFORE reaching the code that emits that
signature, and every member's pin was current. The grep proved only that healthy
repos are healthy.

This is instance 1's shape moved from tests to production logs, and it is easier
to fall for: a test suite at least reports what it ran, while a log search
silently returns nothing for "did not happen" and "could not have happened"
alike.

**Counter-move:** before reading absence as evidence, confirm the emitting code
was REACHED — find a positive control in the same output (a log line only
produced on that path), or identify the input that forces the path and check that
it was present. Absence over an unexercised path is not a negative result.

### 11. Ancestry against a pre-merge SHA is not a containment test

To check which release carried a just-merged PR,
`git merge-base --is-ancestor <local-sha> <tag>` was run and answered NO for both
candidate tags — apparently proving the fix had not shipped. It had. The repo
rebase-merges, so the merged commit is a DIFFERENT object than the local one; the
local SHA is an ancestor of nothing on master.

**Counter-move:** on a rebase- or squash-merging repo, test containment by
CONTENT, not ancestry — `git show <tag>:<path> | grep <marker>` answers the
question the SHA cannot. Reserve `--is-ancestor` for merge-commit workflows where
the object survives.

### 12. A conclusion about live fleet state expires in MINUTES

Two claims, both correct when written, both false shortly after:

- A sibling thread recorded "the fleet GitHub App still does not cover
  `livespec-overseer`" at 04:39:03Z. At 04:42:25Z — three minutes later — the
  fan-out preflight logged `fleet conformance passed` and dispatched to all
  eight siblings.
- This file's own recorder wrote that a fix was "NOT yet live for consumers",
  then measured an hour later and found consumers had already bumped past it.

Neither was careless; both were written from a real earlier reading and simply
not re-measured before being recorded as current.

**Counter-move:** date every claim about live state and re-measure before
repeating it, INCLUDING one you wrote yourself an hour ago. When a fleet is
actively moving — releases cutting, fan-outs dispatching, other sessions
landing — treat any state assertion older than the current turn as a hypothesis.
Prefer writing the INVARIANT ("gap zero") over the reading ("both at v0.20.0"),
because the invariant survives the next release and the reading does not.

## Why this file exists in livespec CORE

The twelve instances span FOUR repositories — `livespec`,
`livespec-dev-tooling`, `livespec-orchestrator-beads-fabro`, and
`livespec-console-beads-fabro` — and core owns fleet-level facts. A lesson filed only in one tenant would not be read
by an agent working in another, which is precisely where most of these happened.

## Related standing rules

This is the same instinct behind two rules already in force:

- **"Done" means rolled out and exercised live** — never merely merged +
  CI-green + AI-accepted.
- **The non-behavior-bearing acceptance form** — discharge by INDEPENDENT
  ADVERSARIAL REVIEW that re-derives claims against live state, rather than
  trusting the artifact, CI, or its author.

Both say: do not accept a signal from a source that could not have contradicted
you.
