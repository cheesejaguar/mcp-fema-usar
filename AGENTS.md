# Repository Guidelines

## Project Structure & Modules
- `fema_usar_mcp/`: Core package (tools, models, integrations, server entrypoints).
- `app/`: Optional FastAPI HTTP API (`app.main`).
- `tests/`: Pytest suite with markers (`unit`, `integration`, `slow`, etc.).
- `resources/`: ICS forms, reference documents, data catalogs.
- `docs/`, `deployment/`: Architecture and ops docs.

## Build, Run, and Test
- Install (dev): `pip install -e .[dev]` then `pre-commit install`.
- Run MCP server: `fema-usar-mcp` (or `python -m fema_usar_mcp.fastmcp_server`).
- Run HTTP API: `fema-usar-http` (or `python -m app.main`).
- Tests: `pytest` (all), `pytest -m unit`, `pytest --cov=fema_usar_mcp`.
- Lint/format: `ruff --fix .` and `ruff format .`; types: `mypy fema_usar_mcp`.
- Docker (optional): `docker build -t usar-mcp .` then `docker run -p 8000:8000 usar-mcp`.

## Coding Style & Naming
- Python 3.11+, 4‑space indents, line length 88.
- Strings: double quotes; imports sorted (ruff/isort).
- Types: required for public functions; mypy strict settings enabled.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Run `pre-commit run -a` before pushing (ruff, black, mypy, bandit, etc.).

## Testing Guidelines
- Framework: Pytest with markers: `unit`, `integration`, `slow`, `requires_network`, `requires_auth`, `simulation`.
- Files: `tests/test_*.py`; names: `test_*` functions, arrange‑act‑assert.
- Coverage: target 90%+ for new/changed code; include edge/error paths.
- Avoid external calls unless marked; use fixtures/mocks in `conftest.py`.

## Commit & PR Guidelines
- Conventional Commits: `feat:`, `fix:`, `style:`, etc. (see `git log`).
- PRs must include: clear description, linked issue, test coverage, and any screenshots/logs for API/UI changes.
- Keep diffs focused; update docs when behavior or interfaces change.

## Security & Configuration
- Never commit secrets; prefer env vars and `example_config.json` as reference.
- Run `bandit -c pyproject.toml` or via pre‑commit for security checks.
- Mark tests needing network/auth accordingly to keep CI deterministic.

## Quick Examples
- Start MCP: `fema-usar-mcp`
- Run unit tests only: `pytest -m unit`
- Auto-fix style: `ruff --fix . && ruff format .`
