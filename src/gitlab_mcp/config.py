"""Environment-backed configuration for the GitLab MCP server."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded exclusively from environment variables.

    Attributes:
        gitlab_url: Base URL of the self-hosted GitLab instance.
        gitlab_token: Personal or project access token.
        gitlab_read_only: When true, write tools are not registered.
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
    gitlab_token: str = Field(..., description="GitLab access token")
    gitlab_read_only: bool = Field(default=False)
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

    @property
    def api_base(self) -> str:
        """Return the GitLab REST API v4 base URL.

        Returns:
            Absolute API base ending in ``/api/v4``.

        """
        base = str(self.gitlab_url)
        if base.endswith("/api/v4"):
            return base
        return f"{base}/api/v4"

    @property
    def verify(self) -> bool | str:
        """Return the httpx ``verify`` argument.

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
