# Repository Guidelines

## Project Structure & Module Organization
- Core code in `src/documentation_search_enhanced/`: `main.py` (MCP entry), `smart_search.py` (semantic search), `project_scanner.py` and `vulnerability_scanner.py` (local analysis), configs (`config_manager.py`, `config_validator.py`, `config.json`).
- Samples in `samples/`; generated demo in `my-test-fastapi-app/`.
- Regression and helpers at repo root: `demo_usage.py`, `interactive_test.py`, `test_project_scanner.py`, `test_rate_limiter.py`.

## Build, Test, and Development Commands
- Install deps: `uv sync` (includes dev extras).
- Run MCP server: `uv run python -m documentation_search_enhanced.main` (optional: set `SERPER_API_KEY` for Serper-powered search).
- Test: `uv run pytest`.
- Lint/format: `uv run ruff check src`, `uv run black src`.
- Build/publish: `uv build`, `publish_to_pypi.sh`.

## Coding Style & Naming Conventions
- Python 3.12+, 4‑space indent, clear type hints on public APIs.
- Names: files `snake_case`, classes `PascalCase`, async helpers prefixed `async_`.
- Black is authoritative; treat Ruff findings as blockers. Use scoped `# noqa` with rationale only when unavoidable.

## Testing Guidelines
- Use pytest; name tests `test_<feature>.py` in the repo root.
- Keep tests fast and isolated; prefer fixtures/mocks over external services.
- Mirror coverage patterns in `test_project_scanner.py` and `test_rate_limiter.py` to guard against regressions.

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat:`, `fix:`); emoji optional.
- PRs: link issues, summarize changes, list validation commands run (`uv run pytest`, linting), update `CHANGELOG.md` for user‑visible changes, attach screenshots/JSON when modifying tool output.

## Security & Configuration Tips
- Never commit secrets; load via `.env` (e.g., optional `SERPER_API_KEY`).
- After editing `config.json`, validate: `uv run python src/documentation_search_enhanced/config_validator.py`.
- Document new env vars in `README.md`; scope and rotate keys if exposure is suspected.
