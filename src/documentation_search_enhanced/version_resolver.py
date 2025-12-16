"""
Version resolution module for detecting installed package versions.

This module provides automatic version detection from:
- Installed packages (pip, npm)
- Project dependency files (pyproject.toml, requirements.txt, package.json)
- Runtime imports (Python __version__ attribute)
"""

import asyncio
import subprocess
import json
import re
from typing import Optional, Dict
from pathlib import Path
import sys


class VersionResolver:
    """Resolves library versions from installed packages and project files."""

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._timeout = 5  # seconds for subprocess calls

    async def resolve_version(
        self,
        library: str,
        requested_version: str,
        auto_detect: bool = True,
        project_path: str = "."
    ) -> str:
        """
        Resolve final version to use for documentation search.

        Priority:
        1. Explicit version from user (if not "latest")
        2. Auto-detected from environment (if auto_detect=True)
        3. Default "latest"

        Args:
            library: Library name
            requested_version: User-requested version
            auto_detect: Whether to auto-detect from installed packages
            project_path: Path to project for dependency file parsing

        Returns:
            Resolved version string
        """
        # Priority 1: Explicit version
        if requested_version != "latest":
            return requested_version

        # Priority 2: Auto-detection
        if auto_detect:
            cache_key = f"{library}:{project_path}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            # Try installed package detection
            installed_version = await self.detect_installed_version(library)
            if installed_version:
                self._cache[cache_key] = installed_version
                return installed_version

            # Try project dependency files
            project_version = await self.detect_from_project(library, project_path)
            if project_version:
                self._cache[cache_key] = project_version
                return project_version

        # Priority 3: Default
        return "latest"

    async def detect_installed_version(self, library: str) -> Optional[str]:
        """
        Detect version of installed package.

        Tries multiple methods:
        1. pip show (Python packages)
        2. npm list (Node packages)
        3. Python import (for Python packages)

        Args:
            library: Library/package name

        Returns:
            Version string or None if not found
        """
        # Try pip show first
        pip_version = await self._try_pip_show(library)
        if pip_version:
            return pip_version

        # Try npm list
        npm_version = await self._try_npm_list(library)
        if npm_version:
            return npm_version

        # Try Python import
        py_version = await self._try_python_import(library)
        if py_version:
            return py_version

        return None

    async def _try_pip_show(self, package: str) -> Optional[str]:
        """
        Try to get version via pip show.

        Args:
            package: Package name

        Returns:
            Version string or None
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "show", package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return None

            if proc.returncode == 0:
                output = stdout.decode()
                match = re.search(r"Version:\s*(\S+)", output)
                if match:
                    version = match.group(1)
                    # Convert to major.minor (e.g., "4.2.8" -> "4.2")
                    parts = version.split(".")
                    if len(parts) >= 2:
                        return f"{parts[0]}.{parts[1]}"
                    return version
        except Exception:
            pass
        return None

    async def _try_npm_list(self, package: str) -> Optional[str]:
        """
        Try to get version via npm list.

        Args:
            package: Package name

        Returns:
            Version string or None
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "list", package, "--depth=0", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return None

            if proc.returncode == 0:
                data = json.loads(stdout.decode())
                deps = data.get("dependencies", {})
                if package in deps:
                    version = deps[package].get("version", "")
                    # Remove semver prefixes (^, ~)
                    version = version.lstrip("^~")
                    # Convert to major.minor
                    parts = version.split(".")
                    if len(parts) >= 2:
                        return f"{parts[0]}.{parts[1]}"
                    return version
        except Exception:
            pass
        return None

    async def _try_python_import(self, package: str) -> Optional[str]:
        """
        Try to get version via Python import.

        Args:
            package: Package name

        Returns:
            Version string or None
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c",
                f"import {package}; print(getattr({package}, '__version__', ''))",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self._timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return None

            if proc.returncode == 0:
                version = stdout.decode().strip()
                if version:
                    # Convert to major.minor
                    parts = version.split(".")
                    if len(parts) >= 2:
                        return f"{parts[0]}.{parts[1]}"
                    return version
        except Exception:
            pass
        return None

    async def detect_from_project(
        self,
        library: str,
        project_path: str
    ) -> Optional[str]:
        """
        Parse project dependency files for version.

        Supports:
        - pyproject.toml
        - requirements.txt
        - package.json

        Args:
            library: Library name
            project_path: Path to project directory

        Returns:
            Version string or None
        """
        project = Path(project_path)

        # Try pyproject.toml
        pyproject = project / "pyproject.toml"
        if pyproject.exists():
            version = await self._parse_pyproject(pyproject, library)
            if version:
                return version

        # Try requirements.txt
        requirements = project / "requirements.txt"
        if requirements.exists():
            version = await self._parse_requirements(requirements, library)
            if version:
                return version

        # Try package.json
        package_json = project / "package.json"
        if package_json.exists():
            version = await self._parse_package_json(package_json, library)
            if version:
                return version

        return None

    async def _parse_pyproject(
        self,
        path: Path,
        library: str
    ) -> Optional[str]:
        """
        Parse pyproject.toml for library version.

        Args:
            path: Path to pyproject.toml
            library: Library name

        Returns:
            Version string or None
        """
        try:
            # Python 3.11+ has tomllib built-in
            import tomllib

            with open(path, "rb") as f:
                data = tomllib.load(f)

            # Check dependencies
            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                # Match library name (case-insensitive)
                if library.lower() in dep.lower():
                    # Extract version constraint (e.g., "django>=4.2")
                    match = re.search(r">=?(\d+\.\d+)", dep)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return None

    async def _parse_requirements(
        self,
        path: Path,
        library: str
    ) -> Optional[str]:
        """
        Parse requirements.txt for library version.

        Args:
            path: Path to requirements.txt
            library: Library name

        Returns:
            Version string or None
        """
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if library.lower() in line.lower():
                        # Extract version (e.g., "django>=4.2.0")
                        match = re.search(r">=?(\d+\.\d+)", line)
                        if match:
                            return match.group(1)
        except Exception:
            pass
        return None

    async def _parse_package_json(
        self,
        path: Path,
        library: str
    ) -> Optional[str]:
        """
        Parse package.json for library version.

        Args:
            path: Path to package.json
            library: Library name

        Returns:
            Version string or None
        """
        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Check dependencies and devDependencies
            for dep_type in ["dependencies", "devDependencies"]:
                deps = data.get(dep_type, {})
                if library in deps:
                    version = deps[library].lstrip("^~")
                    # Convert to major.minor
                    parts = version.split(".")
                    if len(parts) >= 2:
                        return f"{parts[0]}.{parts[1]}"
                    return version
        except Exception:
            pass
        return None

    def clear_cache(self):
        """Clear version resolution cache."""
        self._cache.clear()


# Global instance
version_resolver = VersionResolver()
