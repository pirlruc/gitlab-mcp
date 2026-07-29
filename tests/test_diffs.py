"""Tests for diff and commit tools."""

from __future__ import annotations

import httpx

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings
from gitlab_mcp.tools import diffs


def test_diffs_commits_versions(settings: Settings) -> None:
    """Diff, commit, and version endpoints return lists/objects."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/diffs"):
            return httpx.Response(200, json=[{"old_path": "a.py"}])
        if request.url.path.endswith("/commits"):
            return httpx.Response(200, json=[{"id": "abc"}])
        if request.url.path.endswith("/versions"):
            return httpx.Response(200, json=[{"id": 9}])
        if request.url.path.endswith("/versions/9"):
            return httpx.Response(200, json={"id": 9, "diffs": []})
        return httpx.Response(404, json={"message": "no"})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        assert diffs.get_merge_request_diffs(client, 1, 2)[0]["old_path"] == "a.py"
        assert diffs.list_merge_request_commits(client, 1, 2)[0]["id"] == "abc"
        assert diffs.list_merge_request_diff_versions(client, 1, 2)[0]["id"] == 9
        assert diffs.get_merge_request_diff_version(client, 1, 2, 9)["id"] == 9
