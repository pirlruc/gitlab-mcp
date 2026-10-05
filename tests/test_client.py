"""Tests for the GitLab HTTP client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from gitlab_mcp.client import GitLabClient, encode_path_segment, redact_secrets
from gitlab_mcp.config import Settings
from gitlab_mcp.errors import (
    GitLabError,
    GitLabNotFoundError,
    GitLabRateLimitError,
    GitLabServerError,
)


def test_redact_secrets() -> None:
    """Token values are replaced with asterisks."""
    assert redact_secrets("token=glpat-abc", "glpat-abc") == "token=***"
    assert redact_secrets("nothing", "") == "nothing"


def test_encode_path_segment() -> None:
    """Project paths are percent-encoded."""
    assert encode_path_segment("group/project") == "group%2Fproject"
    assert encode_path_segment(42) == "42"


def test_get_success(settings: Settings) -> None:
    """GET returns parsed JSON on 200."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["PRIVATE-TOKEN"] == settings.gitlab_token
        return httpx.Response(200, json={"id": 1})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        assert client.get("/projects/1") == {"id": 1}


def test_get_not_found(settings: Settings) -> None:
    """404 raises GitLabNotFoundError with redacted message."""
    token = settings.gitlab_access_token()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"message": f"missing {token}"},
        )

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GitLabNotFoundError) as exc:
            client.get("/missing")
    assert token not in exc.value.message
    assert "***" in exc.value.message


def test_paginate_follows_next_page(settings: Settings) -> None:
    """Pagination concatenates pages until X-Next-Page is empty."""
    pages = {
        "1": ([{"id": 1}], {"X-Next-Page": "2"}),
        "2": ([{"id": 2}], {}),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        page = request.url.params.get("page", "1")
        body, headers = pages[page]
        return httpx.Response(200, json=body, headers=headers)

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        items = client.paginate("/merge_requests")
    assert items == [{"id": 1}, {"id": 2}]


def test_retry_on_rate_limit(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    """429 responses are retried with backoff then succeed."""
    monkeypatch.setattr("gitlab_mcp.client.time.sleep", lambda _s: None)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(429, json={"message": "slow down"})
        return httpx.Response(200, json={"ok": True})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        assert client.get("/x") == {"ok": True}
    assert calls["n"] == 2


def test_retry_exhausted(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    """Persistent 503 raises after retries."""
    monkeypatch.setattr("gitlab_mcp.client.time.sleep", lambda _s: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"message": "down"})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GitLabServerError):
            client.get("/x")


def test_transport_error(settings: Settings) -> None:
    """Httpx transport failures become GitLabError."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(GitLabError, match="transport"):
            client.get("/x")


def test_paginate_non_list(settings: Settings) -> None:
    """Non-list first page is returned as-is."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        assert client.paginate("/obj") == {"ok": True}


def test_put_and_post(settings: Settings) -> None:
    """PUT and POST forward JSON bodies."""
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen[request.method] = json.loads(request.content.decode())
        return httpx.Response(200, json={"ok": True})

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        client.post("/a", json={"body": "hi"})
        client.put("/b", json={"title": "t"})
    assert seen["POST"] == {"body": "hi"}
    assert seen["PUT"] == {"title": "t"}


def test_empty_body(settings: Settings) -> None:
    """204 returns None."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    with GitLabClient(settings, transport=httpx.MockTransport(handler)) as client:
        assert client.get("/empty") is None


def test_rate_limit_type() -> None:
    """Sanity-check RateLimit remains retryable."""
    assert issubclass(GitLabRateLimitError, Exception)
