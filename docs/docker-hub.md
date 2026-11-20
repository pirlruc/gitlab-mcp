# Docker Hub — gitlab-mcp

Public overview for the [pirlruc/gitlab-mcp](https://hub.docker.com/r/pirlruc/gitlab-mcp)
image. Paste or adapt this page into the Docker Hub **Overview**. Deeper
build/hardening notes for maintainers live in [docker.md](docker.md).

**gitlab-mcp** is a stdio [MCP](https://modelcontextprotocol.io/) server for
self-hosted GitLab. It exposes merge-request tools (list, search, diffs,
discussions, pipelines, and allowlisted updates) to MCP clients such as Cursor.

The default is MCP over **stdin/stdout**. Set `MCP_TRANSPORT=streamable-http`
to listen on port 3333. That mode requires `MCP_AUTH_TOKEN_FILE` and
`MCP_ALLOWED_HOSTS`. There is no image `HEALTHCHECK`; probe `GET /healthz`
when HTTP is enabled.

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
| `0.1.0` / `0.1` / `latest` / `sha-eacb0af` | Multi-arch index `sha256:9df623d5351c9c544177a3b71db93d7ceae5f96afe89df39fa0fb876b5fa4b8e` |
| `0.1.0` linux/amd64 | `sha256:b70b8437dc82bff081767550b2f9c2dfa30bbf0c14775b6f681b4efd3af0cc26` |
| `0.1.0` linux/arm64 | `sha256:3b01f0401f06252075d72c5d5f3a56c5ce4b092a73dd6afff9c7d0e18a5e256c` |

Prefer the index digest in production so the client selects the architecture.

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
| `GITLAB_TOKEN` | one of token or file | — | Personal or project access token |
| `GITLAB_TOKEN_FILE` | one of token or file | — | File containing the GitLab token. Replaces `GITLAB_TOKEN` |
| `MCP_TRANSPORT` | no | `stdio` | `stdio` or `streamable-http` |
| `MCP_HTTP_HOST` | no | `127.0.0.1` | HTTP bind address |
| `MCP_HTTP_PORT` | no | `3333` | HTTP bind port |
| `MCP_AUTH_TOKEN_FILE` | HTTP only | — | Bearer secret file. Required for HTTP. Not an environment variable |
| `MCP_ALLOWED_HOSTS` | HTTP only | — | Comma-separated Host values. Required for HTTP |
| `MCP_ALLOWED_ORIGINS` | no | empty | Comma-separated Origin values |
| `GITLAB_READ_ONLY` | no | `true` | Set `0` to register write tools. The default is read-only |
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
