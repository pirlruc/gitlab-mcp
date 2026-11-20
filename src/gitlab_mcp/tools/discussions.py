"""Discussion (thread) read and write tools."""

from __future__ import annotations

from typing import Any

from gitlab_mcp.client import GitLabClient, encode_path_segment
from gitlab_mcp.models import DiscussionPosition
from gitlab_mcp.tools.merge_requests import mr_base_path


def list_merge_request_discussions(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> Any:
    """List discussion threads on a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of discussion objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/discussions"
    return client.paginate(path)


def get_merge_request_discussion(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    discussion_id: str,
) -> Any:
    """Fetch a single discussion thread.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.
        discussion_id: Discussion id.

    Returns:
        Discussion object.

    """
    encoded = encode_path_segment(discussion_id)
    path = f"{mr_base_path(project_id, merge_request_iid)}/discussions/{encoded}"
    return client.get(path)


def create_merge_request_thread(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    body: str,
    *,
    position: DiscussionPosition | None = None,
) -> Any:
    """Create a new discussion thread on a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.
        body: Note body markdown.
        position: Optional diff-line position for an inline comment.

    Returns:
        Created discussion object.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/discussions"
    payload: dict[str, Any] = {"body": body}
    if position is not None:
        payload["position"] = position.as_body()
    return client.post(path, json=payload)


def reply_to_merge_request_thread(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    discussion_id: str,
    body: str,
) -> Any:
    """Reply to an existing discussion thread.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.
        discussion_id: Discussion id.
        body: Reply note body markdown.

    Returns:
        Created note object.

    """
    encoded = encode_path_segment(discussion_id)
    path = f"{mr_base_path(project_id, merge_request_iid)}/discussions/{encoded}/notes"
    return client.post(path, json={"body": body})


def set_merge_request_thread_resolved(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    discussion_id: str,
    *,
    resolved: bool,
) -> Any:
    """Resolve or unresolve a discussion thread.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.
        discussion_id: Discussion id.
        resolved: True to resolve, False to unresolve.

    Returns:
        Updated discussion object.

    """
    encoded = encode_path_segment(discussion_id)
    path = f"{mr_base_path(project_id, merge_request_iid)}/discussions/{encoded}"
    return client.put(path, params={"resolved": resolved})
