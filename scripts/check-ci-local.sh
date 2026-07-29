#!/usr/bin/env bash
# Local CI parity (CI-008). Reads org floors from docs/guardrails/python/profile.thresholds.yml
# and overlays stricter repo values from [tool.gitlab_mcp.quality] in pyproject.toml.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

ORG_THRESHOLDS="${ROOT}/docs/guardrails/python/profile.thresholds.yml"
if [[ ! -f "${ORG_THRESHOLDS}" ]]; then
  echo "Missing ${ORG_THRESHOLDS}; init the guardrails submodule first." >&2
  exit 1
fi

mapfile -t THRESH < <(
  uv run python - <<'PY'
from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

root = Path(".")
org = yaml.safe_load((root / "docs/guardrails/python/profile.thresholds.yml").read_text())
with (root / "pyproject.toml").open("rb") as handle:
    repo = tomllib.load(handle)["tool"]["gitlab_mcp"]["quality"]

# Coverage / doc: repo must be >= org floor (higher is stricter).
# Complexity max / avg max: repo must be <= org floor (lower is stricter).
# MI min / avg min: repo must be >= org floor (higher is stricter).
ge_pairs = [
    ("statement_coverage", "statement_coverage"),
    ("branch_coverage", "branch_coverage"),
    ("doc_coverage", "doc_coverage"),
    ("min_maintainability_index", "maintainability_min"),
    ("avg_maintainability_index", "maintainability_avg_min"),
]
le_pairs = [
    ("max_cyclomatic_complexity", "cyclomatic_max"),
    ("avg_cyclomatic_complexity", "cyclomatic_avg_max"),
]
for org_key, repo_key in ge_pairs:
    org_val = float(org[org_key])
    repo_val = float(repo[repo_key])
    if repo_val < org_val:
        raise SystemExit(
            f"Repo {repo_key}={repo_val} is below org floor {org_key}={org_val}"
        )
    print(f"{repo_key}={repo_val}")
for org_key, repo_key in le_pairs:
    org_val = float(org[org_key])
    repo_val = float(repo[repo_key])
    if repo_val > org_val:
        raise SystemExit(
            f"Repo {repo_key}={repo_val} is looser than org floor {org_key}={org_val}"
        )
    print(f"{repo_key}={repo_val}")
PY
)

declare -A GATE
for item in "${THRESH[@]}"; do
  key="${item%%=*}"
  GATE["${key}"]="${item#*=}"
done

echo "==> ruff"
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts

echo "==> mypy"
uv run mypy -p gitlab_mcp -p tests

echo "==> pylint"
uv run pylint src/gitlab_mcp scripts/quality_gates.py

echo "==> radon complexity / maintainability"
uv run radon cc -j src > radon_cc.json
uv run radon mi -j src > radon_mi.json
uv run python scripts/quality_gates.py

echo "==> pytest (coverage >= ${GATE[statement_coverage]})"
uv run pytest \
  --cov=src/gitlab_mcp \
  --cov-branch \
  --cov-fail-under="${GATE[statement_coverage]}"

echo "==> interrogate (doc coverage >= ${GATE[doc_coverage]})"
uv run interrogate -vv --fail-under="${GATE[doc_coverage]}" src

echo "==> bandit"
uv run bandit -c pyproject.toml -r src -q

echo "==> uv audit"
uv audit --preview-features audit || uv audit

echo "All local CI parity checks passed."
