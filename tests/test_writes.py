"""Tests for allowlisted merge request updates."""

from __future__ import annotations

import json

import httpx
import pytest

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.tools import writes


def test_build_update_body_allowlist() -> None:
    """Allowlisted fields survive; empty body is possible only via caller."""
    body = writes.build_update_body({"title": "New", "description": "D"})
    assert body == {"title": "New", "description": "D"}


def test_build_update_body_rejects_state_event() -> None:
    """state_event cannot enter the payload."""
    with pytest.raises(ValueError, match="Forbidden"):
        writes.build_update_body({"state_event": "close", "title": "x"})


def test_build_update_body_rejects_target_branch() -> None:
    """target_branch is forbidden."""
    with pytest.raises(ValueError, match="target_branch"):
        writes.build_update_body({"target_branch": "main"})


def test_update_merge_request_sends_only_allowlisted(settings: Settings) -> None:
    """PUT body never contains forbidden keys."""
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json={"iid": 1, **captured["body"]})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        result = writes.update_merge_request(
            client,
            1,
            1,
            {"title": "T", "labels": "bug"},
        )
    assert result["title"] == "T"
    assert "state_event" not in captured["body"]
    assert set(captured["body"]) <= {
        "title",
        "description",
        "labels",
        "add_labels",
        "remove_labels",
        "milestone_id",
    }


def test_build_update_invalid_type() -> None:
    """Invalid field types raise ValueError."""
    with pytest.raises(ValueError, match="Invalid"):
        writes.build_update_body({"milestone_id": "not-an-int"})


def test_update_requires_fields(settings: Settings) -> None:
    """Empty field map raises."""
    with (
        GitLabClient(
            settings,
            transport=httpx.MockTransport(lambda _r: httpx.Response(200)),
        ) as client,
        pytest.raises(ValueError, match="No updatable"),
    ):
        writes.update_merge_request(client, 1, 1, {})


def test_create_thread_without_position(settings: Settings) -> None:
    """Discussion create works without a position."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert "position" not in body
        return httpx.Response(200, json={"id": "d0"})

    from gitlab_mcp.tools import discussions

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        result = discussions.create_merge_request_thread(client, 1, 2, "plain")
    assert result["id"] == "d0"
