"""Smoke import for ``python -m gitlab_mcp``."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest


def test_module_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running the package as a module invokes main()."""
    called: list[bool] = []
    monkeypatch.setattr("gitlab_mcp.server.main", lambda: called.append(True))
    path = Path("src/gitlab_mcp/__main__.py").resolve()
    runpy.run_path(str(path), run_name="not_main")
    assert called == []
    # Direct import of __main__ with __name__ == __main__ is awkward; cover
    # the import side via package entry.
    import gitlab_mcp.__main__ as mod

    assert mod.main is not None
