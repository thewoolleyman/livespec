---
proposal: ci-host-rebuildable-from-bare-metal.md
decision: accept
revised_at: 2026-09-06T15:14:30Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-fable-5-1 (k3s-on-gmktec-for-vps-usage plan session)
---

## Decision and Rationale

Accepted as filed. The clause states the fleet-level property the maintainer directed on 2026-09-06 as goal 0 of plan k3s-on-gmktec-for-vps-usage (epic livespec-sab5gn): a host carrying fleet CI MUST be rebuildable from bare metal by a committed, re-runnable, rehearsed procedure that a per-host profile parameterizes; destructive storage steps refuse without explicit consent; the host record carries facts and never the procedure; backup-and-restore never substitutes; the recipe, profiles and rehearsal obligation belong to the provisioning repository (proposed there as ci-runner-node-rebuild-recipe). Two independent read-only reviews were performed on the exact final bytes: the configured reviewer model for this repository (opus, designated in .livespec.jsonc as a recorded maintainer-directed deviation) at 2026-09-06T15:06:22Z, and a Fable 5.1 confirmation using different instruments at 2026-09-06T15:12:56Z, satisfying the Fable-review rule; both verified replacement-target fidelity byte-for-byte (only the insertion between the Availability and Pool clauses; only the appended scenario section; only the appended heading-coverage entry), design-record fidelity against research/002 and the R0 scope event, the drift sweep (the storage-tiers reproducibility sentence stays as the narrower statement; the proving clause is below in the same section; no count or expiring claim), ratification mechanics (topic equals stem; v220 tip; the pending ci-host-admission-cap-derivation uses a disjoint anchor), cross-repo consistency (the dev-tooling proposal cites this clause's bold lead character-for-character), the four defect classes, and the digest, each returning NO BLOCKERS. The scenario section and its heading-coverage TODO entry (reason names the integration tier; work_item livespec-sab5gn) are co-edited atomically.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md
- ../tests/heading-coverage.json

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T15:06:22Z
verdict: NO BLOCKERS
proposal_stem: ci-host-rebuildable-from-bare-metal
content_digest: 3182e3bb01ab03bf11f18619747fc94dc2f5db269b76bf2a6609a65d57d8d9d7
