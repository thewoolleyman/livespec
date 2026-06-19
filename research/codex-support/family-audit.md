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
- Four governed sibling repos now have Codex support requirements recorded in
  their own specs:
  - `livespec-dev-tooling` PR #134, merge
    `e76b63621a40ff4f3d88f9681d1503107e82ee79`, cut
    `SPECIFICATION/history/v015/`, and updated
    `SPECIFICATION/non-functional-requirements.md`.
  - `livespec-runtime` PR #48, merge
    `dce528968176c8a80f8cd8b3abe97d988f3b456e`, cut
    `SPECIFICATION/history/v005/`, and updated
    `SPECIFICATION/non-functional-requirements.md`.
  - `livespec-impl-git-jsonl` PR #88, merge
    `e26cebee15bfd43f51a7eab596a75e9b2d719ed0`, cut
    `SPECIFICATION/history/v009/`, and updated
    `SPECIFICATION/constraints.md`.
  - `livespec-impl-beads` PR #62, merge
    `59627827584e43aabeaca9e11b8658b2e32dbfa6`, cut
    `SPECIFICATION/history/v005/`, and updated
    `SPECIFICATION/constraints.md`.

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
| `livespec-impl-beads` | initially one low-urgency `revise` candidate for `proposed_changes/grooming-gherkin-and-gap-detectability.md`; after the repo was refreshed to master, no candidates |
| `livespec-impl-git-jsonl` | no candidates |
| `livespec-runtime` | no candidates |

Sibling PR verification completed on 2026-06-19:

| Repo | Local verification | PR / CI verification |
|---|---|---|
| `livespec-dev-tooling` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 46 targets, 903 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #134 checks passed before merge |
| `livespec-runtime` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 43 targets, 81 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #48 checks passed before merge |
| `livespec-impl-git-jsonl` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 46 targets, 319 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #88 checks passed, including `e2e-cli`, before merge |
| `livespec-impl-beads` | governed `propose_change.py` + `revise.py --post-step-doctor --run-stale-branch-check`; `mise exec -- just check` passed all 44 targets, 917 tests at 100% coverage | doc-only commit/pre-push hooks passed; PR #62 checks passed, including `e2e-cli`, before merge |

## Family-wide gaps

### Repository support

Only core currently exposes Codex project skills. That remains intentional for
the sibling repos as of the 2026-06-19 spec updates:

- `livespec-dev-tooling` owns shared enforcement-suite code, not a user-facing
  `/livespec:*` Driver, so its Codex support is contributor-workflow support
  through `AGENTS.md`, repo hooks, and stable check/wrapper entry points.
- `livespec-runtime` exposes harness-neutral library code. Runtime code must
  stay agent-runtime-neutral and must not branch on Claude, Codex, Pi, or any
  harness identity.
- `livespec-impl-git-jsonl` and `livespec-impl-beads` may need future
  impl-side Codex adapters, but their specs now require those adapters to be
  thin runtime bindings over existing wrapper CLIs and substrate semantics, not
  copies of Claude-specific `SKILL.md` bodies.
- `livespec-driver-claude` is deliberately Claude-specific and has no governed
  `SPECIFICATION/`; no Codex repo update is expected there except explicit
  classification in this audit.

The future distributed path is still open: a `livespec-driver-codex` or
impl-driver package may be appropriate once writable commands and end-to-end
harness proofs are ready.

### Specification coverage

Core and the governed siblings now consistently state the applicable Codex
support requirement.

Observed state:

- `livespec` has Codex-specific non-functional rules, constraints, and
  scenarios.
- `livespec-dev-tooling` now states Codex contributor-workflow support in
  `SPECIFICATION/non-functional-requirements.md`.
- `livespec-runtime` now states Codex contributor-workflow support and
  harness-neutral runtime-code constraints in
  `SPECIFICATION/non-functional-requirements.md`.
- `livespec-impl-beads` now states Codex adapter constraints in
  `SPECIFICATION/constraints.md`.
- `livespec-impl-git-jsonl` now states Codex adapter constraints in
  `SPECIFICATION/constraints.md`.
- `livespec-driver-claude` is intentionally Claude-specific and has no
  governed `SPECIFICATION/`.

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

The sibling updates above were manually verified with governed LiveSpec
wrappers, local `just check`, commit hooks, pre-push hooks, and PR/CI checks.
They were not verified by launching Codex CLI inside each sibling checkout.
Do not claim full family-wide Codex runtime verification until that evidence is
added.

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
- Sibling specs now explicitly state that Claude-only hooks are not assumed to
  run under Codex, and any Codex adapter or hook replacement must be manually
  verified before support is claimed.

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

1. Add Codex CLI runtime evidence for the changed sibling repos before claiming
   family-wide support. At minimum, record whether Codex loads `AGENTS.md`,
   respects the repo mutation protocol, and can identify the relevant wrapper
   or check entry points without editing.
2. Audit Claude-only hooks one by one and classify them as:
   Codex replacement required, AGENTS/repo-hook coverage sufficient, or
   Claude-driver-only by design.
3. Continue `livespec-zkmn.1` high-level e2e/golden-master work with Codex as a
   supported agent-runtime dimension and keep this document updated with the
   evidence.
4. Track telemetry/cost follow-ups through `livespec-impl-beads-zbl` and
   `livespec-dev-tooling-e60`; Codex should remain tokens-primary, not
   Claude-cost-derived.

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
