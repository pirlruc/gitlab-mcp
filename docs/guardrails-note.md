# Guardrails note (repo-specific baseline)

Implements [PY-RUN-001](https://github.com/pirlruc/guardrails/blob/main/python/guardrails.md)
and [CI-008](https://github.com/pirlruc/guardrails/blob/main/ci/guardrails.md).

## Toolchain

| Item | Choice |
|------|--------|
| Python | 3.13 (`requires-python = ">=3.13"`) |
| Package manager | uv (`uv.lock` committed) |
| Formatter / linter | ruff (Google pydocstyle) |
| Type checker | mypy |
| Tests | pytest + pytest-cov |
| Doc coverage | interrogate ≥ 95% |
| Complexity | radon cc / mi via `scripts/quality_gates.py` |
| Security | bandit, gitleaks, semgrep, `uv audit` |

## Thresholds

Org floors live in `docs/guardrails/python/profile.thresholds.yml` (statement /
branch / doc coverage **90**). This repo is **stricter** and records values in
`[tool.gitlab_mcp.quality]` of `pyproject.toml`:

| Metric | Repo gate |
|--------|-----------|
| Statement coverage | ≥ 95 |
| Branch coverage | ≥ 95 |
| Doc coverage | ≥ 95 |
| Cyclomatic complexity max | ≤ 8 |
| Cyclomatic complexity average | ≤ 5 |
| Maintainability index min | ≥ 40 |
| Maintainability index average | ≥ 50 |

Stricter-than-org requires no entry in `docs/guardrail-deviations.yml`.

## Local parity

```bash
bash scripts/check-ci-local.sh
```

The script fails if any repo coverage value falls below the org floor.
