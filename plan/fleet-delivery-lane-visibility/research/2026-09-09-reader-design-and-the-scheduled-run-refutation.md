# The reader design, and the claim that had to be refuted first — 2026-09-09

Carrier `livespec-n33rwg.5`'s remaining half is a **reader** for the release-lane
watcher. Choosing its shape required first disproving a claim this repo's own
tooling asserts, which had already steered the design once.

## The refutation, because it changes which options exist

`.claude/skills/needs-attention-internal/SKILL.md` states:

> the rollup hangs off a COMMIT, so it cannot see a **scheduled** workflow's
> failure at all — that failure attaches to no commit.

**That is false.** A scheduled run attaches to the commit that was HEAD when it
fired, carried as its own `head_sha`. Measured 2026-09-08 against
`thewoolleyman/livespec`: `Pin freshness sweep` (`event: schedule`,
2026-09-07T13:06Z, `head_sha` `be290ffb…`) appears in that commit's
`checkSuites`, alongside two more `schedule`-triggered workflows:

```
conclusion   event      workflow
SUCCESS      schedule   Pin freshness sweep
SUCCESS      schedule   Release park freshness
SUCCESS      schedule   Release readiness
SUCCESS      push       CI
SUCCESS      push       Release Please
```

A first attempt queried `defaultBranchRef.target` — the current tip — and saw no
scheduled runs, which *looks* like confirmation of the blindness claim. It is
not: that HEAD was ten minutes old, so no scheduled run could yet exist for it.
Reading that as structural blindness would have been the ephemeral-population
trap — generalising a structural property from a point-in-time listing. The
control is to take a known scheduled run's `head_sha` and query *that* commit.

**What is actually true is narrower and has different consequences.** The run
attaches to a **past** commit, so a query against the current tip misses it —
not because the data is unreachable, but because the query looked at the wrong
commit. Depth needed, measured on `livespec`:

| Scheduled run | Commits behind HEAD |
|---|---:|
| 2026-09-07 | 38 |
| 2026-09-06 | 54 |
| 2026-09-05 | 95 |

Tracked as `livespec-n33rwg.8`.

## The three options, and why one is disqualified

**A — walk history in the one-call screen.** Add a selection walking N commits
and folding to latest-run-per-workflow. Verified working, but the required depth
is **repo-velocity-dependent**: 38 commits for yesterday on `livespec`, ~1 on a
quiet repo. **The disqualifier is the failure mode, not the cost.** On a busy day
the run falls out of the window and the reader reports green *because it saw
nothing*. That is a vacuous pass — a reader whose silence is not discriminating,
which is the exact defect this epic exists to remove. A history walk would make
the reader's trustworthiness a function of commit velocity.

**B — the watcher writes a durable signal; the reader reads that. RECOMMENDED.**
On a failing lane the watcher opens or updates a labelled issue in its own repo
and closes it on recovery. The reader adds one selection to the existing
one-call screen:

```graphql
issues(states: OPEN, labels: ["release-lane-red"], first: 5) {
  totalCount nodes { number title updatedAt }
}
```

Verified 2026-09-08: the query works across repos in a single call, and
**`hasIssuesEnabled` is true on all ten fleet members** (checked, not assumed;
`livespec-runtime` already carries 2 open issues, the rest zero). No history
walk, no per-repo loop, nothing for `github_rate_limit_guard` to deny.

Its decisive property is that **silence becomes meaningful**: the issue persists
while the lane is red, so "no open issue" is a positive statement of health
rather than an absence of evidence. This is the plan's own recorded lesson —
*watch the durable consequence, never the transient that produces it* — applied
to the watcher instead of rediscovered by it.

Costs, stated rather than glossed: the watcher gains `issues: write`; the
close-on-recovery path becomes state that can drift, so **it needs its own test,
not just the open path** — an alarm that never clears is as useless as one that
never fires.

**C — widen Signal 1 beyond the literal workflow name `CI`.** Cheap to describe,
but reading each repo's watcher run individually is the looped forge read the
guard denies, and the rollup cannot substitute. Not viable alone; at best a
complement to B.

## Why this mattered enough to check

The blindness claim made A look impossible and B look forced. B is still the
recommendation — but it is now chosen against a correct premise rather than a
false one. This is the **second** instrument in this plan found asserting
something false about release behaviour: `AGENTS.md`'s "`refactor:`/`perf:`
commits cut no release" was the first, and that one had already propagated into
two work-items as a design constraint before it was caught.

Both were caught by measuring instead of trusting; both were corrected at the
source rather than worked around. The pattern is the plan's own subject matter
turned on its own tooling.

## Related findings filed this session

- `livespec-n33rwg.8` — the false scheduled-run caveat, above.
- `livespec-n33rwg.9` — the release-pipeline Honeycomb trigger is enabled with
  telemetry landing yet read *Not Triggered* through five failed cuts, because it
  alerts on the transient run event rather than the standing state. The remedy
  installed after the v0.6.0–v0.6.4 incident did not fix the class it was
  installed for.
- `livespec-n33rwg.10` — acceptance written in an item's *description* is
  silently ungradeable, so **every child of this epic was undispatchable from
  the moment it was filed** and nothing said so until a dispatch was attempted.
