---
topic: doctor-uniform-per-finding-disposition
author: claude-opus-4-7
created_at: 2026-05-25T17:26:42Z
---

## Proposal: doctor-MUST-offer-uniform-per-finding-disposition-dialogue-regardless-of-phase

### Target specification files

- SPECIFICATION/contracts.md
- (downstream SKILL.md regeneration is implied — `.claude-plugin/skills/doctor/SKILL.md` Steps 3, 10, 11, and the §"Failure handling" Exit 3 row)

### Summary

Adopt a project-wide rule: the `doctor` skill's per-finding user dialogue (Step 11 in the current SKILL.md) MUST apply uniformly to every non-`pass` finding, regardless of which phase surfaced it. Today the dialogue is wired only to LLM-driven phase findings (Steps 6, 7, 9, 10); static-phase `fail` findings hit `## Failure handling` Exit 3, which narrates corrective actions and aborts, and static-phase `warn` findings are listed in Step 3 narration. In both static-phase cases there is NO disposition surface — the user's only recourse is to act manually outside the skill, which the LLM is free to skip. The fix is uniform: every surfaced non-`pass` finding gets the same disposition menu, with at minimum a `capture-as-work-item` route that guarantees nothing is dropped on the floor.

The disposition menu expands from the current three (`accept` / `defer` / `dismiss`) to five:

- `fix-now` — apply the corrective action implied by the finding's `message` directly (text edit, `mkdir`, ref deletion, etc.). Available only when the corrective action is mechanically describable from the finding's `message` field; otherwise greyed out.
- `capture-as-work-item` — file a freeform work-item in the active impl-plugin's Work Items store via the impl-plugin's `capture-work-item` skill. ALWAYS available. This is the universal fallback that satisfies the "nothing is dropped" guarantee.
- `propose-change` — current `accept` semantics, renamed for clarity. Invoke `/livespec:critique` against the appropriate `--spec-target` and thread the `proposed_change_hint` (LLM-phase findings) or a freshly-generated hint derived from the finding's `message` (static-phase findings) as the user-described change.
- `defer` — record the finding in this session's narration; do nothing durable. Unchanged.
- `dismiss` — the user judges the finding does not apply. Unchanged.

### Motivation

Surfaced on 2026-05-25 during a real `/livespec:doctor` run against `livespec-impl-plaintext`. The static phase produced two `fail` findings (missing `history/v001/proposed_changes/` directory, BCP14 `May` in `contracts.md:281`) and one `warn` finding (18 stale merged-PR branches). Per the current SKILL.md `## Failure handling` Exit 3 contract, the skill aborted after narrating corrective actions — no disposition dialogue, no work-item filed, no propose-change drafted. The user explicitly noticed and asked: "Why didn't you offer me a prompt to fix the things you found? Isn't that part of the doctor's skill?"

The current asymmetry between static-phase and LLM-phase findings has no contract-level justification — it is an artifact of how the two phases were built (the LLM phase produces `proposed_change_hint` strings inline; the Python static phase emits raw findings with corrective-action prose in `message`). The user-facing UX should not carry that seam. A finding the user can act on is a finding worth dispositioning, whatever phase surfaced it.

Two design weakening alternatives were considered and rejected:

1. **"Always offer to fix" (strong form).** Variable corrective actions across finding types (edit a line vs. `mkdir` vs. `gh api DELETE` 18 refs) make the `fix-now` route hard to encode mechanically; the strong form would have required per-finding-type dispatch logic. Rejected as scope creep. `fix-now` is RETAINED in this proposal as an OPTIONAL disposition when the corrective action is mechanically obvious from `message`, but the load-bearing guarantee lives on `capture-as-work-item`.
2. **Status quo plus a `capture-this-finding` shortcut at narration time.** Less uniform — would require parallel UX surfaces for "list-and-narrate" vs. "list-and-disposition", and the LLM would have to decide which surface applies per finding. Rejected: uniformity reduces both LLM and human cognitive load.

The `capture-as-work-item` route specifically requires CROSS-PLUGIN INVOCATION: `doctor` lives in `livespec`; `capture-work-item` lives in the active impl-plugin's namespace (e.g., `/livespec-impl-plaintext:capture-work-item`). This is already an established pattern per `contracts.md` §"Cross-plugin invocation" and the existing `process-memos` → `/livespec:propose-change` cross-boundary handoff codified at `contracts.md` line 316. The new dialogue MUST resolve the active impl-plugin via the project's `.livespec.jsonc` `implementation.plugin` field and invoke the namespaced `capture-work-item` skill.

### Proposed Changes

**`SPECIFICATION/contracts.md`** — add a new subsection under the existing doctor coverage (e.g., between §"Per-sub-sub-spec doctor parameterization" and §"Doctor cross-boundary invariants") titled `## Doctor per-finding disposition dialogue`:

```markdown
## Doctor per-finding disposition dialogue

The `doctor` skill MUST offer a per-finding disposition dialogue for
every non-`pass` finding surfaced during a single invocation,
regardless of which phase produced it (static phase `fail` or `warn`,
or any of the four LLM-driven phase categories — skill-baked objective,
template-extension objective, skill-baked subjective, template-extension
subjective). The disposition menu MUST present at minimum these five
options:

- `fix-now` — apply the corrective action implied by the finding's
  `message`. OPTIONAL on a per-finding basis: only offered when the
  corrective action is mechanically describable from `message` (text
  edits, `mkdir`, single-shell-command cleanups). When the corrective
  action is not mechanically describable, this option MUST NOT be
  offered for that finding (the menu surfaces the remaining four).
- `capture-as-work-item` — file a freeform work item in the active
  impl-plugin's Work Items store via the impl-plugin's
  `capture-work-item` skill. The active impl-plugin is resolved via
  `.livespec.jsonc`'s `implementation.plugin` field; the cross-plugin
  invocation MUST go through the skill namespace per §"Cross-plugin
  invocation". The filed work item carries `origin: freeform` and
  embeds the finding's `check_id`, `spec_root`, optional `path`, and
  `message` in its body so the trail back to the originating doctor
  finding is preserved. This disposition MUST ALWAYS be offered for
  every non-`pass` finding.
- `propose-change` — invoke `/livespec:critique` against the
  appropriate `--spec-target` (the tree whose `spec_root` surfaced the
  finding) and thread a `proposed_change_hint` as the user-described
  change. For LLM-driven phase findings the hint is the one produced
  inline by the check. For static-phase findings the hint is generated
  fresh from the finding's `message` and `path`/`line` fields. This
  disposition MUST ALWAYS be offered.
- `defer` — record the finding in the session's narration; take no
  durable action. The finding MAY surface again on the next invocation.
- `dismiss` — the user judges the finding does not apply. No durable
  action. No cross-invocation persistence of dismissals in v1; the
  finding MAY surface again on the next invocation and the user
  dismisses again or chooses a different disposition.

The dialogue MUST run BEFORE the skill aborts on a static-phase
`fail` (Exit 3 from the wrapper). The pre-existing safety contract
that the LLM-driven phase MUST NOT run after a static-phase `fail` is
PRESERVED: the dialogue handles disposition of the already-surfaced
static findings only, with NO additional LLM-driven check generation.
This narrows the scope of "abort" from "stop interacting with the
user" to "do not run further check generation"; disposition of
already-surfaced findings is not check generation.

The dialogue MUST run for static-phase `warn` findings too (today
they are narrated in Step 3 without a disposition surface). The
`warn` status retains its current semantics with respect to wrapper
exit code (a `warn` finding does NOT lift the wrapper to exit 3);
only the user-facing dispositioning is affected.

Findings with status `pass` and `skipped` are NOT dispositioned. They
are surfaced via the existing Step 3 narration only.

A finding's disposition menu MUST present its five options in the
canonical order listed above. The LLM prose surface MAY render the
options as a single picker, MAY render them per-finding sequentially,
or MAY batch all findings into a multi-disposition picker — the
choice is a SKILL.md prose decision, not a contract one. The
contract is the menu's CONTENT and AVAILABILITY guarantees.
```

**Downstream `.claude-plugin/skills/doctor/SKILL.md` regeneration** (handled at `/livespec:revise` time, but the shape is illustrative):

- Step 3 narration of static findings retains its existing form (list and surface), BUT explicitly delegates to the per-finding dialogue (Step 11) for every non-`pass` static finding before any abort gate.
- Step 11 generalizes from "for every finding accumulated across Steps 6, 7, 9, 10" to "for every non-`pass` finding surfaced this invocation, in `spec_root`-grouped order".
- The Step 11 options list expands from three to the five canonical options above.
- The `## Failure handling` Exit 3 row updates: "Surface ALL findings grouped by `spec_root`; emphasize the failures; describe the corrective actions implied by each message; RUN THE PER-FINDING DISPOSITION DIALOGUE FOR EACH NON-`pass` FINDING; then abort. LLM-driven phase (further check generation) MUST NOT run."

The exact wording is illustrative; the maintainer is free to refine prose during `/livespec:revise`.

### Compatibility & migration notes

- The new `capture-as-work-item` cross-plugin invocation is consistent with the existing `process-memos` → `/livespec:propose-change` cross-boundary handoff pattern; no new contract mechanism is required.
- Impl-plugins that do not yet implement `capture-work-item` would surface a structured error from the cross-plugin invocation, which `doctor` MUST narrate gracefully and fall through to the remaining four disposition options. Per the v1 surface declared in `contracts.md` §"Heavyweight authored skills (6) — required impl-plugin lifecycle surface", every impl-plugin already MUST expose `capture-work-item`, so the fall-through is a defensive safety net rather than a steady-state expectation.
- No schema changes to `finding.schema.json`, `doctor_findings.schema.json`, or `proposal_findings.schema.json` are required. The dialogue operates on existing finding fields (`check_id`, `status`, `message`, `path`, `line`, `spec_root`).
- This proposal does NOT change the static-phase / LLM-driven phase boundary, the wrapper's exit-code derivation, or the LLM-skip flag precedence. It expands ONLY the per-finding disposition surface.

### Doctor static-check implication (optional, follow-on)

A future revise cycle MAY add a doctor static-phase invariant that
asserts the SKILL.md prose enumerates all five disposition options at
Step 11 (grep-based check against the rendered SKILL.md). Out of scope
for this proposal.
