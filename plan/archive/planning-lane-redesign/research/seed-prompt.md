# planning-lane-redesign — seed prompt

Captured 2026-08-04 from a maintainer session in the livespec repo
(session "livespec-plan-redesign"). Ledger anchor: livespec epic
`livespec-zsn2xh` (cited read-only; status lives in the ledger, never
here). This document records the maintainer's ask and the context that
prompted it. The agent-side analysis is in `brainstorm.md`; the
decisions the maintainer made in the same session are in
`maintainer-rulings.md`.

## Triggering context — the foreman post-mortem

The livespec-overseer foreman effort closed its epic and archived its
plan while roughly 60% of the original seed's requirements were never
built. The post-mortem (delivered by the foreman-track supervisor in
the livespec-overseer repo) found:

- Requirement 5 (the consensus panel) was fully designed in
  `plan/foreman/research/brainstorm.md`, deliberately deferred out of
  v1 scope on the record — and then the deferral was lost, because the
  deferral lived in prose while completion was measured in the ledger.
- Phases C, D, and E existed only as prose bullets. They were never cut
  into ledger items, so every completion check ("did we do what the
  epic said?") passed while none asked "does the epic say what was
  asked?".
- The archiving supervisor never read the seed across an entire session
  that closed the epic and archived the plan.
- Independently: no test ever executed a shipped artifact — two
  executables raised `ModuleNotFoundError` before any logic ran,
  despite 983 passing tests and 100% coverage (fixed since by an
  execute-every-binary gate, released in livespec-overseer v0.27.5).

## The maintainer's ask (near-verbatim)

> I think that our approach of storing the plan documents in Markdown
> may be counterproductive. plan docs / handoff / supervisor-handoff
> etc.
>
> Reasons:
>
> 1. As the above shows, it is easy for the ledger to get out of sync
>    with the Markdown and just forget about things.
> 2. To write any handoff doc, there needs to be a full work tree and
>    CI run and pull request and merge because we don't allow any
>    master edits or pushes from master or merges without PRs. This is
>    bad when agents need to quickly wrap up their handoff when they
>    are low on context. And can be catastrophic if CI is broken for
>    some reason or slow, or GitHub is down and we cannot even write
>    handoffs to continue working locally.
>
> But the other side of the benefit is it is good to keep the plans in
> source control so they are versioned. And it is also easy to paste
> just a link to a handoff doc rather than having to remember cryptic
> bead names.
>
> I think the sweet spot may be to still have the plan directory and
> some metadata there that clearly indicates all of the beads, an
> associated epic, etc. And possibly some of the original research
> items, such as the seed or other research that a human has done or
> done in conjunction with an LLM. But all actual planning and handoff
> must live in the ledger.

## The vocabulary complaint

The term "plan thread" was agent-coined during the planning-lane
design work and codified into contracts and a skill name
(`list-plan-threads`) without a maintainer naming decision. The
maintainer's verdict, verbatim: "OK I hate that, it's two words for
the same thing. 'plan thread'. Useless. I never approved that. Some
agent just made it up and started using it."

## The scoping-protocol constraint

When the agent proposed an archive gate stated as "every requirement
in the seed must trace to a ledger item — open, closed, or explicitly
deferred — and [a plan] cannot archive while one doesn't", the
maintainer pushed back:

> As for this — it's not as easy as you glibly claim — because there's
> no current standard or shape/protocol for seed or research docs in
> plans.

That objection is correct and load-bearing: research docs are freeform
prose, not even filename-uniform across live plans (one live plan has
a `seed-prompt.md`; another has only a `brainstorm.md`). Any gate over
"requirements in the seed" requires deciding an enumeration protocol
that does not currently exist. See `brainstorm.md` for the candidate
routes and `maintainer-rulings.md` for the direction chosen at
capture time.
