---
proposal: proposal-critique-v04.md
decision: modify
revised_at: 2026-04-22T00:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v04

## Provenance

- **Proposed change:** `proposal-critique-v04.md` (in this directory)
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context)
- **Revised at:** 2026-04-22 (UTC)
- **Scope:** v004 PROPOSAL.md + companion `bash-skill-script-
  style-requirements.md` → v005 PROPOSAL.md + revised companion

## Critique scope

This pass focused specifically on
`bash-skill-script-style-requirements.md` (the style doc) and the
downstream consequences of its rules on `PROPOSAL.md` and on any
realistic implementation. The driving questions: possibility,
pragmatism, maintainability, internal/cross-doc consistency.

## Summary of dispositions

| Severity | Count | Accepted | Modified-on-accept | Deferred | Rejected |
|---|---|---|---|---|---|
| Major | 5 | 2 | 3 | 0 | 0 |
| Significant | 8 | 4 | 4 | 0 | 0 |
| Smaller | 7 | 5 | 2 | 0 | 0 |

Items B18 (enforcement reframing), B19 (mise for tool versions),
and B20 (decompose doctor-static) were added mid-interview in
response to user-supplied requirements and are treated as
accepted as-proposed.

---

## Disposition by item

### Major

**B1. `main "$@"` final-line rule contradicts sourceable guard.**
Decision: **Accepted.** Guard wins; drop the bare-`main` rule.
§"Functions and `main`" rewritten to point at the guard as the
required final-statement form; the "older bash idioms"
parenthetical deleted. Preserves source-for-tests strategy.

**B2. 100% pure-library coverage via `kcov` infeasible.**
Decision: **Accepted (modified).** Pure-library threshold lowered
from 100% to ≥ 95%. Overall ≥ 80% unchanged. Accommodates `kcov`'s
DEBUG-trap granularity artifacts while still catching untested
functions.

**B3. AST-level enforcement checks hard to implement.**
Decision: **Accepted (modified).** Pin `tree-sitter-bash` via
`mise` (per B19) as the concrete parser. The three checks
(cross-library private-call, source-cycle, global-variable-write)
become genuinely implementable with a named non-bash binary in
the toolchain. Style doc names `tree-sitter-bash` explicitly in
every relevant section.

**B4. Complexity thresholds in combination too strict.**
Decision: **Accepted (modified).** CCN limit raised from ≤ 7 to
≤ 10 (McCabe's own bound); positional-arg limit raised from ≤ 4
to ≤ 6. LLOC ≤ 50 per function and ≤ 300 per file unchanged.
Eliminates over-decomposition pressure on idiomatic patterns
(parse_options, validators, main orchestration).

**B10. Category error: dev-time checks inside runtime bundle.**
Decision: **Accepted.** Split runtime from dev-time:
- Runtime (inside the shipped bundle): `scripts/bash-
  boilerplate.sh`, `scripts/dispatch`, `scripts/doctor/run-static`,
  and `scripts/doctor/static/<slug>` per-check executables.
- Dev-time (at `<livespec-repo-root>/dev-tooling/`):
  `enforcement/check-*` architectural-check executables,
  `Makefile`, `.mise.toml`, `.pre-commit-config.yaml`, and a
  symlinked `bash-boilerplate.sh`.
- `scripts/checks/` removed from the bundle layout entirely.
- "checks" as a directory name dropped in favor of "enforcement"
  for the dev-time tree (disambiguates from `doctor`'s static
  checks).

### Significant

**B5. `noclobber` always-on is disruptive.**
Decision: **Accepted.** Removed from mandatory strict mode.
Authors opt-in locally where accidental-overwrite protection
matters. Strict mode retains `errexit`, `errtrace`, `pipefail`,
`nounset`.

**B6. `BASH_*` env var namespace collision.**
Decision: **Accepted.** Renamed `BASH_XTRACE`→`LIVESPEC_XTRACE`
and `BASH_VERBOSE`→`LIVESPEC_VERBOSE`. Boilerplate helper
`handle_bash_xtrace`→`handle_xtrace`. Forbidden alternative names
updated accordingly.

**B7. `realpath` portability in source pattern.**
Decision: **Accepted.** Non-sibling source pattern replaced with
pure-bash `cd ... && pwd`. No external tool dependency in the
sourcing critical path.

**B8. Pure library env-var ban over-restricts.**
Decision: **Accepted.** Pure libraries MUST NOT **write**
environment variables. Reads are permitted only for a small
allow-list: `IFS`, `LC_ALL`, `LANG`, `PATH`, `HOME`, `TMPDIR`.
Tests can set these in `setup`; the rule remains grep-enforceable.

**B9. Coverage gate not runnable on non-Linux.**
Decision: **Accepted (modified).** Docker wrapper at
`dev-tooling/scripts/coverage-in-docker` (or equivalent path)
runs `kcov` inside a pinned Linux container on non-Linux hosts.
`make check-coverage` dispatches transparently. Enforcement suite
is formally Linux-only; the wrapper is the portable bridge.

**B11. Complexity waivers.**
Decision: **Accepted.** No per-function waivers permitted.
Relaxed thresholds from B4 plus mise-pinned `shellmetrics` (from
B19) make the gate predictable enough to not need an escape hatch.
Refactor is the answer for any function that busts the gate.

**B12. Bash version floor breaks portability premise.**
Decision: **Accepted (modified).** Core premise error fixed:
- **Single** bash standard targeting **3.2.57 or newer** (not
  two-tier runtime/dev). macOS's default `/bin/bash` is 3.2.57;
  the skill scripts execute on the end user's machine, so 3.2
  compatibility is load-bearing.
- Bash 4.x features forbidden: namerefs (`declare -n` / `local
  -n`), associative arrays (`declare -A`), `mapfile`/`readarray`,
  `${var,,}`/`${var^^}`.
- `"${arr[@]-}"` (empty-default expansion) mandated for
  possibly-empty array expansion under `nounset`.
- `bash-boilerplate.sh` asserts `BASH_VERSINFO >= 3.2`; exits
  `127` with install guidance otherwise.
- `mise` pins bash to `3.2.57` exactly for dev and CI so
  accidental 4.x constructs fail at authoring time.
- The style doc's stale sentence *"Skill runtime environments
  ship bash 5.x"* removed (the premise was wrong — Claude Code's
  bash tool runs on the end user's machine).

**B18. Enforcement-section framing.**
Decision: **Accepted (modified).** Mid-interview clarification:
enforcement is **invocation-surface-agnostic** and expressed as
Makefile targets. Pre-commit, pre-push, CI, and manual
invocation are all consumers of the same targets, not separate
owners. Style doc's §"Enforcement via git hooks and CI" renamed
to §"Enforcement suite" with a canonical check-target table and
a short per-invocation-surface subsection listing which targets
each surface runs. Linux-only stated once; per-target-
distributed macOS/Alpine carve-outs removed.

**B19. Mise for tool dependency/version management.**
Decision: **Accepted.** Mid-interview requirement:
every external tool the enforcement suite depends on is pinned
via `mise` in a committed `.mise.toml` at the livespec repo
root. Includes bash=3.2.57, shellcheck, shfmt, shellharden,
shellmetrics, kcov, bats-core, bats-assert, bats-support, jq,
tree-sitter-bash. Scatter-pinned per-tool language elsewhere in
the style doc collapses into the `mise` mandate.

### Smaller

**B13. Test-file dual-naming boundary.**
Decision: **Accepted.** Both patterns kept and explicitly
documented:
- Per-script tests at `tests/scripts/<path>.bats` and
  `tests/dev-tooling/<path>.bats` exercise a script's contract.
- Per-spec-file tests at `tests/test_<spec>.bats` exercise
  rule-coverage end-to-end; these are the tests referenced by
  `heading-coverage.json`.

**B14. `tests/` nested skeleton.**
Decision: **Accepted.** PROPOSAL.md §"Testing approach" skeleton
updated to show the full mirrored tree (`tests/scripts/doctor/
static/*.bats`, `tests/dev-tooling/enforcement/*.bats`), and
states the one-to-one mirror rule explicitly.

**B15. Variadic function mechanical definition.**
Decision: **Accepted.** Variadic = reads `"$@"`, `"$*"`,
`"${@:N}"`, or `"${*:N}"` in the body. `# variadic` annotation
required; CI cross-verifies annotation against body usage.
`main` exempt from the annotation requirement (always implicitly
variadic).

**B16. Library header format.**
Decision: **Accepted.** Structured directive format mandated:
```
# concern: <one sentence>
# prefix: <identifier>
# purity: pure | impure
# sources:
#   - ./path-a.sh
#   - ./path-b.sh
```
Enforcement check verifies directive presence, correct values,
and `sources` list consistency with actual `source` statements.

**B17. Interactivity-check ban.**
Decision: **Accepted (modified).** Refined from absolute ban to
prompt-path-only ban: `[[ -t 0 ]]` and `[[ -p /dev/stdin ]]` MAY
be used to differentiate stdin-pipe from stdin-file-redirect
(both non-interactive); `[[ -t 1 ]]` and `tty -s` remain
forbidden outright; any branch leading to a user prompt remains
forbidden.

**B20. Decompose `doctor-static`.**
Decision: **Accepted.** Mid-interview decomposition:
- `scripts/doctor-static` (monolithic) replaced by
  `scripts/doctor/run-static` (orchestrator) plus per-check
  executables at `scripts/doctor/static/<slug>`.
- Slug-only naming: filenames and `check_id` values (e.g.,
  `doctor-out-of-band-edits`) are stable slugs, not positional
  numbers. Insert/delete of checks is a non-event; no
  number-stability invariant to guard.
- JSON findings' `check_id` format: `doctor-<slug>`.
- Per-check `.bats` tests at `tests/scripts/doctor/static/
  <slug>.bats`.
- PROPOSAL.md §"Static-phase checks" rewritten as a slug-keyed
  bulleted list; all prose references to "check #N" replaced
  with slug form.

---

## Self-consistency check

Post-revision invariants rechecked:

- **Single bash standard.** Both runtime (bundle) and dev-tooling
  (enforcement suite) target bash 3.2.57 or newer; no two-tier
  rules. `.mise.toml` pins bash to `3.2.57` exactly so dev/CI
  match macOS end users.
- **Runtime vs dev-time split.** Skill bundle contains only what
  end users need at livespec runtime. Dev-tooling lives at the
  repo root under `dev-tooling/`, outside the bundle, and is
  never shipped to users.
- **Single name for each concept.** "checks" is no longer
  overloaded: `doctor/static/*` are "static checks" (runtime
  behavior); `dev-tooling/enforcement/*` are "enforcement scripts"
  (livespec-dev behavior). The word "checks" without qualifier
  is retired.
- **Recreatability.** A competent implementer can generate the
  livespec plugin + built-in template + sub-commands + enforcement
  suite + dev-tooling scaffolding from v005 PROPOSAL.md +
  `livespec-nlspec-spec.md` + the revised
  `bash-skill-script-style-requirements.md` alone.
- **Cross-doc consistency.** Style doc and PROPOSAL.md agree on:
  script classifications (executable vs library), file-naming
  conventions (no .sh on executables, .sh on libraries, slugs
  for doctor checks), JSON finding shape (`doctor-<slug>`
  check_ids), exit codes (0/1/3/126/127), tool pinning (via mise),
  enforcement framing (Makefile entry points).

## Outstanding follow-ups

Filed as the first batch of `propose-change`s after `seed`:

- Detailed authoring of each template prompt's input/output JSON
  schemas and prompts themselves.
- Migration of brainstorming-folder companion documents
  (`subdomains-and-unsolved-routing.md`, `prior-art.md`,
  `bash-skill-script-style-requirements.md` etc.) into the seeded
  `SPECIFICATION/`.
- Authoring of the specific enforcement-check scripts under
  `dev-tooling/enforcement/`, plus the Makefile entry points,
  `.mise.toml`, and `.pre-commit-config.yaml`.
- Optional post-v1: bash-3.2 smoke-test target inside a pinned
  Linux container to catch accidental 4.x leakage.

## What was rejected

Nothing was rejected outright. Two classes of reshape occurred:

- Several items underwent modification-on-accept to align with
  cross-cutting framing decisions introduced mid-interview
  (B12 re-scoped by the single-standard / mise-pin-to-3.2 thread;
  B2/B9 re-scoped by the B18 Linux-only invocation framing).
- My initial "two-tier standard" recommendation for B12 (3.2 at
  runtime, 4.4+ for dev-tooling) was retracted on user pushback
  in favor of a single uniform 3.2-compatible standard. Noted in
  the B12 disposition above.
