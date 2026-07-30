"""Shared fixtures for GitLab MCP tests."""

from __future__ import annotations

import json
from collections.abc import Callable, Generator
from typing import Any

import httpx
import pytest

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings, clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_settings() -> Generator[None]:
    """Reset the settings cache around every test.

    Yields:
        Control to the wrapped test.

    """
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def settings() -> Settings:
    """Return settings pointing at a fake GitLab instance.

    Returns:
        Settings with a test token.

    """
    return Settings(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="glpat-test-token-secret",
        gitlab_default_project="group/project",
        gitlab_per_page=20,
        gitlab_max_pages=5,
    )


def make_handler(
    routes: dict[tuple[str, str], tuple[int, Any, dict[str, str] | None]],
) -> httpx.MockTransport:
    """Build a MockTransport from an exact route table.

    Args:
        routes: Mapping of ``(method, path)`` to ``(status, body, headers)``.

    Returns:
        Configured mock transport.

    """

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method.upper(), request.url.path)
        if key not in routes:
            return httpx.Response(404, json={"message": f"unhandled {key}"})
        status, body, headers = routes[key]
        content = b"" if body is None else json.dumps(body).encode()
        return httpx.Response(status, content=content, headers=headers or {})

    return httpx.MockTransport(handler)


@pytest.fixture
def client_factory(
    settings: Settings,
) -> Callable[
    [dict[tuple[str, str], tuple[int, Any, dict[str, str] | None]]],
    GitLabClient,
]:
    """Build a GitLabClient factory bound to shared settings.

    Args:
        settings: Shared test settings.

    Returns:
        Callable accepting a routes dict and returning a client.

    """

    def _factory(
        routes: dict[tuple[str, str], tuple[int, Any, dict[str, str] | None]],
    ) -> GitLabClient:
        return GitLabClient(settings, transport=make_handler(routes))

    return _factory
