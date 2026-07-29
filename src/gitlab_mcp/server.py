"""MCP stdio server exposing GitLab merge request tools."""

from __future__ import annotations

import logging
import sys
from typing import Any

from mcp.server.mcpserver import MCPServer

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings, get_settings
from gitlab_mcp.models import DiscussionPosition, MergeRequestListFilters
from gitlab_mcp.tools import diffs, discussions, merge_requests, pipelines, writes

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "GitLab merge request MCP server for self-hosted GitLab. "
    "Supports list/search/read of merge requests, diffs, discussions, "
    "pipelines, approvals, participants, and reviewers. "
    "Write tools (when enabled) allow thread replies, thread create/resolve, "
    "and updating title/description/labels/milestone only. "
    "Creating, merging, closing, and reopening merge requests is not available."
)


def create_server(
    settings: Settings | None = None,
    client: GitLabClient | None = None,
) -> MCPServer:
    """Build an :class:`MCPServer` with tools registered from settings.

    Args:
        settings: Optional settings override (defaults to environment).
        client: Optional HTTP client override (used by tests).

    Returns:
        Configured MCP server ready for ``run(transport='stdio')``.

    """
    cfg = settings or get_settings()
    server = MCPServer("gitlab-mcp", instructions=INSTRUCTIONS)
    http = client or GitLabClient(cfg)

    _register_read_tools(server, http, cfg)
    if not cfg.gitlab_read_only:
        _register_write_tools(server, http, cfg)
    else:
        logger.info("GITLAB_READ_ONLY set; write tools not registered")

    return server


def _default_project(cfg: Settings, project_id: str | int | None) -> str | int:
    """Resolve project id, falling back to the configured default.

    Args:
        cfg: Runtime settings.
        project_id: Explicit project id or path.

    Returns:
        Effective project id.

    Raises:
        ValueError: If neither argument nor default is available.

    """
    if project_id is not None:
        return project_id
    if cfg.gitlab_default_project:
        return cfg.gitlab_default_project
    raise ValueError("project_id is required (or set GITLAB_DEFAULT_PROJECT)")


def _register_read_tools(
    server: MCPServer,
    client: GitLabClient,
    cfg: Settings,
) -> None:
    """Register read-only merge request tools.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.

    """

    @server.tool()
    def list_merge_requests(
        project_id: str | None = None,
        group_id: str | None = None,
        state: str | None = None,
        scope: str | None = None,
        author_username: str | None = None,
        assignee_id: int | None = None,
        reviewer_username: str | None = None,
        labels: str | None = None,
        milestone: str | None = None,
        source_branch: str | None = None,
        target_branch: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        updated_after: str | None = None,
        updated_before: str | None = None,
        order_by: str | None = None,
        sort: str | None = None,
        search: str | None = None,
        search_in: str | None = None,
    ) -> list[Any]:
        """List merge requests with optional filters.

        Returns:
            Merge request objects.

        """
        filters = MergeRequestListFilters.model_validate(
            {
                "state": state,
                "scope": scope,
                "author_username": author_username,
                "assignee_id": assignee_id,
                "reviewer_username": reviewer_username,
                "labels": labels,
                "milestone": milestone,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "created_after": created_after,
                "created_before": created_before,
                "updated_after": updated_after,
                "updated_before": updated_before,
                "order_by": order_by,
                "sort": sort,
                "search": search,
                "in": search_in,
            },
        )
        return merge_requests.list_merge_requests(
            client,
            project_id=project_id,
            group_id=group_id,
            filters=filters,
        )

    @server.tool()
    def search_merge_requests(
        query: str,
        project_id: str | None = None,
        group_id: str | None = None,
    ) -> list[Any]:
        """Search merge requests by text query.

        Returns:
            Matching merge request search hits.

        """
        return merge_requests.search_merge_requests(
            client,
            query,
            project_id=project_id,
            group_id=group_id,
        )

    @server.tool()
    def get_merge_request(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """Get a single merge request by IID.

        Returns:
            Merge request object.

        """
        pid = _default_project(cfg, project_id)
        return merge_requests.get_merge_request(client, pid, merge_request_iid)

    @server.tool()
    def get_merge_request_diffs(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List file diffs for a merge request.

        Returns:
            Diff objects.

        """
        pid = _default_project(cfg, project_id)
        return diffs.get_merge_request_diffs(client, pid, merge_request_iid)

    @server.tool()
    def list_merge_request_commits(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List commits on a merge request.

        Returns:
            Commit objects.

        """
        pid = _default_project(cfg, project_id)
        return diffs.list_merge_request_commits(client, pid, merge_request_iid)

    @server.tool()
    def list_merge_request_diff_versions(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List diff versions (pushes) for a merge request.

        Returns:
            Diff version summaries.

        """
        pid = _default_project(cfg, project_id)
        return diffs.list_merge_request_diff_versions(client, pid, merge_request_iid)

    @server.tool()
    def get_merge_request_diff_version(
        merge_request_iid: int,
        version_id: int,
        project_id: str | None = None,
    ) -> Any:
        """Get a single diff version by id.

        Returns:
            Diff version object.

        """
        pid = _default_project(cfg, project_id)
        return diffs.get_merge_request_diff_version(
            client,
            pid,
            merge_request_iid,
            version_id,
        )

    @server.tool()
    def list_merge_request_discussions(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List discussion threads on a merge request.

        Returns:
            Discussion objects.

        """
        pid = _default_project(cfg, project_id)
        return discussions.list_merge_request_discussions(
            client,
            pid,
            merge_request_iid,
        )

    @server.tool()
    def get_merge_request_discussion(
        merge_request_iid: int,
        discussion_id: str,
        project_id: str | None = None,
    ) -> Any:
        """Get a single discussion thread.

        Returns:
            Discussion object.

        """
        pid = _default_project(cfg, project_id)
        return discussions.get_merge_request_discussion(
            client,
            pid,
            merge_request_iid,
            discussion_id,
        )

    @server.tool()
    def list_merge_request_pipelines(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List pipelines for a merge request.

        Returns:
            Pipeline objects.

        """
        pid = _default_project(cfg, project_id)
        return pipelines.list_merge_request_pipelines(
            client,
            pid,
            merge_request_iid,
        )

    @server.tool()
    def get_merge_request_approvals(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """Get approval state (Free-tier aware).

        Returns:
            Approvals payload.

        """
        pid = _default_project(cfg, project_id)
        return pipelines.get_merge_request_approvals(client, pid, merge_request_iid)

    @server.tool()
    def list_merge_request_participants(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List participants on a merge request.

        Returns:
            Participant user objects.

        """
        pid = _default_project(cfg, project_id)
        return pipelines.list_merge_request_participants(
            client,
            pid,
            merge_request_iid,
        )

    @server.tool()
    def list_merge_request_reviewers(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> list[Any]:
        """List reviewers on a merge request.

        Returns:
            Reviewer objects.

        """
        pid = _default_project(cfg, project_id)
        return pipelines.list_merge_request_reviewers(
            client,
            pid,
            merge_request_iid,
        )


def _build_position(
    base_sha: str | None,
    start_sha: str | None,
    head_sha: str | None,
    *,
    old_path: str | None,
    new_path: str | None,
    old_line: int | None,
    new_line: int | None,
    position_type: str,
) -> DiscussionPosition | None:
    """Build a discussion position when all SHAs are present.

    Args:
        base_sha: Merge base SHA.
        start_sha: Start commit SHA.
        head_sha: Head commit SHA.
        old_path: Old file path.
        new_path: New file path.
        old_line: Old line number.
        new_line: New line number.
        position_type: Position type (text, image, file).

    Returns:
        Position model, or ``None`` when SHAs are incomplete.

    """
    if not (base_sha and start_sha and head_sha):
        return None
    return DiscussionPosition(
        base_sha=base_sha,
        start_sha=start_sha,
        head_sha=head_sha,
        position_type=position_type,  # type: ignore[arg-type]
        old_path=old_path,
        new_path=new_path,
        old_line=old_line,
        new_line=new_line,
    )


def _register_write_tools(
    server: MCPServer,
    client: GitLabClient,
    cfg: Settings,
) -> None:
    """Register write tools (threads + allowlisted update).

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.

    """

    @server.tool()
    def create_merge_request_thread(
        merge_request_iid: int,
        body: str,
        project_id: str | None = None,
        base_sha: str | None = None,
        start_sha: str | None = None,
        head_sha: str | None = None,
        old_path: str | None = None,
        new_path: str | None = None,
        old_line: int | None = None,
        new_line: int | None = None,
        position_type: str = "text",
    ) -> Any:
        """Create a discussion thread, optionally on a diff line.

        Returns:
            Created discussion object.

        """
        pid = _default_project(cfg, project_id)
        position = _build_position(
            base_sha,
            start_sha,
            head_sha,
            old_path=old_path,
            new_path=new_path,
            old_line=old_line,
            new_line=new_line,
            position_type=position_type,
        )
        return discussions.create_merge_request_thread(
            client,
            pid,
            merge_request_iid,
            body,
            position=position,
        )

    @server.tool()
    def reply_to_merge_request_thread(
        merge_request_iid: int,
        discussion_id: str,
        body: str,
        project_id: str | None = None,
    ) -> Any:
        """Reply to an existing discussion thread.

        Returns:
            Created note object.

        """
        pid = _default_project(cfg, project_id)
        return discussions.reply_to_merge_request_thread(
            client,
            pid,
            merge_request_iid,
            discussion_id,
            body,
        )

    @server.tool()
    def set_merge_request_thread_resolved(
        merge_request_iid: int,
        discussion_id: str,
        resolved: bool,
        project_id: str | None = None,
    ) -> Any:
        """Resolve or unresolve a discussion thread.

        Returns:
            Updated discussion object.

        """
        pid = _default_project(cfg, project_id)
        return discussions.set_merge_request_thread_resolved(
            client,
            pid,
            merge_request_iid,
            discussion_id,
            resolved=resolved,
        )

    @server.tool()
    def update_merge_request(
        merge_request_iid: int,
        project_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        labels: str | None = None,
        add_labels: str | None = None,
        remove_labels: str | None = None,
        milestone_id: int | None = None,
    ) -> Any:
        """Update title, description, labels, or milestone only.

        Returns:
            Updated merge request object.

        """
        pid = _default_project(cfg, project_id)
        fields = {
            "title": title,
            "description": description,
            "labels": labels,
            "add_labels": add_labels,
            "remove_labels": remove_labels,
            "milestone_id": milestone_id,
        }
        provided = {key: value for key, value in fields.items() if value is not None}
        return writes.update_merge_request(client, pid, merge_request_iid, provided)


def main() -> None:
    """Run the MCP server over stdio."""
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
