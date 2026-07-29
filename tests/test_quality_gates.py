"""Tests for the radon quality gate script."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts import quality_gates as qg


def test_collect_cc_and_mi(tmp_path: Path) -> None:
    """Collectors extract numeric samples and ignore bools."""
    del tmp_path
    cc = {
        "a.py": [
            {"name": "f", "complexity": 3},
            {"name": "g", "complexity": True},
        ],
    }
    mi = {
        "a.py": {"mi": 65.5},
        "b.py": 40,
        "c.py": {"mi": False},
    }
    cc_values = qg.collect_cc_values(cc)
    mi_values = qg.collect_mi_values(mi)
    assert cc_values == [("a.py:f", 3.0)]
    assert ("a.py", 65.5) in mi_values
    assert ("b.py", 40.0) in mi_values
    assert all(name != "c.py" for name, _ in mi_values)


def test_evaluate_passes(tmp_path: Path) -> None:
    """Healthy metrics pass all gates."""
    del tmp_path
    thresholds: dict[str, float] = {
        "cyclomatic_max": 8.0,
        "cyclomatic_avg_max": 5.0,
        "maintainability_min": 40.0,
        "maintainability_avg_min": 50.0,
    }
    failures = qg.evaluate(
        [("a.py:f", 2.0), ("a.py:g", 3.0)],
        [("a.py", 70.0), ("b.py", 60.0)],
        thresholds,
    )
    assert failures == []


def test_evaluate_fails_on_max_cc() -> None:
    """High max CC produces a failure naming the offender."""
    thresholds: dict[str, float] = {
        "cyclomatic_max": 8.0,
        "cyclomatic_avg_max": 5.0,
        "maintainability_min": 40.0,
        "maintainability_avg_min": 50.0,
    }
    failures = qg.evaluate(
        [("a.py:f", 9.0)],
        [("a.py", 70.0)],
        thresholds,
    )
    assert any("CC max" in item for item in failures)


def test_main_with_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main() reads artifacts and returns 0 on success."""
    cc_path = tmp_path / "radon_cc.json"
    mi_path = tmp_path / "radon_mi.json"
    cc_path.write_text(json.dumps({"a.py": [{"name": "f", "complexity": 2}]}))
    mi_path.write_text(json.dumps({"a.py": {"mi": 80}}))
    monkeypatch.setattr(qg, "DEFAULT_CC_JSON", cc_path)
    monkeypatch.setattr(qg, "DEFAULT_MI_JSON", mi_path)

    def _thresholds(path: Path | None = None) -> dict[str, float]:
        del path
        return {
            "cyclomatic_max": 8.0,
            "cyclomatic_avg_max": 5.0,
            "maintainability_min": 40.0,
            "maintainability_avg_min": 50.0,
        }

    monkeypatch.setattr(qg, "load_thresholds", _thresholds)
    assert qg.main([]) == 0
