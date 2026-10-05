"""Environment-backed configuration for the GitLab MCP server."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def split_csv(value: str) -> list[str]:
    """Split a comma-separated setting into stripped items.

    Args:
        value: Raw environment value.

    Returns:
        Non-empty items.

    """
    return [item.strip() for item in value.split(",") if item.strip()]


def read_secret_file(path: str) -> str:
    """Read a secret file without including its contents in errors.

    Args:
        path: Filesystem path.

    Returns:
        Stripped file contents.

    Raises:
        ValueError: If the file cannot be read or is empty.

    """
    file_path = Path(path)
    try:
        mode = file_path.stat().st_mode
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read secret file: {exc.strerror}") from exc
    if mode & 0o077:
        logger.warning("file %s mode allows group or other access", path)
    secret = text.strip()
    if not secret:
        raise ValueError("secret file is empty")
    return secret


def _require_http_controls(settings: Settings) -> None:
    """Fail closed when HTTP mode has no bearer file or Host allow-list.

    Args:
        settings: Validated settings.

    Raises:
        ValueError: If HTTP controls are missing or the bearer file is unusable.

    """
    if not settings.mcp_auth_token_file:
        raise ValueError("MCP_AUTH_TOKEN_FILE is required when MCP_TRANSPORT=streamable-http")
    if not split_csv(settings.mcp_allowed_hosts):
        raise ValueError("MCP_ALLOWED_HOSTS is required when MCP_TRANSPORT=streamable-http")
    read_secret_file(settings.mcp_auth_token_file)


class Settings(BaseSettings):
    """Runtime settings loaded exclusively from environment variables.

    Attributes:
        gitlab_url: Base URL of the self-hosted GitLab instance.
        gitlab_token: Personal or project access token.
        gitlab_token_file: Path to a file containing the GitLab token.
        gitlab_read_only: When true, write tools are not registered.
        mcp_transport: ``stdio`` or ``streamable-http``.
        mcp_http_host: Bind address for streamable HTTP.
        mcp_http_port: Bind port for streamable HTTP.
        mcp_auth_token_file: Bearer secret file, required for HTTP.
        mcp_allowed_hosts: Comma-separated Host values allowed on HTTP.
        mcp_allowed_origins: Comma-separated Origin values allowed on HTTP.
        gitlab_default_project: Optional default project id or path.
        gitlab_timeout_seconds: HTTP request timeout in seconds.
        gitlab_per_page: Page size for paginated list endpoints.
        gitlab_max_pages: Hard cap on pages fetched per request.
        gitlab_ca_bundle: Optional path to a CA bundle for private CAs.
        gitlab_verify_ssl: Whether to verify TLS certificates.

    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gitlab_url: str = Field(..., description="GitLab base URL")
    gitlab_token: str | None = Field(default=None, description="GitLab access token")
    gitlab_token_file: str | None = Field(default=None)
    gitlab_read_only: bool = Field(default=False)
    mcp_transport: Literal["stdio", "streamable-http"] = Field(default="stdio")
    mcp_http_host: str = Field(default="127.0.0.1")
    mcp_http_port: int = Field(default=3333, ge=1, le=65535)
    mcp_auth_token_file: str | None = Field(default=None)
    mcp_allowed_hosts: str = Field(default="")
    mcp_allowed_origins: str = Field(default="")
    gitlab_default_project: str | None = Field(default=None)
    gitlab_timeout_seconds: float = Field(default=30.0, gt=0)
    gitlab_per_page: int = Field(default=50, ge=1, le=100)
    gitlab_max_pages: int = Field(default=20, ge=1)
    gitlab_ca_bundle: str | None = Field(default=None)
    gitlab_verify_ssl: bool = Field(default=True)

    @field_validator("gitlab_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        """Normalize the GitLab base URL.

        Args:
            value: Raw URL from the environment.

        Returns:
            URL without a trailing slash.

        """
        return value.rstrip("/")

    @model_validator(mode="after")
    def _resolve_secrets(self) -> Settings:
        """Load token files and refuse an HTTP listener without auth.

        Returns:
            The same settings instance.

        Raises:
            ValueError: If the GitLab token or HTTP controls are missing.

        """
        if self.gitlab_token_file:
            self.gitlab_token = read_secret_file(self.gitlab_token_file)
        if not self.gitlab_token:
            raise ValueError("GITLAB_TOKEN or GITLAB_TOKEN_FILE is required")
        if self.mcp_transport == "streamable-http":
            _require_http_controls(self)
        return self

    def gitlab_access_token(self) -> str:
        """Return the resolved GitLab token.

        Returns:
            Token from the environment or from ``GITLAB_TOKEN_FILE``.

        Raises:
            ValueError: If no token was configured.

        """
        if not self.gitlab_token:
            raise ValueError("GITLAB_TOKEN or GITLAB_TOKEN_FILE is required")
        return self.gitlab_token

    @property
    def api_base(self) -> str:
        """GitLab REST API v4 base URL.

        Returns:
            Absolute API base ending in ``/api/v4``.

        """
        base = str(self.gitlab_url)
        if base.endswith("/api/v4"):
            return base
        return f"{base}/api/v4"

    @property
    def verify(self) -> bool | str:
        """TLS verify setting passed to httpx.

        Returns:
            CA bundle path when set, otherwise the boolean SSL flag.

        """
        if self.gitlab_ca_bundle:
            return self.gitlab_ca_bundle
        return self.gitlab_verify_ssl


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings from the environment.

    Returns:
        Validated :class:`Settings` instance.

    """
    return Settings()  # type: ignore[call-arg]


def clear_settings_cache() -> None:
    """Clear the cached settings (for tests)."""
    get_settings.cache_clear()
