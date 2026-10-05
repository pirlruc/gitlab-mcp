# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-05

### Added

- `MCP_TRANSPORT=streamable-http` on port 3333, with a file-backed bearer token, Host and Origin checks, `GITLAB_TOKEN_FILE`, and `GET /healthz`.
- Initial MCP server scaffold with GitLab merge request read and safe-update tools.
