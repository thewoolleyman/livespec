---
topic: master-green-tolerates-external-red
author: claude-opus-5-5 (livespec-dev-tooling bqnzcm plan seat)
created_at: 2026-11-15T23:25:15Z
---

## Proposal: The master-green gate tolerates an external red, on evidence and for at most one day

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Make the fleet's master-green gate distinguish a defect red from an external red (forge, network or third-party outage). It is keyed only on transport-layer evidence recorded as {dependency, kind, evidence} and fails closed when no record exists. While master's only red is external, the gate warns and admits every commit and push, leaving the red verdicts on master and each PR's own checks intact. The tolerance ends when master reads green, or after 24 hours with a maintainer alert. Add three scenarios, and name this as the one evidence-keyed exception to the no-lever rule.

### Motivation

Maintainer, verbatim, 2026-11-15 ~23:1x-23:5xZ (recorded in the plan-scope-event on livespec-dev-tooling-6tgd2z, the copy marked SUPERSEDES): "we want some easy way to incorporate this concept into future situations that are the same, where master is read for something external, and we don't want to stop everything completely"; "it should be designed flexibly so it can handle any sort of external outage that meets this category of failure. Whether it's any GitHub failure or something else, it could be that the internet is down. It could be anything else: a third-party tool is down or something that we rely on is down but we can still do commits and push things through. That's the category of error that we care about: things that are not our own problem to fix or cannot be fixed immediately for some reason external to us"; and "Make the time limit like a day. Hopefully all external errors can be resolved within a day". From another seat, pasted by the maintainer: "The whole point is to not let failures stack up" / "But this failure is external. It's not due to anything we can fix". Without this, an outage nobody in the fleet can fix stops every commit and push, so failures stack up behind it. The coordinator's design (deterministic, no LLM in the gate, fail closed, evidence an agent cannot fabricate) keeps livespec's ci-gate-discipline ban on levers intact. The companion implementing proposal is livespec-dev-tooling master-green-tolerates-external-red.

### Proposed Changes

In `non-functional-requirements.md`, immediately after the **CI as a merge gate** paragraphs and before **Merge queue on organization-owned repositories**, add:

**The master-green gate tolerates an external red, on evidence and for at most one day.** Every fleet repository's master-green gate (the shared gate that refuses a local commit or push while `master` is red) MUST distinguish a DEFECT red from an EXTERNAL red, deterministically and with no LLM call in the gate.

- An EXTERNAL failure is one whose cause lies outside the repository and its own configuration and which the repository cannot fix now. Examples: a forge API or service failure (rate limit or quota exhaustion, a 5xx response, an outage); the network being unreachable (DNS failure, connect failure or timeout to a host the fleet does not run); a third-party service or tool the repository depends on being down. A failure of a credential or permission the fleet itself configures (a 401 or 403 on its own token or App), a test, lint or type failure, and a failure of the repository's own configuration MUST NOT be classified external; each is a DEFECT.
- The classification MUST be keyed on structured evidence that the transport or HTTP layer produced at the moment of failure, recorded as `{dependency, kind, evidence}`. It MUST NOT be keyed on a flag, environment variable, label, comment or any other input an agent can set.
- The master-green gate MUST fail closed: a red gating job on `master` that carries no external-cause record is a DEFECT, and the gate MUST block exactly as it does without this rule.
- While every red gating job on `master`'s newest completed run carries an external-cause record, the gate MUST warn, naming each dependency and kind, and MUST NOT block a commit or push, for every change, not only for a repair. The red verdict of each failing job and of the all-green gate job MUST remain red on `master`; the tolerance changes only the local gate's decision, so nothing passes vacuously. Each pull request's own required checks MUST still bind its merge.
- The tolerance MUST end when `master`'s gating push run reads green, or when `master` has been red with external-only causes continuously for 24 hours, whichever comes first. At the 24-hour limit the gate MUST block again and the maintainer MUST be alerted through the repository's needs-attention signal, so a long outage is surfaced and never silent.
- This rule does not change the master-health reconciler's own flake-or-infrastructure classification, which governs reverts, not the local gate.

This rule is the one sanctioned exception to the ordinary no-lever rule for CI-green gates, and it is keyed on evidence no agent can produce, never on a lever. After ratification, `.ai/ci-gate-discipline.md` MUST be updated in the same change set as the implementation to name this exception and its evidence key.

Add to `scenarios.md`, beside "A red master heals by revert by default, or through a progressing fix-forward":

## The master-green gate admits work while master is red only for an external cause

```gherkin
Given the newest completed run on master is red
And every failing gating job carries a transport-layer external-cause record naming its dependency and kind
When an agent commits or pushes any change
Then the master-green gate warns, naming each external dependency and kind, and does not block
And the failing jobs and the all-green gate job still read red on master
And each pull request's own required checks still bind its merge
```

## The master-green gate blocks a red master with no external-cause record

```gherkin
Given the newest completed run on master is red
And one failing gating job carries no external-cause record
When an agent commits or pushes any change
Then the master-green gate blocks, naming that job as a defect
```

## The master-green gate's external tolerance ends after one day

```gherkin
Given master has been red with only external-cause records for 24 hours without its gating push run reading green
When an agent commits or pushes any change
Then the master-green gate blocks
And the maintainer is alerted through the needs-attention signal
```

Realization, namely the shared helper, how each gating job publishes its record, and how the gate reads it, belongs to livespec-dev-tooling's companion proposal master-green-tolerates-external-red, not to core. Any heading-coverage rows the new scenario headings owe MUST be co-edited in the revise commit.
