# Codex family support audit

Date: 2026-06-19

## Purpose

This document records what remains to make OpenAI Codex a maintained
dogfooding surface across the livespec family, not just the core `livespec`
checkout. It extends the initial core-only audit in `audit.md`, the bootstrap
plan in `plan.md`, and the read-only adapter proof in `adapter-proof.md`.

The target is reproducibility for another agent runtime, especially the future
Pi driver/harness work: which repositories need support, what was proven, what
is still Claude-specific, and which next changes should be made through normal
LiveSpec processes.

## Completed baseline

- Core `livespec` has committed Codex project skills under `.agents/skills/`
  for `livespec-help`, `livespec-next`, and `livespec-doctor`.
- Those adapters were proven with separate `codex exec` processes in PR #457.
- The adapter sync check landed in PR #460 and is part of `just check`.
- Core `SPECIFICATION/non-functional-requirements.md` was repaired in PR #465
  to describe the project-local `.agents/skills/livespec-*` path over core
  prose and wrappers.
- Core operational instructions in `AGENTS.md` were updated in PR #466 with
  parity-critical repository mutation discipline for Codex.
- Wrapper `--help` zero-exit behavior was fixed in PR #467.
- The core spec wording repair for Driver/prose/binding ownership landed in
  PR #471 through the governed propose-change -> revise lifecycle:
  - `SPECIFICATION/history/v119/` accepts
    `codex-driver-spec-wording.md`, repairing stale `spec.md` and CLI e2e
    harness wording that treated core as owning Claude skill prompts.
  - `SPECIFICATION/history/v120/` accepts
    `codex-contract-binding-wording.md`, repairing remaining `contracts.md`
    SKILL.md terminology and co-editing `tests/heading-coverage.json` for the
    renamed H2 headings.
- The high-level e2e Beads item `livespec-zkmn.1` now has Codex-specific
  acceptance criteria and `codex-support` / `e2e-codex` labels.

## Current live checks

Core spec-side `next` run:

```json
{"candidates":[{"action":"prune-history","reason":"118 unpruned history versions; consider pruning","urgency":"low"}],"pagination":{"has_more":false,"limit":5,"offset":0,"total":1}}
```

Local family checkout inventory:

| Repo | Governed spec | `.agents/skills` | `.claude-plugin` | Beads tenant |
|---|---:|---:|---:|---:|
| `livespec` | yes | yes | yes | yes |
| `livespec-dev-tooling` | yes | no | no | yes |
| `livespec-driver-claude` | no | no | yes | yes |
| `livespec-impl-beads` | yes | no | yes | yes |
| `livespec-impl-git-jsonl` | yes | no | yes | yes |
| `livespec-runtime` | yes | no | no | yes |

All six checkouts were clean on `master` at audit time.

Open Beads work summary relevant to Codex:

| Tenant | Relevant open item | Why it matters |
|---|---|---|
| `livespec` | `livespec-zkmn.1` — W7 golden-master acceptance and orchestrator convergence | This is the high-level e2e/swap-proof thread. Its acceptance criteria were updated on 2026-06-19 to require Codex as an explicit supported agent-runtime dimension where runtime behavior is part of the proof. |
| `livespec-impl-beads` | `livespec-impl-beads-zbl` — multi-provider cost observability: tokens-primary + Codex + self-hosted | Codex telemetry/cost extraction is explicitly deferred here; do not assume Claude Code telemetry covers Codex. |
| `livespec-dev-tooling` | `livespec-dev-tooling-e60` — agent-loop efficiency and Honeycomb observability | Cross-runtime agent observability belongs here or in a child item; Codex should be named when the item is refined. |

Other open work exists in each tenant, but the items above are the ones found
with direct Codex/e2e relevance.

Sibling spec-side `next` runs on 2026-06-19:

| Repo | `next` result |
|---|---|
| `livespec-dev-tooling` | no candidates |
| `livespec-impl-beads` | one low-urgency `revise` candidate for `proposed_changes/grooming-gherkin-and-gap-detectability.md` |
| `livespec-impl-git-jsonl` | no candidates |
| `livespec-runtime` | no candidates |

## Family-wide gaps

### Repository support

Only core currently exposes Codex project skills. The other governed
repositories rely on `AGENTS.md` plus ad hoc reasoning. That may be enough for
ordinary coding instructions, but it is not equivalent to the core read-only
LiveSpec adapter proof.

Each governed repo needs an explicit decision:

- no project skill needed because it only consumes core `/livespec:*`
  operations through repository instructions;
- project-local Codex skills should be added for impl-side commands such as
  next/list/capture operations; or
- Codex support should wait for a future distributed `livespec-driver-codex`
  or impl-driver package.

### Specification coverage

Core `non-functional-requirements.md` now states Codex support, but the
family-wide specifications do not consistently do so.

Observed state:

- `livespec` has Codex-specific non-functional rules, constraints, and
  scenarios.
- `livespec-dev-tooling` has no Codex-specific spec text.
- `livespec-impl-beads` mentions `CLAUDE.md` / `AGENTS.md` loading in
  `contracts.md`, but does not have a Codex-specific non-functional spec file.
- `livespec-impl-git-jsonl` mentions `CLAUDE.md` / `AGENTS.md` loading in
  `contracts.md`, but does not have a Codex-specific non-functional spec file.
- `livespec-runtime` has no Codex-specific spec text.
- `livespec-driver-claude` is intentionally Claude-specific and has no
  governed `SPECIFICATION/`.

Core had stale high-level wording in `SPECIFICATION/spec.md` and
`SPECIFICATION/contracts.md` that described the `livespec` core plugin bundle
as containing `skills/<sub-command>/SKILL.md`, treated prose+CLI decomposition
as future work, and expected an installed core plugin skill tree for the CLI
e2e harness. The `codex-driver-spec-wording` worktree repairs those clauses via
`SPECIFICATION/history/v119/` and `SPECIFICATION/history/v120/`; once the
corresponding PR lands, this gap is closed for core.

### Manual verification

Manual Codex verification exists only for core read-only operations:

- adapter discovery via `codex debug prompt-input`;
- help adapter reads `.agents/skills/livespec-help/SKILL.md` and
  `.claude-plugin/prose/help.md`;
- next adapter reads `.agents/skills/livespec-next/SKILL.md` and names
  `.claude-plugin/scripts/bin/next.py`;
- doctor adapter reads `.agents/skills/livespec-doctor/SKILL.md` and names
  `.claude-plugin/scripts/bin/doctor_static.py`.

No manual Codex verification has been done yet for:

- `livespec-dev-tooling`;
- `livespec-impl-beads`;
- `livespec-impl-git-jsonl`;
- `livespec-runtime`;
- `livespec-driver-claude` as a deliberately non-Codex driver package.

### High-level e2e testing

The relevant thread is `livespec-zkmn.1`, whose description names a
golden-master acceptance harness across the git-jsonl and Beads/Fabro
orchestrators. On 2026-06-19 its formal acceptance criteria were updated to
make Codex a first-class agent-runtime dimension.

The acceptance criteria now require:

- Codex can load the repo instruction surface for each tested checkout;
- Codex can invoke verified project-local adapters where they exist;
- Codex is represented in observability as tokens-primary rather than
  Claude-specific cost spans;
- Codex-specific limitations are explicit rather than silently inherited from
  Claude Code.

### Non-skill mechanisms

Observed hooks and non-skill mechanisms:

- All family repos have repo-level git hooks / lefthook discipline.
- Multiple repos have `.claude/hooks/livespec_footgun_guard.py`, which is a
  Claude Code PreToolUse guard. This does not run under Codex.
- `livespec-driver-claude` ships `.claude-plugin/hooks/` with
  `block-auto-memory.sh` and `warn-plan-persistence.sh`. These are
  Claude-driver runtime mechanics, not Codex mechanics.
- Core `AGENTS.md` now carries the critical Codex-facing replacement for some
  hook protection: worktree -> PR -> merge -> cleanup, `mise exec -- git`,
  never `--no-verify`, and primary checkout protection.

Open questions:

- Which Claude hook behaviors need a Codex-native equivalent, and which should
  stay Claude-only?
- Should Codex rely only on `AGENTS.md` plus repo git hooks for primary
  checkout and no-`--no-verify` discipline, or should a Codex adapter/checklist
  add an explicit pre-edit gate before mutating operations?
- Should impl-plugin memo/plan-persistence redirection be represented in
  Codex instructions, in Beads/Dolt work-item capture commands, or left
  Claude-driver-only?

## Recommended next sequence

1. For each governed sibling repo, use the existing `livespec next` / Beads
   check and file a repo-local proposed spec change if its non-functional
   specification needs to state Codex support.
2. Decide the minimum project-local Codex adapter surface per repo:
   no adapter, read-only adapter, or impl-side thin-transport adapter.
3. Audit Claude-only hooks one by one and classify them as:
   Codex replacement required, AGENTS/repo-hook coverage sufficient, or
   Claude-driver-only by design.
4. Add manual Codex verification evidence for every changed repo before
   claiming family-wide support.

## Reproduction commands

```bash
/usr/bin/python3 .claude-plugin/scripts/bin/next.py \
  --project-root /data/projects/livespec \
  --spec-target /data/projects/livespec/SPECIFICATION \
  --limit 5 \
  --offset 0

for d in /data/projects/livespec*; do
  [ -d "$d/.git" ] || [ -f "$d/.git" ] || continue
  printf '%s\t' "${d##*/}"
  git -C "$d" rev-parse --show-toplevel 2>/dev/null | tr '\n' '\t'
  git -C "$d" branch --show-current 2>/dev/null | tr '\n' '\t'
  [ -d "$d/SPECIFICATION" ] && printf 'SPEC=yes\t' || printf 'SPEC=no\t'
  [ -d "$d/.agents/skills" ] && printf 'agents=yes\t' || printf 'agents=no\t'
  [ -d "$d/.claude-plugin" ] && printf 'claude_plugin=yes\t' || printf 'claude_plugin=no\t'
  [ -d "$d/.beads" ] && printf 'beads=yes\n' || printf 'beads=no\n'
done | sort
```

Beads summary command, run through the 1Password environment wrapper:

```bash
for d in /data/projects/livespec /data/projects/livespec-driver-claude \
  /data/projects/livespec-impl-beads /data/projects/livespec-impl-git-jsonl \
  /data/projects/livespec-runtime /data/projects/livespec-dev-tooling; do
  [ -d "$d/.beads" ] || continue
  name=${d##*/}
  tenant=${name//-/_}
  var="BEADS_DOLT_PASSWORD_${tenant}"
  pw=${!var-}
  printf "=== %s ===\n" "$name"
  if [ -z "$pw" ]; then
    printf "missing-env:%s\n" "$var"
    continue
  fi
  (
    cd "$d" &&
      export BEADS_DOLT_PASSWORD="$pw" LIVESPEC_BD_PATH=/usr/local/bin/bd &&
      /usr/local/bin/bd list --status open --json 2>/dev/null |
        jq -r '.[] | [.id,.priority,.issue_type,.title] | @tsv'
  )
done
```
