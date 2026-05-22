# `<intent-derived-title>`

> The `# H1` MUST reflect the project intent (BCP14 noun phrases
> derived from the seed-time intent statement). Section-level
> `##` headings organize the spec under the H1 and MAY use
> stable section names where appropriate.

## Project intent

A one-paragraph statement of what the project is and what
problem it solves. Populated at seed time from the user's
verbatim intent.

## Architecture

The high-level architecture shape: components, their
responsibilities, and the boundaries between them. Subsections
introduce the project's key concepts in the order a new reader
encounters them.

## Definition of Done

A `<intent-derived-title>` change MUST satisfy this DoD before
merge:

- The spec change flows through the propose-change/revise
  loop; no out-of-band edits.
- Tests for any new behavior are paired with the implementation
  per the project's testing approach (see `contracts.md`).
- The doctor static phase passes against the working spec.

## Non-goals

Things explicitly out of scope. Populated incrementally as
non-goals surface during propose-change cycles.
