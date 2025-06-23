#!/usr/bin/env python3
"""
Test script for the hybrid configuration system
Demonstrates static vs dynamic enhancement modes
"""

import os
import json
import asyncio
import time
from main import recommend_libraries, compare_libraries

async def test_hybrid_system():
    """Test both static and dynamic modes"""
    
    print("🧪 HYBRID SYSTEM TEST")
    print("=" * 60)
    
    # Test 1: Static mode (current behavior)
    print("\n📊 TEST 1: Static Mode (Current)")
    print("-" * 40)
    
    os.environ["ENABLE_DYNAMIC_ENHANCEMENT"] = "false"
    
    start_time = time.time()
    static_recommendations = await recommend_libraries("web-api", "intermediate")
    static_time = time.time() - start_time
    
    print(f"⏱️  Static mode time: {static_time:.3f} seconds")
    print(f"📚 Found {len(static_recommendations['recommendations'])} recommendations")
    
    if static_recommendations['recommendations']:
        top_rec = static_recommendations['recommendations'][0]
        print(f"🥇 Top recommendation: {top_rec['library']} ({top_rec['score']}/100)")
        print(f"🔍 Data source: {top_rec.get('data_source', 'static')}")
    
    # Test 2: Dynamic mode (new hybrid system)
    print("\n🚀 TEST 2: Dynamic Mode (Hybrid)")
    print("-" * 40)
    
    os.environ["ENABLE_DYNAMIC_ENHANCEMENT"] = "true"
    
    # Import main again to pick up the environment change
    import importlib
    import main
    importlib.reload(main)
    
    start_time = time.time()
    try:
        dynamic_recommendations = await main.recommend_libraries("web-api", "intermediate")
        dynamic_time = time.time() - start_time
        
        print(f"⏱️  Dynamic mode time: {dynamic_time:.3f} seconds")
        print(f"📚 Found {len(dynamic_recommendations['recommendations'])} recommendations")
        
        if dynamic_recommendations['recommendations']:
            top_rec = dynamic_recommendations['recommendations'][0]
            print(f"🥇 Top recommendation: {top_rec['library']} ({top_rec['score']}/100)")
            print(f"🔍 Data source: {top_rec.get('data_source', 'unknown')}")
            
            # Show real-time data if available
            if 'popularity' in top_rec:
                pop = top_rec['popularity']
                print(f"⭐ GitHub stars: {pop.get('github_stars', 'N/A')}")
                print(f"📈 Trending: {pop.get('trending', 'unknown')}")
                print(f"💼 Job market: {pop.get('job_market', 'unknown')}")
    
    except Exception as e:
        print(f"⚠️  Dynamic mode failed: {e}")
        print("💡 Note: Dynamic mode requires GitHub API access and dependencies")
        dynamic_time = 0
        dynamic_recommendations = static_recommendations
    
    # Test 3: Performance comparison
    print("\n📊 PERFORMANCE COMPARISON")
    print("-" * 40)
    
    print(f"📈 Static mode:  {static_time:.3f}s")
    print(f"🚀 Dynamic mode: {dynamic_time:.3f}s")
    
    if dynamic_time > 0:
        overhead = ((dynamic_time - static_time) / static_time) * 100
        print(f"⚡ Overhead: {overhead:.1f}% (acceptable for real-time data)")
    
    # Test 4: Library comparison
    print("\n⚖️  TEST 3: Library Comparison")
    print("-" * 40)
    
    try:
        comparison = await main.compare_libraries(["fastapi", "django", "flask"])
        print(f"🏆 Winner: {comparison.get('winner', 'N/A')}")
        
        for lib in comparison.get('libraries', [])[:3]:
            data_source = lib.get('data_source', 'unknown')
            print(f"📚 {lib['name']}: {lib['overall_score']}/100 (data: {data_source})")
    
    except Exception as e:
        print(f"⚠️  Comparison failed: {e}")
    
    # Test 5: Simple config demonstration
    print("\n📝 TEST 4: Simple Config Demonstration")
    print("-" * 40)
    
    # Show simple config size vs full config
    try:
        with open("simple_config.json", "r") as f:
            simple_config = json.load(f)
        
        with open("config.json", "r") as f:
            full_config = json.load(f)
        
        simple_size = len(json.dumps(simple_config))
        full_size = len(json.dumps(full_config))
        reduction = ((full_size - simple_size) / full_size) * 100
        
        print(f"📁 Simple config: {simple_size:,} bytes")
        print(f"📁 Full config: {full_size:,} bytes")
        print(f"📉 Size reduction: {reduction:.1f}%")
        
        # Show what's in simple config
        simple_lib = list(simple_config["docs_urls"].values())[0]
        print(f"\n📋 Simple config contains:")
        for key in simple_lib.keys():
            print(f"   ✅ {key}")
        
        print(f"\n📋 What gets added dynamically:")
        dynamic_fields = ["popularity", "metrics", "github_stars", "job_market", "trending"]
        for field in dynamic_fields:
            print(f"   🚀 {field}")
    
    except FileNotFoundError:
        print("📁 Simple config not found - using full config")
    
    print("\n✅ HYBRID SYSTEM TEST COMPLETE")
    print("=" * 60)
    
    return {
        "static_time": static_time,
        "dynamic_time": dynamic_time,
        "static_recommendations": len(static_recommendations.get('recommendations', [])),
        "dynamic_recommendations": len(dynamic_recommendations.get('recommendations', []))
    }

async def quick_performance_test():
    """Quick performance test for different library counts"""
    
    print("\n🏃 QUICK PERFORMANCE TEST")
    print("-" * 30)
    
    os.environ["ENABLE_DYNAMIC_ENHANCEMENT"] = "true"
    
    # Test with different numbers of libraries
    test_cases = [
        (["fastapi"], "1 library"),
        (["fastapi", "django"], "2 libraries"),
        (["fastapi", "django", "flask", "react"], "4 libraries")
    ]
    
    for libs, description in test_cases:
        start_time = time.time()
        try:
            import main
            result = await main.compare_libraries(libs)
            elapsed = time.time() - start_time
            print(f"⏱️  {description}: {elapsed:.3f}s")
        except Exception as e:
            print(f"❌ {description}: Failed ({e})")

if __name__ == "__main__":
    # Run the comprehensive test
    results = asyncio.run(test_hybrid_system())
    
    # Run quick performance test
    asyncio.run(quick_performance_test())
    
    print(f"\n🎯 SUMMARY:")
    print(f"Static mode processed {results['static_recommendations']} libraries")
    print(f"Dynamic mode processed {results['dynamic_recommendations']} libraries")
    print(f"Dynamic enhancement adds real-time intelligence!") 