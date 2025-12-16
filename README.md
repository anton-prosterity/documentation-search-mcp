# Documentation Search MCP Server

This Model Context Protocol server delivers documentation search, vulnerability auditing, and project bootstrapping in one place. It runs as a long-lived process that serves requests from MCP-compatible clients such as Claude Desktop or Cursor.

## Core Capabilities
- Aggregate semantic search across 100+ documentation sources.
- Scan local Python projects for dependency vulnerabilities.
- Generate starter scaffolds (FastAPI, React) and developer environment files.
- Provide learning paths, curated code examples, and library comparisons on demand.

## Quick Start
```bash
# Requires Python 3.12+
uvx documentation-search-enhanced@latest
```
Configure your assistant to launch the server:
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": { "SERPER_API_KEY": "your_serper_api_key_here" }
    }
  }
}
```
The process stays running and listens for JSON-RPC calls; stop it with `Ctrl+C` when finished.

## Codex CLI
Add the server using Codex’s built-in MCP manager:
```bash
codex mcp add documentation-search-enhanced \
  --env SERPER_API_KEY=your_serper_api_key_here \
  -- uvx documentation-search-enhanced@latest
```
To run from a local checkout instead:
```bash
codex mcp add documentation-search-enhanced \
  --env SERPER_API_KEY=your_serper_api_key_here \
  -- uv run python src/documentation_search_enhanced/main.py
```

## Development Workflow
```bash
git clone https://github.com/antonmishel/documentation-search-mcp.git
cd documentation-search-mcp
uv sync --all-extras --all-groups  # include dev tools
echo "SERPER_API_KEY=your_key_here" > .env
uv run python src/documentation_search_enhanced/main.py
```
- Run core tests: `uv run pytest --ignore=pytest-test-project`.
- Run example FastAPI tests: `cd pytest-test-project && uv run --all-extras python -m pytest -q`.
- Lint: `uv run ruff check src`. Format: `uv run black src` (use `--check` to verify).
- Build distributions via `uv build`; `publish_to_pypi.sh` wraps the release flow.

## Configuration
Ask your assistant for the current configuration via the `get_current_config` tool, save it as `config.json`, then adjust sources or caching preferences. Validate changes locally with `uv run python src/documentation_search_enhanced/config_validator.py`. Keep secrets in `.env` rather than committing them.

## Tools at a Glance
Key MCP tools include `get_docs`, `semantic_search`, `get_learning_path`, `get_code_examples`, `scan_project_dependencies`, `generate_project_starter`, `manage_dev_environment`, `get_security_summary`, and `compare_library_security`.

## Contributing & License
Start with the contributor guide in `AGENTS.md` plus the workflow details in `CONTRIBUTING.md`. Follow Conventional Commits, document validation steps in pull requests, and update `CHANGELOG.md` for user-facing adjustments. Released under the MIT License—see `LICENSE` for the full text.
