---
proposal: codex-skills-picker-discoverability.md
decision: accept
revised_at: 2026-06-23T09:59:20Z
author_human: Tony Wolfram <tony@thewoolleyweb.com>
author_llm: gpt-5-codex
---

## Decision and Rationale

Maintainer intent is to prevent another gap where plugin installation and
model-visible skill loading pass while the human `/skills` picker path remains
untested or misunderstood. The accepted change makes the picker proof explicit:
search is by short skill name, and the plugin is rendered as context in the
picker row. This keeps the existing `codex exec` compatibility proof and adds a
separate top-of-pyramid human-discoverability proof instead of conflating the
two surfaces. No H2/H3 heading is added, removed, or renamed, so
tests/heading-coverage.json is untouched.

## Resulting Changes

- non-functional-requirements.md
