#!/usr/bin/env python3
"""Optional live smoke against a real GitLab instance.

Requires ``GITLAB_URL`` and ``GITLAB_TOKEN``. Exercises every MCP tool
surface against ``GITLAB_DEFAULT_PROJECT`` (an open merge request).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import get_settings
from gitlab_mcp.errors import GitLabError
from gitlab_mcp.models import MergeRequestListFilters
from gitlab_mcp.tools import diffs, discussions, merge_requests, pipelines, writes


def _fail(name: str, exc: BaseException) -> dict[str, Any]:
    """Build a failed-tool result row.

    Args:
        name: Tool name.
        exc: Exception raised while exercising the tool.

    Returns:
        Result mapping with ``ok`` false.

    """
    return {"tool": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _ok(name: str, detail: str = "") -> dict[str, Any]:
    """Build a passed-tool result row.

    Args:
        name: Tool name.
        detail: Short success note.

    Returns:
        Result mapping with ``ok`` true.

    """
    row: dict[str, Any] = {"tool": name, "ok": True}
    if detail:
        row["detail"] = detail
    return row


def _exercise_reads(
    client: GitLabClient,
    project: str,
    iid: int,
) -> list[dict[str, Any]]:
    """Run every read tool against one merge request.

    Args:
        client: GitLab HTTP client.
        project: Project id or path.
        iid: Merge request IID.

    Returns:
        Result rows, one per tool.

    """
    rows: list[dict[str, Any]] = []

    def run(name: str, fn: Callable[[], Any]) -> Any:
        """Call ``fn`` and append a pass/fail row.

        Args:
            name: Tool name recorded in the result.
            fn: Zero-argument callable that hits GitLab.

        Returns:
            The callable's return value, or ``None`` on ``GitLabError``.

        """
        try:
            value = fn()
            extra = ""
            if isinstance(value, list):
                extra = f"count={len(value)}"
            elif isinstance(value, dict) and "iid" in value:
                extra = f"iid={value['iid']}"
            rows.append(_ok(name, extra))
            return value
        except GitLabError as exc:
            rows.append(_fail(name, exc))
            return None

    run(
        "list_merge_requests",
        lambda: merge_requests.list_merge_requests(
            client,
            project_id=project,
            filters=MergeRequestListFilters(state="opened"),
        ),
    )
    run(
        "search_merge_requests",
        lambda: merge_requests.search_merge_requests(
            client,
            "seed",
            project_id=project,
        ),
    )
    run(
        "get_merge_request",
        lambda: merge_requests.get_merge_request(client, project, iid),
    )
    run(
        "get_merge_request_diffs",
        lambda: diffs.get_merge_request_diffs(client, project, iid),
    )
    run(
        "list_merge_request_commits",
        lambda: diffs.list_merge_request_commits(client, project, iid),
    )
    versions = run(
        "list_merge_request_diff_versions",
        lambda: diffs.list_merge_request_diff_versions(client, project, iid),
    )
    if isinstance(versions, list) and versions:
        version_id = versions[0].get("id")
        if isinstance(version_id, int):
            run(
                "get_merge_request_diff_version",
                lambda: diffs.get_merge_request_diff_version(
                    client,
                    project,
                    iid,
                    version_id,
                ),
            )
        else:
            rows.append(_fail("get_merge_request_diff_version", ValueError("no version id")))
    else:
        rows.append(
            _fail(
                "get_merge_request_diff_version",
                ValueError("no diff versions returned"),
            ),
        )
    run(
        "list_merge_request_discussions",
        lambda: discussions.list_merge_request_discussions(client, project, iid),
    )
    run(
        "list_merge_request_pipelines",
        lambda: pipelines.list_merge_request_pipelines(client, project, iid),
    )
    run(
        "get_merge_request_approvals",
        lambda: pipelines.get_merge_request_approvals(client, project, iid),
    )
    run(
        "list_merge_request_participants",
        lambda: pipelines.list_merge_request_participants(client, project, iid),
    )
    run(
        "list_merge_request_reviewers",
        lambda: pipelines.list_merge_request_reviewers(client, project, iid),
    )
    return rows


def _exercise_writes(
    client: GitLabClient,
    project: str,
    iid: int,
    original_title: str,
    original_description: str | None,
) -> list[dict[str, Any]]:
    """Run write tools, then restore the original title and description.

    Args:
        client: GitLab HTTP client.
        project: Project id or path.
        iid: Merge request IID.
        original_title: Title to restore after the update probe.
        original_description: Description to restore after the update probe.

    Returns:
        Result rows, one per write tool.

    """
    rows: list[dict[str, Any]] = []
    discussion_id: str | None = None
    try:
        created = discussions.create_merge_request_thread(
            client,
            project,
            iid,
            body="gitlab-mcp live smoke thread",
        )
        discussion_id = created.get("id") if isinstance(created, dict) else None
        rows.append(_ok("create_merge_request_thread", f"id={discussion_id}"))
    except GitLabError as exc:
        rows.append(_fail("create_merge_request_thread", exc))

    if discussion_id:
        try:
            discussions.reply_to_merge_request_thread(
                client,
                project,
                iid,
                discussion_id,
                body="gitlab-mcp live smoke reply",
            )
            rows.append(_ok("reply_to_merge_request_thread"))
        except GitLabError as exc:
            rows.append(_fail("reply_to_merge_request_thread", exc))
        try:
            discussions.get_merge_request_discussion(
                client,
                project,
                iid,
                discussion_id,
            )
            rows.append(_ok("get_merge_request_discussion"))
        except GitLabError as exc:
            rows.append(_fail("get_merge_request_discussion", exc))
        try:
            discussions.set_merge_request_thread_resolved(
                client,
                project,
                iid,
                discussion_id,
                resolved=True,
            )
            rows.append(_ok("set_merge_request_thread_resolved"))
        except GitLabError as exc:
            rows.append(_fail("set_merge_request_thread_resolved", exc))
    else:
        rows.append(_fail("reply_to_merge_request_thread", ValueError("no discussion")))
        rows.append(_fail("get_merge_request_discussion", ValueError("no discussion")))
        rows.append(_fail("set_merge_request_thread_resolved", ValueError("no discussion")))

    try:
        writes.update_merge_request(
            client,
            project,
            iid,
            {"title": f"{original_title} [smoke]"},
        )
        writes.update_merge_request(
            client,
            project,
            iid,
            {
                "title": original_title,
                "description": original_description or "",
            },
        )
        rows.append(_ok("update_merge_request"))
    except GitLabError as exc:
        rows.append(_fail("update_merge_request", exc))
    return rows


def main() -> int:
    """Run a live API smoke test covering every MCP tool.

    Returns:
        Process exit code.

    """
    settings = get_settings()
    project = settings.gitlab_default_project
    if not project:
        print("GITLAB_DEFAULT_PROJECT is required", file=sys.stderr)
        return 2
    rows: list[dict[str, Any]] = []
    with GitLabClient(settings) as client:
        version = client.get("/version")
        rows.append(
            _ok(
                "version",
                f"{version.get('version') if isinstance(version, dict) else version}",
            ),
        )
        opened = merge_requests.list_merge_requests(
            client,
            project_id=project,
            filters=MergeRequestListFilters(state="opened"),
        )
        if not opened:
            print(json.dumps({"error": "no open merge requests", "project": project}, indent=2))
            return 1
        mr = opened[0]
        iid = int(mr["iid"])
        original_title = str(mr.get("title") or "")
        original_description = mr.get("description")
        if not isinstance(original_description, str):
            original_description = ""
        rows.extend(_exercise_reads(client, str(project), iid))
        rows.extend(
            _exercise_writes(
                client,
                str(project),
                iid,
                original_title,
                original_description,
            ),
        )
    failed = [row for row in rows if not row["ok"]]
    print(
        json.dumps(
            {"gitlab": rows[0].get("detail"), "results": rows, "failed": len(failed)},
            indent=2,
        ),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
