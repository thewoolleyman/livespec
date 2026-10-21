#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(git -C "$script_dir" rev-parse --show-toplevel)"

exec python3 - "$repo_root" "$@" <<'PY'
from __future__ import annotations

import argparse
import calendar
import collections
import datetime as dt
import html
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, Sequence
from urllib.parse import urlparse


UTC = dt.timezone.utc
DEFAULT_SINCE = "2026-06-01"
REPORT_NAME = "livespec-governed-repo-activity.md"

COLORS = (
    "#332288",
    "#88CCEE",
    "#44AA99",
    "#117733",
    "#999933",
    "#DDCC77",
    "#CC6677",
    "#882255",
    "#AA4499",
    "#661100",
    "#6699CC",
    "#AA4466",
    "#4477AA",
    "#228833",
)

DOC_EXTENSIONS = {
    ".adoc",
    ".asciidoc",
    ".md",
    ".mdx",
    ".org",
    ".rst",
    ".txt",
}

CODE_EXTENSIONS = {
    ".astro",
    ".c",
    ".cc",
    ".cjs",
    ".clj",
    ".cljc",
    ".cljs",
    ".cpp",
    ".cs",
    ".css",
    ".cts",
    ".cxx",
    ".dart",
    ".erl",
    ".ex",
    ".exs",
    ".fish",
    ".fs",
    ".fsx",
    ".go",
    ".gql",
    ".graphql",
    ".h",
    ".hh",
    ".hpp",
    ".hrl",
    ".hs",
    ".htm",
    ".html",
    ".java",
    ".j2",
    ".jinja",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".less",
    ".lhs",
    ".lua",
    ".mjs",
    ".ml",
    ".mli",
    ".mts",
    ".nix",
    ".php",
    ".pl",
    ".pm",
    ".proto",
    ".ps1",
    ".py",
    ".pyi",
    ".pyx",
    ".r",
    ".rb",
    ".rs",
    ".sass",
    ".scala",
    ".scss",
    ".sh",
    ".sol",
    ".sql",
    ".svelte",
    ".swift",
    ".tera",
    ".thrift",
    ".tmpl",
    ".ts",
    ".tsx",
    ".vue",
    ".zsh",
}

SCRIPT_EXTENSIONS = {
    ".awk",
    ".bash",
    ".bat",
    ".cmd",
    ".mk",
    ".ps1",
    ".sed",
    ".sh",
    ".zsh",
}

SCRIPT_NAMES = {
    "containerfile",
    "dockerfile",
    "gnumakefile",
    "justfile",
    "makefile",
}

AUTOMATION_CONFIG_PREFIXES = (
    ".fabro/workflows/",
    ".github/actions/",
    ".github/workflows/",
    "ansible/",
    "infra/",
    "playbooks/",
    "roles/",
)

AUTOMATION_CONFIG_EXTENSIONS = {".json", ".toml", ".yaml", ".yml"}

EXCLUDED_PARTS = {
    ".cache",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".terraform",
    ".turbo",
    ".venv",
    "__pycache__",
    "_generated",
    "_vendor",
    "build",
    "coverage",
    "dist",
    "generated",
    "htmlcov",
    "node_modules",
    "site-packages",
    "target",
    "third-party",
    "third_party",
    "vendor",
    "vendored",
    "vendors",
}

DEPENDENCY_FILES = {
    ".copier-answers.yml",
    ".copier-answers.yaml",
    "cargo.lock",
    "composer.lock",
    "flake.lock",
    "gemfile.lock",
    "go.sum",
    "mix.lock",
    "package-lock.json",
    "pipfile.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}

DEPENDENCY_AUTHORS = {
    "dependabot[bot]",
    "dependabot-preview[bot]",
    "renovate[bot]",
    "renovate-bot",
    "release-please[bot]",
}

DEPENDENCY_LABELS = {
    "dependencies",
    "dependency",
    "deps",
    "renovate",
}

DEPENDENCY_SUBJECT_PATTERNS = (
    re.compile(r"^(?:build|chore|ci)(?:\([^)]*\))?!?:\s*(?:bump|refresh|update)\b.*\b(?:dependenc(?:y|ies)|deps?|image|pin|plugin|runtime|tooling|version|v\d)", re.I),
    re.compile(r"^(?:build|chore|ci)(?:\([^)]*\))?!?:\s*(?:freshness[- ]bump|self[- ]bump|bump[- ]pin)\b", re.I),
    re.compile(r"^(?:build|chore|ci)\(deps(?:-dev)?\)!?:", re.I),
    re.compile(r"^chore(?:\([^)]*\))?:\s*release\b", re.I),
)

TEMPLATE_AUTOMATION_PATTERNS = (
    re.compile(r"^(?:build|chore|ci)(?:\([^)]*\))?!?:\s*(?:apply|refresh|regenerate|render|sync|update)\b.*\b(?:copier|scaffold|template)\b", re.I),
    re.compile(r"^(?:build|chore|ci)\((?:copier|scaffold|template(?:-sync)?)\)!?:\s*(?:apply|refresh|regenerate|render|sync|update)\b", re.I),
)

GENERATED_FILE_PATTERNS = (
    re.compile(r"(?:^|/)coverage\.xml$", re.I),
    re.compile(r"(?:^|/).*\.min\.(?:css|js)$", re.I),
    re.compile(r"(?:^|/).*\.map$", re.I),
    re.compile(r"(?:^|/).*\.snap$", re.I),
)


def run(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    text: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        check=check,
        capture_output=True,
        text=text,
    )


def git(git_dir: Path, *args: str, text: bool = True) -> str | bytes:
    result = run(("git", "--git-dir", str(git_dir), *args), text=text)
    return result.stdout


def git_ref_exists(git_dir: Path, ref: str) -> bool:
    result = run(
        ("git", "--git-dir", str(git_dir), "show-ref", "--verify", "--quiet", ref),
        check=False,
    )
    return result.returncode == 0


def parse_date(value: str, *, option: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"{option} must be YYYY-MM-DD, got {value!r}") from exc


def jsonc_load(path: Path) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8")
    without_line_comments = re.sub(r"^\s*//.*$", "", raw, flags=re.MULTILINE)
    value = json.loads(without_line_comments)
    if not isinstance(value, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return value


def month_keys(start: dt.date, through: dt.date) -> list[str]:
    current = start.replace(day=1)
    end = through.replace(day=1)
    values: list[str] = []
    while current <= end:
        values.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return values


def month_cutoff(key: str, through: dt.date) -> dt.datetime:
    year, month = (int(part) for part in key.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    date = min(dt.date(year, month, last_day), through)
    return dt.datetime.combine(date, dt.time.max, tzinfo=UTC)


def parse_origin_slug(url: str) -> str:
    cleaned = url.strip()
    if cleaned.startswith("git@github.com:"):
        path = cleaned.split(":", 1)[1]
    elif cleaned.startswith("ssh://git@github.com/"):
        path = urlparse(cleaned).path.lstrip("/")
    else:
        parsed = urlparse(cleaned)
        if parsed.hostname != "github.com":
            raise SystemExit(f"unsupported non-GitHub origin URL: {cleaned}")
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git").strip("/")
    if path.count("/") != 1:
        raise SystemExit(f"cannot derive owner/repository from origin URL: {cleaned}")
    return path


def clone_candidates(name: str, explicit_root: Path | None, report_root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    roots = [
        explicit_root,
        report_root.parent,
        Path.home() / "workspaces",
        Path.home() / "workspace",
        Path("/data/projects"),
    ]
    for root in roots:
        if root is None:
            continue
        candidate = (root / name).resolve()
        if candidate not in seen:
            seen.add(candidate)
            yield candidate


def find_clone(name: str, explicit_root: Path | None, report_root: Path) -> Path:
    for candidate in clone_candidates(name, explicit_root, report_root):
        result = run(("git", "-C", str(candidate), "rev-parse", "--git-dir"), check=False)
        if result.returncode == 0:
            return candidate
    searched = ", ".join(str(path) for path in clone_candidates(name, explicit_root, report_root))
    raise SystemExit(f"no local clone found for {name}; searched: {searched}")


def source_object_dir(clone: Path) -> Path:
    raw = str(run(("git", "-C", str(clone), "rev-parse", "--git-path", "objects")).stdout).strip()
    path = Path(raw)
    if not path.is_absolute():
        path = clone / path
    return path.resolve()


def github_pull_requests(slug: str) -> list[dict[str, object]]:
    endpoint = f"repos/{slug}/pulls?state=all&per_page=100&sort=updated&direction=desc"
    result = run(("gh", "api", "--paginate", "--slurp", endpoint))
    pages = json.loads(str(result.stdout))
    return [item for page in pages for item in page]


def default_branch(clone: Path, slug: str) -> str:
    result = run(
        ("git", "-C", str(clone), "symbolic-ref", "--short", "refs/remotes/origin/HEAD"),
        check=False,
    )
    if result.returncode == 0:
        return str(result.stdout).strip().removeprefix("origin/")
    result = run(("gh", "repo", "view", slug, "--json", "defaultBranchRef"))
    value = json.loads(str(result.stdout))["defaultBranchRef"]["name"]
    return str(value)


def initialise_analysis_repo(clone: Path, origin_url: str, target: Path) -> None:
    run(("git", "init", "--bare", "--quiet", str(target)))
    info = target / "objects" / "info"
    info.mkdir(parents=True, exist_ok=True)
    (info / "alternates").write_text(f"{source_object_dir(clone)}\n", encoding="utf-8")
    git(target, "remote", "add", "origin", origin_url)
    git(
        target,
        "fetch",
        "--quiet",
        "--force",
        "--prune",
        "--no-tags",
        "origin",
        "+refs/heads/*:refs/heads/*",
    )


def fetch_pull_refs(git_dir: Path, numbers: Sequence[int]) -> None:
    for offset in range(0, len(numbers), 100):
        batch = numbers[offset : offset + 100]
        refspecs = tuple(
            f"+refs/pull/{number}/head:refs/pull/{number}/head" for number in batch
        )
        if refspecs:
            git(git_dir, "fetch", "--quiet", "--force", "--no-tags", "origin", *refspecs)


def is_automated_activity(subject: str, author: str = "", labels: Iterable[str] = ()) -> bool:
    lowered_author = author.casefold()
    lowered_labels = {label.casefold() for label in labels}
    if lowered_author in DEPENDENCY_AUTHORS:
        return True
    if lowered_labels & DEPENDENCY_LABELS:
        return True
    return any(pattern.search(subject) for pattern in (*DEPENDENCY_SUBJECT_PATTERNS, *TEMPLATE_AUTOMATION_PATTERNS))


def is_eligible_path(path: str) -> bool:
    normal = path.replace("\\", "/").lstrip("./")
    lower = normal.casefold()
    pure = PurePosixPath(lower)
    if set(pure.parts) & EXCLUDED_PARTS:
        return False
    basename = pure.name
    if basename in DEPENDENCY_FILES:
        return False
    if re.fullmatch(r"(?:requirements|constraints)(?:[-_.].*)?\.txt", basename):
        return False
    if any(pattern.search(lower) for pattern in GENERATED_FILE_PATTERNS):
        return False
    suffix = pure.suffix
    if suffix in DOC_EXTENSIONS | CODE_EXTENSIONS | SCRIPT_EXTENSIONS:
        return True
    if basename in SCRIPT_NAMES:
        return True
    return suffix in AUTOMATION_CONFIG_EXTENSIONS and lower.startswith(AUTOMATION_CONFIG_PREFIXES)


def parse_git_log(git_dir: Path, since: dt.datetime, through: dt.datetime) -> list[dict[str, object]]:
    raw = git(
        git_dir,
        "log",
        "--all",
        "--no-merges",
        f"--since={since.isoformat()}",
        f"--until={through.isoformat()}",
        "--format=%x1e%H%x00%ct%x00%an%x00%ae%x00%s%x00",
        "--numstat",
        "-z",
        text=False,
    )
    assert isinstance(raw, bytes)
    commits: list[dict[str, object]] = []
    for segment in raw.split(b"\x1e"):
        if not segment:
            continue
        fields = segment.split(b"\x00")
        if len(fields) < 7:
            continue
        sha = fields[0].decode("ascii")
        timestamp = int(fields[1])
        author = fields[2].decode("utf-8", "replace")
        email = fields[3].decode("utf-8", "replace")
        subject = fields[4].decode("utf-8", "replace")
        tokens = fields[6:]
        changes: list[tuple[int, int, str, str | None]] = []
        index = 0
        while index < len(tokens):
            token = tokens[index].lstrip(b"\n")
            index += 1
            if not token:
                continue
            parts = token.split(b"\t", 2)
            if len(parts) != 3:
                continue
            additions_raw, deletions_raw, path_raw = parts
            if additions_raw == b"-" or deletions_raw == b"-":
                continue
            additions = int(additions_raw)
            deletions = int(deletions_raw)
            if path_raw:
                path = path_raw.decode("utf-8", "surrogateescape")
                changes.append((additions, deletions, path, None))
            elif index + 1 < len(tokens):
                old_path = tokens[index].decode("utf-8", "surrogateescape")
                new_path = tokens[index + 1].decode("utf-8", "surrogateescape")
                index += 2
                changes.append((additions, deletions, new_path, old_path))
        commits.append(
            {
                "sha": sha,
                "timestamp": timestamp,
                "author": author,
                "email": email,
                "subject": subject,
                "changes": changes,
            }
        )
    return commits


def patch_ids(git_dir: Path, since: dt.datetime, through: dt.datetime) -> dict[str, str]:
    log = subprocess.Popen(
        (
            "git",
            "--git-dir",
            str(git_dir),
            "log",
            "--all",
            "--no-merges",
            f"--since={since.isoformat()}",
            f"--until={through.isoformat()}",
            "--pretty=format:commit %H",
            "-p",
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert log.stdout is not None
    patch = subprocess.run(
        ("git", "patch-id", "--stable"),
        stdin=log.stdout,
        capture_output=True,
        text=True,
    )
    log.stdout.close()
    stderr = log.stderr.read().decode("utf-8", "replace") if log.stderr else ""
    log_returncode = log.wait()
    if log_returncode != 0:
        raise SystemExit(f"git log for patch-id failed in {git_dir}: {stderr.strip()}")
    if patch.returncode != 0:
        raise SystemExit(f"git patch-id failed in {git_dir}: {patch.stderr.strip()}")
    mapping: dict[str, str] = {}
    for line in patch.stdout.splitlines():
        patch_id, sha = line.split()
        mapping[sha] = patch_id
    return mapping


def excluded_pr_patch_ids(
    git_dir: Path,
    prs: Sequence[dict[str, object]],
    commit_patch_ids: dict[str, str],
    since: dt.datetime,
) -> set[str]:
    excluded: set[str] = set()
    for pr in prs:
        user = pr.get("user") or {}
        labels = pr.get("labels") or []
        author = str(user.get("login") or "") if isinstance(user, dict) else ""
        label_names = [str(label.get("name") or "") for label in labels if isinstance(label, dict)]
        title = str(pr.get("title") or "")
        if not is_automated_activity(title, author, label_names):
            continue
        number = int(pr["number"])
        base = pr.get("base") or {}
        base_ref = str(base.get("ref") or "") if isinstance(base, dict) else ""
        command = [
            "rev-list",
            "--no-merges",
            f"--since={since.isoformat()}",
            f"refs/pull/{number}/head",
        ]
        if base_ref and git_ref_exists(git_dir, f"refs/heads/{base_ref}"):
            command.extend(("--not", f"refs/heads/{base_ref}"))
        raw = str(git(git_dir, *command))
        excluded.update(commit_patch_ids[sha] for sha in raw.splitlines() if sha in commit_patch_ids)
    return excluded


def activity_lines_by_month(
    git_dir: Path,
    prs: Sequence[dict[str, object]],
    months: Sequence[str],
    since: dt.datetime,
    through: dt.datetime,
) -> dict[str, int]:
    commits = parse_git_log(git_dir, since, through)
    ids = patch_ids(git_dir, since, through)
    excluded_ids = excluded_pr_patch_ids(git_dir, prs, ids, since)
    groups: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for commit in commits:
        sha = str(commit["sha"])
        groups[ids.get(sha, f"sha:{sha}")].append(commit)
    result = {month: 0 for month in months}
    for identity, copies in groups.items():
        if identity in excluded_ids:
            continue
        if any(
            is_automated_activity(str(commit["subject"]), str(commit["author"]))
            for commit in copies
        ):
            continue
        representative = min(copies, key=lambda commit: (int(commit["timestamp"]), str(commit["sha"])))
        month = dt.datetime.fromtimestamp(int(representative["timestamp"]), UTC).strftime("%Y-%m")
        if month not in result:
            continue
        for additions, deletions, path, old_path in representative["changes"]:  # type: ignore[assignment]
            eligible = is_eligible_path(path)
            if old_path is not None:
                eligible = eligible or is_eligible_path(old_path)
            if eligible:
                result[month] += additions + deletions
    return result


def closed_prs_by_month(
    prs: Sequence[dict[str, object]],
    months: Sequence[str],
    since: dt.datetime,
    through: dt.datetime,
) -> dict[str, int]:
    result = {month: 0 for month in months}
    for pr in prs:
        closed_raw = pr.get("closed_at")
        if not closed_raw:
            continue
        closed = dt.datetime.fromisoformat(str(closed_raw).replace("Z", "+00:00"))
        if since <= closed <= through:
            result[closed.strftime("%Y-%m")] += 1
    return result


def ls_tree_blobs(git_dir: Path, commit: str) -> collections.Counter[str]:
    raw = git(git_dir, "ls-tree", "-r", "-z", commit, text=False)
    assert isinstance(raw, bytes)
    blobs: collections.Counter[str] = collections.Counter()
    for record in raw.split(b"\x00"):
        if not record:
            continue
        metadata, path_raw = record.split(b"\t", 1)
        mode, kind, sha = metadata.decode("ascii").split()
        path = path_raw.decode("utf-8", "surrogateescape")
        if kind == "blob" and mode != "120000" and is_eligible_path(path):
            blobs[sha] += 1
    return blobs


def blob_line_counts(git_dir: Path, blob_ids: Iterable[str]) -> dict[str, int]:
    process = subprocess.Popen(
        ("git", "--git-dir", str(git_dir), "cat-file", "--batch"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    ordered = sorted(set(blob_ids))
    counts: dict[str, int] = {}
    for expected_sha in ordered:
        process.stdin.write(f"{expected_sha}\n".encode("ascii"))
        process.stdin.flush()
        header = process.stdout.readline().decode("ascii").strip()
        sha, kind, size_raw = header.split()
        if sha != expected_sha or kind != "blob":
            raise SystemExit(f"unexpected git cat-file response for {expected_sha}: {header}")
        data = process.stdout.read(int(size_raw))
        process.stdout.read(1)
        if b"\x00" in data:
            counts[sha] = 0
        else:
            counts[sha] = data.count(b"\n") + int(bool(data) and not data.endswith(b"\n"))
    process.stdin.close()
    if process.wait() != 0:
        raise SystemExit(f"git cat-file failed in {git_dir}")
    return counts


def current_lines_by_month(
    git_dir: Path,
    branch: str,
    months: Sequence[str],
    through_date: dt.date,
) -> dict[str, int]:
    snapshots: dict[str, str] = {}
    for month in months:
        cutoff = month_cutoff(month, through_date)
        commit = str(
            git(
                git_dir,
                "rev-list",
                "-1",
                f"--before={cutoff.isoformat()}",
                f"refs/heads/{branch}",
            )
        ).strip()
        snapshots[month] = commit
    trees = {
        month: ls_tree_blobs(git_dir, commit) if commit else collections.Counter()
        for month, commit in snapshots.items()
    }
    counts = blob_line_counts(git_dir, (sha for tree in trees.values() for sha in tree))
    return {
        month: sum(counts[sha] * copies for sha, copies in tree.items())
        for month, tree in trees.items()
    }


def relevant_prs(prs: Sequence[dict[str, object]], since: dt.datetime) -> list[dict[str, object]]:
    values = []
    for pr in prs:
        updated_raw = str(pr.get("updated_at") or "")
        if not updated_raw:
            continue
        updated = dt.datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
        if updated >= since:
            values.append(pr)
    return values


def format_number(value: int) -> str:
    return f"{value:,}"


def markdown_table(
    repos: Sequence[str],
    slugs: dict[str, str],
    months: Sequence[str],
    values: dict[str, dict[str, int]],
    *,
    stock: bool,
) -> str:
    columns = [*months, "Overall"]
    lines = [
        "| Repository | " + " | ".join(columns) + " |",
        "|:--|" + "|".join("--:" for _ in columns) + "|",
    ]
    for repo in repos:
        row = [values[repo][month] for month in months]
        overall = row[-1] if stock else sum(row)
        link = f"[{repo}](https://github.com/{slugs[repo]})"
        lines.append("| " + link + " | " + " | ".join(format_number(value) for value in [*row, overall]) + " |")
    totals = [sum(values[repo][month] for repo in repos) for month in months]
    overall_total = totals[-1] if stock else sum(totals)
    lines.append("| **Total** | " + " | ".join(f"**{format_number(value)}**" for value in [*totals, overall_total]) + " |")
    return "\n".join(lines)


def nice_ceiling(value: int) -> int:
    if value <= 0:
        return 1
    magnitude = 10 ** math.floor(math.log10(value))
    normalized = value / magnitude
    step = 1 if normalized <= 1 else 2 if normalized <= 2 else 5 if normalized <= 5 else 10
    return int(step * magnitude)


def svg_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def stacked_area_svg(
    *,
    title: str,
    description: str,
    y_label: str,
    months: Sequence[str],
    repos: Sequence[str],
    values: dict[str, dict[str, int]],
) -> str:
    width = 1440
    height = 660
    plot_left = 110
    plot_top = 70
    plot_width = 950
    plot_height = 450
    legend_left = 1100
    totals = [sum(values[repo][month] for repo in repos) for month in months]
    maximum = nice_ceiling(max(totals, default=0))
    x_values = [
        plot_left + (plot_width * index / max(1, len(months) - 1))
        for index in range(len(months))
    ]

    def y(value: int) -> float:
        return plot_top + plot_height - (plot_height * value / maximum)

    output = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{html.escape(title)}</title>",
        f"<desc id=\"desc\">{html.escape(description)}</desc>",
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}.title{font-size:22px;font-weight:600}.axis{font-size:13px}.label{font-size:15px;font-weight:600}.legend{font-size:12px}.grid{stroke:#d8dee4;stroke-width:1}.frame{stroke:#57606a;stroke-width:1.25;fill:none}</style>",
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text class="title" x="{plot_left}" y="35">{html.escape(title)}</text>',
    ]
    for tick in range(6):
        value = round(maximum * tick / 5)
        y_value = y(value)
        output.append(f'<line class="grid" x1="{plot_left}" y1="{svg_number(y_value)}" x2="{plot_left + plot_width}" y2="{svg_number(y_value)}"/>')
        output.append(f'<text class="axis" x="{plot_left - 12}" y="{svg_number(y_value + 4)}" text-anchor="end">{format_number(value)}</text>')
    cumulative = [0 for _ in months]
    for index, repo in enumerate(repos):
        lower = cumulative.copy()
        upper = [lower[position] + values[repo][month] for position, month in enumerate(months)]
        points = [f"{svg_number(x_values[position])},{svg_number(y(upper[position]))}" for position in range(len(months))]
        points.extend(
            f"{svg_number(x_values[position])},{svg_number(y(lower[position]))}"
            for position in reversed(range(len(months)))
        )
        output.append(
            f'<polygon points="{" ".join(points)}" fill="{COLORS[index]}" fill-opacity="0.88" stroke="#ffffff" stroke-width="0.8"><title>{html.escape(repo)}</title></polygon>'
        )
        cumulative = upper
    output.append(f'<rect class="frame" x="{plot_left}" y="{plot_top}" width="{plot_width}" height="{plot_height}"/>')
    label_every = max(1, math.ceil(len(months) / 12))
    for index, month in enumerate(months):
        if index % label_every == 0 or index == len(months) - 1:
            output.append(f'<text class="axis" x="{svg_number(x_values[index])}" y="{plot_top + plot_height + 28}" text-anchor="middle">{month}</text>')
    output.extend(
        (
            f'<text class="label" x="{plot_left + plot_width / 2}" y="{plot_top + plot_height + 68}" text-anchor="middle">Month (UTC)</text>',
            f'<text class="label" transform="translate(28 {plot_top + plot_height / 2}) rotate(-90)" text-anchor="middle">{html.escape(y_label)}</text>',
            f'<text class="label" x="{legend_left}" y="{plot_top}">Repositories</text>',
        )
    )
    for index, repo in enumerate(repos):
        y_value = plot_top + 28 + index * 28
        output.append(f'<rect x="{legend_left}" y="{y_value - 13}" width="18" height="18" rx="2" fill="{COLORS[index]}"/>')
        output.append(f'<text class="legend" x="{legend_left + 28}" y="{y_value + 1}">{html.escape(repo)}</text>')
    output.append("</svg>\n")
    return "\n".join(output)


def atomic_write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.chmod(0o755 if executable else 0o644)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate the livespec governed-repository activity report")
    parser.add_argument(
        "--since",
        default=os.environ.get("LIVESPEC_ACTIVITY_SINCE", DEFAULT_SINCE),
        help=f"first included UTC date (default: {DEFAULT_SINCE})",
    )
    parser.add_argument(
        "--through",
        default=os.environ.get("LIVESPEC_ACTIVITY_THROUGH"),
        help="last included UTC date (default: generation date)",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=os.environ.get("LIVESPEC_ACTIVITY_WORKSPACE_ROOT"),
        help="directory containing the governed repository clones",
    )
    args = parser.parse_args(sys.argv[2:])

    repo_root = Path(sys.argv[1]).resolve()
    generated_at = (
        dt.datetime.fromtimestamp(int(os.environ["SOURCE_DATE_EPOCH"]), UTC)
        if "SOURCE_DATE_EPOCH" in os.environ
        else dt.datetime.now(UTC)
    )
    start_date = parse_date(args.since, option="--since")
    through_date = parse_date(args.through, option="--through") if args.through else generated_at.date()
    if through_date < start_date:
        raise SystemExit("--through must not precede --since")
    since = dt.datetime.combine(start_date, dt.time.min, tzinfo=UTC)
    through = dt.datetime.combine(through_date, dt.time.max, tzinfo=UTC)
    months = month_keys(start_date, through_date)

    manifest = jsonc_load(repo_root / ".livespec-fleet-manifest.jsonc")
    fleet = manifest.get("fleet")
    adopters = manifest.get("adopters")
    if not isinstance(fleet, list) or not isinstance(adopters, list):
        raise SystemExit("fleet manifest must contain fleet[] and adopters[]")
    entries = [*fleet, *adopters]
    repos = [str(entry["repo"]) for entry in entries if isinstance(entry, dict)]
    if len(repos) != len(entries) or len(set(repos)) != len(repos):
        raise SystemExit("fleet manifest repository names must be present and unique")
    if len(repos) > len(COLORS):
        raise SystemExit(f"report has {len(repos)} repositories but only {len(COLORS)} chart colors")

    slugs: dict[str, str] = {}
    pr_values: dict[str, dict[str, int]] = {}
    activity_values: dict[str, dict[str, int]] = {}
    current_values: dict[str, dict[str, int]] = {}

    if shutil.which("gh") is None:
        raise SystemExit("gh is required and must be authenticated to GitHub")
    if shutil.which("git") is None:
        raise SystemExit("git is required")

    workspace_root = args.workspace_root.resolve() if args.workspace_root else None
    with tempfile.TemporaryDirectory(prefix="livespec-activity-") as temp_raw:
        temp = Path(temp_raw)
        for position, repo in enumerate(repos, start=1):
            print(f"[{position}/{len(repos)}] {repo}", file=sys.stderr, flush=True)
            clone = find_clone(repo, workspace_root, repo_root)
            origin_url = str(run(("git", "-C", str(clone), "remote", "get-url", "origin")).stdout).strip()
            slug = parse_origin_slug(origin_url)
            slugs[repo] = slug
            branch = default_branch(clone, slug)
            prs = github_pull_requests(slug)
            relevant = relevant_prs(prs, since)
            analysis_repo = temp / f"{repo}.git"
            initialise_analysis_repo(clone, origin_url, analysis_repo)
            fetch_pull_refs(analysis_repo, [int(pr["number"]) for pr in relevant])
            pr_values[repo] = closed_prs_by_month(prs, months, since, through)
            activity_values[repo] = activity_lines_by_month(
                analysis_repo,
                relevant,
                months,
                since,
                through,
            )
            current_values[repo] = current_lines_by_month(
                analysis_repo,
                branch,
                months,
                through_date,
            )

    output_dir = repo_root / "docs" / "activity"
    charts = (
        (
            "activity-closed-pull-requests.svg",
            stacked_area_svg(
                title="Pull requests closed per month",
                description="Monthly closed pull requests, stacked by governed repository.",
                y_label="Closed pull requests",
                months=months,
                repos=repos,
                values=pr_values,
            ),
        ),
        (
            "activity-modified-lines.svg",
            stacked_area_svg(
                title="Eligible lines modified per month",
                description="Monthly eligible additions plus deletions, stacked by governed repository.",
                y_label="Lines added + deleted",
                months=months,
                repos=repos,
                values=activity_values,
            ),
        ),
        (
            "activity-existing-lines.svg",
            stacked_area_svg(
                title="Eligible lines existing on default branches",
                description="Eligible physical lines at each month-end default-branch snapshot, stacked by governed repository.",
                y_label="Physical lines",
                months=months,
                repos=repos,
                values=current_values,
            ),
        ),
    )
    for filename, content in charts:
        atomic_write(output_dir / filename, content)

    generated_label = generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    report = f"""# Livespec-governed repository activity

Generated by [`update-activity.sh`](update-activity.sh) at **{generated_label}** from live GitHub pull-request data and freshly fetched Git refs. The reporting window is **{start_date.isoformat()} through {through_date.isoformat()} UTC** and includes all {len(repos)} entries in `.livespec-fleet-manifest.jsonc` (`fleet` and `adopters`).

## Activity tables

### Pull requests closed

{markdown_table(repos, slugs, months, pr_values, stock=False)}

### Eligible lines modified

{markdown_table(repos, slugs, months, activity_values, stock=False)}

### Eligible lines currently existing on default branches

{markdown_table(repos, slugs, months, current_values, stock=True)}

For the stock metric, completed month columns are month-end snapshots, the current month is a through-date snapshot, and `Overall` repeats the latest snapshot rather than summing snapshots.

## Stacked activity by repository

### Pull requests closed

![Stacked area chart of pull requests closed per month by repository](activity-closed-pull-requests.svg)

### Eligible lines modified

![Stacked area chart of eligible lines modified per month by repository](activity-modified-lines.svg)

### Eligible lines currently existing

![Stacked area chart of eligible physical lines on default branches by month and repository](activity-existing-lines.svg)

## What the graphs and numbers represent

The first graph is a monthly flow of pull requests whose GitHub `closed_at` timestamp falls inside the reporting window. It includes both merged pull requests and pull requests closed without merging. Dependency and automation pull requests remain in this count because the exclusion applies to line activity, not to the number of pull requests handled.

The second graph is a monthly flow of physical lines modified: additions plus deletions in eligible documentation, source-code, and script/automation files. The generator examines unique non-merge patches reachable from every current remote branch plus every pull-request head updated during the window. Stable patch IDs collapse the original and rebased/cherry-picked copies of the same change, so one logical patch is counted once. The earliest copy supplies its UTC month. AI-authored work, including Fabro/Codex-authored work, is intentionally included.

The third graph is a stock, not a flow. Each point counts physical lines present in eligible files on that repository's default branch at the end of the month (or at the report's through-date for the current month). Stacking the repository series shows the governed estate's total size and each repository's share. Its `Overall` column is the latest stock value; adding the monthly snapshots would be meaningless.

Eligible files are documentation (`.md`, `.mdx`, `.rst`, `.adoc`, `.org`, `.txt`), source and web/template languages, shell and other script formats, standard script entry files such as `Dockerfile`, `Makefile`, and `justfile`, plus YAML/JSON/TOML automation under workflow and infrastructure directories. Counts are physical lines, including comments and blank lines, so the stock metric is directly comparable to Git's physical-line additions and deletions.

Excluded line activity is deterministic and intentionally conservative: known dependency/lock files; dependency, release, pin-bump, and automated template-sync commits/PRs; vendored or third-party trees; generated/build/cache/output trees; source maps, minified assets, snapshots, and other generated artifacts. Merge commits are excluded because their branch patches are counted directly. Binary changes have no line count. Rename detection is retained, so a pure rename contributes zero modified lines. The exact extension lists and classifiers live in the generator and are documented operationally in [`AGENTS.md`](AGENTS.md).

Repository identity and default branches come from each local clone's `origin`; this matters for entries such as `homelab`, whose GitHub organization differs from the manifest's fleet-owner default. Analysis happens in temporary bare repositories that borrow the local clone's object database, then fetch current GitHub branch and relevant pull-request refs without changing the clone's branches or working tree.
"""
    atomic_write(output_dir / REPORT_NAME, report)
    print(f"wrote {output_dir / REPORT_NAME}", file=sys.stderr)
    for filename, _ in charts:
        print(f"wrote {output_dir / filename}", file=sys.stderr)


if __name__ == "__main__":
    main()
PY
