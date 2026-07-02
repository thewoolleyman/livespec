"""Env-only fail-closed config boundary for the GitHub App mint.

Inputs come ONLY from environment variables injected by the calling
tenant's credential_wrapper (the fleet ships GITHUB_APP_ID +
GITHUB_PRIVATE_KEY per the fleet contract in livespec core's
SPECIFICATION/non-functional-requirements.md). A missing or empty
required var is a hard error with an actionable diagnostic — NEVER a
silent fallback to the fleet's credential (the fleet is adopter #0; it
holds no privileged path). The caller passes an environ snapshot
(typically `os.environ`) so the boundary is a total, process-free
function of its inputs, mirroring
`livespec_runtime.credentials.decide_credentials`.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from livespec_runtime.github_auth.errors import GithubAppAuthError

__all__: list[str] = ["DEFAULT_API_URL", "GithubAppConfig", "load_github_app_config"]

DEFAULT_API_URL = "https://api.github.com"

_APP_ID_VAR = "GITHUB_APP_ID"
_PRIVATE_KEY_VAR = "GITHUB_PRIVATE_KEY"
_INSTALLATION_ID_VAR = "GITHUB_APP_INSTALLATION_ID"
_API_URL_VAR = "GITHUB_API_URL"


@dataclass(frozen=True, slots=True, kw_only=True)
class GithubAppConfig:
    """The resolved GitHub App mint inputs (the PEM is the durable secret).

    `installation_id` is the optional pin for Apps with more than one
    installation; `None` defers to sole-installation discovery at mint
    time. `api_url` covers GitHub Enterprise API roots; the default is
    the public API.
    """

    app_id: str
    private_key_pem: str
    api_url: str = DEFAULT_API_URL
    installation_id: str | None = None


def load_github_app_config(*, environ: Mapping[str, str]) -> GithubAppConfig:
    """Resolve the App mint inputs from the wrapper-injected environment.

    Fail-closed per the fleet contract: raises `GithubAppAuthError`
    naming EVERY absent-or-empty required variable (a name mapping to
    an empty string counts as missing), pointing the operator at the
    calling tenant's credential_wrapper. The optional installation-id
    pin and API-URL override fall back to their defaults when absent
    or empty.
    """
    missing = [name for name in (_APP_ID_VAR, _PRIVATE_KEY_VAR) if not environ.get(name)]
    if missing:
        raise GithubAppAuthError(
            detail=(
                f"required GitHub App env var(s) {missing} absent or empty; "
                "automated GitHub operations resolve their credential ONLY through "
                "the calling tenant's credential_wrapper environment injection "
                "(e.g. with-livespec-env.sh) — there is NO fleet fallback. Run under "
                "the tenant's wrapper, or fix the wrapper to inject them."
            ),
        )
    return GithubAppConfig(
        app_id=environ[_APP_ID_VAR].strip(),
        private_key_pem=environ[_PRIVATE_KEY_VAR],
        api_url=environ.get(_API_URL_VAR) or DEFAULT_API_URL,
        installation_id=environ.get(_INSTALLATION_ID_VAR) or None,
    )
