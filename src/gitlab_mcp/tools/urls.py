"""Same-host URL checks for tool arguments."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

_MERGE_REQUEST = re.compile(r"^/(.+)/-/merge_requests/(\d+)$")


def require_same_host(gitlab_url: str, url: str) -> str:
    """Accept a URL only when its host matches the configured GitLab host.

    Args:
        gitlab_url: Configured GitLab base URL.
        url: Caller-supplied URL.

    Returns:
        The URL path.

    Raises:
        ValueError: When the URL is not http(s) or the host differs.

    """
    parsed = urlsplit(url)
    expected = urlsplit(gitlab_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("url must be an http(s) URL")
    if parsed.hostname != expected.hostname or parsed.port != expected.port:
        raise ValueError("url host must match GITLAB_URL")
    return parsed.path


def parse_merge_request_url(gitlab_url: str, url: str) -> tuple[str, int]:
    """Parse a merge request URL on the configured GitLab host.

    Args:
        gitlab_url: Configured GitLab base URL.
        url: Merge request URL.

    Returns:
        Project path and merge request IID.

    Raises:
        ValueError: When the URL is not a merge request on that host.

    """
    path = require_same_host(gitlab_url, url).rstrip("/")
    match = _MERGE_REQUEST.match(path)
    if match is None:
        raise ValueError("url is not a merge request on GITLAB_URL")
    return match.group(1), int(match.group(2))
