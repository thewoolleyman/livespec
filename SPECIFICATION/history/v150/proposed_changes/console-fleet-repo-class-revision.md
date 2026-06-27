---
proposal: console-fleet-repo-class.md
decision: accept
revised_at: 2026-06-27T01:48:42Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Names `console` in the core-owned repo-class enumeration so livespec-console-beads-fabro can be registered as a fleet member (livespec-zs22.7.8). Core already records the Control-Plane console architecturally (§"Control-Plane console guidance") and §"Obligations per repo class" already scopes shim-workflow obligations to pin-consuming classes, so naming the class is the only enumeration gap. The per-class obligation table (console as a non-pin-consuming member) is owned by livespec-dev-tooling's spec.

## Resulting Changes

- non-functional-requirements.md
