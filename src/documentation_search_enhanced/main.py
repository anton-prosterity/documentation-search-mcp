import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio
import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from importlib import resources
#Load the environment variables
load_dotenv()

#Initialize the MCP server
mcp = FastMCP("docs")
USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"

# Environment variables (removing API key exposure)
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Simple in-memory cache with TTL
class SimpleCache:
    def __init__(self, ttl_hours: int = 24, max_entries: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_hours = ttl_hours
        self.max_entries = max_entries

    def _is_expired(self, timestamp: datetime) -> bool:
        return datetime.now() - timestamp > timedelta(hours=self.ttl_hours)

    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry['timestamp']):
                return entry['data']
            else:
                # Remove expired entry
                del self.cache[key]
        return None

    def set(self, key: str, data: str) -> None:
        # Clean up expired entries and enforce max size
        self.clear_expired()
        
        if len(self.cache) >= self.max_entries:
            # Remove oldest entries (simple FIFO)
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }

    def clear_expired(self) -> None:
        expired_keys = [k for k, v in self.cache.items() if self._is_expired(v['timestamp'])]
        for key in expired_keys:
            del self.cache[key]

# Load configuration from external file
def load_config():
    """Load configuration with enhanced popularity data"""
    try:
        # Try to load from package resources first (for installed package)
        try:
            config_text = resources.read_text("documentation_search_enhanced", "config.json")
            config = json.loads(config_text)
        except (FileNotFoundError, ModuleNotFoundError):
            # Fallback to relative path (for development)
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
            with open(config_path, "r") as f:
                config = json.load(f)
    except Exception:
        # Final fallback to current directory
        with open("config.json", "r") as f:
            config = json.load(f)
    return config

# Load configuration
config = load_config()
docs_urls = {}
# Handle both old simple URL format and new enhanced format
for lib_name, lib_data in config["docs_urls"].items():
    if isinstance(lib_data, dict):
        docs_urls[lib_name] = lib_data.get("url", "")
    else:
        docs_urls[lib_name] = lib_data

cache_config = config.get("cache", {"enabled": False})

# Initialize cache if enabled
cache = SimpleCache(
    ttl_hours=cache_config.get("ttl_hours", 24),
    max_entries=cache_config.get("max_entries", 1000)
) if cache_config.get("enabled", False) else None

async def search_web_with_retry(query: str, max_retries: int = 3) -> dict:
    """Search web with exponential backoff retry logic"""
    if not SERPER_API_KEY:
        print("⚠️ SERPER_API_KEY not set - web search functionality will be limited")
        return {"organic": []}
    
    payload = json.dumps({"q": query, "num": 2})
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SERPER_URL, headers=headers, content=payload, 
                    timeout=httpx.Timeout(30.0, read=60.0)
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                print(f"Timeout after {max_retries} attempts for query: {query}")
                return {"organic": []}
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                if attempt == max_retries - 1:
                    print(f"Rate limited after {max_retries} attempts")
                    return {"organic": []}
                await asyncio.sleep(2 ** (attempt + 2))  # Longer wait for rate limits
            else:
                print(f"HTTP error {e.response.status_code}: {e}")
                return {"organic": []}
                
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Unexpected error after {max_retries} attempts: {e}")
                return {"organic": []}
            await asyncio.sleep(2 ** attempt)
    
    return {"organic": []}

async def fetch_url_with_cache(url: str, max_retries: int = 3) -> str:
    """Fetch URL content with caching and retry logic"""
    # Generate cache key
    cache_key = hashlib.md5(url.encode()).hexdigest()
    
    # Check cache first
    if cache:
        cached_content = cache.get(cache_key)
        if cached_content:
            return cached_content
    
    # Fetch with retry logic
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    timeout=httpx.Timeout(30.0, read=60.0),
                    headers={"User-Agent": USER_AGENT},
                    follow_redirects=True
                )
                response.raise_for_status()
                
                # Parse content
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get text and clean it up
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                # Cache the result
                if cache and text:
                    cache.set(cache_key, text)
                
                return text
                
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                return f"Timeout error fetching {url}"
            await asyncio.sleep(2 ** attempt)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Page not found: {url}"
            elif e.response.status_code == 403:
                return f"Access forbidden: {url}"
            elif attempt == max_retries - 1:
                return f"HTTP error {e.response.status_code} for {url}"
            await asyncio.sleep(2 ** attempt)
            
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Error fetching {url}: {str(e)}"
            await asyncio.sleep(2 ** attempt)
    
    return f"Failed to fetch {url} after {max_retries} attempts"

# Backward compatibility aliases
async def search_web(query: str) -> dict:
    return await search_web_with_retry(query)

async def fetch_url(url: str) -> str:
    return await fetch_url_with_cache(url)
    
        

@mcp.tool()
async def get_docs(query: str, library: str):
    """
    Search the latest docs for a given query and library.

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs (limited to ~50KB for readability)
    """
    
    if library not in docs_urls:
        raise ValueError(f"Library {library} not supported by this tool")
    
    # Clean expired cache entries periodically
    if cache:
        cache.clear_expired()
    
    query = f"site:{docs_urls[library]} {query}"
    results = await search_web(query)
    if len(results["organic"]) == 0:
        return "No results found"
    
    # Fetch content from multiple results concurrently
    tasks = [fetch_url(result["link"]) for result in results["organic"]]
    contents = await asyncio.gather(*tasks, return_exceptions=True)
    
    text = ""
    max_length = 50000  # Limit to ~50KB for better readability
    
    for i, content in enumerate(contents):
        if isinstance(content, Exception):
            error_msg = f"\n[Error fetching {results['organic'][i]['link']}: {str(content)}]\n"
            if len(text) + len(error_msg) > max_length:
                text += f"\n... [Results truncated at {max_length} characters for readability] ..."
                break
            text += error_msg
        else:
            # content is a string here
            content_str = str(content)  # Ensure it's a string for type safety
            source_header = f"\n--- Source: {results['organic'][i]['link']} ---\n"
            new_content = source_header + content_str + "\n"
            
            if len(text) + len(new_content) > max_length:
                # Add partial content if we have room
                remaining_space = max_length - len(text) - 100  # Leave room for truncation message
                if remaining_space > 500:  # Only add if we have meaningful space
                    text += source_header + content_str[:remaining_space] + "\n"
                text += f"\n... [Results truncated at {max_length} characters for readability] ..."
                break
            text += new_content
    
    return text.strip()

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
                    follow_redirects=True
                )
                response_time = time.time() - start_time
                results[library] = {
                    "status": "healthy",
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time * 1000, 2),
                    "url": url
                }
        except httpx.TimeoutException:
            results[library] = {
                "status": "timeout",
                "error": "Request timed out",
                "url": url
            }
        except Exception as e:
            results[library] = {
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    # Add cache stats if caching is enabled
    if cache:
        results["_cache_stats"] = {
            "enabled": True,
            "entries": len(cache.cache),
            "max_entries": cache.max_entries,
            "ttl_hours": cache.ttl_hours
        }
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
        entries_cleared = len(cache.cache)
        cache.cache.clear()
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
    
    # Count expired entries
    expired_count = sum(1 for entry in cache.cache.values() 
                       if cache._is_expired(entry['timestamp']))
    
    return {
        "enabled": True,
        "total_entries": len(cache.cache),
        "expired_entries": expired_count,
        "active_entries": len(cache.cache) - expired_count,
        "max_entries": cache.max_entries,
        "ttl_hours": cache.ttl_hours,
        "memory_usage_estimate": f"{len(str(cache.cache)) / 1024:.2f} KB"
    }

def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
    
