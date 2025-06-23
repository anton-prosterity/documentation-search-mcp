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
#Load the environment variables
load_dotenv()

#Initialize the MCP server
mcp = FastMCP("docs")
USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"


# TO DO: Add the API key to the .env file
SERPER_API_KEY = os.getenv("SERPER_API_KEY")



# Simple in-memory cache
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
                del self.cache[key]
        return None
    
    def set(self, key: str, data: str) -> None:
        # Clean up expired entries and enforce max size
        if len(self.cache) >= self.max_entries:
            # Remove oldest entries (simple FIFO)
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def clear_expired(self) -> None:
        expired_keys = [k for k, v in self.cache.items() 
                       if self._is_expired(v['timestamp'])]
        for key in expired_keys:
            del self.cache[key]

# Load configuration from external file
def load_config():
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
    payload = json.dumps({"q": query, "num": 2})
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    SERPER_URL, headers=headers, data=payload, 
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
    f"""
    Search the latest docs for a given query and library.
    Supports: {', '.join(sorted(docs_urls.keys()))}

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs
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
    for i, content in enumerate(contents):
        if isinstance(content, Exception):
            text += f"\n[Error fetching {results['organic'][i]['link']}: {content}]\n"
        else:
            text += f"\n--- Source: {results['organic'][i]['link']} ---\n{content}\n"
    
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

@mcp.tool()
async def recommend_libraries(use_case: str, experience_level: str = "intermediate"):
    """
    Recommend libraries based on use case and developer experience level.
    
    Args:
        use_case: The type of project (e.g., "web-api", "frontend", "ai", "data-science")
        experience_level: Developer experience ("beginner", "intermediate", "advanced")
    
    Returns:
        Ranked list of recommended libraries with popularity scores and reasoning
    """
    docs_data = config["docs_urls"]
    
    # Map use cases to relevant tags
    use_case_mapping = {
        "web-api": ["api", "web", "backend"],
        "frontend": ["frontend", "ui", "javascript"],
        "ai": ["ai", "llm", "ml"],
        "data-science": ["data-science", "data-analysis", "visualization"],
        "mobile": ["mobile", "app"],
        "devops": ["docker", "kubernetes", "deployment", "containers"],
        "cloud": ["cloud", "infrastructure", "scalability"]
    }
    
    # Experience level preferences
    experience_preferences = {
        "beginner": {"learning_curve": ["easy", "moderate"], "maturity": ["stable", "very-stable"]},
        "intermediate": {"learning_curve": ["moderate"], "maturity": ["stable", "evolving"]},
        "advanced": {"learning_curve": ["moderate", "steep"], "maturity": ["evolving", "stable"]}
    }
    
    relevant_tags = use_case_mapping.get(use_case.lower(), [])
    exp_prefs = experience_preferences.get(experience_level.lower(), experience_preferences["intermediate"])
    
    recommendations = []
    
    for lib_name, lib_data in docs_data.items():
        if isinstance(lib_data, dict) and "popularity" in lib_data:
            # Check if library matches use case
            lib_tags = lib_data.get("tags", [])
            tag_match = any(tag in lib_tags for tag in relevant_tags)
            
            if tag_match or not relevant_tags:  # Include all if no specific use case
                popularity = lib_data["popularity"]
                
                # Calculate relevance score
                relevance_score = popularity["overall_score"]
                
                # Adjust for experience level
                learning_curve = popularity.get("learning_curve", "moderate")
                maturity = popularity.get("maturity", "stable")
                
                if learning_curve in exp_prefs.get("learning_curve", []):
                    relevance_score += 5
                if maturity in exp_prefs.get("maturity", []):
                    relevance_score += 3
                
                # Boost trending libraries for intermediate/advanced users
                if experience_level != "beginner" and popularity.get("trending") in ["hot", "explosive"]:
                    relevance_score += 7
                
                recommendations.append({
                    "library": lib_name,
                    "score": min(relevance_score, 100),
                    "popularity": popularity,
                    "category": lib_data.get("category", "unknown"),
                    "tags": lib_tags,
                    "url": lib_data.get("url", ""),
                    "reasoning": f"Score: {min(relevance_score, 100)}/100, Learning: {learning_curve}, Market: {popularity.get('job_market', 'unknown')}"
                })
    
    # Sort by relevance score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "use_case": use_case,
        "experience_level": experience_level,
        "recommendations": recommendations[:10],  # Top 10
        "total_matches": len(recommendations)
    }

@mcp.tool()
async def compare_libraries(library_names: list):
    """
    Compare multiple libraries across various popularity metrics.
    
    Args:
        library_names: List of library names to compare (e.g., ["fastapi", "django", "flask"])
        
    Returns:
        Detailed comparison with scores, pros/cons, and recommendations
    """
    docs_data = config["docs_urls"]
    
    comparison = {
        "libraries": [],
        "winner": None,
        "summary": {}
    }
    
    for lib_name in library_names:
        if lib_name in docs_data and isinstance(docs_data[lib_name], dict):
            lib_data = docs_data[lib_name]
            if "popularity" in lib_data:
                popularity = lib_data["popularity"]
                
                # Calculate weighted score
                weights = config.get("popularity_weights", {})
                weighted_score = (
                    popularity["overall_score"] * 0.4 +
                    (90 if popularity.get("trending") == "explosive" else 
                     80 if popularity.get("trending") == "hot" else 
                     70 if popularity.get("trending") == "growing" else 60) * weights.get("trending", 0.1) +
                    (95 if popularity.get("job_market") == "excellent" else 
                     85 if popularity.get("job_market") == "hot" else 
                     75 if popularity.get("job_market") == "growing" else 50) * weights.get("job_market", 0.25)
                )
                
                comparison["libraries"].append({
                    "name": lib_name,
                    "overall_score": popularity["overall_score"],
                    "weighted_score": round(weighted_score, 1),
                    "github_stars": popularity.get("github_stars", "N/A"),
                    "learning_curve": popularity.get("learning_curve", "unknown"),
                    "job_market": popularity.get("job_market", "unknown"),
                    "maturity": popularity.get("maturity", "unknown"),
                    "trending": popularity.get("trending", "stable"),
                    "category": lib_data.get("category", "unknown"),
                    "pros": _get_library_pros(popularity),
                    "cons": _get_library_cons(popularity)
                })
    
    if comparison["libraries"]:
        # Find winner
        winner = max(comparison["libraries"], key=lambda x: x["weighted_score"])
        comparison["winner"] = winner["name"]
        
        # Generate summary
        comparison["summary"] = {
            "best_overall": winner["name"],
            "easiest_to_learn": min(comparison["libraries"], 
                                  key=lambda x: {"easy": 1, "moderate": 2, "steep": 3}.get(x["learning_curve"], 2))["name"],
            "most_popular": max(comparison["libraries"], key=lambda x: x["overall_score"])["name"],
            "hottest_trend": max(comparison["libraries"], 
                               key=lambda x: {"explosive": 4, "hot": 3, "growing": 2, "stable": 1}.get(x["trending"], 1))["name"]
        }
    
    return comparison

def _get_library_pros(popularity):
    """Generate pros based on popularity metrics"""
    pros = []
    
    if popularity.get("learning_curve") == "easy":
        pros.append("Easy to learn")
    if popularity.get("job_market") in ["excellent", "hot", "explosive"]:
        pros.append("High demand in job market")
    if popularity.get("trending") in ["hot", "explosive"]:
        pros.append("Rapidly growing community")
    if popularity.get("maturity") in ["stable", "very-stable"]:
        pros.append("Mature and reliable")
    
    return pros

def _get_library_cons(popularity):
    """Generate cons based on popularity metrics"""
    cons = []
    
    if popularity.get("learning_curve") == "steep":
        cons.append("Steep learning curve")
    if popularity.get("maturity") == "evolving":
        cons.append("Still evolving (breaking changes possible)")
    if popularity.get("trending") == "declining":
        cons.append("Declining popularity")
    
    return cons

@mcp.tool()
async def get_trending_libraries(time_period: str = "current", category: str = "all"):
    """
    Get trending libraries based on popularity metrics.
    
    Args:
        time_period: "current", "emerging", "stable"
        category: "all", "web-framework", "ai-framework", "language", etc.
        
    Returns:
        List of trending libraries with trend analysis
    """
    docs_data = config["docs_urls"]
    
    trending_libs = []
    
    for lib_name, lib_data in docs_data.items():
        if isinstance(lib_data, dict) and "popularity" in lib_data:
            lib_category = lib_data.get("category", "unknown")
            
            # Filter by category if specified
            if category != "all" and lib_category != category:
                continue
                
            popularity = lib_data["popularity"]
            trending_status = popularity.get("trending", "stable")
            
            # Filter by time period
            include = False
            if time_period == "current":
                include = trending_status in ["hot", "explosive", "growing"]
            elif time_period == "emerging":
                include = trending_status in ["explosive", "hot"]
            elif time_period == "stable":
                include = trending_status == "stable"
            else:
                include = True
            
            if include:
                trending_libs.append({
                    "library": lib_name,
                    "category": lib_category,
                    "trending": trending_status,
                    "overall_score": popularity["overall_score"],
                    "job_market": popularity.get("job_market", "unknown"),
                    "github_stars": popularity.get("github_stars", "N/A"),
                    "learning_curve": popularity.get("learning_curve", "moderate"),
                    "tags": lib_data.get("tags", [])
                })
    
    # Sort by trend intensity and overall score
    trend_weight = {"explosive": 4, "hot": 3, "growing": 2, "stable": 1, "declining": 0}
    trending_libs.sort(key=lambda x: (trend_weight.get(x["trending"], 1), x["overall_score"]), reverse=True)
    
    return {
        "time_period": time_period,
        "category": category,
        "trending_libraries": trending_libs,
        "count": len(trending_libs)
    }

@mcp.tool()
async def get_library_insights(library_name: str):
    """
    Get detailed insights about a specific library including popularity metrics.
    
    Args:
        library_name: Name of the library to analyze
        
    Returns:
        Comprehensive analysis of the library's popularity and characteristics
    """
    docs_data = config["docs_urls"]
    
    if library_name not in docs_data:
        return {"error": f"Library '{library_name}' not found in configuration"}
    
    lib_data = docs_data[library_name]
    if not isinstance(lib_data, dict) or "popularity" not in lib_data:
        return {"error": f"No popularity data available for '{library_name}'"}
    
    popularity = lib_data["popularity"]
    
    # Generate market position analysis
    market_position = "leader" if popularity["overall_score"] >= 90 else \
                     "strong" if popularity["overall_score"] >= 80 else \
                     "moderate" if popularity["overall_score"] >= 70 else "niche"
    
    # Calculate learning investment
    learning_investment = {
        "easy": "Low (1-2 weeks)",
        "moderate": "Medium (1-2 months)", 
        "steep": "High (3-6 months)"
    }.get(popularity.get("learning_curve", "moderate"), "Medium")
    
    # Job market outlook
    job_outlook = {
        "excellent": "Very high demand, abundant opportunities",
        "explosive": "Explosive growth, emerging market leader",
        "hot": "High demand, growing opportunities",
        "growing": "Moderate demand, increasing opportunities",
        "stable": "Steady demand, consistent opportunities",
        "declining": "Decreasing demand, limited opportunities"
    }.get(popularity.get("job_market", "stable"), "Unknown")
    
    return {
        "library": library_name,
        "category": lib_data.get("category", "unknown"),
        "url": lib_data.get("url", ""),
        "tags": lib_data.get("tags", []),
        "popularity_metrics": popularity,
        "analysis": {
            "market_position": market_position,
            "learning_investment": learning_investment,
            "job_outlook": job_outlook,
            "recommendation": _generate_recommendation(popularity),
            "best_for": _determine_best_use_cases(lib_data)
        }
    }

def _generate_recommendation(popularity):
    """Generate a recommendation based on popularity metrics"""
    score = popularity["overall_score"]
    learning = popularity.get("learning_curve", "moderate")
    trending = popularity.get("trending", "stable")
    job_market = popularity.get("job_market", "stable")
    
    if score >= 90 and learning == "easy":
        return "Highly recommended - Popular, easy to learn, great for beginners"
    elif score >= 85 and trending in ["hot", "explosive"]:
        return "Strongly recommended - Growing rapidly, good career investment"
    elif score >= 80 and job_market in ["excellent", "hot", "explosive"]:
        return "Recommended - Strong job market demand"
    elif learning == "steep" and score < 80:
        return "Consider alternatives - High learning curve for moderate benefits"
    else:
        return "Good choice - Solid option with decent popularity"

def _determine_best_use_cases(lib_data):
    """Determine best use cases based on tags and category"""
    tags = lib_data.get("tags", [])
    category = lib_data.get("category", "")
    
    use_cases = []
    
    if "api" in tags:
        use_cases.append("Building REST APIs")
    if "frontend" in tags:
        use_cases.append("Frontend development")
    if "ai" in tags or "llm" in tags:
        use_cases.append("AI/ML applications")
    if "web" in tags:
        use_cases.append("Web applications")
    if "data-science" in tags or "data-analysis" in tags:
        use_cases.append("Data analysis and science")
    if "devops" in tags:
        use_cases.append("DevOps and deployment")
    if "cloud" in tags:
        use_cases.append("Cloud infrastructure")
    
    return use_cases or ["General purpose development"]

if __name__ == "__main__":
    mcp.run(transport="stdio")
    
