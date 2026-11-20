"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from gitlab_mcp.config import Settings, clear_settings_cache, get_settings


def test_api_base_appends_v4() -> None:
    """API base appends /api/v4 when missing."""
    settings = Settings(
        gitlab_url="https://gitlab.example.com/",
        gitlab_token="token",
    )
    assert settings.api_base == "https://gitlab.example.com/api/v4"
    assert settings.gitlab_url == "https://gitlab.example.com"


def test_api_base_preserves_existing_suffix() -> None:
    """API base is unchanged when already ending in /api/v4."""
    settings = Settings(
        gitlab_url="https://gitlab.example.com/api/v4",
        gitlab_token="token",
    )
    assert settings.api_base == "https://gitlab.example.com/api/v4"


def test_verify_prefers_ca_bundle() -> None:
    """CA bundle path wins over the boolean SSL flag."""
    settings = Settings(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="token",
        gitlab_ca_bundle="/etc/ssl/custom.pem",
        gitlab_verify_ssl=False,
    )
    assert settings.verify == "/etc/ssl/custom.pem"


def test_token_file_replaces_env_token(tmp_path: Path) -> None:
    """GITLAB_TOKEN_FILE wins over GITLAB_TOKEN."""
    secret = tmp_path / "gitlab"
    secret.write_text("from-file\n")
    secret.chmod(0o600)
    settings = Settings(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="from-env",
        gitlab_token_file=str(secret),
    )
    assert settings.gitlab_access_token() == "from-file"


def test_missing_token_is_rejected() -> None:
    """Settings require a token value or a token file."""
    with pytest.raises(ValidationError, match="GITLAB_TOKEN"):
        Settings(gitlab_url="https://gitlab.example.com")


def test_secret_file_must_exist_and_be_nonempty(tmp_path: Path) -> None:
    """A missing or empty token file is rejected without echoing contents."""
    missing = tmp_path / "missing"
    with pytest.raises(ValidationError, match="cannot read secret file"):
        Settings(
            gitlab_url="https://gitlab.example.com",
            gitlab_token_file=str(missing),
        )
    empty = tmp_path / "empty"
    empty.write_text("\n")
    empty.chmod(0o600)
    with pytest.raises(ValidationError, match="secret file is empty"):
        Settings(
            gitlab_url="https://gitlab.example.com",
            gitlab_token_file=str(empty),
        )


def test_group_readable_secret_is_rejected(tmp_path: Path) -> None:
    """A loose file mode fails closed."""
    secret = tmp_path / "gitlab"
    secret.write_text("from-file\n")
    secret.chmod(0o644)
    with pytest.raises(ValidationError, match="group or other"):
        Settings(
            gitlab_url="https://gitlab.example.com",
            gitlab_token_file=str(secret),
        )


def test_access_token_rejects_an_unresolved_model() -> None:
    """A model built without validation still refuses a missing token."""
    bare = Settings.model_construct(gitlab_url="https://gitlab.example.com", gitlab_token=None)
    with pytest.raises(ValueError, match="GITLAB_TOKEN"):
        bare.gitlab_access_token()


def test_http_mode_requires_hosts_when_bearer_exists(tmp_path: Path) -> None:
    """A bearer file without MCP_ALLOWED_HOSTS is rejected."""
    gitlab = tmp_path / "gitlab"
    gitlab.write_text("glpat\n")
    gitlab.chmod(0o600)
    auth = tmp_path / "auth"
    auth.write_text("bearer\n")
    auth.chmod(0o600)
    with pytest.raises(ValidationError, match="MCP_ALLOWED_HOSTS"):
        Settings(
            gitlab_url="https://gitlab.example.com",
            gitlab_token_file=str(gitlab),
            mcp_transport="streamable-http",
            mcp_auth_token_file=str(auth),
        )


def test_http_mode_requires_bearer_file_and_hosts(tmp_path: Path) -> None:
    """Streamable HTTP refuses to start without a bearer file and Host list."""
    gitlab = tmp_path / "gitlab"
    gitlab.write_text("glpat\n")
    gitlab.chmod(0o600)
    with pytest.raises(ValidationError, match="MCP_AUTH_TOKEN_FILE"):
        Settings(
            gitlab_url="https://gitlab.example.com",
            gitlab_token_file=str(gitlab),
            mcp_transport="streamable-http",
        )


def test_get_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings reads required env vars."""
    clear_settings_cache()
    monkeypatch.setenv("GITLAB_URL", "https://gl.example")
    monkeypatch.setenv("GITLAB_TOKEN", "secret")
    monkeypatch.setenv("GITLAB_READ_ONLY", "true")
    loaded = get_settings()
    assert loaded.gitlab_url == "https://gl.example"
    assert loaded.gitlab_read_only is True
