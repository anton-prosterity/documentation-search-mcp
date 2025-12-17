# Documentation Search MCP Server

[![CI](https://github.com/antonmishel/documentation-search-mcp/workflows/CI%20-%20Test%20&%20Quality/badge.svg)](https://github.com/antonmishel/documentation-search-mcp/actions/workflows/ci.yml)
[![Security Scan](https://github.com/antonmishel/documentation-search-mcp/workflows/Security%20Scan/badge.svg)](https://github.com/antonmishel/documentation-search-mcp/actions/workflows/security.yml)
[![PyPI version](https://badge.fury.io/py/documentation-search-enhanced.svg)](https://pypi.org/project/documentation-search-enhanced/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This Model Context Protocol server delivers documentation search, vulnerability auditing, and project bootstrapping in one place. It runs as a long-lived process that serves requests from MCP-compatible clients such as Claude Desktop or Cursor.

## Core Capabilities
- **AI-Powered Semantic Search**: Vector embeddings + hybrid reranking across 100+ documentation sources for superior relevance.
- **Security-First Approach**: Scan local Python projects for dependency vulnerabilities with multi-tool analysis.
- **Project Scaffolding**: Generate production-ready starters (FastAPI, React) and developer environment files.
- **Developer Productivity**: Learning paths, curated code examples, and library security comparisons on demand.

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
      "args": ["documentation-search-enhanced@latest"]
    }
  }
}
```
No API key is required. Optionally set `SERPER_API_KEY` to use Serper-powered search.
Without it, the server uses a prebuilt docs index (auto-downloaded from GitHub Releases on startup) plus on-site docs search (MkDocs/Sphinx indexes when available).
Control the download with `DOCS_SITE_INDEX_AUTO_DOWNLOAD`, `DOCS_SITE_INDEX_MAX_AGE_HOURS`, `DOCS_SITE_INDEX_URL(S)`, and `DOCS_SITE_INDEX_PATH`.
Set `server_config.features.real_time_search=false` to avoid any live crawling and rely only on the downloaded index.
The process stays running and listens for JSON-RPC calls; stop it with `Ctrl+C` when finished.

## Codex CLI
Add the server using Codex’s built-in MCP manager:
```bash
codex mcp add documentation-search-enhanced \
  -- uvx documentation-search-enhanced@latest
```
To run from a local checkout instead:
```bash
codex mcp add documentation-search-enhanced \
  -- bash -lc 'cd /path/to/documentation-search-mcp && uv run python -m documentation_search_enhanced.main'
```

## Development Workflow
```bash
git clone https://github.com/anton-prosterity/documentation-search-mcp.git
cd documentation-search-mcp
uv sync --all-extras --all-groups  # include dev tools
# Optional: enable Serper-powered search
# echo "SERPER_API_KEY=your_key_here" > .env
uv run python -m documentation_search_enhanced.main
```
- Run core tests: `uv run pytest --ignore=pytest-test-project`.
- Run example FastAPI tests: `cd pytest-test-project && uv run --all-extras python -m pytest -q`.
- Lint: `uv run ruff check src`. Format: `uv run black src` (use `--check` to verify).
- Build distributions via `uv build`; `publish_to_pypi.sh` wraps the release flow.

## Configuration
Ask your assistant for the current configuration via the `get_current_config` tool, save it as `config.json`, then adjust sources or caching preferences. Validate changes locally with `uv run python src/documentation_search_enhanced/config_validator.py`. Keep secrets in `.env` rather than committing them.

## AI-Powered Semantic Search
The server now features **vector-based semantic search** with hybrid reranking for significantly improved relevance:

### How It Works
- **Vector Embeddings**: Uses sentence-transformers (all-MiniLM-L6-v2) to generate 384-dimensional semantic embeddings
- **Hybrid Scoring**: Combines three signals with configurable weights:
  - Semantic similarity (50%): True meaning-based matching via cosine similarity
  - Keyword relevance (30%): Precise term matching for specific queries
  - Source authority (20%): Official docs, code examples, and URL quality signals
- **FAISS Index**: Lightning-fast similarity search over large documentation corpora

### Benefits
- **Better Understanding**: Finds semantically related content even with different terminology
- **Improved Ranking**: Hybrid approach balances semantic understanding with keyword precision
- **Production Ready**: Compact 120MB model, efficient L2-normalized embeddings
- **Flexible**: Enable/disable vector reranking with `use_vector_rerank` parameter

### Usage
Vector reranking is **enabled by default** in `semantic_search`. To disable:
```python
semantic_search(query="FastAPI auth", libraries=["fastapi"], use_vector_rerank=False)
```

This feature addresses the #1 competitive gap vs Context7 while maintaining our security and scaffolding advantages.

## Tools at a Glance
Key MCP tools include `get_docs`, `semantic_search`, `get_learning_path`, `get_code_examples`, `scan_project_dependencies`, `generate_project_starter`, `manage_dev_environment`, `get_security_summary`, and `compare_library_security`.

## Contributing & License
Start with the contributor guide in `AGENTS.md` plus the workflow details in `CONTRIBUTING.md`. Follow Conventional Commits, document validation steps in pull requests, and update `CHANGELOG.md` for user-facing adjustments. Released under the MIT License—see `LICENSE` for the full text.
