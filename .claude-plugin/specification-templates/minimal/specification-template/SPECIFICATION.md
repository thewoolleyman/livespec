# `<intent-derived-title>`

> The `# H1` reflects the project intent (BCP14 noun phrases
> derived from the seed-time intent statement). The single-file
> body uses HTML-comment delimiter markers (`<!-- region:<name> -->`
> open + `<!-- /region:<name> -->` close) per
> `SPECIFICATION/templates/minimal/contracts.md` §"Delimiter-
> comment format" so propose-change/revise cycles can target
> regions precisely.

<!-- region:project-intent -->

A one-paragraph statement of what the project is and what
problem it solves. Populated at seed time from the user's
verbatim intent.

<!-- /region:project-intent -->

<!-- region:cadence -->

The maintenance / review cadence the project commits to (e.g.,
"the maintainer MUST review issues at least once per month").
Populate when the user's intent describes operational rhythm;
omit otherwise.

<!-- /region:cadence -->

<!-- region:dod -->

A `<intent-derived-title>` change MUST satisfy this Definition
of Done before merge:

- The spec change flows through the propose-change/revise loop;
  no out-of-band edits to `SPECIFICATION.md`.
- Region open + close markers stay paired (no nesting across
  boundaries; well-formed open/close balance per the
  delimiter-comment format invariants).
- The doctor static phase passes against the working spec.

<!-- /region:dod -->

<!-- region:non-goals -->

Things explicitly out of scope. Populated incrementally as
non-goals surface during propose-change cycles.

<!-- /region:non-goals -->
