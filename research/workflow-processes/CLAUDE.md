# research/workflow-processes/

Discussion captures and open-question notes about how livespec
gets built — agent / contributor collaboration patterns, issue
tracker scope and lifecycle, the line between spec content and
implementation-only intent, etc. These are deliberately
*pre-formal*: the docs here exist so questions can be re-read,
expanded, and reasoned about before any of the answers get
codified into `SPECIFICATION/`.

## Convention for docs in this subdirectory

Each file captures one workflow-process question or discussion.
A useful template (not enforced):

- **Title** — descriptive, hyphen-separated.
- **Header block** — date the discussion happened, branch the
  capture was authored from, status (open question / sitting /
  formalized / superseded), pointers to related artifacts (PRs,
  beads issues, spec sections).
- **Why this conversation happened** — short framing for a cold
  reader.
- **Turn-by-turn capture** when the doc is a transcript: each
  turn under a clear `## Turn N — User` / `## Turn N — Assistant`
  header so attribution is unambiguous.
- **Things to sit with** — explicit list of open questions the
  capture leaves unresolved.

## What graduates a doc out of this directory

When a workflow-process question's answer matures into a
*requirement* — a statement the project MUST/SHOULD/MAY honor —
it's authored as a proposed change under
`SPECIFICATION/proposed_changes/<topic>.md` and processed via
`/livespec:revise`. The research doc itself stays here (or gets
deleted if fully superseded), but the load-bearing rule lives in
the spec from then on.

## What does NOT belong here

- Implementation-level intent that should become a beads issue —
  file as a freeform beads issue instead.
- Frozen historical artifacts — those go in `archive/`.
- Vendored external reference material — that's `prior-art/`.
- Anything the user has not explicitly asked to capture — these
  docs are deliberate, not auto-generated.
