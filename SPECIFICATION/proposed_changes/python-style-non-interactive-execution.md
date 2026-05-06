---
topic: python-style-non-interactive-execution
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-06T04:43:00Z
---

## Proposal: Migrate style-doc §"Non-interactive execution" into `SPECIFICATION/constraints.md`

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Cycle 2 of Plan Phase 8 item 2 per-section migration. Lands the source doc's §"Non-interactive execution" content (lines 73-87 of `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`) as a new `## Non-interactive execution` section in `SPECIFICATION/constraints.md`, inserted after `## Constraint scope` and before `## Python runtime constraint`. Restructured for BCP 14 normative language (already largely BCP 14 in the source).

### Motivation

Per Plan Phase 8 item 2 (`python-style-doc-into-constraints`), the source-doc §"Non-interactive execution" content forbids interactive prompts in scripts, gates terminal manipulation and `isatty()` use, and pins the precondition-failed contract for human-confirmation requirements. Codifying these rules in `SPECIFICATION/constraints.md` makes them governance-bearing alongside the existing pure/IO and supervisor-discipline rules. The deviation rationale from `deferred-items.md` §`python-style-doc-into-constraints`'s "at seed time" guidance is recorded in the cycle 1 (`python-style-scope`) revise body; this cycle cross-references it.

The destination is `SPECIFICATION/constraints.md` (not `spec.md`) per Plan Phase 8 item 2's "destination heading taxonomy fits better" heuristic: non-interactive execution is a script-behavior constraint, parallel to §"Pure / IO boundary" and §"Supervisor discipline", and belongs alongside them.

### Proposed Changes

One atomic edit to **SPECIFICATION/constraints.md**: insert a new `## Non-interactive execution` section after the closing line of `## Constraint scope` and before `## Python runtime constraint`:

> ## Non-interactive execution
>
> Scripts MUST NOT prompt the user via the terminal: `input()`, `getpass.getpass()`, and any other prompt-and-wait construct are forbidden. Scripts MUST NOT manipulate terminal modes or open `/dev/tty`. Scripts MUST NOT rely on `sys.stdout.isatty()` or `os.isatty(...)` to gate interactive behavior; they MAY use these checks to select between stdin-piped and stdin-file-redirect handling, provided neither branch prompts the user.
>
> A script that requires a human-confirmation step MUST fail with an actionable message and exit code `3` (precondition failed), leaving the decision to the caller.
>
> All configuration and input MUST arrive through one of: positional arguments, flags via `argparse`, environment variables, files named by the above, or stdin pipe when documented.
