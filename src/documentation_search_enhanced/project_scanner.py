#!/usr/bin/env python3
"""
Scans project directories to find and parse dependency files.
"""

import os
import json
import sys
from typing import Dict, Tuple, Optional
import re
import tomllib


def _parse_requirement(req: str) -> Tuple[str, str]:
    """Parses a requirement string (e.g., 'fastapi==0.1.0' or 'django>=3.2')."""
    match = re.match(r"([a-zA-Z0-9\-_]+)\s*([~<>=!]=?)\s*([0-9\.\*a-zA-Z]+)", req)
    if match:
        name, specifier, version = match.groups()
        return name.strip(), f"{specifier}{version}"
    return req.strip(), "latest"


def parse_pyproject_toml(content: str) -> Dict[str, str]:
    """Parses dependencies from pyproject.toml content."""
    data = tomllib.loads(content)
    dependencies = data.get("project", {}).get("dependencies", [])

    parsed_deps = {}
    for req in dependencies:
        name, version = _parse_requirement(req)
        parsed_deps[name] = version

    return parsed_deps


def parse_requirements_txt(content: str) -> Dict[str, str]:
    """Parses dependencies from requirements.txt content."""
    lines = content.splitlines()
    parsed_deps = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            name, version = _parse_requirement(line)
            parsed_deps[name] = version
    return parsed_deps


def parse_package_json(content: str) -> Dict[str, str]:
    """Parses dependencies from package.json content."""
    data = json.loads(content)
    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})
    deps.update(dev_deps)
    return deps


def find_and_parse_dependencies(
    directory: str,
) -> Optional[Tuple[str, str, Dict[str, str]]]:
    """
    Finds and parses the most relevant dependency file in a directory.

    Returns:
        A tuple of (file_path, ecosystem, dependencies_dict) or None.
    """
    supported_files = {
        "pyproject.toml": ("PyPI", parse_pyproject_toml),
        "requirements.txt": ("PyPI", parse_requirements_txt),
        "package.json": ("npm", parse_package_json),
    }

    for filename, (ecosystem, parser_func) in supported_files.items():
        file_path = os.path.join(directory, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                dependencies = parser_func(content)
                return filename, ecosystem, dependencies
            except Exception as e:
                print(f"⚠️ Error parsing {filename}: {e}", file=sys.stderr)
                # Continue to the next file type if parsing fails
                continue

    return None
