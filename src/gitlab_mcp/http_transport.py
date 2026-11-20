"""Streamable HTTP transport with a static bearer token.

SSE is not offered. A listener without a bearer file or a Host allow-list
refuses to start. ``/healthz`` does not require the bearer token and does not
read secrets.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
from collections.abc import Callable

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import JSONResponse

from gitlab_mcp.config import Settings, read_secret_file, split_csv


class StaticTokenVerifier:
    """Compare a bearer token to a file-backed secret."""

    def __init__(self, expected: str, resource: str) -> None:
        """Store the expected bearer secret.

        Args:
            expected: Secret read from ``MCP_AUTH_TOKEN_FILE``.
            resource: Resource URL the token is issued for.

        """
        self._expected = expected
        self._resource = resource

    async def verify_token(self, token: str) -> AccessToken | None:
        """Accept the configured bearer token.

        Args:
            token: Value from the Authorization header.

        Returns:
            An access token when the bearer matches, otherwise ``None``.

        """
        presented = hashlib.sha256(token.encode()).digest()
        expected = hashlib.sha256(self._expected.encode()).digest()
        if not hmac.compare_digest(presented, expected):
            return None
        return AccessToken(
            token=token,
            client_id="mcp-client",
            scopes=[],
            resource=self._resource,
        )


def resource_url(settings: Settings) -> str:
    """Build the resource URL the SDK requires for bearer auth.

    Args:
        settings: Runtime settings.

    Returns:
        An HTTP URL. ``0.0.0.0`` and ``::`` become ``127.0.0.1``.

    """
    host = _resource_host(settings.mcp_http_host)
    return f"http://{host}:{settings.mcp_http_port}"


def _resource_host(host: str) -> str:
    """Map an unspecified bind address to loopback for the resource URL.

    Args:
        host: Configured bind address.

    Returns:
        Loopback when the bind address is unspecified, otherwise ``host``.

    """
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host
    if address.is_unspecified:
        return "127.0.0.1"
    return host


async def healthz(_request: Request) -> JSONResponse:
    """Report process liveness without reading secrets.

    Returns:
        JSON ``{"status": "ok"}``.

    """
    return JSONResponse({"status": "ok"})


def build_http_server(
    settings: Settings,
    factory: Callable[..., MCPServer],
) -> MCPServer:
    """Build a server that requires a bearer token on ``/mcp``.

    Args:
        settings: Settings already validated for HTTP mode.
        factory: ``create_server`` from the server module.

    Returns:
        Server with ``/healthz`` and bearer auth configured.

    """
    secret = read_secret_file(settings.mcp_auth_token_file or "")
    url = AnyHttpUrl(resource_url(settings))
    auth = AuthSettings(
        issuer_url=url,
        resource_server_url=url,
        required_scopes=[],
        validate_token_resource=True,
    )
    server = factory(
        settings,
        auth=auth,
        token_verifier=StaticTokenVerifier(secret, str(url)),
    )
    server.custom_route("/healthz", methods=["GET"], include_in_schema=False)(healthz)
    return server


def transport_security(settings: Settings) -> TransportSecuritySettings:
    """Host and Origin allow-lists for DNS-rebinding protection.

    Args:
        settings: Runtime settings.

    Returns:
        Security settings with protection enabled.

    """
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=split_csv(settings.mcp_allowed_hosts),
        allowed_origins=split_csv(settings.mcp_allowed_origins),
    )


def run_streamable_http(
    settings: Settings,
    factory: Callable[..., MCPServer],
) -> None:
    """Serve MCP on streamable HTTP until the process is stopped.

    Args:
        settings: Runtime settings.
        factory: ``create_server`` from the server module.

    """
    server = build_http_server(settings, factory)
    server.run(
        transport="streamable-http",
        host=settings.mcp_http_host,
        port=settings.mcp_http_port,
        transport_security=transport_security(settings),
    )
