# Version Parameter Implementation Plan

**Created:** 2025-12-16
**Status:** Planning Phase
**Estimated Effort:** 6-8 hours for full implementation, 2-3 hours for MVP

---

## Executive Summary

Add version-specific documentation search capabilities to the documentation-search-enhanced MCP server. This feature allows users to search documentation for specific library versions (e.g., Django 4.2 vs 5.0), addressing a key competitive gap identified when comparing to Upstash Context7.

### Goals
1. Add `version` parameter to all documentation search tools
2. Support auto-detection of installed package versions
3. Maintain backward compatibility (default: `version="latest"`)
4. Handle version-specific URL templates for libraries that support it
5. Gracefully degrade for libraries without version-specific docs

---

## Background & Motivation

### Current State
- All doc tools search "latest" documentation only
- No way to specify version (e.g., "Django 4.2 authentication")
- 39 libraries in config.json use `/stable/` or `/latest/` in URLs
- Snyk integration already has version parameter as reference (line 2587)

### Competitive Analysis: Upstash Context7
Context7 provides version-specific docs as a core feature:
- `resolve-library-id("django")` → returns versioned library IDs
- `get-library-docs(library_id, version, max_tokens)`
- Users can request specific versions in prompts

### Value Proposition
- **Accuracy**: Search docs matching user's installed version
- **Relevance**: Avoid deprecated API confusion (e.g., React class vs hooks)
- **Developer Experience**: Auto-detect from project dependencies
- **Competitive Parity**: Match Context7's key differentiator

---

## Architecture Overview

### Three-Tier Version Resolution Strategy

```
User Request → Version Resolution → URL Construction → Search Execution
     ↓               ↓                    ↓                  ↓
"django auth"   1. Explicit:         Template:        site:docs.django...
version="4.2"   user provided        /en/{version}/   version 4.2

                2. Auto-detect:      OR
                pip show django
                                     Append to query:
                3. Default:          + " version 4.2"
                "latest"
```

### Components to Build

1. **Version Resolver Module** (`version_resolver.py`)
   - Detect installed versions via pip/npm
   - Parse project dependency files
   - Validate version strings
   - Cache version lookups

2. **URL Template System** (config.json enhancement)
   - Add `version_url_template` field
   - Add `version_pattern` for validation
   - Add `default_version` field

3. **Tool Signature Updates** (main.py)
   - Add `version: str = "latest"` parameter
   - Add `auto_detect_version: bool = True` option
   - Update tool docstrings

4. **Search Query Enhancement**
   - Inject version into search queries when no template exists
   - Modify `process_library_search()` function

---

## Implementation Phases

### Phase 1: Foundation (MVP - 2-3 hours)

#### 1.1 Add Version Parameter to Core Tools
**Files:** `src/documentation_search_enhanced/main.py`

Update tool signatures:
```python
@mcp.tool()
async def get_docs(
    query: str,
    libraries: Union[str, List[str]],
    version: str = "latest"  # NEW
):
    """
    Search documentation for specified libraries.

    Args:
        query: Search query
        libraries: Library name(s) to search
        version: Library version (e.g., "4.2", "stable", "latest")
                 Default: "latest" for backward compatibility
    """
```

Apply to:
- `get_docs` (line 440)
- `semantic_search` (line 697)
- `filtered_search` (line 759)
- `get_code_examples` (line 1928)

#### 1.2 Update process_library_search Function
**File:** `src/documentation_search_enhanced/main.py` (line 481)

```python
async def process_library_search(
    library: str,
    query: str,
    config_dict: Dict,
    version: str = "latest"  # NEW PARAMETER
) -> tuple:
    """Process a single library search with version support."""

    lib_config = config_dict.get("docs_urls", {}).get(library, {})

    # Get version-aware URL
    docs_root = get_versioned_docs_url(library, version, lib_config)

    # Build search query
    search_query = f"site:{docs_root} {query}"
    if version != "latest" and "{version}" not in str(lib_config.get("url", "")):
        # Append version to query if URL doesn't support versioning
        search_query += f" version {version}"

    # ... rest of implementation
```

#### 1.3 Create URL Helper Function
**File:** `src/documentation_search_enhanced/main.py`

```python
def get_versioned_docs_url(
    library: str,
    version: str,
    lib_config: Dict
) -> str:
    """
    Build version-specific documentation URL.

    Args:
        library: Library name
        version: Requested version
        lib_config: Library configuration from config.json

    Returns:
        Versioned documentation URL
    """
    base_url = lib_config.get("url", "")

    # Check if library supports version templates
    template = lib_config.get("version_url_template")
    if template and version != "latest":
        return template.format(version=version)

    # Handle common patterns
    if version != "latest":
        # Replace 'stable' or 'latest' in URL with specific version
        base_url = base_url.replace("/stable/", f"/{version}/")
        base_url = base_url.replace("/latest/", f"/{version}/")

    return base_url
```

#### 1.4 Update 10 High-Priority Configs
**File:** `src/documentation_search_enhanced/config.json`

Add version templates to these libraries:
```json
{
  "django": {
    "url": "https://docs.djangoproject.com/en/stable/",
    "version_url_template": "https://docs.djangoproject.com/en/{version}/",
    "version_pattern": "stable|5.1|5.0|4.2|4.1",
    "default_version": "stable",
    "supports_versioning": true
  },
  "flask": {
    "url": "https://flask.palletsprojects.com/en/stable/",
    "version_url_template": "https://flask.palletsprojects.com/en/{version}/",
    "version_pattern": "stable|3.0|2.3|2.2",
    "default_version": "stable",
    "supports_versioning": true
  }
  // ... add 8 more
}
```

Priority list:
1. django (line 101)
2. flask (line 125)
3. numpy (line 253)
4. scikit-learn (line 269)
5. matplotlib (line 261)
6. litestar (line 93)
7. requests (line 317)
8. pillow (line 325)
9. networkx (line 309)
10. ipywidgets (line 365)

#### 1.5 Update Tool Invocations
Search for all calls to `process_library_search` and add version parameter:

```python
# In get_docs tool
results = await asyncio.gather(
    *[process_library_search(lib, query, config, version)
      for lib in libraries_list]
)
```

#### 1.6 Testing MVP
Create test cases:
```bash
# Manual testing via MCP client
get_docs("authentication", "django", version="4.2")
get_docs("routing", "flask", version="3.0")
get_docs("arrays", "numpy")  # defaults to "latest"
```

**MVP Success Criteria:**
- ✅ All 4 tools accept version parameter
- ✅ URL substitution works for versioned URLs
- ✅ Search queries include version context
- ✅ No breaking changes to existing behavior
- ✅ 10 libraries configured with version templates

---

### Phase 2: Auto-Detection (2-3 hours)

#### 2.1 Create Version Resolver Module
**File:** `src/documentation_search_enhanced/version_resolver.py` (NEW)

```python
"""
Version resolution module for detecting installed package versions.
"""
import asyncio
import subprocess
import json
from typing import Optional, Dict, Tuple
from pathlib import Path
import re

class VersionResolver:
    """Resolves library versions from installed packages and project files."""

    def __init__(self):
        self._cache: Dict[str, str] = {}

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

        Returns:
            Version string or None
        """
        # Try pip show
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
        """Try to get version via pip show."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "pip", "show", package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode()
                match = re.search(r"Version:\s*(\S+)", output)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None

    async def _try_npm_list(self, package: str) -> Optional[str]:
        """Try to get version via npm list."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "list", package, "--depth=0", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                data = json.loads(stdout.decode())
                deps = data.get("dependencies", {})
                if package in deps:
                    version = deps[package].get("version")
                    return version
        except Exception:
            pass
        return None

    async def _try_python_import(self, package: str) -> Optional[str]:
        """Try to get version via Python import."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "python", "-c",
                f"import {package}; print({package}.__version__)",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            if proc.returncode == 0:
                version = stdout.decode().strip()
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
        """Parse pyproject.toml for library version."""
        try:
            import tomli
            with open(path, "rb") as f:
                data = tomli.load(f)

            # Check dependencies
            deps = data.get("project", {}).get("dependencies", [])
            for dep in deps:
                if library in dep.lower():
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
        """Parse requirements.txt for library version."""
        try:
            with open(path, "r") as f:
                for line in f:
                    if library in line.lower():
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
        """Parse package.json for library version."""
        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Check dependencies and devDependencies
            for dep_type in ["dependencies", "devDependencies"]:
                deps = data.get(dep_type, {})
                if library in deps:
                    version = deps[library].lstrip("^~")
                    return version
        except Exception:
            pass
        return None

    def clear_cache(self):
        """Clear version resolution cache."""
        self._cache.clear()


# Global instance
version_resolver = VersionResolver()
```

#### 2.2 Integrate Resolver into Main
**File:** `src/documentation_search_enhanced/main.py`

Add import:
```python
from .version_resolver import version_resolver
```

Update tool signatures:
```python
@mcp.tool()
async def get_docs(
    query: str,
    libraries: Union[str, List[str]],
    version: str = "latest",
    auto_detect_version: bool = True  # NEW
):
```

Update process_library_search:
```python
async def process_library_search(
    library: str,
    query: str,
    config_dict: Dict,
    version: str = "latest",
    auto_detect: bool = True  # NEW
) -> tuple:
    # Resolve version
    resolved_version = await version_resolver.resolve_version(
        library=library,
        requested_version=version,
        auto_detect=auto_detect,
        project_path="."
    )

    # ... rest of implementation using resolved_version
```

#### 2.3 Add Dependencies
**File:** `pyproject.toml`

```toml
dependencies = [
    # ... existing
    "tomli>=2.0.0; python_version<'3.11'",  # For pyproject.toml parsing
]
```

#### 2.4 Testing Auto-Detection
```python
# Test with installed packages
get_docs("routing", "flask", auto_detect_version=True)
# Should detect installed Flask version automatically

# Test with explicit override
get_docs("routing", "flask", version="2.3", auto_detect_version=True)
# Should use "2.3" (explicit wins)

# Test with no detection
get_docs("routing", "flask", auto_detect_version=False)
# Should use "latest"
```

**Phase 2 Success Criteria:**
- ✅ Version resolver module complete
- ✅ Auto-detection works for pip packages
- ✅ Auto-detection works for npm packages
- ✅ Project file parsing works
- ✅ Caching prevents repeated subprocess calls
- ✅ Graceful fallback to "latest"

---

### Phase 3: Full Configuration (1-2 hours)

#### 3.1 Enhance All 120 Library Configs
**File:** `src/documentation_search_enhanced/config.json`

Add version metadata to all libraries:
```json
{
  "library_name": {
    "url": "https://...",
    "version_url_template": "https://.../en/{version}/",  // if supported
    "version_pattern": "stable|latest|5.0|4.2",           // validation regex
    "default_version": "stable",                          // default if unspecified
    "supports_versioning": true,                          // boolean flag
    "version_mapping": {                                  // optional aliases
      "latest": "stable",
      "5": "5.1"
    }
  }
}
```

**Classification:**
- **Tier 1** (has version URLs): Django, Flask, NumPy, etc. → Full template
- **Tier 2** (active development): React, FastAPI → Add but no URL template
- **Tier 3** (stable APIs): Python core, JS core → Mark as version-insensitive

#### 3.2 Create Migration Script
**File:** `scripts/migrate_config_versions.py` (NEW)

```python
"""
Script to add version metadata to config.json.
Run: python scripts/migrate_config_versions.py
"""
import json
from pathlib import Path

def migrate_config():
    config_path = Path("src/documentation_search_enhanced/config.json")
    with open(config_path) as f:
        config = json.load(f)

    for lib_name, lib_config in config.get("docs_urls", {}).items():
        if isinstance(lib_config, str):
            # Convert old string format to new dict format
            config["docs_urls"][lib_name] = {
                "url": lib_config,
                "supports_versioning": False,
                "default_version": "latest"
            }
        elif "supports_versioning" not in lib_config:
            # Add missing version fields
            lib_config["supports_versioning"] = False
            lib_config["default_version"] = "latest"

            # Auto-detect versioning from URL
            url = lib_config.get("url", "")
            if "/stable/" in url or "/latest/" in url:
                lib_config["supports_versioning"] = True
                lib_config["version_pattern"] = "stable|latest"

    # Write back
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    print("Migration complete!")

if __name__ == "__main__":
    migrate_config()
```

#### 3.3 Update Config Validator
**File:** `src/documentation_search_enhanced/config_validator.py`

Add validation for new fields:
```python
class LibraryConfig(BaseModel):
    url: str
    category: Optional[str] = None
    learning_curve: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    auto_approve: Optional[bool] = True

    # NEW VERSION FIELDS
    version_url_template: Optional[str] = None
    version_pattern: Optional[str] = None
    default_version: str = "latest"
    supports_versioning: bool = False
    version_mapping: Optional[Dict[str, str]] = None
```

**Phase 3 Success Criteria:**
- ✅ All 120 libraries have version metadata
- ✅ Migration script successfully updates config
- ✅ Config validator passes with new schema
- ✅ No breaking changes to existing configs

---

### Phase 4: Testing & Documentation (1-2 hours)

#### 4.1 Create Test Suite
**File:** `tests/test_version_search.py` (NEW)

```python
"""
Test suite for version-specific documentation search.
"""
import pytest
from documentation_search_enhanced.main import (
    get_versioned_docs_url,
    process_library_search
)
from documentation_search_enhanced.version_resolver import version_resolver

@pytest.mark.asyncio
async def test_explicit_version():
    """Test explicit version parameter."""
    result = await version_resolver.resolve_version(
        library="django",
        requested_version="4.2",
        auto_detect=False
    )
    assert result == "4.2"

@pytest.mark.asyncio
async def test_auto_detect_fallback():
    """Test auto-detection with fallback to latest."""
    result = await version_resolver.resolve_version(
        library="nonexistent-package",
        requested_version="latest",
        auto_detect=True
    )
    assert result == "latest"

def test_version_url_template():
    """Test URL template substitution."""
    config = {
        "url": "https://docs.djangoproject.com/en/stable/",
        "version_url_template": "https://docs.djangoproject.com/en/{version}/"
    }

    url = get_versioned_docs_url("django", "4.2", config)
    assert url == "https://docs.djangoproject.com/en/4.2/"

def test_version_url_fallback():
    """Test URL generation without template."""
    config = {
        "url": "https://docs.djangoproject.com/en/stable/"
    }

    url = get_versioned_docs_url("django", "4.2", config)
    assert url == "https://docs.djangoproject.com/en/4.2/"  # stable replaced

@pytest.mark.asyncio
async def test_pip_version_detection():
    """Test pip package version detection."""
    # Test with known installed package
    version = await version_resolver._try_pip_show("pytest")
    assert version is not None
    assert len(version.split(".")) >= 2  # Has major.minor

@pytest.mark.asyncio
async def test_project_pyproject_parsing():
    """Test pyproject.toml parsing."""
    # Would need fixture file
    pass

def test_version_cache():
    """Test version resolution caching."""
    version_resolver.clear_cache()
    # Add to cache
    version_resolver._cache["django:."] = "4.2"

    # Should return cached value
    assert "django:." in version_resolver._cache
    assert version_resolver._cache["django:."] == "4.2"

# Integration tests
@pytest.mark.asyncio
async def test_get_docs_with_version(mocked_search):
    """Test get_docs tool with version parameter."""
    # Would need to mock search_web
    pass
```

Run tests:
```bash
uv run pytest tests/test_version_search.py -v
```

#### 4.2 Update Documentation
**Files to update:**

**README.md:**
```markdown
## Version-Specific Documentation Search

Search documentation for specific library versions:

### Explicit Version
```python
# Search Django 4.2 docs
get_docs("authentication", "django", version="4.2")

# Search multiple versions
get_docs("hooks", ["react", "vue"], version="18.0")
```

### Auto-Detection
```python
# Automatically detect installed version
get_docs("routing", "flask", auto_detect_version=True)

# Disable auto-detection
get_docs("routing", "flask", auto_detect_version=False)
```

### Version Support by Library
See `config.json` for `supports_versioning` flag.

Libraries with full version support:
- Django (4.2, 5.0, 5.1, stable)
- Flask (2.3, 3.0, stable)
- NumPy (1.24, 1.25, stable)
- [See full list in config.json]
```

**AGENTS.md:**
```markdown
## Working with Version-Specific Searches

When implementing features that use version search:

1. **Always check `supports_versioning`** in config before using templates
2. **Default to "latest"** for backward compatibility
3. **Use auto-detection** for better UX when possible
4. **Cache version lookups** to avoid repeated subprocess calls
```

**CHANGELOG.md:**
```markdown
## [Unreleased]

### Added
- Version-specific documentation search support
- Auto-detection of installed package versions
- `version` parameter to `get_docs`, `semantic_search`, `filtered_search`, `get_code_examples`
- `auto_detect_version` parameter for automatic version resolution
- Version metadata in config.json for 120+ libraries
- Version URL template system for libraries with versioned docs
```

#### 4.3 Example Usage Documentation
**File:** `docs/VERSION_SEARCH_EXAMPLES.md` (NEW)

```markdown
# Version Search Examples

## Basic Usage

### Explicit Version
```json
{
  "tool": "get_docs",
  "arguments": {
    "query": "authentication middleware",
    "libraries": "django",
    "version": "4.2"
  }
}
```

### Auto-Detection
```json
{
  "tool": "get_docs",
  "arguments": {
    "query": "hooks",
    "libraries": "react",
    "auto_detect_version": true
  }
}
```

## Advanced Patterns

### Multiple Libraries with Different Versions
```python
# Search Django 4.2 and Flask 3.0 simultaneously
# Note: Single version applies to all libraries in one call
get_docs("authentication", ["django", "flask"], version="stable")
```

### Version for Code Examples
```python
# Get React 18 code examples
get_code_examples(
    library="react",
    topic="hooks",
    version="18.0"
)
```

## Troubleshooting

### Version Not Found
If a specific version doesn't exist, the search falls back to the base URL.

### Auto-Detection Fails
Falls back to "latest" gracefully. No errors thrown.

### Unsupported Library
Libraries without `supports_versioning: true` still accept version parameter
but append it to search query instead of modifying URL.
```

**Phase 4 Success Criteria:**
- ✅ Comprehensive test suite (>80% coverage)
- ✅ All tests passing
- ✅ README updated with examples
- ✅ CHANGELOG updated
- ✅ Usage documentation created

---

## Implementation Checklist

### Pre-Implementation
- [x] Commit current code changes
- [x] Create project plan document
- [ ] Review plan with stakeholders
- [ ] Set up feature branch

### Phase 1: MVP (2-3 hours)
- [ ] Add version parameter to 4 core tools
- [ ] Implement get_versioned_docs_url helper
- [ ] Update process_library_search function
- [ ] Add version templates to 10 high-priority configs
- [ ] Manual testing of MVP features
- [ ] Commit MVP implementation

### Phase 2: Auto-Detection (2-3 hours)
- [ ] Create version_resolver.py module
- [ ] Implement pip version detection
- [ ] Implement npm version detection
- [ ] Implement project file parsing
- [ ] Add tomli dependency
- [ ] Integrate resolver into main.py
- [ ] Add auto_detect_version parameter
- [ ] Test auto-detection flow
- [ ] Commit auto-detection features

### Phase 3: Full Config (1-2 hours)
- [ ] Create config migration script
- [ ] Run migration on all 120 libraries
- [ ] Update config validator schema
- [ ] Validate migrated config
- [ ] Commit config updates

### Phase 4: Testing & Docs (1-2 hours)
- [ ] Write test suite
- [ ] Run tests and fix issues
- [ ] Update README.md
- [ ] Update AGENTS.md
- [ ] Update CHANGELOG.md
- [ ] Create example documentation
- [ ] Final integration testing
- [ ] Commit tests and documentation

### Post-Implementation
- [ ] Create pull request
- [ ] Update version number (1.3.2 → 1.4.0)
- [ ] Tag release
- [ ] Publish to PyPI

---

## Risk Mitigation

### Risk: Breaking Changes
**Mitigation:** Default `version="latest"` maintains current behavior

### Risk: Performance Impact
**Mitigation:**
- Cache version lookups
- Make subprocess calls async
- Timeout subprocess calls (5s max)

### Risk: Version Detection Failures
**Mitigation:** Always fall back to "latest" gracefully

### Risk: Config Complexity
**Mitigation:** Migration script automates updates

### Risk: Search API Cost (Serper)
**Mitigation:**
- Cache versioned searches longer (48h vs 24h)
- Consider switching to Brave API (free tier)

---

## Success Metrics

### Technical
- [ ] Zero breaking changes (all existing tests pass)
- [ ] >80% test coverage for new code
- [ ] All 4 doc tools support version parameter
- [ ] 20+ libraries configured with version templates
- [ ] Auto-detection works for pip and npm

### User Experience
- [ ] Version searches return relevant results
- [ ] Auto-detection improves accuracy
- [ ] Backward compatible (no user changes required)
- [ ] Clear documentation for new feature

### Competitive
- [ ] Feature parity with Context7 versioning
- [ ] Maintains security scanning advantage
- [ ] Better library coverage (120 vs ~50)

---

## Future Enhancements (Out of Scope)

1. **Version Range Support**
   - `version=">=4.2,<5.0"` for compatibility queries

2. **Smart Version Recommendations**
   - Suggest LTS versions vs latest

3. **Deprecation Warnings**
   - Flag searches for EOL versions

4. **Multi-Version Comparison**
   - Side-by-side comparison of version differences

5. **Version Change Logs**
   - Integrate release notes and migration guides

---

## Contact & Support

**Implementation Questions:**
- Review this plan before starting
- Check AGENTS.md for code patterns
- Test incrementally after each phase

**After Implementation:**
- Update this document with lessons learned
- Note any deviations from plan
- Document any additional edge cases discovered

---

**Status Updates:**
- 2025-12-16: Plan created, security fixes committed
- Next: Begin Phase 1 implementation
