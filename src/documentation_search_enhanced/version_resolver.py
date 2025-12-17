"""Version resolution for detecting installed package versions."""

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
        self._timeout = 5

    async def resolve_version(
        self,
        library: str,
        requested_version: str,
        auto_detect: bool = True,
        project_path: str = "."
    ) -> str:
        """Resolve final version to use for documentation search.

        Priority: explicit version > auto-detected > "latest"
        """
        if requested_version != "latest":
            return requested_version

        if auto_detect:
            cache_key = f"{library}:{project_path}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            installed_version = await self.detect_installed_version(library)
            if installed_version:
                self._cache[cache_key] = installed_version
                return installed_version

            project_version = await self.detect_from_project(library, project_path)
            if project_version:
                self._cache[cache_key] = project_version
                return project_version

        return "latest"

    async def detect_installed_version(self, library: str) -> Optional[str]:
        """Detect version from pip, npm, or Python import."""
        if pip_version := await self._try_pip_show(library):
            return pip_version
        if npm_version := await self._try_npm_list(library):
            return npm_version
        if py_version := await self._try_python_import(library):
            return py_version
        return None

    async def _run_subprocess(
        self,
        *cmd: str,
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """Run subprocess with timeout handling."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout or self._timeout
            )
            if proc.returncode == 0:
                return stdout.decode().strip()
        except (asyncio.TimeoutError, Exception):
            pass
        return None

    def _to_major_minor(self, version: str) -> str:
        """Convert version to major.minor format."""
        parts = version.split(".")
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return version

    async def _try_pip_show(self, package: str) -> Optional[str]:
        """Get version via pip show."""
        output = await self._run_subprocess(sys.executable, "-m", "pip", "show", package)
        if output:
            if match := re.search(r"Version:\s*(\S+)", output):
                return self._to_major_minor(match.group(1))
        return None

    async def _try_npm_list(self, package: str) -> Optional[str]:
        """Get version via npm list."""
        output = await self._run_subprocess("npm", "list", package, "--depth=0", "--json")
        if output:
            try:
                data = json.loads(output)
                if package in data.get("dependencies", {}):
                    version = data["dependencies"][package].get("version", "").lstrip("^~")
                    return self._to_major_minor(version)
            except json.JSONDecodeError:
                pass
        return None

    async def _try_python_import(self, package: str) -> Optional[str]:
        """Get version via Python import."""
        output = await self._run_subprocess(
            sys.executable, "-c",
            f"import {package}; print(getattr({package}, '__version__', ''))"
        )
        if output:
            return self._to_major_minor(output)
        return None

    async def detect_from_project(
        self,
        library: str,
        project_path: str
    ) -> Optional[str]:
        """Parse project dependency files for version."""
        project = Path(project_path)

        if (pyproject := project / "pyproject.toml").exists():
            if version := await self._parse_pyproject(pyproject, library):
                return version

        if (requirements := project / "requirements.txt").exists():
            if version := await self._parse_requirements(requirements, library):
                return version

        if (package_json := project / "package.json").exists():
            if version := await self._parse_package_json(package_json, library):
                return version

        return None

    async def _parse_pyproject(self, path: Path, library: str) -> Optional[str]:
        """Parse pyproject.toml for library version."""
        try:
            import tomllib
            with open(path, "rb") as f:
                data = tomllib.load(f)

            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                if library.lower() in dep.lower():
                    if match := re.search(r">=?(\d+\.\d+)", dep):
                        return match.group(1)
        except Exception:
            pass
        return None

    async def _parse_requirements(self, path: Path, library: str) -> Optional[str]:
        """Parse requirements.txt for library version."""
        try:
            with open(path, "r") as f:
                for line in f:
                    if library.lower() in line.strip().lower():
                        if match := re.search(r">=?(\d+\.\d+)", line):
                            return match.group(1)
        except Exception:
            pass
        return None

    async def _parse_package_json(self, path: Path, library: str) -> Optional[str]:
        """Parse package.json for library version."""
        try:
            with open(path, "r") as f:
                data = json.load(f)

            for dep_type in ["dependencies", "devDependencies"]:
                if library in data.get(dep_type, {}):
                    version = data[dep_type][library].lstrip("^~")
                    return self._to_major_minor(version)
        except Exception:
            pass
        return None

    def clear_cache(self):
        """Clear version resolution cache."""
        self._cache.clear()


version_resolver = VersionResolver()
