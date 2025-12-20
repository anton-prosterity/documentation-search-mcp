# Documentation Search MCP Server

[![CI](https://github.com/antonmishel/documentation-search-mcp/workflows/CI%20-%20Test%20&%20Quality/badge.svg)](https://github.com/antonmishel/documentation-search-mcp/actions/workflows/ci.yml)
[![Security Scan](https://github.com/antonmishel/documentation-search-mcp/workflows/Security%20Scan/badge.svg)](https://github.com/antonmishel/documentation-search-mcp/actions/workflows/security.yml)
[![PyPI version](https://badge.fury.io/py/documentation-search-enhanced.svg)](https://pypi.org/project/documentation-search-enhanced/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server for searching documentation, scanning dependencies for vulnerabilities, and generating project boilerplate. Works with Claude Desktop, Cursor, and other MCP clients.

**📚 [Read the comprehensive tutorial](TUTORIAL.md)** for detailed examples and workflows.

## Features

- Search 190+ curated documentation sources with optional semantic vector search
- Scan Python projects for vulnerabilities (Snyk, Safety, OSV)
- Generate FastAPI and React project starters
- Learning paths and code examples

## Installation

```bash
# Recommended: use uvx (install uv from https://docs.astral.sh/uv)
uvx documentation-search-enhanced@1.9.0

# Or with pip in a virtual environment
pip install documentation-search-enhanced==1.9.0

# Optional: AI semantic search (Python 3.12 only, adds ~600MB)
pip install documentation-search-enhanced[vector]==1.9.0
```

## Configuration

### Claude Desktop

Find your uvx path: `which uvx`

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/Users/yourusername/.local/bin/uvx",
      "args": ["documentation-search-enhanced@1.9.0"],
      "env": {
        "SERPER_API_KEY": "optional_key_here"
      }
    }
  }
}
```

Replace `/Users/yourusername/.local/bin/uvx` with your actual uvx path.

### Codex CLI

```bash
# Find your uvx path first
which uvx

# Then add with full path (replace with your actual path)
codex mcp add documentation-search-enhanced \
  -- /Users/yourusername/.local/bin/uvx documentation-search-enhanced@1.9.0

# Or if uvx is in PATH:
codex mcp add documentation-search-enhanced \
  -- uvx documentation-search-enhanced@1.9.0
```

**With SERPER API Key** (enables live web search):
```bash
codex mcp add documentation-search-enhanced \
  --env SERPER_API_KEY=your_key_here \
  -- /Users/yourusername/.local/bin/uvx documentation-search-enhanced@1.9.0
```

**Without SERPER API Key** (uses prebuilt index from GitHub Releases):
```bash
codex mcp add documentation-search-enhanced \
  -- /Users/yourusername/.local/bin/uvx documentation-search-enhanced@1.9.0
```

If you get a timeout on first run, pre-download dependencies:
```bash
uvx documentation-search-enhanced@1.9.0
```

### Environment Variables

- `SERPER_API_KEY` - Optional. Enables live web search. Without it, uses prebuilt index from GitHub Releases.
- `DOCS_SITE_INDEX_AUTO_DOWNLOAD` - Set to `false` to disable automatic index downloads
- `DOCS_SITE_INDEX_PATH` - Custom path for documentation index

Set `server_config.features.real_time_search=false` in your config to disable live crawling.

## Semantic Search (Optional)

The `[vector]` extra adds semantic search using sentence-transformers (all-MiniLM-L6-v2) with hybrid reranking:

- 50% semantic similarity (cosine)
- 30% keyword matching
- 20% source authority

Only works on Python 3.12 (PyTorch limitation). Python 3.13 users get keyword-based search.

To disable vector search even when installed:
```python
semantic_search(query="FastAPI auth", libraries=["fastapi"], use_vector_rerank=False)
```

## Available Tools

Core MCP tools:
- `semantic_search` - Search documentation
- `get_docs` - Fetch specific documentation
- `get_learning_path` - Generate learning roadmap
- `get_code_examples` - Find code snippets
- `scan_project_dependencies` - Vulnerability scan
- `snyk_scan_project` - Detailed Snyk analysis
- `generate_project_starter` - Create project boilerplate
- `manage_dev_environment` - Generate docker-compose files
- `compare_library_security` - Compare library vulnerabilities

## Development

```bash
git clone https://github.com/anton-prosterity/documentation-search-mcp.git
cd documentation-search-mcp
uv sync --all-extras
uv run python -m documentation_search_enhanced.main
```

### Testing

```bash
uv run pytest --ignore=pytest-test-project  # Core tests
uv run ruff check src                       # Linting
uv run ruff format src --check              # Format check
```

### Configuration

Use the `get_current_config` tool to export current settings to `config.json`. Validate with:
```bash
uv run python src/documentation_search_enhanced/config_validator.py
```

## Contributing

See `CONTRIBUTING.md` for guidelines. Use Conventional Commits for commit messages.

## License

MIT License - see `LICENSE` for details.
