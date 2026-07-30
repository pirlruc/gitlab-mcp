#!/usr/bin/env python3
"""Optional live smoke against a real GitLab instance.

Requires ``GITLAB_URL`` and ``GITLAB_TOKEN``. Lists open merge requests for
``GITLAB_DEFAULT_PROJECT`` when set.
"""

from __future__ import annotations

import json

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import get_settings
from gitlab_mcp.models import MergeRequestListFilters
from gitlab_mcp.tools import merge_requests


def main() -> int:
    """Run a minimal live API smoke test.

    Returns:
        Process exit code.

    """
    settings = get_settings()
    with GitLabClient(settings) as client:
        filters = MergeRequestListFilters(state="opened")
        items = merge_requests.list_merge_requests(
            client,
            project_id=settings.gitlab_default_project,
            filters=filters,
        )
    print(json.dumps({"count": len(items)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
