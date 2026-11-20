"""Toolset selection."""

from __future__ import annotations

TOOLSETS = frozenset({
    "merge_requests",
    "issues",
    "work_items",
    "search",
    "wiki",
    "core",
    "repository",
    "ci",
})


def enabled_toolsets(value: str) -> set[str]:
    """Resolve ``GITLAB_TOOLSETS``.

    Args:
        value: ``all`` or a comma-separated list.

    Returns:
        Enabled toolset names.

    Raises:
        ValueError: When a name is not a known toolset.

    """
    if value.strip() == "all":
        return set(TOOLSETS)
    chosen = {item.strip() for item in value.split(",") if item.strip()}
    unknown = chosen - TOOLSETS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"unknown toolsets: {names}")
    return chosen
