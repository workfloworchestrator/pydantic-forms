# CLAUDE.md

## Project

pydantic-forms: JSON schema form generation for FastAPI/Flask using Pydantic v2 models. Supports multi-step form wizards.

## Commands

```bash
# Install
uv sync --all-extras

# Test
uv run pytest tests/unit_tests
uv run pytest -n auto tests/unit_tests          # parallel
uv run pytest tests/unit_tests --cov=pydantic_forms  # coverage

# Lint/format
uv run pre-commit run --all-files        # all checks
uv run black --check .                   # formatting
uv run ruff check .                      # linting
uv run mypy pydantic_forms               # type checking

# Dependencies
uv lock                                  # regenerate uv.lock after editing pyproject.toml
uv version --bump patch                  # bump the version
```

## Code style

- Python 3.10+, Pydantic v2 (>=2.9.0)
- Packaged with uv (`uv_build` backend); `uv.lock` is committed
- Runtime deps go in `[project.dependencies]`, dev tooling in `[dependency-groups]`
- Black formatting, 120 char line length
- Ruff linting with google-style docstrings
- Strict mypy
- No relative imports (absolute only)
- Async and sync variants live in `pydantic_forms/core/`
- pytest-asyncio with `asyncio_mode=auto`
- No `break`/`continue` in for-loops -- use itertools (`takewhile`, `filter`) or early return in helpers
- No nested for-loops -- use `itertools.product()`, `chain.from_iterable()`, comprehensions, or extract helpers
- Prefer `match/case` over `isinstance` chains
- No duplicate test functions -- use `@pytest.mark.parametrize` instead

## Plugins

Install the surf-python-style hooks from https://github.com/workfloworchestrator/surf-hooks:
```
/plugin marketplace add workfloworchestrator/surf-hooks
/plugin install surf-python-style@surf-hooks
```
