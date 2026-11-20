"""Merge request list, search, and get tools."""

from __future__ import annotations

from typing import Any

from gitlab_mcp.client import GitLabClient, encode_path_segment
from gitlab_mcp.models import MergeRequestListFilters


def search_collection_path(
    project_id: str | int | None,
    group_id: str | int | None,
) -> str:
    """Resolve a search collection for project, group, or instance scope.

    Args:
        project_id: Optional project scope.
        group_id: Optional group scope.

    Returns:
        Relative search path.

    Raises:
        ValueError: If both project and group are provided.

    """
    if project_id is not None and group_id is not None:
        raise ValueError("Provide at most one of project_id or group_id")
    if project_id is not None:
        return f"/projects/{encode_path_segment(project_id)}/search"
    if group_id is not None:
        return f"/groups/{encode_path_segment(group_id)}/search"
    return "/search"


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
) -> Any:
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
) -> Any:
    """Search merge requests via the GitLab Search API.

    Args:
        client: GitLab HTTP client.
        query: Search query string.
        project_id: Optional project scope.
        group_id: Optional group scope.

    Returns:
        List of matching merge request search results.

    """
    params = {"scope": "merge_requests", "search": query}
    path = search_collection_path(project_id, group_id)
    return client.paginate(path, params=params)


_FACETS = ("diffs", "commits", "notes", "pipelines", "conflicts")


def get_merge_request(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    *,
    include: str | None = None,
) -> Any:
    """Fetch a single merge request by project and IID.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID within the project.
        include: Comma-separated facets (diffs, commits, notes, pipelines, conflicts).

    Returns:
        Merge request object, or that object plus an ``include`` map.

    Raises:
        ValueError: When ``include`` names an unknown facet.

    """
    path = mr_base_path(project_id, merge_request_iid)
    body = client.get(path)
    facets = _facets(include)
    if not facets:
        return body
    attached = {name: _facet(client, path, name) for name in facets}
    return {"merge_request": body, "include": attached}


def _facets(include: str | None) -> list[str]:
    """Parse and validate include facet names.

    Args:
        include: Comma-separated facet names.

    Returns:
        Facet names, possibly empty.

    Raises:
        ValueError: When a name is not a known facet.

    """
    names = [name.strip() for name in (include or "").split(",") if name.strip()]
    unknown = [name for name in names if name not in _FACETS]
    if unknown:
        raise ValueError(f"unknown include facet: {', '.join(unknown)}")
    return names


def _facet(client: GitLabClient, path: str, name: str) -> Any:
    """Load one merge-request include facet.

    Args:
        client: GitLab HTTP client.
        path: Merge request base path.
        name: Facet name.

    Returns:
        Facet payload.

    """
    if name == "conflicts":
        return client.get(f"{path}/conflicts")
    if name == "notes":
        return client.paginate(f"{path}/notes")
    return client.paginate(f"{path}/{name}")


def mr_base_path(project_id: str | int, merge_request_iid: int) -> str:
    """Build the base path for a merge request sub-resource.

    Args:
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        Relative API path ending at the merge request resource.

    """
    return f"/projects/{encode_path_segment(project_id)}/merge_requests/{merge_request_iid}"
