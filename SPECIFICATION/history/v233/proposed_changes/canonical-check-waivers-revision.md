---
proposal: canonical-check-waivers.md
decision: modify
revised_at: 2026-10-28T12:25:07Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepts reasoned per-check waivers of canonical checks so that a fleet member with no subject for a check (the Rust console) can rejoin the release fan-out without a duplicate coverage map. It is modified per the independent review: the stale and malformed obligations are scoped to the in-repo gate and the fleet-conformance check; the template gate is stated to be unaffected; the doctor invariant's exclusion and status mapping are stated here and in contracts.md §wiring-completeness-cross-repo; reporting of honoured waivers is normative; and scenarios cover the malformed waiver and the doctor invariant.

## Modifications

The waiver text moves into a standalone 'Reasoned waivers' paragraph after the Wiring-completeness invariant. Layer 2 (the template gate) is explicitly unaffected. The doctor invariant excludes a waived slug and reports a stale or malformed waiver with the status of a missing slug, and contracts.md §wiring-completeness-cross-repo is amended to match. The fleet-conformance check MUST report each honoured waiver with its member, slug and reason. scenarios.md gains six scenarios, including a malformed waiver, a waived sibling slug at the doctor invariant, and a stale waiver at the doctor invariant.

## Resulting Changes

- contracts.md
- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-28T12:24:37Z
verdict: NO BLOCKERS
proposal_stem: canonical-check-waivers
content_digest: 6015d3aa4ec6af61eacee8d0a6c3ca14b859b2193c29d953ecdc7c62ea532bb5
