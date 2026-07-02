"""GitHub App JWT assembly + RS256 signing (the mint substrate).

The unsigned JWT (`header.payload`) is assembled purely — the caller
injects the issuance time — and signed RS256 by the production
openssl-subprocess signer. openssl is a SYSTEM dependency of this
module (like `gh` for `livespec_runtime.cross_repo`): universally
present on factory hosts, and shelling out keeps the library free of a
Python crypto dependency per this repo's SPECIFICATION/constraints.md
dependency constraints.

`iat` is backdated 60s for clock skew; `exp` is +540s from issuance,
well under GitHub's 10-minute App-JWT cap. Prior art: the orchestrator
plugin's `_app_token.py` mint (livespec-orchestrator-beads-fabro),
promoted into the shared runtime per the github-app-auth design record
(Pillar 1 — one primitive for factory AND standalone).
"""

import base64
import json
import re
import subprocess
import tempfile
from pathlib import Path

from livespec_runtime.github_auth.errors import GithubAppAuthError

__all__: list[str] = [
    "b64url",
    "jwt_signing_input",
    "normalize_pem",
    "sign_rs256_with_openssl",
]

# iat is backdated for clock skew; the JWT lives well under GitHub's 10-min cap.
_JWT_SKEW_SECONDS = 60
_JWT_TTL_SECONDS = 540


def b64url(*, raw: bytes) -> str:
    """URL-safe base64 without padding (the JWS/JWT encoding)."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def jwt_signing_input(*, app_id: str, issued_at: int) -> str:
    """The unsigned `header.payload` of the App JWT (pure; caller injects time)."""
    header = b64url(raw=json.dumps({"alg": "RS256", "typ": "JWT"}).encode("utf-8"))
    payload = b64url(
        raw=json.dumps(
            {
                "iat": issued_at - _JWT_SKEW_SECONDS,
                "exp": issued_at + _JWT_TTL_SECONDS,
                "iss": app_id,
            }
        ).encode("utf-8")
    )
    return f"{header}.{payload}"


def normalize_pem(*, raw: str) -> str:
    """Return a valid PEM with real line structure.

    A secrets manager may deliver the key flattened to one line
    (newlines stripped or turned into spaces / literal backslash-n);
    openssl needs real PEM line structure, so de-whitespace the base64
    body and re-wrap at 64 columns. A key that already carries real
    newlines passes through unchanged.
    """
    text = raw.replace("\\n", "\n").strip()
    if "\n" in text:
        return text + "\n"
    match = re.match(r"(-----BEGIN [A-Z0-9 ]+-----)(.*)(-----END [A-Z0-9 ]+-----)", text)
    if match is None:
        return text
    begin, body, end = match.group(1), match.group(2), match.group(3)
    compact = "".join(body.split())
    wrapped = "\n".join(compact[i : i + 64] for i in range(0, len(compact), 64))
    return f"{begin}\n{wrapped}\n{end}\n"


def sign_rs256_with_openssl(*, signing_input: str, pem: str) -> bytes:
    """Production signer: RS256 over `signing_input` with the App private key.

    openssl reads the key from a file, so the PEM is written to a
    mode-600 temp file and removed immediately after the sign — the
    durable secret never persists beyond this scoped temp file. A key
    openssl cannot load is an EXPECTED misconfiguration →
    `GithubAppAuthError` with an actionable diagnostic.
    """
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)  # noqa: SIM115 — must outlive the with-scope so openssl can read it; removed in the finally.
    key_path = Path(handle.name)
    try:
        key_path.chmod(0o600)
        _ = handle.write(pem)
        handle.close()
        completed = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(key_path)],
            input=signing_input.encode("utf-8"),
            capture_output=True,
            check=False,
        )
    finally:
        key_path.unlink()
    if completed.returncode != 0:
        raise GithubAppAuthError(
            detail=(
                f"openssl could not sign with the App private key (exit "
                f"{completed.returncode}); verify GITHUB_PRIVATE_KEY holds the App's "
                "PEM private key as injected by the tenant's credential_wrapper"
            ),
        )
    return completed.stdout
