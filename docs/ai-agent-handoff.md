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
| Container image (GLMCP-009) | In progress — DHI Python base; pin digests after `docker login dhi.io` |
| Guardrails realign (GLMCP-010) | In progress — MI avg 60; note/rule removed |

## Commands

```bash
export PATH="$PWD/.tools:$PATH"   # project-local uv binary
uv python install 3.13
uv sync --extra dev
bash scripts/check-ci-local.sh
uv run gitlab-mcp                 # requires GITLAB_URL + GITLAB_TOKEN
docker login dhi.io
bash scripts/pin-dhi-digests.sh   # digest-pin Dockerfile FROM lines
docker buildx build --load -t gitlab-mcp:local .
```

## Key paths

- `src/gitlab_mcp/server.py` — MCP stdio entry (`MCPServer` from mcp v2)
- `Dockerfile` — multi-stage DHI `dhi.io/python:3.13-debian13(-dev)`
- `scripts/pin-dhi-digests.sh` — refresh base digests after login
- `docs/docker.md` — run/hardening, DHI free tier, registry coordinates
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
- DHI pulls need `docker login dhi.io` locally and Hub secrets in CI
  (`DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`) — Community is free; auth is still
  required. Workflows pin `containerdevops@e537c48` (dhi.io login step).
- Runtime has no shell; structure tests use absolute paths under `/app/.venv`.
- Signing/provenance deferred while private — see `docs/guardrail-deviations.yml`.

## Suggested next work

1. Run `docker login dhi.io` + `bash scripts/pin-dhi-digests.sh`; rebuild and Trivy.
2. Merge [containerdevops#14](https://github.com/pirlruc/containerdevops/pull/14); re-pin to `main` SHA.
3. Confirm Hub secrets on the repo; exercise container workflow.
4. Land guardrails PR; bump `docs/guardrails` submodule.

*Last updated: 2026-07-30*
