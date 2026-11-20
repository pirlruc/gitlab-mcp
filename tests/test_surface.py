"""Coverage for the added toolsets, URL guard, and pagination edges."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import httpx
import pytest

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.server import create_server
from gitlab_mcp.tools.scope import enabled_toolsets
from gitlab_mcp.tools.urls import parse_merge_request_url


def test_toolset_names() -> None:
    """All expands, and an unknown name fails."""
    assert "core" in enabled_toolsets("all")
    assert enabled_toolsets("wiki,core") == {"wiki", "core"}
    with pytest.raises(ValueError, match="unknown"):
        enabled_toolsets("duo")


def test_merge_request_url_must_match_host() -> None:
    """A URL on another host is rejected."""
    project, iid = parse_merge_request_url(
        "https://gitlab.example.com",
        "https://gitlab.example.com/group/proj/-/merge_requests/4",
    )
    assert project == "group/proj"
    assert iid == 4
    with pytest.raises(ValueError, match="host"):
        parse_merge_request_url(
            "https://gitlab.example.com",
            "https://evil.example/group/proj/-/merge_requests/4",
        )


def test_toolsets_hide_unselected_tools(settings: Settings) -> None:
    """GITLAB_TOOLSETS limits registration."""
    settings.gitlab_toolsets = "wiki"
    server = create_server(settings, client=GitLabClient(settings, transport=_transport()))
    names = {tool.name for tool in asyncio.run(server.list_tools())}
    assert "list_wiki_pages" in names
    assert "get_project" not in names
    assert "update_merge_request" not in names


def test_surface_tools(settings: Settings) -> None:
    """Each added tool reaches the client."""
    settings.gitlab_read_only = False
    client = GitLabClient(settings, transport=_transport())
    server = create_server(settings, client=client)
    calls: dict[str, dict[str, Any]] = {
        "get_mcp_server_version": {},
        "get_project": {},
        "list_projects": {"search": "a", "membership": True},
        "get_group": {"group_id": "g"},
        "list_groups": {"search": "g"},
        "get_user": {"user_id": 3},
        "list_project_members": {},
        "list_milestones": {"state": "active"},
        "list_todos": {"state": "pending"},
        "list_user_events": {"user_id": 3},
        "list_branches": {"search": "main"},
        "get_repository_file": {"file_path": "a.py", "ref": "main"},
        "list_repository_tree": {"path": "src", "ref": "main"},
        "get_commit": {"sha": "abc"},
        "list_commits": {"ref_name": "main"},
        "list_tags": {},
        "list_releases": {},
        "list_pipelines": {"ref": "main"},
        "get_pipeline": {"pipeline_id": 1},
        "get_pipeline_jobs": {"pipeline_id": 1},
        "get_job": {"job_id": 1, "include_log": True},
        "get_artifact_file": {"job_id": 1, "artifact_path": "out.txt"},
        "list_pipeline_schedules": {},
        "manage_pipeline": {"pipeline_id": 1, "action": "retry"},
        "get_issue": {"issue_iid": 1},
        "create_issue": {"title": "t", "description": "d", "labels": "bug"},
        "get_work_item": {"work_item_iid": 1},
        "list_work_items": {},
        "get_workitem_notes": {"work_item_iid": 1},
        "list_work_item_saved_views": {},
        "get_saved_view_work_items": {"view_id": 2},
        "create_work_item_note": {"work_item_iid": 1, "body": "n"},
        "link_work_items": {"work_item_iid": 1, "target_work_item_iid": 2},
        "search": {"scope": "issues", "query": "q", "project_id": "group/project"},
        "search_labels": {"query": "bug", "group_id": "g"},
        "list_wiki_pages": {"group_id": "g"},
        "create_merge_request": {
            "source_branch": "a",
            "target_branch": "main",
            "title": "t",
        },
        "get_merge_request_notes": {"merge_request_iid": 1},
        "get_merge_request_conflicts": {"merge_request_iid": 1},
        "get_merge_request_commits": {"merge_request_iid": 1},
        "get_merge_request_pipelines": {"merge_request_iid": 1},
    }

    async def run() -> None:
        version = cast(Any, await server.call_tool("get_mcp_server_version", {}))
        assert version.structured_content["version"] == "0.2.0"
        for name, arguments in calls.items():
            if name == "get_mcp_server_version":
                continue
            result = cast(Any, await server.call_tool(name, arguments))
            assert result.is_error is False, name

    asyncio.run(run())


def test_surface_rejections(settings: Settings) -> None:
    """Invalid actions and scopes fail before a confusing API call."""
    settings.gitlab_read_only = False
    client = GitLabClient(settings, transport=_transport())
    server = create_server(settings, client=client)

    async def run() -> None:
        with pytest.raises(Exception, match="manage_pipeline"):
            await server.call_tool(
                "manage_pipeline",
                {"pipeline_id": 1, "action": "delete"},
            )
        with pytest.raises(Exception, match="search"):
            await server.call_tool(
                "search",
                {"scope": "issues", "query": "q", "project_id": "p", "group_id": "g"},
            )
        with pytest.raises(Exception, match="search_labels"):
            await server.call_tool("search_labels", {"query": "q"})
        url = await server.call_tool(
            "get_merge_request",
            {"url": "https://gitlab.example.com/group/project/-/merge_requests/9"},
        )
        assert cast(Any, url).is_error is False
        include = await server.call_tool(
            "get_merge_request",
            {"merge_request_iid": 9, "include": "notes,conflicts"},
        )
        assert cast(Any, include).is_error is False

    asyncio.run(run())


def test_graphql_errors(settings: Settings) -> None:
    """GraphQL errors become GitLabError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "no"}]})

    client = GitLabClient(settings, transport=httpx.MockTransport(handler))
    with pytest.raises(Exception, match="no"):
        client.graphql("query { x }")

    def ok(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"x": 1}})

    client_ok = GitLabClient(settings, transport=httpx.MockTransport(ok))
    assert client_ok.graphql("query { x }", {"a": 1}) == {"x": 1}


def test_direct_edges(settings: Settings) -> None:
    """Cover validation branches that the happy path skips."""
    from gitlab_mcp.tools import merge_requests, writes

    client = GitLabClient(settings, transport=_transport())
    with pytest.raises(ValueError, match="unknown include"):
        merge_requests.get_merge_request(client, 1, 9, include="nope")
    merged = merge_requests.get_merge_request(client, 1, 9, include="conflicts")
    assert "include" in merged
    created = writes.create_merge_request(
        client,
        1,
        source_branch="a",
        target_branch="b",
        title="t",
        description="d",
        labels="bug",
    )
    assert created["id"] == 1
    with pytest.raises(ValueError, match="http"):
        parse_merge_request_url("https://gitlab.example.com", "ftp://gitlab.example.com/x")
    with pytest.raises(ValueError, match="not a merge request"):
        parse_merge_request_url(
            "https://gitlab.example.com", "https://gitlab.example.com/group/proj"
        )

    def odd(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["nope"])

    odd_client = GitLabClient(settings, transport=httpx.MockTransport(odd))
    with pytest.raises(Exception, match="not an object"):
        odd_client.graphql("query { x }")

    settings.gitlab_read_only = False
    server = create_server(settings, client=client)

    async def more() -> None:
        user = cast(Any, await server.call_tool("get_user", {}))
        events = cast(Any, await server.call_tool("list_user_events", {}))
        projects = cast(Any, await server.call_tool("list_projects", {}))
        found = cast(Any, await server.call_tool("search", {"scope": "commits", "query": "q"}))
        pages = cast(Any, await server.call_tool("list_wiki_pages", {}))
        assert user.is_error is False
        assert events.is_error is False
        assert projects.is_error is False
        assert found.is_error is False
        assert pages.is_error is False
        with pytest.raises(Exception, match="list_wiki_pages"):
            await server.call_tool(
                "list_wiki_pages",
                {"project_id": "p", "group_id": "g"},
            )
        with pytest.raises(Exception, match="get_merge_request"):
            await server.call_tool("get_merge_request", {})

    asyncio.run(more())

    bare = Settings(gitlab_url="https://gitlab.example.com", gitlab_token="t")
    with pytest.raises(ValueError, match="project_id"):
        from gitlab_mcp.tools.surface import _project

        _project(bare, None)


def _transport() -> httpx.MockTransport:
    """Return a transport that accepts every path.

    Returns:
        Mock transport.

    """

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/trace") or "/artifacts/" in path:
            return httpx.Response(200, content=b"log-line")
        if request.method == "GET" and path.endswith("/merge_requests/9"):
            return httpx.Response(200, json={"iid": 9})
        if request.method == "GET":
            return httpx.Response(200, json=[{"id": 1}])
        return httpx.Response(200, json={"id": 1})

    return httpx.MockTransport(handler)
