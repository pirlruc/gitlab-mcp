# Configuration

All settings are environment variables (never CLI flags for secrets).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITLAB_URL` | yes | — | Base URL of the GitLab instance (e.g. `https://gitlab.example.com`) |
| `GITLAB_TOKEN` | yes | — | Personal/project access token (`read_api` for read-only; `api` for writes) |
| `GITLAB_READ_ONLY` | no | `false` | When `true`/`1`, write tools are not registered |
| `GITLAB_DEFAULT_PROJECT` | no | — | Default project id or `group/project` path |
| `GITLAB_TIMEOUT_SECONDS` | no | `30` | HTTP timeout |
| `GITLAB_PER_PAGE` | no | `50` | Page size (1–100) |
| `GITLAB_MAX_PAGES` | no | `20` | Hard cap on pages per paginated call |
| `GITLAB_CA_BUNDLE` | no | — | Path to CA bundle for private TLS CAs |
| `GITLAB_VERIFY_SSL` | no | `true` | Verify TLS certificates |

Logging goes to **stderr** so it cannot corrupt the MCP stdio framing. The
token is redacted from error messages.
