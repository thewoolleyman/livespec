# prune-history

Harness-neutral driving prose for the `prune-history` operation, per
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture": this artifact is the core-owned LLM-facing half of the
operation; the prune-history CLI named in `.livespec.jsonc` (core
reference implementation: `bin/prune_history.py`) is the contract
half. Drivers bind this prose to their runtime; nothing in this file
names any specific agent runtime's tools or command namespace.

Destructively reduce `<spec-root>/history/` size by replacing
older `vNNN/` snapshots with a single `PRUNED_HISTORY.json`
marker at `v(N-1)/`, leaving `vN/` (the current head) intact.
Pre-step doctor static runs before the pruning operation;
post-step doctor static runs after it; there is no LLM-driven
post-step phase. Version numbers are never re-used and numeric
contiguity is preserved by the doctor `version-contiguity`
check, which treats the marker's `pruned_range` as intentional
missing history.

## When to run

- The user explicitly invokes the prune-history operation, says
  "prune the livespec history", "trim the history snapshots", or
  otherwise explicitly asks to reduce the size of
  `<spec-root>/history/`.
- This operation is destructive. Per `SPECIFICATION/contracts.md`
  §"`prune-history` skill-prose responsibilities", the LLM MUST
  NOT invoke `prune-history` on its own initiative, and every
  Driver MUST configure its runtime so model-driven
  self-invocation is disabled. Only an explicit user request
  (a Driver command or natural-language directive that
  unambiguously names the prune-history operation) triggers
  this prose.
- If the user mentions "history" generally (e.g., "look at the
  history", "show me the history") without explicitly asking to
  remove it, do NOT run this operation.

## Inputs

The prune-history CLI accepts only the following flags in v1:

- `--project-root <path>` (optional; defaults to `Path.cwd()`).
  Anchors `<spec-root>/` resolution and the upward walk to find
  `.livespec.jsonc`. Uniform across every spec-side CLI.
- `--skip-pre-check` (optional). Skips the pre-step doctor
  static phase before pruning. Mutually exclusive with
  `--run-pre-check`.
- `--run-pre-check` (optional). Forces the pre-step doctor
  static phase to run even if `pre_step_skip_static_checks`
  is `true` in `.livespec.jsonc`. Mutually exclusive with
  `--skip-pre-check`.

`prune-history` does NOT accept `--spec-target`. The v1 scope
prunes only the main spec tree; sub-spec tree pruning is
deferred (tracked under `sub-spec-structural-formalization`).
The CLI takes no JSON-payload flag; there is no
LLM-provided JSON input for this operation.

Effective skip resolution for the pre-step (per
SPECIFICATION/spec.md §"Sub-command lifecycle"):

1. `--skip-pre-check` on the CLI → skip = true.
2. `--run-pre-check` on the CLI → skip = false (overrides
   config).
3. Neither flag → use config key
   `pre_step_skip_static_checks` (default `false`).
4. Both flags set → argparse usage error (exit 2).

## Steps

1. **Confirm with the user.** Because `prune-history` is
   destructive, restate what is about to happen ("This will
   delete every `<spec-root>/history/vK/` directory where
   `K < N-1` and replace `v(N-1)/`'s contents with a single
   `PRUNED_HISTORY.json` marker. `vN/` remains intact.") and
   ask the user to confirm before invoking the CLI. Skip
   the confirmation only when the user has already explicitly
   authorized the operation in the same turn (e.g., the
   operation was invoked with an unambiguous phrase like
   "prune the livespec history now, no further questions").

2. **Resolve effective flags.** Determine whether the user
   passed `--skip-pre-check` or `--run-pre-check` in their
   request. Compose the CLI argv accordingly. If the user
   passed neither flag and `.livespec.jsonc`'s
   `pre_step_skip_static_checks` is `true`, the pre-step will
   be silently skipped — record this for the narration step
   below.

3. **Invoke the prune-history CLI.** Run the prune-history CLI
   named in config with `[flags]` and explicit argv. Capture
   the exit code. The CLI writes structured findings
   (including any pruning summary) to stderr via structlog.

4. **Narrate skipped pre-step (when silent).** If the
   effective resolution was `skip = true` AND the user did NOT
   explicitly pass `--skip-pre-check` (i.e., the skip came
   from `pre_step_skip_static_checks: true` in config),
   surface a warning to the user: "Pre-step doctor static was
   skipped because `pre_step_skip_static_checks` is set to
   `true` in `.livespec.jsonc`. Run with `--run-pre-check` to
   force the pre-step." When the user passed
   `--skip-pre-check` explicitly, no narration is required
   (the skip is intentional and acknowledged). When the user
   passed `--run-pre-check`, the pre-step ran; no narration
   needed.

5. **Surface the pruning result.** On exit 0, parse the
   CLI's stderr structlog output and report the deletion
   summary to the user (e.g., "Pruned versions v001..v014;
   PRUNED_HISTORY.json marker now at v014/; v015 retained.").
   If the CLI short-circuited as a no-op (only `v001`
   exists, or the oldest surviving entry is already a
   `PRUNED_HISTORY.json` marker), report the no-op explicitly:
   "Nothing to prune; oldest surviving history is already
   `PRUNED_HISTORY.json`."

This operation does NOT dispatch an LLM template prompt. The
pruning operation is purely mechanical; no semantic phase runs
under prompt control. Likewise, retry-on-exit-4 does NOT apply
here: there is no LLM-provided JSON payload for the CLI to
schema-validate, so exit 4 cannot be raised by this CLI in
v1.

## Post-CLI

No post-step LLM-driven phase. After exit 0, the CLI has:

- Deleted every `<spec-root>/history/vK/` directory where
  `K < N-1`.
- Replaced the contents of `<spec-root>/history/v(N-1)/` with
  a single file `PRUNED_HISTORY.json` containing
  `{"pruned_range": [first, N-1]}` (where `first` carries
  forward from any prior marker, or is the earliest
  v-directory version number that was present before this
  run).
- Left `<spec-root>/history/vN/` fully intact.

Post-step doctor static then runs over every spec tree per
the standard CLI-side lifecycle (see the doctor prose,
`prose/doctor.md`). The `version-contiguity` check reads the
new `PRUNED_HISTORY.json` and applies contiguity only to
surviving versions ≥ `N-1`.

`prune-history` is a per-tree operation; in v1 it acts only on
the main spec tree. Sub-spec trees under
`<main-spec-root>/templates/<name>/history/` are not affected.

## Failure handling

CLI exit-code-to-narration mapping:

- Exit `0` → success. Surface the deletion summary (or no-op
  message) to the user per Step 5 above. Proceed to post-step
  doctor narration (handled by the doctor prose,
  `prose/doctor.md`).
- Exit `1` → internal bug; surface the structlog stderr lines
  (including any traceback) and abort. Do NOT retry.
- Exit `2` → usage error (e.g., both `--skip-pre-check` and
  `--run-pre-check` supplied; unknown flag). Restate the
  expected invocation shape per `## Inputs` above and abort.
- Exit `3` → precondition / pre-step doctor-static failure.
  Surface the findings from the CLI's stderr structlog
  line(s) and direct the user to the corrective action each
  finding describes (e.g., "Fix the version-contiguity gap in
  `<spec-root>/history/` before re-running prune-history."). NOT
  retryable via prompt re-run.
- Exit `127` → too-old Python or missing tool; surface the
  install instruction from stderr and abort.

Exit `4` is N/A for this operation (no LLM-provided JSON
payload to schema-validate).
