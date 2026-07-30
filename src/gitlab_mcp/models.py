"""Pydantic models for merge request filters and write payloads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MergeRequestListFilters(BaseModel):
    """Optional filters for listing merge requests.

    Fields map 1:1 to GitLab list query parameters. ``None`` values are
    excluded from the query string via :meth:`as_params`.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    state: Literal["opened", "closed", "locked", "merged", "all"] | None = None
    scope: Literal["created_by_me", "assigned_to_me", "reviews_for_me", "all"] | None = None
    author_username: str | None = None
    assignee_id: int | Literal["None", "Any"] | None = None
    reviewer_username: str | None = None
    labels: str | None = Field(default=None, description="Comma-separated label names")
    milestone: str | None = None
    source_branch: str | None = None
    target_branch: str | None = None
    created_after: str | None = None
    created_before: str | None = None
    updated_after: str | None = None
    updated_before: str | None = None
    order_by: Literal["created_at", "updated_at", "title", "merged_at"] | None = None
    sort: Literal["asc", "desc"] | None = None
    search: str | None = None
    search_in: str | None = Field(
        default=None,
        alias="in",
        description="Comma-separated fields to search (title, description)",
    )

    def as_params(self) -> dict[str, Any]:
        """Dump filters as GitLab query parameters.

        Returns:
            Dict with ``None`` values removed; uses API field aliases.

        """
        return self.model_dump(by_alias=True, exclude_none=True)


class MergeRequestUpdateFields(BaseModel):
    """Allowlisted fields for updating a merge request.

    Anything outside this model is rejected by Pydantic ``extra='forbid'``
    before a request body is built, so ``state_event`` cannot be smuggled.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    labels: str | None = None
    add_labels: str | None = None
    remove_labels: str | None = None
    milestone_id: int | None = None

    def as_body(self) -> dict[str, Any]:
        """Dump allowlisted fields as a PUT body.

        Returns:
            Dict with ``None`` values removed.

        """
        return self.model_dump(exclude_none=True)


class DiscussionPosition(BaseModel):
    """Diff-line position for creating a discussion on a merge request."""

    model_config = ConfigDict(extra="forbid")

    base_sha: str
    start_sha: str
    head_sha: str
    position_type: Literal["text", "image", "file"] = "text"
    old_path: str | None = None
    new_path: str | None = None
    old_line: int | None = None
    new_line: int | None = None
    line_range: dict[str, Any] | None = None

    def as_body(self) -> dict[str, Any]:
        """Dump the position as a GitLab discussion ``position`` object.

        Returns:
            Dict with ``None`` values removed.

        """
        return self.model_dump(exclude_none=True)


# Fields that must never appear in an update payload.
FORBIDDEN_UPDATE_FIELDS: frozenset[str] = frozenset(
    {
        "state_event",
        "target_branch",
        "remove_source_branch",
        "squash",
        "merge_commit_message",
        "squash_commit_message",
        "should_remove_source_branch",
        "merge_when_pipeline_succeeds",
        "sha",
        "merge_status",
        "assignee_id",
        "assignee_ids",
        "reviewer_ids",
        "discussion_locked",
    },
)
