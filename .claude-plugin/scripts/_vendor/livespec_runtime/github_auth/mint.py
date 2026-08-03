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

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

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
    """RS256 signer seam (production: `signing.sign_rs256_with_openssl`).

    ⛔ THE PROTOCOL AND ITS IMPLEMENTATION CANNOT BE SPLIT. Changing the
    signer's return type IS changing this protocol, and a tree part-way
    through that change does not type-check.
    """

    def __call__(self, *, signing_input: str, pem: str) -> IOResult[bytes, GithubAppAuthError]: ...


class HttpJson(Protocol):
    """JWT-authenticated GitHub REST call seam returning parsed JSON."""

    def __call__(self, *, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]: ...


@dataclass(frozen=True, slots=True, kw_only=True)
class MintSeams:
    """The injectable side-effecting seams of the mint (defaulted to production)."""

    sign: SignRs256
    http_get: HttpJson
    http_post: HttpJson


def _request_json(*, url: str, jwt: str, method: str) -> IOResult[Any, GithubAppAuthError]:
    """JWT-authenticated GitHub REST call → parsed JSON.

    Refuses non-https URLs before any request leaves the process. An
    App-API rejection (e.g. a 401 from a bad App id / clock-skewed JWT)
    or a transport error is an EXPECTED failure → `GithubAppAuthError`.
    """
    if not url.startswith("https://"):
        return IOFailure(
            GithubAppAuthError(
                detail=(
                    f"refusing non-https GitHub API URL {url!r}; "
                    "set GITHUB_API_URL to an https root"
                ),
            )
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
            decoded: Any = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return IOFailure(GithubAppAuthError(detail=f"GitHub App API call to {url} failed: {exc}"))
    return IOSuccess(decoded)


def http_get_json(*, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]:
    """Production HTTP GET seam (JWT-authenticated)."""
    return _request_json(url=url, jwt=jwt, method="GET")


def http_post_json(*, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]:
    """Production HTTP POST seam (JWT-authenticated)."""
    return _request_json(url=url, jwt=jwt, method="POST")


DEFAULT_MINT_SEAMS = MintSeams(
    sign=sign_rs256_with_openssl,
    http_get=http_get_json,
    http_post=http_post_json,
)


def resolve_installation_id(
    *, api_url: str, jwt: str, installation_id: str | None, http_get: HttpJson
) -> IOResult[str, GithubAppAuthError]:
    """Return the installation id: the pinned one, else the App's sole install.

    Discovery is deliberately strict: anything other than exactly one
    installation is an EXPECTED ambiguity the operator resolves by
    pinning `GITHUB_APP_INSTALLATION_ID`.
    """
    if installation_id is not None and installation_id != "":
        return IOSuccess(installation_id)
    listed = http_get(url=f"{api_url}/app/installations", jwt=jwt)
    if isinstance(listed, IOFailure):
        return listed
    payload = unsafe_perform_io(listed.unwrap())
    if not isinstance(payload, list):
        return IOFailure(
            GithubAppAuthError(
                detail=(
                    "the App /installations API did not return a list; "
                    "set GITHUB_APP_INSTALLATION_ID to pin the installation to mint for"
                ),
            )
        )
    installations = cast("list[object]", payload)
    if len(installations) != 1:
        return IOFailure(
            GithubAppAuthError(
                detail=(
                    f"the App has {len(installations)} installations; set "
                    "GITHUB_APP_INSTALLATION_ID to pin the one to mint for"
                ),
            )
        )
    return IOSuccess(str(cast("dict[str, Any]", installations[0])["id"]))


def mint_installation_token(
    *, config: GithubAppConfig, issued_at: int, seams: MintSeams = DEFAULT_MINT_SEAMS
) -> IOResult[str, GithubAppAuthError]:
    """Mint and return a GitHub App installation token (the railway entry point).

    Composes the pure JWT assembly with the injected signer + HTTP
    seams. The caller injects `issued_at` (epoch seconds) so the mint
    itself reads no ambient clock — the caching provider owns time.
    Raises `GithubAppAuthError` for every EXPECTED failure; caller bugs
    propagate as built-ins. The returned token is ephemeral: use it,
    never persist it at rest.
    """
    gap = _credential_gap(config=config)
    if gap is not None:
        return IOFailure(gap)
    signing_input = jwt_signing_input(app_id=config.app_id, issued_at=issued_at)
    signed = seams.sign(signing_input=signing_input, pem=normalize_pem(raw=config.private_key_pem))
    if isinstance(signed, IOFailure):
        return signed
    jwt = f"{signing_input}.{b64url(raw=unsafe_perform_io(signed.unwrap()))}"
    return _token_for_installation(config=config, jwt=jwt, seams=seams)


def _credential_gap(*, config: GithubAppConfig) -> GithubAppAuthError | None:
    """The fail-closed credential precondition, or `None` when both are present.

    ⛔ `GithubAppAuthError | None` HERE IS A LEGITIMATE ABSENCE, NOT A
    HAND-ROLLED FAILURE TRACK: `None` means "no gap", the ordinary answer.
    The failure this reports rides the caller's `IOResult` one line up.
    """
    if config.app_id == "":
        return GithubAppAuthError(
            detail="GITHUB_APP_ID is empty; the tenant's credential_wrapper must inject it",
        )
    if config.private_key_pem == "":
        return GithubAppAuthError(
            detail="GITHUB_PRIVATE_KEY is empty; the tenant's credential_wrapper must inject it",
        )
    return None


def _token_for_installation(
    *, config: GithubAppConfig, jwt: str, seams: MintSeams
) -> IOResult[str, GithubAppAuthError]:
    """Resolve the installation and POST for its token, given a signed App JWT.

    Split from `mint_installation_token` so neither carries the other's
    branches: that one owns the credential precondition and the signature,
    this one owns the two API calls and what their answers must contain.
    """
    identified = resolve_installation_id(
        api_url=config.api_url,
        jwt=jwt,
        installation_id=config.installation_id,
        http_get=seams.http_get,
    )
    if isinstance(identified, IOFailure):
        return identified
    resolved = unsafe_perform_io(identified.unwrap())
    posted = seams.http_post(
        url=f"{config.api_url}/app/installations/{resolved}/access_tokens", jwt=jwt
    )
    if isinstance(posted, IOFailure):
        return posted
    minted = unsafe_perform_io(posted.unwrap())
    token = cast("dict[str, Any]", minted).get("token") if isinstance(minted, dict) else None
    if not isinstance(token, str) or token == "":
        return IOFailure(
            GithubAppAuthError(
                detail=(
                    f"installation {resolved} returned no access token; "
                    "verify the App's permissions"
                ),
            )
        )
    return IOSuccess(token)
