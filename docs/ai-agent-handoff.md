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
| Dependabot Insights (GLMCP-012) | Done — multi-ecosystem `all-dependencies` PR #62 merged; registries + PAT access working |
| Official MCP parity (GLMCP-014…021) | Open — authored from GitLab MCP tools docs; not implemented yet |

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
- `docs/issues.yml` — authored backlog (GLMCP-001…021); 001–008 marked `done`
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
  required. Container CI and Release `container-publish` pin
  `containerdevops@4185836` with matching `scripts_ref`, plus
  `CONTAINERDEVOPS_READ_TOKEN` as `checkout_token` (private-repo script
  checkout). Scan passes `pkg_types: library`; `trivy.yaml` sets
  `ignore-unfixed` only. Container jobs skip fork PRs (no secrets).
- Runtime has no shell; structure tests use absolute paths under `/app/.venv`.
- Signing/provenance deferred while private — see `docs/guardrail-deviations.yml`.
- Dependabot multi-ecosystem **accepted form (local validation 2026-08-08):** `schedule`
  and `commit-message` only under `multi-ecosystem-groups`; each `updates` entry has
  `patterns: ["*"]` and `multi-ecosystem-group: all-dependencies` and **no** per-ecosystem
  `schedule` or `groups:`. Matches GitHub multi-ecosystem docs.
- **Post-merge Dependabot (2026-08-09):** merging PR #13 triggered four
  `Dependabot Updates` jobs on `main`. Job definitions show
  `multi-ecosystem-update: true` and `dependency-groups: [{name: all-dependencies}]`.
  `uv` and `pre_commit` succeeded and logged `Creating a pull request for
  'all-dependencies'` (`create_pull_request` → 204) but **no new PR appeared**
  while six pre-existing per-ecosystem Dependabot PRs occupied the default
  open-PR limit. Those PRs (#2, #3, #5, #6, #11, #12) were closed on 2026-08-09
  and `dependabot.yml` was touched to re-trigger.
- **Dependabot private access (personal account):** org “grant Dependabot access”
  UI is unavailable. Wire Dependabot secrets via top-level `registries:` in
  `.github/dependabot.yml`: `DEPENDABOT_GITHUB_TOKEN` (PAT, `type: git`) for
  private siblings / reusable workflows, and `DOCKERHUB_*` (`type: docker-registry`)
  for `dhi.io`. Secrets live under Settings → Dependabot (not Actions).
- CI security job failed on this branch when `cryptography` 49.0.0 hit GHSA-g6cj-pr64-35w5;
  lockfile on main is already `cryptography` 50.0.0 (PR #12 is obsolete). Container
  workflow runs on `push`/`pull_request` to `main` (blocking). Container jobs skip
  `dependabot[bot]` (Actions secrets unavailable on Dependabot PRs for private
  reusable workflows). Host Docker Desktop may fail pulls via GPG creds helper;
  bases already cached still build (or unlock the keyring / `docker login`).

## Suggested next work

1. Close [GLMCP-012](https://github.com/pirlruc/gitlab-mcp/issues/38) as done (Insights confirmed via PR #62).
2. Implement Phase 6 starting with [GLMCP-014](https://github.com/pirlruc/gitlab-mcp/issues/42).
3. Decide [GLMCP-020](https://github.com/pirlruc/gitlab-mcp/issues/58); then GLMCP-011.

## Recent history

- Merged [PR #62](https://github.com/pirlruc/gitlab-mcp/pull/62) (`all-dependencies`):
  ruff 0.16.1, coverage 7.15.4, pre-commit 4.6.1, setuptools floor, pre-commit
  hook bumps; fixed ruff property docstrings; local `check-ci-local` + Docker
  image `gitlab-mcp:local` verified.
- Dependabot multi-ecosystem path confirmed after PAT (`guardrails`+) and
  `registries:` for git / dhi.io.
- Merged [PR #13](https://github.com/pirlruc/gitlab-mcp/pull/13) to `main`:
  multi-ecosystem Dependabot, container CI fixes, Phase 6 backlog.

*Last updated: 2026-08-09*
