"""Tests for discussion read/write tools."""

from __future__ import annotations

import json

import httpx

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.models import DiscussionPosition
from gitlab_mcp.tools import discussions


def test_list_and_get_discussion(settings: Settings) -> None:
    """List and get discussion endpoints."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/discussions/d1"):
            return httpx.Response(200, json={"id": "d1"})
        return httpx.Response(200, json=[{"id": "d1"}])

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        listed = discussions.list_merge_request_discussions(client, 1, 2)
        assert listed["items"][0]["id"] == "d1"
        assert discussions.get_merge_request_discussion(client, 1, 2, "d1")["id"] == "d1"


def test_create_reply_resolve(settings: Settings) -> None:
    """Create, reply, and resolve discussion calls."""
    seen: list[tuple[str, str, dict]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode()) if request.content else {}
        seen.append((request.method, request.url.path, body))
        if request.method == "POST" and request.url.path.endswith("/notes"):
            return httpx.Response(200, json={"id": 3, "body": body.get("body")})
        if request.method == "PUT":
            return httpx.Response(200, json={"id": "d1", "resolved": True})
        return httpx.Response(200, json={"id": "d1", "notes": []})

    position = DiscussionPosition(
        base_sha="a",
        start_sha="b",
        head_sha="c",
        new_path="f.py",
        new_line=1,
    )
    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        created = discussions.create_merge_request_thread(
            client,
            1,
            2,
            "hello",
            position=position,
        )
        reply = discussions.reply_to_merge_request_thread(
            client,
            1,
            2,
            "d1",
            "reply",
        )
        resolved = discussions.set_merge_request_thread_resolved(
            client,
            1,
            2,
            "d1",
            resolved=True,
        )
    assert created["id"] == "d1"
    assert reply["body"] == "reply"
    assert resolved["resolved"] is True
    assert any("position" in item[2] for item in seen if item[0] == "POST")


def test_discussion_id_is_encoded(settings: Settings) -> None:
    """A discussion id cannot change the request path."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"id": "x"})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        discussions.get_merge_request_discussion(client, "group/proj", 2, "a/b?c")
    raw = seen[0]
    assert "a%2Fb%3Fc" in raw or "discussions/a%2Fb%3Fc" in raw
