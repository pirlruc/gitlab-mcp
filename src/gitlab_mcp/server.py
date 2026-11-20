"""MCP server exposing GitLab merge request tools."""

from __future__ import annotations

import logging
import sys
from typing import Any

from mcp.server.mcpserver import MCPServer

from gitlab_mcp.client import GitLabClient
from gitlab_mcp.config import Settings, get_settings
from gitlab_mcp.http_transport import run_streamable_http
from gitlab_mcp.models import DiscussionPosition, MergeRequestListFilters
from gitlab_mcp.tools import diffs, discussions, merge_requests, pipelines, writes
from gitlab_mcp.tools.scope import enabled_toolsets
from gitlab_mcp.tools.surface import _project as _default_project
from gitlab_mcp.tools.surface import register_surface
from gitlab_mcp.tools.urls import parse_merge_request_url

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
    **server_kwargs: Any,
) -> MCPServer:
    """Build an :class:`MCPServer` with tools registered from settings.

    Args:
        settings: Optional settings override (defaults to environment).
        client: Optional HTTP client override (used by tests).
        **server_kwargs: Extra arguments for :class:`MCPServer` (auth, verifier).

    Returns:
        Configured MCP server ready to run.

    """
    cfg = settings or get_settings()
    server = MCPServer("gitlab-mcp", instructions=INSTRUCTIONS, **server_kwargs)
    http = client or GitLabClient(cfg)
    chosen = enabled_toolsets(cfg.gitlab_toolsets)
    allow_writes = not cfg.gitlab_read_only

    if "merge_requests" in chosen:
        _register_read_tools(server, http, cfg)
        _register_mr_aliases(server, http, cfg)
    if allow_writes and "merge_requests" in chosen:
        _register_write_tools(server, http, cfg)
    elif not allow_writes:
        logger.info("Read-only mode; write tools not registered")
    register_surface(server, http, cfg, chosen, allow_writes=allow_writes)

    return server


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
    ) -> Any:
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
    ) -> Any:
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
        merge_request_iid: int | None = None,
        project_id: str | None = None,
        url: str | None = None,
        include: str | None = None,
    ) -> Any:
        """Get a single merge request by IID or by a same-host URL.

        Returns:
            Merge request object, plus requested include facets.

        Raises:
            ValueError: When neither an IID nor a URL is given.

        """
        if url:
            project_id, merge_request_iid = parse_merge_request_url(cfg.gitlab_url, url)
        if merge_request_iid is None:
            raise ValueError("merge_request_iid or url is required")
        pid = _default_project(cfg, project_id)
        return merge_requests.get_merge_request(
            client,
            pid,
            merge_request_iid,
            include=include,
        )

    @server.tool()
    def get_merge_request_diffs(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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
    ) -> Any:
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

    @server.tool()
    def create_merge_request(
        source_branch: str,
        target_branch: str,
        title: str,
        project_id: str | None = None,
        description: str | None = None,
        labels: str | None = None,
    ) -> Any:
        """Create a merge request. Merging and closing stay unavailable.

        Returns:
            Created merge request object.

        """
        pid = _default_project(cfg, project_id)
        return writes.create_merge_request(
            client,
            pid,
            source_branch=source_branch,
            target_branch=target_branch,
            title=title,
            description=description,
            labels=labels,
        )


def _register_mr_aliases(server: MCPServer, client: GitLabClient, cfg: Settings) -> None:
    """Register official names that alias existing merge request reads.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.

    """

    @server.tool()
    def get_merge_request_commits(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """Alias of list_merge_request_commits.

        Returns:
            Commit objects.

        """
        pid = _default_project(cfg, project_id)
        return diffs.list_merge_request_commits(client, pid, merge_request_iid)

    @server.tool()
    def get_merge_request_pipelines(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """Alias of list_merge_request_pipelines.

        Returns:
            Pipeline objects.

        """
        pid = _default_project(cfg, project_id)
        return pipelines.list_merge_request_pipelines(client, pid, merge_request_iid)

    @server.tool()
    def get_merge_request_notes(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """List notes on a merge request.

        Returns:
            A page of note objects.

        """
        pid = _default_project(cfg, project_id)
        path = f"{merge_requests.mr_base_path(pid, merge_request_iid)}/notes"
        return client.paginate(path)

    @server.tool()
    def get_merge_request_conflicts(
        merge_request_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """List merge request conflicts.

        Returns:
            Conflict payload from GitLab.

        """
        pid = _default_project(cfg, project_id)
        path = f"{merge_requests.mr_base_path(pid, merge_request_iid)}/conflicts"
        return client.get(path)


def main() -> None:
    """Run stdio, or streamable HTTP when configured."""
    settings = get_settings()
    if settings.mcp_transport == "stdio":
        create_server(settings).run(transport="stdio")
        return
    run_streamable_http(settings, create_server)


if __name__ == "__main__":
    main()
