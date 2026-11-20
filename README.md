# gitlab-mcp

[MCP](https://modelcontextprotocol.io/) server for **self-hosted GitLab**
merge requests and the read-only core, repository, and CI toolsets.
Writes (thread replies, issue creation, `create_merge_request`) stay off unless
`GITLAB_READ_ONLY=0`. Merging and closing merge requests stay unavailable.
Verified against GitLab CE **18.11** (self-hosted Free; no built-in MCP server).
The client is `/api/v4` and is not version-gated.

**Repository:** [pirlruc/gitlab-mcp](https://github.com/pirlruc/gitlab-mcp)

## Features

| Tool | Access |
|------|--------|
| `list_merge_requests` / `search_merge_requests` / `get_merge_request` | Read |
| Diffs, commits, diff versions | Read |
| Discussions, pipelines, approvals, participants, reviewers | Read |
| Create / reply / resolve discussion threads | Write (`GITLAB_READ_ONLY=0`) |
| Update title, description, labels, milestone | Write (`GITLAB_READ_ONLY=0`) |
| `create_merge_request` | Write (`GITLAB_READ_ONLY=0`) |
| Projects, groups, users, milestones, todos | Read (`core`) |
| Branches, files, commits, tags, releases | Read (`repository`) |
| Pipelines, jobs, capped logs, artifacts | Read (`ci`) |

## Quick start

```bash
# Project-local uv binary (no system install). Example:
#   mkdir -p .tools && gh release download --repo astral-sh/uv \
#     --pattern 'uv-x86_64-unknown-linux-gnu.tar.gz' -O /tmp/uv.tgz
#   tar -xzf /tmp/uv.tgz -C /tmp && cp /tmp/uv-*/uv .tools/uv
export PATH="$PWD/.tools:$PATH"
uv python install 3.13
uv sync --extra dev
```

Configure Cursor (or another MCP host) with stdio:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "uv",
      "args": ["--directory", "/path/to/gitlab-mcp", "run", "gitlab-mcp"],
      "env": {
        "GITLAB_URL": "https://gitlab.example.com",
        "GITLAB_TOKEN": "<token>",
        "GITLAB_DEFAULT_PROJECT": "group/project"
      }
    }
  }
}
```

See [docs/configuration.md](docs/configuration.md) and [docs/tools.md](docs/tools.md).

## Quality gates

Org floors from [`docs/guardrails/python/profile.thresholds.yml`](https://github.com/pirlruc/guardrails/blob/1.15.0/python/profile.thresholds.yml):

- Cyclomatic complexity: max ≤ 8, average ≤ 5
- Maintainability index: min ≥ 40, average ≥ 60
- Statement and branch coverage ≥ 95%
- Documentation coverage ≥ 95% (Google docstring style)

```bash
bash scripts/check-ci-local.sh
```

## Container image

See [docs/docker-hub.md](docs/docker-hub.md) for pull/run/env (Hub Overview) and
[docs/docker.md](docs/docker.md) for maintainer build notes. Build locally with
`docker buildx build --load -t gitlab-mcp:local .`.
Published images: `ghcr.io/pirlruc/gitlab-mcp` and (when configured) `pirlruc/gitlab-mcp` on Docker Hub.
## Releases (local Commitizen)

1. `uv sync --frozen --extra dev`
2. `uv run cz bump`
3. Push the tag; `.github/workflows/release.yml` creates the GitHub Release.

## License

MIT — see [LICENSE](LICENSE).
