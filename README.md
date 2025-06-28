# 🚀 Enhanced Documentation Search MCP Server

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![PyPI version](https://badge.fury.io/py/documentation-search-enhanced.svg)](https://badge.fury.io/py/documentation-search-enhanced)

> An enhanced MCP server for documentation search, security analysis, and developer productivity.
> Deploys instantly with `uvx`, just like official AWS MCP servers.

| Key Features | Description | Example Query |
| :--- | :--- | :--- |
| 📚 **Multi-Lib Search** | Search across 104+ docs simultaneously | `"Compare state management in react vs vue"` |
| 🛡️ **Project Security** | Scan all dependencies for vulnerabilities | `"Are there any security issues in my project?"` |
| 🏗️ **Project Generation**| Create boilerplate for new projects | `"Create a new fastapi project"` |
| 🐳 **Docker Environments**| Set up local services like Postgres/Redis | `"Set up a postgres database for me"` |
| 🎓 **Learning Paths** | Get a structured learning plan | `"Give me a learning path for devops"` |
| ⚖️ **Security Comparison**| Compare security scores of libraries | `"Compare flask vs django"` |

## 🚀 MCP Value Proposition: From Minutes to Seconds

To understand the impact of this MCP server, let's compare a common, critical developer task with and without the tool.

**Scenario: "Are there any vulnerabilities in my project's dependencies?"**

| Without MCP (The Manual Grind) | With MCP (The Instant Audit) |
| :--- | :--- |
| 1. Open your `pyproject.toml` or `requirements.txt`. | 1. Ask your AI assistant: |
| 2. For **each** of your 25 dependencies: | <br> `Are there any vulnerabilities in my project?` |
| &nbsp;&nbsp;&nbsp; a. Google `"[library-name] vulnerability"`. | |
| &nbsp;&nbsp;&nbsp; b. Open its PyPI page, look for warnings. | |
| &nbsp;&nbsp;&nbsp; c. Open its GitHub page, find the "Security" tab. | |
| &nbsp;&nbsp;&nbsp; d. Manually check if CVEs apply to your version. | |
| 3. Try to mentally aggregate the risk level. | |
| --- | --- |
| **_Time Required: 15-30 minutes_** | **_Time Required: ~5 seconds_** |
| **_Output: A vague sense of security._** | **_Output: A precise, actionable JSON report._** |
| | <br> ```json { "summary": { "vulnerable_count": 2, "overall_project_risk": "High" }, "vulnerable_packages": [ { "library": "requests", "security_score": 35 } ] } ``` |

This is the core value: **automating tedious, complex, and critical developer workflows** to deliver instant, accurate, and actionable insights.

## 🚀 Quick Start

### 1. Install & Run
```bash
# No git clone required! Needs Python 3.12+
uvx documentation-search-enhanced@latest
```

### 2. Configure with your AI Assistant
Add to your Claude Desktop or Cursor configuration:

```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_serper_api_key_here"
      }
    }
  }
}
```

## 🛠️ Available Tools

This server provides a powerful suite of tools to enhance your development workflow:

| Tool | Description |
| :--- | :--- |
| `get_docs` | Fetches and summarizes documentation for one or more libraries. |
| `semantic_search`| Performs AI-powered semantic search across multiple libraries, ranking results by relevance. |
| `get_learning_path`| Generates a structured learning curriculum for a technology or skill level. |
| `get_code_examples`| Finds curated code examples for a specific topic. |
| `scan_project_dependencies`| **(New!)** Scans your project's dependencies (`pyproject.toml`, etc.) for known security vulnerabilities. |
| `generate_project_starter`| **(New!)** Creates boilerplate for new FastAPI or React projects. |
| `manage_dev_environment`| **(New!)** Generates a `docker-compose.yml` for services like Postgres or Redis. |
| `get_security_summary`| Provides a quick security score and summary for a single library. |
| `compare_library_security`| Compares the security posture of multiple libraries side-by-side. |
| `suggest_libraries`| Autocompletes library names. |
| `get_current_config`| **(New!)** Returns the active configuration, which you can save and modify for local overrides. |
| `health_check`| Checks the status of documentation sources. |

## ⚙️ Customization

You can customize the server by creating a `config.json` file in your project directory.

1.  **Get the default config:** Ask your AI assistant, `"get the current configuration"`.
2.  **Save as `config.json`:** Save the output to a `config.json` file in your project's root.
3.  **Modify:** Add your own private documentation URLs or change settings.

The server will automatically use your local `config.json` if it exists.

## 🏠 Local Development

If you want to contribute or customize the server's code:
```bash
git clone https://github.com/antonmishel/documentation-search-mcp.git
cd documentation-search-mcp
uv sync
echo "SERPER_API_KEY=your_key_here" > .env
uv run python src/documentation_search_enhanced/main.py
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

This project is open source under the MIT License. See [LICENSE](LICENSE) for details.

## 🎯 Quick Reference

| Command | What It Does | Example |
|---------|--------------|---------|
| `uvx documentation-search-enhanced@latest` | Install/run MCP server | One-time setup |
| Get docs for library | Search documentation | "*Find FastAPI authentication examples*" |
| Get library suggestions | Auto-complete libraries | "*What libraries start with 'lang'?*" |
| Check system health | Monitor performance | "*Check if documentation sources are working*" |
| Compare technologies | Side-by-side analysis | "*Compare FastAPI vs Django for APIs*" |

### 🔑 Supported Libraries (45+)

**🔥 AI & ML**: langchain, openai, anthropic, transformers, scikit-learn, spacy  
**🌐 Web Frameworks**: fastapi, django, flask, express  
**⚛️ Frontend**: react, svelte, javascript, typescript  
**☁️ Cloud**: aws, google-cloud, azure, boto3  
**🐍 Python**: pandas, numpy, matplotlib, requests, streamlit  
**🛠️ DevOps**: docker, kubernetes  
**💾 Data**: duckdb, jupyter, papermill  

### ✨ Benefits of AWS-Style Deployment

✅ **Zero Local Setup** - No cloning, no path management  
✅ **Automatic Updates** - Always get the latest version with `@latest`  
✅ **Isolated Environment** - `uvx` handles dependencies automatically  
✅ **Universal Compatibility** - Works with any MCP-compatible AI assistant  
✅ **No Maintenance** - No local virtual environments to manage  

### 🔄 Update to Latest Version

```bash
# The @latest tag automatically gets the newest version
# Just restart your AI assistant to get updates
```

---

## 🎯 **Complete Enhancement Recommendations** (Based on AWS MCP Analysis)

Based on my analysis of the [AWS MCP repository](https://github.com/awslabs/mcp), here are **priority enhancements** that would make your documentation-search-enhanced MCP server enterprise-grade:

### ✅ **Already Implemented**
1. **Enhanced Configuration Management** - Added AWS-style config with `auto_approve`, `priority`, `features`
2. **Structured Logging** - Created AWS-style logging with `FASTMCP_LOG_LEVEL` support
3. **Samples Directory** - Added comprehensive usage examples and configurations
4. **Project-Aware Security Scan** - Scans `pyproject.toml`, etc. for vulnerabilities.
5. **Project Boilerplate Generation** - Creates starter projects from templates.
6. **Local Dev Environment Management** - Generates `docker-compose.yml` for services.
7. **Configuration Validation** - Ensures `config.json` is valid on startup, providing clear errors.

### 🚀 **High Priority Enhancements** 

#### 8. **Rate Limiting & Resource Management**
```python
# Add to main.py
from asyncio import Semaphore
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, identifier: str = "default"):
        now = datetime.now()
        # Implementation...
```

#### 9. **Auto-Approve Tool Integration**
```python
# Modify tools to respect auto-approve settings
@mcp.tool()
async def get_docs(query: str, library: str):
    """Enhanced with auto-approve support"""
    config = load_config()
    auto_approve = config["server_config"]["auto_approve"].get("get_docs", False)
    
    if not auto_approve:
        # Request user approval for external fetch
        pass
```

#### 10. **Enhanced Analytics & Metrics**
```python
# Add usage analytics like AWS MCP servers
class AnalyticsTracker:
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "libraries_searched": defaultdict(int),
            "response_times": [],
            "error_count": 0
        }
```

#### 11. **Plugin Architecture** 
```python
# Enable community extensions
class PluginManager:
    def __init__(self):
        self.plugins = []
    
    def register_plugin(self, plugin):
        self.plugins.append(plugin)
    
    async def execute_plugins(self, event_type: str, data: dict):
        for plugin in self.plugins:
            await plugin.handle(event_type, data)
```

### 🎯 **Medium Priority Enhancements**

#### 12. **Persistent Caching**
```python
# Add SQLite-based persistent cache
import sqlite3
import pickle

class PersistentCache(SimpleCache):
    def __init__(self, db_path: str = "cache.db"):
        super().__init__()
        self.db_path = db_path
        self._init_db()
```

#### 13. **Health Check Enhancements**
```python
# Add comprehensive health monitoring
@mcp.tool()
async def detailed_health_check():
    """Enhanced health check with more metrics"""
    return {
        "status": "healthy",
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "cache_hit_rate": cache.get_hit_rate(),
        "active_connections": len(active_connections),
        "rate_limit_status": rate_limiter.get_status()
    }
```

### 📊 **Advanced Features (AWS MCP Inspired)**

#### 14. **Multiple Sub-Servers** (Like AWS MCP Collection)
```bash
# Modular architecture
uvx documentation-search-enhanced.core@latest      # Core search
uvx documentation-search-enhanced.ai@latest        # AI-specific docs  
uvx documentation-search-enhanced.web@latest       # Web framework docs
uvx documentation-search-enhanced.cloud@latest     # Cloud platform docs
```

#### 15. **Environment-Specific Configurations**
```json
{
  "environments": {
    "development": {
      "logging_level": "DEBUG",
      "cache_ttl_hours": 1,
      "rate_limit_enabled": false
    },
    "production": {
      "logging_level": "ERROR", 
      "cache_ttl_hours": 24,
      "rate_limit_enabled": true
    }
  }
}
```

#### 16. **Advanced Search Features**
```python
@mcp.tool()
async def semantic_search(query: str, libraries: list[str], context: str = None):
    """AI-powered semantic search across multiple libraries"""

@mcp.tool() 
async def code_examples_search(query: str, language: str = "python"):
    """Search specifically for code examples"""

@mcp.tool()
async def trending_topics(category: str = "ai"):
    """Get trending topics in a category"""
```

## 🎉 **Implementation Priority**

### **Phase 1 (Done)**
1. ✅ Enhanced Configuration
2. ✅ Structured Logging
3. ✅ Samples Directory
4. ✅ Project-Aware Security Scan
5. ✅ Project Boilerplate Generation

### **Phase 2 (Done)**
6. ✅ Multi-Library Search

### **Phase 3 (Done)**
7. ✅ Local Dev Environment Management

### **Phase 4 (Current)**
8. ✅ Configuration Validation
9. 🔄 Rate Limiting Implementation
10. 🔄 Auto-Approve Tool Integration
11. Analytics & Metrics Tracking

## 🚀 **Expected Benefits**

After implementing these AWS MCP-inspired enhancements:

- **🏢 Enterprise-Ready**: Production-grade reliability and monitoring
- **🔒 Security**: Rate limiting, auto-approve controls, audit trails
- **📈 Scalability**: Plugin architecture, modular design, resource management
- **🛠️ Developer Experience**: Better logging, samples, configuration validation
- **📊 Observability**: Comprehensive metrics, health checks, performance tracking

Your MCP server would then match or exceed the capabilities of AWS MCP servers while maintaining the same professional deployment model! 🎯

Would you like me to implement any specific enhancement from this list?

## 🎯 Ready to Transform Your Development Workflow?

### ⭐ **Star this repository** if you find it valuable!

### 🚀 **Get Started Now**
1. **Install:** `uvx documentation-search-enhanced@latest`
2. **API Key:** Get free key from [serper.dev](https://serper.dev)
3. **Configure:** Add to your AI assistant (see Quick Start above)
4. **Experience:** Ask Claude "*What's the best framework for my project?*"

### 🤝 **Join the Community**
- **💬 Questions?** Open an [issue](https://github.com/anton-prosterity/documentation-search-mcp/issues)
- **🐛 Bug Reports:** We fix them fast!
- **✨ Feature Requests:** Your ideas make this better
- **🔀 Pull Requests:** Contributions welcome!

---

## 📜 License

This project is open source under the MIT License. See [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ by developers, for developers**

*Transform Claude into your personal development advisor today!*

⭐ **Don't forget to star this repo if it helped you!** ⭐

</div>

@mcp.tool()
async def semantic_search(query: str, libraries: list[str], context: str = None):
    """AI-powered semantic search across multiple libraries"""

@mcp.tool() 
async def code_examples_search(query: str, language: str = "python"):
    """Search specifically for code examples"""

@mcp.tool()
async def trending_topics(category: str = "ai"):
    """Get trending topics in a category"""

#### Multi-Library Search
Get a broader perspective by searching across multiple libraries at once.

**🤖 You**: `How do I handle state management in React vs Vue?`
(This will search both libraries and return a combined, ranked result)

**Claude**:
```json
{
  "query": "state management",
  "libraries_searched": ["react", "vue"],
  "total_results": 20,
  "results": [
    {
      "source_library": "react",
      "title": "React Docs: State and Lifecycle",
      "relevance_score": 95.5,
      "snippet": "Learn how to use state and lifecycle methods in React components..."
    },
    {
      "source_library": "vue",
      "title": "Vue Docs: State Management with Pinia",
      "relevance_score": 92.1,
      "snippet": "Pinia is the now the official state management library for Vue..."
    },
    {
      "source_library": "react",
      "title": "Redux Toolkit Tutorial",
      "relevance_score": 88.7,
      "snippet": "The official, opinionated, batteries-included toolset for efficient Redux development..."
    }
  ]
}
```

### 🚀 New in Version 1.2: Project-Aware Tools

#### Project Security Audit

## Configuration

Your MCP server comes pre-configured with 104 popular libraries, but you can easily customize it.

### How to Customize Your Configuration

1.  **Get the Default Configuration:**
    Ask your AI assistant: `"Show me the current configuration"`
    This will output the entire `config.json` content.

2.  **Create a Local `config.json`:**
    -   Save the output from the previous step into a file named `config.json` in your project's root directory.

3.  **Modify Your Local Config:**
    -   Add your own private documentation URLs, internal libraries, or tweak any settings.

The MCP server will **automatically detect and use your local `config.json`** instead of the default one.

### Adding New Documentation Sources

To add a new library, simply edit your local `config.json` and add a new entry to the `docs_urls` and `categories` sections: