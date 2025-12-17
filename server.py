#!/usr/bin/env python3
"""
MCP server entrypoint for documentation-search-enhanced.

Usage examples:
- Run via Python: `.venv/bin/python server.py`
- Run via MCP CLI: `.venv/bin/mcp run -t stdio server.py:app`
- Run function entrypoint: `.venv/bin/mcp run -t stdio server.py:run`
"""

import os
import sys

# Ensure 'src' is on sys.path so the package imports work when run by file path
ROOT = os.path.dirname(__file__)
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from documentation_search_enhanced.main import mcp, main as _main  # type: ignore

# Expose server object and a callable for MCP CLI
app = mcp
run = _main

if __name__ == "__main__":
    _main()

