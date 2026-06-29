"""Fractional-index `rank` wrapper + the shared bottom-sentinel constant.

The thin livespec-facing surface over the ported, CC0-1.0
`_fractional_indexing` module (the Figma/`rocicorp` fractional-indexing
scheme). `rank` is the work-item lifecycle's sole ordering authority: a
self-contained lexicographic key, merge-robust in the append-only /
git-merged / concurrent-agent world (no pointers to dangle; an insert
rewrites exactly one item's key).

- `key_between(*, a, b)` — a fresh key ordering strictly between the
  neighbor keys `a` and `b` (`None` = open end). The single-insert path.
- `n_keys_between(*, a, b, n)` — `n` evenly-spaced keys between the
  neighbors; the bulk generator the orchestrator's `rebalance-ranks`
  command and the one-time `rank` backfill reuse.
- `BOTTOM_SENTINEL` — the shared constant a backend store ADAPTER
  substitutes for a legacy line written before `rank` existed. It uses a
  character OUTSIDE the lib's base-62 alphabet (`0-9A-Za-z`), so it sorts
  strictly AFTER every real key and a rank-less legacy line lands last
  rather than crashing a listing. The domain `WorkItem.rank` type stays a
  strict non-null `str`; the sentinel lives only in the adapter read path.

The keys are valid base-62 order keys (`generate_key_between` /
`generate_n_keys_between`); the wrapper keeps the livespec call sites
keyword-only and free of the ported module's positional, base-parameter
signature.
"""

from livespec_runtime.work_items._fractional_indexing import (
    generate_key_between,
    generate_n_keys_between,
)

__all__: list[str] = ["BOTTOM_SENTINEL", "key_between", "n_keys_between"]

# A char outside the base-62 alphabet ('0'-'9','A'-'Z','a'-'z'; max 'z' is
# 0x7A). '~' is 0x7E > 0x7A, so it sorts strictly after every real key.
BOTTOM_SENTINEL = "~"


def key_between(*, a: str | None, b: str | None) -> str:
    """Return a fresh order key ordering strictly between `a` and `b`.

    `a` / `b` are existing order keys or `None` for the open start / end.
    """
    return generate_key_between(a, b)


def n_keys_between(*, a: str | None, b: str | None, n: int) -> list[str]:
    """Return `n` order keys, evenly spaced and sorted, between `a` and `b`.

    `a` / `b` are existing order keys or `None` for the open start / end;
    `n >= 0` (returns `[]` for `n == 0`).
    """
    return generate_n_keys_between(a, b, n)
