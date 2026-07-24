# Recovered research inventories — raw, unedited

These three reports were produced by research agents on 2026-07-19 and then
LOST: the agents completed their work normally but their final reports never
reached the driver session. They were recovered from the agent transcripts
under `~/.claude/projects/<slug>/<session>/subagents/agent-*.jsonl` (the last
assistant text block of each) and are committed here **verbatim, unedited**.

They are kept raw because their detail exceeds what the diagnosis note
summarizes — per-gate file:line citations, the full pin-format table, the
per-repo PR-state bifurcation, and each agent's own explicitly-flagged
unknowns.

| File | Covers |
|---|---|
| `pin-inventory.md` | Every pin format (6 managed / 5+ unmanaged), the fan-out machinery end-to-end, what the fan-out runtime has and lacks, and the per-repo PR backlog with `mergeStateStatus` bifurcation |
| `gate-breakage-inventory.md` | The 12 reddenable gates with (a)/(b) classification, blast radius, and the latent stricter-upstream hazards |
| `consolidation-map.md` | All 23 pre-existing items across 5 tenants with disposition verdicts, verbatim decision records, contradictions, and duplicate pairs |

## Reading discipline

**These are inputs, not conclusions.** The diagnosis note
(`../diagnosis.md`) is the authority for this thread — it carries only claims
that were INDEPENDENTLY RE-VERIFIED in-session, and it marks the ones that
were not.

Each report also carries its own "could not verify" section. Honor those:
notably the adopter ledgers were unreachable, several dev-tooling item scopes
are title-derived rather than read from their bodies, and the mechanism by
which a red bump PR reached `livespec` master is undetermined because the
Actions history aged out.

One report's headline claim — that the `livespec-console-beads-fabro-7wy`
premise does not reproduce — was independently confirmed here and is now
load-bearing: it withdrew a sequencing constraint the plan had wrongly placed
on the console unblock path.
