# gitlab-mcp

stdio [MCP](https://modelcontextprotocol.io/) server for self-hosted GitLab.
It exposes merge-request tools and the read-only core, repository, and CI
toolsets. Writes stay off unless `GITLAB_READ_ONLY=0`. Merging and closing
merge requests stay unavailable.

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

Debian owns the unsuffixed tags. Alpine is the `-alpine` suffix. Pin `0.2.4`
or its index digest. A later publish can move `latest`.

### Tags

| Tag | Meaning |
|-----|---------|
| `0.2.4` / `0.2` / `latest` / `0.2.4-debian` / `latest-debian` | Debian index `sha256:527454bc119b2b20756db609f03533c5b35d5ffe2a0b348f8066253897f4c2b9` |
| `0.2.4-alpine` / `0.2-alpine` / `latest-alpine` | Alpine index `sha256:569c3aab2248a037e90e0669de3c4ef33f4f025e1b9fce985c29cba155f4fd8b` |
| `0.1.0` / `0.1` | Previous Debian index `sha256:9df623d5351c9c544177a3b71db93d7ceae5f96afe89df39fa0fb876b5fa4b8e` |

`0.2.4` is the signed release. Prefer that tag over `0.2.0`–`0.2.3`.

```bash
docker pull pirlruc/gitlab-mcp:0.2.4
docker pull pirlruc/gitlab-mcp:0.2.4-alpine
docker pull pirlruc/gitlab-mcp@sha256:527454bc119b2b20756db609f03533c5b35d5ffe2a0b348f8066253897f4c2b9
```

GHCR serves the same tags. The package requires a login:

```bash
echo "$CR_PAT" | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/pirlruc/gitlab-mcp:0.2.4
```

## Quick start

```bash
docker run --rm -i \
  -e GITLAB_URL=https://gitlab.example.com \
  -e GITLAB_TOKEN=glpat-xxxxxxxx \
  pirlruc/gitlab-mcp:0.2.4
```

Hardened run:

```bash
docker run --rm -i \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  -e GITLAB_URL=https://gitlab.example.com \
  -e GITLAB_TOKEN \
  -e GITLAB_READ_ONLY=1 \
  pirlruc/gitlab-mcp:0.2.4
```

Pass secrets with `-e VAR` (from the host environment) or `--env-file`. Never bake
tokens into the image.

### Token scopes

| Mode | Suggested GitLab token scopes |
|------|-------------------------------|
| Read-only (`GITLAB_READ_ONLY=1` or unset) | `read_api` |
| Writes enabled (`GITLAB_READ_ONLY=0`) | `api` |

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITLAB_URL` | **yes** | — | GitLab base URL, e.g. `https://gitlab.example.com` |
| `GITLAB_TOKEN` | one of token or file | — | Personal or project access token |
| `GITLAB_TOKEN_FILE` | one of token or file | — | File containing the GitLab token. Replaces `GITLAB_TOKEN` |
| `MCP_TRANSPORT` | no | `stdio` | `stdio` or `streamable-http` |
| `MCP_HTTP_HOST` | no | `127.0.0.1` | HTTP bind address |
| `MCP_HTTP_PORT` | no | `3333` | HTTP bind port |
| `MCP_AUTH_TOKEN_FILE` | HTTP only | — | Bearer secret file. Required for HTTP |
| `MCP_ALLOWED_HOSTS` | HTTP only | — | Comma-separated Host values. Required for HTTP |
| `MCP_ALLOWED_ORIGINS` | no | empty | Comma-separated Origin values |
| `GITLAB_READ_ONLY` | no | `true` | Set `0` to register write tools |
| `GITLAB_TOOLSETS` | no | `all` | `all`, or a comma-separated list: `merge_requests`, `issues`, `work_items`, `search`, `wiki`, `core`, `repository`, `ci` |
| `GITLAB_DEFAULT_PROJECT` | no | — | Default project id or `group/project` path |
| `GITLAB_TIMEOUT_SECONDS` | no | `30` | HTTP timeout in seconds |
| `GITLAB_PER_PAGE` | no | `50` | Page size for list endpoints (1–100) |
| `GITLAB_MAX_PAGES` | no | `20` | Max pages per paginated call |
| `GITLAB_CA_BUNDLE` | no | — | Path to a CA bundle file **inside the container** for private CAs |
| `GITLAB_VERIFY_SSL` | no | `true` | Set `false` / `0` to disable TLS verification (not recommended) |

Full reference: https://github.com/pirlruc/gitlab-mcp/blob/main/docs/configuration.md.
Tool list: https://github.com/pirlruc/gitlab-mcp/blob/main/docs/tools.md.

### Private CA certificates

```bash
docker run --rm -i \
  -v /etc/ssl/certs/ca-certificates.crt:/certs/ca.crt:ro \
  -e GITLAB_CA_BUNDLE=/certs/ca.crt \
  -e GITLAB_URL \
  -e GITLAB_TOKEN \
  pirlruc/gitlab-mcp:0.2.4
```

## Cursor MCP config

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
        "pirlruc/gitlab-mcp:0.2.4"
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

## Verify a publish

```bash
cosign verify \
  --certificate-identity-regexp 'https://github.com/pirlruc/containerdevops/.github/workflows/container-publish.yml' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  pirlruc/gitlab-mcp@sha256:527454bc119b2b20756db609f03533c5b35d5ffe2a0b348f8066253897f4c2b9
```

## Source and support

- Source: https://github.com/pirlruc/gitlab-mcp
- Releases: https://github.com/pirlruc/gitlab-mcp/releases
- License: MIT
