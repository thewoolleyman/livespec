"""Caching installation-token provider — re-mints transparently BEFORE expiry.

Pillar 1's HARD requirement (github-app-auth design record): token
acquisition MUST be a mint-or-refresh capability callable at any time
by any factory machine/process, transparent to callers — NEVER a
once-at-start `export GH_TOKEN=...` that assumes the run finishes
within an hour. Operations that outlive a token's ~1-hour validity
(e.g. the ~76-minute merge-poll) keep working because any access past
the refresh horizon re-mints without caller involvement.

The minted token lives in process memory ONLY — never persisted at
rest, per the fleet contract in livespec core's
SPECIFICATION/non-functional-requirements.md. The refresh horizon is
55 minutes from mint time, safely BEFORE GitHub's ~60-minute
installation-token expiry, so a caller always holds a token with
several minutes of remaining validity. Refresh is lazy on access — no
threads, no asyncio, per this library's process-boundary constraints
(SPECIFICATION/constraints.md).
"""

import time
from collections.abc import Callable

from livespec_runtime.github_auth.config import GithubAppConfig
from livespec_runtime.github_auth.mint import (
    DEFAULT_MINT_SEAMS,
    MintSeams,
    mint_installation_token,
)

__all__: list[str] = ["TOKEN_REFRESH_SECONDS", "InstallationTokenProvider"]

# 55 minutes: re-mint safely BEFORE GitHub's ~60-minute token expiry.
TOKEN_REFRESH_SECONDS = 55 * 60


class InstallationTokenProvider:
    """Mints on first use; caches ~55 minutes; re-mints transparently.

    `clock` and `seams` are injectable for tests (fake time forces
    expiry mid-sequence without sleeping); production defaults are
    `time.time` and the openssl+urllib mint seams. The provider is
    synchronous and not thread-safe by design — one provider per
    process/loop, matching the library's no-threads constraint.
    """

    def __init__(
        self,
        *,
        config: GithubAppConfig,
        seams: MintSeams = DEFAULT_MINT_SEAMS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._config = config
        self._seams = seams
        self._clock = clock
        self._token: str | None = None
        self._refresh_at = 0.0

    def token(self) -> str:
        """Return a currently-valid installation token, re-minting if needed.

        Callers never handle expiry: any access at or past the refresh
        horizon mints a fresh token first. Mint failures raise
        `GithubAppAuthError` (fail-closed; no fallback credential).
        """
        now = self._clock()
        if self._token is None or now >= self._refresh_at:
            self._token = mint_installation_token(
                config=self._config,
                issued_at=int(now),
                seams=self._seams,
            )
            self._refresh_at = now + TOKEN_REFRESH_SECONDS
        return self._token
