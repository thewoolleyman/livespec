"""GitHub App installation-token mint railway (over injectable seams).

Mint = normalize the PEM → sign an RS256 App JWT → resolve the
installation (pinned id, else sole-installation discovery) →
`POST /app/installations/{id}/access_tokens`. The signer and the two
HTTP calls are bundled in an injectable `MintSeams` so the
orchestration is unit-tested with fakes; the production seams default
to openssl (`livespec_runtime.github_auth.signing`) and urllib against
the https GitHub REST API.

WHY urllib rather than this library's usual `gh` subprocess surface
(SPECIFICATION/constraints.md keeps external-state queries behind
`gh auth`): the mint IS the credential bootstrap — it runs exactly
when no `gh`-visible credential exists yet, so it cannot ride that
surface. The minted token is ephemeral (never persisted at rest); the
JWT lives under GitHub's 10-minute cap; the PEM never leaves the
process except through the scoped openssl temp file.

Every EXPECTED failure (bad credentials, ambiguous installations,
transport errors, malformed responses) raises `GithubAppAuthError`
with an actionable diagnostic; caller bugs propagate as built-ins.
Prior art: the orchestrator plugin's `_app_token.py`
(livespec-orchestrator-beads-fabro), promoted into the shared runtime
per the github-app-auth design record (Pillar 1).
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol, cast

from livespec_runtime.github_auth.config import GithubAppConfig
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.signing import (
    b64url,
    jwt_signing_input,
    normalize_pem,
    sign_rs256_with_openssl,
)

__all__: list[str] = [
    "DEFAULT_MINT_SEAMS",
    "HttpJson",
    "MintSeams",
    "SignRs256",
    "http_get_json",
    "http_post_json",
    "mint_installation_token",
    "resolve_installation_id",
]

_API_VERSION = "2022-11-28"
_HTTP_TIMEOUT_SECONDS = 30.0
_USER_AGENT = "livespec-runtime-github-auth"


class SignRs256(Protocol):
    """RS256 signer seam (production: `signing.sign_rs256_with_openssl`)."""

    def __call__(self, *, signing_input: str, pem: str) -> bytes: ...


class HttpJson(Protocol):
    """JWT-authenticated GitHub REST call seam returning parsed JSON."""

    def __call__(self, *, url: str, jwt: str) -> Any: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class MintSeams:
    """The injectable side-effecting seams of the mint (defaulted to production)."""

    sign: SignRs256
    http_get: HttpJson
    http_post: HttpJson


def _request_json(*, url: str, jwt: str, method: str) -> Any:
    """JWT-authenticated GitHub REST call → parsed JSON.

    Refuses non-https URLs before any request leaves the process. An
    App-API rejection (e.g. a 401 from a bad App id / clock-skewed JWT)
    or a transport error is an EXPECTED failure → `GithubAppAuthError`.
    """
    if not url.startswith("https://"):
        raise GithubAppAuthError(
            detail=(
                f"refusing non-https GitHub API URL {url!r}; " "set GITHUB_API_URL to an https root"
            ),
        )
    request = urllib.request.Request(  # noqa: S310 — https-only enforced above; fixed scheme.
        url,
        data=b"{}" if method == "POST" else None,
        method=method,
        headers={
            "Authorization": f"Bearer {jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310 — https-only enforced above.
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GithubAppAuthError(detail=f"GitHub App API call to {url} failed: {exc}") from exc


def http_get_json(*, url: str, jwt: str) -> Any:
    """Production HTTP GET seam (JWT-authenticated)."""
    return _request_json(url=url, jwt=jwt, method="GET")


def http_post_json(*, url: str, jwt: str) -> Any:
    """Production HTTP POST seam (JWT-authenticated)."""
    return _request_json(url=url, jwt=jwt, method="POST")


DEFAULT_MINT_SEAMS = MintSeams(
    sign=sign_rs256_with_openssl,
    http_get=http_get_json,
    http_post=http_post_json,
)


def resolve_installation_id(
    *, api_url: str, jwt: str, installation_id: str | None, http_get: HttpJson
) -> str:
    """Return the installation id: the pinned one, else the App's sole install.

    Discovery is deliberately strict: anything other than exactly one
    installation is an EXPECTED ambiguity the operator resolves by
    pinning `GITHUB_APP_INSTALLATION_ID`.
    """
    if installation_id is not None and installation_id != "":
        return installation_id
    payload = http_get(url=f"{api_url}/app/installations", jwt=jwt)
    if not isinstance(payload, list):
        raise GithubAppAuthError(
            detail=(
                "the App /installations API did not return a list; "
                "set GITHUB_APP_INSTALLATION_ID to pin the installation to mint for"
            ),
        )
    installations = cast("list[object]", payload)
    if len(installations) != 1:
        raise GithubAppAuthError(
            detail=(
                f"the App has {len(installations)} installations; set "
                "GITHUB_APP_INSTALLATION_ID to pin the one to mint for"
            ),
        )
    return str(cast("dict[str, Any]", installations[0])["id"])


def mint_installation_token(
    *, config: GithubAppConfig, issued_at: int, seams: MintSeams = DEFAULT_MINT_SEAMS
) -> str:
    """Mint and return a GitHub App installation token (the railway entry point).

    Composes the pure JWT assembly with the injected signer + HTTP
    seams. The caller injects `issued_at` (epoch seconds) so the mint
    itself reads no ambient clock — the caching provider owns time.
    Raises `GithubAppAuthError` for every EXPECTED failure; caller bugs
    propagate as built-ins. The returned token is ephemeral: use it,
    never persist it at rest.
    """
    if config.app_id == "":
        raise GithubAppAuthError(
            detail="GITHUB_APP_ID is empty; the tenant's credential_wrapper must inject it",
        )
    if config.private_key_pem == "":
        raise GithubAppAuthError(
            detail="GITHUB_PRIVATE_KEY is empty; the tenant's credential_wrapper must inject it",
        )
    signing_input = jwt_signing_input(app_id=config.app_id, issued_at=issued_at)
    signature = seams.sign(
        signing_input=signing_input, pem=normalize_pem(raw=config.private_key_pem)
    )
    jwt = f"{signing_input}.{b64url(raw=signature)}"
    resolved = resolve_installation_id(
        api_url=config.api_url,
        jwt=jwt,
        installation_id=config.installation_id,
        http_get=seams.http_get,
    )
    minted = seams.http_post(
        url=f"{config.api_url}/app/installations/{resolved}/access_tokens", jwt=jwt
    )
    token = cast("dict[str, Any]", minted).get("token") if isinstance(minted, dict) else None
    if not isinstance(token, str) or token == "":
        raise GithubAppAuthError(
            detail=(
                f"installation {resolved} returned no access token; " "verify the App's permissions"
            ),
        )
    return token
