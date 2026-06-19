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

Manual Codex verification exists for core read-only operations:

- adapter discovery via `codex debug prompt-input`;
- help adapter reads `.agents/skills/livespec-help/SKILL.md` and
  `.claude-plugin/prose/help.md`;
- next adapter reads `.agents/skills/livespec-next/SKILL.md` and names
  `.claude-plugin/scripts/bin/next.py`;
- doctor adapter reads `.agents/skills/livespec-doctor/SKILL.md` and names
  `.claude-plugin/scripts/bin/doctor_static.py`.

On 2026-06-19, read-only Codex CLI probes were launched from each sibling
checkout with `codex exec --sandbox read-only`. Every probe confirmed that
Codex loaded or read the repository-root `AGENTS.md`, identified relevant
non-mutating verification surfaces, and left `git status --short` clean.

| Repo | Codex-loaded instruction surface | Mutation protocol evidence | Non-mutating surfaces Codex identified |
|---|---|---|---|
| `livespec-dev-tooling` | `/data/projects/livespec-dev-tooling/AGENTS.md` | Has Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`; does **not** carry full worktree -> PR -> merge -> cleanup lifecycle. | `just check-scoped`, `just check`, `just check-static`, `just check-changed`, `just check-pre-commit`, `just check-pre-push`, individual `just check-*` targets. |
| `livespec-runtime` | `/data/projects/livespec-runtime/AGENTS.md` | Has Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`; does **not** carry full worktree -> PR -> merge -> cleanup lifecycle. | `just check`, `just check-static`, `just check-changed`, `just check-lint`, `just check-format`, `just check-types`, `just check-coverage`, `just check-pre-commit`, `just check-pre-push`. |
| `livespec-impl-git-jsonl` | `/data/projects/livespec-impl-git-jsonl/AGENTS.md` | Has Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`; full lifecycle appears in README/justfile/hook docs, not in `AGENTS.md`. | `mise exec -- just check`, `check-pre-commit`, `check-pre-push`, `check-red-green-replay`, `check-static`, `check-changed`, store checks, and read-only wrappers `list_work_items.py`, `list_memos.py`, `next.py`, `detect_impl_gaps.py`. |
| `livespec-impl-beads` | `/data/projects/livespec-impl-beads/AGENTS.md` | Has Red-Green-Replay, `mise exec -- git ...`, and never `--no-verify`; full lifecycle appears in README/justfile/dispatcher docs, not in `AGENTS.md`. | `just check-static`, `just check-format`, `just check-lint`, `just check-types`, `just changed-files`, `just check-red-green-replay`, `just check-work-item-merge-evidence`, read/check wrappers, and dispatcher `ledger-check`, `spec-check`, `janitor-check`. |
| `livespec-driver-claude` | `/data/projects/livespec-driver-claude/AGENTS.md` | Has worktree secondary checkout guidance, `mise exec -- git ...`, and never `--no-verify`; does **not** carry the full worktree -> PR -> merge -> cleanup lifecycle. | `just check` for plugin-structure, hook tests, and mock e2e. Codex correctly classified the repo as deliberately Claude-specific and not a Codex adapter host. |

Conclusion: sibling runtime evidence now exists, but family-wide Codex support
is still not fully claimable. The missing piece is instruction parity: sibling
`AGENTS.md` files should carry the same complete repo mutation protocol now
present in core before Codex is trusted for mutating family-wide work.

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
- Each active family checkout has `.claude/hooks/livespec_footgun_guard.py`.
  `livespec-driver-claude` also has Driver-plugin hooks under
  `.claude-plugin/hooks/`.
- Sibling specs now explicitly state that Claude-only hooks are not assumed to
  run under Codex, and any Codex adapter or hook replacement must be manually
  verified before support is claimed.

Hook classification:

| Mechanism | Locations | Classification | Rationale |
|---|---|---|---|
| `.claude/hooks/livespec_footgun_guard.py` | `livespec`, `livespec-dev-tooling`, `livespec-driver-claude`, `livespec-impl-beads`, `livespec-impl-git-jsonl`, `livespec-runtime` | Codex replacement required before mutating Codex automation; AGENTS/repo-hook coverage sufficient for read-only probes and human-supervised verification. | This Claude Code `PreToolUse` Bash guard blocks `git commit/push --no-verify`, `LEFTHOOK=0/false`, and `git config core.bare=true` before a command runs. Codex does not run it. Git hooks and branch protections catch many commit/push failures later, but cannot stop direct file edits in a primary checkout. |
| `.claude/settings.json` `SessionStart` plugin/bootstrap hooks | active family checkouts | Claude-driver-only by design. | These run Claude plugin installation or project hook setup. Codex has no proven livespec marketplace/plugin path; project-local `.agents/skills` plus repo instructions are the current Codex path. |
| `.claude/settings.json` `PreToolUse` background/subagent guards | active family checkouts where configured | Claude-driver-only unless a future Codex runtime exposes equivalent hook events. | The hooks enforce Claude Code tool/session behavior. Current Codex evidence covers read-only execution, not background tool lifecycle integration. |
| `livespec-driver-claude/.claude-plugin/hooks/block-auto-memory.sh` | `livespec-driver-claude` plugin | Claude-driver-only by design. | This prevents Claude Code auto-memory behavior in the Claude Driver. It is not a cross-runtime livespec contract. |
| `livespec-driver-claude/.claude-plugin/hooks/warn-plan-persistence.sh` | `livespec-driver-claude` plugin | Claude-driver-only by design, with possible future documentation analogue for other runtimes. | This warns Claude users about plan persistence. Codex support should not inherit it silently; if Pi/Codex need equivalent guidance it belongs in their runtime instructions or driver, not in the Claude Driver. |
| Repo git hooks and `check-primary-checkout-commit-refuse-hook-installed` | all governed family repos | AGENTS/repo-hook coverage sufficient for commit/push enforcement once installed. | These are runtime-neutral git/just mechanisms. They do not replace pre-edit instruction loading, but they are the correct backstop for commit/push discipline under Codex. |

## Recommended next sequence

1. Sync the complete core repository mutation protocol into sibling
   `AGENTS.md` files, using each repo's normal worktree -> PR -> merge ->
   cleanup path. The Codex runtime probes proved those files load, but they do
   not yet carry the full lifecycle.
2. Continue `livespec-zkmn.1` high-level e2e/golden-master work with Codex as a
   supported agent-runtime dimension and keep this document updated with the
   evidence.
3. Track telemetry/cost follow-ups through `livespec-impl-beads-zbl` and
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
