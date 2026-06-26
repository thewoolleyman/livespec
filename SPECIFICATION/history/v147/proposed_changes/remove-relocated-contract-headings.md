---
topic: remove-relocated-contract-headings
author: claude-opus-4-8
created_at: 2026-06-26T04:09:28Z
---

## Proposal: Remove relocated contract headings (besm.6)

### Target specification files

- SPECIFICATION/contracts.md
- tests/heading-coverage.json

### Summary

Remove the two contract sections relocated to their owning sibling repos under livespec-besm.6 — `## Interactive dialogue ownership (orchestrator-side)` (now owned by livespec-orchestrator-beads-fabro) and `## CLI end-to-end harness contract` (now owned by livespec-driver-claude) — and drop their tests/heading-coverage.json entries. This takes core's release-gate check-no-todo-registry to zero heading-coverage TODOs. The two now-dangling same-file `§"..."` citations to these headings are reworded to prose so doctor-anchor-reference-resolution still passes.

### Motivation

livespec-besm.6 (RELOCATE decision, maintainer 2026-06-26): the contract text for these two headings is genuinely sibling-owned and was relocated entirely into the owning repos (B2 → orchestrator-beads-fabro PR #175 merged; B4 → driver-claude PR #47 merged, each with a paired heading-coverage entry). This core-side removal is the final step, clearing core's last two release-gate heading-coverage TODOs so the release-tag.yml gate goes green.

### Proposed Changes

Delete the `## Interactive dialogue ownership (orchestrator-side)` section and the `## CLI end-to-end harness contract` 6-point section from SPECIFICATION/contracts.md. Reword the two remaining same-file citations to the removed headings: the `capture-as-work-item` disposition in `## Doctor per-finding disposition dialogue` (drop the §-citation; the consent dialogue is orchestrator-owned), and the sibling-tier reference in `## E2E harness contract` (describe the CLI-driven tier as owned by livespec-driver-claude rather than citing the removed heading). Drop both contracts.md TODO entries from tests/heading-coverage.json. (Ride-along, outside this revise: the matching stale citation in .claude-plugin/prose/doctor.md is reworded the same way.)
