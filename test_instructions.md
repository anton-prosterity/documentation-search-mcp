# 🧪 Testing Documentation Search Enhanced MCP Server

## Quick Start

Run the quick test script:
```bash
uv run python quick_test.py
```

## Method 1: Direct Testing with uvx (AWS MCP Style)

### Local Testing
```bash
# Run from your local directory
uvx --from . documentation-search-enhanced

# Or using uv run
uv run documentation-search-enhanced
```

### Testing from PyPI (once published)
```bash
# Install and run directly (no git clone needed!)
uvx documentation-search-enhanced@latest
```

## Method 2: Testing with Claude Desktop

### 1. Update Claude Desktop Configuration

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "documentation-search": {
      "command": "uvx",
      "args": ["--from", "/Users/antonmishel/workspace/documentation-search-mcp", "documentation-search-enhanced"],
      "env": {
        "SERPER_API_KEY": "your-serper-api-key-here",
        "ENVIRONMENT": "development"
      }
    }
  }
}
```

### 2. Restart Claude Desktop and test with prompts:
- "Search FastAPI documentation for authentication tutorials"
- "Compare security of django vs flask vs fastapi"
- "Create a beginner learning path for React development"
- "Find code examples for MongoDB aggregation pipelines"
- "Show me Prometheus monitoring setup documentation"
- "What's the security score for the requests library?"

## Method 3: Interactive Python Testing

Save this as `interactive_test.py`:

```python
import asyncio
from src.documentation_search_enhanced.main import *

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
                print(f"\nRetrieved {len(docs)} characters")
                print(f"Preview: {docs[:500]}...")
                
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
    asyncio.run(interactive_menu())
```

## Method 4: Testing with Cursor

Add to your `.cursorrules` or Cursor settings:

```json
{
  "mcpServers": {
    "documentation-search": {
      "command": "uvx",
      "args": ["--from", ".", "documentation-search-enhanced"],
      "cwd": "/Users/antonmishel/workspace/documentation-search-mcp",
      "env": {
        "SERPER_API_KEY": "your-key-here",
        "ENVIRONMENT": "development"
      }
    }
  }
}
```

## Available Test Commands

### 1. Library Discovery
```python
# Find libraries
await suggest_libraries("react")

# With security scores
await suggest_secure_libraries("data", include_security_score=True)
```

### 2. Documentation Search
```python
# Basic search
await get_docs("hooks tutorial", "react")

# Semantic search with context
await semantic_search("authentication", "fastapi", "building secure API")

# Filtered search
await filtered_search("tutorial", "react", content_type="tutorial", difficulty_level="beginner")
```

### 3. Security Features
```python
# Quick security check
await get_security_summary("django", "PyPI")

# Compare multiple libraries
await compare_library_security(["flask", "django", "fastapi"])

# Full vulnerability scan
await scan_library_vulnerabilities("requests")
```

### 4. Learning & Examples
```python
# Generate learning path
await get_learning_path("react", "beginner")

# Get code examples
await get_code_examples("fastapi", "authentication", "python")
```

### 5. System Status
```python
# Check health
await health_check()

# Cache stats
await get_cache_stats()

# Environment config
await get_environment_config()
```

## Testing Production Tools

Test the newly added production tools:

```python
# Prometheus monitoring
await get_docs("kubernetes monitoring", "prometheus")

# Grafana dashboards
await get_docs("create dashboard", "grafana")

# Elasticsearch queries
await get_docs("query DSL", "elasticsearch")

# Celery tasks
await get_docs("distributed tasks", "celery")

# ESLint configuration
await get_docs("rules plugins", "eslint")
```

## Troubleshooting

### SERPER_API_KEY not set
If you see warnings about SERPER_API_KEY, set it:
```bash
export SERPER_API_KEY="your-key-here"
```

### Import errors
Make sure you're in the project directory:
```bash
cd /Users/antonmishel/workspace/documentation-search-mcp
uv sync
```

### Version conflicts
The current version is 1.1.0. To test the latest local changes:
```bash
uv run --from . documentation-search-enhanced
```

## Performance Testing

Test caching performance:
```python
import time

# First call (no cache)
start = time.time()
await get_docs("tutorial", "react")
print(f"First call: {time.time() - start:.2f}s")

# Second call (cached)
start = time.time()
await get_docs("tutorial", "react")
print(f"Cached call: {time.time() - start:.2f}s")
```

## 🎯 Ready to Deploy

Once testing is complete, you can:
1. Publish to PyPI: `./publish_to_pypi.sh`
2. Users can install with: `uvx documentation-search-enhanced@latest`
3. No git clone or local setup required! 