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
| Container image (GLMCP-009) | In progress — Dockerfile + callers; pin SHA after containerdevops push |
| Guardrails realign (GLMCP-010) | In progress — MI avg 60; note/rule removed |

## Commands

```bash
export PATH="$PWD/.tools:$PATH"   # project-local uv binary
uv python install 3.13
uv sync --extra dev
bash scripts/check-ci-local.sh
uv run gitlab-mcp                 # requires GITLAB_URL + GITLAB_TOKEN
docker buildx build --load -t gitlab-mcp:local .
```

## Key paths

- `src/gitlab_mcp/server.py` — MCP stdio entry (`MCPServer` from mcp v2)
- `Dockerfile` — multi-stage digest-pinned `python:3.13-slim-bookworm`
- `docs/docker.md` — run/hardening and registry coordinates
- `scripts/quality_gates.py` — radon CC/MI gates
- `docs/issues.yml` — authored backlog (GLMCP-001…010)
- `docs/guardrails/` — submodule (bump after guardrails python/docker pack merges)
- `.github/scaffold/` — submodule @ `db1ae34`

## Known pitfalls

- uv is not on host PATH; use `.tools/uv` (project-local binary, gitignored).
- System Python may be 3.14 without `python3-venv`; uv manages 3.13.
- MCP SDK v2: `FastMCP` → `MCPServer` (`mcp.server.mcpserver`).
- `GITLAB_READ_ONLY=1` omits write tools from `tools/list`.
- `sync-templates.sh` overwrites `.github/dependabot.yml` with the scaffold
  github-actions-only template; restore uv + pre-commit + docker ecosystems after sync.
- Container workflow pins use `CONTAINERDEVOPS_SHA` until the first
  containerdevops commit is published.
- Signing/provenance deferred while private — see `docs/guardrail-deviations.yml`.

## Suggested next work

1. Land guardrails + containerdevops PRs; bump submodule / replace `CONTAINERDEVOPS_SHA`.
2. Set `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` before exercising publish.
3. Measure image size vs 300 MB and arm64 wheel resolution.
4. Open PR / sync issues when approved.

*Last updated: 2026-07-29*
