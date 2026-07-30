# Docker Hub — gitlab-mcp

Public overview for the [pirlruc/gitlab-mcp](https://hub.docker.com/r/pirlruc/gitlab-mcp)
image. Paste or adapt this page into the Docker Hub **Overview**. Deeper
build/hardening notes for maintainers live in [docker.md](docker.md).

**gitlab-mcp** is a stdio [MCP](https://modelcontextprotocol.io/) server for
self-hosted GitLab. It exposes merge-request tools (list, search, diffs,
discussions, pipelines, and allowlisted updates) to MCP clients such as Cursor.

The image speaks MCP over **stdin/stdout** only. There is no HTTP port and no
container `HEALTHCHECK`.

## Image

| Item | Value |
|------|--------|
| Docker Hub | `pirlruc/gitlab-mcp` |
| GHCR | `ghcr.io/pirlruc/gitlab-mcp` |
| Architectures | `linux/amd64`, `linux/arm64` |
| User | non-root `65532:65532` |

### Tags

| Tag | Meaning |
|-----|---------|
| `0.1.0` | Immutable release (example; use a semver tag) |
| `0.1` | Latest patch in the `0.1` line |
| `latest` | Latest release on the default branch publish |
| `sha-<git>` | Exact git SHA of the published commit |

Prefer a version tag (or digest) in production.

```bash
docker pull pirlruc/gitlab-mcp:0.1.0
```

## Quick start

Minimum run (interactive stdio — how MCP clients launch the server):

```bash
docker run --rm -i \
  -e GITLAB_URL=https://gitlab.example.com \
  -e GITLAB_TOKEN=glpat-xxxxxxxx \
  pirlruc/gitlab-mcp:0.1.0
```

Recommended hardened run:

```bash
docker run --rm -i \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e GITLAB_URL=https://gitlab.example.com \
  -e GITLAB_TOKEN \
  -e GITLAB_READ_ONLY=1 \
  pirlruc/gitlab-mcp:0.1.0
```

Pass secrets with `-e VAR` (from the host environment) or `--env-file`. Never bake
tokens into the image.

### Token scopes

| Mode | Suggested GitLab token scopes |
|------|-------------------------------|
| Read-only (`GITLAB_READ_ONLY=1`) | `read_api` |
| Writes enabled | `api` |

## Environment variables

All configuration is via environment variables (no CLI flags for secrets).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITLAB_URL` | **yes** | — | GitLab base URL, e.g. `https://gitlab.example.com` |
| `GITLAB_TOKEN` | **yes** | — | Personal or project access token |
| `GITLAB_READ_ONLY` | no | `false` | When `true` / `1`, write tools are not registered |
| `GITLAB_DEFAULT_PROJECT` | no | — | Default project id or `group/project` path |
| `GITLAB_TIMEOUT_SECONDS` | no | `30` | HTTP timeout in seconds |
| `GITLAB_PER_PAGE` | no | `50` | Page size for list endpoints (1–100) |
| `GITLAB_MAX_PAGES` | no | `20` | Max pages per paginated call |
| `GITLAB_CA_BUNDLE` | no | — | Path to a CA bundle file **inside the container** for private CAs |
| `GITLAB_VERIFY_SSL` | no | `true` | Set `false` / `0` to disable TLS verification (not recommended) |

Full reference: [configuration.md](configuration.md). Tool list:
[tools.md](tools.md).

### Private CA certificates

Mount a host CA bundle and point `GITLAB_CA_BUNDLE` at the mount path:

```bash
docker run --rm -i \
  -v /etc/ssl/certs/ca-certificates.crt:/certs/ca.crt:ro \
  -e GITLAB_CA_BUNDLE=/certs/ca.crt \
  -e GITLAB_URL \
  -e GITLAB_TOKEN \
  pirlruc/gitlab-mcp:0.1.0
```

## Cursor MCP config

Add to your Cursor MCP settings (adjust the image tag and env values):

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        "-e", "GITLAB_URL",
        "-e", "GITLAB_TOKEN",
        "-e", "GITLAB_READ_ONLY",
        "-e", "GITLAB_DEFAULT_PROJECT",
        "pirlruc/gitlab-mcp:0.1.0"
      ],
      "env": {
        "GITLAB_URL": "https://gitlab.example.com",
        "GITLAB_TOKEN": "<token>",
        "GITLAB_READ_ONLY": "1",
        "GITLAB_DEFAULT_PROJECT": "group/project"
      }
    }
  }
}
```

Docker must be available on the host PATH. The client starts the container and
talks MCP over the attached stdio streams.

## Compose sketch

```yaml
# For local smoke tests only — MCP clients usually invoke `docker run` directly.
services:
  gitlab-mcp:
    image: pirlruc/gitlab-mcp:0.1.0
    stdin_open: true
    tty: false
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=64m
    environment:
      GITLAB_URL: ${GITLAB_URL}
      GITLAB_TOKEN: ${GITLAB_TOKEN}
      GITLAB_READ_ONLY: "1"
```

## Source and support

- Source: https://github.com/pirlruc/gitlab-mcp
- Releases: https://github.com/pirlruc/gitlab-mcp/releases
- License: MIT
