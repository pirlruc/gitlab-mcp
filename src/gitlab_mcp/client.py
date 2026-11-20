"""HTTP client for the GitLab REST API v4."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx

from gitlab_mcp.config import Settings
from gitlab_mcp.errors import (
    GitLabError,
    GitLabRateLimitError,
    GitLabServerError,
    error_from_status,
)

logger = logging.getLogger(__name__)

_RETRYABLE = (GitLabRateLimitError, GitLabServerError)
_MAX_RETRIES = 3
_BACKOFF_SECONDS = (0.5, 1.0, 2.0)


def redact_secrets(text: str, token: str) -> str:
    """Replace the access token in arbitrary text.

    Args:
        text: Text that may contain the token.
        token: Token value to redact.

    Returns:
        Text with the token replaced by ``***``.

    """
    if not token:
        return text
    return text.replace(token, "***")


def encode_path_segment(value: str | int) -> str:
    """URL-encode a path segment such as a project path.

    Args:
        value: Project id (int) or path (``group/project``).

    Returns:
        Encoded path segment safe for URL interpolation.

    """
    return quote(str(value), safe="")


class GitLabClient:
    """Thin httpx wrapper with pagination, retry, and token redaction.

    Attributes:
        settings: Validated runtime settings.

    """

    def __init__(
        self,
        settings: Settings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create a client bound to ``settings``.

        Args:
            settings: Runtime configuration.
            transport: Optional httpx transport (used by tests).

        """
        self.settings = settings
        self._client = httpx.Client(
            base_url=settings.api_base,
            headers={
                "PRIVATE-TOKEN": settings.gitlab_access_token(),
                "Accept": "application/json",
            },
            timeout=settings.gitlab_timeout_seconds,
            verify=settings.verify,
            transport=transport,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> GitLabClient:
        """Enter the context manager.

        Returns:
            This client instance.

        """
        return self

    def __exit__(self, *_exc: object) -> None:
        """Exit the context manager and close the client."""
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        """Send one HTTP request with retry/backoff on transient failures.

        Args:
            method: HTTP method name.
            path: API path relative to ``/api/v4``.
            params: Optional query parameters.
            json: Optional JSON body.

        Returns:
            Parsed JSON body, or ``None`` for empty responses.

        Raises:
            GitLabError: On non-success HTTP statuses after retries.

        """
        last_error: GitLabError | None = None
        for attempt, delay in enumerate((*_BACKOFF_SECONDS, None)):
            try:
                return self._send(method, path, params=params, json=json)
            except _RETRYABLE as exc:
                last_error = exc
                if delay is None or attempt >= _MAX_RETRIES:
                    raise
                logger.warning(
                    "Retrying %s %s after %s (attempt %s)",
                    method,
                    path,
                    type(exc).__name__,
                    attempt + 1,
                )
                time.sleep(delay)
        if last_error is None:
            raise GitLabError(f"Retries exhausted for {method} {path}")
        raise last_error

    def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> Any:
        """GET a single resource.

        Args:
            path: API path relative to ``/api/v4``.
            params: Optional query parameters.

        Returns:
            Parsed JSON body.

        """
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        """POST a resource.

        Args:
            path: API path relative to ``/api/v4``.
            params: Optional query parameters.
            json: Optional JSON body.

        Returns:
            Parsed JSON body.

        """
        return self.request("POST", path, params=params, json=json)

    def put(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        """PUT a resource.

        Args:
            path: API path relative to ``/api/v4``.
            params: Optional query parameters.
            json: Optional JSON body.

        Returns:
            Parsed JSON body.

        """
        return self.request("PUT", path, params=params, json=json)

    def graphql(self, query: str, variables: Mapping[str, Any] | None = None) -> Any:
        """POST a GraphQL query to ``/api/graphql``.

        Args:
            query: GraphQL document.
            variables: Optional variables object.

        Returns:
            The ``data`` object from the GraphQL response.

        Raises:
            GitLabError: When the response contains errors or no data.

        """
        url = f"{self.settings.gitlab_url}/api/graphql"
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = dict(variables)
        body = self.request("POST", url, json=payload)
        if not isinstance(body, dict):
            raise GitLabError("GraphQL response was not an object")
        errors = body.get("errors")
        if errors:
            raise GitLabError(redact_secrets(str(errors), self.settings.gitlab_access_token()))
        return body.get("data")

    def get_capped_text(self, path: str, *, limit: int) -> dict[str, Any]:
        """GET a text body and truncate it to ``limit`` bytes.

        Args:
            path: API path relative to ``/api/v4``.
            limit: Maximum number of bytes kept.

        Returns:
            ``text``, ``truncated``, and ``bytes``.

        """
        response = self._send_response("GET", path)
        raw = response.content
        truncated = len(raw) > limit
        kept = raw[:limit]
        return {
            "text": kept.decode("utf-8", errors="replace"),
            "truncated": truncated,
            "bytes": len(kept),
        }

    def paginate(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fetch all pages up to ``gitlab_max_pages``.

        Args:
            path: API path relative to ``/api/v4``.
            params: Optional query parameters (without page/per_page).

        Returns:
            ``items``, ``truncated``, and ``next_page``. A non-list body is
            returned under ``object``.

        """
        query = dict(params or {})
        query["per_page"] = self.settings.gitlab_per_page
        items: list[Any] = []
        page = 1
        truncated = False
        next_page_out: str | None = None
        while page <= self.settings.gitlab_max_pages:
            query["page"] = page
            response = self._send_response("GET", path, params=query)
            body = self._parse_body(response)
            if not isinstance(body, list):
                return {
                    "items": items,
                    "truncated": False,
                    "next_page": None,
                    "object": body,
                }
            items.extend(body)
            next_page = response.headers.get("X-Next-Page") or ""
            if not next_page:
                break
            if page >= self.settings.gitlab_max_pages:
                truncated = True
                next_page_out = next_page
                break
            page = int(next_page)
        return {"items": items, "truncated": truncated, "next_page": next_page_out}

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        """Send a request and return the parsed body.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.
            json: JSON body.

        Returns:
            Parsed JSON body.

        """
        return self._parse_body(self._send_response(method, path, params=params, json=json))

    def _send_response(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> httpx.Response:
        """Send a request and raise typed errors on failure.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.
            json: JSON body.

        Returns:
            Successful httpx response.

        Raises:
            GitLabError: Mapped from the response status.

        """
        try:
            response = self._client.request(method, path, params=params, json=json)
        except httpx.HTTPError as exc:
            safe = redact_secrets(str(exc), self.settings.gitlab_access_token())
            raise GitLabError(f"HTTP transport error: {safe}") from exc
        if response.is_success:
            return response
        body: Any
        try:
            body = response.json()
        except ValueError:
            body = None
        error = error_from_status(response.status_code, body)
        error.message = redact_secrets(error.message, self.settings.gitlab_access_token())
        raise error

    def _parse_body(self, response: httpx.Response) -> Any:
        """Parse a successful response body, refusing oversized JSON.

        Args:
            response: Successful HTTP response.

        Returns:
            Parsed JSON, or ``None`` when the body is empty.

        Raises:
            GitLabError: When the body exceeds ``gitlab_max_response_bytes``.

        """
        if response.status_code == 204 or not response.content:
            return None
        limit = self.settings.gitlab_max_response_bytes
        if len(response.content) > limit:
            raise GitLabError(f"response exceeds {limit} bytes")
        return response.json()
