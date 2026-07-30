"""Tests for HTTP status → exception mapping."""

from __future__ import annotations

from gitlab_mcp.errors import (
    GitLabAuthError,
    GitLabClientError,
    GitLabConflictError,
    GitLabError,
    GitLabForbiddenError,
    GitLabNotFoundError,
    GitLabRateLimitError,
    GitLabServerError,
    error_from_status,
)


def test_known_status_mapping() -> None:
    """Known statuses map to typed subclasses."""
    assert isinstance(error_from_status(401), GitLabAuthError)
    assert isinstance(error_from_status(403), GitLabForbiddenError)
    assert isinstance(error_from_status(404), GitLabNotFoundError)
    assert isinstance(error_from_status(409), GitLabConflictError)
    assert isinstance(error_from_status(429), GitLabRateLimitError)
    assert isinstance(error_from_status(500), GitLabServerError)
    assert isinstance(error_from_status(400, {"message": "bad"}), GitLabClientError)


def test_message_extraction_variants() -> None:
    """Message is pulled from string, list, or dict error bodies."""
    assert "boom" in error_from_status(400, {"message": "boom"}).message
    assert "a" in error_from_status(400, {"error": ["a", "b"]}).message
    assert "x" in error_from_status(400, {"error": {"x": 1}}).message
    assert isinstance(error_from_status(418), GitLabError)
