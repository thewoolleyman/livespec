---
proposal: rowoutcome-railway-spelling.md
decision: accept
revised_at: 2026-08-01T02:40:44Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-rop-railway-enforcement
---

## Decision and Rationale

ACCEPTED, and the reason it is not a softening is the same test that decides which functions it does NOT cover.

THE PRINCIPLE: CONVERT WHERE THE FAILURE ORIGINATES AND IS CURRENTLY UNREPRESENTABLE; RATIFY THE TYPE THAT RENDERS IT AT THE BOUNDARY. It earns acceptance because it sends two populations OPPOSITE ways from one rule. `RowOutcome` is ratified as a rendering at the row boundary. The `default_gh_runner` / `default_command_runner` / `default_gh_downloader` trio is NOT — those call `subprocess.run` directly rather than through an injected parameter, so they ARE the boundary, and an OSError there has no `try` anywhere in the chain and crashes a nine-member sweep partway through a member. A rule that produced only the convenient answer would be a rationalisation.

THE EVIDENCE WAS PRODUCED, NOT ARGUED. Both defects fixed in this epic's 2026-08-01 pair lived at the LEAF and rendered into `RowOutcome` sufficiently at the row boundary: one needed a distinct MESSAGE at unchanged severity, the other needed `RowSkip` instead of `RowPass`. The union was sufficient both times and the railway was necessary both times, one layer down. That is the architecture the requirement asks for.

CONDITION 2 IS THE WHOLE DIFFERENCE BETWEEN AN HONEST RATIFICATION AND A LAUNDERED EXEMPTION, and it is accepted as BINDING TEXT rather than as a follow-up. Measured on master before ruling: 14 consumption sites, every one an independent `if isinstance` chain (`_lanes.py` 3, `local_reconcile.py` 3, `wire_fleet_member.py` 4, `_rows_claude_plugin.py` 2, `_adopter_lane.py` 2), ZERO `match` statements over the union, and ZERO occurrences of `assert_never` in that entire package. So the type has `Result`'s shape and none of its enforcement, and a fourth variant would fall silently through all 14. Ratifying without condition 2 would preserve the exact property that let `RowSkip` acquire two contradictory meanings across two lanes.

CONDITION 3 IS THE OTHER HALF OF THAT SAME PRICE, and it makes the outstanding two-meanings defect a PRECONDITION of this clause rather than an incidental cleanup: under ratification nothing else fixes it. It needs no new type — the central lane already renders an excluded-note form for inapplicability, and two rows simply do not use it.

The discharge of condition 2 is deliberately CHEAP and adds no machinery: converting the 14 sites from `isinstance` chains to `match` statements places them under a check that is ALREADY ARMED and already wired into every governed repo's aggregate. No new check, no new severity, no new role key — which is what keeps this a tightening rather than a new lever. The blind spot it works around is recorded in the ratified text because it is this section's own subject arriving in the enforcement of this section.

## Resulting Changes

- non-functional-requirements.md
