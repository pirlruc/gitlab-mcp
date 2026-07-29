"""Exception types mapped from GitLab HTTP status codes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class GitLabError(Exception):
    """Base error for GitLab API failures.

    Attributes:
        status_code: HTTP status when known.
        message: Human-readable error detail (token-safe).

    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize the error.

        Args:
            message: Safe error detail with secrets already redacted.
            status_code: Optional HTTP status code.

        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GitLabAuthError(GitLabError):
    """Raised for 401 Unauthorized responses."""


class GitLabForbiddenError(GitLabError):
    """Raised for 403 Forbidden responses."""


class GitLabNotFoundError(GitLabError):
    """Raised for 404 Not Found responses."""


class GitLabConflictError(GitLabError):
    """Raised for 409 Conflict responses."""


class GitLabRateLimitError(GitLabError):
    """Raised for 429 Too Many Requests responses."""


class GitLabServerError(GitLabError):
    """Raised for 5xx server errors."""


class GitLabClientError(GitLabError):
    """Raised for other 4xx client errors."""


def _message_from_body(body: Any, fallback: str) -> str:
    """Extract a message string from a GitLab JSON error body.

    Args:
        body: Parsed JSON body or None.
        fallback: Default message when the body has no message.

    Returns:
        Best-effort error message.

    """
    if isinstance(body, dict):
        error = body.get("error") or body.get("message")
        if isinstance(error, str):
            return error
        if isinstance(error, list):
            return "; ".join(str(item) for item in error)
        if isinstance(error, dict):
            return str(error)
    return fallback


_STATUS_FACTORIES: dict[int, Callable[[str, int], GitLabError]] = {
    401: GitLabAuthError,
    403: GitLabForbiddenError,
    404: GitLabNotFoundError,
    409: GitLabConflictError,
    429: GitLabRateLimitError,
}


def error_from_status(status_code: int, body: Any = None) -> GitLabError:
    """Map an HTTP status code to a typed :class:`GitLabError`.

    Args:
        status_code: HTTP response status.
        body: Optional parsed JSON body.

    Returns:
        Concrete error subclass for the status family.

    """
    message = _message_from_body(body, f"GitLab API error ({status_code})")
    factory = _STATUS_FACTORIES.get(status_code)
    if factory is not None:
        return factory(message, status_code)
    if 500 <= status_code < 600:
        return GitLabServerError(message, status_code)
    if 400 <= status_code < 500:
        return GitLabClientError(message, status_code)
    return GitLabError(message, status_code)
