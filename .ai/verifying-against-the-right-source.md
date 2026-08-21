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

## Recorded instances, by observation date — 1-8 on 2026-07-20, 9-12 on
## 2026-07-21, 13 on 2026-07-26, 14-15 on 2026-07-27, 16 on 2026-08-04, 19-23
## on 2026-08-05, 24-28 on 2026-08-06, 29-30 on 2026-08-11, 32-33 on 2026-08-19,
## 37 on 2026-08-21;
## instances 1-16 span
## five repos and four independent operators

The gaps in that heading are deliberate rather than oversights. **Instances
17, 18, 31, 34, 35 and 36 carry no recorded observation date**, so none is assigned
to them here — verified by reading each entry for an inline date rather than
inferred from the heading's own silence — a first draft of this correction invented one for 17 and 18 and it was
backed out. Instance 31's RECORDING commit is dated 2026-08-12, and that is
deliberately not promoted into the list above: a landing date is not an
observation date, and quietly substituting one for the other is the same
wrong-source substitution this file exists to catalogue. And
the repo/operator tally is **scoped to instances 1-16**, because it could not be
re-derived from the file; incrementing it on assumption would be the exact error
this file exists to prevent.

**This heading used to carry a total, and that total is gone on purpose — the
history of why is the useful part.** It read "Sixteen instances" while eighteen
were present, because it was not updated when 17 and 18 landed: the
clause-lockstep defect `.ai/spec-proposal-review.md` describes, where a count
must be re-derived whenever the set it describes changes. Corrected 2026-08-05
alongside instances 19-21, and again 2026-08-06 alongside instance 24 — where
the count in `AGENTS.md` had to move in the same commit, since it stated the
total too.

It then drifted a THIRD time. When instances 24 and 25 landed, the count in
`AGENTS.md` and the one in §"Why this file exists in livespec CORE" were both
updated, but this heading was not, so it read "Twenty-three" while twenty-five
were present. There were THREE copies of the same total — this heading, that
section, and `AGENTS.md` — and the one that rotted was whichever was not on
screen when the instance was added. **Two of three being right is exactly what
let it survive review:** a spot-check landing on either correct copy confirms
the number and moves on.

Three rots in three weeks is the argument for deleting duplicated state rather
than maintaining it harder, so all three totals were REMOVED on 2026-08-11
rather than corrected a fourth time. The count is now derived on demand with
`grep -c '^### ' .ai/verifying-against-the-right-source.md`, which cannot
disagree with itself. **Do not reintroduce a total in any of those three
places.** What this heading still carries is the per-instance observation dates,
which are provenance rather than duplicated state — the `###` headings record no
dates, so nothing else holds them — and those DO need extending when you add an
instance.

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

**A SECOND CONSEQUENCE, worse than a duplicate: the closed record often holds the
CORRECT ANALYSIS, so missing it means re-deriving the question badly.** Recorded
2026-08-06. A session measured that `release-tag.yml` fails on every release,
inferred that the dogfooding-pin rationale ("a release is the more-validated
artifact") therefore held "only for mutation testing", and escalated that to a
human. The framing was wrong — all three release-gate validations do run, and
run strictly. A CLOSED item in the same tenant, `livespec-besm`, had already
stated the right framing in one clause: *"Does NOT block the release (the gate
runs post-tag)."* The real point is that the gate fires on tag push, after the
release object exists, so a failing gate cannot retract a release that siblings
will consume — sharper than what was escalated, and available for the reading.

So the cost of skipping closed records is not only a duplicate filing. It is
**escalating an analysis that the ledger had already got right**, which spends a
reviewer's round-trip and puts a wrong claim in front of a human. Note the scale
that made it easy: the default listing returned **50** items where
`--all -n 0` returned **624**, of which **532** were closed. A prior-art check
run against 8% of the record is not a weak check, it is a different question.

**The same blind spot has a NON-LEDGER form — two documents describing one
effort.** Also 2026-08-06: the same defect was filed twice, ten hours apart, by
two lanes of one plan, because the lanes' own records cited different ids for it
(`handoff.md` named one, `supervisor-handoff.md` the other) and neither lane's
prior-art check read the other's document. **Two records of one effort are two
prior-art blind spots.** When a plan is written down in more than one place,
search every place, not the one you authored.

### 6. A directory listing cannot distinguish "never existed" from "deleted"

A supervisor checked whether a plan existed, found the path absent from a
directory listing, and issued the directive "it does not exist active or
archived; you were pointed at a handoff that was never written." The plan DID
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

### 7. An archived plan moves every path it owns

A fleet audit checked whether four confirmation artifacts existed, searched the
LIVE plan path (`plan/<topic>/`), found nothing, and concluded the dispatches
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

**A second counter-move, for the "is this BRANCH's work already merged?" form of
the same question (added 2026-08-05): `git cherry <upstream> <branch>`.** It
compares PATCH-IDs, so it sees through the SHA change a rebase-merge causes,
marking each commit `-` when an equivalent exists upstream and `+` when none
does. Deciding whether five stale worktrees were safe to delete, `git diff
origin/master --stat` reported each one carrying insertions plus up to 57,793
deletions — which reads as unmerged work alongside mass deletion, and is neither:
the deletions were just the branch being behind master, and the insertions were
files master had since changed again. `git cherry` settled it in one line per
branch — every commit `-`, nothing unmerged, all five safe. **Prefer it whenever
the question is about a branch rather than a single commit, and note that `git
diff` against master is actively misleading here rather than merely unhelpful,
because a stale branch always produces a large, alarming, meaningless diff.**

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

**A third case, added 2026-08-11, because it sharpens WHICH readings expire
fastest — and it is deliberately not a new instance number, since the class is
already this one.** A session recorded that a repaired release gate could not
prove itself for some time, evidencing this with *"there is no pending
release-please PR — its branch was deleted when the last release was cut."* The
deletion was real and correctly observed at `06:26Z`. By `06:36Z` release-please
had re-opened the PR; it merged at `06:55:06Z` and the gate ran fifteen seconds
later, green. Acting on the sixteen-minute-old reading would have deferred to a
later session a proof that was four minutes away.

**What makes this one worse than the two above is that the reading was of an
ABSENCE.** "Both at v0.20.0" announces itself as a snapshot; "the branch was
deleted" reads as a settled historical fact, because deletion feels terminal. It
is not — anything a bot creates on a schedule or a trigger, a bot will create
again. So the expiry rule applies with FULL force to absences, and the shorter
half-life belongs to whatever a bot owns: a release-please PR, an auto-merge
queue, a bump branch, a scheduled sweep's artifacts. **Never evidence a claim
about the future with the current absence of a bot-managed artifact.** Evidence
it with the condition that would produce the artifact.

### 13. An UNTRACKED file is invisible to a git-derived check universe

`just check` reported **61/61 green** on a branch whose whole point was a new
module — and the new module was not in the scan. The LLOC checks
(`file_lloc`, `no_lloc_soft_warnings`) and every other check routed through
`config.resolve_check_universe` derive their file set from `git ls-files`, which
lists the INDEX. A newly created file that has never been `git add`-ed is not in
the index, so it is not in the universe, so no check walks it. The green was
read off a universe that did not contain the file under review.

Nothing was misconfigured — the git-derived universe is the deliberate fix for
an OLDER fail-open hole (a hardcoded tree list that resolved to zero files in
repos whose package directory was named differently). It simply has this edge:
coverage begins at `git add`, not at file creation.

The mechanism is worst exactly when it matters most, because the checks it
disarms are the ones that police NEW files: size ceilings, `__all__`
declarations, mirror-test pairing. A refactor that splits one large module into
several new ones is precisely the changeset where every new file is untracked
and every relevant check silently skips it.

**Counter-move:** on any changeset that ADDS files, `git add` before measuring,
and treat a green obtained on a dirty tree with untracked files as provisional.
`git status --short` showing `??` lines beside a passing check is the tell. The
cheap habit is `git add -A` first, then run the gate — the same tree the commit
will carry is the only tree whose green means anything.

### 14. Distrusting a signal you never checked — and paying for it destructively

THE INVERSE OF EVERY INSTANCE ABOVE, and worth the entry precisely because it
inverts them. The other thirteen are a green signal wrongly TRUSTED. This one is a
signal wrongly DISTRUSTED: an agent decided a check's output could not be
believed unless the repo's config were first mutated, and the mutation was both
unnecessary and lossy.

`check-file-lloc` reports over-ceiling files at `error` severity in a repo that
declares `source_trees`, and at `warning` severity in one that does not. To take a
reading "as it would really be", three consecutive sessions in `livespec-overseer`
edited the TRACKED `pyproject.toml` — setting `source_trees = ["overseer"]` and
`covered_trees = ["overseer"]` — ran the check, then reverted.

**The premise was false. Arming those keys cannot change which files are
measured.** The universe comes from `config.resolve_check_universe()`, which is
`git ls-files '*.py'` filtered by exactly two keys — `tests_tree_prefix` and
`neutral_hook_body_path`. `source_trees` and `covered_trees` are not consulted in
resolving it at all. They change how a finding is CLASSIFIED, never what is
walked. Measured both ways in `livespec-overseer`: 84 files armed, 84 files
unarmed, identical set.

So every LLOC number those sessions wanted was already available with no edit at
all, and the sessions that mutated config were not getting a truer reading than
the one they already had.

THE COST WAS NOT THEORETICAL. The revert step destroyed real work TWICE:

- `git checkout -- pyproject.toml`, used to undo the temporary arming, also
  discarded an unrelated edit made in the same file during the same session;
- a `str.replace` on `source_trees = []` silently rewrote the long explanatory
  COMMENT above the key, because the comment quoted the same string.

Both were recovered only because someone re-diffed afterwards and noticed. A
destructive, lossy workaround was being paid, repeatedly, for a problem that did
not exist.

WHY IT SURVIVED THREE SESSIONS: the technique WORKED. The armed run did print the
error-severity output the agent wanted to see, so the reading looked like it had
required the mutation to obtain. Nothing ever contradicted the premise, because
nobody ran the check unarmed and compared. This is the file's own test applied to
a *dis*trusted signal — "could the unarmed source have shown this?" was never
asked, and the answer was yes all along.

**Counter-move:** before mutating any tracked config to make a check report
differently, READ the check's universe-resolution path and establish what the key
you are about to set actually controls. A key that selects SEVERITY does not need
to be set to obtain a measurement; only a key that selects the UNIVERSE does. Take
the census directly instead:

```python
from livespec_dev_tooling.checks.file_lloc import _count_lloc, resolve_check_universe
root, files = resolve_check_universe()
rows = sorted(((_count_lloc(source=(root / p).read_text()), p) for p in files), reverse=True)
```

And the general form, which outlives this particular check: **a destructive
technique that appears to work is not evidence it was needed.** If a measurement
requires mutating tracked state, that is a claim about the tool worth verifying in
the tool's source before paying for it — the mutation costs nothing to skip and
can cost real work to perform. When a temporary edit to a tracked file genuinely
is unavoidable, revert it BY LINE and re-diff, never with a whole-file
`git checkout --` that cannot distinguish your temporary edit from your real one.

### 15. A check that EXITED EARLY reports a clean stream, not a clean result

`no_except_outside_io` evaluated `find_ruff_backstop_gaps` first and
`return 1`-ed on any gap — BEFORE the block that logs position offenses. So in
every repo carrying a gap, real broad catches were computed, counted in the
`files_inspected` / `offenses` info line, and then never logged. The check
exited non-zero, so it LOOKED like it worked; the offenses it had already found
simply never reached the error stream a reviewer and a CI log actually read.

A fleet census read that stream and concluded **"zero genuine broad catches,
zero domain raises"** across all nine repos. There were **seven**, every one
hiding behind a gap. The wrong number was journalled on the work-item and acted
on — it was the evidence for a design that then had to be reverted from six
repositories.

This is the family the whole file is about, one layer in: not a green read off
the wrong REPO or the wrong REF, but a green read off a stream the check
ABANDONED before it finished. The source was right. The check stopped talking
partway through, and silence after an early return is indistinguishable from
silence after a clean pass.

The tell was available and was missed twice: the check's own info line said
`"offenses": 1` while its error stream named none. A summary count that
disagrees with the itemised output is the signal, and it is worth looking for
precisely because a check that exits non-zero does not feel like a check that
is hiding something.

**Counter-move:** when a check can fail for more than one reason, never read
only the first failure it decides to report — read its structured COUNTS too,
and reconcile them against the items it listed. When measuring with a check
rather than merely running it, replay its own loop rather than trusting `main()`
to have finished: an unmasking pass that re-runs the finding logic against the
same universe is cheap, and it is what turned "zero" into "seven" here. And when
you find such an early return, FIX it — report every failure kind in one run —
because the next reader will trust the stream exactly as you did. (Fixed in
`livespec-dev-tooling` PR #727, with a regression test whose fixture carries a
backstop gap AND a position offense in different files, because asserting only
the exit code passes against the defect.)

### 16. A REQUIRED check reporting SUCCESS may have skipped its own step

Five fleet repositories sat with red `master` CI for hours while pull requests
kept merging into them, and every merged PR's required `ci-green` was honestly
green. Nothing was misconfigured and no gate had been weakened.

The mechanism is one layer below instance 9. There, a job's status was read as
health. Here the JOB status is not merely a weak proxy — it is affirmatively
wrong, because the job ran and reported `success` having executed none of its
real steps. On `livespec-overseer` PR #698, job `check-public-api-result-typed`:

    Skip when no .py changes            success   <- the whole story
    Checkout                            skipped
    Install Python dev deps via uv      skipped
    just check-public-api-result-typed  skipped   <- the check NEVER RAN
    JOB CONCLUSION                      success

The same job on the master push at the SAME merge commit ran the check and
FAILED. A zero-`.py` changeset takes a deliberate "skip" step that SUCCEEDS,
every real step is `if:`-skipped, and a REQUIRED context therefore certifies
nothing while presenting as a check that passed. It does not even report
`skipped`, which an observer might have noticed.

Four hypotheses were eliminated by measurement before the real one was found,
each of which had felt obvious: a pin difference across the rebase-merge (the
pin was identical at both commits), a container-image difference (identical tag,
and the two runs started six seconds apart), universe scoping in the recipe (the
justfile recipe is a bare module invocation), and a stale base — master gaining
violating code between the PR run and the merge — which died when the checker
was run against BOTH trees in throwaway worktrees and reported the same 123
violations in each. The answer was never in the trees; it was in which STEPS ran.

**Counter-move:** for a required check, read STEP conclusions, not the job
conclusion. `gh run view <id> --json jobs` carries `.jobs[].steps[]`, and the
question to ask is not "did this job pass" but "did the step that runs the check
execute". A green required context whose command step is `skipped` is a check
that CANNOT FAIL — the same defect as a check that cannot pass, which this file
names elsewhere. When a subsetting optimisation exists to skip work, the design
obligation is that a skipped verification must not be indistinguishable from a
successful one: report a non-success outcome, or make the aggregate distinguish
"ran and passed" from "did not run". (Tracked as `livespec-dev-tooling-zi29`,
filed separately from the regression it concealed precisely so that fixing the
regression could not close it.)

### 17. A flag that DOES NOT EXIST returns an empty result, not a negative one

Before filing a cross-repo epic, a dedup sweep ran seven queries against the
beads ledger with `bd list --search "<term>"`. All seven returned nothing. That
is exactly the shape of "no duplicates exist", and it would have authorised
filing straight over `livespec-j49m` — an open P1 covering part of the same
ground.

`--search` is not a flag `bd list` has. It was accepted and ignored, so every
query degraded to an unfiltered listing whose output was then filtered by a grep
that matched nothing meaningful. The real flag is `--desc-contains`. Re-running
the sweep with it surfaced the overlap immediately.

The tell was statistical, not mechanical: SEVEN queries, including deliberately
broad ones, all returning zero. A search space that answers "no" to everything is
not describing the corpus, it is describing itself. **Before accepting an empty
result as evidence of absence, prove the query can return a non-empty result** —
run it against a term you KNOW is present. One positive control converts an
unfalsifiable silence into a real measurement, and costs one command.

This generalises past CLIs. Any filter that silently tolerates an unknown
predicate — an unrecognised flag, a typo'd label, a JSON path that matches no
key — fails in this direction, and the failure always looks like good news.

### 18. A working tree one commit BEHIND is not the tree that failed

`livespec-runtime` master CI went red on `check-public-api-result-typed`
immediately after a bot-authored pin bump to `livespec-dev-tooling` v1.18.9. The
repo declares `pure_trees = { not_applicable = ... }`, and the check's own
docstring says its scan universe is `pure_trees`-scoped — so the working
hypothesis was that v1.18.9 had REGRESSED the role-absence gate and was now
scanning a tree it had been told did not exist.

Running the check locally returned exit 0, logging `role key declared NOT
APPLICABLE`. That looked like confirmation the gate still worked locally and
something environmental differed in CI, and it was one step from an upstream bug
report against a sibling repo.

The local checkout was `behind 1`. The failing commit was not in the working
tree; the check had been run against the last GREEN commit. After
`git pull --ff-only`, the same command reproduced all eleven violations. The
truth was the opposite of the hypothesis: `46c5dab` in `livespec-dev-tooling`
("scan the first-party universe, not pure_trees") had deliberately ARMED the
check, fixing the very vacuity defect instance 1 of this file's sibling finding
records. Nothing had regressed; enforcement had landed ahead of adoption.

**A local reproduction proves nothing until you have confirmed WHICH COMMIT you
reproduced against.** `git status --short --branch` shows `[behind N]` in one
line. The trap is specific to investigating a CI failure, because the natural
motion is to reproduce locally, and a primary checkout drifts behind origin
constantly in an active fleet — so the default state of the tree is "not the one
that failed". Note also the direction of the error: it manufactured a
*sibling-repo bug* out of a *local staleness*, which is the expensive direction
to be wrong in.

### 19. Verifying the STEP you changed is not verifying the RUN it sits in

An eight-repo propagation added a pack-install step to each consumer's `ci.yml`
(`livespec-dev-tooling-y6e2`). It was reported complete as "8-of-8 done, each
verified `pack-install=success` where it previously read `skipped`" — a precise,
per-repo, step-level measurement, and every word of it was true.

Two of those eight repositories had a RED master at that exact commit.
`livespec-orchestrator-beads-fabro` and `livespec-driver-codex` both failed on
OTHER jobs in the same run — a `shellcheck` download reset and a `pytest-cov`
download failure — neither of which the propagation caused or touched. Nobody
looked, because the thing that had been changed was green, and the report
answered the question "did my change take effect?" rather than "is the repository
healthy?".

Note how naturally the narrow question substitutes for the broad one: the step
was the unit of work, so it became the unit of verification. And the narrower
check is the more rigorous-LOOKING one — it names a specific step and a specific
before/after transition, which reads as more careful than "CI is green".

**After landing a change, verify the RUN, not just the step you touched — and do
it in every repository the change reached.** The step-level check is still worth
doing; it is simply not a substitute. A useful discriminator: a step-level pass
tells you your change works, and only a run-level pass tells you it did not break
something else. This is instance 9 ("a job or run STATUS is not a health
signal") inverted — there, a green status hid a skipped step; here, a green step
hid a red run.

### 20. A 404 for one repo's filename is not evidence another repo has no CI

A fleet-wide master-CI sweep queried
`repos/<owner>/<repo>/actions/workflows/ci.yml/runs` for all 13 manifest members.
Eleven answered. `openbrain` and `resume` returned HTTP 404, and the first draft
of the finding recorded them as running no CI and therefore unmeasured.

Enumerating each repository's workflows instead of guessing one filename showed
`resume` gates with **`check.yml`** — green on `master`, measurable the whole
time — while `openbrain` genuinely has no per-push gate, only a scheduled
`tripwire.yml` whose latest run predated the sweep by a week and was therefore no
evidence about current `main` either.

The 404 was real. The inference from it was not: it silently assumed the fleet
names its gating workflow uniformly, in a fleet whose own `AGENTS.md` says it is
**non-uniform by design**. This is the same error recorded elsewhere in this
thread as "grepping ONE repo's spelling to conclude another repo's state".

**Enumerate the set before concluding a member lacks a thing.** `GET
/actions/workflows` costs one extra call and answers "what does this repo
actually have?", where a filename probe only answers "does it have the name I
guessed?". The tell is a NEGATIVE conclusion resting on a single lookup keyed by
a name you chose rather than read.

### 21. A control verified as currently-UNMET is not verified as HARD to meet

The shared factory host's residual `gate-runner` units each carry a drop-in whose
entire `[Unit]` body is `ConditionPathExists=/run/livespec-local-ci-enabled`.
The path was measured absent, the units measured `inactive` and `disabled`, the
slice measured `Tasks: 0`. That was recorded as a second, independent gate
requiring an explicit operator opt-in.

Every one of those readings establishes only that the condition is **not met right
now**. None of them establishes that it is **difficult to meet** — and the claim
being banked was the second one. Had any `tmpfiles.d` rule, unit, cron entry or
boot script created that runfile automatically, "explicit operator opt-in" would
have been false while every reading still looked green.

Checked adversarially, the claim held: the runfile has **consumers only and no
creators** across both `tmpfiles.d` directories, `/etc/systemd/system/`,
`/usr/lib/systemd/system/`, `/usr/local/{lib,bin,sbin}/`, `cron.d`, `cron.daily`,
`rc.local`, and every tracked file on `livespec` master. The search was shown
fail-capable by the same grep returning the two CONSUMING drop-ins, so the zero
was a measurement rather than a silent miss.

**For any control, ask what would have to be true for it to be defeated, then go
look for that.** A condition's current value is cheap to read and nearly always
the wrong question; what matters is who can change it. Concretely: enumerate the
WRITERS of the thing a control reads, not just its present value. This is the
`livespec-opwqmy` lesson stated generally — *a control is not a control until it
has been made to fail on demand* — and it applies with most force to controls
that are currently satisfied, because those produce no signal to investigate.

### 22. A ref that does not exist here returns empty, so a sweep reports the repo OUT OF SCOPE

Discharging a work-item's "enumerate the fleet, do not assume" clause, a sweep
read every governed repo's committed config with
`git show origin/master:.livespec.jsonc` and classified each as affected or
clean. Two of thirteen came back with nothing and were recorded as **"no
committed config — out of scope"**.

`openbrain` and `homelab` do not have an `origin/master`. They use `origin/main`.
Both carry the file, both lack the key being audited, and both were therefore
AFFECTED. A non-existent ref makes `git show` print nothing and exit 0, which is
byte-identical to a repo that genuinely has no such file.

The bias is what makes this dangerous: it under-reports SCOPE, so an incomplete
sweep reads as a complete one. The report said "13 enumerated" and looked
exhaustive while silently excluding 2 of the 8 affected repos — and "I enumerated
the whole fleet from the manifest" was TRUE, which is precisely why nothing felt
wrong. Enumerating the right repos does not mean reading them correctly.

**Resolve each repo's default branch instead of assuming one**
(`git symbolic-ref --short refs/remotes/origin/HEAD`), and make an unresolvable
ref FAIL LOUD rather than record an absence. `AGENTS.md` already warns that the
fleet is non-uniform and that per-repo state must be verified rather than assumed;
the default branch is one of those dimensions, and it is easy to forget because
eleven of thirteen repos agree.

The control that caught it could not silently pass:
`git ls-tree <ref> --name-only | wc -l` returned **0 files at the repository
root** — a count that cannot be true for any real ref of any real repo. Note that
the obvious control does NOT work here: re-reading `.livespec.jsonc` and getting
empty again just reproduces the same ambiguity. The control has to interrogate the
REF rather than the file, because the ref is what is missing. When a read comes
back empty, pick a positive control that tests the thing you assumed, not the
thing you asked for.

This is instance 17's mechanism — a nonexistent predicate silently degrading a
query — relocated from a CLI flag to a git ref, and from a dedup search to a
coverage sweep. Worth its own entry because the consequence differs: 17 invents
absence of DUPLICATES and risks a redundant filing; this one invents absence of
WORK and risks shipping a fix that misses a quarter of its targets.

**A second case, added 2026-08-11, and it is the uncomfortable one: FIXING THE
AXIS THIS ENTRY NAMES DOES NOT PROTECT YOU ON THE OTHER AXES.** A fleet
master-CI sweep was written that handled the `master`/`main` asymmetry correctly
— it tried both refs, which is precisely the counter-move above — and it still
fell into this same trap one level over, because it probed a **hardcoded
workflow filename**, `ci.yml`. It reported:

    resume     adopter   NO ci.yml RUNS (excluded, not claimed green)

`resume`'s gating workflow is **`check.yml`**, with **145 runs**, master green.
Twelve of thirteen repos use `ci.yml`, so the assumption held everywhere it was
looked at, and the one exception read as an absence of CI rather than an absence
of that filename. The bias is identical to the `origin/main` case: it
under-reports, and the sweep looked complete because every repo in the manifest
appeared in the output. The wording *"excluded, not claimed green"* even sounded
careful — it honestly flagged that the repo was not being asserted green, while
being wrong about why.

**What generalises past both cases: a sweep should never hardcode a per-repo
NAME it could enumerate.** The corrected probe lists each repo's workflows first
and selects from what exists; when nothing matches, it prints the workflows it
DID find rather than the phrase "no CI". That makes the negative
self-falsifying — `openbrain`, the one repo that genuinely has no gating
workflow, now reports `has: bump-plugin-pin.yml deploy-dashboard.yml
tripwire.yml`, which a reader can immediately check, instead of an unfalsifiable
absence.

So the entry's own counter-move needs stating more broadly than the ref: **for
every per-repo name a sweep assumes — default branch, workflow filename, config
path, job name, label — either enumerate it or make its absence fail loud. The
fleet is non-uniform on more dimensions than the one that bit you last time.**
(Self-caught, roughly an hour after the wrong figure had already been published
in a merged handoff and had to be corrected there too.)

### 23. A dead query that returns the RIGHT answer is the one that erodes the habit

Instances 17 and 22 are dead queries returning WRONG answers, which is the
tractable case: something eventually contradicts you. This is the other case, and
it is worse.

Re-verifying that no `ci-runner*` or `runner@` unit files remained on the shared
factory host, a check ran
`ls /etc/systemd/system/ | grep -cE '^ci-runner|^runner@'` and returned **0** —
the correct answer, independently true.

The query could not have returned anything else. On this host `ls` is aliased to a
rich formatter whose every line begins with an INODE NUMBER, not a filename, so a
`^`-anchored pattern matches nothing no matter what the directory contains. The
grep was structurally incapable of a positive result and happened to agree with
reality.

Nothing about the output looked wrong, because nothing WAS wrong — this time. The
same command run on the day a `ci-runner@.service` reappears returns 0 just as
confidently. A result that is correct by coincidence actively teaches you to trust
the method that produced it, which is why this class survives review: every past
run "worked".

The positive control is what exposed it, and only because it was aimed at a
prefix KNOWN PRESENT: `^gate-runner` also returned 0, while an unanchored
`gate-runner` returned 4. Those two numbers cannot both be right, and the
contradiction — not the original result — is the finding. Re-running with bare
filenames (`find . -maxdepth 1 -printf '%f\n'`) gave `^gate-runner` = 4 and
`ci-runner|runner@` = 0 out of 85 entries: same conclusion, now actually measured.

**Two rules follow.** Run the positive control even when the answer looks right —
especially then, because a matching result is exactly what suppresses the impulse.
And never parse `ls` in a check; its output is a display artifact that a user alias,
a locale, or a terminal width can reshape. Use `find -printf`, a glob, or `git
ls-files`, all of which emit names and nothing else.

### 24. A step named "Skip …" that is SKIPPED is proof the check RAN

Every other entry here guards against believing a green that is hollow. This one
guards the opposite error, and it was reached by a reviewer catching a first
draft of this very session's verification.

Instance 16 taught this fleet to distrust a green required context and read its
STEP list. Applied to `livespec` master run `31057914032` for merge commit
`cead37ca`, the step list for `check-public-api-result-typed` contains a step
named `Skip when no .py changes` whose conclusion is `skipped`. Seeing the word
"Skip" in the step list of a job you have been trained to suspect is a strong
pull toward "there it is again."

It is the exact opposite. The two shapes are mirrors, and the discriminator is
the STATUS of that step, never its name:

    TRAP (instance 16)                      GENUINE (this run)
    Skip when no .py changes    success     Skip when no .py changes    skipped
    Checkout                    skipped     Checkout                    success
    Install Python dev deps     skipped     Install Python dev deps     success
    just check-…                skipped     just check-…                success
    JOB CONCLUSION              success     JOB CONCLUSION              success

That step is a **complement notice**, guarded by the negation of the same
condition the real steps carry. It can only SUCCEED when `py_changed` is false,
so observing it `skipped` is positive evidence that `py_changed` was TRUE and
the real command ran. Reading its presence — rather than its status — as the
trap inverts the signal and discards a green that was honestly earned.

The failure this would cause is the mirror of instance 16's and no less costly:
16 makes you accept a check that never ran, 24 makes you reject a check that
did, and then hunt for a defect that is not there. In this session it would have
thrown away the one piece of evidence that actually certified the change — the
same run's `check-vendor-manifest` executing and passing, which is what proves a
pin bump and its vendored source stayed in lockstep.

A second, subtler half sits in the same run. `Install canonical worktree pack`
is `success` in `check-shell-quality` and `skipped` in `check-vendor-manifest`.
Both are correct: only the job that INSPECTS the pack needs it installed, and
that job having it is the fix for `livespec-dev-tooling-y6e2` holding. So the
same step name, with opposite conclusions, is right in both places. **A step
name plus a conclusion is still not a verdict — you need to know whether THAT
job's check depends on THAT step.**

**Counter-move:** when reading a step list, name the step that runs the command
(`just <target>`) and require it to be `success`. Treat every `if:`-guarded
scaffolding step as uninterpretable in isolation, because a guard and its
complement produce opposite conclusions from the same true condition. The
question is never "is there a skip here" — there is always a skip somewhere —
but "did the command step execute". If you cannot say which step runs the
command, you are not yet reading the step list, only scanning it.

### 25. `--dry-run` is scoped to a verb list, and `--help` does not say so

Every other entry here is about misreading a signal. This one is about a flag
that silently is not the flag you think, and it is the only entry whose cost was
paid in host state rather than in a wrong conclusion.

`sudo systemctl preset-all --dry-run` was written into a shipped acceptance
criterion as the NEGATIVE CONTROL proving a unit removal was durable. Run on the
shared factory host on 2026-08-04, it did not print a plan — it **applied vendor
presets host-wide**, creating 48 enablement symlinks including `nginx`, `vault`,
`podman`, `ssh` and a deliberately-disabled runner supervisor. Nothing started,
so the damage was to NEXT-BOOT enablement; 46 were reverted, and `ssh.service`
plus the `sshd.service` alias were deliberately left enabled because a lockout on
a remote host is not recoverable.

**It is documented behaviour, not a bug, which is exactly why it is dangerous.**
Measured on systemd **257 (257.9-0ubuntu2.5)**. `man systemctl` scopes the flag:

> `--dry-run` — Just print what would be done. Currently supported by verbs
> halt, poweroff, reboot, kexec, suspend, hibernate, hybrid-sleep,
> suspend-then-hibernate, default, rescue, emergency, and exit.

That list is **twelve** verbs and `preset-all` is not among them. The flag is
nevertheless accepted without error and exits 0. And `systemctl --help` advertises
it with **no scope caveat at all**:

    --dry-run           Only print what would be done

So the two sources disagree, and the one an operator reaches for first is the one
that omits the constraint. A flag that is silently ignored on the verb you are
using is indistinguishable from a flag that worked — until you inspect the state
it was supposed not to touch.

**Counter-move:** before trusting any `--dry-run`, `--check`, `-n` or
`--what-if`, confirm the flag is honoured *by the specific subcommand*, from the
man page rather than `--help`; treat the absence of a caveat in short help as no
evidence. Prefer a control that is read-only **by construction** over one that is
read-only by flag. Here that replacement already existed and is strictly stronger:

    find /etc/systemd/system /run/systemd/system /usr/lib/systemd/system \
         /lib/systemd/system -name '<pattern>'
    systemctl list-unit-files | grep -E '<pattern>'

It asserts nothing is left for ANY preset run to enable, rather than predicting
what one particular preset run would do — and it cannot mutate, whatever the
verb. Demonstrated fail-capable against a synthetic unit planted in a scratch
root: 2 matches with it present (the unit file AND its `.wants/` enablement
symlink), 0 once removed. **A control is not a control until it has been made to
fail on demand** — the original was trusted because its name and its `--help`
line implied a behaviour nobody had tested. (Tracked as `livespec-opwqmy`.)

### 26. `pgrep -f <pattern>` matches the shell running it, so the scan finds itself

The wait-loop version of this is already a standing rule. This entry records the
version that matters HERE: the same self-match inside a **verification**, where
it does not hang — it **fabricates evidence**.

Re-measuring the banked completion-evidence bullet *"the shared factory host
carries no CI listener or worker process"* on 2026-08-06, the check was:

    pgrep -a -f 'ci-runner|Runner.Listener|run-gate-jit'

It returned a hit. The hit was the wrapping shell's own `argv`, which contains
the pattern because the pattern was typed into it. Read literally, a bullet
asserting that no listener exists had just reported a listener — and the opposite
error is equally reachable: the same self-match makes a `pgrep | wc -l` guard
read `1` and conclude "still running" forever.

**Why it is worse in a verification than in a loop.** A self-matching wait-loop
hangs, which is loud and gets noticed. A self-matching verification returns
promptly with a plausible number, and the number is about a security-relevant
property nobody re-checks. Nothing distinguishes it from a true positive.

**Counter-move:** never let the needle appear in the scanning process's own
command line. Assemble the pattern at runtime inside a script file
(`"ci-" + "runner"`), exclude your own PID and PPID, and pair it with a
**positive control** — a needle you know matches — so an empty result is proved
discriminating rather than merely empty:

    CONTROL (processes matching 'systemd'): 16 - scan is not vacuous
    listener/worker process hits: 0

Where the question is "is anything running here", prefer a source that cannot
self-match at all: `systemctl show <slice> -p TasksCurrent` returning
`TasksCurrent=0` is an empty cgroup, and no phrasing of the query can put your
own shell inside it.

### 27. A clock read once per session stamps every later measurement with a stale time

The rule *"`date -u` before dating any measurement"* is already in this fleet's
records — it was added after an inherited session date made six-minute-old CI
jobs look like a 26-hour stall. This entry is that same rule **failing on its own
second application**, which is why it earns a slot rather than a footnote.

A session read `date -u` at its start (`04:29:34Z`) and treated that as "now" for
the rest of its work. Seventy minutes later it wrote a note to the beads ledger,
read the record back, and found `updated_at: 2026-08-06T05:39:54Z` — an hour and
ten minutes "in the future". The obvious inference was a timezone defect: a
ledger stamping local CET while labelling the field `Z`. **Had that been true it
would have invalidated every gate comparison in the thread**, since the whole
method is comparing `updated_at` values across readings.

It was false. True UTC at that moment was `05:40:22Z`; the ledger was correct to
the second. The only stale value was the session's own idea of the time.

**The trap is that a session's felt duration is not its elapsed duration.** Tool
calls are fast, so a long session reads as a short one, and the start-of-session
clock feels current long after it is not.

**Counter-move:** re-run `date -u` **at the moment you stamp something**, not
once per session — and when a timestamp from an external system disagrees with
your expectation, re-measure your own clock BEFORE concluding the other system is
wrong. State session measurements as a range (`04:29Z–04:35Z`) rather than a
point, so a later reader can see how old they are.

### 28. A `mutants/` tree is DELIBERATELY WRONG source, and a backup snapshot puts one on a plausible path

Every other entry here concerns a signal that was stale, absent, or misread. This
one concerns source code that is **intentionally incorrect by design**, read as if
it were the contract.

Establishing what a check actually enforces, a reader opened
`livespec_dev_tooling/checks/no_todo_registry.py` and the path resolved to:

    /srv/arq-vps-root-snapshot/current/data/projects/livespec-dev-tooling/
      mutants/livespec_dev_tooling/checks/no_todo_registry.py

That is an ARQ **backup snapshot** of a **mutation-testing** tree. Two independent
hazards compound in one path:

- The snapshot root mirrors the real workspace layout, so
  `…/data/projects/<repo>/…` appears verbatim inside it. A recursive search from
  `/`, or any glob, surfaces it looking exactly like the real clone with a prefix.
- The `mutants/` subtree is generated by `mutmut`. Its whole purpose is to hold
  **deliberately mutated variants** of the logic under test.

Measured on the two files: canonical is **97 lines**, sha256 `3ec97165…`; the
mutants copy is **1730 lines**, sha256 `409ae936…`. The mutants copy carries a
`_mutmut_trampoline` that dispatches on `os.environ['MUTANT_UNDER_TEST']` and swaps
in a mutated body, and it contains **84** occurrences of the `TODO` token — dozens
of altered variants of the exact predicate the reader was trying to establish. A
mutation of `==` to `!=`, or of the compared string, is precisely what such a tree
is built to contain.

**Why it survives a careful reader:** the docstring at the top of a mutmut-generated
file is copied intact from the original, so it reads as authoritative and describes
the real contract. The mutation is in the body, far below. It was reported as "close
enough to be believable" — which is the design goal of a mutant, not a coincidence.

**Counter-move:** read committed contracts with
`git show origin/master:<path>` from the real clone, never from a filesystem path —
that form cannot resolve into a snapshot, a vendored copy, or a generated tree,
because it resolves through git's object store rather than the filesystem. When a
filesystem read is unavoidable, treat these as disqualifying path segments:
`mutants/`, `.mutmut-cache/`, any snapshot or backup root (`/srv/*-snapshot/`,
`.arq*`, `*/current/data/projects/…`), and `_vendor/`. A cheap tell is size: a
mutmut-generated module is roughly an order of magnitude longer than its original
(here 18×), so a file far larger than the thing you expected to read is a signal to
re-derive the path before reading the content.

(Recorded from a supervisor's own near-miss on this thread, self-reported and then
verified independently against both files before being written up here.)

### 29. A parent record's `updated_at` does not aggregate its children

Every other entry here concerns reading the wrong SOURCE. This one concerns
reading the right source's wrong FIELD — a timestamp that is real, current, and
accurate, and still answers a different question than the one being asked.

A thread had spent eleven consecutive readings establishing that an external gate
had not moved, using each blocking item's `updated_at` as the motion test. On the
twelfth reading the gate's critical-path item measured:

    hl-r6hihy   active   P2   updated_at 2026-08-06T10:48:44Z

Five days stale, on a day when everything else in the census was also unmoved. The
natural reading — and the one the thread's own eleven-reading method invited — is
*that lane is idle too*.

It was the opposite. Enumerating the subtree found **six of seven children closed
across four separate days**, and the seventh (`hl-r6hihy.7`) carrying
`updated_at 2026-08-11T06:29:47Z` — updated roughly ninety seconds before the
census read it. The lane was not merely active; it was the single busiest thing in
the repository at that moment.

**The mechanism is that beads (like most trackers) stamps `updated_at` on writes to
THAT record.** Closing a child writes the child. Nothing touches the parent, so a
parent can sit untouched for days while its subtree is delivered underneath it. The
field is not lying — it faithfully reports when the parent row last changed. It
simply is not a subtree activity measure, and nothing in its name says so.

**Why it survives a careful reader:** the value is fresh-looking data from the
authoritative store, it agrees with every other reading in the census, and the
census method itself had been validated over eleven prior runs. Corroboration from
a method that shares the defect is not corroboration.

**Counter-move:** when asking "has this lane moved?", enumerate the SUBTREE, never
the parent — `bd list --all -n 0`, then filter on the id prefix (`<id>` and
`<id>.*`), and take the MAXIMUM `updated_at` across the set. The generalisation
beyond ledgers: before using any timestamp as an activity signal, ask *what write
sets this field?* If the answer is "writes to this row" but the question is about a
tree, a directory, an epic, or any other container, the field cannot answer it. The
same trap sits in `git log -1 <dir>` on a path whose children moved in commits that
did not touch the directory entry, and in a container image's created-at versus its
layers'.

(Observed 2026-08-11 by the `livespec-ci-on-hetzner` plan, on the twelfth reading of
a gate whose eleven prior readings had all been correct.)

### 30. A CONFLICTED pull request produces zero workflow runs, which looks exactly like a broken trigger

An empty run list is a true answer to the wrong question. Run-existence is not
the signal for "did the trigger fire".

Live-exercising a just-shipped `auto-enable-merge` change, PR #2148 in `livespec`
produced no `pull_request` workflow runs at all. The natural reading was that the
newly-landed logic had broken the trigger — a serious defect in a gate that had
merged minutes earlier.

It had not. The pull request was `mergeable=false` / `mergeable_state=dirty`, a
conflict against master. **GitHub cannot compute a merge ref for a conflicted
pull request, and `pull_request` workflows run against that merge ref**, so no
run object is created at all. That is why `opened`, `reopened` AND `synchronize`
each produced nothing — three trigger types failing identically, which reads as
strong evidence of a broken workflow and is nothing of the kind. Rebasing and
resolving the conflict caused a run to appear immediately, which is what
established causation rather than correlation.

The first diagnosis — "repo-wide Actions scheduling delay" — was reached by
querying `runs?head_sha=`, then `runs?branch=`, then an unfiltered repo-wide
listing, all of which agreed. On a quiet repo the unfiltered listing corroborates
"nothing scheduled recently" perfectly well, and the agreement of three queries
felt like triangulation. All three answered the same wrong question.

**The counter-move:** before concluding a workflow did not fire, read the pull
request's `mergeable` and `mergeable_state`. A `dirty` state explains zero runs
completely and must be excluded first. Note `mergeable` is computed
asynchronously and reads `null` on a fresh query — re-read until it resolves
rather than treating `null` as false, which would recreate the same error one
level down.

The smaller lesson is the one worth carrying: **that wrong diagnosis was stated
WITH a positive control attached, and was still wrong.** The queries were sound
and could return results; they simply did not measure trigger-firing. A positive
control establishes that a query CAN return a result. It does not establish that
the query answers the question being asked. Reviewing a proposal, the same
distinction appears as the shared-instrument defect class in
`.ai/spec-proposal-review.md`.

### 31. `gh api -q` on a 404 prints `null`, which is NOT empty, so every row passes

A failed lookup that still produces output defeats an emptiness test, and a
sweep built on one reports the same verdict for every repository it visits —
including the verdict you were hoping for.

Sweeping all thirteen `.livespec-fleet-manifest.jsonc` repositories to establish
which are generated from the copier template, the probe was
`ans="$(gh api "repos/$OWNER/$r/contents/.copier-answers.yml" -q '.name' 2>/dev/null)"`,
classified as a consumer when `$ans` was non-empty. Every one of the thirteen
came back a consumer.

On a 404, `gh api` still prints the error body — `{"message":"Not Found", ...}` —
and `-q '.name'` is a jq filter over THAT object. jq emits `null` for a missing
key, so `$ans` is the four-character string `null`. Non-empty. `2>/dev/null`
suppressed the human-readable `gh: Not Found (HTTP 404)` on stderr, removing the
one signal that would have shown the lookup failing.

What exposed it was a CONTRADICTION rather than suspicion: the sweep called
`livespec` itself a template consumer, while a `git ls-tree origin/master`
moments earlier had found no `.copier-answers.yml` there. Two sources
disagreeing is what forced the re-check. Had the wrong answer been merely
plausible everywhere — as it was for the other twelve — it would have shipped.

**The counter-move:** branch on the command's EXIT STATUS, not on whether its
output is empty:

```sh
if gh api "repos/$OWNER/$r/contents/$PATH" >/dev/null 2>&1; then ...
```

Re-run that way, the true answer was two consumers, not thirteen. Note the
original conclusion drawn from a three-repository spot-check had been RIGHT;
the thirteen-repository sweep meant to upgrade it from inference to measurement
is what nearly replaced a correct claim with a false one. A verification step
is not automatically safer than the claim it audits.

The generalisation is the part worth carrying: **any wrapper that prints a
structured error to stdout turns "no output" into an unreliable proxy for
"not found".** The same shape sits behind instance 22, where a ref that does not
exist returns empty and reads as out-of-scope; here the polarity is inverted —
absence returns something — which is worse, because the tell is a passing test
rather than a suspicious blank.

### 32. A watcher whose filter can never match is silent, and silence reads as "not finished yet"

Every other instance here is a green signal that carried no information. This
one is the same failure wearing the opposite face: NO signal, read as "the thing
I am waiting for has not happened yet."

Watching a merge commit's CI, the query was

```sh
gh run list --workflow CI --branch master --limit 12 \
  --json headSha,status,conclusion \
  --jq --arg s "$SHA" '.[] | select(.headSha | startswith($s)) | "\(.status) \(.conclusion)"'
```

The `--jq` option takes ONE expression and does not implement jq's own `--arg`.
So `--arg` was consumed AS the expression, `s` and the SHA became stray
positional arguments, and the intended filter was never applied. The command
matched nothing and exited without complaint. The watcher then ran its full
forty-minute timeout reporting nothing at all — while the run it was watching had
already completed SUCCESSFULLY within the first few minutes.

What makes this worth its own entry rather than a footnote to instance 31 is the
tell, not the cause. In 31 a failed lookup PRINTS `null` and so defeats an
emptiness test. Here the failed lookup prints nothing — which is exactly what a
correctly-working watcher looks like while it waits. **A filter that cannot match
and a job that has not finished produce byte-identical output: none.** There is
no moment at which the broken watcher looks broken. It looked most trustworthy
precisely when it was most wrong, because patient silence is what a watcher is
supposed to do.

Nothing about the forty quiet minutes invited suspicion. What exposed it was
reading the underlying state directly for an unrelated reason and finding the run
had been green the whole time.

**The counter-move, in two parts.** First, keep the value out of the filter's
argument list — interpolate it into the expression, or emit plain output and
filter in the shell, where an unsupported flag fails loudly instead of quietly:

```sh
gh run list --workflow CI --branch master --limit 12 \
  --json headSha,status,conclusion \
  --jq '.[] | "\(.headSha) \(.status) \(.conclusion)"' | grep "^$SHA"
```

Second, and the part that generalises past this one flag: **a watcher's silence
is not an observation.** Before concluding from quiet that something has not
happened, read the underlying state once, directly. A watcher reports the
transitions it can see; it cannot report that its own filter is incapable of
seeing any.

The habit this protects is the one instance 23 names — a query returning the
answer you expected is the least likely to be audited. Prolonged silence from a
watcher IS the expected answer while you are waiting, and it earns a direct check
for exactly that reason.

### 33. A well-formed filter over the WRONG STATE-SPACE, where success is what makes the event invisible

Instance 32 is a filter that could never match because it was malformed. This is
its harder sibling: a filter that is perfectly well-formed, matches exactly what
it was written to match, and still cannot observe the thing you care about —
because it asks about the wrong state.

Watching a cross-repo pin fan-out, the watcher polled every 120 seconds:

```sh
gh pr list -R "thewoolleyman/$repo" --state open --limit 10 --json number,title
```

The question it was built to answer was **"did a bump happen?"** The question it
actually asked was **"is a bump pull request open right now?"** Those coincide
only for a pull request that lingers.

Five bump PRs opened and merged in one window. Their lifetimes were 62 seconds,
2m22s, 3m26s, and 6m47s, against a 120-second poll. A merged pull request is
invisible to `--state open` permanently, and a short-lived one can open and
merge entirely between two polls. The watcher reported nothing, and its silence
was indistinguishable from "the fan-out has not started" — which is what got
written into a session summary as fact.

Measured over the identical window:

| query | rows |
|---|---|
| org-wide search, all states | 5 (all 5 merged) |
| per-repo `--state open` | 0 |

**The property that makes this class nasty: success is what hides the event.** A
bump that lands cleanly spends almost no time in the polled state. A bump that
stalls — blocked, conflicted, waiting on review — sits in `open` for hours and is
seen immediately. So the watcher reliably reports the failures and reliably
misses the successes, which is precisely inverted from what a health check
should do. Speed and health made the system less observable, not more.

**The counter-move is not a better filter.** It is to stop watching the event:

```sh
# Not: "is there an open PR?" — a transient a poll interval can straddle.
# Instead: "what does master actually say?" — a durable end state.
git -C "$repo" fetch origin master --quiet
git -C "$repo" show origin/master:pyproject.toml | grep 'livespec-dev-tooling = {'
```

**When you can watch the durable consequence instead of the transient event that
produces it, watch the consequence.** A pull request is a transient; a pin on
`master` is a fact that stays true and cannot be missed by arriving late. The
end-state form also needs no API call, so it carries no rate-limit budget and no
state-visibility semantics to get wrong.

Both watcher failures recorded on 2026-08-19 — this one and instance 32 — came
from monitoring events. Neither would have been possible watching state.

The generalisation reaches past watchers. Any check that samples a system
periodically is really asking "was the system in state X at the moment I
looked?", and that is only a proxy for "did X happen" when X is durable. Before
trusting a periodic check, ask **how long the thing being detected remains
detectable** — and if that interval can be shorter than the sampling period,
the check cannot answer the question no matter how correct its filter is.

### 34. A rule inferred from behaviour observed DURING A DEGRADED WINDOW, which then outlives the degradation and blocks the repaired behaviour

Every other instance here is a reader drawing a wrong conclusion from a
right-looking signal. This one is worse, because the wrong conclusion gets
COMMITTED — frozen into an enforcement rule that then contradicts the system it
governs, long after the evidence for it expired.

`livespec-overseer` guards its workflow files: any change under
`.github/workflows/` needs a reviewed, per-change exemption declaration. The
automated pin-bump lane cannot author one, so the guard carries a narrow
allowance — a bump passes without a declaration when EVERY altered line is a
version pin:

```sh
[[ "$line" =~ ^[+-][[:space:]]*uses:[[:space:]]*[^[:space:]]+@v[0-9]+\.[0-9]+\.[0-9]+$ ]] && return 0
[[ "$line" =~ ^[+-][[:space:]]*image:[[:space:]]*[^[:space:]]+:[a-z]+-v[0-9]+\.[0-9]+\.[0-9]+$ ]] && return 0
```

The allowance documents its own basis, which is the part that matters:

```
# Measured 2026-08-19/20 over the four most recent bumps (27404e6, a05cbb1,
# cf916d5, 7d82d5d): every one alters ONLY these two line shapes.
```

That is careful work. Four real bumps, named by SHA, checked rather than
assumed. And it produced a rule that froze the repo.

**Because the window it sampled was broken.** Throughout 2026-08-19/20 the
canonical-CI reconciler `ci_yaml_canonical_reconcile` hard-failed the bump job
on every consumer that had a slug to adopt (`livespec-s43svm.34`). A bump that
wrote a non-pin line into `ci.yml` was not rare in that window — it was
*mechanically impossible*. The four samples could not have shown anything but
pin lines. When the reconciler was repaired, the very first wave in which it
wrote its aggregate line

```
+          just check-self-hosted-uv-lane || failed="$failed check-self-hosted-uv-lane"
```

failed the guard, and `livespec-overseer` alone stayed two releases behind while
the other seven Python consumers took the bump with the line auto-written.

**The trap is that the sample is accurate and the inference is still void.** No
amount of care in the measurement rescues it, and a larger sample would not have
helped — every bump in that window, not just four, was pin-only. The defect is
not sample size or sloppiness. It is that observed behaviour was treated as
specification while the producer of that behaviour was in a degraded state, so
the rule recorded a symptom of the outage as if it were a policy.

Note the second-order cost: the guard did not merely fail to notice the repair,
it actively PREVENTED it. A rule calibrated on a broken world becomes the thing
standing in the way once the world is fixed, and it presents as a legitimate
policy objection rather than as stale data — the guard's message is a correct
statement of its rule.

**Counter-move: derive an enforcement rule from the producer's SPECIFICATION or
its writer source, not from a sample of its output.** The reconciler's writer
defines exactly which line forms it can emit; that set is knowable by reading
it, is complete, and does not change when the reconciler is broken. A sample of
diffs is a measurement of the producer's current health as much as of its
contract, and the two are indistinguishable from the outside.

When you must calibrate from observation because no specification is reachable,
record the assumption as a hypothesis with its window (`observed over <dates>;
re-derive if the producer changes`) rather than as a settled invariant — and
before trusting any such rule, ask **was the thing I sampled fully operational
while I sampled it?** A quiet period is exactly as consistent with a broken
producer as with a producer that never does the thing.

The general form, which reaches past guards: any threshold, allowlist,
timeout, or baseline fitted to observed traffic inherits the health of the
system that generated that traffic. Fitting a rule during an outage bakes the
outage into the rule.

### 35. The plugin cache holds many builds of one file, and reading the wrong one is the DEFAULT

Every other instance here is a signal misread. This one is a *file* misread —
the source was real, correct-looking code that simply was not the code running.

While characterising the shipped `github_rate_limit_guard` hook, a session read
it out of the plugin cache, quoted its matcher, and generalised a mechanism from
it. The quoted code was genuine and parsed fine. It was also two builds stale,
and the conclusion drawn from it was wrong.

**The base rate is the finding.** Hashing every copy of that one hook on the
host:

| Variant | Copies | Status |
|---|---|---|
| `bcc352abbc4b196b049226b3e8a9c512` | 7 | stale |
| `c52db7ef2b2686b4e4916b4b68eb57cd` | 5 | stale |
| `db57c8eb7fb356ea86bee87c346bc42b` | 3 | **RUNNING** |

Fifteen copies, three variants, the live one is **3 of 15** — a blind pick is
**wrong 80% of the time**. This is not a cache that occasionally goes stale. It
is an archive of every build the host has ever installed, in which the current
one is a minority.

**Two DIFFERENT hazards, and they need different remedies.** Measured on the
same tree in the same minute by two sessions:

- **A glob or `ls` is STABLE and BIASED.** The shell sorts a glob (POSIX
  requires it), and `.` (0x2E) sorts before digits and letters, so semver-named
  directories land ahead of every hash-named build. On this host `0.5.2/`,
  `0.5.5/`, `0.5.7/` come first — and all three are stale variants. The bias is
  reproducible, learnable, and reliably wrong.
- **`find` is UNSTABLE.** It does not sort at all; it yields directory-entry
  order, which mutates as builds are added. The identical `find … | head -1`
  returned three different first results across two sessions on one machine
  within two hours — a stale hash build, then the marketplace copy, then
  `0.5.2/` — because a sibling release added a directory mid-session.

Conflating the two costs the reader the remedy. An operator who reaches for
`ls`, reads only the instability warning, tests it, sees stable ordering, and
concludes the warning does not apply has walked into the *other* failure by way
of the correct half of the advice.

**What makes it hard to catch is that nothing looks wrong.** The stale build is
real code with plausible behaviour, and its predictions matched every denial the
session had actually observed. The two accounts only diverged when a second
agent quoted different source, and even then it took hashing to settle which was
live. Neither agent could have detected it alone.

**Counter-move: never let the filesystem choose the build.** The running build
is named in the session's own startup output; hash the candidate against it, or
confirm every candidate agrees:

```bash
find ~/.claude/plugins -name '<hook>.py' -exec md5sum {} \; | awk '{print $1}' | sort | uniq -c
```

One line, and it converts archaeology into evidence — it reports the variant
count directly, so a result of `1` means any copy is safe to read and anything
higher means you must identify the live one before quoting it. The discriminator
does not care which command found the file, so it survives both hazards above.

**The general form:** any tool that installs versioned artifacts side by side —
plugin caches, wheel caches, container layer stores, vendored dependency trees —
turns "read the source" into "sample the source". Reading code is only evidence
about a running system when you have established that the bytes you read are the
bytes that run.

### 36. A PER-REPO endpoint answering a FLEET question, and a service checked on the wrong HOST

Two errors that compounded into a maintainer escalation, both of which read as
diligence rather than as mistakes.

A foreman was reconciling two claims about the fleet's self-hosted runners: this
epic's records said **482**, and its own live query said **75**. It reported the
discrepancy as unresolved and recommended nobody act on either number.

**Neither number was wrong.** 75 was `livespec`'s row; 482 was the eight-repo
fleet total; the eight rows sum to exactly 482. The query
`gh api repos/thewoolleyman/livespec/actions/runners` is a **per-repository**
endpoint, and its `total_count` field is named as though it were a total of
something the reader chose. It is not — it totals that one repo. The right
source for "how many runners does the FLEET have" is eight calls and a sum, or a
fleet inventory; a single repo's endpoint cannot answer it and does not say so.

**Then the corroborating check was run on the wrong machine.** To test the peer
session's claim that `ci-runner-rate-replenisher.service` was re-minting runners,
the foreman ran `systemctl` **locally** — on `vmi3006760`, where the foreman
happens to run — and reported "that service isn't running on this machine." True,
and irrelevant: the service lived on `poweredge-xubuntu`. It was `active` and had
been for eight days. Absence on the host you happen to occupy is not absence.

**Both errors share a shape: the query was well-formed, executed cleanly, and
returned a real number about a real thing — just not the thing being asked
about.** There is no error to notice. A wrong-scope answer looks exactly like a
right one, which is why it survived three sessions and reached the maintainer as
"work out what's actually true before anyone acts."

A third conflation was found while verifying, and it is the one still live: a
repo's `total_count` **mixes populations and moves**. ARC/k3s runners register
with an EMPTY label array and autoscale, so `livespec` read 75, then 82, then 80
within seconds — 75 stranded podman-era registrations plus a churning ARC count.
Two readings minutes apart produce an apparent discrepancy that is only
autoscaling.

**Counter-move:** before comparing two counts, state the SCOPE of each in words
("this is one repo's; that is eight repos' sum") — if you cannot, you are not yet
comparing them. For any claim about a service, a file, or a process, name the
HOST it is claimed to be on and run the check **there**, over ssh if needed;
never let the session's own machine stand in for the machine under discussion.
And when a count can contain more than one population, split it by a
distinguishing field before reporting a total. `livespec-s43svm.42` exists to
make this particular family structurally unavailable, by ensuring the only
sanctioned way to answer "how many runners" prints scope, population, host, cap
and fleet total together.

### 37. A point-in-time listing of an EPHEMERAL population, read as a structural property

Every query here was well-formed. This one was well-formed, hit the right
endpoint, and returned a TRUE result — and the inference drawn from it was still
wrong, because the population being listed does not persist.

A post-cutover audit asked whether ARC-provisioned CI runners can carry the
labels the specification requires. It queried
`repos/thewoolleyman/livespec-console-beads-fabro/actions/runners`, got back
sixteen podman-era runners and no ARC members, and concluded that **"ARC runners
do not appear in the repository runners API at all"** — a structural claim, and
the load-bearing evidence in a filed spec proposal.

They do appear. Measured on `thewoolleyman/livespec` while a job was running:

```json
{"total_count":1,"runners":[{"id":31096,
  "name":"livespec-local-ci-k3s-d4j8r-runner-xndz6",
  "status":"offline","busy":false,"labels":[]}]}
```

**Why the first read saw nothing, and why that was not a defect.** An ARC scale
set runs `minRunners: 0` and its registrations are ephemeral — one job, then
deregister. A member exists in that listing only while it is serving work. The
audit happened to query a repository at a moment when no job was running. Three
consecutive reads of the same endpoint during a single CI run returned three
runners, then two, then one.

**The asymmetry is what made it convincing.** The two populations in that one
listing have completely different lifetimes:

| Population | Lifetime | Visible when idle? |
|---|---|---|
| podman-era JIT registrations | permanent until deleted | **yes** — all 482 |
| ARC scale-set registrations | one job, then gone | **no** |

So the endpoint returned a full, confident, non-empty answer — sixteen rows —
that was complete about the permanent population and silent about the ephemeral
one. An empty result invites suspicion. A *populated* result does not, and this
one was populated by exactly the runners the reader was not asking about.

**What no amount of re-running would have fixed.** Repeating the query is the
standard counter-move for a flaky read, and it is useless here: the same repo
idle at 3pm and idle at 4pm returns the same wrong answer twice, and two
agreeing reads feel like corroboration. The defect is not in the sampling rate.
It is that a listing answers *"which members are registered RIGHT NOW"*, and the
question asked was *"what can this pool's members do"* — a property of the
mechanism, not of the current instant.

**Counter-move: before generalising from a listing, establish the lifetime of
what it lists.** One question settles it — *would this row still be here if
nothing were happening?* If no, the listing is a sample of a moving population
and cannot support a structural claim, however many times it agrees with itself.
Sample it while the population is at its maximum (here: during a job), or read
the mechanism's own definition (`minRunners`, ephemeral registration) instead of
its runtime shadow.

> **Neighbour, not duplicate.** Entry 36 above also lands on an ARC runner
> listing, and reaches it from a different direction: it is about SCOPE (a
> per-repo `total_count` read as a fleet total) and notes in passing that the
> count moves because ARC autoscales. This entry is about LIFETIME — the
> inference from a listing's contents to a STRUCTURAL property of the
> mechanism. Both were found within an hour of each other by two sessions who
> did not share a query. That two independent readings of one endpoint went
> wrong in two unrelated ways is itself the argument for reading a listing's
> definition rather than its output.

**The general form:** any registry of transient participants — ephemeral CI
runners, autoscaled workers, connection pools, service-mesh endpoints, container
task lists, leases — will show an empty or partial set at rest. Absence there is
evidence about the moment, never about the mechanism. And when a transient and a
durable population share one listing, the durable one supplies enough rows to
make the reading look complete.


## Why this file exists in livespec CORE

These instances span the repositories `livespec`,
`livespec-dev-tooling`, `livespec-runtime`,
`livespec-orchestrator-beads-fabro`,
`livespec-console-beads-fabro`, `livespec-overseer`, `openbrain` and
`homelab` — and core owns
fleet-level facts. A lesson filed only in one tenant would not be read
by an agent working in another, which is precisely where most of these happened.
The last two entered the list via instance 22, which is fitting: they were
mis-read precisely BECAUSE they sit outside the repos an operator handles daily.

## Related standing rules

This is the same instinct behind two rules already in force:

- **"Done" means rolled out and exercised live** — never merely merged +
  CI-green + AI-accepted.
- **The non-behavior-bearing acceptance form** — discharge by INDEPENDENT
  ADVERSARIAL REVIEW that re-derives claims against live state, rather than
  trusting the artifact, CI, or its author.

Both say: do not accept a signal from a source that could not have contradicted
you.
