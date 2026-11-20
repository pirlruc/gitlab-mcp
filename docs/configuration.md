# Configuration

All settings are environment variables (never CLI flags for secrets).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITLAB_URL` | yes | — | Base URL of the GitLab instance (e.g. `https://gitlab.example.com`) |
| `GITLAB_TOKEN` | one of token or file | — | Personal/project access token (`read_api` for read-only; `api` for writes) |
| `GITLAB_TOKEN_FILE` | one of token or file | — | File containing the GitLab token. When set, it replaces `GITLAB_TOKEN` |
| `GITLAB_READ_ONLY` | no | `true` | Set `0` to register write tools. The default is read-only |
| `GITLAB_TOOLSETS` | no | `all` | Comma-separated toolsets, or `all` |
| `GITLAB_MAX_RESPONSE_BYTES` | no | `1048576` | Maximum JSON body. Job logs are capped at 512000 bytes |
| `MCP_TRANSPORT` | no | `stdio` | `stdio` or `streamable-http`. SSE is not supported |
| `MCP_HTTP_HOST` | no | `127.0.0.1` | Bind address for streamable HTTP |
| `MCP_HTTP_PORT` | no | `3333` | Bind port for streamable HTTP |
| `MCP_AUTH_TOKEN_FILE` | HTTP only | — | File containing the bearer secret. Required for `streamable-http`. There is no env var for this secret |
| `MCP_ALLOWED_HOSTS` | HTTP only | — | Comma-separated `Host` values. Required. Requests with another Host get HTTP 421 |
| `MCP_ALLOWED_ORIGINS` | no | empty | Comma-separated `Origin` values. A missing Origin is allowed. Any other Origin is rejected |
| `GITLAB_DEFAULT_PROJECT` | no | — | Default project id or `group/project` path |
| `GITLAB_TIMEOUT_SECONDS` | no | `30` | HTTP timeout |
| `GITLAB_PER_PAGE` | no | `50` | Page size (1–100) |
| `GITLAB_MAX_PAGES` | no | `20` | Hard cap on pages per paginated call |
| `GITLAB_CA_BUNDLE` | no | — | Path to CA bundle for private TLS CAs |
| `GITLAB_VERIFY_SSL` | no | `true` | Verify TLS certificates |

Logging goes to **stderr** so it cannot corrupt the MCP stdio framing. The
token is redacted from error messages.

`streamable-http` listens on `/mcp` and refuses to start unless
`MCP_AUTH_TOKEN_FILE` and `MCP_ALLOWED_HOSTS` are set. `GET /healthz` does not
require the bearer token and does not read secrets. The bearer check is a
static comparison, not an OAuth login.
