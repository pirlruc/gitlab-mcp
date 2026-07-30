"""Safe merge request update tool with a frozen field allowlist."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.models import FORBIDDEN_UPDATE_FIELDS, MergeRequestUpdateFields
from gitlab_mcp.tools.merge_requests import mr_base_path


def build_update_body(fields: dict[str, Any]) -> dict[str, Any]:
    """Validate and build an allowlisted update payload.

    Args:
        fields: Caller-supplied field mapping.

    Returns:
        Sanitized PUT body containing only allowlisted keys.

    Raises:
        ValueError: If forbidden fields are present or validation fails.

    """
    forbidden = FORBIDDEN_UPDATE_FIELDS.intersection(fields)
    if forbidden:
        names = ", ".join(sorted(forbidden))
        raise ValueError(f"Forbidden update fields: {names}")
    try:
        model = MergeRequestUpdateFields.model_validate(fields)
    except ValidationError as exc:
        raise ValueError(f"Invalid update fields: {exc}") from exc
    body = model.as_body()
    leaked = FORBIDDEN_UPDATE_FIELDS.intersection(body)
    if leaked:
        raise ValueError(f"Internal allowlist violation: {', '.join(sorted(leaked))}")
    return body


def update_merge_request(
    client: GitLabClient,
    project_id: str | int,
    merge_request_iid: int,
    fields: dict[str, Any],
) -> Any:
    """Update allowlisted merge request fields.

    Args:
        client: GitLab HTTP client.
        project_id: Project id or path.
        merge_request_iid: Merge request IID.
        fields: Mapping of fields to update (allowlisted only).

    Returns:
        Updated merge request object.

    Raises:
        ValueError: If forbidden or invalid fields are supplied.

    """
    body = build_update_body(fields)
    if not body:
        raise ValueError("No updatable fields provided")
    path = mr_base_path(project_id, merge_request_iid)
    return client.put(path, json=body)
