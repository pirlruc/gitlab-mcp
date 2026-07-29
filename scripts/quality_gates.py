#!/usr/bin/env python3
"""Evaluate radon cyclomatic complexity and maintainability gates.

Reads ``radon_cc.json`` and ``radon_mi.json`` (produced by ``radon cc -j`` /
``radon mi -j``) and enforces thresholds from ``[tool.gitlab_mcp.quality]``
in ``pyproject.toml``.
"""

from __future__ import annotations

import json
import statistics
import sys
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CC_JSON = REPO_ROOT / "radon_cc.json"
DEFAULT_MI_JSON = REPO_ROOT / "radon_mi.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _as_number(value: Any) -> float | None:
    """Coerce a JSON value to float, excluding bools.

    Args:
        value: Raw JSON value.

    Returns:
        Float when numeric, otherwise ``None``.

    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def collect_cc_values(data: dict[str, Any]) -> list[tuple[str, float]]:
    """Collect ``(qualified_name, complexity)`` pairs from radon cc JSON.

    Args:
        data: Mapping of file path to block list.

    Returns:
        List of named complexity values.

    """
    values: list[tuple[str, float]] = []
    for file_path, blocks in data.items():
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            complexity = _as_number(block.get("complexity"))
            if complexity is None:
                continue
            name = str(block.get("name", "<unknown>"))
            values.append((f"{file_path}:{name}", complexity))
    return values


def collect_mi_values(data: dict[str, Any]) -> list[tuple[str, float]]:
    """Collect ``(file_path, mi)`` pairs from radon mi JSON.

    Args:
        data: Mapping of file path to MI entry.

    Returns:
        List of named maintainability values.

    """
    values: list[tuple[str, float]] = []
    for file_path, entry in data.items():
        mi = _as_number(entry.get("mi")) if isinstance(entry, dict) else _as_number(entry)
        if mi is not None:
            values.append((file_path, mi))
    return values


def load_thresholds(path: Path = PYPROJECT) -> dict[str, float]:
    """Load quality thresholds from pyproject.toml.

    Args:
        path: Path to ``pyproject.toml``.

    Returns:
        Threshold mapping.

    Raises:
        SystemExit: If the quality table is missing.

    """
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    quality = data.get("tool", {}).get("gitlab_mcp", {}).get("quality")
    if not isinstance(quality, dict):
        raise SystemExit("Missing [tool.gitlab_mcp.quality] in pyproject.toml")
    return {key: float(value) for key, value in quality.items()}


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk.

    Args:
        path: JSON file path.

    Returns:
        Parsed object.

    Raises:
        SystemExit: If the file is missing or not an object.

    """
    if not path.is_file():
        raise SystemExit(f"Missing radon artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected object in {path}")
    return payload


def evaluate(
    cc_values: list[tuple[str, float]],
    mi_values: list[tuple[str, float]],
    thresholds: dict[str, float],
) -> list[str]:
    """Evaluate CC and MI gates.

    Args:
        cc_values: Named cyclomatic complexity samples.
        mi_values: Named maintainability samples.
        thresholds: Gate thresholds from pyproject.

    Returns:
        List of failure messages (empty when all gates pass).

    """
    failures: list[str] = []
    if not cc_values:
        failures.append("No cyclomatic complexity samples found")
        return failures
    if not mi_values:
        failures.append("No maintainability index samples found")
        return failures

    cc_nums = [value for _, value in cc_values]
    mi_nums = [value for _, value in mi_values]
    cc_max = max(cc_nums)
    cc_avg = statistics.fmean(cc_nums)
    mi_min = min(mi_nums)
    mi_avg = statistics.fmean(mi_nums)

    print(f"CC max={cc_max:.2f} avg={cc_avg:.2f}")
    print(f"MI min={mi_min:.2f} avg={mi_avg:.2f}")

    if cc_max > thresholds["cyclomatic_max"]:
        offenders = [
            f"  {name}={value:.1f}"
            for name, value in cc_values
            if value > thresholds["cyclomatic_max"]
        ]
        failures.append(
            f"CC max {cc_max:.1f} > {thresholds['cyclomatic_max']:.0f}\n" + "\n".join(offenders),
        )
    if cc_avg > thresholds["cyclomatic_avg_max"]:
        failures.append(
            f"CC avg {cc_avg:.2f} > {thresholds['cyclomatic_avg_max']:.0f}",
        )
    if mi_min < thresholds["maintainability_min"]:
        offenders = [
            f"  {name}={value:.1f}"
            for name, value in mi_values
            if value < thresholds["maintainability_min"]
        ]
        failures.append(
            f"MI min {mi_min:.1f} < {thresholds['maintainability_min']:.0f}\n"
            + "\n".join(offenders),
        )
    if mi_avg < thresholds["maintainability_avg_min"]:
        failures.append(
            f"MI avg {mi_avg:.2f} < {thresholds['maintainability_avg_min']:.0f}",
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (unused; reserved for future flags).

    Returns:
        Process exit code (0 on success).

    """
    del argv  # reserved
    thresholds = load_thresholds()
    cc_values = collect_cc_values(read_json(DEFAULT_CC_JSON))
    mi_values = collect_mi_values(read_json(DEFAULT_MI_JSON))
    failures = evaluate(cc_values, mi_values, thresholds)
    if failures:
        print("QUALITY GATE FAILURES:", file=sys.stderr)
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("All complexity / maintainability gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
