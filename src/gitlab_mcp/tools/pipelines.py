"""Pipeline, approval, participant, and reviewer read tools."""

from __future__ import annotations

from typing import Any

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.errors import GitLabClientError, GitLabForbiddenError, GitLabNotFoundError
from gitlab_mcp.tools.merge_requests import mr_base_path


def list_merge_request_pipelines(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> list[Any]:
    """List pipelines for a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of pipeline objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/pipelines"
    return client.paginate(path)


def get_merge_request_approvals(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> Any:
    """Fetch approval state for a merge request.

    On Free tier, rule-based ``approval_state`` may be unavailable. This
    function degrades to the ``/approvals`` payload and annotates the result
    rather than raising when Premium-only fields are missing.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        Approvals object, possibly with a ``tier_note`` explaining Free limits.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/approvals"
    try:
        data = client.get(path)
    except (GitLabForbiddenError, GitLabNotFoundError, GitLabClientError) as exc:
        return {
            "approved_by": [],
            "approvals_available": False,
            "tier_note": (f"Approvals endpoint unavailable on this instance/tier: {exc.message}"),
        }
    if isinstance(data, dict) and "approval_rules_left" not in data:
        data = {
            **data,
            "tier_note": (
                "Rule-based approval_state is Premium/Ultimate; "
                "returning Free-tier approved_by data."
            ),
        }
    return data


def list_merge_request_participants(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> list[Any]:
    """List participants on a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of user objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/participants"
    result = client.get(path)
    return result if isinstance(result, list) else []


def list_merge_request_reviewers(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
) -> list[Any]:
    """List reviewers on a merge request.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.

    Returns:
        List of reviewer objects.

    """
    path = f"{mr_base_path(project_id, merge_request_iid)}/reviewers"
    result = client.get(path)
    return result if isinstance(result, list) else []
