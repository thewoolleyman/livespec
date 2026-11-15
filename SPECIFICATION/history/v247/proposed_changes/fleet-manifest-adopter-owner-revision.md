---
proposal: fleet-manifest-adopter-owner.md
decision: modify
revised_at: 2026-11-15T02:07:04Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted by legacy-coordinator-agent under R301 (delegated revise decision, relayed to this session on livespec#3242), including the SHOULD that an adopter owned by an account other than the default adopter owner carries its own `owner` rather than resolving through a forge redirect. Motivation: the stale-base-merge-options org cutover (livespec-dev-tooling epic xowhol; note 005 §4 DoD bullet 2; cutover window Mon 2026-11-16 16:00Z) moves only the `fleet`-array members to the livespec-ai organization, so the manifest must name adopter owners independently of `owner` before `owner` changes. The revise adds no `## ` heading, so tests/heading-coverage.json needs no co-edit; the new scenario is an H3 like its siblings. Recorded as MODIFY rather than ACCEPT only because of the one wording repair in Modifications; the first independent review flagged that the literal proposal would carry a dangling reference into the spec. Ratified against the independent auto-spawned reviewer's NO BLOCKERS verdict on these exact bytes (the reviewer stated its identity as claude-sonnet-5-5, matching the configured sonnet designation, at 2026-11-15T02:06:20Z).

## Modifications

Item 5's replacement text is applied without its final sentence, "The normative MAY for that key lives in item 3." That sentence refers to a numbered item of the proposal itself, which stops existing once the proposal is archived, so carrying it into the live spec would leave a dangling reference (a claim that expires at ratification, per .ai/spec-proposal-review.md section 1). Items 1 to 4 and 6 are applied verbatim. Every normative clause of the accepted design is unchanged; the normative MAY for a per-adopter owner lives in the new Repository owners paragraph.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-15T02:06:20Z
verdict: NO BLOCKERS
proposal_stem: fleet-manifest-adopter-owner
content_digest: d6604cd743efb2c9c359267e8eebfbfba120e1d5ce050f07b2417cc89d78ed31
