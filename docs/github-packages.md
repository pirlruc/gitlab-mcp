# gitlab-mcp (GitHub Packages)

Same image as [docker-hub.md](docker-hub.md). Not a product runtime — no `HEALTHCHECK`.

## Image

| Item | Value |
|------|--------|
| GHCR | `ghcr.io/pirlruc/gitlab-mcp` |
| Architectures | `linux/amd64`, `linux/arm64` |
| User | non-root `65532:65532` |

### Tags

`0.1.0`, `0.1`, `latest`, and `sha-eacb0af` share one multi-arch index.

| Manifest | Digest |
|----------|--------|
| Index (`0.1.0` / `latest`) | `sha256:9df623d5351c9c544177a3b71db93d7ceae5f96afe89df39fa0fb876b5fa4b8e` |
| linux/amd64 | `sha256:b70b8437dc82bff081767550b2f9c2dfa30bbf0c14775b6f681b4efd3af0cc26` |
| linux/arm64 | `sha256:3b01f0401f06252075d72c5d5f3a56c5ce4b092a73dd6afff9c7d0e18a5e256c` |

Prefer the index digest so the client selects the architecture.

## Authentication

```bash
echo "$CR_PAT" | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/pirlruc/gitlab-mcp@sha256:9df623d5351c9c544177a3b71db93d7ceae5f96afe89df39fa0fb876b5fa4b8e
```

## License

MIT. Source: https://github.com/pirlruc/gitlab-mcp
