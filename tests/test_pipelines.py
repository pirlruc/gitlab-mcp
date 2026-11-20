"""Tests for pipeline, approval, participant, and reviewer tools."""

from __future__ import annotations

import httpx

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.tools import pipelines


def test_pipelines_participants_reviewers(settings: Settings) -> None:
    """Pipeline and user listing endpoints."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/pipelines"):
            return httpx.Response(200, json=[{"id": 10, "status": "success"}])
        if request.url.path.endswith("/participants"):
            return httpx.Response(200, json=[{"username": "alice"}])
        if request.url.path.endswith("/reviewers"):
            return httpx.Response(200, json=[{"user": {"username": "bob"}}])
        return httpx.Response(404)

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        assert pipelines.list_merge_request_pipelines(client, 1, 2)["items"][0]["id"] == 10
        assert pipelines.list_merge_request_participants(client, 1, 2)[0]["username"] == "alice"
        assert pipelines.list_merge_request_reviewers(client, 1, 2)[0]["user"]["username"] == "bob"


def test_approvals_free_tier_note(settings: Settings) -> None:
    """Approvals without Premium fields get a tier_note."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"approved_by": [{"user": {"id": 1}}]})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        data = pipelines.get_merge_request_approvals(client, 1, 2)
    assert "tier_note" in data
    assert data["approved_by"]


def test_approvals_unavailable(settings: Settings) -> None:
    """Forbidden approvals degrade to an explanatory payload."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": "forbidden"})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        data = pipelines.get_merge_request_approvals(client, 1, 2)
    assert data["approvals_available"] is False
    assert "tier_note" in data
