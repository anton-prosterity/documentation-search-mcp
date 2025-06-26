# 🚀 Enhanced Documentation Search MCP Server

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![AWS-Style](https://img.shields.io/badge/AWS--Style-Deployment-orange.svg)](https://github.com/awslabs/mcp)

> **Transform Claude into your personal development advisor** 🤖✨
> 
> An intelligent MCP server that gives Claude real-time access to documentation, library popularity data, and career insights. Make smarter technology choices with data-driven recommendations tailored to your experience level.

> 🔥 **NEW: AWS-Style Deployment** - No local setup required! Run directly with `uvx documentation-search-enhanced@latest` just like AWS MCP servers.

---

## 🎯 What This Does

**Transforms your AI assistant into a documentation expert!**

Instead of Claude saying *"I don't have access to current documentation"*, it now:

1. **🔍 Searches live documentation** from 45+ popular libraries
2. **📚 Returns current, accurate code examples** 
3. **🎯 Provides contextual recommendations** based on your needs
4. **⚡ Caches results** for lightning-fast follow-up questions

## 🚀 AWS-Style Deployment Ready

This MCP server follows the **exact same deployment pattern** as AWS MCP servers:

```bash
# Just like AWS MCP servers - zero setup required!
uvx documentation-search-enhanced@latest
```

Same professional experience:
- ✅ No local cloning or setup
- ✅ Automatic dependency management  
- ✅ Always up-to-date with `@latest`
- ✅ Works with any MCP-compatible AI assistant

---

## ⭐ Why This MCP Server is Different

🎯 **Intelligent Recommendations** - Not just search, but smart suggestions based on your skill level and project needs  
📊 **Data-Driven Insights** - Real popularity scores, job market trends, and learning time estimates  
🚀 **Career-Focused** - Salary insights, trending technologies, and market positioning  
⚡ **Lightning Fast** - Smart caching delivers responses in 2-5 seconds  
🔧 **AWS-Style Deployment** - Same professional deployment model as AWS MCP servers - just run `uvx documentation-search-enhanced@latest`  
🛠️ **Universal Compatibility** - Works with Cursor, Claude Desktop, Windsurf, and any MCP-compatible tool  

### 🎬 See the Transformation

**🤖 Question:** *"What's the best agentic framework?"*

**❌ Generic AI Response:**
```
"Popular agentic frameworks include LangChain, AutoGPT, and CrewAI."
```

**✅ Enhanced MCP Server Response:**
```
🎯 LANGCHAIN - Leading Agentic Framework (Score: 92/100)

📊 Real-Time Market Analysis:
• GitHub Stars: 95,247+ ← Live data from GitHub API
• Job Market: EXPLOSIVE (500% increase in Q4 2024)  
• Salary Impact: $50k-$120k+ increase potential
• Companies: Google, Microsoft, OpenAI, Anthropic actively hiring

💡 Career Intelligence:
"LangChain skills can increase salary by $50k-$120k+. 
500% growth in job postings makes it THE #1 AI skill for 2024.
Best time to learn: NOW - market demand far exceeds supply."
```

## 🚀 Quick Start (30 seconds)

> **No local setup required!** Run directly with `uvx` just like AWS MCP servers.

```bash
# 1. Install and run directly (no cloning needed)
uvx documentation-search-enhanced@latest

# 2. Get your free API key from serper.dev
export SERPER_API_KEY="your_key_here"
```

### 🔧 Add to Your AI Assistant

#### For Cursor

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_key_here"
      }
    }
  }
}
```

#### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_key_here"
      }
    }
  }
}
```

#### For Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_key_here"
      }
    }
  }
}
```

**That's it!** 🎉 Claude now has intelligent development superpowers.

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

## 🏠 Local Development (Optional)

If you want to contribute or customize:

```bash
# 1. Clone and setup
git clone https://github.com/antonmishel/documentation-search-mcp.git
cd documentation-search-mcp
uv sync

# 2. Get your free API key from serper.dev
echo "SERPER_API_KEY=your_key_here" > .env

# 3. Test the MCP server
python src/documentation_search_enhanced/main.py
# Press Ctrl+C when you see it waiting for input ✅

# 4. Add to Cursor (.cursor/mcp.json):
```

For local development:
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/path/to/.local/bin/uv", 
      "args": [
        "--directory",
        "/path/to/documentation-search-mcp",
        "run", 
        "src/documentation_search_enhanced/main.py"
      ],
      "env": {
        "SERPER_API_KEY": "your_key_here"
      }
    }
  }
}
```

## 🛠️ 7 Specialized AI Tools

Transform Claude from a generic assistant into a **data-driven development expert**:

| Tool | What It Does | Example Output |
|------|-------------|----------------|
| 🔍 **`get_docs`** | Smart documentation search | *Returns targeted FastAPI auth docs in 3 seconds* |
| 🎯 **`recommend_libraries`** | Personalized suggestions with real-time career impact | *"FastAPI (91/100): $45k salary boost, 83k+ GitHub stars"* |
| ⚖️ **`compare_libraries`** | Multi-dimensional analysis with live data | *"Winner: Django (91.2/100) vs FastAPI vs Flask (real-time)"* |
| 📈 **`get_trending_libraries`** | Live trend analysis with growth metrics | *"AutoGen: Explosive growth, 500% job increase in Q4"* |
| 💡 **`get_library_insights`** | Real-time market analysis with ROI data | *"React: 236k+ stars, $35k-$85k salary increase, 2-month ROI"* |
| 🔤 **`suggest_libraries`** | Smart autocomplete with live popularity | *"lang" → LangChain (95k+ stars, explosive growth)"* |
| ⚡ **`health_check`** | Performance tracking of 20+ sources | *"20/20 sources healthy, avg 180ms response"* |

## 📚 20+ Supported Technologies

**🔥 Hot & Trending:** FastAPI, LangChain, PromptFlow, AutoGen, OpenAI, Anthropic  
**⚡ Frontend:** React, JavaScript, TypeScript  
**🛠️ Backend:** Django, Flask, Express, Node.js, Python  
**☁️ Cloud Platforms:** AWS, Google Cloud, Azure  
**🤖 AI Frameworks:** LangChain, PromptFlow, AutoGen  
**🤖 AI Services:** OpenAI, Anthropic  
**🛠️ DevOps:** Docker, Kubernetes  
**📊 Data Science:** Pandas, Streamlit  

*All with real-time GitHub data, job market trends, and career insights!*

## 🌟 Core Intelligence Features

### 🧠 **Real-Time Intelligence (Default)**
- **Live GitHub Data** - Real-time stars, forks, activity, community metrics
- **Career Intelligence** - Current salary data, job market trends, hiring insights  
- **Experience Matching** - Beginner/Intermediate/Advanced optimization
- **Trend Analysis** - Live growth velocity and market timing advice

### 🎯 **Personalized Recommendations**
- **Experience-Level Adaptation** - Tailored advice for your skill level
- **Use Case Optimization** - Web-API, Frontend, AI, Data-Science specific
- **Context-Aware Suggestions** - Considers project type, timeline, team size
- **Future-Proof Guidance** - Trend analysis for long-term skill investment

### ⚖️ **Objective Comparisons**
- **Winner Declarations** - Data-driven "best choice" recommendations
- **Pros/Cons Analysis** - Detailed advantage/disadvantage breakdowns
- **Market Position Mapping** - Leader/Strong/Moderate/Niche classifications

## Prerequisites

- **Serper API Key**: Get your free key from [serper.dev](https://serper.dev)
- **UV Package Manager**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

That's it! No Python installation, no virtual environments, no dependency management needed.

## Configuration

### Adding New Documentation Sources

Adding new libraries is incredibly simple! Just edit `src/documentation_search_enhanced/config.json`:

```json
{
    "docs_urls": {
        "your_library": {
            "url": "https://docs.example.com/",
            "category": "web-framework",
            "learning_curve": "easy",
            "tags": ["python", "web", "api"]
        }
    },
    "categories": {
        "web-framework": ["fastapi", "django", "flask", "your_library"]
    }
}
```

**That's it!** The system automatically:
- ✅ Makes the library searchable immediately
- ✅ Includes it in suggestions and recommendations
- ✅ Provides intelligent categorization
- ✅ Delivers contextual help

For step-by-step contribution guide, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Usage

### Running the Server

```bash
# AWS-style deployment (recommended)
uvx documentation-search-enhanced@latest

# Local development (if you've cloned the repo)
python src/documentation_search_enhanced/main.py
```

### Integration with AI Tools

The server integrates seamlessly with any MCP-compatible AI assistant. Simply add the configuration above to your AI tool's MCP settings and restart.

#### Configuration Files

- **Cursor**: `.cursor/mcp.json` (project-specific) or `~/.cursor/mcp.json` (global)
- **Claude Desktop**: 
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`

#### Security Best Practices

⚠️ **Important**: Keep your API keys secure and never commit them to version control. The MCP configuration files should be private and not shared publicly.

### Available Tools

#### 1. `get_docs` - Documentation Search
Search for specific information within library documentation.

**Example:**
```
🤖 You: "Using the documentation-search-enhanced MCP server, find FastAPI authentication examples"

Claude: I'll search the FastAPI documentation for authentication examples.

📚 FastAPI Authentication Examples:

From FastAPI's security documentation:

**OAuth2 with Password Bearer**
```python
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authenticate user and return token
    return {"access_token": access_token, "token_type": "bearer"}
```

**JWT Authentication**
```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```
```

#### 2. `suggest_libraries` - Smart Auto-complete
Get library suggestions based on partial names.

**Example:**
```
🤖 You: "What libraries start with 'lang'?"

Claude: Here are libraries matching "lang":

• **langchain** - AI framework for building applications with LLMs
• **language-tool** - Grammar and spell checking
• **langdetect** - Language detection library

Would you like more details about any of these?
```

#### 3. `health_check` - System Status
Monitor the health of documentation sources.

**Example:**
```
🤖 You: "Check if the documentation sources are working"

Claude: 📊 Documentation Health Status:

✅ **fastapi**: Healthy (142ms response)
✅ **langchain**: Healthy (203ms response) 
✅ **react**: Healthy (186ms response)
✅ **django**: Healthy (167ms response)
✅ **openai**: Healthy (124ms response)

📈 **Cache Stats**: 47 active entries, 12% utilization
🚀 **Overall Status**: All systems operational
```

#### 4. Real-World Usage Scenarios

**Scenario 1: Learning New Technology**
```
🤖 You: "I'm new to web development. What's the easiest Python web framework to start with?"

Claude: Based on the documentation and current trends:

🎯 **Flask** - Perfect for Beginners (Score: 88/100)
• **Learning Curve**: Easy (2-3 weeks to proficiency)
• **Documentation Quality**: Excellent, beginner-friendly
• **Community**: Large, helpful community
• **Job Market**: Strong demand, good entry-level opportunities

📚 **Getting Started with Flask**:
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
```

**Next Steps**: Try the Flask tutorial, build a simple blog, then explore Flask-SQLAlchemy for databases.
```

**Scenario 2: Technology Comparison**
```
🤖 You: "Compare FastAPI vs Django for building APIs"

Claude: 🔍 **FastAPI vs Django** - Comprehensive Analysis

**FastAPI** (Winner for APIs - 94/100)
✅ **Pros**:
- Automatic API documentation (Swagger/OpenAPI)
- Built-in async support
- Type hints integration
- 3x faster performance
- Modern Python features

**Django** (Better for Full-Stack - 89/100)  
✅ **Pros**:
- Mature ecosystem
- Built-in admin interface
- Comprehensive ORM
- Better for full-stack applications
- Larger community

**🎯 Recommendation**: 
- Choose **FastAPI** for pure APIs, microservices, high-performance needs
- Choose **Django** for full-stack web applications with admin interfaces
```

**Scenario 3: Debugging and Problem Solving**
```
🤖 You: "I'm getting CORS errors in my FastAPI app. How do I fix this?"

Claude: 🔧 **FastAPI CORS Configuration**

From FastAPI documentation:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# For production, be more specific:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**🔐 Security Note**: Never use `allow_origins=["*"]` in production with `allow_credentials=True`.
```

## How It Works

1. **Query Processing** - Takes your search query and target library
2. **Real-Time Enhancement** - Fetches live GitHub data, job market trends (default)
3. **Smart Search** - Uses Serper API for site-specific documentation search
4. **Parallel Fetching** - Concurrently fetches multiple documentation pages
5. **Content Extraction** - Parses clean text using BeautifulSoup
6. **Intelligence Analysis** - Applies real-time scoring and career recommendations
7. **Intelligent Caching** - Stores results for faster future requests

## Environment Variables

### For AWS-Style Deployment (Recommended)
Set in your MCP configuration:

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

### For Local Development
Create a `.env` file with:

```env
SERPER_API_KEY=your_serper_api_key_here
```

## Real-Time Intelligence (Default)

The MCP server uses **real-time data by default** for maximum accuracy:

```bash
# Real-time mode is DEFAULT - no setup needed!
# System automatically fetches:
# - Live GitHub stars, forks, activity
# - Current job market trends  
# - Real-time popularity calculations
# - Career impact analysis

# Optional: Add GitHub token for higher API rate limits
export GITHUB_TOKEN=your_github_token

# Switch to static mode only if needed (not recommended)

```

**Benefits of Real-Time Mode:**
- ✅ Always current data (never stale)
- ✅ Accurate trending analysis  
- ✅ Current job market insights
- ✅ Zero maintenance overhead

## Project Structure

```
documentation-search-mcp/
├── src/
│   └── documentation_search_enhanced/
│       ├── __init__.py           # Package initialization
│       ├── main.py              # Main MCP server implementation
│       └── config.json          # Documentation sources configuration
├── dynamic_enhancer.py          # Optional enhancement module (not used)
├── pyproject.toml              # Project dependencies and packaging
├── publish_to_pypi.sh          # Publishing script for AWS-style deployment
├── test_publish.sh             # Test publishing script
├── PUBLISHING_GUIDE.md         # Step-by-step publishing guide
├── README.md                   # This file
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
└── .env                        # Environment variables (create this for local dev)
```

## Contributing

To add support for new libraries:

1. Add the library and its documentation URL to `config.json`
2. Test that the documentation site returns useful content
3. Submit a pull request

## Troubleshooting

### Common Issues

**❌ "Library not supported"**
```
Solution: Check available libraries with suggest_libraries tool
Available: python, javascript, react, fastapi, django, langchain, openai, anthropic, etc.
```

**❌ "No results found"**
```
Solution: Try broader search terms
❌ "FastAPI OAuth implementation with custom scopes"
✅ "FastAPI authentication" or "FastAPI security"
```

**❌ Tool not appearing in AI assistant**
```
1. Verify MCP configuration file location:
   - Cursor: .cursor/mcp.json
   - Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json
   
2. Check configuration syntax:
   - JSON must be valid
   - Use "uvx" command for AWS-style deployment
   - Include SERPER_API_KEY in env section
   
3. Restart your AI assistant after configuration changes
```

**❌ "SERPER_API_KEY not set" error**
```
1. Get free API key from https://serper.dev
2. Add to MCP configuration:
   "env": {
     "SERPER_API_KEY": "your_key_here"
   }
3. Restart AI assistant
```

**❌ "uvx command not found"**
```
Install UV package manager:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Performance Issues

**🐌 Slow responses**
- First search is slower (cache warming)
- Subsequent searches are much faster
- Use health_check tool to monitor performance

**🔧 Clear cache if issues persist**
- Use clear_cache tool in your AI assistant
- This forces fresh fetches from documentation sources



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
