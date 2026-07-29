"""Integration-style tests that exercise registered MCP tools."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.server import create_server, main


def _transport() -> httpx.MockTransport:
    """Build a transport covering common MR endpoints.

    Returns:
        Mock transport.

    """

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/merge_requests") and request.method == "GET":
            return httpx.Response(200, json=[{"iid": 1}])
        if "/search" in path:
            return httpx.Response(200, json=[{"iid": 2}])
        if path.endswith("/merge_requests/1") and request.method == "GET":
            return httpx.Response(200, json={"iid": 1, "title": "t"})
        if path.endswith("/diffs"):
            return httpx.Response(200, json=[{"old_path": "a.py"}])
        if path.endswith("/commits"):
            return httpx.Response(200, json=[{"id": "abc"}])
        if path.endswith("/versions"):
            return httpx.Response(200, json=[{"id": 9}])
        if path.endswith("/versions/9"):
            return httpx.Response(200, json={"id": 9})
        if path.endswith("/discussions") and request.method == "GET":
            return httpx.Response(200, json=[{"id": "d1"}])
        if path.endswith("/discussions/d1") and request.method == "GET":
            return httpx.Response(200, json={"id": "d1"})
        if path.endswith("/discussions") and request.method == "POST":
            return httpx.Response(200, json={"id": "d2"})
        if path.endswith("/notes") and request.method == "POST":
            body = json.loads(request.content.decode())
            return httpx.Response(200, json={"body": body["body"]})
        if path.endswith("/discussions/d1") and request.method == "PUT":
            return httpx.Response(200, json={"id": "d1", "resolved": True})
        if path.endswith("/pipelines"):
            return httpx.Response(200, json=[{"id": 10}])
        if path.endswith("/approvals"):
            return httpx.Response(
                200,
                json={"approved_by": [], "approval_rules_left": []},
            )
        if path.endswith("/participants"):
            return httpx.Response(200, json=[])
        if path.endswith("/reviewers"):
            return httpx.Response(200, json=[])
        if path.endswith("/merge_requests/1") and request.method == "PUT":
            body = json.loads(request.content.decode())
            return httpx.Response(200, json={"iid": 1, **body})
        return httpx.Response(404, json={"message": path})

    return httpx.MockTransport(handler)


async def _call(server: Any, name: str, arguments: dict[str, Any]) -> Any:
    """Call a tool and return unstructured content / structured result.

    Args:
        server: MCP server.
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        CallToolResult from the server.

    """
    return await server.call_tool(name, arguments)


def test_registered_tools_end_to_end(settings: Settings) -> None:
    """Exercise read and write tools through the MCP server facade."""
    client = GitLabClient(settings, transport=_transport())
    settings.gitlab_read_only = False
    server = create_server(settings, client=client)

    async def run() -> None:
        listed = await _call(server, "list_merge_requests", {"state": "opened"})
        assert listed is not None
        await _call(server, "search_merge_requests", {"query": "x"})
        await _call(server, "get_merge_request", {"merge_request_iid": 1})
        await _call(server, "get_merge_request_diffs", {"merge_request_iid": 1})
        await _call(server, "list_merge_request_commits", {"merge_request_iid": 1})
        await _call(server, "list_merge_request_diff_versions", {"merge_request_iid": 1})
        await _call(
            server,
            "get_merge_request_diff_version",
            {"merge_request_iid": 1, "version_id": 9},
        )
        await _call(server, "list_merge_request_discussions", {"merge_request_iid": 1})
        await _call(
            server,
            "get_merge_request_discussion",
            {"merge_request_iid": 1, "discussion_id": "d1"},
        )
        await _call(server, "list_merge_request_pipelines", {"merge_request_iid": 1})
        await _call(server, "get_merge_request_approvals", {"merge_request_iid": 1})
        await _call(server, "list_merge_request_participants", {"merge_request_iid": 1})
        await _call(server, "list_merge_request_reviewers", {"merge_request_iid": 1})
        await _call(
            server,
            "create_merge_request_thread",
            {
                "merge_request_iid": 1,
                "body": "hi",
                "base_sha": "a",
                "start_sha": "b",
                "head_sha": "c",
                "new_path": "f.py",
                "new_line": 1,
            },
        )
        await _call(
            server,
            "reply_to_merge_request_thread",
            {"merge_request_iid": 1, "discussion_id": "d1", "body": "r"},
        )
        await _call(
            server,
            "set_merge_request_thread_resolved",
            {"merge_request_iid": 1, "discussion_id": "d1", "resolved": True},
        )
        await _call(
            server,
            "update_merge_request",
            {"merge_request_iid": 1, "title": "New"},
        )

    asyncio.run(run())


def test_main_is_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() constructs a server and calls run(stdio)."""
    calls: list[str] = []

    class FakeServer:
        def run(self, transport: str = "stdio") -> None:
            calls.append(transport)

    monkeypatch.setattr(
        "gitlab_mcp.server.create_server",
        lambda: FakeServer(),
    )
    monkeypatch.setenv("GITLAB_URL", "https://g.example")
    monkeypatch.setenv("GITLAB_TOKEN", "t")
    main()
    assert calls == ["stdio"]
