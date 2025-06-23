#!/usr/bin/env python3
"""
Configuration Sync Script
Automatically updates enhanced_config.json with all data from config.json
"""

import json
from pathlib import Path

def sync_enhanced_config():
    """Sync enhanced_config.json with main config.json"""
    
    # Load main config
    with open("config.json", "r") as f:
        main_config = json.load(f)
    
    # Create enhanced config structure
    enhanced_config = {
        "cache": main_config.get("cache", {
            "enabled": True,
            "ttl_hours": 24,
            "max_entries": 1000
        }),
        "docs_urls": {},
        "popularity_weights": main_config.get("popularity_weights", {
            "github_stars": 0.3,
            "community_size": 0.2,
            "job_market": 0.25,
            "maturity": 0.15,
            "trending": 0.1
        }),
        "categories": main_config.get("categories", {})
    }
    
    # Process each library from main config
    for lib_name, lib_data in main_config["docs_urls"].items():
        if isinstance(lib_data, dict):
            # Enhanced format - copy as is
            enhanced_config["docs_urls"][lib_name] = lib_data.copy()
            
            # Ensure all required fields exist
            if "popularity" in lib_data:
                popularity = lib_data["popularity"]
                
                # Add missing fields with defaults
                if "community_size" not in popularity:
                    # Estimate community size from GitHub stars
                    stars = popularity.get("github_stars", "0")
                    if "220000" in stars or "100000" in stars:
                        popularity["community_size"] = "huge"
                    elif "70000" in stars or "75000" in stars or "85000" in stars:
                        popularity["community_size"] = "large"
                    elif "41000" in stars or "31000" in stars:
                        popularity["community_size"] = "medium"  
                    else:
                        popularity["community_size"] = "growing"
                
                if "last_updated" not in popularity:
                    popularity["last_updated"] = "2024-12"
        else:
            # Simple URL format - convert to enhanced format
            enhanced_config["docs_urls"][lib_name] = {
                "url": lib_data,
                "category": "unknown",
                "popularity": {
                    "overall_score": 70,
                    "github_stars": "N/A",
                    "community_size": "unknown",
                    "learning_curve": "moderate",
                    "job_market": "stable",
                    "maturity": "stable",
                    "last_updated": "2024-12",
                    "trending": "stable"
                },
                "tags": ["general"]
            }
    
    # Write enhanced config
    with open("enhanced_config.json", "w") as f:
        json.dump(enhanced_config, f, indent=4)
    
    print("✅ Enhanced config synced successfully!")
    print(f"📊 Synced {len(enhanced_config['docs_urls'])} libraries")
    
    # Show differences
    original_count = 6  # Current enhanced_config.json library count
    new_count = len(enhanced_config['docs_urls'])
    print(f"📈 Added {new_count - original_count} new libraries")
    
    return enhanced_config

def verify_sync():
    """Verify that both configs are in sync"""
    with open("config.json", "r") as f:
        main_config = json.load(f)
    
    with open("enhanced_config.json", "r") as f:
        enhanced_config = json.load(f)
    
    main_libs = set(main_config["docs_urls"].keys())
    enhanced_libs = set(enhanced_config["docs_urls"].keys())
    
    missing_in_enhanced = main_libs - enhanced_libs
    extra_in_enhanced = enhanced_libs - main_libs
    
    print("\n🔍 Configuration Verification:")
    print(f"Main config libraries: {len(main_libs)}")
    print(f"Enhanced config libraries: {len(enhanced_libs)}")
    
    if missing_in_enhanced:
        print(f"❌ Missing in enhanced: {missing_in_enhanced}")
    
    if extra_in_enhanced:
        print(f"⚠️  Extra in enhanced: {extra_in_enhanced}")
    
    if not missing_in_enhanced and not extra_in_enhanced:
        print("✅ Configurations are fully synchronized!")
        return True
    
    return False

if __name__ == "__main__":
    print("🔄 Syncing enhanced_config.json with main config.json...")
    sync_enhanced_config()
    verify_sync() 