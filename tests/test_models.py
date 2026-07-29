"""Tests for Pydantic filter and update models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gitlab_mcp.models import (
    FORBIDDEN_UPDATE_FIELDS,
    DiscussionPosition,
    MergeRequestListFilters,
    MergeRequestUpdateFields,
)


def test_filters_exclude_none_and_use_alias() -> None:
    """as_params drops Nones and emits the ``in`` alias."""
    filters = MergeRequestListFilters(state="opened", search="foo", search_in="title")
    params = filters.as_params()
    assert params == {"state": "opened", "search": "foo", "in": "title"}
    assert "author_username" not in params


def test_update_fields_forbid_extra() -> None:
    """Extra fields are rejected by the update model."""
    with pytest.raises(ValidationError):
        MergeRequestUpdateFields.model_validate({"state_event": "close"})


def test_forbidden_set_covers_state_event() -> None:
    """state_event is in the forbidden set."""
    assert "state_event" in FORBIDDEN_UPDATE_FIELDS
    assert "target_branch" in FORBIDDEN_UPDATE_FIELDS


def test_position_as_body() -> None:
    """Position dump omits unset optional fields."""
    position = DiscussionPosition(
        base_sha="a",
        start_sha="b",
        head_sha="c",
        new_path="file.py",
        new_line=10,
    )
    body = position.as_body()
    assert body["base_sha"] == "a"
    assert body["new_line"] == 10
    assert "old_line" not in body
