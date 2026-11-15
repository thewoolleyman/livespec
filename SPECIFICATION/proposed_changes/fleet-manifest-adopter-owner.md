---
topic: fleet-manifest-adopter-owner
author: claude-opus-5-5
created_at: 2026-11-15T01:51:14Z
---

## Proposal: Fleet manifest names adopter owners separately from the fleet owner

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

The fleet manifest's single top-level `owner` is today the account every reader prefixes onto BOTH `fleet`-array members and `adopters`-array entries (`<owner>/<repo>`). The spec never states the key, so nothing stops a reader from coupling the two populations. This proposal names the owner keys in §"Fleet membership contract": `owner` owns the `fleet` members only; a new optional top-level `adopter_owner` names the default owner of adopter repositories and defaults to `owner` when absent (so the current manifest stays valid unchanged); an optional per-adopter `owner` overrides `adopter_owner` for that one entry. It fixes the resolution order every manifest consumer MUST use, forbids building an adopter name from `owner` alone once either adopter key is present, and records the adoption ordering: readers resolve the new keys before the manifest sets them, and the manifest carries `adopter_owner` before `owner` changes. The enumerations of an adopter entry's keys (§"Fleet membership contract" **Adopters** and §"Conformance Pattern" profiles paragraph) and the **Discovery safety net** rule's "fleet owner" are updated in lockstep, and one contributor-facing scenario is added to §"Scenarios".

### Motivation

The stale-base-merge-options plan (livespec-dev-tooling ledger, epic livespec-dev-tooling-xowhol) moves the ten `fleet`-array members from the `thewoolleyman` account to the GitHub organization `livespec-ai` in the org cutover window of Mon 2026-11-16 16:00Z. Its maintainer-approved Definition of Done (research note 005, §4, DoD bullet 2) says: "Every adopter repository stays owned by its current account (thewoolleyman or mi-homelab)". Because every manifest reader builds both member and adopter names as `<owner>/<repo>` from the one top-level `owner`, flipping `owner` to `livespec-ai` would point all twelve adopters at repositories that do not exist under that organization. One adopter already lives under a different account: `homelab` is `mi-homelab/homelab`, and the manifest's implied `thewoolleyman/homelab` resolves today only through GitHub's transfer redirect. The manifest therefore needs a way to name adopter owners independently of the fleet owner, and the readers need one shared resolution rule, before the cutover can flip `owner`. The fleet's confirm-the-reader-before-you-write rule dictates the order: a manifest that sets a key its readers ignore silently resolves every adopter against the wrong account, with no error.

### Proposed Changes

All edits are in `SPECIFICATION/non-functional-requirements.md`. No `## ` heading is added, changed or removed, so `tests/heading-coverage.json` needs no co-edit. Every quoted replace-target below exists verbatim, once, in the live file.

**1. §"Fleet membership contract" → **Fleet manifest** paragraph.** Replace the sentence fragment

> each carrying its repo class (core / enforcement-suite / impl-plugin / driver-plugin / library / console / control-plane-tool), and MAY carry an `adopters` array (see **Adopters**).

with

> each carrying its repo class (core / enforcement-suite / impl-plugin / driver-plugin / library / console / control-plane-tool), and MAY carry an `adopters` array (see **Adopters**). The manifest names the GitHub accounts that own those repositories through its owner keys (see **Repository owners**).

**2. §"Fleet membership contract" → **Adopters** paragraph.** Replace

> and a `posture` (`released` / `pinned` / `none`) governing how it tracks upstream livespec releases.

with

> and a `posture` (`released` / `pinned` / `none`) governing how it tracks upstream livespec releases. An adopter entry MAY also name an `owner`, the GitHub account that owns that adopter's repository (see **Repository owners**).

**3. §"Fleet membership contract" — insert a new rule paragraph immediately after the **Adopters** paragraph and before **Registration follows wiring for a released adopter.**:**

> **Repository owners.** The manifest's top-level `owner` names the GitHub account (a user or an organization) that owns every `fleet`-array member, and only those members: a member's repository is `<owner>/<repo>`, and `owner` is the fleet owner the **Discovery safety net** rule scans. The manifest MAY carry a top-level `adopter_owner` naming the GitHub account that owns adopter repositories by default; when `adopter_owner` is absent, its value is the value of `owner`. An adopter entry MAY carry its own `owner`, which overrides `adopter_owner` for that entry alone. Every manifest consumer MUST resolve an adopter's repository as `<adopter.owner>/<repo>` when the entry carries `owner`, else `<adopter_owner>/<repo>` when the manifest carries `adopter_owner`, else `<owner>/<repo>`; and MUST resolve a `fleet`-array member's repository as `<owner>/<repo>`. A consumer MUST NOT build an adopter's repository name from `owner` alone when the manifest carries `adopter_owner` or the entry carries its own `owner`, and MUST NOT apply `adopter_owner` or a per-adopter `owner` to a `fleet`-array member. An adopter whose repository is owned by an account other than the manifest's default adopter owner SHOULD carry its own `owner` rather than resolve through a forge's rename or transfer redirect. **Ordering.** Each owner key reaches the manifest only after its readers. A manifest change MUST NOT introduce `adopter_owner` or a per-adopter `owner` until every manifest consumer resolves adopter repositories by the rule above, because a consumer that ignores those keys resolves every adopter against `owner` with no error. A manifest change that alters `owner` MUST NOT land until the manifest on master already names, through `adopter_owner` or per-adopter `owner` keys, the account that owns each adopter, so that changing `owner` moves only the `fleet`-array members.

**4. §"Fleet membership contract" → **Discovery safety net** paragraph.** Replace

> flags any repo under the fleet owner matching the `livespec-*` naming

with

> flags any repo under the fleet owner (the manifest's `owner`, per **Repository owners**) matching the `livespec-*` naming

**5. §"Conformance Pattern" → **Profiles and the declarative manifest.** paragraph.** Replace

> each adopter entry naming its `profile` and a `posture` (`released` / `pinned` / `none`) governing how it tracks upstream.

with

> each adopter entry naming its `profile` and a `posture` (`released` / `pinned` / `none`) governing how it tracks upstream, and, optionally, the `owner` of its repository (§"Fleet membership contract" → "Repository owners"). The normative MAY for that key lives in item 3.

**6. §"Scenarios" — append a new scenario at the end of the section, immediately after the step**

> And a newly introduced finding outside the acceptance policy owned by `livespec-dev-tooling` fails per §"Shell and Justfile discipline"

**and before `## Factory routing`:**

> ### Scenario: An adopter's repository resolves through the adopter owner keys, never the fleet owner alone
>
> Given the fleet manifest names `owner` as one GitHub account and `adopter_owner` as a different account
>
> And one adopter entry carries its own `owner` naming a third account
>
> When a manifest consumer resolves every repository the manifest names
>
> Then each `fleet`-array member resolves to `<owner>/<repo>`
>
> And the adopter carrying its own `owner` resolves to `<adopter.owner>/<repo>`
>
> And every other adopter resolves to `<adopter_owner>/<repo>`
>
> And no adopter resolves to `<owner>/<repo>`

The scenario heading is `### ` (H3) like every other scenario in this section, so it adds no `tests/heading-coverage.json` row.

Out of scope for this revise, by the ordering rule it states: the change to `.livespec-fleet-manifest.jsonc` itself (adding `adopter_owner`, the `homelab` entry's `owner`, and the header comment's `adopters` entry shape) MUST land only after the manifest consumers resolve the new keys, and so travels in its own later change, not in this spec revise.
