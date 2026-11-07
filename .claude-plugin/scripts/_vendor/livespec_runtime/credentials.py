"""Pure credential-decision brain for the self-heal chokepoint.

Per livespec/plan/credential-wrapper/research/01-design.md §1 (the
self-heal algorithm). At process entry — the first statement of every
orchestrator CLI's ``bin/_bootstrap.py::bootstrap()`` — the caller must
decide, before any secret is read, whether to run normally, re-exec
itself through the configured credential wrapper so the wrapper injects
the missing secrets, or fail with an actionable message.

This module is the PURE brain of that decision. It reads no environment,
touches no filesystem, spawns no process, and NEVER raises: the caller
passes a snapshot of the process environment plus the interpreter path
and argv, and this module returns a ``CredentialDecision`` describing
what the caller should do. The impure act (``os.execvp`` /
``sys.exit`` / actually reading ``os.environ``) stays entirely in the
caller's ``bin/`` boundary; the decision itself is a total function of
its inputs, so it is exhaustively testable without a process. (This
library ships no ``io/`` tree, so a pure module MUST NOT ``import os`` /
``import sys`` and MUST NOT raise domain errors.)

Loop guard — why the marker rides in ``argv``, not the environment
------------------------------------------------------------------

The re-exec must be bounded to ONE hop: if the wrapper runs but still
does not inject the secrets, the second entry into this decision must
``Fail`` rather than re-exec again. The original guard was the env
sentinel ``CREDENTIAL_REEXEC_SENTINEL``, on the assumption that a
conforming wrapper preserves it. Measured 2026-08-10, that assumption is
false for EVERY wrapper tested, including the reference fleet wrapper:
rebuilding the ambient environment is precisely what a credential
wrapper is for, and an arbitrary canary variable is dropped alongside
the sentinel. The guard could therefore never fire, and a repo whose
wrapper cannot supply a required secret re-execed unboundedly and
silently. (Evidence with controls:
``plan/archive/credential-reexec-loop-guard/research/findings.md``.)

``CREDENTIAL_REEXEC_ARGV_MARKER`` fixes that by carrying the marker
where a wrapper cannot scrub it. A wrapper's contract is to exec the
argv it was handed, so an argv token survives by construction. The env
sentinel is still honored, so the guard is the OR of the two: whichever
survives terminates the recursion.

Contract for performers (the callers' ``_bootstrap.py``, which build and
run the ``Reexec`` argv):

1. APPEND ``CREDENTIAL_REEXEC_ARGV_MARKER`` to the ``Reexec.argv`` vector
   before handing it to ``os.execvp``, so the re-execed child sees it in
   its own ``sys.argv``. This module deliberately does NOT append it: the
   marker's placement is the performer's concern (it must land after the
   wrapper's own argv-prefix and after the program's arguments), and
   ``Reexec.argv`` stays the exact wrapper-prefixed vector its callers
   already assert on.
2. STRIP every occurrence of the marker from ``sys.argv`` before handing
   argv to the real argument parser, so the token never reaches the CLI's
   own option handling. Pass the UNSTRIPPED argv to
   ``decide_credentials`` — the detection happens first, at process
   entry, before any parsing.
3. Setting ``CREDENTIAL_REEXEC_SENTINEL`` remains correct and is still
   honored, but a performer MUST NOT rely on it alone; it is best-effort
   belt-and-braces, and the argv marker is the load-bearing guard.

The three-variant ``CredentialDecision`` union is discriminated on a
``Literal[...]``-typed ``kind`` field — mirroring the
``livespec_runtime.cross_repo.types.DependsOnEntry`` union — so pyright
narrows the variant in the caller's ``match`` dispatch. Each literal
value equals the snake_case variant name (``"proceed"``, ``"reexec"``,
``"fail"``), the load-bearing narrowing contract this library's
``SPECIFICATION/constraints.md`` places on every public union.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

__all__: list[str] = [
    "CREDENTIAL_REEXEC_ARGV_MARKER",
    "CREDENTIAL_REEXEC_SENTINEL",
    "CredentialDecision",
    "Fail",
    "Proceed",
    "Reexec",
    "decide_credentials",
    "wrapper_launch_failure",
]

# The livespec-namespaced marker the caller sets on ``os.environ`` before
# it re-execs through the wrapper, so a second entry into this decision
# (now under the wrapper) recognizes that a re-exec already happened. Its
# presence at value ``"1"`` means "already re-execed and the secrets are
# STILL missing" — an unrecoverable state. BEST-EFFORT ONLY: a credential
# wrapper rebuilds the ambient environment, and no measured wrapper
# preserves this variable, so it can be absent in a genuine second entry.
# ``CREDENTIAL_REEXEC_ARGV_MARKER`` is the load-bearing guard; this one is
# retained because it costs nothing and is correct when it does survive.
CREDENTIAL_REEXEC_SENTINEL = "LIVESPEC_CREDENTIAL_REEXEC"

# The argv token a performer appends to the re-exec command line, and the
# guard this module actually relies on. A wrapper execs the argv vector it
# was handed, so the token survives a hop that scrubs the environment. Its
# presence anywhere in ``argv`` means "already re-execed", bounding the
# recursion at one hop regardless of wrapper cooperation. Dash-prefixed and
# livespec-namespaced so it cannot collide with a positional argument;
# performers strip it before the real parser sees argv.
CREDENTIAL_REEXEC_ARGV_MARKER = "--livespec-credential-reexec"


@dataclass(frozen=True, slots=True, kw_only=True)
class Proceed:
    """The required secrets are all present; run the CLI normally.

    The no-op decision. When invoked already-wrapped (Dispatcher/Fabro
    inject the secrets ahead of time) or when the secrets are otherwise
    present, self-heal costs nothing.
    """

    kind: Literal["proceed"] = "proceed"


@dataclass(frozen=True, slots=True, kw_only=True)
class Reexec:
    """Re-exec the process through the credential wrapper.

    ``argv`` is the literal argv vector the caller hands to
    ``os.execvp(argv[0], argv)``: ``[*credential_wrapper, executable,
    *argv]``. livespec treats ``credential_wrapper`` as an opaque literal
    prefix (no shell, no word-splitting, no ``--`` synthesis), so the
    tokens are prepended verbatim.
    """

    argv: tuple[str, ...]
    kind: Literal["reexec"] = "reexec"


@dataclass(frozen=True, slots=True, kw_only=True)
class Fail:
    """Cannot self-heal; ``message`` is an actionable diagnostic.

    Reached either when the secrets are still absent AFTER a re-exec
    (the wrapper did not inject them) or when secrets are absent and no
    ``credential_wrapper`` is configured. The message names the still-
    missing variables and the cause so the caller can print it and exit
    non-zero rather than emit a raw backend traceback that names neither.
    """

    message: str
    kind: Literal["fail"] = "fail"


CredentialDecision = Proceed | Reexec | Fail


def wrapper_launch_failure(
    *,
    required: Sequence[str],
    credential_wrapper: Sequence[str],
) -> Fail:
    """Build the fail-soft diagnostic for a failed wrapper handoff."""
    return Fail(
        message=(
            f"credential_wrapper could not run in this environment "
            f"(wrapper {list(credential_wrapper)!r}; required secret env "
            f"var(s) {list(required)!r}). This can happen in a sandbox "
            f"that blocks sudo or sets no_new_privs, preventing the wrapper "
            f"from reaching the root-only systemd-creds credstore. Re-run "
            f"under the credential wrapper with the required secret(s) already "
            f"present, or, when running Codex, with "
            f"--dangerously-bypass-approvals-and-sandbox."
        ),
    )


def decide_credentials(
    *,
    required: Sequence[str],
    credential_wrapper: Sequence[str],
    environ: Mapping[str, str],
    executable: str,
    argv: Sequence[str],
) -> CredentialDecision:
    """Decide whether to proceed, re-exec through the wrapper, or fail.

    ``required`` names the secret environment variables the CLI needs;
    ``credential_wrapper`` is the ``.livespec.jsonc`` argv-prefix
    (possibly empty); ``environ`` is a snapshot of the process
    environment; ``executable`` is the interpreter path (the caller's
    ``sys.executable``) and ``argv`` the caller's ``sys.argv``.

    The algorithm (design §1), in order:

    1. A ``required`` name is "missing" when it is absent from
       ``environ`` OR maps to an empty string. With none missing, the
       secrets are present -> ``Proceed``.
    2. Otherwise, if a re-exec has ALREADY happened — the argv marker is
       present in ``argv``, or the env sentinel is set to ``"1"`` — the
       wrapper ran and did not inject the secrets -> ``Fail`` naming the
       still-missing vars and the wrapper. Either marker alone suffices,
       which is what bounds the recursion at one hop when the wrapper
       scrubs the environment.
    3. Otherwise, if no ``credential_wrapper`` is configured, there is
       nothing to re-exec through -> ``Fail`` naming the missing vars.
    4. Otherwise -> ``Reexec`` with the wrapper-prefixed argv.

    Total: every input path returns one of the three variants; the
    function never raises.
    """
    missing = [name for name in required if not environ.get(name)]
    if not missing:
        return Proceed()
    already_reexeced = (
        CREDENTIAL_REEXEC_ARGV_MARKER in argv or environ.get(CREDENTIAL_REEXEC_SENTINEL) == "1"
    )
    if already_reexeced:
        return Fail(
            message=(
                f"required secret env var(s) {missing} absent even after re-exec "
                f"through credential_wrapper {list(credential_wrapper)!r}; verify the "
                f"wrapper injects them (backend/profile/service correct?)."
            ),
        )
    if not credential_wrapper:
        return Fail(
            message=(
                f"required secret env var(s) {missing} absent and no "
                f"credential_wrapper configured in .livespec.jsonc."
            ),
        )
    return Reexec(argv=(*credential_wrapper, executable, *argv))
