# Hand-off: land the agent-instruction `.ai/` convention (fleet + adopter-wide)

**Standing hand-off — refresh this file + the beads state each session that
advances it.** Run this prompt to continue the track.

## What this is

Make durable agent guidance have a real, non-ephemeral, fleet-universal home:
`AGENTS.md` + progressively-disclosed **`.ai/<topic>.md`** files it references,
at any directory level, enforced by the `block-auto-memory` hook + a conformance
check. Full design + provenance: **`research/agent-instruction-dot-ai-convention/design.md`**.

Epic: **`livespec-hso8`**. Children: **`livespec-co9h`** (P1 hook reword),
**`livespec-a244`** (keystone NFR), **`livespec-8njn`** (document the convention).
Mechanism: the five-slot Conformance Pattern **`livespec-zs22.7`**. Concern epic:
**`ob-0x5`**.

## Maintainer decisions (2026-06-26) — load-bearing

1. Directory name is **`.ai/`** (NOT `.ai-instructions/` — that was a
   placeholder in the older `a244`/`co9h`/`8njn` wording; update it).
2. `.ai/` is supported at **ANY directory level**, parallel to that level's
   `AGENTS.md` + its symlinked `CLAUDE.md` (mirrors nested `AGENTS.md`).
3. `AGENTS.md` references its sibling `.ai/<topic>.md`; the detail file loads
   **progressively/conditionally** (keep `AGENTS.md` small).
4. **Fleet- and adopter-wide.** Specify once in core → capture in `AGENTS.md` +
   `.ai/` → propagate via the impl-plugin copier template → enforce (hook) →
   verify (conformance check).
5. Never ephemeral `~/.claude/.../memory/*.md`.

## Next actions (by Conformance-Pattern slot)

1. **Specify** (`a244`): drive `/livespec:propose-change` → `/livespec:revise`
   to codify the convention as a core non-functional-requirement/contract, using
   `.ai/` + the any-directory-level rule. Co-edit `tests/heading-coverage.json`
   if it adds/changes a `## ` heading.
2. **Enforce** (`co9h`, P1): (a) confirm the `block-auto-memory` hook `reason`
   reads `.ai/` (driver-claude master already has the intent-routing reword from
   co9h — update its wording `.ai-instructions` → `.ai/`); (b) add the **codex**
   driver's sibling reword; (c) **ACTIVATE** the corrected build — the active
   installed driver-claude version this session was the stale `0.1.0` cache whose
   message still said only "capture-work-item / file work items into the ledger";
   the post-co9h build must be the enabled one (`/plugin update
   livespec@livespec-driver-claude`, or bump the project-pinned version).
3. **Capture** (`8njn`): document the convention in the family-universal
   `AGENTS.md` (core + impl-plugin template), and create the first required
   `.ai/<topic>.md` (candidate: `.ai/agent-disciplines.md` gathering the
   cross-cutting disciplines — TDD red-green-replay, 1Password secret-wrapper,
   worktree discipline, no-local-memory, and **"always print `run
   prompts/<name>.md` for the active standing handoff when ending a session"**,
   the preference that triggered this whole track).
4. **Propagate**: add the `AGENTS.md` block + `.ai/` scaffold to the impl-plugin
   copier template so adopters inherit it.
5. **Verify**: add a fail-closed conformance check (shared `livespec-dev-tooling`
   check + a doctor cross-boundary invariant) asserting every `AGENTS.md`'s
   `.ai/<topic>.md` references resolve, at each directory level. Model on
   `doctor-anchor-reference-resolution` / `doctor-no-cross-spec-reference`.

See the design doc's "Open questions for execution" for the granularity / Verify
shape / nesting-semantics decisions to settle as you go.

## Discipline

Worktree → PR → rebase-merge per repo; `mise exec -- git …`; never `--no-verify`.
Drive spec changes through `/livespec:propose-change` → `/livespec:revise` (a
direct `SPECIFICATION/` edit trips `doctor-out-of-band-edits`). Cross-repo work
(core + both drivers + dev-tooling + the copier template) is one epic (`hso8`) —
file per-repo children with cross-repo links; use `/livespec:doctor` as the
cross-repo consistency check. Do NOT bypass a hook — if a guard blocks you,
stop and surface it.

## Done when

The convention is specified in core, both drivers' `block-auto-memory` hooks
intent-route to `.ai/` and are the ACTIVE builds, `AGENTS.md` + the required
`.ai/<topic>.md` exist in core + the copier template, the conformance check is
wired into `just check` + CI fleet-wide, and `/livespec:doctor` is clean across
the fleet. Then close `hso8` + children and delete this file.
