"""Primary, branch, and pull-request hygiene findings."""

from __future__ import annotations

import json
import shlex
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import cast

from livespec_runtime.hygiene_scan_context import git, quote_path, worktrees
from livespec_runtime.hygiene_scan_types import ScanContext
from livespec_runtime.hygiene_scan_worktrees import head_is_merged
from livespec_runtime.needs_attention import HygieneScanFinding

__all__: list[str] = [
    "GH_PR_FIELDS",
    "primary_health_findings",
    "stale_branch_findings",
    "stale_pr_findings",
]

GH_PR_FIELDS = "number,headRefName,updatedAt,title,url"


def primary_health_findings(*, context: ScanContext) -> list[HygieneScanFinding]:
    findings: list[HygieneScanFinding] = []
    primary = str(context.primary_path)
    status = git(
        repo_path=context.primary_path,
        argv=["status", "--porcelain"],
        runner=context.runner,
    )
    if status.returncode == 0 and status.stdout != "":
        findings.append(
            HygieneScanFinding(
                type="primary-dirty",
                resource=primary,
                path=primary,
                summary=f"Primary checkout {primary} has uncommitted changes.",
                command=f"git -C {quote_path(path=context.primary_path)} status --short",
                urgency="medium",
            )
        )
    branch_result = git(
        repo_path=context.primary_path,
        argv=["symbolic-ref", "--quiet", "--short", "HEAD"],
        runner=context.runner,
    )
    branch = branch_result.stdout.strip()
    if branch_result.returncode != 0:
        findings.append(primary_detached_finding(context=context))
    elif branch != context.default_branch:
        findings.append(primary_off_default_finding(context=context, branch=branch))
    return findings


def primary_detached_finding(*, context: ScanContext) -> HygieneScanFinding:
    primary = str(context.primary_path)
    return HygieneScanFinding(
        type="primary-detached",
        resource=primary,
        path=primary,
        summary=f"Primary checkout {primary} is detached instead of on {context.default_branch}.",
        command=(
            f"git -C {quote_path(path=context.primary_path)} "
            f"switch {shlex.quote(context.default_branch)}"
        ),
        urgency="medium",
    )


def primary_off_default_finding(*, context: ScanContext, branch: str) -> HygieneScanFinding:
    primary = str(context.primary_path)
    return HygieneScanFinding(
        type="primary-off-default",
        resource=primary,
        path=primary,
        summary=f"Primary checkout {primary} is on {branch}, expected {context.default_branch}.",
        command=(
            f"git -C {quote_path(path=context.primary_path)} "
            f"switch {shlex.quote(context.default_branch)}"
        ),
        urgency="medium",
    )


def stale_branch_findings(*, context: ScanContext) -> list[HygieneScanFinding]:
    worktree_branches = frozenset(
        worktree.branch for worktree in worktrees(context=context) if worktree.branch is not None
    )
    findings: list[HygieneScanFinding] = []
    result = git(
        repo_path=context.primary_path,
        argv=["for-each-ref", "--format=%(refname:short)%00%(objectname)", "refs/heads"],
        runner=context.runner,
    )
    if result.returncode != 0:
        return findings
    for branch, head in branch_rows(output=result.stdout):
        if branch == context.default_branch or branch in worktree_branches:
            continue
        if head_is_merged(context=context, head=head):
            findings.append(stale_branch_finding(context=context, branch=branch))
    return findings


def branch_rows(*, output: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in output.splitlines():
        branch, separator, head = line.partition("\x00")
        if separator != "" and branch != "" and head != "":
            rows.append((branch, head))
    return rows


def stale_branch_finding(*, context: ScanContext, branch: str) -> HygieneScanFinding:
    ref = f"refs/heads/{branch}"
    return HygieneScanFinding(
        type="stale-branch",
        resource=ref,
        path=f".git/refs/heads/{branch}",
        summary=f"Delete local branch {branch}; it is merged into {context.base_ref}.",
        command=f"git -C {quote_path(path=context.primary_path)} branch -d {shlex.quote(branch)}",
    )


def stale_pr_findings(*, context: ScanContext) -> list[HygieneScanFinding]:
    argv = ["pr", "list", "--state", "open", "--json", GH_PR_FIELDS]
    origin = git(
        repo_path=context.primary_path,
        argv=["config", "--get", "remote.origin.url"],
        runner=context.runner,
    ).stdout.strip()
    if origin != "":
        argv.extend(["--repo", origin])
    result = context.runner(argv=["gh", *argv], cwd=context.primary_path)
    if result.returncode != 0:
        return []
    try:
        payload: object = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    entries = cast(list[object], payload)
    return [finding for entry in entries for finding in pr_finding(context=context, entry=entry)]


def pr_finding(*, context: ScanContext, entry: object) -> tuple[HygieneScanFinding, ...]:
    if not isinstance(entry, dict):
        return ()
    entry_map = cast(Mapping[str, object], entry)
    number = entry_map.get("number")
    updated_at = entry_map.get("updatedAt")
    if not isinstance(number, int) or not isinstance(updated_at, str):
        return ()
    updated = parse_github_datetime(value=updated_at)
    if updated is None or context.now - updated <= context.stale_after:
        return ()
    title = entry_map.get("title")
    url = entry_map.get("url")
    head_ref = entry_map.get("headRefName")
    summary_title = title if isinstance(title, str) and title != "" else f"PR #{number}"
    branch = head_ref if isinstance(head_ref, str) and head_ref != "" else "unknown branch"
    path = url if isinstance(url, str) else ""
    return (
        HygieneScanFinding(
            type="stale-pr",
            resource=f"pr-{number}",
            path=path,
            summary=f"Open PR #{number} ({summary_title}) on {branch} has gone stale.",
            command=f"gh pr view {number} --web",
            urgency="medium",
        ),
    )


def parse_github_datetime(*, value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
