# Design — wrapper-agnostic credential injection

The finalized architecture for making secret-backed skill/CLI access
**bulletproof and backend-agnostic** across the fleet. Self-sufficient; no chat
history required.

## Problem

A `/livespec-orchestrator-beads-fabro:next` invocation in the
`livespec-console-beads-fabro` session failed: the thin-transport SKILL.md
instructed a **bare** `python3 .../next.py`, whose internal `bd` subprocess
inherited an environment with no `BEADS_DOLT_PASSWORD` → Dolt "Access denied".
The agent then burned ~12 tool calls reverse-engineering the credential
mechanism. Three defects stacked:

1. Nothing (skill, CLI, or session) made the required secret present.
2. The one guard that knows about wrappers (`beads_access_guard`) keys on the
   literal Bash string, so it is blind to the Python-spawned `bd` — and it is
   only installed in 2 of 8 fleet repos.
3. The runtime failure is a raw `BeadsCommandError` traceback that names neither
   the missing variable nor the wrapper.

The intended model (per `SPECIFICATION` + the console's own `AGENTS.md`) is
**per-command wrapping, not session wrapping** — a human types `claude` bare and
each secret-touching command is prefixed with the credential wrapper. That is
correct by design (minimizes secret lifetime; the wrapper's `op run` burns
1Password quota per call with no caching). The bug is that the skill's command
was not wrapped and nothing enforced or self-healed it.

## Maintainer directive (locked)

- FULL cross-repo epic, incl. the PreToolUse guard rollout.
- Generalize beyond one skill to ANY skill/CLI needing an injected secret
  (beads password, GitHub token, Claude OAuth, future AWS), across ALL fleet
  AND adopter repos and all necessary commands/skills.
- Make the credential wrapper **backend-generic** — decouple from 1Password
  (planned AWS migration). `.livespec.jsonc` gets a `credential_wrapper` key
  naming a wrapper CLI conforming to a standardized contract.
- Proceed autonomously: plan → groom → implement.

## The three mechanisms

### 1. Self-heal at the CLI chokepoint (primary fix)

At process entry — orchestrator `bin/_bootstrap.py::bootstrap()`, the first
statement of every fabro CLI — before any secret is read, run
`ensure_credentials()`:

```python
import os, sys

SENTINEL = "LIVESPEC_CREDENTIAL_REEXEC"  # livespec-namespaced; wrapper preserves it

def ensure_credentials(required, credential_wrapper, environ):
    missing = [name for name in required if not environ.get(name)]
    if not missing:
        return                                    # secrets present -> proceed
    if environ.get(SENTINEL) == "1":              # already re-execed, still missing
        fail(f"required secret env var(s) {missing} absent even after re-exec "
             f"through credential_wrapper {credential_wrapper!r}; verify the "
             f"wrapper injects them (backend/profile/service correct?).")
    if not credential_wrapper:
        fail(f"required secret env var(s) {missing} absent and no "
             f"credential_wrapper configured in .livespec.jsonc.")
    os.environ[SENTINEL] = "1"
    argv = [*credential_wrapper, sys.executable, *sys.argv]
    os.execvp(argv[0], argv)                       # same PID, transparent stdio
```

Properties: **one** 1Password call whether invoked bare or pre-wrapped;
**no-op** when the secret is already present (Dispatcher/Fabro pay nothing);
checked-once sentinel → no infinite loop; `execvp` preserves stdio/exit-code;
LOUD (prints one stderr line when it re-execs). The reference wrapper strips
only `OP_SERVICE_ACCOUNT_TOKEN` + `WRAPPER_STAGE`, so the namespaced sentinel
survives the re-exec.

Secondary defense-in-depth for in-process library callers that bypass `bin/`
(regroom, store, intake_dor, reflector-oob → `make_beads_client` /
`ShellBeadsClient._invoke`): a **guard/raise** with the same actionable message
(re-exec is awkward mid-stack there), NOT a re-exec.

### 2. `credential_wrapper` — opaque literal argv-prefix array

`.livespec.jsonc` carries an optional array of literal argv tokens. livespec
runs `execvp([*credential_wrapper, *child_argv])` **directly — no shell, no
word-splitting, no `--` synthesis/stripping**. The operator bakes the correct
separator into the array. This sidesteps the one portability quirk (bare `env`
rejects a trailing `--` after `NAME=value` operands).

```jsonc
"credential_wrapper": ["/usr/local/bin/with-livespec-env.sh", "--"]
// AWS:     ["aws-vault", "exec", "livespec", "--"]
// chamber: ["chamber", "exec", "livespec", "--"]
// op:      ["op", "run", "--env-file=.env", "--"]
// dotenvx: ["dotenvx", "run", "--"]
// null:    ["env"]     // no trailing "--"
```

Conformance (all fit the prefix-array model; injects secrets, execs child,
passes exit code): `with-<id>-env.sh`, `aws-vault exec`, `chamber exec`,
`op run`, `dotenvx run`, custom `with-<project>-env.sh`. Do NOT fit (excluded by
contract): wrappers that must be **sourced** into the calling shell, or that
take the command only as a single **quoted string**.

Standardized contract text (drop-in for SPECIFICATION):

> **Credential wrapper.** A governed project MAY declare a `credential_wrapper`
> in `.livespec.jsonc`: a JSON array of literal argv tokens naming a conforming
> credential-injection CLI and its fixed arguments. A conforming credential
> wrapper is any command that, invoked as `[*credential_wrapper, *child_argv]`,
> (1) injects the project's secret environment variables into the child process
> environment, (2) execs (or runs and awaits) `child_argv` as its child, and
> (3) propagates the child's exit code. livespec treats the array as an opaque
> literal prefix: it prepends the tokens to the command it wants to run and
> invokes the result directly (no shell, no word-splitting, no quoting), and it
> neither synthesizes, repositions, nor strips any `--` separator — the operator
> includes exactly the separator token their chosen backend requires. livespec
> makes no assumption about the secret backend (1Password, AWS, Vault, an
> encrypted `.env`, or a bare `env`); swapping backends is a `credential_wrapper`
> edit, not a code change. A wrapper that must be sourced into the calling shell,
> or that accepts the command only as a single quoted string, does NOT conform.

### 3. Generalized PreToolUse guard (backstop for RAW hand-typed access)

Self-heal covers the plugin CLIs. Raw hand-typed `bd`/`dolt`/`mysql` still needs
the guard. Two generalizations of `beads_access_guard.py`:

- **Recognize the configured wrapper**, not just the `with-[a-z0-9-]+-env\.sh`
  regex (so `aws-vault`/`chamber` etc. are accepted as "under a wrapper"). Drive
  recognition from the resolved `credential_wrapper` first token.
- Keep the blocked set = **`bd`/`dolt`/`mysql`** (resources that genuinely fail
  without injection). Deliberately NOT broadening to `gh`/`git push`: interactive
  git/gh use ambient GitHub auth; the App-token path is CI/container-only and
  already self-injects (`dispatcher.py` preflight; `orchestrator-entrypoint.sh`).

Install across the 6 fleet repos + 2 adopters currently missing it.

## Self-resolved decisions

- Guard blocked set stays `bd`/`dolt`/`mysql`; no blanket `gh`/`git push` block.
- `credential_wrapper` is a CORE-owned schema key (so doctor validates it), not
  an orchestrator-tier `additionalProperties` key.
- LOUD self-heal (stderr line on re-exec), not silent.
- Contract name/wording is blessed at the `/livespec:revise` gate.

## Quota accounting (settled)

Self-inject invoked bare = ONE `op run` (the re-exec's wrapped invocation),
identical to a properly-wrapped call. When already wrapped/injected, self-heal
is a no-op → zero extra calls. There is NO extra quota cost; the earlier "silent
quota burn" objection was withdrawn.
