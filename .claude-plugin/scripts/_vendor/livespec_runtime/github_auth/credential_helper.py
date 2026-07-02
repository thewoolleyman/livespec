"""`git credential` helper over the App-token mint (get/store/erase protocol).

git invokes `<helper> <operation>` with attributes as `key=value`
lines on stdin (terminated by a blank line or EOF). This helper
answers `get` for https contexts with `username=x-access-token` and a
freshly minted installation token as the password, so plain
`git clone/push` of any duration works transparently — each `get`
mints fresh, and the transparent-remint guarantee for long-lived
processes lives in `InstallationTokenProvider`. `store` and `erase`
are deliberate no-ops: the token is ephemeral (never persisted at
rest), so there is nothing to store and nothing to erase.

Inputs come ONLY from the wrapper-injected environment
(`livespec_runtime.github_auth.config`); a missing env fails closed
with the actionable diagnostic on stderr and a non-zero exit — never a
fleet fallback. Scoping the helper to particular remotes is the
consumer's git-config concern; wire it as, e.g.:

    git config credential.helper '!livespec-github-credential-helper'

The console script is declared in pyproject `[project.scripts]`;
`python -m livespec_runtime.github_auth.credential_helper` works too.
"""

import os
import sys
from collections.abc import Mapping
from typing import TextIO

from livespec_runtime.github_auth.config import load_github_app_config
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.mint import DEFAULT_MINT_SEAMS, MintSeams
from livespec_runtime.github_auth.provider import InstallationTokenProvider

__all__: list[str] = ["main", "run"]


def _read_attributes(*, stdin: TextIO) -> dict[str, str]:
    """Parse the `key=value` attribute lines git writes (blank line/EOF ends)."""
    attributes: dict[str, str] = {}
    for line in stdin:
        stripped = line.rstrip("\n")
        if stripped == "":
            break
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            attributes[key] = value
    return attributes


def main(
    *,
    argv: list[str],
    environ: Mapping[str, str],
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
    seams: MintSeams = DEFAULT_MINT_SEAMS,
) -> int:
    """The helper body over injected streams (the tested core).

    Exit codes: 0 on success (including the deliberate no-ops and the
    emit-nothing non-https path — git treats missing output as "no
    credential from this helper"), 1 on a fail-closed credential
    error, 2 on a usage error.
    """
    if len(argv) != 1:
        _ = stderr.write("usage: livespec-github-credential-helper get|store|erase\n")
        return 2
    operation = argv[0]
    attributes = _read_attributes(stdin=stdin)
    if operation != "get":
        return 0
    if attributes.get("protocol") != "https":
        return 0
    try:
        config = load_github_app_config(environ=environ)
        token = InstallationTokenProvider(config=config, seams=seams).token()
    except GithubAppAuthError as error:
        _ = stderr.write(f"livespec github_auth credential helper: {error.detail}\n")
        return 1
    _ = stdout.write(f"username=x-access-token\npassword={token}\n")
    return 0


def run() -> int:
    """Process entry: wire the real streams and environment."""
    return main(
        argv=sys.argv[1:],
        environ=os.environ,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(run())
