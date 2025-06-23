#!/usr/bin/env python3
"""
Dynamic Configuration Enhancer
Fetches real-time data from APIs to enhance simple base configuration
"""

import asyncio
import httpx
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os

@dataclass
class LibraryMetrics:
    github_stars: int = 0
    github_forks: int = 0
    github_contributors: int = 0
    github_last_push: str = ""
    npm_weekly_downloads: int = 0
    pypi_monthly_downloads: int = 0
    documentation_last_updated: str = ""
    
class DynamicEnhancer:
    """Enhances simple config with real-time API data"""
    
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.cache = {}
        self.cache_ttl = timedelta(hours=6)  # Cache for 6 hours
        
    async def enhance_library(self, lib_name: str, lib_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance a single library with real-time data"""
        enhanced = lib_data.copy()
        
        try:
            # Get cached or fetch fresh metrics
            metrics = await self._get_library_metrics(lib_name, lib_data)
            
            # Calculate dynamic popularity data
            enhanced["popularity"] = await self._calculate_popularity(lib_name, metrics, lib_data)
            enhanced["metrics"] = {
                "github_stars": metrics.github_stars,
                "github_forks": metrics.github_forks,
                "last_updated": datetime.now().isoformat(),
                "data_freshness": "real-time"
            }
            
        except Exception as e:
            print(f"⚠️ Failed to enhance {lib_name}: {e}")
            # Fallback to static data
            enhanced["popularity"] = lib_data.get("popularity", self._get_default_popularity())
            enhanced["metrics"] = {"data_freshness": "fallback"}
        
        return enhanced
    
    async def _get_library_metrics(self, lib_name: str, lib_data: Dict[str, Any]) -> LibraryMetrics:
        """Get metrics from cache or fetch from APIs"""
        cache_key = f"metrics_{lib_name}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data
        
        # Fetch fresh data
        metrics = LibraryMetrics()
        
        # GitHub data (most libraries have GitHub repos)
        github_repo = await self._get_github_repo(lib_name, lib_data)
        if github_repo:
            github_data = await self._fetch_github_data(github_repo)
            if github_data:
                metrics.github_stars = github_data.get("stargazers_count", 0)
                metrics.github_forks = github_data.get("forks_count", 0) 
                metrics.github_last_push = github_data.get("pushed_at", "")
        
        # NPM data (for JavaScript libraries)
        if self._is_npm_library(lib_data):
            npm_data = await self._fetch_npm_data(lib_name)
            if npm_data:
                metrics.npm_weekly_downloads = npm_data.get("downloads", 0)
        
        # PyPI data (for Python libraries) 
        if self._is_python_library(lib_data):
            pypi_data = await self._fetch_pypi_data(lib_name)
            if pypi_data:
                metrics.pypi_monthly_downloads = pypi_data.get("downloads", 0)
        
        # Cache the results
        self.cache[cache_key] = (metrics, datetime.now())
        
        return metrics
    
    async def _fetch_github_data(self, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch GitHub repository data"""
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/repos/{repo}",
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"GitHub API error for {repo}: {e}")
        
        return None
    
    async def _fetch_npm_data(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch NPM package data"""
        try:
            async with httpx.AsyncClient() as client:
                # Get package info
                response = await client.get(
                    f"https://api.npmjs.org/downloads/point/last-week/{package_name}",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"NPM API error for {package_name}: {e}")
        
        return None
    
    async def _fetch_pypi_data(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch PyPI package data"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://pypistats.org/api/packages/{package_name}/recent",
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"PyPI API error for {package_name}: {e}")
        
        return None
    
    async def _calculate_popularity(self, lib_name: str, metrics: LibraryMetrics, lib_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate popularity metrics from real-time data"""
        
        # GitHub stars scoring (logarithmic scale)
        stars_score = min(self._stars_to_score(metrics.github_stars), 100)
        
        # Community size classification
        community_size = self._classify_community_size(metrics.github_stars, metrics.github_forks)
        
        # Trending analysis (based on recent activity)
        trending = await self._analyze_trending(metrics)
        
        # Job market estimation (based on popularity + technology type)
        job_market = self._estimate_job_market(metrics, lib_data)
        
        # Learning curve (keep manual for now, but could use documentation analysis)
        learning_curve = lib_data.get("learning_curve", "moderate")
        
        # Maturity assessment (based on GitHub activity + age)
        maturity = self._assess_maturity(metrics)
        
        # Calculate composite score
        overall_score = self._calculate_overall_score(
            stars_score, community_size, trending, job_market, maturity
        )
        
        return {
            "overall_score": overall_score,
            "github_stars": self._format_stars(metrics.github_stars),
            "community_size": community_size,
            "learning_curve": learning_curve,
            "job_market": job_market,
            "maturity": maturity,
            "trending": trending,
            "last_updated": datetime.now().strftime("%Y-%m")
        }
    
    def _stars_to_score(self, stars: int) -> int:
        """Convert GitHub stars to 0-100 score"""
        if stars == 0:
            return 20
        elif stars < 1000:
            return 30
        elif stars < 5000:
            return 50
        elif stars < 20000:
            return 70
        elif stars < 50000:
            return 80
        elif stars < 100000:
            return 90
        else:
            return 95
    
    def _classify_community_size(self, stars: int, forks: int) -> str:
        """Classify community size based on GitHub metrics"""
        total_engagement = stars + (forks * 5)  # Weight forks higher
        
        if total_engagement > 150000:
            return "huge"
        elif total_engagement > 50000:
            return "large"
        elif total_engagement > 10000:
            return "medium"
        elif total_engagement > 1000:
            return "growing"
        else:
            return "small"
    
    async def _analyze_trending(self, metrics: LibraryMetrics) -> str:
        """Analyze trending status (simplified - could fetch historical data)"""
        # For now, use stars as proxy (could fetch historical data from GitHub API)
        stars = metrics.github_stars
        
        if stars > 100000:
            return "explosive"
        elif stars > 50000:
            return "hot" 
        elif stars > 20000:
            return "growing"
        else:
            return "stable"
    
    def _estimate_job_market(self, metrics: LibraryMetrics, lib_data: Dict[str, Any]) -> str:
        """Estimate job market demand"""
        tags = lib_data.get("tags", [])
        category = lib_data.get("category", "")
        stars = metrics.github_stars
        
        # AI/ML libraries are hot
        if any(tag in ["ai", "llm", "ml"] for tag in tags):
            return "explosive" if stars > 50000 else "hot"
        
        # Web frameworks
        if category == "web-framework":
            return "excellent" if stars > 50000 else "growing"
        
        # Cloud/DevOps
        if any(tag in ["cloud", "devops", "containers"] for tag in tags):
            return "excellent" if stars > 30000 else "hot"
        
        # Default based on popularity
        if stars > 100000:
            return "excellent"
        elif stars > 50000:
            return "hot"
        elif stars > 20000:
            return "growing"
        else:
            return "stable"
    
    def _assess_maturity(self, metrics: LibraryMetrics) -> str:
        """Assess library maturity"""
        stars = metrics.github_stars
        
        # Simple heuristic (could check GitHub repo age, release frequency)
        if stars > 100000:
            return "very-stable"
        elif stars > 50000:
            return "stable"
        elif stars > 10000:
            return "stable"
        else:
            return "evolving"
    
    def _calculate_overall_score(self, stars_score: int, community_size: str, 
                                trending: str, job_market: str, maturity: str) -> int:
        """Calculate weighted overall score"""
        
        # Base score from stars
        score = stars_score * 0.4
        
        # Community size bonus
        community_bonus = {
            "huge": 20, "large": 15, "medium": 10, "growing": 5, "small": 0
        }.get(community_size, 0)
        score += community_bonus * 0.2
        
        # Trending bonus
        trending_bonus = {
            "explosive": 20, "hot": 15, "growing": 10, "stable": 5
        }.get(trending, 5)
        score += trending_bonus * 0.1
        
        # Job market bonus
        job_bonus = {
            "explosive": 25, "excellent": 20, "hot": 15, "growing": 10, "stable": 5
        }.get(job_market, 5)
        score += job_bonus * 0.25
        
        # Maturity bonus
        maturity_bonus = {
            "very-stable": 15, "stable": 12, "evolving": 8
        }.get(maturity, 8)
        score += maturity_bonus * 0.15
        
        return min(int(score), 100)
    
    def _format_stars(self, stars: int) -> str:
        """Format stars for display"""
        if stars == 0:
            return "N/A"
        elif stars >= 1000000:
            return f"{stars//1000000}M+"
        elif stars >= 1000:
            return f"{stars//1000}K+"
        else:
            return str(stars)
    
    async def _get_github_repo(self, lib_name: str, lib_data: Dict[str, Any]) -> Optional[str]:
        """Extract GitHub repo from library data or infer it"""
        # Could check documentation URL for GitHub links
        # For now, use common mappings
        github_mappings = {
            "react": "facebook/react",
            "fastapi": "tiangolo/fastapi", 
            "django": "django/django",
            "langchain": "langchain-ai/langchain",
            "flask": "pallets/flask",
            "express": "expressjs/express",
            "docker": "docker/docker-ce",
            "kubernetes": "kubernetes/kubernetes",
            "pandas": "pandas-dev/pandas",
            "streamlit": "streamlit/streamlit"
        }
        
        return github_mappings.get(lib_name)
    
    def _is_npm_library(self, lib_data: Dict[str, Any]) -> bool:
        """Check if library is from NPM"""
        tags = lib_data.get("tags", [])
        return "javascript" in tags or "nodejs" in tags
    
    def _is_python_library(self, lib_data: Dict[str, Any]) -> bool:
        """Check if library is from PyPI"""
        tags = lib_data.get("tags", [])
        return "python" in tags
    
    def _get_default_popularity(self) -> Dict[str, Any]:
        """Default popularity data when API fails"""
        return {
            "overall_score": 70,
            "github_stars": "N/A",
            "community_size": "unknown",
            "learning_curve": "moderate",
            "job_market": "stable", 
            "maturity": "stable",
            "trending": "stable",
            "last_updated": datetime.now().strftime("%Y-%m")
        }

async def enhance_simple_config(config_file: str = "config.json") -> Dict[str, Any]:
    """Enhance simple config with real-time data"""
    
    # Load simple config
    with open(config_file, "r") as f:
        simple_config = json.load(f)
    
    enhancer = DynamicEnhancer()
    enhanced_config = {
        "cache": simple_config.get("cache", {"enabled": True, "ttl_hours": 24}),
        "docs_urls": {},
        "enhancement_timestamp": datetime.now().isoformat(),
        "data_sources": ["github_api", "npm_api", "pypi_api"]
    }
    
    print("🚀 Enhancing configuration with real-time data...")
    start_time = time.time()
    
    # Enhance each library
    tasks = []
    for lib_name, lib_data in simple_config["docs_urls"].items():
        tasks.append(enhancer.enhance_library(lib_name, lib_data))
    
    # Process concurrently for speed
    enhanced_libraries = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, (lib_name, result) in enumerate(zip(simple_config["docs_urls"].keys(), enhanced_libraries)):
        if isinstance(result, Exception):
            print(f"❌ Failed to enhance {lib_name}: {result}")
            enhanced_config["docs_urls"][lib_name] = simple_config["docs_urls"][lib_name]
        else:
            enhanced_config["docs_urls"][lib_name] = result
    
    total_time = time.time() - start_time
    print(f"✅ Enhanced {len(enhanced_config['docs_urls'])} libraries in {total_time:.2f} seconds")
    
    return enhanced_config

if __name__ == "__main__":
    async def main():
        # Test the dynamic enhancer
        enhanced = await enhance_simple_config("config.json")
        
        # Save enhanced config
        with open("dynamic_enhanced_config.json", "w") as f:
            json.dump(enhanced, f, indent=2)
        
        print("📁 Saved to: dynamic_enhanced_config.json")
        
        # Show some results
        print("\n📊 Sample Enhanced Data:")
        for lib_name, lib_data in list(enhanced["docs_urls"].items())[:3]:
            if "popularity" in lib_data:
                pop = lib_data["popularity"]
                print(f"{lib_name}: {pop['github_stars']} stars, {pop['overall_score']}/100 score")
    
    asyncio.run(main()) 