# Surface inventory — files to touch, per repo

The concrete implementation map. Paths are repo-relative unless absolute.
**F** = livespec-orchestrator-beads-fabro, **C** = livespec (CORE).

## CORE (livespec) — contract + schema + doctor + self-heal lib + guard template

### Contract prose (spec-side; ritual-exempt `chore(spec):`/`docs:`)
- `SPECIFICATION/non-functional-requirements.md` L1006 (`**Canonical source.**`)
  + L1008 (`**Local consumption rule.**`), under H3 `### Fleet secrets —
  1Password Environment as canonical source` (owned by H2 `## Constraints`
  L443). Generalize 1Password/`with-livespec-env.sh` to the wrapper-agnostic
  `credential_wrapper` (1Password becomes the reference default).
- `SPECIFICATION/contracts.md` L250 (§`## Fleet agent-instruction core`, L246) —
  the authored-once beads-runtime prose already says "per-project
  credential-injection wrapper"; bind that phrase to the `credential_wrapper`
  key. L258 — the beads-access guard term `with-<id>-env.sh` → generalize to
  "the project's configured `credential_wrapper`". L59-63 (§`## Spec-side CLI
  contract`) — add the new key to core's schema-key description. L133-135
  (H3 `### config-named-cli-callability` under `## Doctor cross-boundary
  invariants` L127) — extend the callability invariant to the wrapper.
- `docs/installation.md` L200-203; root `AGENTS.md` L305-313 — authored-once
  restatements of the 1Password coupling; generalize wording.
- **heading-coverage**: only if a NEW `## ` H2 is added. Reworking existing H2
  bodies / the H3 secrets section does NOT trip `tests/heading-coverage.json`.

### Schema triplet (product `.py`/JSON; `credential_wrapper: list[str]`, optional, default `[]`)
- `.claude-plugin/scripts/livespec/schemas/livespec_config.schema.json` — add
  `credential_wrapper` property (`type:array, items:{type:string}, minItems:1`),
  beside `spec_clis` (L50) / `orchestrator` (L106). Root is
  `additionalProperties:true` so unknown keys are tolerated until declared.
- `.claude-plugin/scripts/livespec/schemas/dataclasses/livespec_config.py` —
  add `credential_wrapper: list[str] = field(default_factory=list)` to
  `LivespecConfig` (L106-133). Precedent: `SpecClis` (L54-85).
- `.claude-plugin/scripts/livespec/validate/livespec_config.py` — materialize
  `credential_wrapper=validated.get("credential_wrapper", [])` in `_raw_validate`
  (L99-114).
- Drift guard: `dev-tooling/checks/schema_dataclass_pairing.py` fails
  `just check` if the triplet drifts.
- Mirror tests (Red-Green-Replay, ONE failing test staged at Red):
  `tests/livespec/schemas/dataclasses/test_livespec_config.py`,
  `tests/livespec/validate/test_livespec_config.py`.

### Doctor callability
- `.claude-plugin/scripts/livespec/doctor/static/config_named_cli_callability.py`
  `_named_clis` (L112-138) — add `("credential_wrapper", config.credential_wrapper)`
  guarded on non-empty (like the orchestrator block L130-137). Validates the
  wrapper's first token resolves to an executable.
- Mirror test: `tests/livespec/doctor/static/test_config_named_cli_callability.py`.

### Self-heal helper (CORE-owned, vendored into orchestrator via livespec_runtime)
- New pure `ensure_credentials(required, credential_wrapper, environ)` per
  design §1. Home: `livespec_runtime` (vendored as `F
  _vendor/livespec_runtime`) so both CORE bin scripts and orchestrator
  `_bootstrap` can call it. Fully unit-testable (pure argv/exec decision).

### Guard template (fleet-tier)
- `templates/impl-plugin/.claude/hooks/beads_access_guard.py` L23 —
  `_WRAPPER_RE = re.compile(r"with-[a-z0-9-]+-env\.sh")` → drive recognition
  from the resolved `credential_wrapper` first token (keep `with-*-env.sh` as a
  fallback default). Test: `tests/test_template_beads_access_guard.py`.
- `templates/impl-plugin/.livespec.jsonc.jinja` (near the L33-39 onboarding
  TODO) — scaffold/document the `credential_wrapper` key.
- Root `.livespec.jsonc` — add the key as the reference example.

## Orchestrator (F) — self-heal wiring + guard + skills

- **Chokepoint**: `.claude-plugin/scripts/bin/_bootstrap.py::bootstrap()` (L12)
  — every fabro CLI's first statement. After sys.path setup, read
  `credential_wrapper` (+ required-secret list, e.g. `["BEADS_DOLT_PASSWORD"]`)
  from the governed project's `.livespec.jsonc` via `commands/_jsonc.py` +
  `commands/_config.py`, then call `ensure_credentials(...)`. Covers `next.py`,
  `list_work_items.py`, `detect_impl_gaps.py`, `orchestrate.py`,
  `orchestrator.py`, `dispatcher.py`, `mint_app_token.py`, +
  `close_work_item`/`groom`/`rebalance_ranks`.
- **Secondary guard/raise**: `_beads_client.py::_invoke` (L432) /
  `make_beads_client` (L708) — actionable raise when `BEADS_DOLT_PASSWORD`
  absent (in-process callers that bypass `bin/`).
- **Guard**: `.claude/hooks/beads_access_guard.py` + `beads-access-guard.sh` —
  same generalization as the CORE template. (Both files exist here AND as the
  CORE template seed; keep in sync.)
- **SKILL.md prose** (optional now that self-heal exists, but good hygiene) —
  the thin-transport skills carry literal bare invocations:
  `skills/next/SKILL.md:15`, `skills/list-work-items/SKILL.md:15`,
  `skills/detect-impl-gaps/SKILL.md:15`, `skills/orchestrate/SKILL.md:12`.
  Codex twins under `.claude-plugin/.codex-plugin/skills/*` mirror (e.g.
  `next/SKILL.md:59`). Heavyweight skills delegate to these.
- Pin timing: F pins CORE via `compat.pinned` to a RELEASE tag; the schema key
  must be in a CORE release before F can read it. Cross-repo fan-out `bump-pin`
  rewrites the pin on the next CORE `feat:`/`fix:` release.

## Guard blind spots (what generalization must fix)

1. Does NOT catch `python3 .../next.py` (internal `bd`) — the dominant path.
   → self-heal covers this; guard remains for RAW `bd`.
2. Only knows `bd`/`dolt`/`mysql`; `mysql` only when `3307`/`127.0.0.1` present.
3. Fail-open (non-Bash / malformed / no python3 → pass).
4. Wrapper detection is a loose substring (any mention of `with-*-env.sh`
   passes, even a `;`-chained bare `bd` in another segment).
5. Registered only in F + git-jsonl; CORE template is the adopter seed.

## Fleet rollout (cross-tenant — filed from each owning repo's OWN session)

All 8 fleet members run server-mode beads @127.0.0.1:3307 → all need
`BEADS_DOLT_PASSWORD` and all should carry `credential_wrapper`.

| repo | wrapper to configure | guard installed? | action |
|---|---|---|---|
| livespec (CORE) | `["/usr/local/bin/with-livespec-env.sh","--"]` | NO | add key + install guard |
| livespec-orchestrator-beads-fabro | same | YES | add key; generalize guard |
| livespec-orchestrator-git-jsonl | same | YES | add key; generalize guard |
| livespec-dev-tooling | same | NO | add key + install guard |
| livespec-driver-claude | same | NO | add key + install guard |
| livespec-driver-codex | same | NO (no hooks block) | add key + install guard; fix jsonc↔beads-config tenant drift |
| livespec-runtime | same | NO | add key + install guard |
| livespec-console-beads-fabro | same | NO (no hooks block) | add key + install guard |

Adopters (off-manifest; own wrappers): **openbrain** →
`["/usr/local/bin/with-openbrain-env.sh","--"]` (own 1Password env; NOT fleet);
**dolt-server** → its own wrapper. Also reconcile the manifest
`.livespec-fleet-manifest.jsonc` `adopters: []` drift (a separate conformance
finding) — decide whether openbrain/dolt-server should register.

## Co-edit disciplines

- Red-Green-Replay for any product `.py` (schema field, validator, doctor check,
  guard regex, self-heal helper): stage ONE failing test alone at Red, amend impl
  at Green, `feat:`/`fix:` subject, test bytes byte-identical.
- Schema JSON, `.jinja`, spec `.md`, `heading-coverage.json` are ritual-exempt
  (`chore`/`docs`) — but a changeset touching BOTH `.py` and those rides the
  ritual because of the `.py`.
- `just check` is the gate everywhere; never `--no-verify`.
- Every repo change: worktree → PR → merge → cleanup.
