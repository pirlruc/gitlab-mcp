"""Merge request list, search, and get tools."""

from __future__ import annotations

from typing import Any

from gitlab_mcp.client import GitLabClient, encode_path_segment
from gitlab_mcp.models import MergeRequestListFilters


def _mr_collection_path(
    project_id: str | int | None,
    group_id: str | int | None,
) -> str:
    """Resolve the list endpoint for project, group, or instance scope.

    Args:
        project_id: Project id or path, if scoping to a project.
        group_id: Group id or path, if scoping to a group.

    Returns:
        Relative API path for the merge request collection.

    Raises:
        ValueError: If both project and group are provided.

    """
    if project_id is not None and group_id is not None:
        raise ValueError("Provide at most one of project_id or group_id")
    if project_id is not None:
        return f"/projects/{encode_path_segment(project_id)}/merge_requests"
    if group_id is not None:
        return f"/groups/{encode_path_segment(group_id)}/merge_requests"
    return "/merge_requests"


def list_merge_requests(
    client: GitLabClient,
    *,
    project_id: str | int | None = None,
    group_id: str | int | None = None,
    filters: MergeRequestListFilters | None = None,
) -> list[Any]:
    """List merge requests with optional filters.

    Args:
        client: GitLab HTTP client.
        project_id: Optional project scope.
        group_id: Optional group scope.
        filters: Optional list filters.

    Returns:
        List of merge request objects.

    """
    path = _mr_collection_path(project_id, group_id)
    params = filters.as_params() if filters is not None else {}
    return client.paginate(path, params=params)


def search_merge_requests(
    client: GitLabClient,
    query: str,
    *,
    project_id: str | int | None = None,
    group_id: str | int | None = None,
) -> list[Any]:
    """Search merge requests via the GitLab Search API.

    Args:
        client: GitLab HTTP client.
        query: Search query string.
        project_id: Optional project scope.
        group_id: Optional group scope.

    Returns:
        List of matching merge request search results.

    Raises:
        ValueError: If both project and group are provided.

    """
    if project_id is not None and group_id is not None:
        raise ValueError("Provide at most one of project_id or group_id")
    params = {"scope": "merge_requests", "search": query}
    if project_id is not None:
        path = f"/projects/{encode_path_segment(project_id)}/search"
    elif group_id is not None:
        path = f"/groups/{encode_path_segment(group_id)}/search"
    else:
        path = "/search"
    return client.paginate(path, params=params)


def get_merge_request(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> Any:
    """Fetch a single merge request by project and IID.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID within the project.

    Returns:
        Merge request object.

    """
    path = f"/projects/{encode_path_segment(project_id)}/merge_requests/{merge_request_iid}"
    return client.get(path)


def mr_base_path(project_id: str | int, merge_request_iid: int) -> str:
    """Build the base path for a merge request sub-resource.

    Args:
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        Relative API path ending at the merge request resource.

    """
    return f"/projects/{encode_path_segment(project_id)}/merge_requests/{merge_request_iid}"
