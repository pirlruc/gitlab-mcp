# gitlab-mcp

stdio [MCP](https://modelcontextprotocol.io/) server for **self-hosted GitLab**
merge requests: list, search, and read MRs plus safe updates (thread replies,
description/labels). Creating, merging, and closing MRs is intentionally
unavailable — suitable for GitLab 18.6 Free, which has no built-in MCP server.

**Repository:** [pirlruc/gitlab-mcp](https://github.com/pirlruc/gitlab-mcp)

## Features

| Tool | Access |
|------|--------|
| `list_merge_requests` / `search_merge_requests` / `get_merge_request` | Read |
| Diffs, commits, diff versions | Read |
| Discussions, pipelines, approvals, participants, reviewers | Read |
| Create / reply / resolve discussion threads | Write (optional) |
| Update title, description, labels, milestone | Write (optional) |

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

Org floors from [`docs/guardrails/python/profile.thresholds.yml`](https://github.com/pirlruc/guardrails/blob/main/python/profile.thresholds.yml):

- Cyclomatic complexity: max ≤ 8, average ≤ 5
- Maintainability index: min ≥ 40, average ≥ 60
- Statement and branch coverage ≥ 95%
- Documentation coverage ≥ 95% (Google docstring style)

```bash
bash scripts/check-ci-local.sh
```

## Container image

See [docs/docker.md](docs/docker.md). Build locally with `docker buildx build --load -t gitlab-mcp:local .`.
Published images: `ghcr.io/pirlruc/gitlab-mcp` and (when configured) `pirlruc/gitlab-mcp` on Docker Hub.
## Releases (local Commitizen)

1. `uv sync --frozen --extra dev`
2. `uv run cz bump`
3. Push the tag; `.github/workflows/release.yml` creates the GitHub Release.

## License

MIT — see [LICENSE](LICENSE).
