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

## Six instances — all observed on 2026-07-20, across three repos and two
## independent operators

These are recorded with their concrete mechanism and counter-move, because the
slogan alone is a platitude that gets skimmed. The pattern is ENVIRONMENTAL, not
personal: it hit two operators working independently on the same day.

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

## Why this file exists in livespec CORE

The six instances span THREE repositories — `livespec`,
`livespec-orchestrator-beads-fabro`, and `livespec-console-beads-fabro` — and
core owns fleet-level facts. A lesson filed only in one tenant would not be read
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
