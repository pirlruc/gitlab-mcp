# Docker image — gitlab-mcp

Production OCI image for the stdio MCP server. Principles:
[DOCKER-*](https://github.com/pirlruc/guardrails/tree/main/docker).

## Base image (DHI Community)

The image uses free **Docker Hardened Images** Community bases from `dhi.io`
(Apache 2.0 — not a timed trial; Select/Enterprise are optional paid SLAs only):

| Stage | Tag |
|-------|-----|
| Builder | `dhi.io/python:3.13-debian13-dev` |
| Runtime | `dhi.io/python:3.13-debian13` |

Debian (glibc) keeps wheels aligned with the previous slim-bookworm stack. Runtime
is minimal (no shell / package manager) and runs as `65532:65532`. Do **not**
strip packages from Official Image slim bases — CVE noise there is OS-layer; DHI
replaces that surface.

Pulls require a free Docker Hub account:

```bash
docker login dhi.io
# then pin digests into the Dockerfile (DOCKER-BUILD-003):
bash scripts/pin-dhi-digests.sh
```

CI: set repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` (Hub PAT
with read). The containerdevops build/publish workflows log in to `dhi.io` with
those secrets before Buildx.

## Registries

| Registry | Image |
|----------|-------|
| GHCR | `ghcr.io/pirlruc/gitlab-mcp` |
| Docker Hub | `pirlruc/gitlab-mcp` (when credentials are configured) |

Prefer pull-by-digest in deployments (`DOCKER-SEC-006`).

## Required environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITLAB_URL` | yes | GitLab base URL |
| `GITLAB_TOKEN` | yes | Access token |
| `GITLAB_READ_ONLY` | no | Omit write tools when `true` |
| `GITLAB_DEFAULT_PROJECT` | no | Default project id/path |

See [configuration.md](configuration.md) for the full table.

## Recommended run (hardening)

The server speaks MCP over **stdio** only — no published port and **no
HEALTHCHECK** (`DOCKER-RUN-006`).

```bash
docker run --rm -i \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e GITLAB_URL \
  -e GITLAB_TOKEN \
  -e GITLAB_READ_ONLY=1 \
  ghcr.io/pirlruc/gitlab-mcp:latest
```

## Cursor MCP config (image)

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "-e", "GITLAB_URL",
        "-e", "GITLAB_TOKEN",
        "ghcr.io/pirlruc/gitlab-mcp:latest"
      ],
      "env": {
        "GITLAB_URL": "https://gitlab.example.com",
        "GITLAB_TOKEN": "<token>"
      }
    }
  }
}
```

## Signing and provenance

While this repository is **private** on a non–Enterprise Cloud plan, image
signing (`DOCKER-SEC-003`) and SLSA provenance (`DOCKER-SEC-004`) are deferred.
See `docs/guardrail-deviations.yml`. The publish workflow enables both when
`sign: true` (intended once the repo is public). SBOM artifacts are still
produced by the scan workflow.

## Local build

```bash
docker login dhi.io
bash scripts/pin-dhi-digests.sh   # digest-pin FROM lines
docker buildx build --load -t gitlab-mcp:local .
container-structure-test test --image gitlab-mcp:local --config container-structure-test.yml
```
