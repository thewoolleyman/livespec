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
    "CREDENTIAL_REEXEC_SENTINEL",
    "CredentialDecision",
    "Fail",
    "Proceed",
    "Reexec",
    "decide_credentials",
]

# The livespec-namespaced marker the caller sets on ``os.environ`` before
# it re-execs through the wrapper, so a second entry into this decision
# (now under the wrapper) recognizes that a re-exec already happened. A
# conforming credential wrapper preserves it across the re-exec (the
# reference wrapper strips only ``OP_SERVICE_ACCOUNT_TOKEN`` +
# ``WRAPPER_STAGE``), so its presence at value ``"1"`` means "already
# re-execed and the secrets are STILL missing" — an unrecoverable state.
CREDENTIAL_REEXEC_SENTINEL = "LIVESPEC_CREDENTIAL_REEXEC"


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
    2. Otherwise, if the re-exec sentinel is already set to ``"1"``, a
       re-exec has already happened and the wrapper did not inject the
       secrets -> ``Fail`` naming the still-missing vars and the wrapper.
    3. Otherwise, if no ``credential_wrapper`` is configured, there is
       nothing to re-exec through -> ``Fail`` naming the missing vars.
    4. Otherwise -> ``Reexec`` with the wrapper-prefixed argv.

    Total: every input path returns one of the three variants; the
    function never raises.
    """
    missing = [name for name in required if not environ.get(name)]
    if not missing:
        return Proceed()
    if environ.get(CREDENTIAL_REEXEC_SENTINEL) == "1":
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
