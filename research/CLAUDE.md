# research/

Durable scratch for thought, discussion captures, and exploratory
notes that aren't yet (and may never become) spec content. The
goal is a place where workflow-process questions, design
deliberations, and "things to sit with before deciding" can
persist past a single conversation without prematurely forcing
them into the spec lifecycle.

## What lives here

Subdirectories group docs by topic. As of writing:

- `workflow-processes/` — discussions about how livespec gets
  built, how agents and contributors collaborate, how work flows
  through the issue tracker, etc. NOT spec content; orientation
  notes and open-question captures.

Future subdirectories may include things like
`architecture-decisions/`, `notebooks/`, etc. Each gets its own
`CLAUDE.md` describing what kind of doc belongs there.

## What this directory is NOT

- **Not `SPECIFICATION/`.** Files here are NOT requirements.
  Spec content (functional or non-functional) MUST flow through
  `/livespec:propose-change` → `/livespec:revise` per the spec's
  self-application rule; nothing here bypasses that. If a
  `research/` doc evolves into a requirement that the system or
  process MUST honor, the formalization happens by authoring a
  proper proposed change, not by the doc itself becoming
  load-bearing.
- **Not `archive/`.** Files there are frozen historical artifacts
  from the bootstrap process — do not edit. Files here are
  living: they may be revised, expanded, superseded, or deleted
  as thinking matures.
- **Not `prior-art/`.** Files there are reference source material
  vendored from external projects (e.g., NLSpec). Files here are
  livespec's own thinking, even if they cite external work.

## When to add a doc

When a conversation produces something worth re-reading later but
NOT yet ready (or appropriate) to land in the spec — typically:

- a workflow-process question the user wants to sit with
- a multi-turn discussion with open questions explicitly flagged
- an analysis / audit that informs future work without being a
  requirement itself

Files are markdown, free-form, and may be deleted or moved into
the spec lifecycle once the thinking matures. There is no
required template; each subdirectory's `CLAUDE.md` may impose
local conventions if useful.
