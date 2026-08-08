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
| Supply-chain parity (GLMCP-011) | Open — wheel/sdist SBOM + provenance vs container |

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
- `docs/docker-hub.md` — Hub Overview: pull, run, env vars, Cursor config
- `docs/docker.md` — maintainer build/hardening, DHI, registry coordinates
- `scripts/quality_gates.py` — radon CC/MI gates
- `docs/issues.yml` — authored backlog (GLMCP-001…011); 001–008 marked `done`
- `docs/guardrails/` — submodule @ `c43e347` (includes `supply-chain/` / `SC-DEP-*`)
- `.github/scaffold/` — submodule @ `7435f1d` (`dependency-updates.mdc` + Dependabot seed_once)
- `.github/dependabot.yml` — multi-ecosystem `all-dependencies` group, monthly (SC-DEP-*)

## Known pitfalls

- uv is not on host PATH; use `.tools/uv` (project-local binary, gitignored).
- System Python may be 3.14 without `python3-venv`; uv manages 3.13.
- `requires-python` is `>=3.13,<3.15` so the lock resolves only for supported CPythons.
- MCP SDK v2: `FastMCP` → `MCPServer` (`mcp.server.mcpserver`).
- `GITLAB_READ_ONLY=1` omits write tools from `tools/list`.
- After scaffold bump, `sync-templates.sh` **seeds** `.github/dependabot.yml` once and does
  not overwrite it — the multi-ecosystem config is safe across syncs.
- DHI pulls need `docker login dhi.io` locally and Hub secrets in CI
  (`DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`) — Community is free; auth is still
  required. Workflows pin `containerdevops@e38ce1d` and pass matching
  `scripts_ref` plus `CONTAINERDEVOPS_READ_TOKEN` as `checkout_token`
  (private-repo script checkout).
- Runtime has no shell; structure tests use absolute paths under `/app/.venv`.
- Signing/provenance deferred while private — see `docs/guardrail-deviations.yml`.
- Dependabot multi-ecosystem **accepted form (local validation 2026-08-08):** `schedule`
  and `commit-message` only under `multi-ecosystem-groups`; each `updates` entry has
  `patterns: ["*"]` and `multi-ecosystem-group: all-dependencies` and **no** per-ecosystem
  `schedule` or `groups:`. Matches GitHub multi-ecosystem docs. Confirm under
  Insights → Dependency graph → Dependabot after the config lands on the default branch.
- CI security job failed on this branch when `cryptography` 49.0.0 hit GHSA-g6cj-pr64-35w5;
  lockfile bumps to 50.0.0. Container workflow now also runs on `push`/`pull_request` to
  `main` (blocking); `workflow_dispatch` still respects the blocking input.

## Suggested next work

1. Ensure `CONTAINERDEVOPS_READ_TOKEN` is set; re-run Container on PR #13.
2. Implement GLMCP-011 (wheel/sdist supply-chain parity).
3. After Dependabot lands on `main`, trigger a version update and confirm one PR for all ecosystems.

*Last updated: 2026-08-09*
