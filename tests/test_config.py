"""Tests for configuration loading."""

from __future__ import annotations

import pytest

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


def test_get_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings reads required env vars."""
    clear_settings_cache()
    monkeypatch.setenv("GITLAB_URL", "https://gl.example")
    monkeypatch.setenv("GITLAB_TOKEN", "secret")
    monkeypatch.setenv("GITLAB_READ_ONLY", "true")
    loaded = get_settings()
    assert loaded.gitlab_url == "https://gl.example"
    assert loaded.gitlab_read_only is True
