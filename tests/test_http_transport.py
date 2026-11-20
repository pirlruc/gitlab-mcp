"""Streamable HTTP auth, health, and Host checks."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from mcp.server.mcpserver import MCPServer
from starlette.testclient import TestClient

from gitlab_mcp.config import Settings
from gitlab_mcp.http_transport import (
    StaticTokenVerifier,
    build_http_server,
    resource_url,
    run_streamable_http,
    transport_security,
)
from gitlab_mcp.server import create_server


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    """Build HTTP settings with mode-0600 secret files.

    Args:
        tmp_path: Temporary directory for secret files.
        **overrides: Settings fields to replace.

    Returns:
        Validated settings.

    """
    gitlab = tmp_path / "gitlab"
    gitlab.write_text("glpat-test\n")
    gitlab.chmod(0o600)
    auth = tmp_path / "auth"
    auth.write_text("bearer-secret\n")
    auth.chmod(0o600)
    values: dict[str, object] = {
        "gitlab_url": "https://gitlab.example.com",
        "gitlab_token_file": str(gitlab),
        "mcp_transport": "streamable-http",
        "mcp_http_host": "127.0.0.1",
        "mcp_http_port": 3333,
        "mcp_auth_token_file": str(auth),
        "mcp_allowed_hosts": "testserver",
        "mcp_allowed_origins": "http://testserver",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_verifier_compares_without_leaking_mismatch() -> None:
    """A wrong bearer is rejected and a matching one is accepted."""
    verifier = StaticTokenVerifier("expected", "http://127.0.0.1:3333")
    assert asyncio.run(verifier.verify_token("nope")) is None
    accepted = asyncio.run(verifier.verify_token("expected"))
    assert accepted is not None
    assert accepted.client_id == "mcp-client"


def test_resource_url_keeps_a_hostname() -> None:
    """A DNS name is not rewritten."""
    settings = Settings(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="token",
        mcp_http_host="mcp.lab.example",
        mcp_http_port=3333,
    )
    assert resource_url(settings) == "http://mcp.lab.example:3333"


def test_resource_url_rewrites_wildcard_bind() -> None:
    """A wildcard bind is not used as the resource URL."""
    settings = Settings(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="token",
        mcp_http_host="0.0.0.0",
        mcp_http_port=3333,
    )
    assert resource_url(settings) == "http://127.0.0.1:3333"


def test_health_is_public_and_mcp_requires_bearer(tmp_path: Path) -> None:
    """/healthz is open. /mcp requires the bearer and an allowed Host."""
    settings = _settings(tmp_path)
    server = build_http_server(settings, create_server)
    app = server.streamable_http_app(
        transport_security=transport_security(settings),
        host="127.0.0.1",
    )
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.post("/mcp").status_code == 401
        rejected = client.post(
            "/mcp",
            headers={"Authorization": "Bearer wrong", "Host": "testserver"},
        )
        assert rejected.status_code == 401
        bad_host = client.post(
            "/mcp",
            headers={
                "Authorization": "Bearer bearer-secret",
                "Host": "evil.example",
                "Content-Type": "application/json",
            },
            content=b"{}",
        )
        assert bad_host.status_code == 421
        bad_origin = client.post(
            "/mcp",
            headers={
                "Authorization": "Bearer bearer-secret",
                "Host": "testserver",
                "Origin": "http://evil.example",
                "Content-Type": "application/json",
            },
            content=b"{}",
        )
        assert bad_origin.status_code == 403


def test_run_streamable_http_uses_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The HTTP runner binds the configured host and port."""
    settings = _settings(tmp_path)
    seen: dict[str, object] = {}

    def fake_run(self: MCPServer, transport: str = "stdio", **kwargs: object) -> None:
        seen["transport"] = transport
        seen["host"] = kwargs["host"]
        seen["port"] = kwargs["port"]

    monkeypatch.setattr(MCPServer, "run", fake_run)
    run_streamable_http(settings, create_server)
    assert seen == {
        "transport": "streamable-http",
        "host": "127.0.0.1",
        "port": 3333,
    }


def test_main_selects_http(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """main() delegates when the transport is streamable HTTP."""
    settings = _settings(tmp_path)
    monkeypatch.setattr("gitlab_mcp.server.get_settings", lambda: settings)
    called: list[Settings] = []
    monkeypatch.setattr(
        "gitlab_mcp.server.run_streamable_http",
        lambda loaded, _factory: called.append(loaded),
    )
    from gitlab_mcp.server import main

    main()
    assert called == [settings]
