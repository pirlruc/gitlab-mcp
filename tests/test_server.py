"""Tests for MCP server registration."""

from __future__ import annotations

import asyncio

import pytest

from gitlab_mcp.config import Settings
from gitlab_mcp.server import _build_position, _default_project, create_server


def test_default_project_fallback(settings: Settings) -> None:
    """Default project is used when project_id is omitted."""
    assert _default_project(settings, None) == "group/project"
    assert _default_project(settings, "other") == "other"


def test_default_project_required() -> None:
    """Missing project and default raises."""
    settings = Settings(gitlab_url="https://g.example", gitlab_token="t")
    with pytest.raises(ValueError, match="project_id is required"):
        _default_project(settings, None)


def test_build_position_optional() -> None:
    """Position is None unless all SHAs are provided."""
    assert (
        _build_position(
            None,
            "b",
            "c",
            old_path=None,
            new_path=None,
            old_line=None,
            new_line=None,
            position_type="text",
        )
        is None
    )
    position = _build_position(
        "a",
        "b",
        "c",
        old_path=None,
        new_path="f.py",
        old_line=None,
        new_line=3,
        position_type="text",
    )
    assert position is not None
    assert position.new_line == 3


def _tool_names(settings: Settings) -> set[str]:
    """Return registered tool names for the given settings.

    Args:
        settings: Server settings.

    Returns:
        Set of tool names.

    """
    server = create_server(settings)
    tools = asyncio.run(server.list_tools())
    return {tool.name for tool in tools}


def test_create_server_registers_write_tools(settings: Settings) -> None:
    """Write tools are registered when not read-only."""
    settings.gitlab_read_only = False
    names = _tool_names(settings)
    assert "list_merge_requests" in names
    assert "update_merge_request" in names
    assert "create_merge_request_thread" in names


def test_create_server_read_only_omits_writes(settings: Settings) -> None:
    """Write tools are absent in read-only mode."""
    settings.gitlab_read_only = True
    names = _tool_names(settings)
    assert "list_merge_requests" in names
    assert "update_merge_request" not in names
    assert "reply_to_merge_request_thread" not in names
