import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import asyncio
import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from importlib import resources
from .smart_search import smart_search, SearchResult
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
async def get_docs(query: str, libraries: Union[str, List[str]]):
    """
    Search the latest docs for a given query and one or more libraries.

    Args:
        query: The query to search for (e.g., "Chroma DB")
        libraries: A single library or a list of libraries to search in (e.g., "langchain" or ["fastapi", "django"])

    Returns:
        Text from the docs (limited to ~50KB for readability)
    """
    
    if isinstance(libraries, str):
        libraries = [libraries]

    all_fetch_tasks = []
    all_urls = []
    library_results_map = {}

    for library in libraries:
        # Check auto-approve settings
        config = load_config()
        lib_config = config.get("docs_urls", {}).get(library, {})
        auto_approve = lib_config.get("auto_approve", True)
        
        if not auto_approve:
            # For libraries marked as requiring approval (like AWS, cloud services)
            print(f"⚠️  Requesting approval to search {library} documentation...")
        
        if library not in docs_urls:
            # Instead of raising an error, we'll just note it and continue
            print(f"⚠️ Library '{library}' not supported by this tool. Skipping.")
            continue
        
        search_query = f"site:{docs_urls[library]} {query}"
        results = await search_web(search_query)
        
        if results.get("organic"):
            links = [result["link"] for result in results["organic"]]
            library_results_map[library] = links
            all_urls.extend(links)
            all_fetch_tasks.extend([fetch_url(link) for link in links])

    # Clean expired cache entries periodically
    if cache:
        cache.clear_expired()

    if not all_fetch_tasks:
        return "No results found for the specified libraries."

    # Fetch all content concurrently
    fetched_contents = await asyncio.gather(*all_fetch_tasks, return_exceptions=True)
    
    # Create a direct map from URL to its content or error
    content_map = {url: content for url, content in zip(all_urls, fetched_contents)}

    library_outputs = []
    for library, links in library_results_map.items():
        lib_output = f"\n\n--- RESULTS FOR: {library.upper()} ---\n"
        
        for link in links:
            content = content_map.get(link)

            if isinstance(content, Exception):
                lib_output += f"\n[Error fetching {link}: {str(content)}]\n"
            else:
                content_str = str(content)
                source_header = f"\n--- Source: {link} ---\n"
                lib_output += source_header + content_str + "\n"
        
        library_outputs.append(lib_output)
    
    final_text = "".join(library_outputs)
    
    max_length = 50000
    if len(final_text) > max_length:
        final_text = final_text[:max_length] + "\n\n... [Results truncated for readability] ..."

    return final_text.strip()

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

@mcp.tool()
async def semantic_search(query: str, libraries: Union[str, List[str]], context: Optional[str] = None):
    """
    Enhanced semantic search across one or more libraries with relevance ranking.

    Args:
        query: The search query.
        libraries: A single library or a list of libraries to search in.
        context: Optional context about your project or use case.

    Returns:
        Enhanced search results with relevance scores and metadata, ranked across all libraries.
    """
    if isinstance(libraries, str):
        libraries = [libraries]

    search_tasks = [
        smart_search.semantic_search(query, lib, context) for lib in libraries
    ]
    
    try:
        results_by_library = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        all_results: List[SearchResult] = []
        for res_list in results_by_library:
            if not isinstance(res_list, Exception):
                all_results.extend(res_list) # type: ignore

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
                    "snippet": result.snippet[:300] + "..." if len(result.snippet) > 300 else result.snippet,
                    "relevance_score": result.relevance_score,
                    "content_type": result.content_type,
                    "difficulty_level": result.difficulty_level,
                    "estimated_read_time": f"{result.estimated_read_time} min",
                    "has_code_examples": result.code_snippets_count > 0
                }
                for result in all_results[:10]  # Top 10 combined results
            ]
        }
    except Exception as e:
        return {"error": f"Search failed: {str(e)}", "results": []}


@mcp.tool()
async def filtered_search(query: str, library: str, content_type: Optional[str] = None, 
                         difficulty_level: Optional[str] = None, has_code_examples: Optional[bool] = None):
    """
    Search with advanced filtering options.

    Args:
        query: The search query
        library: The library to search in
        content_type: Filter by content type ("tutorial", "reference", "example", "guide")
        difficulty_level: Filter by difficulty ("beginner", "intermediate", "advanced")
        has_code_examples: Filter for content with code examples (true/false)

    Returns:
        Filtered search results matching specified criteria
    """
    from .smart_search import filtered_search, SearchFilters
    
    filters = SearchFilters(
        content_type=content_type,
        difficulty_level=difficulty_level,
        has_code_examples=has_code_examples
    )
    
    try:
        results = await filtered_search.search_with_filters(query, library, filters)
        
        return {
            "query": query,
            "library": library,
            "filters_applied": {
                "content_type": content_type,
                "difficulty_level": difficulty_level,
                "has_code_examples": has_code_examples
            },
            "total_results": len(results),
            "results": [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet[:200] + "..." if len(result.snippet) > 200 else result.snippet,
                    "relevance_score": result.relevance_score,
                    "content_type": result.content_type,
                    "difficulty_level": result.difficulty_level,
                    "estimated_read_time": f"{result.estimated_read_time} min"
                }
                for result in results[:10]
            ]
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
    learning_paths = {
        # Frontend Development Paths
        "frontend-development": {
            "beginner": [
                {"topic": "HTML Fundamentals", "query": "html elements semantic structure", "type": "tutorial", "library": "html"},
                {"topic": "CSS Basics", "query": "css selectors properties styling", "type": "tutorial", "library": "css"},
                {"topic": "JavaScript Essentials", "query": "javascript variables functions DOM", "type": "tutorial", "library": "javascript"},
                {"topic": "Responsive Design", "query": "css responsive design flexbox", "type": "example", "library": "css"},
                {"topic": "Modern CSS Layout", "query": "css grid layout modern", "type": "tutorial", "library": "css"},
            ],
            "intermediate": [
                {"topic": "React Introduction", "query": "react components JSX props", "type": "tutorial", "library": "react"},
                {"topic": "State Management", "query": "react useState hooks", "type": "example", "library": "react"},
                {"topic": "CSS Frameworks", "query": "tailwind utility classes responsive", "type": "tutorial", "library": "tailwind"},
                {"topic": "Build Tools", "query": "vite development server bundling", "type": "tutorial", "library": "vite"},
                {"topic": "Version Control", "query": "git workflow branches commits", "type": "tutorial", "library": "git"},
            ],
            "advanced": [
                {"topic": "Advanced React", "query": "react performance optimization", "type": "tutorial", "library": "react"},
                {"topic": "State Management", "query": "redux state management", "type": "tutorial", "library": "redux"},
                {"topic": "Next.js Framework", "query": "nextjs SSR routing", "type": "tutorial", "library": "nextjs"},
                {"topic": "Testing", "query": "jest testing components", "type": "tutorial", "library": "jest"},
                {"topic": "CI/CD Deployment", "query": "github actions frontend deployment", "type": "tutorial", "library": "github-actions"},
            ]
        },
        
        # Backend Development Paths
        "backend-development": {
            "beginner": [
                {"topic": "Python Basics", "query": "python functions classes basics", "type": "tutorial", "library": "python"},
                {"topic": "API Fundamentals", "query": "fastapi hello world first api", "type": "tutorial", "library": "fastapi"},
                {"topic": "Database Basics", "query": "postgresql tables queries", "type": "tutorial", "library": "postgresql"},
                {"topic": "Request Handling", "query": "fastapi request body validation", "type": "example", "library": "fastapi"},
                {"topic": "Git Version Control", "query": "git commit push pull basics", "type": "tutorial", "library": "git"},
            ],
            "intermediate": [
                {"topic": "Database Integration", "query": "fastapi sqlalchemy database", "type": "tutorial", "library": "fastapi"},
                {"topic": "NoSQL Databases", "query": "mongodb collections documents", "type": "tutorial", "library": "mongodb"},
                {"topic": "Authentication", "query": "fastapi JWT authentication", "type": "tutorial", "library": "fastapi"},
                {"topic": "API Testing", "query": "pytest fastapi testing", "type": "tutorial", "library": "pytest"},
                {"topic": "API Documentation", "query": "openapi swagger specification", "type": "tutorial", "library": "openapi"},
            ],
            "advanced": [
                {"topic": "Microservices", "query": "fastapi microservices architecture", "type": "tutorial", "library": "fastapi"},
                {"topic": "Containerization", "query": "docker python application", "type": "tutorial", "library": "docker"},
                {"topic": "CI/CD Pipelines", "query": "github actions python deployment", "type": "tutorial", "library": "github-actions"},
                {"topic": "Monitoring", "query": "fastapi logging monitoring", "type": "tutorial", "library": "fastapi"},
                {"topic": "Cloud Deployment", "query": "aws deployment docker", "type": "tutorial", "library": "aws"},
            ]
        },
        
        # Full-Stack Development Paths
        "fullstack-development": {
            "beginner": [
                {"topic": "Web Fundamentals", "query": "html css javascript basics", "type": "tutorial", "library": "html"},
                {"topic": "Frontend Framework", "query": "react components state", "type": "tutorial", "library": "react"},
                {"topic": "Backend API", "query": "fastapi rest api", "type": "tutorial", "library": "fastapi"},
                {"topic": "Database Setup", "query": "mongodb setup collections", "type": "tutorial", "library": "mongodb"},
                {"topic": "Version Control", "query": "git workflow collaboration", "type": "tutorial", "library": "git"},
            ],
            "intermediate": [
                {"topic": "MERN Stack Setup", "query": "mongodb express react nodejs", "type": "tutorial", "library": "mongodb"},
                {"topic": "State Management", "query": "redux react state", "type": "tutorial", "library": "redux"},
                {"topic": "API Design", "query": "openapi rest specification", "type": "tutorial", "library": "openapi"},
                {"topic": "Authentication Flow", "query": "JWT react fastapi authentication", "type": "tutorial", "library": "fastapi"},
                {"topic": "Testing Strategy", "query": "jest pytest testing", "type": "tutorial", "library": "jest"},
            ],
            "advanced": [
                {"topic": "Advanced Architecture", "query": "microservices react fastapi", "type": "tutorial", "library": "fastapi"},
                {"topic": "Performance Optimization", "query": "react performance database optimization", "type": "tutorial", "library": "react"},
                {"topic": "DevOps Integration", "query": "docker kubernetes deployment", "type": "tutorial", "library": "docker"},
                {"topic": "CI/CD Pipeline", "query": "github actions fullstack deployment", "type": "tutorial", "library": "github-actions"},
                {"topic": "Production Deployment", "query": "aws production deployment", "type": "tutorial", "library": "aws"},
            ]
        },
        
        # DevOps & Deployment Paths  
        "devops": {
            "beginner": [
                {"topic": "Git Workflows", "query": "git branches merging collaboration", "type": "tutorial", "library": "git"},
                {"topic": "Docker Basics", "query": "docker containers images", "type": "tutorial", "library": "docker"},
                {"topic": "CI/CD Concepts", "query": "github actions workflow automation", "type": "tutorial", "library": "github-actions"},
                {"topic": "Testing Automation", "query": "pytest jest automated testing", "type": "tutorial", "library": "pytest"},
                {"topic": "Basic Deployment", "query": "docker deployment simple", "type": "tutorial", "library": "docker"},
            ],
            "intermediate": [
                {"topic": "Advanced Git", "query": "git rebase cherry-pick advanced", "type": "tutorial", "library": "git"},
                {"topic": "Container Orchestration", "query": "kubernetes pods services", "type": "tutorial", "library": "kubernetes"},
                {"topic": "Infrastructure as Code", "query": "terraform infrastructure automation", "type": "tutorial", "library": "terraform"},
                {"topic": "Cloud Platforms", "query": "aws services deployment", "type": "tutorial", "library": "aws"},
                {"topic": "Monitoring Setup", "query": "monitoring logging production", "type": "tutorial", "library": "docker"},
            ],
            "advanced": [
                {"topic": "Advanced Kubernetes", "query": "kubernetes advanced deployment", "type": "tutorial", "library": "kubernetes"},
                {"topic": "Multi-Cloud Strategy", "query": "aws google-cloud deployment", "type": "tutorial", "library": "aws"},
                {"topic": "Security Practices", "query": "docker security kubernetes", "type": "tutorial", "library": "docker"},
                {"topic": "Scaling Strategies", "query": "kubernetes scaling performance", "type": "tutorial", "library": "kubernetes"},
                {"topic": "Production Operations", "query": "terraform production management", "type": "tutorial", "library": "terraform"},
            ]
        },
        
        # Enhanced Individual Library Paths
        "react": {
            "beginner": [
                {"topic": "HTML/CSS Foundation", "query": "html semantic elements", "type": "tutorial", "library": "html"},
                {"topic": "JavaScript Essentials", "query": "javascript fundamentals", "type": "tutorial", "library": "javascript"},
                {"topic": "React Basics", "query": "react components JSX props", "type": "tutorial", "library": "react"},
                {"topic": "State Management", "query": "react useState hooks", "type": "example", "library": "react"},
                {"topic": "Styling with CSS", "query": "css styling react components", "type": "example", "library": "css"},
            ],
            "intermediate": [
                {"topic": "Advanced Hooks", "query": "react useEffect custom hooks", "type": "tutorial", "library": "react"},
                {"topic": "Routing", "query": "react router navigation", "type": "tutorial", "library": "react"},
                {"topic": "CSS Frameworks", "query": "tailwind react integration", "type": "tutorial", "library": "tailwind"},
                {"topic": "State Libraries", "query": "zustand react state", "type": "example", "library": "zustand"},
                {"topic": "Build Tools", "query": "vite react development", "type": "tutorial", "library": "vite"},
            ],
            "advanced": [
                {"topic": "Redux Integration", "query": "redux react complex state", "type": "tutorial", "library": "redux"},
                {"topic": "Next.js Framework", "query": "nextjs react SSR", "type": "tutorial", "library": "nextjs"},
                {"topic": "Testing Strategy", "query": "jest react testing", "type": "tutorial", "library": "jest"},
                {"topic": "Performance", "query": "react performance optimization", "type": "tutorial", "library": "react"},
                {"topic": "Deployment", "query": "github actions react deployment", "type": "tutorial", "library": "github-actions"},
            ]
        },
        
        "fastapi": {
            "beginner": [
                {"topic": "Python Foundation", "query": "python basics functions", "type": "tutorial", "library": "python"},
                {"topic": "FastAPI Setup", "query": "fastapi installation first api", "type": "tutorial", "library": "fastapi"},
                {"topic": "Request Handling", "query": "fastapi path parameters", "type": "example", "library": "fastapi"},
                {"topic": "Data Validation", "query": "pydantic models validation", "type": "tutorial", "library": "pydantic"},
                {"topic": "Git Basics", "query": "git commit push basics", "type": "tutorial", "library": "git"},
            ],
            "intermediate": [
                {"topic": "Database Integration", "query": "fastapi sqlalchemy postgresql", "type": "tutorial", "library": "fastapi"},
                {"topic": "NoSQL with MongoDB", "query": "fastapi mongodb integration", "type": "tutorial", "library": "mongodb"},
                {"topic": "Authentication", "query": "fastapi JWT authentication", "type": "tutorial", "library": "fastapi"},
                {"topic": "API Documentation", "query": "openapi swagger fastapi", "type": "tutorial", "library": "openapi"},
                {"topic": "Testing", "query": "pytest fastapi testing", "type": "tutorial", "library": "pytest"},
            ],
            "advanced": [
                {"topic": "Advanced Features", "query": "fastapi dependency injection", "type": "reference", "library": "fastapi"},
                {"topic": "Containerization", "query": "docker fastapi deployment", "type": "tutorial", "library": "docker"},
                {"topic": "CI/CD Pipeline", "query": "github actions fastapi", "type": "tutorial", "library": "github-actions"},
                {"topic": "Cloud Deployment", "query": "aws fastapi production", "type": "tutorial", "library": "aws"},
                {"topic": "Monitoring", "query": "fastapi monitoring logging", "type": "tutorial", "library": "fastapi"},
            ]
        },
        
        # New Technology-Specific Paths
        "git": {
            "beginner": [
                {"topic": "Git Basics", "query": "git init commit status", "type": "tutorial", "library": "git"},
                {"topic": "Working with Files", "query": "git add commit push", "type": "tutorial", "library": "git"},
                {"topic": "Branching", "query": "git branch checkout merge", "type": "tutorial", "library": "git"},
                {"topic": "Remote Repositories", "query": "git remote origin push pull", "type": "tutorial", "library": "git"},
                {"topic": "Basic Collaboration", "query": "git clone fork collaboration", "type": "tutorial", "library": "git"},
            ],
            "intermediate": [
                {"topic": "Merge Conflicts", "query": "git merge conflicts resolution", "type": "tutorial", "library": "git"},
                {"topic": "Git Workflows", "query": "git workflow gitflow", "type": "tutorial", "library": "git"},
                {"topic": "Rebasing", "query": "git rebase interactive", "type": "tutorial", "library": "git"},
                {"topic": "Stashing", "query": "git stash temporary changes", "type": "tutorial", "library": "git"},
                {"topic": "Tags and Releases", "query": "git tag versioning", "type": "tutorial", "library": "git"},
            ],
            "advanced": [
                {"topic": "Advanced Rebasing", "query": "git rebase cherry-pick", "type": "tutorial", "library": "git"},
                {"topic": "Git Hooks", "query": "git hooks automation", "type": "tutorial", "library": "git"},
                {"topic": "Submodules", "query": "git submodules management", "type": "reference", "library": "git"},
                {"topic": "Performance", "query": "git performance large repos", "type": "tutorial", "library": "git"},
                {"topic": "CI/CD Integration", "query": "git github actions integration", "type": "tutorial", "library": "github-actions"},
            ]
        },
        
        "mongodb": {
            "beginner": [
                {"topic": "MongoDB Basics", "query": "mongodb documents collections", "type": "tutorial", "library": "mongodb"},
                {"topic": "CRUD Operations", "query": "mongodb insert find update delete", "type": "tutorial", "library": "mongodb"},
                {"topic": "Data Modeling", "query": "mongodb schema design", "type": "tutorial", "library": "mongodb"},
                {"topic": "Querying", "query": "mongodb queries filtering", "type": "example", "library": "mongodb"},
                {"topic": "Indexes", "query": "mongodb indexes performance", "type": "tutorial", "library": "mongodb"},
            ],
            "intermediate": [
                {"topic": "Aggregation Framework", "query": "mongodb aggregation pipeline", "type": "tutorial", "library": "mongodb"},
                {"topic": "Relationships", "query": "mongodb references embedding", "type": "tutorial", "library": "mongodb"},
                {"topic": "Transactions", "query": "mongodb transactions ACID", "type": "tutorial", "library": "mongodb"},
                {"topic": "Atlas Cloud", "query": "mongodb atlas setup", "type": "tutorial", "library": "mongodb"},
                {"topic": "Integration", "query": "mongodb fastapi python", "type": "tutorial", "library": "mongodb"},
            ],
            "advanced": [
                {"topic": "Advanced Aggregation", "query": "mongodb complex aggregation", "type": "tutorial", "library": "mongodb"},
                {"topic": "Sharding", "query": "mongodb sharding scaling", "type": "tutorial", "library": "mongodb"},
                {"topic": "Replication", "query": "mongodb replica sets", "type": "tutorial", "library": "mongodb"},
                {"topic": "Performance Tuning", "query": "mongodb optimization performance", "type": "tutorial", "library": "mongodb"},
                {"topic": "Security", "query": "mongodb security authentication", "type": "tutorial", "library": "mongodb"},
            ]
        },
        
        "github-actions": {
            "beginner": [
                {"topic": "GitHub Actions Basics", "query": "github actions workflow syntax", "type": "tutorial", "library": "github-actions"},
                {"topic": "First Workflow", "query": "github actions hello world", "type": "tutorial", "library": "github-actions"},
                {"topic": "Triggers and Events", "query": "github actions push pull request", "type": "tutorial", "library": "github-actions"},
                {"topic": "Basic CI", "query": "github actions continuous integration", "type": "tutorial", "library": "github-actions"},
                {"topic": "Job Configuration", "query": "github actions jobs steps", "type": "tutorial", "library": "github-actions"},
            ],
            "intermediate": [
                {"topic": "Testing Automation", "query": "github actions testing workflows", "type": "tutorial", "library": "github-actions"},
                {"topic": "Build and Deploy", "query": "github actions deployment pipeline", "type": "tutorial", "library": "github-actions"},
                {"topic": "Environment Variables", "query": "github actions secrets environment", "type": "tutorial", "library": "github-actions"},
                {"topic": "Matrix Builds", "query": "github actions matrix strategy", "type": "tutorial", "library": "github-actions"},
                {"topic": "Caching", "query": "github actions cache dependencies", "type": "tutorial", "library": "github-actions"},
            ],
            "advanced": [
                {"topic": "Custom Actions", "query": "github actions custom action", "type": "tutorial", "library": "github-actions"},
                {"topic": "Complex Workflows", "query": "github actions advanced workflows", "type": "tutorial", "library": "github-actions"},
                {"topic": "Security", "query": "github actions security best practices", "type": "tutorial", "library": "github-actions"},
                {"topic": "Self-Hosted Runners", "query": "github actions self hosted runners", "type": "tutorial", "library": "github-actions"},
                {"topic": "Integration", "query": "github actions docker kubernetes", "type": "tutorial", "library": "github-actions"},
            ]
        },
        
        "openapi": {
            "beginner": [
                {"topic": "API Documentation Basics", "query": "openapi specification intro", "type": "tutorial", "library": "openapi"},
                {"topic": "Swagger UI", "query": "swagger ui documentation", "type": "tutorial", "library": "openapi"},
                {"topic": "Basic Specification", "query": "openapi yaml json structure", "type": "tutorial", "library": "openapi"},
                {"topic": "Paths and Operations", "query": "openapi paths methods", "type": "tutorial", "library": "openapi"},
                {"topic": "Request/Response", "query": "openapi request response models", "type": "tutorial", "library": "openapi"},
            ],
            "intermediate": [
                {"topic": "Data Models", "query": "openapi schemas components", "type": "tutorial", "library": "openapi"},
                {"topic": "Authentication", "query": "openapi security schemes", "type": "tutorial", "library": "openapi"},
                {"topic": "Validation", "query": "openapi validation constraints", "type": "tutorial", "library": "openapi"},
                {"topic": "Code Generation", "query": "openapi code generation", "type": "tutorial", "library": "openapi"},
                {"topic": "API Testing", "query": "openapi testing tools", "type": "tutorial", "library": "openapi"},
            ],
            "advanced": [
                {"topic": "Advanced Schemas", "query": "openapi advanced schemas", "type": "tutorial", "library": "openapi"},
                {"topic": "API Versioning", "query": "openapi versioning strategies", "type": "tutorial", "library": "openapi"},
                {"topic": "Integration", "query": "openapi fastapi integration", "type": "tutorial", "library": "openapi"},
                {"topic": "Documentation Automation", "query": "openapi automated documentation", "type": "tutorial", "library": "openapi"},
                {"topic": "Best Practices", "query": "openapi design best practices", "type": "tutorial", "library": "openapi"},
            ]
        }
    }
    
    if library not in learning_paths:
        return {"error": f"Learning path not available for {library}"}
    
    if experience_level not in learning_paths[library]:
        return {"error": f"Experience level {experience_level} not supported"}
    
    path = learning_paths[library][experience_level]
    
    # Calculate enhanced metadata
    total_topics = len(path)
    estimated_time = f"{total_topics * 2}-{total_topics * 4} hours"
    
    # Build learning path with library references
    learning_steps = []
    for i, item in enumerate(path):
        step = {
            "step": i + 1,
            "topic": item["topic"],
            "content_type": item["type"],
            "search_query": item["query"],
            "target_library": item.get("library", library),
            "estimated_time": "2-4 hours"
        }
        learning_steps.append(step)
    
    return {
        "library": library,
        "experience_level": experience_level,
        "total_topics": total_topics,
        "estimated_total_time": estimated_time,
        "learning_path": learning_steps,
        "next_level": {
            "beginner": "intermediate",
            "intermediate": "advanced", 
            "advanced": "Consider specializing in specific areas or exploring related technologies"
        }.get(experience_level, ""),
        "related_paths": _get_related_learning_paths(library),
        "prerequisites": _get_prerequisites(library, experience_level)
    }

def _get_related_learning_paths(library: str) -> List[str]:
    """Get related learning paths for cross-skill development"""
    relationships = {
        "react": ["frontend-development", "fullstack-development", "javascript", "nextjs"],
        "fastapi": ["backend-development", "fullstack-development", "python", "mongodb"],
        "git": ["devops", "github-actions", "frontend-development", "backend-development"],
        "mongodb": ["backend-development", "fullstack-development", "fastapi"],
        "github-actions": ["devops", "git", "docker", "kubernetes"],
        "openapi": ["fastapi", "backend-development", "fullstack-development"],
        "frontend-development": ["react", "nextjs", "javascript", "css"],
        "backend-development": ["fastapi", "python", "mongodb", "postgresql"],
        "fullstack-development": ["frontend-development", "backend-development", "react", "fastapi"],
        "devops": ["git", "docker", "kubernetes", "github-actions"]
    }
    return relationships.get(library, [])

def _get_prerequisites(library: str, experience_level: str) -> List[str]:
    """Get prerequisites for learning paths"""
    if experience_level == "beginner":
        return []
    
    prerequisites = {
        "react": ["HTML basics", "CSS fundamentals", "JavaScript essentials"],
        "fastapi": ["Python basics", "HTTP fundamentals", "API concepts"],
        "fullstack-development": ["HTML/CSS basics", "JavaScript fundamentals", "Python basics"],
        "devops": ["Command line basics", "Git fundamentals", "Basic development experience"],
        "mongodb": ["Database concepts", "JSON understanding"],
        "github-actions": ["Git basics", "YAML syntax", "CI/CD concepts"],
        "openapi": ["API concepts", "HTTP methods", "JSON/YAML syntax"]
    }
    
    return prerequisites.get(library, [])

@mcp.tool()
async def get_code_examples(library: str, topic: str, language: str = "python"):
    """
    Get curated code examples for a specific topic and library.

    Args:
        library: The library to search for examples
        topic: The specific topic or feature
        language: Programming language for examples

    Returns:
        Curated code examples with explanations
    """
    
    # Enhanced query for code-specific search
    code_query = f"{library} {topic} example code {language}"
    
    try:
        # Use filtered search to find examples with code
        from .smart_search import filtered_search, SearchFilters
        
        filters = SearchFilters(
            content_type="example",
            has_code_examples=True
        )
        
        results = await filtered_search.search_with_filters(code_query, library, filters)
        
        if not results:
            # Fallback to regular search
            config = load_config()
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
            code_pattern = r'```(?:python|javascript|typescript|js)?\n(.*?)```'
            matches = re.finditer(code_pattern, content, re.DOTALL)
            
            for i, match in enumerate(matches):
                if i >= 3:  # Limit to 3 examples
                    break
                code_blocks.append({
                    "example": i + 1,
                    "code": match.group(1).strip(),
                    "language": language,
                    "source_url": first_result["link"]
                })
            
            return {
                "library": library,
                "topic": topic,
                "language": language,
                "total_examples": len(code_blocks),
                "examples": code_blocks
            }
        
        else:
            # Process enhanced results
            examples = []
            for i, result in enumerate(results[:3]):
                examples.append({
                    "example": i + 1,
                    "title": result.title,
                    "description": result.snippet[:200] + "..." if len(result.snippet) > 200 else result.snippet,
                    "url": result.url,
                    "difficulty": result.difficulty_level,
                    "estimated_read_time": f"{result.estimated_read_time} min"
                })
            
            return {
                "library": library,
                "topic": topic,
                "language": language,
                "total_examples": len(examples),
                "examples": examples
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
            "max_concurrent_requests": config["server_config"]["max_concurrent_requests"],
            "request_timeout_seconds": config["server_config"]["request_timeout_seconds"],
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
        "available_libraries": list(config_manager.get_docs_urls().keys())[:10]  # Show first 10
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
    from .vulnerability_scanner import vulnerability_scanner
    
    try:
        # Perform comprehensive scan
        security_report = await vulnerability_scanner.scan_library(library_name, ecosystem)
        
        return {
            "scan_results": security_report.to_dict(),
            "summary": {
                "library": security_report.library_name,
                "ecosystem": security_report.ecosystem,
                "security_score": security_report.security_score,
                "risk_level": (
                    "🚨 High Risk" if security_report.security_score < 50 else
                    "⚠️ Medium Risk" if security_report.security_score < 70 else
                    "✅ Low Risk" if security_report.security_score < 90 else
                    "🛡️ Excellent"
                ),
                "critical_vulnerabilities": security_report.critical_count,
                "total_vulnerabilities": security_report.total_vulnerabilities,
                "primary_recommendation": security_report.recommendations[0] if security_report.recommendations else "No specific recommendations"
            },
            "scan_timestamp": security_report.scan_date,
            "sources": ["OSV Database", "GitHub Security Advisories", "Safety DB (PyPI only)"]
        }
        
    except Exception as e:
        return {
            "error": f"Vulnerability scan failed: {str(e)}",
            "library": library_name,
            "ecosystem": ecosystem,
            "scan_timestamp": datetime.now().isoformat()
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
    from .vulnerability_scanner import security_integration
    
    try:
        summary = await security_integration.get_security_summary(library_name, ecosystem)
        
        # Add security badge
        score = summary.get("security_score", 50)
        if score >= 90:
            badge = "🛡️ EXCELLENT"
            color = "green"
        elif score >= 70:
            badge = "✅ SECURE"
            color = "green"
        elif score >= 50:
            badge = "⚠️ CAUTION"
            color = "yellow"
        else:
            badge = "🚨 HIGH RISK"
            color = "red"
        
        return {
            "library": library_name,
            "ecosystem": ecosystem,
            "security_badge": badge,
            "security_score": score,
            "status": summary.get("status", "unknown"),
            "vulnerabilities": {
                "total": summary.get("total_vulnerabilities", 0),
                "critical": summary.get("critical_vulnerabilities", 0)
            },
            "recommendation": summary.get("primary_recommendation", "No recommendations available"),
            "last_scanned": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "library": library_name,
            "ecosystem": ecosystem,
            "security_badge": "❓ UNKNOWN",
            "security_score": None,
            "status": "scan_failed",
            "error": str(e)
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
    from .vulnerability_scanner import security_integration
    
    if len(libraries) > 10:
        return {"error": "Maximum 10 libraries allowed for comparison"}
    
    results = []
    
    # Scan all libraries in parallel for faster comparison
    scan_tasks = [
        security_integration.get_security_summary(lib, ecosystem) 
        for lib in libraries
    ]
    
    try:
        summaries = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        for i, (library, summary_item) in enumerate(zip(libraries, summaries)):
            if isinstance(summary_item, Exception):
                results.append({
                    "library": library,
                    "security_score": 0,
                    "status": "scan_failed",
                    "error": str(summary_item)
                })
            else:
                summary = summary_item
                results.append({
                    "library": library,
                    "security_score": summary.get("security_score", 0),  # type: ignore
                    "status": summary.get("status", "unknown"),  # type: ignore
                    "vulnerabilities": summary.get("total_vulnerabilities", 0),  # type: ignore
                    "critical_vulnerabilities": summary.get("critical_vulnerabilities", 0),  # type: ignore
                    "recommendation": summary.get("primary_recommendation", "")  # type: ignore
                })
        
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
            worst_lib = results[-1]
            
            if best_lib.get("security_score", 0) >= 80:
                overall_rec = f"✅ Recommended: {best_lib['library']} has excellent security"
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
            "ecosystem": ecosystem
        }
        
    except Exception as e:
        return {
            "error": f"Security comparison failed: {str(e)}",
            "libraries": libraries,
            "ecosystem": ecosystem
        }


@mcp.tool()
async def suggest_secure_libraries(partial_name: str, include_security_score: bool = True):
    """
    Enhanced library suggestions that include security scores for informed decisions.

    Args:
        partial_name: Partial library name to search for
        include_security_score: Whether to include security scores (slower but more informative)

    Returns:
        Library suggestions with optional security information
    """
    # Get basic suggestions first
    basic_suggestions = await suggest_libraries(partial_name)
    
    if not include_security_score or not basic_suggestions:
        return {
            "suggestions": basic_suggestions,
            "partial_name": partial_name,
            "security_info_included": False
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
                suggestion.update({
                    "security_score": None,
                    "security_status": "unknown",
                    "security_badge": "❓"
                })
            else:
                security_result = sec_res_item
                score = security_result.get("security_score", 50)
                suggestion.update({
                    "security_score": score,
                    "security_status": security_result.get("status", "unknown"),  # type: ignore
                    "security_badge": (
                        "🛡️" if score >= 90 else
                        "✅" if score >= 70 else
                        "⚠️" if score >= 50 else
                        "🚨"
                    ),
                    "vulnerabilities": security_result.get("total_vulnerabilities", 0)  # type: ignore
                })
            
            enhanced_suggestions.append(suggestion)
        
        # Add remaining suggestions without security info
        for lib in basic_suggestions[5:]:
            enhanced_suggestions.append({
                "library": lib,
                "security_score": None,
                "security_status": "not_scanned",
                "note": "Use scan_library_vulnerabilities for security details"
            })
        
        # Sort by security score for enhanced suggestions
        enhanced_suggestions.sort(
            key=lambda x: x.get("security_score") or 0, 
            reverse=True
        )
        
        return {
            "suggestions": enhanced_suggestions,
            "partial_name": partial_name,
            "security_info_included": True,
            "total_suggestions": len(enhanced_suggestions),
            "note": "Libraries with security scores are sorted by security rating"
        }
        
    except Exception as e:
        return {
            "suggestions": [{"library": lib} for lib in basic_suggestions],
            "partial_name": partial_name,
            "security_info_included": False,
            "error": f"Security enhancement failed: {str(e)}"
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
            "message": "Supported files are pyproject.toml, requirements.txt, or package.json."
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
                "message": "No dependencies found to scan."
            },
            "vulnerable_packages": []
        }

    total_deps = len(dependencies)
    print(f"🔎 Found {total_deps} dependencies in '{filename}'. Scanning for vulnerabilities...")

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
                vulnerable_deps.append({
                    "library": dep_name,
                    "version": dependencies[dep_name],
                    "vulnerability_count": report.total_vulnerabilities,  # type: ignore
                    "security_score": report.security_score,
                    "summary": report.recommendations[0] if report.recommendations else "Update to the latest version.",
                    "details": [vuln.to_dict() for vuln in report.vulnerabilities[:3]] # Top 3
                })

    vulnerable_deps.sort(key=lambda x: x["security_score"])

    return {
        "summary": {
            "dependency_file": filename,
            "ecosystem": ecosystem,
            "total_dependencies": total_deps,
            "vulnerable_count": len(vulnerable_deps),
            "overall_project_risk": "High" if any(d['security_score'] < 50 for d in vulnerable_deps) else "Medium" if any(d['security_score'] < 70 for d in vulnerable_deps) else "Low",
        },
        "vulnerable_packages": vulnerable_deps
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
            
        result['user_summary'] = summary
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
            return {"error": f"Service '{service}' not supported.", "available_services": list(TEMPLATES.keys())}
            
        compose_file = create_docker_compose(service, project_path)
        
        return {
            "status": "success",
            "message": f"✅ Successfully created 'docker-compose.yml' for '{service}' in '{project_path}'.",
            "next_steps": [
                f"1. Review the generated file: {compose_file}",
                "2. Run the service: docker-compose up -d",
                "3. To stop the service: docker-compose down"
            ],
            "service_details": TEMPLATES[service]['services']
        }
        
    except (ValueError, FileExistsError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
    
