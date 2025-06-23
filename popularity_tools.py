import json
import asyncio
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Enhanced MCP tools for popularity-based recommendations
mcp = FastMCP("docs-with-popularity")

def load_enhanced_config():
    """Load configuration with popularity data"""
    with open("enhanced_config.json", "r") as f:
        return json.load(f)

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
    config = load_enhanced_config()
    docs_urls = config["docs_urls"]
    
    # Map use cases to relevant tags
    use_case_mapping = {
        "web-api": ["api", "web", "backend"],
        "frontend": ["frontend", "ui", "javascript"],
        "ai": ["ai", "llm", "ml"],
        "data-science": ["data-science", "analytics"],
        "mobile": ["mobile", "app"],
        "devops": ["docker", "kubernetes", "deployment"]
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
    
    for lib_name, lib_data in docs_urls.items():
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
                    "score": relevance_score,
                    "popularity": popularity,
                    "category": lib_data.get("category", "unknown"),
                    "tags": lib_tags,
                    "url": lib_data.get("url", ""),
                    "reasoning": f"Score: {relevance_score}/100, Learning: {learning_curve}, Market: {popularity.get('job_market', 'unknown')}"
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
async def compare_libraries(library_names: List[str]):
    """
    Compare multiple libraries across various popularity metrics.
    
    Args:
        library_names: List of library names to compare
        
    Returns:
        Detailed comparison with scores, pros/cons, and recommendations
    """
    config = load_enhanced_config()
    docs_urls = config["docs_urls"]
    
    comparison = {
        "libraries": [],
        "winner": None,
        "summary": {}
    }
    
    for lib_name in library_names:
        if lib_name in docs_urls and isinstance(docs_urls[lib_name], dict):
            lib_data = docs_urls[lib_name]
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

def _get_library_pros(popularity: Dict[str, Any]) -> List[str]:
    """Generate pros based on popularity metrics"""
    pros = []
    
    if popularity.get("learning_curve") == "easy":
        pros.append("Easy to learn")
    if popularity.get("job_market") in ["excellent", "hot"]:
        pros.append("High demand in job market")
    if popularity.get("trending") in ["hot", "explosive"]:
        pros.append("Rapidly growing community")
    if popularity.get("maturity") in ["stable", "very-stable"]:
        pros.append("Mature and reliable")
    if popularity.get("community_size") == "huge":
        pros.append("Large community support")
    
    return pros

def _get_library_cons(popularity: Dict[str, Any]) -> List[str]:
    """Generate cons based on popularity metrics"""
    cons = []
    
    if popularity.get("learning_curve") == "steep":
        cons.append("Steep learning curve")
    if popularity.get("maturity") == "evolving":
        cons.append("Still evolving (breaking changes possible)")
    if popularity.get("community_size") == "small":
        cons.append("Limited community support")
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
    config = load_enhanced_config()
    docs_urls = config["docs_urls"]
    
    trending_libs = []
    
    for lib_name, lib_data in docs_urls.items():
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
    config = load_enhanced_config()
    docs_urls = config["docs_urls"]
    
    if library_name not in docs_urls:
        return {"error": f"Library '{library_name}' not found in configuration"}
    
    lib_data = docs_urls[library_name]
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
            "best_for": _determine_best_use_cases(lib_data),
            "alternatives": _suggest_alternatives(library_name, lib_data, docs_urls)
        }
    }

def _generate_recommendation(popularity: Dict[str, Any]) -> str:
    """Generate a recommendation based on popularity metrics"""
    score = popularity["overall_score"]
    learning = popularity.get("learning_curve", "moderate")
    trending = popularity.get("trending", "stable")
    job_market = popularity.get("job_market", "stable")
    
    if score >= 90 and learning == "easy":
        return "Highly recommended - Popular, easy to learn, great for beginners"
    elif score >= 85 and trending in ["hot", "explosive"]:
        return "Strongly recommended - Growing rapidly, good career investment"
    elif score >= 80 and job_market in ["excellent", "hot"]:
        return "Recommended - Strong job market demand"
    elif learning == "steep" and score < 80:
        return "Consider alternatives - High learning curve for moderate benefits"
    else:
        return "Good choice - Solid option with decent popularity"

def _determine_best_use_cases(lib_data: Dict[str, Any]) -> List[str]:
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
    if "data-science" in tags:
        use_cases.append("Data analysis and science")
    
    return use_cases or ["General purpose development"]

def _suggest_alternatives(lib_name: str, lib_data: Dict[str, Any], all_libs: Dict[str, Any]) -> List[str]:
    """Suggest alternative libraries in the same category"""
    category = lib_data.get("category", "")
    alternatives = []
    
    for name, data in all_libs.items():
        if (name != lib_name and 
            isinstance(data, dict) and 
            data.get("category") == category and
            "popularity" in data):
            alternatives.append(name)
    
    return alternatives[:3]  # Return top 3 alternatives

if __name__ == "__main__":
    mcp.run(transport="stdio") 