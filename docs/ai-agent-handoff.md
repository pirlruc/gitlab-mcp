# AI agent handoff — gitlab-mcp

## Delivery status

| Phase | Status |
|-------|--------|
| Foundation (GLMCP-001) | Done — git init, submodules pinned, sync-templates |
| Quality gates (GLMCP-002) | Done |
| Client (GLMCP-003) | Done |
| Read tools (GLMCP-004/005) | Done |
| Write tools (GLMCP-006/007) | Done |
| Docs / release (GLMCP-008) | Done |

## Commands

```bash
export PATH="$PWD/.tools:$PATH"   # project-local uv binary
uv python install 3.13
uv sync --extra dev
bash scripts/check-ci-local.sh
uv run gitlab-mcp                 # requires GITLAB_URL + GITLAB_TOKEN
```

## Key paths

- `src/gitlab_mcp/server.py` — MCP stdio entry (`MCPServer` from mcp v2)
- `src/gitlab_mcp/client.py` — httpx GitLab client
- `src/gitlab_mcp/tools/writes.py` — update allowlist (blocks `state_event`)
- `scripts/quality_gates.py` — radon CC/MI gates
- `docs/issues.yml` — authored backlog (GLMCP-001…008)
- `docs/guardrails/` — submodule @ `2b42236`
- `.github/scaffold/` — submodule @ `db1ae34`

## Known pitfalls

- uv is not on host PATH; use `.tools/uv` (project-local binary, gitignored).
- System Python may be 3.14 without `python3-venv`; uv manages 3.13.
- MCP SDK v2: `FastMCP` → `MCPServer` (`mcp.server.mcpserver`).
- `GITLAB_READ_ONLY=1` omits write tools from `tools/list`.
- `sync-templates.sh` overwrites `.github/dependabot.yml` with the scaffold
  github-actions-only template; restore uv + pre-commit ecosystems after sync.

## Suggested next work

1. Open PR: https://github.com/pirlruc/gitlab-mcp/pull/new/feature-gitlab-mcp-foundation
2. `setup-issue-scaffold.sh` then `issues-sync.py --dry-run` (approval for publish)
3. Optional: smoke against a live self-hosted GitLab (`scripts/smoke.py`)

*Last updated: 2026-07-29*
