# Driver Hook Body Design

This note is the design-first pass for ledger epic `livespec-9z8h`
(`driver-hook-body`). It turns the epic's wall analysis into an execution shape
that can be groomed into ready, dependency-layered work-items. It is not an
implementation brief; the implementation slices still need `groom` and, for
workflow edits, maintainer-side branches.

## Current Shape

`livespec-driver-claude` carries three plugin-shipped hooks under
`.claude-plugin/hooks/`:

- `block-auto-memory.sh`, a shell wrapper with embedded Python loaded through
  `python3 -c`.
- `warn-plan-persistence.sh`, also a shell wrapper with embedded Python.
- `no_shadow_ledger.py`, a Python Stop hook body that must ship
  byte-identically in both Driver bundles.

`livespec-driver-codex` carries Python hook modules under `livespec/hooks/`:

- `livespec_footgun_guard.py`, plus `_footgun_shell.py` and
  `_footgun_primary_checkout.py`.
- `block_auto_memory.py`.
- `no_shadow_ledger.py`, intended to be byte-identical with the Claude Driver
  copy.

The Codex Driver already has `main()` entry points in `block_auto_memory.py` and
`livespec_footgun_guard.py`, but those entry points call `sys.exit()` internally
and the tests mostly exercise the scripts through subprocesses. The Claude
Driver's two shell hooks cannot be imported for in-process Python coverage at
all, because their Python bodies are strings passed to `python3 -c`.

`main_guard` is not a blocker for hook modules. The shared check is scoped to
`.claude-plugin/scripts/`, not hook directories. Hook files may use a standard
entry tail such as `if __name__ == "__main__": raise SystemExit(main())`
without violating that check. The design should still avoid top-level work so
imports are cheap and side-effect free.

## Entry-Point Rule

Each Python hook body should expose a `main() -> int` function plus a standard
script entry tail that raises `SystemExit(main())` when the file is invoked as a
script. `main()` owns stdin/stdout at the hook boundary, catches every expected and
unexpected failure, and returns `0` in all paths. It should not call
`sys.exit()` internally. Helper functions should be pure or locally I/O-bound
enough that tests can call them directly. This gives three useful test seams:

- In-process tests call helpers for branch-heavy pure logic.
- In-process tests call `main()` with monkeypatched stdin, stdout, cwd, and env
  to record real coverage on the hook module.
- One subprocess test per hook remains to prove the actual hook registration
  shape and stdin/stdout protocol.

For Claude's two shell hooks, the implementation slice should convert them to
Python hook files instead of preserving embedded Python in shell. `hooks.json`
then invokes `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/block_auto_memory.py"` and
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/warn_plan_persistence.py"`. This is the
smallest change that makes those hook bodies importable and measured by Python
coverage. The old shell filenames should be removed only in the same slice that
updates `hooks.json`, tests, ruff exclusions, and Driver spec text.

## Byte-Identity Rule

Do not force every hook to be byte-identical across runtimes. That would encode
false sameness:

- `no_shadow_ledger.py` is the declared cross-Driver neutral body and must stay
  byte-identical.
- The auto-memory guards share an intent-routing contract, but the runtime
  stores and tool surfaces differ: Claude targets
  `~/.claude/projects/<slug>/memory/*.md` on `Write`; Codex targets
  `~/.codex/memories/` across `Write`, `Edit`, and `apply_patch`.
- The Codex footgun guard is required for mutating Codex automation and has no
  plugin-bundle counterpart in the Claude Driver.
- The Claude plan-persistence hook is Claude-only.

The conformance rule should therefore be: byte-identity is mandatory for hook
bodies whose core contract declares them neutral shared bodies, currently
`no_shadow_ledger.py`. Runtime-specific hooks should instead share behavioral
fixtures or helper wording where that removes real duplication, but not through
a cross-runtime byte-equality claim.

For `no_shadow_ledger.py`, the canonical body can be stored in `livespec` core
only if consumers read upstream, never the reverse. The allowed direction is:

- `livespec` core may declare the contract and, if useful, carry a canonical
  reference body.
- `livespec-driver-claude` and `livespec-driver-codex` each verify their local
  copy against the core reference or against a vendored shared source package.
- `livespec-dev-tooling` must not read downstream Driver repos in its own CI.
  A shared verifier may live in `livespec-dev-tooling`, but it must run inside
  each Driver checkout and read only configured upstream/reference paths.

This follows the no-circular-dependency directive: checks live on the consumer
side reading up, or the duplication is designed away.

## Coverage And Subprocess Boundary

The per-file coverage target should measure hook modules in-process. Tests that
spawn `python3 hook.py` must be retained only for the real hook I/O contract and
declared in `subprocess_spawn_allowlist`, because those children deliberately do
not contribute coverage to the parent process.

Recommended test split per hook:

- `test_<hook>_main.py` or existing `tests/hooks/test_<hook>.py` imports the
  hook module and calls `main()` under monkeypatched `sys.stdin`,
  `sys.stdout`, env, and cwd.
- Pure helpers keep the current fine-grained tests where they already exist,
  especially Codex's `_footgun_shell.py` and `_footgun_primary_checkout.py`.
- One subprocess smoke asserts the script file still exits `0` and emits the
  expected JSON shape for one positive case and one fail-open case.

This keeps real coverage honest while preserving the runtime protocol check.

## Driver Infra Slices

The groomed work should land in dependency order:

1. Dev-tooling verifier support, if needed. Add or generalize a reusable
   consumer-side byte-identity verifier that reads an upstream/reference path
   declared by the consumer. Do not make `livespec-dev-tooling` CI read a Driver
   checkout. If the existing Conformance Pattern machinery already has the
   necessary configurable verifier, use it rather than adding a new one.
2. Core contract and reference disposition. Clarify that byte-identity applies
   to declared neutral shared bodies, currently `no_shadow_ledger.py`, and that
   runtime-specific hooks share behavior rather than bytes. If core will carry a
   canonical reference body, add it in the same contract slice or a following
   core implementation slice.
3. Claude Driver hook refactor. Convert shell hooks to Python modules, refactor
   `no_shadow_ledger.py` to `main() -> int`, update `hooks.json`, update tests to
   in-process-plus-subprocess, add coverage config, update ruff exclusions and
   supervisor-entry config, and keep the required fail-open posture.
4. Codex Driver hook refactor. Normalize `main() -> int` for Codex hooks, remove
   internal `sys.exit()` helper exits, align `no_shadow_ledger.py` with the
   neutral body, update tests to in-process-plus-subprocess, add coverage config,
   and keep Codex-specific apply_patch and footgun coverage.
5. Driver CI parity. Reorder each `check:` aggregate into the canonical
   contiguous alphabetical block, wire every aggregate target into CI and
   `ci-green.needs`, add `check-aggregate-completeness`,
   `check-tool-backed-check-completeness`, `check-per-file-coverage`,
   `check-coverage`, `check-types`, and `check-ci-matrix-completeness`, then set
   `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST=1` only after the matrix is complete.

Workflow edits in slice 5 are maintainer-side because the fleet App does not
have `workflows` permission. Do not factory-dispatch a slice that includes
`.github/workflows/` edits.

## Open Design Checks Before Grooming

The `groom` pass should verify these before filing ready children:

- Whether `livespec` core should carry an actual canonical
  `no_shadow_ledger.py` reference file, or whether the canonical source should
  be a small shared runtime package. Core-as-reference is simpler for this
  one-body concern; a runtime package only pays off if more neutral hook bodies
  appear.
- Whether the Claude Driver specs need a propose-change before replacing
  `.sh` hook scripts with `.py` scripts. The current Claude Driver contract says
  most hooks are shell scripts, so that repo likely needs a spec update.
- Whether Driver specs need heading-coverage updates when hook bundle headings
  change. Any H2 change in those spec trees must co-edit their
  `tests/heading-coverage.json` files.
- Whether `livespec-driver-claude` should upgrade its
  `livespec-dev-tooling` pin from `v0.40.0`; the handoff said all four repos
  were already on `v0.43.2`, but the primary checkout currently shows
  `v0.40.0`.
- Whether `livespec-driver-codex` should upgrade from `v0.43.0` before adding
  the full CI parity gates.
- Whether the stale `livespec-driver-codex` `justfile` comment around
  `file_lloc_hard_gate` is still present on the branch used for implementation.
  The primary checkout already has `file_lloc_hard_gate = true`, so any comment
  saying it is deliberately unset must be removed in the Driver justfile slice.

## Recommended Next Action

Resume the thread and invoke the `groom` operation on `livespec-9z8h`, using this
note as the design input. The first groomed child should be the byte-identity
Verifier/reference decision, because the Driver refactors should not proceed
until the neutral-body source and consumer-side verifier shape are fixed.
