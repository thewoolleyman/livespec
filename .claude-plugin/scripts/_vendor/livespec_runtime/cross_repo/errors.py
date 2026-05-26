"""Cross-repo expected-error surface.

Per livespec/SPECIFICATION/non-functional-requirements.md
§"Error discipline" (the Result-vs-bugs split inherited from
livespec-core): expected failures bubble as concrete exception
subclasses with structured detail; unexpected failures propagate
as raised built-ins to the outermost supervisor.

`CrossRepoSchemaError` is the single domain error raised by the
parser helpers in `livespec_runtime.cross_repo.types` when a dict
representation of a `DependsOnEntry` or `cross_repo_targets` block
deviates from the schema codified in livespec/SPECIFICATION/
contracts.md v072 §"Cross-repo dependency awareness".
"""

__all__: list[str] = ["CrossRepoSchemaError"]


class CrossRepoSchemaError(Exception):
    """A dict-shaped cross-repo payload violated the schema contract.

    The `detail` field carries a human-readable description of the
    specific deviation (missing required field, unknown kind, etc.);
    callers MAY surface it verbatim.
    """

    def __init__(self, *, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail
