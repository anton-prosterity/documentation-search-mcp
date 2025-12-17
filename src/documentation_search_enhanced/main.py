import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from pydantic import BeforeValidator
from importlib import resources
from .smart_search import smart_search, SearchResult
from .web_scraper import scraper
from .config_validator import validate_config, Config as AppConfig
from .content_enhancer import content_enhancer
from .version_resolver import version_resolver
import sys
import atexit

# Load the environment variables
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("documentation_search_enhanced")
USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

# Environment variables (removing API key exposure)
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


def _normalize_libraries(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return [part for part in parts if part]
    if isinstance(value, (list, tuple, set)):
        libraries: List[str] = []
        for item in value:
            if item is None:
                continue
            item_str = str(item).strip()
            if item_str:
                libraries.append(item_str)
        return libraries
    return [str(value).strip()]


LibrariesParam = Annotated[List[str], BeforeValidator(_normalize_libraries)]


# Simple in-memory cache with TTL
class SimpleCache:
    def __init__(
        self,
        ttl_hours: int = 24,
        max_entries: int = 1000,
        persistence_enabled: bool = False,
        persist_path: Optional[str] = None,
    ):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_hours = ttl_hours
        self.max_entries = max_entries
        self.persistence_enabled = persistence_enabled
        self.persist_path = persist_path
        self._lock = asyncio.Lock()

        if self.persistence_enabled and self.persist_path:
            self._load_from_disk()

    def _is_expired(self, timestamp: datetime) -> bool:
        return datetime.now() - timestamp > timedelta(hours=self.ttl_hours)

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if not self._is_expired(entry["timestamp"]):
                    return entry["data"]
                del self.cache[key]
            return None

    async def set(self, key: str, data: str) -> None:
        async with self._lock:
            await self._cleanup_locked()

            if len(self.cache) >= self.max_entries:
                oldest_key = min(
                    self.cache.keys(), key=lambda k: self.cache[k]["timestamp"]
                )
                del self.cache[oldest_key]

            self.cache[key] = {"data": data, "timestamp": datetime.now()}

            await self._persist_locked()

    async def clear_expired(self) -> None:
        async with self._lock:
            await self._cleanup_locked()
            await self._persist_locked()

    async def stats(self) -> Dict[str, Any]:
        async with self._lock:
            expired_count = sum(
                1
                for entry in self.cache.values()
                if self._is_expired(entry["timestamp"])
            )
            return {
                "total_entries": len(self.cache),
                "expired_entries": expired_count,
                "active_entries": len(self.cache) - expired_count,
                "max_entries": self.max_entries,
                "ttl_hours": self.ttl_hours,
                "memory_usage_estimate": f"{len(str(self.cache)) / 1024:.2f} KB",
            }

    async def clear(self) -> int:
        async with self._lock:
            removed = len(self.cache)
            self.cache.clear()
            await self._persist_locked()
            return removed

    async def _cleanup_locked(self) -> None:
        expired_keys = [
            k for k, v in self.cache.items() if self._is_expired(v["timestamp"])
        ]
        for key in expired_keys:
            del self.cache[key]

    def _load_from_disk(self) -> None:
        try:
            if not os.path.exists(self.persist_path or ""):
                return
            with open(self.persist_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            for key, entry in raw.items():
                try:
                    timestamp = datetime.fromisoformat(entry["timestamp"])
                    if not self._is_expired(timestamp):
                        self.cache[key] = {
                            "data": entry["data"],
                            "timestamp": timestamp,
                        }
                except Exception:
                    continue
        except Exception as exc:
            print(f"⚠️ Failed to load cache persistence: {exc}", file=sys.stderr)

    async def _persist_locked(self) -> None:
        if not (self.persistence_enabled and self.persist_path):
            return
        try:
            serialisable = {
                key: {
                    "data": value["data"],
                    "timestamp": value["timestamp"].isoformat(),
                }
                for key, value in self.cache.items()
                if not self._is_expired(value["timestamp"])
            }
            tmp_path = f"{self.persist_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as fh:
                json.dump(serialisable, fh)
            os.replace(tmp_path, self.persist_path)
        except Exception as exc:
            print(f"⚠️ Failed to persist cache: {exc}", file=sys.stderr)


class TokenBucketRateLimiter:
    def __init__(self, requests_per_minute: int, burst: int):
        self.capacity = max(burst, requests_per_minute, 1)
        self.refill_rate = requests_per_minute / 60 if requests_per_minute > 0 else 0
        self.tokens: Dict[str, float] = {}
        self.last_refill: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "global") -> None:
        if self.refill_rate == 0:
            return

        while True:
            async with self._lock:
                now = time.monotonic()
                tokens = self.tokens.get(key, float(self.capacity))
                last = self.last_refill.get(key, now)

                elapsed = now - last
                if elapsed > 0:
                    tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

                if tokens >= 1:
                    self.tokens[key] = tokens - 1
                    self.last_refill[key] = now
                    return

                wait_time = (1 - tokens) / self.refill_rate if self.refill_rate else 0
                self.tokens[key] = tokens
                self.last_refill[key] = now

            await asyncio.sleep(wait_time)


def load_config() -> AppConfig:
    """Load and validate the configuration file.

    Priority:
    1. Looks for `config.json` in the current working directory.
    2. Falls back to the `config.json` bundled with the package.
    """
    config_data = None
    local_config_path = os.path.join(os.getcwd(), "config.json")

    try:
        # 1. Prioritize local config file
        if os.path.exists(local_config_path):
            print("📝 Found local config.json. Loading...", file=sys.stderr)
            with open(local_config_path, "r") as f:
                config_data = json.load(f)
        else:
            # 2. Fallback to packaged config
            try:
                config_text = resources.read_text(
                    "documentation_search_enhanced", "config.json"
                )
                config_data = json.loads(config_text)
            except (FileNotFoundError, ModuleNotFoundError):
                # This is a critical failure if the package is broken
                print("FATAL: Packaged config.json not found.", file=sys.stderr)
                raise

    except Exception as e:
        print(f"FATAL: Could not read config.json. Error: {e}", file=sys.stderr)
        raise

    if not config_data:
        raise FileNotFoundError("Could not find or load config.json")

    try:
        validated_config = validate_config(config_data)
        print("✅ Configuration successfully loaded and validated.", file=sys.stderr)
        return validated_config
    except Exception as e:  # Pydantic's ValidationError
        print(
            "❌ FATAL: Configuration validation failed. Please check your config.json.",
            file=sys.stderr,
        )
        print(e, file=sys.stderr)
        raise


# Load configuration
config_model = load_config()
config = config_model.model_dump()  # Use the dict version for existing logic
docs_urls = {}
# Handle both old simple URL format and new enhanced format
for lib_name, lib_data in config.get("docs_urls", {}).items():
    if isinstance(lib_data, dict):
        docs_urls[lib_name] = lib_data.get("url", "")
    else:
        docs_urls[lib_name] = lib_data

cache_config = config.get("cache", {"enabled": False})
cache_persistence_enabled = cache_config.get("persistence_enabled", False)
cache_persist_path = cache_config.get("persist_path")
if cache_persistence_enabled and not cache_persist_path:
    cache_persist_path = os.path.join(os.getcwd(), ".docs_cache.json")

# Initialize cache if enabled
cache = (
    SimpleCache(
        ttl_hours=cache_config.get("ttl_hours", 24),
        max_entries=cache_config.get("max_entries", 1000),
        persistence_enabled=cache_persistence_enabled,
        persist_path=cache_persist_path,
    )
    if cache_config.get("enabled", False)
    else None
)

http_client: Optional[httpx.AsyncClient] = None
scrape_semaphore = asyncio.Semaphore(
    config.get("server_config", {}).get("max_concurrent_requests", 10)
)

rate_limit_config = config.get("rate_limiting", {"enabled": False})
rate_limiter = (
    TokenBucketRateLimiter(
        requests_per_minute=rate_limit_config.get("requests_per_minute", 60),
        burst=rate_limit_config.get("burst_requests", 10),
    )
    if rate_limit_config.get("enabled", False)
    else None
)


async def enforce_rate_limit(tool_name: str) -> None:
    if rate_limiter:
        await rate_limiter.acquire(tool_name)


async def search_web_with_retry(
    query: str, max_retries: int = 3, num_results: int = 3
) -> dict:
    """Search web with exponential backoff retry logic"""
    if not SERPER_API_KEY:
        print(
            "⚠️ SERPER_API_KEY not set - web search functionality will be limited",
            file=sys.stderr,
        )
        return {"organic": []}

    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=60.0))

    payload = json.dumps({"q": query, "num": num_results})
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    for attempt in range(max_retries):
        try:
            response = await http_client.post(
                SERPER_URL,
                headers=headers,
                content=payload,
            )
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                print(
                    f"Timeout after {max_retries} attempts for query: {query}",
                    file=sys.stderr,
                )
                return {"organic": []}
            await asyncio.sleep(2**attempt)  # Exponential backoff

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                if attempt == max_retries - 1:
                    print(f"Rate limited after {max_retries} attempts", file=sys.stderr)
                    return {"organic": []}
                await asyncio.sleep(2 ** (attempt + 2))  # Longer wait for rate limits
            else:
                print(f"HTTP error {e.response.status_code}: {e}", file=sys.stderr)
                return {"organic": []}

        except Exception as e:
            if attempt == max_retries - 1:
                print(
                    f"Unexpected error after {max_retries} attempts: {e}",
                    file=sys.stderr,
                )
                return {"organic": []}
            await asyncio.sleep(2**attempt)

    return {"organic": []}


async def fetch_url_with_cache(url: str, max_retries: int = 3) -> str:
    """Fetch URL content with caching and a Playwright-based scraper."""
    cache_key = hashlib.md5(url.encode()).hexdigest()

    if cache:
        cached_content = await cache.get(cache_key)
        if cached_content:
            return cached_content

    # Use the new Playwright scraper
    async with scrape_semaphore:
        content = await scraper.scrape_url(url)

    if cache and "Error:" not in content:
        await cache.set(cache_key, content)

    return content


# Backward compatibility aliases
async def search_web(query: str, num_results: int = 3) -> dict:
    return await search_web_with_retry(query, num_results=num_results)


async def fetch_url(url: str) -> str:
    return await fetch_url_with_cache(url)


# Configure smart search now that the helpers are in place
smart_search.configure(docs_urls, search_web)


async def shutdown_resources() -> None:
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None
    await scraper.close()


def _cleanup_sync() -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(shutdown_resources())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(shutdown_resources())
            loop.close()
    else:
        loop.create_task(shutdown_resources())


atexit.register(_cleanup_sync)


def get_versioned_docs_url(library: str, version: str, lib_config: Dict) -> str:
    """
    Build version-specific documentation URL.

    Args:
        library: Library name
        version: Requested version (e.g., "4.2", "stable", "latest")
        lib_config: Library configuration from config.json

    Returns:
        Versioned documentation URL
    """
    base_url = lib_config.get("url", "")

    # If version is "latest", return base URL as-is
    if version == "latest":
        return base_url

    # Check if library supports version templates
    template = lib_config.get("version_url_template")
    if template:
        return template.format(version=version)

    # Handle common patterns by replacing stable/latest in URL
    versioned_url = base_url.replace("/stable/", f"/{version}/")
    versioned_url = versioned_url.replace("/latest/", f"/{version}/")

    return versioned_url


@mcp.tool()
async def get_docs(query: str, libraries: LibrariesParam, version: str = "latest", auto_detect_version: bool = False):
    """
    Search documentation for a given query and one or more libraries.

    Args:
        query: The query to search for (e.g., "Chroma DB")
        libraries: A single library or a list of libraries to search in (e.g., "langchain" or ["fastapi", "django"])
        version: Library version to search (e.g., "4.2", "stable", "latest"). Default: "latest"
        auto_detect_version: Automatically detect installed package version. Default: False

    Returns:
        Dictionary with structured summaries and supporting metadata
    """
    await enforce_rate_limit("get_docs")

    if isinstance(libraries, str):
        libraries = [lib.strip() for lib in libraries.split(",") if lib.strip()]

    config_dict = config_model.model_dump()
    library_summaries: List[Dict[str, Any]] = []
    summary_sections: List[str] = []

    for library in libraries:
        # Resolve version (with auto-detection if enabled)
        resolved_version = await version_resolver.resolve_version(
            library=library,
            requested_version=version,
            auto_detect=auto_detect_version,
            project_path="."
        )
        lib_entry: Dict[str, Any] = {
            "library": library,
            "requested_query": query,
            "status": "searched",
            "results": [],
        }

        lib_config = config_dict.get("docs_urls", {}).get(library, {})
        auto_approve = lib_config.get("auto_approve", True)

        if not auto_approve:
            print(
                f"⚠️  Requesting approval to search {library} documentation...",
                file=sys.stderr,
            )

        docs_root = docs_urls.get(library)
        if not docs_root:
            lib_entry.update(
                {
                    "status": "unsupported",
                    "message": f"Library '{library}' not supported by this tool",
                }
            )
            library_summaries.append(lib_entry)
            summary_sections.append(
                f"### {library}\n- Unsupported library; no documentation root configured."
            )
            continue

        # Get version-specific URL
        versioned_url = get_versioned_docs_url(library, resolved_version, lib_config)

        # Build search query with version context
        search_query = f"site:{versioned_url} {query}"
        if resolved_version != "latest" and not lib_config.get("version_url_template"):
            # Add version to query if URL doesn't support versioning
            search_query += f" version {resolved_version}"

        search_results = await search_web(search_query, num_results=5)
        organic_results = (search_results.get("organic") or [])[:3]

        if not organic_results:
            lib_entry.update(
                {
                    "status": "no_results",
                    "message": "No indexed documentation results returned",
                }
            )
            library_summaries.append(lib_entry)
            summary_sections.append(f"### {library}\n- No results for query '{query}'.")
            continue

        fetch_tasks = [fetch_url(result["link"]) for result in organic_results]
        fetched_contents = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        library_lines = [f"### {library}"]
        for result, content in zip(organic_results, fetched_contents):
            entry: Dict[str, Any] = {
                "title": result.get("title") or result.get("link"),
                "url": result.get("link"),
                "source_snippet": result.get("snippet", ""),
            }

            if isinstance(content, Exception):
                error_message = str(content)
                entry["status"] = "error"
                entry["error"] = error_message
                library_lines.append(
                    f"- {entry['title']}: failed to fetch ({error_message})"
                )
            else:
                content_str = str(content)
                summary = content_enhancer.generate_summary(content_str, query)
                code_snippet_count = len(
                    content_enhancer.extract_code_snippets(content_str)
                )

                entry.update(
                    {
                        "status": "ok",
                        "summary": summary,
                        "code_snippet_count": code_snippet_count,
                    }
                )

                bullet_summary = summary if summary else "No summary extracted."
                library_lines.append(
                    f"- {entry['title']}: {bullet_summary} (code snippets: {code_snippet_count})"
                )

            lib_entry["results"].append(entry)

        lib_entry["total_results"] = len(lib_entry["results"])
        library_summaries.append(lib_entry)
        summary_sections.append("\n".join(library_lines))

    if cache:
        await cache.clear_expired()

    return {
        "query": query,
        "libraries": library_summaries,
        "summary_markdown": "\n\n".join(summary_sections),
    }


@mcp.tool()
async def suggest_libraries(partial_name: str):
    """
    Suggest libraries based on partial input for auto-completion.

    Args:
        partial_name: Partial library name to search for (e.g. "lang" -> ["langchain"])

    Returns:
        List of matching library names
    """
    if not partial_name:
        return list(sorted(docs_urls.keys()))

    partial_lower = partial_name.lower()
    suggestions = []

    # Exact matches first
    for lib in docs_urls.keys():
        if lib.lower() == partial_lower:
            suggestions.append(lib)

    # Starts with matches
    for lib in docs_urls.keys():
        if lib.lower().startswith(partial_lower) and lib not in suggestions:
            suggestions.append(lib)

    # Contains matches
    for lib in docs_urls.keys():
        if partial_lower in lib.lower() and lib not in suggestions:
            suggestions.append(lib)

    return sorted(suggestions[:10])  # Limit to top 10 suggestions


@mcp.tool()
async def health_check():
    """
    Check the health and availability of documentation sources.

    Returns:
        Dictionary with health status of each library's documentation site
    """
    results = {}

    # Test a sample of libraries to avoid overwhelming servers
    sample_libraries = list(docs_urls.items())[:5]

    for library, url in sample_libraries:
        start_time = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(
                    url,
                    timeout=httpx.Timeout(10.0),
                    headers={"User-Agent": USER_AGENT},
                    follow_redirects=True,
                )
                response_time = time.time() - start_time
                results[library] = {
                    "status": "healthy",
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time * 1000, 2),
                    "url": url,
                }
        except httpx.TimeoutException:
            results[library] = {
                "status": "timeout",
                "error": "Request timed out",
                "url": url,
            }
        except Exception as e:
            results[library] = {"status": "error", "error": str(e), "url": url}

    # Add cache stats if caching is enabled
    if cache:
        cache_stats = await cache.stats()
        results["_cache_stats"] = {"enabled": True, **cache_stats}
    else:
        results["_cache_stats"] = {"enabled": False}

    return results


@mcp.tool()
async def clear_cache():
    """
    Clear the documentation cache to force fresh fetches.

    Returns:
        Status message about cache clearing
    """
    if cache:
        entries_cleared = await cache.clear()
        return f"Cache cleared. Removed {entries_cleared} cached entries."
    else:
        return "Caching is not enabled."


@mcp.tool()
async def get_cache_stats():
    """
    Get statistics about the current cache usage.

    Returns:
        Dictionary with cache statistics
    """
    if not cache:
        return {"enabled": False, "message": "Caching is not enabled"}

    stats = await cache.stats()
    details = {
        "enabled": True,
        **stats,
    }
    details["persistence"] = {
        "enabled": cache.persistence_enabled,
        "path": cache.persist_path,
    }
    return details


@mcp.tool()
async def semantic_search(
    query: str, libraries: LibrariesParam, context: Optional[str] = None, version: str = "latest", auto_detect_version: bool = False
):
    """
    Enhanced semantic search across one or more libraries with relevance ranking.

    Args:
        query: The search query.
        libraries: A single library or a list of libraries to search in.
        context: Optional context about your project or use case.
        version: Library version to search (e.g., "4.2", "stable", "latest"). Default: "latest"
        auto_detect_version: Automatically detect installed package version. Default: False

    Returns:
        Enhanced search results with relevance scores and metadata, ranked across all libraries.
    """
    await enforce_rate_limit("semantic_search")

    if isinstance(libraries, str):
        libraries = [lib.strip() for lib in libraries.split(",") if lib.strip()]

    search_tasks = [
        smart_search.semantic_search(query, lib, context) for lib in libraries
    ]

    try:
        results_by_library = await asyncio.gather(*search_tasks, return_exceptions=True)

        all_results: List[SearchResult] = []
        for res_list in results_by_library:
            if not isinstance(res_list, Exception):
                all_results.extend(res_list)  # type: ignore

        # Sort all results from all libraries by relevance score
        all_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return {
            "query": query,
            "libraries_searched": libraries,
            "total_results": len(all_results),
            "results": [
                {
                    "source_library": result.source_library,
                    "title": result.title,
                    "url": result.url,
                    "snippet": (
                        result.snippet[:300] + "..."
                        if len(result.snippet) > 300
                        else result.snippet
                    ),
                    "relevance_score": result.relevance_score,
                    "content_type": result.content_type,
                    "difficulty_level": result.difficulty_level,
                    "estimated_read_time": f"{result.estimated_read_time} min",
                    "has_code_examples": result.code_snippets_count > 0,
                }
                for result in all_results[:10]  # Top 10 combined results
            ],
        }
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}


@mcp.tool()
async def filtered_search(
    query: str,
    library: str,
    content_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    has_code_examples: Optional[bool] = None,
    version: str = "latest",
    auto_detect_version: bool = False,
):
    """
    Search with advanced filtering options.

    Args:
        query: The search query
        library: The library to search in
        content_type: Filter by content type ("tutorial", "reference", "example", "guide")
        difficulty_level: Filter by difficulty ("beginner", "intermediate", "advanced")
        has_code_examples: Filter for content with code examples (true/false)
        version: Library version to search (e.g., "4.2", "stable", "latest"). Default: "latest"
        auto_detect_version: Automatically detect installed package version. Default: False

    Returns:
        Filtered search results matching specified criteria
    """
    from .smart_search import filtered_search, SearchFilters

    await enforce_rate_limit("filtered_search")

    filters = SearchFilters(
        content_type=content_type,
        difficulty_level=difficulty_level,
        has_code_examples=has_code_examples,
    )

    try:
        results = await filtered_search.search_with_filters(query, library, filters)

        return {
            "query": query,
            "library": library,
            "filters_applied": {
                "content_type": content_type,
                "difficulty_level": difficulty_level,
                "has_code_examples": has_code_examples,
            },
            "total_results": len(results),
            "results": [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": (
                        result.snippet[:200] + "..."
                        if len(result.snippet) > 200
                        else result.snippet
                    ),
                    "relevance_score": result.relevance_score,
                    "content_type": result.content_type,
                    "difficulty_level": result.difficulty_level,
                    "estimated_read_time": f"{result.estimated_read_time} min",
                }
                for result in results[:10]
            ],
        }
    except Exception as e:
        return {"error": f"Filtered search failed: {str(e)}", "results": []}


@mcp.tool()
async def get_learning_path(library: str, experience_level: str = "beginner"):
    """
    Get a structured learning path for a library based on experience level.

    Args:
        library: The library to create a learning path for
        experience_level: Your current level ("beginner", "intermediate", "advanced")

    Returns:
        Structured learning path with progressive topics and resources
    """
    # Dynamic learning path generation based on difficulty
    level_topics = {
        "beginner": ["Getting Started", "Basic Concepts", "First Examples", "Common Patterns"],
        "intermediate": ["Advanced Features", "Best Practices", "Integration", "Testing"],
        "advanced": ["Performance Optimization", "Advanced Architecture", "Production Deployment", "Monitoring"]
    }

    if experience_level not in level_topics:
        return {"error": f"Experience level {experience_level} not supported"}

    learning_steps = []
    for i, topic in enumerate(level_topics[experience_level]):
        learning_steps.append({
            "step": i + 1,
            "topic": f"{library.title()} - {topic}",
            "content_type": "tutorial",
            "search_query": f"{library} {topic.lower()}",
            "target_library": library,
            "estimated_time": "2-4 hours",
        })

    return {
        "library": library,
        "experience_level": experience_level,
        "total_topics": len(learning_steps),
        "estimated_total_time": f"{len(learning_steps) * 2}-{len(learning_steps) * 4} hours",
        "learning_path": learning_steps,
        "next_level": {
            "beginner": "intermediate",
            "intermediate": "advanced",
            "advanced": "Consider specializing in specific areas or exploring related technologies",
        }.get(experience_level, ""),
    }


# Removed 1000+ lines of hardcoded learning path data
@mcp.tool()
async def get_code_examples(library: str, topic: str, language: str = "python", version: str = "latest", auto_detect_version: bool = False):
    """
    Get curated code examples for a specific topic and library.

    Args:
        library: The library to search for examples
        topic: The specific topic or feature
        language: Programming language for examples
        version: Library version to search (e.g., "4.2", "stable", "latest"). Default: "latest"
        auto_detect_version: Automatically detect installed package version. Default: False

    Returns:
        Curated code examples with explanations
    """

    await enforce_rate_limit("get_code_examples")

    # Enhanced query for code-specific search
    code_query = f"{library} {topic} example code {language}"

    try:
        # Use filtered search to find examples with code
        from .smart_search import filtered_search, SearchFilters

        filters = SearchFilters(content_type="example", has_code_examples=True)

        results = await filtered_search.search_with_filters(
            code_query, library, filters
        )

        if not results:
            # Fallback to regular search
            if library not in docs_urls:
                return {"error": f"Library {library} not supported"}

            query = f"site:{docs_urls[library]} {code_query}"
            search_results = await search_web(query)

            if not search_results.get("organic"):
                return {"error": "No code examples found"}

            # Process first result for code extraction
            first_result = search_results["organic"][0]
            content = await fetch_url(first_result["link"])

            # Extract code snippets (simplified)
            code_blocks = []
            import re

            code_pattern = r"```(?:python|javascript|typescript|js)?\n(.*?)```"
            matches = re.finditer(code_pattern, content, re.DOTALL)

            for i, match in enumerate(matches):
                if i >= 3:  # Limit to 3 examples
                    break
                code_blocks.append(
                    {
                        "example": i + 1,
                        "code": match.group(1).strip(),
                        "language": language,
                        "source_url": first_result["link"],
                    }
                )

            return {
                "library": library,
                "topic": topic,
                "language": language,
                "total_examples": len(code_blocks),
                "examples": code_blocks,
            }

        else:
            # Process enhanced results
            examples = []
            for i, result in enumerate(results[:3]):
                examples.append(
                    {
                        "example": i + 1,
                        "title": result.title,
                        "description": (
                            result.snippet[:200] + "..."
                            if len(result.snippet) > 200
                            else result.snippet
                        ),
                        "url": result.url,
                        "difficulty": result.difficulty_level,
                        "estimated_read_time": f"{result.estimated_read_time} min",
                    }
                )

            return {
                "library": library,
                "topic": topic,
                "language": language,
                "total_examples": len(examples),
                "examples": examples,
            }

    except Exception as e:
        return {"error": f"Failed to get code examples: {str(e)}"}


@mcp.tool()
async def get_environment_config():
    """
    Get current environment configuration and settings.

    Returns:
        Current environment configuration details
    """
    from .config_manager import config_manager

    config = config_manager.get_config()

    return {
        "environment": config_manager.environment,
        "server_config": {
            "logging_level": config["server_config"]["logging_level"],
            "max_concurrent_requests": config["server_config"][
                "max_concurrent_requests"
            ],
            "request_timeout_seconds": config["server_config"][
                "request_timeout_seconds"
            ],
        },
        "cache_config": {
            "enabled": config["cache"]["enabled"],
            "ttl_hours": config["cache"]["ttl_hours"],
            "max_entries": config["cache"]["max_entries"],
        },
        "rate_limiting": {
            "enabled": config["rate_limiting"]["enabled"],
            "requests_per_minute": config["rate_limiting"]["requests_per_minute"],
        },
        "features": config["server_config"]["features"],
        "total_libraries": len(config_manager.get_docs_urls()),
        "available_libraries": list(config_manager.get_docs_urls().keys())[
            :10
        ],  # Show first 10
    }


@mcp.tool()
async def scan_library_vulnerabilities(library_name: str, ecosystem: str = "PyPI"):
    """
    Comprehensive vulnerability scan using OSINT sources (OSV, GitHub Advisories, Safety DB).

    Args:
        library_name: Name of the library to scan (e.g., "fastapi", "react")
        ecosystem: Package ecosystem ("PyPI", "npm", "Maven", "Go", etc.)

    Returns:
        Detailed security report with vulnerabilities, severity levels, and recommendations
    """
    await enforce_rate_limit("scan_library_vulnerabilities")

    from .vulnerability_scanner import vulnerability_scanner

    try:
        # Perform comprehensive scan
        security_report = await vulnerability_scanner.scan_library(
            library_name, ecosystem
        )

        return {
            "scan_results": security_report.to_dict(),
            "summary": {
                "library": security_report.library_name,
                "ecosystem": security_report.ecosystem,
                "security_score": security_report.security_score,
                "risk_level": (
                    "🚨 High Risk"
                    if security_report.security_score < 50
                    else (
                        "⚠️ Medium Risk"
                        if security_report.security_score < 70
                        else (
                            "✅ Low Risk"
                            if security_report.security_score < 90
                            else "🛡️ Excellent"
                        )
                    )
                ),
                "critical_vulnerabilities": security_report.critical_count,
                "total_vulnerabilities": security_report.total_vulnerabilities,
                "primary_recommendation": (
                    security_report.recommendations[0]
                    if security_report.recommendations
                    else "No specific recommendations"
                ),
            },
            "scan_timestamp": security_report.scan_date,
            "sources": [
                "OSV Database",
                "GitHub Security Advisories",
                "Safety DB (PyPI only)",
            ],
        }

    except Exception as e:
        return {
            "error": f"Vulnerability scan failed: {str(e)}",
            "library": library_name,
            "ecosystem": ecosystem,
            "scan_timestamp": datetime.now().isoformat(),
        }


@mcp.tool()
async def get_security_summary(library_name: str, ecosystem: str = "PyPI"):
    """
    Get quick security overview for a library without detailed vulnerability list.

    Args:
        library_name: Name of the library
        ecosystem: Package ecosystem (default: PyPI)

    Returns:
        Concise security summary with score and basic recommendations
    """
    await enforce_rate_limit("get_security_summary")

    from .vulnerability_scanner import security_integration

    try:
        summary = await security_integration.get_security_summary(
            library_name, ecosystem
        )

        # Add security badge
        score = summary.get("security_score", 50)
        if score >= 90:
            badge = "🛡️ EXCELLENT"
        elif score >= 70:
            badge = "✅ SECURE"
        elif score >= 50:
            badge = "⚠️ CAUTION"
        else:
            badge = "🚨 HIGH RISK"

        return {
            "library": library_name,
            "ecosystem": ecosystem,
            "security_badge": badge,
            "security_score": score,
            "status": summary.get("status", "unknown"),
            "vulnerabilities": {
                "total": summary.get("total_vulnerabilities", 0),
                "critical": summary.get("critical_vulnerabilities", 0),
            },
            "recommendation": summary.get(
                "primary_recommendation", "No recommendations available"
            ),
            "last_scanned": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "library": library_name,
            "ecosystem": ecosystem,
            "security_badge": "❓ UNKNOWN",
            "security_score": None,
            "status": "scan_failed",
            "error": str(e),
        }


@mcp.tool()
async def compare_library_security(libraries: List[str], ecosystem: str = "PyPI"):
    """
    Compare security scores across multiple libraries to help with selection.

    Args:
        libraries: List of library names to compare
        ecosystem: Package ecosystem for all libraries

    Returns:
        Security comparison with rankings and recommendations
    """
    await enforce_rate_limit("compare_library_security")

    from .vulnerability_scanner import security_integration

    if len(libraries) > 10:
        return {"error": "Maximum 10 libraries allowed for comparison"}

    results = []

    # Scan all libraries in parallel for faster comparison
    scan_tasks = [
        security_integration.get_security_summary(lib, ecosystem) for lib in libraries
    ]

    try:
        summaries = await asyncio.gather(*scan_tasks, return_exceptions=True)

        for i, (library, summary_item) in enumerate(zip(libraries, summaries)):
            if isinstance(summary_item, Exception):
                results.append(
                    {
                        "library": library,
                        "security_score": 0,
                        "status": "scan_failed",
                        "error": str(summary_item),
                    }
                )
            else:
                summary = summary_item
                results.append(
                    {
                        "library": library,
                        "security_score": summary.get("security_score", 0),  # type: ignore
                        "status": summary.get("status", "unknown"),  # type: ignore
                        "vulnerabilities": summary.get("total_vulnerabilities", 0),  # type: ignore
                        "critical_vulnerabilities": summary.get("critical_vulnerabilities", 0),  # type: ignore
                        "recommendation": summary.get("primary_recommendation", ""),  # type: ignore
                    }
                )

        # Sort by security score (highest first)
        results.sort(key=lambda x: x.get("security_score", 0), reverse=True)

        # Add rankings
        for i, result in enumerate(results):
            result["rank"] = i + 1
            score = result.get("security_score", 0)
            if score >= 90:
                result["rating"] = "🛡️ Excellent"
            elif score >= 70:
                result["rating"] = "✅ Secure"
            elif score >= 50:
                result["rating"] = "⚠️ Caution"
            else:
                result["rating"] = "🚨 High Risk"

        # Generate overall recommendation
        if results:
            best_lib = results[0]

            if best_lib.get("security_score", 0) >= 80:
                overall_rec = (
                    f"✅ Recommended: {best_lib['library']} has excellent security"
                )
            elif best_lib.get("security_score", 0) >= 60:
                overall_rec = f"⚠️ Proceed with caution: {best_lib['library']} is the most secure option"
            else:
                overall_rec = "🚨 Security concerns: All libraries have significant vulnerabilities"
        else:
            overall_rec = "Unable to generate recommendation"

        return {
            "comparison_results": results,
            "total_libraries": len(libraries),
            "scan_timestamp": datetime.now().isoformat(),
            "overall_recommendation": overall_rec,
            "ecosystem": ecosystem,
        }

    except Exception as e:
        return {
            "error": f"Security comparison failed: {str(e)}",
            "libraries": libraries,
            "ecosystem": ecosystem,
        }


@mcp.tool()
async def suggest_secure_libraries(
    partial_name: str, include_security_score: bool = True
):
    """
    Enhanced library suggestions that include security scores for informed decisions.

    Args:
        partial_name: Partial library name to search for
        include_security_score: Whether to include security scores (slower but more informative)

    Returns:
        Library suggestions with optional security information
    """
    await enforce_rate_limit("suggest_secure_libraries")

    # Get basic suggestions first
    basic_suggestions = await suggest_libraries(partial_name)

    if not include_security_score or not basic_suggestions:
        return {
            "suggestions": basic_suggestions,
            "partial_name": partial_name,
            "security_info_included": False,
        }

    # Add security information for top 5 suggestions
    from .vulnerability_scanner import security_integration

    enhanced_suggestions = []
    top_suggestions = basic_suggestions[:5]  # Limit to avoid too many API calls

    # Get security scores in parallel
    security_tasks = [
        security_integration.get_security_summary(lib, "PyPI")
        for lib in top_suggestions
    ]

    try:
        security_results = await asyncio.gather(*security_tasks, return_exceptions=True)

        for lib, sec_res_item in zip(top_suggestions, security_results):
            suggestion = {"library": lib}

            if isinstance(sec_res_item, Exception):
                suggestion.update(
                    {
                        "security_score": None,
                        "security_status": "unknown",
                        "security_badge": "❓",
                    }
                )
            else:
                security_result = sec_res_item
                score = security_result.get("security_score", 50)
                suggestion.update(
                    {
                        "security_score": score,
                        "security_status": security_result.get("status", "unknown"),  # type: ignore
                        "security_badge": (
                            "🛡️"
                            if score >= 90
                            else "✅" if score >= 70 else "⚠️" if score >= 50 else "🚨"
                        ),
                        "vulnerabilities": security_result.get("total_vulnerabilities", 0),  # type: ignore
                    }
                )

            enhanced_suggestions.append(suggestion)

        # Add remaining suggestions without security info
        for lib in basic_suggestions[5:]:
            enhanced_suggestions.append(
                {
                    "library": lib,
                    "security_score": None,
                    "security_status": "not_scanned",
                    "note": "Use scan_library_vulnerabilities for security details",
                }
            )

        # Sort by security score for enhanced suggestions
        enhanced_suggestions.sort(
            key=lambda x: x.get("security_score") or 0, reverse=True
        )

        return {
            "suggestions": enhanced_suggestions,
            "partial_name": partial_name,
            "security_info_included": True,
            "total_suggestions": len(enhanced_suggestions),
            "note": "Libraries with security scores are sorted by security rating",
        }

    except Exception as e:
        return {
            "suggestions": [{"library": lib} for lib in basic_suggestions],
            "partial_name": partial_name,
            "security_info_included": False,
            "error": f"Security enhancement failed: {str(e)}",
        }


@mcp.tool()
async def scan_project_dependencies(project_path: str = "."):
    """
    Scans project dependencies from files like pyproject.toml or requirements.txt for vulnerabilities.

    Args:
        project_path: The path to the project directory (defaults to current directory).

    Returns:
        A comprehensive security report of all project dependencies.
    """
    from .vulnerability_scanner import vulnerability_scanner
    from .project_scanner import find_and_parse_dependencies

    parsed_info = find_and_parse_dependencies(project_path)

    if not parsed_info:
        return {
            "error": "No dependency file found.",
            "message": "Supported files are pyproject.toml, requirements.txt, or package.json.",
        }

    filename, ecosystem, dependencies = parsed_info

    if not dependencies:
        return {
            "summary": {
                "dependency_file": filename,
                "ecosystem": ecosystem,
                "total_dependencies": 0,
                "vulnerable_count": 0,
                "overall_project_risk": "None",
                "message": "No dependencies found to scan.",
            },
            "vulnerable_packages": [],
        }

    total_deps = len(dependencies)
    print(
        f"🔎 Found {total_deps} dependencies in '{filename}'. Scanning for vulnerabilities...",
        file=sys.stderr,
    )

    scan_tasks = [
        vulnerability_scanner.scan_library(name, ecosystem)
        for name in dependencies.keys()
    ]

    results = await asyncio.gather(*scan_tasks, return_exceptions=True)

    vulnerable_deps = []
    for i, report_item in enumerate(results):
        dep_name = list(dependencies.keys())[i]
        if isinstance(report_item, Exception):
            # Could log this error
            continue
        else:
            report = report_item
            if report.vulnerabilities:  # type: ignore
                vulnerable_deps.append(
                    {
                        "library": dep_name,
                        "version": dependencies[dep_name],
                        "vulnerability_count": report.total_vulnerabilities,  # type: ignore
                        "security_score": report.security_score,
                        "summary": (
                            report.recommendations[0]
                            if report.recommendations
                            else "Update to the latest version."
                        ),
                        "details": [
                            vuln.to_dict() for vuln in report.vulnerabilities[:3]
                        ],  # Top 3
                    }
                )

    vulnerable_deps.sort(key=lambda x: x["security_score"])

    return {
        "summary": {
            "dependency_file": filename,
            "ecosystem": ecosystem,
            "total_dependencies": total_deps,
            "vulnerable_count": len(vulnerable_deps),
            "overall_project_risk": (
                "High"
                if any(d["security_score"] < 50 for d in vulnerable_deps)
                else (
                    "Medium"
                    if any(d["security_score"] < 70 for d in vulnerable_deps)
                    else "Low"
                )
            ),
        },
        "vulnerable_packages": vulnerable_deps,
    }


@mcp.tool()
async def generate_project_starter(project_name: str, template: str):
    """
    Generates a starter project from a template (e.g., 'fastapi', 'react-vite').

    Args:
        project_name: The name for the new project directory.
        template: The project template to use.

    Returns:
        A summary of the created project structure.
    """
    from .project_generator import generate_project

    try:
        result = generate_project(project_name, template)

        # Provide a more user-friendly summary
        summary = f"✅ Successfully created '{result['project_name']}' using the '{result['template_used']}' template.\n"
        summary += f"Location: {result['project_path']}\n\n"
        summary += "Next steps:\n"

        if template == "fastapi":
            summary += f"1. cd {result['project_name']}\n"
            summary += "2. uv pip sync\n"
            summary += "3. uv run uvicorn main:app --reload\n"
        elif template == "react-vite":
            summary += f"1. cd {result['project_name']}\n"
            summary += "2. npm install\n"
            summary += "3. npm run dev\n"

        result["user_summary"] = summary
        return result

    except (ValueError, FileExistsError) as e:
        return {"error": str(e)}


@mcp.tool()
async def manage_dev_environment(service: str, project_path: str = "."):
    """
    Manages local development environments using Docker Compose.

    Args:
        service: The service to set up (e.g., 'postgres', 'redis').
        project_path: The path to the project directory.

    Returns:
        A confirmation message with the next steps.
    """
    from .docker_manager import create_docker_compose, TEMPLATES

    try:
        if service not in TEMPLATES:
            return {
                "error": f"Service '{service}' not supported.",
                "available_services": list(TEMPLATES.keys()),
            }

        compose_file = create_docker_compose(service, project_path)

        return {
            "status": "success",
            "message": f"✅ Successfully created 'docker-compose.yml' for '{service}' in '{project_path}'.",
            "next_steps": [
                f"1. Review the generated file: {compose_file}",
                "2. Run the service: docker-compose up -d",
                "3. To stop the service: docker-compose down",
            ],
            "service_details": TEMPLATES[service]["services"],
        }

    except (ValueError, FileExistsError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


@mcp.tool()
async def get_current_config():
    """
    Returns the current, active configuration of the MCP server.
    This allows users to view the default config and use it as a template for local overrides.
    """
    try:
        # The `config` global is a dictionary created from the Pydantic model
        # at startup, so it represents the active configuration.
        return config
    except Exception as e:
        return {"error": f"Could not retrieve configuration: {str(e)}"}


@mcp.tool()
async def snyk_scan_library(library_name: str, version: str = "latest", ecosystem: str = "pypi"):
    """
    Scan a library using Snyk for comprehensive security analysis.
    
    Args:
        library_name: Name of the library to scan
        version: Version of the library (default: "latest") 
        ecosystem: Package ecosystem ("pypi", "npm", "maven", etc.)
    
    Returns:
        Detailed security report from Snyk including vulnerabilities, licenses, and remediation advice
    """
    from .snyk_integration import snyk_integration
    
    try:
        # Test connection first
        connection_test = await snyk_integration.test_connection()
        if connection_test["status"] != "connected":
            return {
                "error": "Snyk integration not configured",
                "details": connection_test.get("error", "Unknown error"),
                "setup_instructions": [
                    "1. Sign up for Snyk account at https://snyk.io",
                    "2. Get API token from your Snyk account settings",
                    "3. Set SNYK_API_KEY environment variable",
                    "4. Optionally set SNYK_ORG_ID for organization-specific scans"
                ]
            }
        
        # Perform the scan
        package_info = await snyk_integration.scan_package(library_name, version, ecosystem)
        
        return {
            "library": library_name,
            "version": version,
            "ecosystem": ecosystem,
            "scan_timestamp": datetime.now().isoformat(),
            "vulnerability_summary": {
                "total": len(package_info.vulnerabilities),
                "critical": package_info.severity_counts.get("critical", 0),
                "high": package_info.severity_counts.get("high", 0),
                "medium": package_info.severity_counts.get("medium", 0),
                "low": package_info.severity_counts.get("low", 0)
            },
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "title": vuln.title,
                    "severity": vuln.severity.value,
                    "cvss_score": vuln.cvss_score,
                    "cve": vuln.cve,
                    "is_patchable": vuln.is_patchable,
                    "upgrade_path": vuln.upgrade_path[:3] if vuln.upgrade_path else [],
                    "snyk_url": f"https://snyk.io/vuln/{vuln.id}"
                }
                for vuln in package_info.vulnerabilities[:10]  # Limit to top 10
            ],
            "license_info": [
                {
                    "name": license.name,
                    "type": license.type,
                    "spdx_id": license.spdx_id,
                    "is_deprecated": license.is_deprecated
                }
                for license in package_info.licenses
            ],
            "recommendations": [
                "🔍 Review all critical and high severity vulnerabilities",
                "📦 Update to latest secure version if available",
                "⚖️ Ensure license compliance with your organization's policies",
                "🔄 Set up continuous monitoring for this package"
            ]
        }
        
    except Exception as e:
        return {
            "error": f"Snyk scan failed: {str(e)}",
            "library": library_name,
            "version": version
        }


@mcp.tool()
async def snyk_scan_project(project_path: str = "."):
    """
    Scan entire project dependencies using Snyk.
    
    Args:
        project_path: Path to the project directory (default: current directory)
    
    Returns:
        Comprehensive security report for all project dependencies
    """
    from .snyk_integration import snyk_integration
    from .project_scanner import find_and_parse_dependencies
    
    try:
        # Find project dependencies
        dep_result = find_and_parse_dependencies(project_path)
        if not dep_result:
            return {
                "error": "No supported dependency files found",
                "supported_files": ["pyproject.toml", "requirements.txt", "package.json"],
                "project_path": project_path
            }
        
        filename, ecosystem, dependencies = dep_result
        manifest_path = os.path.join(project_path, filename)
        
        # Test Snyk connection
        connection_test = await snyk_integration.test_connection()
        if connection_test["status"] != "connected":
            return {
                "error": "Snyk integration not configured",
                "details": connection_test.get("error", "Unknown error")
            }
        
        # Scan the project manifest
        scan_result = await snyk_integration.scan_project_manifest(manifest_path, ecosystem)
        
        if "error" in scan_result:
            return scan_result
            
        # Enhance with additional analysis
        high_priority_vulns = [
            vuln for vuln in scan_result["vulnerabilities"] 
            if vuln.get("severity") in ["critical", "high"]
        ]
        
        return {
            "project_path": project_path,
            "manifest_file": filename,
            "ecosystem": ecosystem,
            "scan_timestamp": scan_result["scan_timestamp"],
            "summary": {
                **scan_result["summary"],
                "high_priority_vulnerabilities": len(high_priority_vulns),
                "security_score": max(0, 100 - (
                    len([v for v in scan_result["vulnerabilities"] if v.get("severity") == "critical"]) * 25 +
                    len([v for v in scan_result["vulnerabilities"] if v.get("severity") == "high"]) * 15 +
                    len([v for v in scan_result["vulnerabilities"] if v.get("severity") == "medium"]) * 5 +
                    len([v for v in scan_result["vulnerabilities"] if v.get("severity") == "low"]) * 1
                ))
            },
            "high_priority_vulnerabilities": high_priority_vulns[:10],
            "license_issues": scan_result["license_issues"],
            "remediation_summary": {
                "patches_available": len([v for v in scan_result["vulnerabilities"] if v.get("is_patchable")]),
                "upgrades_available": len([v for v in scan_result["vulnerabilities"] if v.get("upgrade_path")]),
                "total_fixable": len([v for v in scan_result["vulnerabilities"] 
                                   if v.get("is_patchable") or v.get("upgrade_path")])
            },
            "next_steps": [
                "🚨 Address all critical vulnerabilities immediately",
                "📦 Update packages with available security patches",
                "🔍 Review medium and low priority issues", 
                "⚖️ Check license compliance for flagged packages",
                "🔄 Set up continuous monitoring with Snyk"
            ]
        }
        
    except Exception as e:
        return {
            "error": f"Project scan failed: {str(e)}",
            "project_path": project_path
        }


@mcp.tool()
async def snyk_license_check(project_path: str = ".", policy: str = "permissive"):
    """
    Check license compliance for project dependencies using Snyk.
    
    Args:
        project_path: Path to the project directory
        policy: License policy to apply ("permissive", "copyleft-limited", "strict")
    
    Returns:
        License compliance report with risk assessment
    """
    from .snyk_integration import snyk_integration
    from .project_scanner import find_and_parse_dependencies
    
    try:
        # Find project dependencies
        dep_result = find_and_parse_dependencies(project_path)
        if not dep_result:
            return {"error": "No supported dependency files found"}
        
        filename, ecosystem, dependencies = dep_result
        
        # Convert dependencies to list of tuples
        packages = [(name, version) for name, version in dependencies.items()]
        
        # Get license compliance report
        compliance_report = await snyk_integration.get_license_compliance(packages, ecosystem)
        
        # Apply policy-specific analysis
        policy_rules = {
            "permissive": {
                "allowed": {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"},
                "restricted": {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0"},
                "name": "Permissive Policy"
            },
            "copyleft-limited": {
                "allowed": {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "LGPL-2.1", "LGPL-3.0"},
                "restricted": {"GPL-2.0", "GPL-3.0", "AGPL-3.0"},
                "name": "Limited Copyleft Policy"
            },
            "strict": {
                "allowed": {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"},
                "restricted": {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0"},
                "name": "Strict Policy"
            }
        }
        
        selected_policy = policy_rules.get(policy, policy_rules["permissive"])
        
        # Risk assessment
        risk_assessment = {
            "policy_applied": selected_policy["name"],
            "overall_compliance": "compliant" if compliance_report["non_compliant_packages"] == 0 else "non-compliant",
            "risk_level": "low" if compliance_report["non_compliant_packages"] == 0 else 
                         "high" if compliance_report["non_compliant_packages"] > 5 else "medium",
            "action_required": compliance_report["non_compliant_packages"] > 0
        }
        
        return {
            "project_path": project_path,
            "policy": selected_policy["name"],
            "scan_timestamp": datetime.now().isoformat(),
            "compliance_summary": compliance_report,
            "risk_assessment": risk_assessment,
            "recommendations": [
                "📋 Review all non-compliant packages",
                "🔄 Find alternative packages with compatible licenses",
                "⚖️ Consult legal team for high-risk licenses",
                "📝 Document license decisions for audit trail"
            ]
        }
        
    except Exception as e:
        return {
            "error": f"License check failed: {str(e)}",
            "project_path": project_path
        }


@mcp.tool()
async def snyk_monitor_project(project_path: str = "."):
    """
    Set up continuous monitoring for a project with Snyk.
    
    Args:
        project_path: Path to the project directory
    
    Returns:
        Status of monitoring setup and project details
    """
    from .snyk_integration import snyk_integration
    
    try:
        # Test connection and get organization info
        connection_test = await snyk_integration.test_connection()
        if connection_test["status"] != "connected":
            return {
                "error": "Snyk integration not configured",
                "details": connection_test.get("error", "Unknown error"),
                "setup_required": [
                    "Set SNYK_API_KEY environment variable",
                    "Set SNYK_ORG_ID environment variable",
                    "Ensure you have organization admin privileges"
                ]
            }
        
        # Set up monitoring
        monitor_result = await snyk_integration.monitor_project(project_path)
        
        if "error" in monitor_result:
            return monitor_result
        
        return {
            "status": "success",
            "monitoring_enabled": True,
            "project_details": monitor_result,
            "organization": connection_test.get("organizations", []),
            "next_steps": [
                "🔔 Configure alert preferences in Snyk dashboard",
                "📊 Review security reports regularly",
                "🔄 Enable automatic PRs for security updates",
                "📈 Set up integration with CI/CD pipeline"
            ],
            "dashboard_url": "https://app.snyk.io/org/your-org/projects"
        }
        
    except Exception as e:
        return {
            "error": f"Monitoring setup failed: {str(e)}",
            "project_path": project_path
        }


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
