# gitlab-mcp (GitHub Packages)

Same image as [docker-hub.md](docker-hub.md). Not a product runtime — no `HEALTHCHECK`.

## Image

| Item | Value |
|------|--------|
| GHCR | `ghcr.io/pirlruc/gitlab-mcp` |
| Architectures | `linux/amd64`, `linux/arm64` |
| User | non-root `65532:65532` |

Debian owns the unsuffixed tags. Alpine is the `-alpine` suffix. Pin `0.2.4`
or its index digest.

### Tags

| Tag | Digest |
|-----|--------|
| `0.2.4` / `0.2` / `latest` / `0.2.4-debian` / `latest-debian` | `sha256:527454bc119b2b20756db609f03533c5b35d5ffe2a0b348f8066253897f4c2b9` |
| `0.2.4-alpine` / `0.2-alpine` / `latest-alpine` | `sha256:569c3aab2248a037e90e0669de3c4ef33f4f025e1b9fce985c29cba155f4fd8b` |
| `0.1.0` / `0.1` | `sha256:9df623d5351c9c544177a3b71db93d7ceae5f96afe89df39fa0fb876b5fa4b8e` |

`0.2.4` is the signed release.

## Authentication

The package is private. A token with `read:packages` is required.

```bash
echo "$CR_PAT" | docker login ghcr.io -u USERNAME --password-stdin
docker pull ghcr.io/pirlruc/gitlab-mcp@sha256:527454bc119b2b20756db609f03533c5b35d5ffe2a0b348f8066253897f4c2b9
```

Docker Hub serves the same tags without that login: `pirlruc/gitlab-mcp:0.2.4`.

## License

MIT. Source: https://github.com/pirlruc/gitlab-mcp
