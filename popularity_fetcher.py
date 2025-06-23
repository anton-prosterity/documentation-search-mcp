import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
import os
from dataclasses import dataclass

@dataclass
class PopularityMetrics:
    github_stars: int = 0
    github_forks: int = 0
    github_issues: int = 0
    github_contributors: int = 0
    npm_weekly_downloads: int = 0
    pypi_monthly_downloads: int = 0
    stackoverflow_questions: int = 0
    github_last_commit: str = ""
    created_date: str = ""
    language: str = ""
    
    def calculate_overall_score(self) -> int:
        """Calculate a weighted overall popularity score (0-100)"""
        # Normalize metrics to 0-100 scale
        star_score = min(self.github_stars / 1000, 100)  # 1k stars = max points
        fork_score = min(self.github_forks / 200, 100)   # 200 forks = max points
        download_score = min((self.npm_weekly_downloads + self.pypi_monthly_downloads/4) / 10000, 100)
        so_score = min(self.stackoverflow_questions / 1000, 100)
        
        # Recency bonus (more active = higher score)
        recency_bonus = self._calculate_recency_bonus()
        
        # Weighted combination
        overall = (
            star_score * 0.4 +           # GitHub stars (40%)
            download_score * 0.3 +       # Downloads (30%)
            fork_score * 0.15 +          # Forks (15%)
            so_score * 0.1 +             # Stack Overflow (10%)
            recency_bonus * 0.05         # Recent activity (5%)
        )
        
        return min(int(overall), 100)
    
    def _calculate_recency_bonus(self) -> float:
        """Calculate bonus points for recent activity"""
        if not self.github_last_commit:
            return 0
        
        try:
            last_commit = datetime.fromisoformat(self.github_last_commit.replace('Z', '+00:00'))
            days_ago = (datetime.now().replace(tzinfo=None) - last_commit.replace(tzinfo=None)).days
            
            if days_ago <= 7:
                return 100    # Very active
            elif days_ago <= 30:
                return 80     # Active
            elif days_ago <= 90:
                return 60     # Moderately active
            elif days_ago <= 365:
                return 40     # Less active
            else:
                return 20     # Inactive
        except:
            return 0

class PopularityFetcher:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "User-Agent": "Documentation-Search-MCP/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    async def fetch_github_metrics(self, repo_url: str) -> Dict[str, Any]:
        """Fetch metrics from GitHub API"""
        try:
            # Extract owner/repo from URL
            if "github.com" not in repo_url:
                return {}
            
            parts = repo_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                return {}
            
            owner, repo = parts[0], parts[1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, headers=self.headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "stars": data.get("stargazers_count", 0),
                        "forks": data.get("forks_count", 0),
                        "issues": data.get("open_issues_count", 0),
                        "language": data.get("language", ""),
                        "created_at": data.get("created_at", ""),
                        "pushed_at": data.get("pushed_at", ""),
                        "subscribers_count": data.get("subscribers_count", 0)
                    }
        except Exception as e:
            print(f"Error fetching GitHub metrics: {e}")
        
        return {}
    
    async def fetch_npm_metrics(self, package_name: str) -> Dict[str, Any]:
        """Fetch NPM package metrics"""
        try:
            # NPM registry API
            registry_url = f"https://registry.npmjs.org/{package_name}"
            downloads_url = f"https://api.npmjs.org/downloads/point/last-week/{package_name}"
            
            async with httpx.AsyncClient() as client:
                # Get package info
                registry_response = await client.get(registry_url, timeout=10.0)
                downloads_response = await client.get(downloads_url, timeout=10.0)
                
                metrics = {}
                
                if registry_response.status_code == 200:
                    registry_data = registry_response.json()
                    metrics["repository"] = registry_data.get("repository", {}).get("url", "")
                    metrics["created"] = registry_data.get("time", {}).get("created", "")
                    metrics["modified"] = registry_data.get("time", {}).get("modified", "")
                
                if downloads_response.status_code == 200:
                    downloads_data = downloads_response.json()
                    metrics["weekly_downloads"] = downloads_data.get("downloads", 0)
                
                return metrics
                
        except Exception as e:
            print(f"Error fetching NPM metrics: {e}")
        
        return {}
    
    async def fetch_pypi_metrics(self, package_name: str) -> Dict[str, Any]:
        """Fetch PyPI package metrics"""
        try:
            pypi_url = f"https://pypi.org/pypi/{package_name}/json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(pypi_url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    info = data.get("info", {})
                    
                    return {
                        "description": info.get("summary", ""),
                        "home_page": info.get("home_page", ""),
                        "project_urls": info.get("project_urls", {}),
                        "requires_python": info.get("requires_python", ""),
                        "upload_time": list(data.get("releases", {}).keys())[-1] if data.get("releases") else ""
                    }
        except Exception as e:
            print(f"Error fetching PyPI metrics: {e}")
        
        return {}
    
    async def estimate_library_popularity(self, library_name: str, library_config: Dict[str, Any]) -> PopularityMetrics:
        """Estimate popularity for a library using multiple data sources"""
        metrics = PopularityMetrics()
        
        # Try to find GitHub repository
        github_repo = None
        url = library_config.get("url", "")
        
        # Common patterns to find GitHub repos
        github_searches = [
            f"https://github.com/{library_name}/{library_name}",
            f"https://github.com/{library_name}",
        ]
        
        # Check if URL contains GitHub
        if "github.com" in url:
            github_repo = url
        else:
            # Try common GitHub patterns
            for search_url in github_searches:
                github_metrics = await self.fetch_github_metrics(search_url)
                if github_metrics:
                    github_repo = search_url
                    break
        
        if github_repo:
            github_metrics = await self.fetch_github_metrics(github_repo)
            if github_metrics:
                metrics.github_stars = github_metrics.get("stars", 0)
                metrics.github_forks = github_metrics.get("forks", 0)
                metrics.github_issues = github_metrics.get("issues", 0)
                metrics.github_last_commit = github_metrics.get("pushed_at", "")
                metrics.created_date = github_metrics.get("created_at", "")
                metrics.language = github_metrics.get("language", "")
        
        # Try NPM for JavaScript packages
        if "javascript" in library_name.lower() or "js" in library_name.lower() or library_name in ["react", "express", "nodejs"]:
            npm_metrics = await self.fetch_npm_metrics(library_name)
            if npm_metrics:
                metrics.npm_weekly_downloads = npm_metrics.get("weekly_downloads", 0)
        
        # Try PyPI for Python packages
        python_packages = ["django", "flask", "fastapi", "pandas", "numpy", "matplotlib", "langchain"]
        if library_name in python_packages:
            pypi_metrics = await self.fetch_pypi_metrics(library_name)
            # Note: PyPI doesn't provide download stats in public API
            # You'd need services like pypistats.org for download numbers
        
        return metrics

async def update_popularity_scores():
    """Update popularity scores for all libraries"""
    fetcher = PopularityFetcher()
    
    # Load current config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    updated_config = {
        "cache": config.get("cache", {}),
        "docs_urls": {},
        "last_updated": datetime.now().isoformat(),
        "popularity_weights": {
            "github_stars": 0.4,
            "downloads": 0.3,
            "github_forks": 0.15,
            "stackoverflow": 0.1,
            "recency": 0.05
        }
    }
    
    print("🔄 Fetching real-time popularity data...")
    print("=" * 50)
    
    for lib_name, lib_url in config["docs_urls"].items():
        print(f"📊 Processing {lib_name}...")
        
        # Convert simple URL to config object if needed
        if isinstance(lib_url, str):
            lib_config = {"url": lib_url}
        else:
            lib_config = lib_url
        
        # Fetch popularity metrics
        metrics = await fetcher.estimate_library_popularity(lib_name, lib_config)
        overall_score = metrics.calculate_overall_score()
        
        # Create enhanced config
        updated_config["docs_urls"][lib_name] = {
            "url": lib_config.get("url", lib_url),
            "category": _categorize_library(lib_name),
            "popularity": {
                "overall_score": overall_score,
                "github_stars": f"{metrics.github_stars:,}" if metrics.github_stars > 0 else "N/A",
                "github_forks": f"{metrics.github_forks:,}" if metrics.github_forks > 0 else "N/A",
                "weekly_downloads": f"{metrics.npm_weekly_downloads:,}" if metrics.npm_weekly_downloads > 0 else "N/A",
                "language": metrics.language or "Unknown",
                "last_commit": metrics.github_last_commit[:10] if metrics.github_last_commit else "Unknown",
                "created_date": metrics.created_date[:10] if metrics.created_date else "Unknown",
                "learning_curve": _estimate_learning_curve(lib_name),
                "job_market": _estimate_job_market(lib_name, metrics),
                "maturity": _estimate_maturity(lib_name, metrics),
                "trending": _estimate_trending(lib_name, metrics)
            },
            "tags": _generate_tags(lib_name),
            "last_fetched": datetime.now().isoformat()
        }
        
        print(f"  ✅ Score: {overall_score}/100, Stars: {metrics.github_stars:,}")
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    # Save updated config
    with open("dynamic_config.json", "w") as f:
        json.dump(updated_config, f, indent=2)
    
    print(f"\n✅ Dynamic popularity scoring complete!")
    print(f"📁 Saved to: dynamic_config.json")
    
    return updated_config

def _categorize_library(lib_name: str) -> str:
    """Categorize library based on name"""
    categories = {
        "language": ["python", "javascript"],
        "web-framework": ["django", "flask", "fastapi", "express"],
        "frontend-framework": ["react", "angular", "vue"],
        "ai-framework": ["langchain", "llama-index", "anthropic", "openai"],
        "data-science": ["pandas", "numpy", "matplotlib", "streamlit"],
        "runtime": ["nodejs"],
        "devops": ["docker", "kubernetes", "terraform", "ansible"],
        "cloud": ["aws", "firebase", "vercel", "supabase"],
        "database": ["mongodb", "sql", "sqlalchemy"]
    }
    
    for category, libs in categories.items():
        if lib_name.lower() in libs:
            return category
    
    return "other"

def _estimate_learning_curve(lib_name: str) -> str:
    """Estimate learning curve based on library characteristics"""
    easy_libs = ["fastapi", "streamlit", "firebase"]
    steep_libs = ["django", "kubernetes", "terraform", "aws"]
    
    if lib_name in easy_libs:
        return "easy"
    elif lib_name in steep_libs:
        return "steep"
    else:
        return "moderate"

def _estimate_job_market(lib_name: str, metrics: PopularityMetrics) -> str:
    """Estimate job market demand"""
    hot_libs = ["react", "python", "javascript", "aws", "nodejs"]
    
    if lib_name in hot_libs or metrics.github_stars > 50000:
        return "excellent"
    elif metrics.github_stars > 20000:
        return "hot"
    elif metrics.github_stars > 5000:
        return "growing"
    else:
        return "stable"

def _estimate_maturity(lib_name: str, metrics: PopularityMetrics) -> str:
    """Estimate library maturity"""
    if metrics.created_date:
        try:
            created = datetime.fromisoformat(metrics.created_date.replace('Z', '+00:00'))
            age_years = (datetime.now().replace(tzinfo=None) - created.replace(tzinfo=None)).days / 365
            
            if age_years > 5:
                return "very-stable"
            elif age_years > 2:
                return "stable"
            else:
                return "evolving"
        except:
            pass
    
    stable_libs = ["python", "django", "react", "nodejs"]
    return "stable" if lib_name in stable_libs else "evolving"

def _estimate_trending(lib_name: str, metrics: PopularityMetrics) -> str:
    """Estimate trending status"""
    explosive_libs = ["langchain", "fastapi"]
    hot_libs = ["react", "python"]
    
    if lib_name in explosive_libs:
        return "explosive"
    elif lib_name in hot_libs or metrics.github_stars > 100000:
        return "hot"
    elif metrics.github_stars > 20000:
        return "growing"
    else:
        return "stable"

def _generate_tags(lib_name: str) -> list:
    """Generate tags for a library"""
    tag_mapping = {
        "python": ["programming-language", "backend", "data-science"],
        "javascript": ["programming-language", "frontend", "backend"],
        "react": ["frontend", "ui", "javascript", "spa"],
        "django": ["python", "web", "orm", "full-stack"],
        "fastapi": ["python", "api", "async", "modern"],
        "langchain": ["ai", "llm", "python", "chains"],
        "nodejs": ["javascript", "runtime", "backend", "npm"],
        "aws": ["cloud", "infrastructure", "devops"],
        "docker": ["containers", "devops", "deployment"]
    }
    
    return tag_mapping.get(lib_name.lower(), ["development"])

if __name__ == "__main__":
    print("🚀 Dynamic Popularity Scoring System")
    print("This will fetch real-time popularity data from GitHub, NPM, PyPI, etc.")
    print("\n⚠️  Note: Set GITHUB_TOKEN environment variable for higher API limits")
    
    asyncio.run(update_popularity_scores()) 