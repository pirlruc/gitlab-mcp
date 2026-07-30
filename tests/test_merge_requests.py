"""Tests for merge request list/search/get helpers."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.models import MergeRequestListFilters
from gitlab_mcp.tools import merge_requests


def _client(
    settings: Settings,
    path_suffix: str,
    payload: Any,
) -> GitLabClient:
    """Build a client that answers one path with ``payload``.

    Args:
        settings: Test settings.
        path_suffix: Expected URL path under /api/v4.
        payload: JSON body to return.

    Returns:
        Configured client.

    """

    def handler(request: httpx.Request) -> httpx.Response:
        # httpx decodes %2F in URL.path; match against the raw URL string.
        assert path_suffix.replace("%2F", "/") in str(request.url) or path_suffix in str(
            request.url,
        )
        return httpx.Response(200, json=payload)

    return GitLabClient(settings, transport=httpx.MockTransport(handler))


def test_list_project_scope(settings: Settings) -> None:
    """Project-scoped list hits /projects/.../merge_requests."""
    client = _client(
        settings,
        "/projects/group%2Fproject/merge_requests",
        [{"iid": 1}],
    )
    filters = MergeRequestListFilters(state="opened")
    items = merge_requests.list_merge_requests(
        client,
        project_id="group/project",
        filters=filters,
    )
    assert items[0]["iid"] == 1


def test_list_rejects_both_scopes(settings: Settings) -> None:
    """Providing project and group together raises."""
    client = _client(settings, "/merge_requests", [])
    with pytest.raises(ValueError, match="at most one"):
        merge_requests.list_merge_requests(
            client,
            project_id="p",
            group_id="g",
        )


def test_search_instance_scope(settings: Settings) -> None:
    """Instance search hits /search with merge_requests scope."""
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json=[{"iid": 2}])

    client = GitLabClient(settings, transport=httpx.MockTransport(handler))
    items = merge_requests.search_merge_requests(client, "login")
    assert items[0]["iid"] == 2
    assert seen["scope"] == "merge_requests"
    assert seen["search"] == "login"


def test_get_merge_request(settings: Settings) -> None:
    """get_merge_request returns the object body."""
    client = _client(
        settings,
        "/projects/1/merge_requests/7",
        {"iid": 7, "title": "t"},
    )
    result = merge_requests.get_merge_request(client, 1, 7)
    assert result["title"] == "t"


def test_list_group_and_instance(settings: Settings) -> None:
    """Group and instance list paths are selected correctly."""
    client = _client(settings, "/groups/g/merge_requests", [{"iid": 3}])
    items = merge_requests.list_merge_requests(client, group_id="g")
    assert items[0]["iid"] == 3

    client2 = _client(settings, "/merge_requests", [{"iid": 4}])
    items2 = merge_requests.list_merge_requests(client2)
    assert items2[0]["iid"] == 4


def test_search_project_and_group(settings: Settings) -> None:
    """Search scopes project and group paths."""
    client = _client(settings, "/projects/", [{"iid": 5}])
    assert merge_requests.search_merge_requests(client, "q", project_id=1)[0]["iid"] == 5
    client2 = _client(settings, "/groups/", [{"iid": 6}])
    assert merge_requests.search_merge_requests(client2, "q", group_id="g")[0]["iid"] == 6


def test_search_rejects_both_scopes(settings: Settings) -> None:
    """Search rejects combined project and group."""
    client = _client(settings, "/search", [])
    with pytest.raises(ValueError, match="at most one"):
        merge_requests.search_merge_requests(client, "q", project_id="p", group_id="g")
