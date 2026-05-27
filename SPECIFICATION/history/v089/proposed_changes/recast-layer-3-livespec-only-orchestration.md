---
topic: recast-layer-3-livespec-only-orchestration
author: claude-opus-4-7
created_at: 2026-05-27T07:25:37Z
---

## Proposal: recast-layer-3-as-livespec-resident-cross-repo-orchestration

### Target specification files

- SPECIFICATION/spec.md

### Summary

Recast the Layer 3 — Project-local composition bullet and the Cross-side composition belongs at Layer 3 paragraph in spec.md §Three-layer orchestration architecture so Layer 3 is livespec-resident only. Layer 3 MUST live at livespec/.claude/skills/loop/SKILL.md and no other repo. Cross-side composition between /livespec:next and every active impl-plugin's next remains Layer 3's concern, but the driver MUST NOT be carried into impl-plugin repos.

### Motivation

The original three-layer architecture placed Layer 3 in every consuming repo (livespec and every livespec-impl-*) on the theoretical basis that each repo would develop independent orchestration. Eighteen months of practice (the livespec self-hosting bootstrap, every cross-repo epic from li-fgqgnk through the cross-repo ci.yml fetch-depth propagation epic and the Resolution-enum migration) has shown that all meaningful orchestration happens from livespec — via ad-hoc tmp/prompt.md driver scripts dispatching sub-agents into the sibling repos. The impl-plaintext template instantiation of .claude/skills/loop/SKILL.md is contract-only; it has never been invoked. The per-repo Layer 3 slot is dead architecture. Recasting Layer 3 as livespec-resident matches what the architecture actually IS in practice and removes the unused per-repo mandate.

### Proposed Changes

Replace the Layer 3 — Project-local composition bullet (currently 'Each repository that consumes livespec MAY check in a project-local orchestration driver at .claude/skills/loop/SKILL.md.') with: 'Layer 3 — Cross-repo orchestration (livespec-resident). The livespec repository MUST carry a project-local orchestration driver at .claude/skills/loop/SKILL.md. The driver composes Layer 2 primitives — invoking /livespec:next and the active impl-plugin's next to produce a unified cross-side ranking, dispatching to the appropriate heavyweight skill for the chosen action, running janitor checks (e.g., just check plus /livespec:doctor), committing on green, and looping until the queue drains or the configured budget exhausts. The driver MUST be the single cross-repo orchestrator across the livespec family of repos; livespec-impl-* plugin repos MUST NOT carry their own Layer 3 driver. The composition is local to the livespec family, not to each repo in it.' Update the following Cross-side composition belongs at Layer 3 paragraph so the cross-side ranker exclusion and Layer 3 discoverability nudge cross-references refer to livespec's resident Layer 3 driver (not 'the project's Layer 3 driver'). The phrase 'every impl-plugin's next' in the discoverability-nudge cross-reference MUST be removed; impl-plugin next skills no longer participate in the nudge contract (see the §Layer 3 discoverability nudge recast in contracts.md, filed as a separate finding in this propose-change).

## Proposal: drop-per-repo-loop-driver-mandate-from-non-functional-requirements

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Remove the per-repo Layer 3 loop driver mandate from non-functional-requirements.md and recast the section as livespec-only. The driver contract itself (mode parameter, budget parameter, janitor as hard gate, structured iteration journal) remains intact and SHALL apply to livespec's driver; what changes is the requirement that every consuming repo carries one.

### Motivation

The current §Project-local orchestration layer text MUST require every livespec-impl-* repository to inherit a starter .claude/skills/loop/SKILL.md from the copier template. Under the architectural recast (see the spec.md recast finding), Layer 3 is livespec-resident only; no impl-plugin repo carries a Layer 3 driver. The shared-content provenance enumeration MUST also drop its mention of .claude/skills/loop/SKILL.md as a static-scaffold requirement, since the loop skill is no longer a per-repo concern flowing through the copier template at all.

### Proposed Changes

1. In §Shared content provenance, remove 'the starter .claude/skills/loop/SKILL.md,' from the Static-scaffold requirements bullet's enumeration of items that MUST flow into every livespec-impl-* repo via the copier template. The remaining enumeration (justfile recipe surface, lefthook.yml, .mise.toml, pyproject.toml skeletons, GitHub workflows scaffolds, project-local plugin layout, commit-and-merge-discipline scaffolds) MUST stay intact. 2. Delete the paragraph beginning '.claude/skills/loop/SKILL.md (the project-local orchestration driver — see §Project-local orchestration layer below) is exempt from the copier drift check' (currently directly below the Drift-between-livespec-and-consumer-repo-content paragraph). The exemption is no longer needed because the file is no longer in the template's flow. 3. Rename §Project-local orchestration layer to §Cross-repo orchestration layer and recast its body: 'livespec MUST carry a project-local orchestration driver at .claude/skills/loop/SKILL.md per the three-layer architecture (see spec.md §Three-layer orchestration architecture for the Layer 1 / Layer 2 / Layer 3 model). The driver is the single cross-repo orchestrator across the livespec family of repos. livespec-impl-* repositories MUST NOT carry their own .claude/skills/loop/SKILL.md; the per-repo Layer 3 driver mandate (present in earlier revisions of this spec) is withdrawn. The copier template at livespec/templates/impl-plugin/ MUST NOT include a .claude/skills/loop/ subtree; the corresponding copier-update drift exemption is therefore obsolete and removed.' 4. Delete the trailing paragraph in the renamed section beginning 'The copier-update drift check MUST exclude .claude/skills/loop/SKILL.md from drift detection'. 5. Recast the §Layer 3 loop driver — required shape and discipline subsection so its opening sentence reads: 'The Layer 3 loop driver MUST be implemented as a Claude Code project-local skill at .claude/skills/loop/SKILL.md in the livespec repository.' Drop 'in each consuming repository' and the alternative-authoring sentence referencing the copier starter. The remaining contract — mode parameter, budget parameter, janitor as hard gate, structured iteration journal, exemption from the copier-update drift detection (now vacuous because there is no template subtree to drift against), and exemption from the thin-transport brevity discipline — MUST remain intact and apply to livespec's driver.

## Proposal: drop-loop-skill-from-copier-template-enumeration

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Remove the starter project-local loop skill from the copier-template enumeration in contracts.md §Shared content sync — copier template, and remove the .claude/skills/loop/SKILL.md drift-exemption sentences. The copier template MUST NOT include a .claude/skills/loop/ subtree under the recast architecture.

### Motivation

Under the architectural recast (see the spec.md and non-functional-requirements.md findings in this propose-change), Layer 3 is livespec-resident only. The copier template at livespec/templates/impl-plugin/ MUST NOT include a starter .claude/skills/loop/SKILL.md because no impl-plugin repo carries a Layer 3 driver. Three contract sentences currently codify the inclusion and drift exemption; all three MUST be revised.

### Proposed Changes

1. In §Shared content sync — copier template (the paragraph beginning 'The shared-content sync mechanism between livespec and its sibling livespec-impl-* repos is copier'), remove the phrase 'and a starter project-local loop skill' from the enumeration of canonical scaffold contents. Remove the trailing clause 'with .claude/skills/loop/SKILL.md explicitly excluded from drift detection because local divergence there is expected by the orchestration-layer design.' from the same paragraph. 2. In the following paragraph (beginning 'livespec MUST publish a copier template at templates/impl-plugin/'), remove 'a starter .claude/skills/loop/SKILL.md orchestration driver,' from the enumeration of contents the template MUST contain. The remaining required contents (justfile, lefthook.yml, .mise.toml, pyproject.toml, .claude-plugin/marketplace.json and plugin.json skeletons, the starter SPECIFICATION/ skeleton, and the .github/workflows/ files) MUST stay intact. 3. In the paragraph beginning 'When livespec's templates/impl-plugin/ changes', remove the final sentence '.claude/skills/loop/SKILL.md MUST be excluded from drift detection because local divergence there is expected by the orchestration-layer design (a later propose-change cycle defines that layer in detail).' The exemption is obsolete because the file is no longer in the template's flow.

## Proposal: recast-layer-3-discoverability-nudge-to-livespec-next-only

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Recast the Layer 3 discoverability nudge contract so it applies only to /livespec:next, and drop the parallel-and-symmetric requirement on impl-plugin next skills. Drop the soften-when-driver-absent paragraph, which becomes vacuous under the recast.

### Motivation

The current contract requires both /livespec:next and every impl-plugin's next to surface a discoverability nudge pointing at the local repo's .claude/skills/loop/SKILL.md. Under the architectural recast, impl-plugin repos do NOT carry their own Layer 3 driver — the nudge from an impl-plugin's next would necessarily point at livespec's loop skill in a different repo, which the user cannot invoke in their current shell context anyway. The parallel-symmetric contract MUST be retracted from the impl-plugin side. The /livespec:next nudge remains intact because livespec's loop skill is colocated and directly invocable when the user is in livespec's repo. The softening paragraph for projects where the driver is absent also becomes vacuous: the driver is unambiguously present in livespec and unambiguously absent everywhere else, with no in-between case.

### Proposed Changes

1. In the bullet for the impl-plugin contract (the long bullet beginning 'next — required (new). Ranks the most ripe impl-side action'), remove the trailing block starting at 'The impl-plugin's next SKILL.md prose MUST surface a Layer 3 discoverability nudge on direct user invocation' through the end of that bullet. The wrapper-stays-thin-transport sentence in that block MUST be preserved as a standalone sentence at the bullet's end ('The wrapper at <impl-plugin>'s .claude-plugin/scripts/bin/next.py MUST remain a pure thin-transport pass-through.'). 2. In §Layer 3 discoverability nudge (under §/livespec:next spec-side thin-transport skill), the existing nudge contract on /livespec:next MUST stay intact in spirit but the 'Projects whose .claude/skills/loop/SKILL.md is absent (the file is OPTIONAL per spec.md §Layer 3 — Project-local composition) MAY soften the nudge to a documentation pointer...' paragraph MUST be deleted. Under the recast, livespec's loop skill is present unambiguously; the absent-driver branch has no instance. 3. The cross-reference in spec.md §Three-layer orchestration architecture pointing at 'every impl-plugin's next' (handled by the spec.md finding in this propose-change) MUST be coordinated with this change.

## Proposal: recast-contracts-md-references-from-project-local-to-livespec-resident

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Recast the two contracts.md references to the project-local loop driver so they correctly identify the driver as livespec-resident, not as a generic per-repo concern. Affects §Cross-plugin invocation (line ~52) and §Cross-boundary handoffs item #6.

### Motivation

Under the architectural recast, the loop driver lives in livespec only; calling it project-local is misleading. Each reference MUST be updated to identify the driver as livespec's Layer 3 loop driver. The semantic content (the driver invokes /livespec:next and the active impl-plugin's next through the skill namespace) remains correct and MUST stay intact.

### Proposed Changes

1. In §Cross-plugin invocation (the paragraph beginning 'Cross-plugin invocation (doctor invoking the active impl-plugin's list-memos, the project-local loop driver invoking livespec:next and <impl-plugin>:next, etc.)'), change 'the project-local loop driver' to 'livespec's Layer 3 loop driver'. The remainder of the paragraph MUST stay intact. 2. In §Cross-boundary handoffs item #6 ('The project-local Layer 3 loop driver invokes both /livespec:next and <impl-plugin>:next to compose cross-side recommendations; the cross-side composition itself is defined by a separate propose-change cycle for the orchestration layer.'), change 'The project-local Layer 3 loop driver' to 'livespec's Layer 3 loop driver'. Drop the trailing clause 'the cross-side composition itself is defined by a separate propose-change cycle for the orchestration layer' since the propose-change cycle in question has long since landed and the deferral marker is stale. 3. In §Impl-side query skills cross-boundary doctrine (the paragraph beginning 'The impl-side query skills exist because impl backends are pluggable'), the parenthetical '(doctor, the loop driver, core's next)' MUST stay intact; no edit needed there beyond confirming the reference still resolves under the recast (livespec's loop driver remains a cross-side consumer of the impl-side query skills, so the reference is correct as-is).
