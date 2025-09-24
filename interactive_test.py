#!/usr/bin/env python3
"""Interactive test menu for Documentation Search Enhanced MCP Server"""

import asyncio

from src.documentation_search_enhanced.main import (
    compare_library_security,
    get_code_examples,
    get_docs,
    get_learning_path,
    get_security_summary,
    health_check,
    semantic_search,
    suggest_libraries,
)

async def interactive_menu():
    while True:
        print("\n🧪 DOCUMENTATION SEARCH MCP - INTERACTIVE TEST")
        print("=" * 50)
        print("1. Search libraries")
        print("2. Get documentation")
        print("3. Check security")
        print("4. Generate learning path")
        print("5. Semantic search")
        print("6. Compare library security")
        print("7. Find code examples")
        print("8. Health check")
        print("9. Exit")
        
        choice = input("\nSelect option (1-9): ")
        
        try:
            if choice == "1":
                query = input("Enter search term: ")
                results = await suggest_libraries(query)
                print(f"\nFound {len(results)} libraries:")
                for lib in results[:10]:
                    print(f"  • {lib}")
                    
            elif choice == "2":
                library = input("Enter library name: ")
                query = input("Enter search query: ")
                docs = await get_docs(query, library)
                print("\nRetrieved structured documentation summary:")
                print(docs.get("summary_markdown", "(no summary available)"))
                
            elif choice == "3":
                library = input("Enter library name: ")
                result = await get_security_summary(library, "PyPI")
                print(f"\nSecurity Report for {library}:")
                print(f"  Score: {result['security_score']}/100 {result['security_badge']}")
                print(f"  Status: {result['status']}")
                
            elif choice == "4":
                library = input("Enter library/path (e.g., react, devops): ")
                level = input("Enter level (beginner/intermediate/advanced): ")
                path = await get_learning_path(library, level)
                print(f"\nLearning Path: {path['total_topics']} topics")
                for step in path['learning_path'][:5]:
                    print(f"  {step['step']}. {step['topic']}")
                    
            elif choice == "5":
                query = input("Enter search query: ")
                library = input("Enter library: ")
                results = await semantic_search(query, library)
                print(f"\nFound {results['total_results']} results")
                for r in results['results'][:3]:
                    print(f"  • {r['title']} (relevance: {r['relevance_score']:.2f})")
                    
            elif choice == "6":
                libs = input("Enter libraries to compare (comma-separated): ").split(',')
                libs = [lib.strip() for lib in libs]
                result = await compare_library_security(libs)
                print("\nSecurity Comparison:")
                for lib in result['comparison_results']:
                    print(f"  {lib['rank']}. {lib['library']}: {lib['security_score']}/100 {lib['rating']}")
                    
            elif choice == "7":
                library = input("Enter library: ")
                topic = input("Enter topic: ")
                examples = await get_code_examples(library, topic)
                print(f"\nFound {examples['total_examples']} code examples")
                
            elif choice == "8":
                health = await health_check()
                print("\nHealth Check Results:")
                for lib, status in list(health.items())[:5]:
                    if lib != "_cache_stats":
                        print(f"  • {lib}: {status.get('status')}")
                        
            elif choice == "9":
                break
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("🚀 Starting Documentation Search MCP Interactive Test")
    print("Make sure you have set SERPER_API_KEY environment variable")
    asyncio.run(interactive_menu()) 
