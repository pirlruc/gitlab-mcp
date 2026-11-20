"""Diff, commit, and diff-version read tools."""

from __future__ import annotations

from typing import Any

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.tools.merge_requests import mr_base_path


def get_merge_request_diffs(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> Any:
    """List file diffs for a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of diff objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/diffs"
    return client.paginate(path)


def list_merge_request_commits(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> Any:
    """List commits on a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of commit objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/commits"
    return client.paginate(path)


def list_merge_request_diff_versions(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> Any:
    """List diff versions (pushes) for a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of version summary objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/versions"
    return client.paginate(path)


def get_merge_request_diff_version(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    version_id: int,
) -> Any:
    """Fetch a single diff version by id.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.
        version_id: Diff version id.

    Returns:
        Diff version object including diffs.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/versions/{version_id}"
    return client.get(path)
