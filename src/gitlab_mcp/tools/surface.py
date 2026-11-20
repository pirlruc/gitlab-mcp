"""Read toolsets beyond merge requests, plus opt-in CI writes."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from gitlab_mcp import __version__
from gitlab_mcp.client import GitLabClient, encode_path_segment
from gitlab_mcp.config import Settings
from gitlab_mcp.tools.merge_requests import search_collection_path

_JOB_LOG_LIMIT = 512_000


def _project(cfg: Settings, project_id: str | int | None) -> str | int:
    """Resolve a project id or the configured default.

    Args:
        cfg: Runtime settings.
        project_id: Explicit project id or path.

    Returns:
        Project id or path.

    Raises:
        ValueError: When neither is available.

    """
    if project_id is not None:
        return project_id
    if cfg.gitlab_default_project:
        return cfg.gitlab_default_project
    raise ValueError("project_id is required (or set GITLAB_DEFAULT_PROJECT)")


def _proj(project_id: str | int) -> str:
    """Encode a project path segment.

    Args:
        project_id: Project id or path.

    Returns:
        Encoded segment.

    """
    return encode_path_segment(project_id)


def register_surface(
    server: MCPServer,
    client: GitLabClient,
    cfg: Settings,
    toolsets: set[str],
    *,
    allow_writes: bool,
) -> None:
    """Register tools for the enabled toolsets.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.
        toolsets: Enabled toolset names.
        allow_writes: Whether write tools may be registered.

    """
    if "core" in toolsets:
        _register_core(server, client, cfg)
    if "repository" in toolsets:
        _register_repository(server, client, cfg)
    if "ci" in toolsets:
        _register_ci(server, client, cfg, allow_writes=allow_writes)
    if "issues" in toolsets:
        _register_issues(server, client, cfg, allow_writes=allow_writes)
    if "work_items" in toolsets:
        _register_work_items(server, client, cfg, allow_writes=allow_writes)
    if "search" in toolsets:
        _register_search(server, client)
    if "wiki" in toolsets:
        _register_wiki(server, client, cfg)


def _register_core(server: MCPServer, client: GitLabClient, cfg: Settings) -> None:
    """Register core read tools.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.

    """

    @server.tool()
    def get_mcp_server_version() -> dict[str, str]:
        """Report this server's version.

        Returns:
            Name and version.

        """
        return {"name": "gitlab-mcp", "version": __version__}

    @server.tool()
    def get_project(project_id: str | None = None) -> Any:
        """Fetch a project.

        Returns:
            Project object.

        """
        return client.get(f"/projects/{_proj(_project(cfg, project_id))}")

    @server.tool()
    def list_projects(search: str | None = None, membership: bool | None = None) -> Any:
        """List projects visible to the token.

        Returns:
            A page of project objects.

        """
        params: dict[str, Any] = {}
        if search is not None:
            params["search"] = search
        if membership is not None:
            params["membership"] = membership
        return client.paginate("/projects", params=params)

    @server.tool()
    def get_group(group_id: str) -> Any:
        """Fetch a group.

        Returns:
            Group object.

        """
        return client.get(f"/groups/{encode_path_segment(group_id)}")

    @server.tool()
    def list_groups(search: str | None = None) -> Any:
        """List groups visible to the token.

        Returns:
            A page of group objects.

        """
        params = {"search": search} if search else None
        return client.paginate("/groups", params=params)

    @server.tool()
    def get_user(user_id: int | None = None) -> Any:
        """Fetch a user, or the authenticated user when no id is given.

        Returns:
            User object.

        """
        if user_id is None:
            return client.get("/user")
        return client.get(f"/users/{user_id}")

    @server.tool()
    def list_project_members(project_id: str | None = None) -> Any:
        """List members of a project.

        Returns:
            A page of member objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/members")

    @server.tool()
    def list_milestones(project_id: str | None = None, state: str | None = None) -> Any:
        """List project milestones.

        Returns:
            A page of milestone objects.

        """
        pid = _proj(_project(cfg, project_id))
        params = {"state": state} if state else None
        return client.paginate(f"/projects/{pid}/milestones", params=params)

    @server.tool()
    def list_todos(state: str | None = None) -> Any:
        """List todos for the authenticated user.

        Returns:
            A page of todo objects.

        """
        params = {"state": state} if state else None
        return client.paginate("/todos", params=params)

    @server.tool()
    def list_user_events(user_id: int | None = None) -> Any:
        """List events for a user, or the authenticated user.

        Returns:
            A page of event objects.

        """
        if user_id is None:
            return client.paginate("/events")
        return client.paginate(f"/users/{user_id}/events")


def _register_repository(server: MCPServer, client: GitLabClient, cfg: Settings) -> None:
    """Register repository read tools.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.

    """

    @server.tool()
    def list_branches(project_id: str | None = None, search: str | None = None) -> Any:
        """List repository branches.

        Returns:
            A page of branch objects.

        """
        pid = _proj(_project(cfg, project_id))
        params = {"search": search} if search else None
        return client.paginate(f"/projects/{pid}/repository/branches", params=params)

    @server.tool()
    def get_repository_file(file_path: str, ref: str, project_id: str | None = None) -> Any:
        """Fetch a repository file at a ref.

        Returns:
            File metadata and content from GitLab.

        """
        pid = _proj(_project(cfg, project_id))
        encoded = encode_path_segment(file_path)
        return client.get(f"/projects/{pid}/repository/files/{encoded}", params={"ref": ref})

    @server.tool()
    def list_repository_tree(
        project_id: str | None = None,
        path: str | None = None,
        ref: str | None = None,
    ) -> Any:
        """List a repository tree.

        Returns:
            A page of tree entries.

        """
        pid = _proj(_project(cfg, project_id))
        params: dict[str, Any] = {}
        if path is not None:
            params["path"] = path
        if ref is not None:
            params["ref"] = ref
        return client.paginate(f"/projects/{pid}/repository/tree", params=params)

    @server.tool()
    def get_commit(sha: str, project_id: str | None = None) -> Any:
        """Fetch one commit.

        Returns:
            Commit object.

        """
        pid = _proj(_project(cfg, project_id))
        return client.get(f"/projects/{pid}/repository/commits/{encode_path_segment(sha)}")

    @server.tool()
    def list_commits(project_id: str | None = None, ref_name: str | None = None) -> Any:
        """List commits.

        Returns:
            A page of commit objects.

        """
        pid = _proj(_project(cfg, project_id))
        params = {"ref_name": ref_name} if ref_name else None
        return client.paginate(f"/projects/{pid}/repository/commits", params=params)

    @server.tool()
    def list_tags(project_id: str | None = None) -> Any:
        """List repository tags.

        Returns:
            A page of tag objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/repository/tags")

    @server.tool()
    def list_releases(project_id: str | None = None) -> Any:
        """List project releases.

        Returns:
            A page of release objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/releases")


def _register_ci(
    server: MCPServer,
    client: GitLabClient,
    cfg: Settings,
    *,
    allow_writes: bool,
) -> None:
    """Register CI read tools and the opt-in pipeline write.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.
        allow_writes: Whether manage_pipeline is registered.

    """

    @server.tool()
    def list_pipelines(project_id: str | None = None, ref: str | None = None) -> Any:
        """List pipelines in a project.

        Returns:
            A page of pipeline objects.

        """
        pid = _proj(_project(cfg, project_id))
        params = {"ref": ref} if ref else None
        return client.paginate(f"/projects/{pid}/pipelines", params=params)

    @server.tool()
    def get_pipeline(pipeline_id: int, project_id: str | None = None) -> Any:
        """Fetch one pipeline.

        Returns:
            Pipeline object.

        """
        pid = _proj(_project(cfg, project_id))
        return client.get(f"/projects/{pid}/pipelines/{pipeline_id}")

    @server.tool()
    def get_pipeline_jobs(pipeline_id: int, project_id: str | None = None) -> Any:
        """List jobs in a pipeline.

        Returns:
            A page of job objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/pipelines/{pipeline_id}/jobs")

    @server.tool()
    def get_job(job_id: int, project_id: str | None = None, include_log: bool = False) -> Any:
        """Fetch a job and, when asked, a capped trace.

        Returns:
            Job object, plus ``log`` when ``include_log`` is true.

        """
        pid = _proj(_project(cfg, project_id))
        job = client.get(f"/projects/{pid}/jobs/{job_id}")
        if not include_log:
            return job
        log = client.get_capped_text(f"/projects/{pid}/jobs/{job_id}/trace", limit=_JOB_LOG_LIMIT)
        return {"job": job, "log": log}

    @server.tool()
    def get_artifact_file(
        job_id: int,
        artifact_path: str,
        project_id: str | None = None,
    ) -> Any:
        """Download one file from a job's artifacts, capped by the response limit.

        Returns:
            Text payload and whether it was truncated.

        """
        pid = _proj(_project(cfg, project_id))
        encoded = encode_path_segment(artifact_path)
        path = f"/projects/{pid}/jobs/{job_id}/artifacts/{encoded}"
        return client.get_capped_text(path, limit=cfg.gitlab_max_response_bytes)

    @server.tool()
    def list_pipeline_schedules(project_id: str | None = None) -> Any:
        """List pipeline schedules.

        Returns:
            A page of schedule objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/pipeline_schedules")

    if not allow_writes:
        return

    @server.tool()
    def manage_pipeline(pipeline_id: int, action: str, project_id: str | None = None) -> Any:
        """Retry or cancel a pipeline.

        Returns:
            Pipeline object after the action.

        Raises:
            ValueError: When ``action`` is not retry or cancel.

        """
        if action not in {"retry", "cancel"}:
            raise ValueError("action must be retry or cancel")
        pid = _proj(_project(cfg, project_id))
        return client.post(f"/projects/{pid}/pipelines/{pipeline_id}/{action}")


def _register_issues(
    server: MCPServer,
    client: GitLabClient,
    cfg: Settings,
    *,
    allow_writes: bool,
) -> None:
    """Register issue tools.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.
        allow_writes: Whether create_issue is registered.

    """

    @server.tool()
    def get_issue(issue_iid: int, project_id: str | None = None) -> Any:
        """Fetch one issue.

        Returns:
            Issue object.

        """
        pid = _proj(_project(cfg, project_id))
        return client.get(f"/projects/{pid}/issues/{issue_iid}")

    if not allow_writes:
        return

    @server.tool()
    def create_issue(
        title: str,
        project_id: str | None = None,
        description: str | None = None,
        labels: str | None = None,
    ) -> Any:
        """Create an issue.

        Returns:
            Created issue object.

        """
        pid = _proj(_project(cfg, project_id))
        body: dict[str, Any] = {"title": title}
        if description is not None:
            body["description"] = description
        if labels is not None:
            body["labels"] = labels
        return client.post(f"/projects/{pid}/issues", json=body)


def _register_work_items(
    server: MCPServer,
    client: GitLabClient,
    cfg: Settings,
    *,
    allow_writes: bool,
) -> None:
    """Register work-item read tools and opt-in note and link writes.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.
        allow_writes: Whether note and link writes are registered.

    """

    @server.tool()
    def get_work_item(work_item_iid: int, project_id: str | None = None) -> Any:
        """Fetch one work item.

        Returns:
            Work item object.

        """
        pid = _proj(_project(cfg, project_id))
        return client.get(f"/projects/{pid}/work_items/{work_item_iid}")

    @server.tool()
    def list_work_items(project_id: str | None = None) -> Any:
        """List work items in a project.

        Returns:
            A page of work item objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/work_items")

    @server.tool()
    def get_workitem_notes(work_item_iid: int, project_id: str | None = None) -> Any:
        """List notes on a work item.

        Returns:
            A page of note objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/work_items/{work_item_iid}/notes")

    @server.tool()
    def list_work_item_saved_views(project_id: str | None = None) -> Any:
        """List saved work-item views.

        Returns:
            A page of saved view objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/work_item_saved_views")

    @server.tool()
    def get_saved_view_work_items(view_id: int, project_id: str | None = None) -> Any:
        """List work items in a saved view.

        Returns:
            A page of work item objects.

        """
        pid = _proj(_project(cfg, project_id))
        return client.paginate(f"/projects/{pid}/work_item_saved_views/{view_id}/work_items")

    if not allow_writes:
        return

    @server.tool()
    def create_work_item_note(
        work_item_iid: int,
        body: str,
        project_id: str | None = None,
    ) -> Any:
        """Add a note on a work item.

        Returns:
            Created note object.

        """
        pid = _proj(_project(cfg, project_id))
        path = f"/projects/{pid}/work_items/{work_item_iid}/notes"
        return client.post(path, json={"body": body})

    @server.tool()
    def link_work_items(
        work_item_iid: int,
        target_work_item_iid: int,
        project_id: str | None = None,
    ) -> Any:
        """Link two work items in the same project.

        Returns:
            Link object.

        """
        pid = _proj(_project(cfg, project_id))
        path = f"/projects/{pid}/work_items/{work_item_iid}/linked_items"
        return client.post(path, json={"target_work_item_iid": target_work_item_iid})


def _register_search(server: MCPServer, client: GitLabClient) -> None:
    """Register multi-scope search and label search.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.

    """

    @server.tool()
    def search(
        scope: str,
        query: str,
        project_id: str | None = None,
        group_id: str | None = None,
    ) -> Any:
        """Search one GitLab scope.

        Returns:
            A page of search hits.

        """
        params = {"scope": scope, "search": query}
        path = search_collection_path(project_id, group_id)
        return client.paginate(path, params=params)

    @server.tool()
    def search_labels(
        query: str,
        project_id: str | None = None,
        group_id: str | None = None,
    ) -> Any:
        """Search labels in a project or group.

        Returns:
            A page of label objects.

        Raises:
            ValueError: When the scope is missing or both scopes are set.

        """
        params = {"search": query}
        if project_id is not None and group_id is not None:
            raise ValueError("Provide at most one of project_id or group_id")
        if project_id is not None:
            path = f"/projects/{encode_path_segment(project_id)}/labels"
        elif group_id is not None:
            path = f"/groups/{encode_path_segment(group_id)}/labels"
        else:
            raise ValueError("project_id or group_id is required")
        return client.paginate(path, params=params)


def _register_wiki(server: MCPServer, client: GitLabClient, cfg: Settings) -> None:
    """Register wiki reads.

    Args:
        server: MCP server instance.
        client: GitLab HTTP client.
        cfg: Runtime settings.

    """

    @server.tool()
    def list_wiki_pages(project_id: str | None = None, group_id: str | None = None) -> Any:
        """List wiki pages for a project or a group.

        Returns:
            A page of wiki page objects.

        Raises:
            ValueError: When the scope is missing or both scopes are set.

        """
        if (project_id is None) == (group_id is None) and project_id is None:
            if cfg.gitlab_default_project:
                project_id = cfg.gitlab_default_project
            else:
                raise ValueError("Provide exactly one of project_id or group_id")
        if project_id is not None and group_id is not None:
            raise ValueError("Provide exactly one of project_id or group_id")
        if project_id is not None:
            path = f"/projects/{encode_path_segment(project_id)}/wikis"
        else:
            path = f"/groups/{encode_path_segment(group_id or '')}/wikis"
        return client.paginate(path)
