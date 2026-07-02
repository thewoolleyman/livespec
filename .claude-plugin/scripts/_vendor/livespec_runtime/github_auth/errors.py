"""GitHub App auth expected-error surface.

Per livespec/SPECIFICATION/non-functional-requirements.md (the
Result-vs-bugs split inherited from livespec-core): expected failures
bubble as concrete exception subclasses with structured detail;
unexpected failures propagate as raised built-ins to the outermost
supervisor.

`GithubAppAuthError` is the single domain error raised by the
`livespec_runtime.github_auth` modules for every EXPECTED failure on
the mint path: missing/empty credential env vars (the fail-closed
boundary — there is NEVER a fleet fallback), a private key openssl
cannot load, an App API rejection, or a malformed mint response. The
`detail` is an actionable diagnostic naming the specific cause and the
fix, per the fleet contract's "hard error with an actionable
diagnostic" requirement (livespec core
SPECIFICATION/non-functional-requirements.md).
"""

__all__: list[str] = ["GithubAppAuthError"]


class GithubAppAuthError(Exception):
    """An expected GitHub App auth failure (misconfiguration or API rejection).

    The `detail` field carries an actionable human-readable diagnostic
    (which env var is missing, what the wrapper should have injected,
    what the App API rejected); callers MAY surface it verbatim.
    """

    def __init__(self, *, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail
