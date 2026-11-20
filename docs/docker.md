# Docker image — gitlab-mcp

Production OCI image for the stdio MCP server. Principles:
[DOCKER-*](https://github.com/pirlruc/guardrails/tree/main/docker).

**Docker Hub Overview (end-user runbook):** [docker-hub.md](docker-hub.md).

## Base image (DHI Community)

The image uses free **Docker Hardened Images** Community bases from `dhi.io`
(Apache 2.0 — not a timed trial; Select/Enterprise are optional paid SLAs only):

| Stage | Debian | Alpine |
|-------|--------|--------|
| Builder | `dhi.io/python:3.13-debian13-dev` | `dhi.io/python:3.13-alpine3.24-dev` |
| Runtime | `dhi.io/python:3.13-debian13` | `dhi.io/python:3.13-alpine3.24` |

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
those secrets before Buildx. `pirlruc/containerdevops` is public, so the caller
does not pass a checkout token.

`DOCKERHUB_DESCRIPTION_TOKEN` (Read, Write, and Delete) is what publishes
[docker-hub.md](docker-hub.md) as the Hub Overview. The image-pull token cannot
call that API.

### Scanning notes

The blocking scan is `pkg_types: library`. A full OS scan of the Debian base
still reports fixed OpenSSL findings, so the weekly rescan keeps `os,library`
and is non-blocking. Root `trivy.yaml` sets `vulnerability.ignore-unfixed: true`.

## Registries

| Registry | Image |
|----------|-------|
| GHCR | `ghcr.io/pirlruc/gitlab-mcp` (private; login required) |
| Docker Hub | `pirlruc/gitlab-mcp` |

Prefer pull-by-digest in deployments (`DOCKER-SEC-006`).

## Required environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITLAB_URL` | yes | GitLab base URL |
| `GITLAB_TOKEN` | one of token or file | Access token. `GITLAB_TOKEN_FILE` replaces it |
| `GITLAB_READ_ONLY` | no | Default `true`. Set `0` to register write tools |
| `GITLAB_DEFAULT_PROJECT` | no | Default project id/path |

See [configuration.md](configuration.md) for the full table.

## Recommended run (hardening)

The default transport is **stdio**. There is **no image HEALTHCHECK**
(`DOCKER-RUN-006`): a stdio container has no port, so a probe would fail the
common case. `EXPOSE 3333` documents streamable HTTP. In that mode the
orchestrator probes `GET /healthz`.

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  -e GITLAB_URL \
  -e GITLAB_TOKEN_FILE=/run/secrets/gitlab \
  -e GITLAB_READ_ONLY=1 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_HTTP_HOST=127.0.0.1 \
  -e MCP_AUTH_TOKEN_FILE=/run/secrets/mcp \
  -e MCP_ALLOWED_HOSTS=127.0.0.1:3333 \
  -v /path/gitlab-token:/run/secrets/gitlab:ro \
  -v /path/mcp-token:/run/secrets/mcp:ro \
  -p 127.0.0.1:3333:3333 \
  ghcr.io/pirlruc/gitlab-mcp:0.2.4
```

Stdio (no published port):

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

`v0.2.4` is signed. The publish job sets `sign: true`. Verify with the command
in [docker-hub.md](docker-hub.md). `docs/guardrail-deviations.yml` is empty.

## Local build

```bash
docker login dhi.io
bash scripts/pin-dhi-digests.sh   # digest-pin FROM lines
docker buildx build --load -t gitlab-mcp:local .
docker buildx build --load -f Dockerfile.alpine -t gitlab-mcp:alpine-local .
container-structure-test test --image gitlab-mcp:local --config container-structure-test.yml
```
