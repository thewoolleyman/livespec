---
proposal: spec-tree-path-closure.md
decision: accept
revised_at: 2026-08-24T02:29:17Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-plan-spec-tree-manifest-and-clause-citation
---

## Decision and Rationale

Ratifies Gate 0 of the pre-foreman livespec hardening program (finding F6, epic livespec-r6siae, work-item livespec-6fhcw7): under a template that declares its spec_files manifest explicitly, the spec root is closed over the manifest's kind: markdown entries; a file present under the spec root and absent from the manifest is a doctor failure naming it, never a warning or a silence. Markdown remains the ONLY manifest kind -- an 'opaque' second kind was drafted and withdrawn after a fleet sweep found zero legitimate non-markdown files under any spec root. An externally-rendered diagram image is now committed OUTSIDE the spec root. This PARTIALLY REVERSES the v136 decision (mermaid-default-scrub-rendering), which permitted such an image to sit undeclared inside the spec root on the reasoning that the whole-tree history snapshot preserves it -- true about preservation, silently false about permission, and F6 is exactly what that gap cost. Every other v136 deletion (the diagram_source/diagram_rendered kinds, render_commands, the render-on-revise lifecycle, the drift check) is KEPT; only the in-tree-undeclared-image clause is reversed. Two independent read-only Fable-5 reviewers, deliberately different instruments (exact-substring fidelity; latent-defect + coherence), reviewed the proposal across three rounds (1ffa8c5c 2+4 blockers; fde5c6bd 2+2; 63b3b2f4 NO-BLOCKERS x2), then independently re-attested the exact resulting_files[] bytes below (content_digest c07f951377f866b968c0efe7c4b9afdfb7b3a14b828f67ca066979a073df1cc7), catching and confirming the fix for one mechanical apply defect (a blockquote-parsing bug that dropped the new section's body) before the digest was finalized.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-24T02:25:19Z
verdict: NO BLOCKERS
proposal_stem: spec-tree-path-closure
content_digest: c07f951377f866b968c0efe7c4b9afdfb7b3a14b828f67ca066979a073df1cc7
