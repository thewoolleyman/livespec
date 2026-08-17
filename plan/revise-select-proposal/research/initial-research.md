# revise-select-proposal: research note (initial)

## Problem statement

The maintainer wants /livespec:revise to be selectable to a SINGLE proposed
change, not process every pending proposal in <spec-target>/proposed_changes/
at once.

## Finding (confirmed by reading the implementation, not just --help)

The capability already exists at the API layer. revise.py's --revise-json
payload takes a `decisions[]` array; the only topic-level validation
(_validate_proposal_topics_exist in _revise_validation.py) checks that each
listed decisions[].proposal_topic resolves to an existing
<spec-target>/proposed_changes/<topic>.md file. Nothing requires the payload
to cover every pending proposal. A caller can already act on exactly one
proposal today by constructing a --revise-json payload whose decisions[]
array has a single entry for that topic.

--help does not surface this because it is a payload-SHAPE fact (what you
put inside decisions[]), not a CLI flag -- there is no --only-topic style
flag today.

## Scope decided with the maintainer (2026-08-17)

Two things, not one:
1. Add a convenience flag (e.g. --only-topic <topic> or equivalent) to
   revise.py so a caller does not have to hand-construct a full
   decisions[] JSON array just to act on one proposal -- the flag should
   filter/construct the payload down to that single topic before the
   existing validation/processing path runs.
2. Document the existing single-proposal-selection capability (both the
   payload-shape fact and the new flag) in revise.py's own --help/argparse
   help strings and in prose/revise.md, so it is discoverable without
   reading the implementation.

## Open questions for scoping event

- Exact flag name and whether it composes with --revise-json (does it
  filter down a payload's decisions[] server-side, or replace the need to
  build one at all for the single-proposal case) -- needs a look at how
  the Driver-side skill (livespec-driver-claude) currently constructs
  --revise-json payloads, since that's the primary caller.
- Whether the flag needs a matching decision verb (accept/modify/reject)
  argument, or only makes sense alongside an already-built minimal payload.
