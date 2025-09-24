#!/usr/bin/env python3
"""Demo real-world usage of Documentation Search Enhanced MCP Server"""

import asyncio
from src.documentation_search_enhanced.main import (
    compare_library_security, get_learning_path, get_docs,
    get_code_examples, semantic_search, suggest_secure_libraries
)

async def demo_scenarios():
    print("🚀 REAL-WORLD USAGE DEMOS")
    print("=" * 60)
    
    # Scenario 1: Developer choosing a web framework
    print("\n📌 SCENARIO 1: Choosing a Secure Web Framework")
    print("-" * 40)
    
    frameworks = ["django", "flask", "fastapi", "tornado"]
    print("Comparing security of popular Python web frameworks...")
    
    result = await compare_library_security(frameworks, "PyPI")
    print("\nSecurity Rankings:")
    for lib in result['comparison_results']:
        print(f"  {lib['rank']}. {lib['library']}: {lib['security_score']}/100 {lib['rating']}")
    print(f"\n💡 Recommendation: {result['overall_recommendation']}")
    
    # Scenario 2: Learning React from scratch
    print("\n\n📌 SCENARIO 2: Learning React Development")
    print("-" * 40)
    
    path = await get_learning_path("react", "beginner")
    print(f"Generated {path['total_topics']}-step learning path:")
    print(f"Estimated time: {path['estimated_total_time']}")
    print("\nYour learning journey:")
    for step in path['learning_path']:
        print(f"  {step['step']}. {step['topic']} → Use {step['target_library']} docs")
    
    # Scenario 3: Finding authentication solution
    print("\n\n📌 SCENARIO 3: Implementing JWT Authentication in FastAPI")
    print("-" * 40)
    
    # Search for authentication docs
    docs = await get_docs("JWT authentication tutorial", "fastapi")
    print(f"✅ Found comprehensive documentation ({len(docs)} chars)")
    
    # Get specific code examples
    examples = await get_code_examples("fastapi", "JWT authentication", "python")
    print(f"✅ Found {examples['total_examples']} code examples")
    
    # Scenario 4: Setting up monitoring
    print("\n\n📌 SCENARIO 4: Setting Up Production Monitoring")
    print("-" * 40)
    
    print("Finding Prometheus monitoring setup guides...")
    monitoring_docs = await semantic_search(
        "kubernetes cluster monitoring setup",
        "prometheus",
        "production monitoring infrastructure"
    )
    
    if monitoring_docs['results']:
        print(f"✅ Found {monitoring_docs['total_results']} relevant guides:")
        for result in monitoring_docs['results'][:3]:
            print(f"  • {result['title']}")
            print(f"    Relevance: {result['relevance_score']:.1f}%, Read time: {result['estimated_read_time']}")
    
    # Scenario 5: Data science library selection
    print("\n\n📌 SCENARIO 5: Choosing Secure Data Science Libraries")
    print("-" * 40)
    
    suggestions = await suggest_secure_libraries("data", include_security_score=True)
    print("Secure data science library recommendations:")
    for lib in suggestions['suggestions'][:5]:
        if lib.get('security_score'):
            print(f"  • {lib['library']} {lib['security_badge']} Score: {lib['security_score']}/100")
    
    # Summary
    print("\n\n💡 KEY BENEFITS DEMONSTRATED:")
    print("-" * 40)
    print("✅ Security-first library selection")
    print("✅ Structured learning paths with multi-library integration")
    print("✅ Quick access to relevant documentation")
    print("✅ Production-ready monitoring and DevOps tools")
    print("✅ Smart search with relevance scoring")

async def main():
    print("🎯 Documentation Search Enhanced MCP - Real-World Demos")
    print("This demo shows how developers actually use this tool\n")
    
    await demo_scenarios()
    
    print("\n\n📚 AVAILABLE FOR 104 LIBRARIES!")
    print("Including: React, Vue, FastAPI, Django, Flask, MongoDB, PostgreSQL,")
    print("Docker, Kubernetes, Prometheus, Grafana, Elasticsearch, and many more!")
    
    print("\n🚀 Ready to use with Claude Desktop, Cursor, or any MCP client!")

if __name__ == "__main__":
    asyncio.run(main()) 