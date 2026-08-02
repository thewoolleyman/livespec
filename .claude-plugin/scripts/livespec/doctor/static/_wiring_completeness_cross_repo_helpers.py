# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# json.loads returns Any; isinstance(x, dict) narrows to
# dict[Unknown, Unknown] under pyright strict mode and the
# subsequent .get() calls + dict membership tests surface as
# partially-unknown types. The runtime behavior is correct
# (every value is re-checked via isinstance at each .get()
# call site), so the per-line cast burden buys no real safety
# in this pure-helper module. Non-railway code in this tree
# retains full enforcement (other helpers do not carry this
# pragma).
"""Private helpers for `wiring_completeness_cross_repo`.

Extracts the pure helpers (URL parsing, justfile parsing, slug
diffing, manifest filtering, finding construction, gh-payload
decoding) from the parent module so the public check wrapper
stays below the 250-LLOC hard ceiling enforced by the per-file
LLOC check.

Per `SPECIFICATION/contracts.md`, the cross-repo wiring-completeness
invariant walks every registered sibling repo, reads its
`justfile`'s `check` recipe, computes the canonical-set
difference, and fires `fail` on any aggregate lacking any
canonical slug.

This helpers module owns:

- `parse_owner_name_from_github_url` — extract `(owner, name)`
  from a canonical `https://github.com/<owner>/<name>` URL.
- `extract_check_slugs_from_justfile` — parse a justfile's
  `check:` recipe to extract the wired-slug list.
- `compute_missing_slugs` — set difference between the canonical
  slug tuple and a sibling's wired slug list.
- `decode_gh_contents_payload` — base64-decode the `content`
  field of a `gh api contents/<path>` JSON response.
- `interpret_justfile_text` — map a justfile text (or None) to
  per-sibling missing-slug pairs.
- `filter_sibling_targets` — drop non-dict and host-repo entries
  from the manifest.
- `is_host_repo` — detect whether a target's local_clone
  resolves to the project_root.
- `build_aggregate_finding` — construct the pass/fail Finding
  payload from the full (sibling, missing-slug) set.
- `make_finding` — build a Finding bound to the check's SLUG.
- `resolve_effective_local_clone` — apply the
  `LIVESPEC_SIBLING_CLONES_ROOT` env-var override (when set) on top
  of the manifest's `local_clone` field. CI sets the env var to a
  freshly-cloned siblings-root so the check passes against
  ephemeral GitHub Actions runners that do not have
  `/data/projects/<sibling>/` populated.

All functions in this module are pure (no I/O, no global state);
the IO boundary lives in the parent module's `run()`. The env-var
read in `resolve_effective_local_clone` is a process-state read
(read-only); the cross-boundary policy classifies env-var reads
alongside config-file reads — both pure.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, NamedTuple

from returns.result import Success, safe

from livespec.context import DoctorContext
from livespec.doctor.static._wiring_completeness_host import is_host_repo
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = [
    "CLONES_ROOT_ENV_VAR",
    "GithubRepoIdentity",
    "build_aggregate_finding",
    "compute_missing_slugs",
    "decode_gh_contents_payload",
    "extract_check_slugs_from_justfile",
    "filter_sibling_targets",
    "interpret_justfile_text",
    "is_host_repo",
    "make_finding",
    "parse_owner_name_from_github_url",
    "resolve_effective_local_clone",
]


# Env-var override for sibling local-clone roots. When set, the
# cross-repo wiring check resolves a sibling's clone path as
# `<env-var-value>/<sibling-slug>` regardless of the manifest's
# `local_clone` field. CI sets this to a fresh clones-root the
# workflow populates with `git clone --depth 1` of each sibling at
# its default branch; locally, the env var is normally unset and
# the manifest's `local_clone` path (e.g. `/data/projects/<sibling>`)
# is used directly.
CLONES_ROOT_ENV_VAR: str = "LIVESPEC_SIBLING_CLONES_ROOT"


_SLUG: CheckId = CheckId("doctor-wiring-completeness-cross-repo")


# Pattern matching the canonical `https://github.com/<owner>/<name>`
# URL contract from `.livespec.jsonc`'s `cross_repo_targets`
# `github_url` field. No trailing `.git`. Group 1 captures the
# owner; group 2 captures the name. Both segments allow any
# non-slash characters; further validation is the
# `cross-repo-targets-wellformedness` invariant's domain.
_GITHUB_URL_PATTERN: re.Pattern[str] = re.compile(
    r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
)

# Pattern matching the `check:` recipe head; we then walk the
# captured body until the closing `)` of the `targets=(...)`
# bash-array literal. Justfiles use a fixed two-space-or-greater
# indent for recipe bodies; we tolerate any leading whitespace.
_CHECK_RECIPE_HEAD_PATTERN: re.Pattern[str] = re.compile(r"^check\s*:\s*$", re.MULTILINE)

# Pattern matching the `targets=(` opener; once matched, the slug
# extractor walks line-by-line collecting bare slug tokens until
# it hits the closing `)`. Whitespace before/after permitted.
_TARGETS_OPENER_PATTERN: re.Pattern[str] = re.compile(r"^\s*targets\s*=\s*\(\s*$")

# Pattern matching the closing `)` of the `targets=(...)` array.
# Trailing comments after the close-paren are tolerated.
_TARGETS_CLOSER_PATTERN: re.Pattern[str] = re.compile(
    r"^\s*\)\s*(?:#.*)?$",
)

# Pattern matching a single slug entry inside the targets array.
# Justfile convention: one slug per line, optional surrounding
# whitespace, optional trailing comment. Comments-only lines and
# blank lines are skipped by the caller.
_TARGET_SLUG_PATTERN: re.Pattern[str] = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9_-]*)\s*(?:#.*)?$",
)


class GithubRepoIdentity(NamedTuple):
    """`(owner, name)` identity extracted from a github_url."""

    owner: str
    name: str


def parse_owner_name_from_github_url(*, github_url: str) -> GithubRepoIdentity | None:
    """Extract `(owner, name)` from a canonical github_url.

    Returns `None` when the URL does not match the canonical
    `https://github.com/<owner>/<name>` shape. The
    `cross-repo-targets-wellformedness` invariant catches
    malformed URLs upstream; this helper degrades gracefully
    (skip the sibling) rather than raising.
    """
    match = _GITHUB_URL_PATTERN.match(github_url)
    if match is None:
        return None
    return GithubRepoIdentity(owner=match.group(1), name=match.group(2))


def extract_check_slugs_from_justfile(*, justfile_text: str) -> tuple[str, ...] | None:
    """Extract the canonical-aggregate slug list from a justfile's `check:` recipe.

    Walks the justfile text line-by-line: finds the `check:`
    recipe head, then the `targets=(` opener, then collects
    every bare slug token until the closing `)`. Returns a
    tuple of slugs in declaration order.

    Returns `None` when no `check:` recipe is found OR when no
    `targets=(...)` array exists inside that recipe.
    """
    lines = justfile_text.splitlines()
    in_check_recipe = False
    in_targets_array = False
    collected: list[str] = []
    for line in lines:
        if _CHECK_RECIPE_HEAD_PATTERN.match(line):
            in_check_recipe = True
            continue
        if not in_check_recipe:
            continue
        if not in_targets_array:
            if _TARGETS_OPENER_PATTERN.match(line):
                in_targets_array = True
            continue
        if _TARGETS_CLOSER_PATTERN.match(line):
            return tuple(collected)
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        slug_match = _TARGET_SLUG_PATTERN.match(line)
        if slug_match is not None:
            collected.append(slug_match.group(1))
    if not in_targets_array:
        return None
    # Reached EOF inside the targets array without a closer; treat
    # as a malformed justfile and return what we found so far.
    return tuple(collected)


def compute_missing_slugs(
    *,
    canonical_slugs: tuple[str, ...],
    wired_slugs: tuple[str, ...],
) -> tuple[str, ...]:
    """Return the sorted tuple of canonical slugs absent from `wired_slugs`."""
    wired_set = set(wired_slugs)
    return tuple(slug for slug in canonical_slugs if slug not in wired_set)


@safe(exceptions=(json.JSONDecodeError,))
def _raw_json_loads(*, stdout: str) -> Any:
    """`@safe`-lifted call into stdlib json.loads."""
    return json.loads(stdout)


@safe(exceptions=(ValueError, TypeError))
def _raw_b64_decode(*, content: str) -> bytes:
    """`@safe`-lifted call into base64.b64decode."""
    return base64.b64decode(content)


@safe(exceptions=(UnicodeDecodeError,))
def _raw_utf8_decode(*, decoded: bytes) -> str:
    """`@safe`-lifted call into bytes.decode."""
    return decoded.decode("utf-8")


def decode_gh_contents_payload(*, stdout: str) -> str | None:
    """Decode the base64-encoded `content` field of a gh contents response.

    The `gh api contents/<path>` endpoint returns a JSON object
    with `content` (base64-encoded file body, possibly with
    embedded newlines) and `encoding` (`"base64"`). On a
    malformed payload (non-JSON, missing field, wrong encoding,
    base64 decode error), return `None` so the caller treats
    the sibling as unfetchable.

    The three exception classes that callable side-effects raise
    here (JSONDecodeError, ValueError/TypeError, UnicodeDecodeError)
    are converted to Result via `@safe`-lifted helpers; this
    function is pure (no try/except) and chains the Results
    through isinstance-based narrowing.
    """
    parsed_result = _raw_json_loads(stdout=stdout)
    if not isinstance(parsed_result, Success):
        return None
    parsed = parsed_result.unwrap()
    if not isinstance(parsed, dict):
        return None
    content = parsed.get("content")
    encoding = parsed.get("encoding")
    if not isinstance(content, str) or encoding != "base64":
        return None
    decoded_result = _raw_b64_decode(content=content)
    if not isinstance(decoded_result, Success):
        return None
    text_result = _raw_utf8_decode(decoded=decoded_result.unwrap())
    if not isinstance(text_result, Success):
        return None
    return text_result.unwrap()


def interpret_justfile_text(
    *,
    sibling_slug: str,
    justfile_text: str | None,
    canonical_slugs: tuple[str, ...],
) -> list[tuple[str, str]]:
    """Map (justfile_text, canonical_slugs) to per-sibling missing-slug pairs."""
    if justfile_text is None:
        return [(sibling_slug, ":no-justfile-resolved")]
    wired_slugs = extract_check_slugs_from_justfile(justfile_text=justfile_text)
    if wired_slugs is None:
        return [(sibling_slug, ":no-check-recipe")]
    missing = compute_missing_slugs(canonical_slugs=canonical_slugs, wired_slugs=wired_slugs)
    return [(sibling_slug, slug) for slug in missing]


def resolve_effective_local_clone(
    *,
    sibling_slug: str,
    target: dict[str, Any],
    env: dict[str, str] | None = None,
) -> str | None:
    """Return the effective `local_clone` path for `sibling_slug`.

    Precedence:
      1. When the `LIVESPEC_SIBLING_CLONES_ROOT` env var is set to a
         non-empty value, return `<value>/<sibling_slug>`. This is
         the CI path — the workflow clones siblings to a freshly-
         provisioned root and points the check at it via the env var.
      2. Otherwise, return `target.local_clone` when present and
         non-empty (the local-dev path against
         `/data/projects/<sibling>`).
      3. Otherwise, return `None` to signal Path A is unavailable.

    `env` defaults to `os.environ` — accepting an explicit dict
    keeps the helper testable without monkeypatching the process
    environment.
    """
    effective_env = os.environ if env is None else env
    clones_root = effective_env.get(CLONES_ROOT_ENV_VAR, "")
    if clones_root != "":
        return str(Path(clones_root) / sibling_slug)
    local_clone_raw = target.get("local_clone")
    if isinstance(local_clone_raw, str) and local_clone_raw != "":
        return local_clone_raw
    return None


def filter_sibling_targets(
    *,
    cross_repo_targets: dict[str, Any],
    project_root: Path,
    env: dict[str, str] | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Drop non-dict and host-repo entries from the manifest."""
    sibling_targets: list[tuple[str, dict[str, Any]]] = []
    for slug, target in cross_repo_targets.items():
        if not isinstance(target, dict):
            continue
        if is_host_repo(
            sibling_slug=slug,
            target=target,
            project_root=project_root,
            env=env,
        ):
            continue
        sibling_targets.append((slug, target))
    return sibling_targets


def make_finding(
    *,
    ctx: DoctorContext,
    status: str,
    message: str,
) -> Finding:
    """Build a Finding bound to the check's SLUG + ctx.spec_root."""
    return Finding(
        check_id=_SLUG,
        status=status,
        message=message,
        path=None,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def build_aggregate_finding(
    *,
    ctx: DoctorContext,
    all_pairs: list[tuple[str, str]],
) -> Finding:
    """Build the aggregate Finding from the full (sibling, missing-slug) set."""
    if not all_pairs:
        return make_finding(
            ctx=ctx,
            status="pass",
            message=(
                "wiring-completeness-cross-repo: every registered sibling's "
                "`check` aggregate wires every canonical slug"
            ),
        )
    pairs_joined = ", ".join(f"{sibling}→{slug}" for sibling, slug in sorted(all_pairs))
    return make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"wiring-completeness-cross-repo: {len(all_pairs)} "
            f"(sibling, missing-canonical-slug) drift pair(s): "
            f"{pairs_joined}. Corrective action: open a bump PR against "
            "each offending sibling that re-wires the missing canonical "
            "slug(s) into the consumer's `just check` aggregate (per "
            '`SPECIFICATION/contracts.md` §"Shared code sync — '
            'livespec-dev-tooling").'
        ),
    )
