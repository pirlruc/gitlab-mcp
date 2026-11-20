# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-11-20

### Fixed

- Image publish follows a containerdevops pin that removes the previous
  platform image before the arm64 smoke pull.

## [0.2.1] - 2026-11-20

### Fixed

- The image publish smoke command imports the package without a quoted
  `python -c` program. The publisher splits that command on spaces.

## [0.2.0] - 2026-11-20

### Changed

- Read-only is the default. Set `GITLAB_READ_ONLY=0` to register write tools.
- List tools report `truncated` and `next_page` instead of a silently cut list.

### Added

- `MCP_TRANSPORT=streamable-http` on port 3333, with a file-backed bearer token, Host and Origin checks, `GITLAB_TOKEN_FILE`, and `GET /healthz`.
- Read toolsets for core, repository, CI, issues, work items, search, and wikis. `GITLAB_TOOLSETS` limits which sets are registered.
- `create_merge_request` when writes are enabled. Merge and close stay unavailable.
- Alpine image `Dockerfile.alpine` published as the `-alpine` tags. Debian keeps the unsuffixed tags.
- Initial MCP server scaffold with GitLab merge request read and safe-update tools.
