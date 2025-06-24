# 🚀 Enhanced Documentation Search MCP Server

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> **Transform Claude into your personal development advisor** 🤖✨
> 
> An intelligent MCP server that gives Claude real-time access to documentation, library popularity data, and career insights. Make smarter technology choices with data-driven recommendations tailored to your experience level.

## ⭐ Why This MCP Server is Different

🎯 **Intelligent Recommendations** - Not just search, but smart suggestions based on your skill level and project needs  
📊 **Data-Driven Insights** - Real popularity scores, job market trends, and learning time estimates  
🚀 **Career-Focused** - Salary insights, trending technologies, and market positioning  
⚡ **Lightning Fast** - Smart caching delivers responses in 2-5 seconds  
🔧 **Drop-in Ready** - Works with Cursor, Claude Desktop, and any MCP-compatible tool  

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

## 🚀 Quick Start (2 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/anton-prosterity/documentation-search-mcp.git
cd documentation-search-mcp
uv sync

# 2. Get your free API key from serper.dev
echo "SERPER_API_KEY=your_key_here" > .env

# 3. Test the MCP server
python main.py
# Press Ctrl+C when you see it waiting for input ✅

# 4. Add to Cursor (.cursor/mcp.json):
```

Create `.cursor/mcp.json` in your project root:
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/path/to/.local/bin/uv", 
      "args": [
        "--directory",
        "/path/to/documentation-search-mcp",
        "run", 
        "main.py"
      ],
      "env": {
        "SERPER_API_KEY": "your_key_here"
      }
    }
  }
}
```

**That's it!** 🎉 Claude now has intelligent development superpowers.

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

## Setup

### Prerequisites

- Python 3.8+
- UV package manager (recommended) or pip

### Installation

1. Clone this repository:
```bash
git clone https://github.com/anton-prosterity/documentation-search-mcp.git
cd documentation-search-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Set up your environment variables:
```bash
echo "SERPER_API_KEY=your_key_here" > .env
```

4. Get a Serper API key:
   - Visit [serper.dev](https://serper.dev)
   - Sign up for a free account
   - Copy your API key to the `.env` file

## Configuration

### Adding New Documentation Sources

Adding new libraries is incredibly simple! Just edit the `config.json` file:

```json
{
    "docs_urls": {
        "your_library": {
            "url": "https://docs.example.com/",
            "category": "web-framework",
            "learning_curve": "easy",
            "tags": ["python", "web", "api"]
        }
    }
}
```

**That's it!** The system automatically:
- ✅ Fetches real-time GitHub stars and metrics
- ✅ Calculates popularity scores and job market trends  
- ✅ Provides career impact analysis
- ✅ Delivers intelligent recommendations

No manual score updates needed - everything is dynamic!

## Usage

### Running the Server

```bash
python main.py
```

### Integration with AI Tools

#### Adding to Cursor

1. Create an MCP configuration file in your project:
   - **Project-specific**: Create `.cursor/mcp.json` in your project root
   - **Global**: Create `~/.cursor/mcp.json` in your home directory

2. Add the MCP server configuration:

**Option A: Using UV (Recommended)**
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/path/to/.local/bin/uv",
      "args": [
        "--directory",
        "/path/to/documentation-search-mcp",
        "run",
        "main.py"
      ],
      "env": {
        "SERPER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Option B: Using Python Virtual Environment**
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/main.py"],
      "env": {
        "SERPER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. Replace paths with your actual file locations:
   - **For UV**: Update the `--directory` path to your project location
   - **For Python venv**: Update both the Python executable and script paths
4. Restart Cursor to load the configuration

**Configuration Options:**
- **Project-specific** (`.cursor/mcp.json`): Use this for MCP servers specific to a project
- **Global** (`~/.cursor/mcp.json`): Use this for MCP servers you want available across all projects

**Path Examples:**
- UV command: Usually `~/.local/bin/uv` or `/usr/local/bin/uv`
- Project directory: Full path to your cloned repository  
- Python venv: `path/to/your/project/.venv/bin/python`

⚠️ **Security Note:** Keep your `.cursor/mcp.json` file private and never commit it to version control with real API keys. Consider using environment variables or a separate `.env` file for sensitive data.

#### Adding to Claude Desktop

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the MCP server configuration:

```json
{
  "mcpServers": {
    "documentation-search": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/main.py"],
      "env": {
        "SERPER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. Replace paths with your actual file locations
4. Restart Claude Desktop

### Available Tools

#### 1. `get_docs` - Documentation Search
Search for specific information within library documentation.

**Parameters:**
- `query` (string): Your search query
- `library` (string): The library to search in

**Example:**
```python
get_docs(query="authentication middleware", library="fastapi")
```

#### 2. `recommend_libraries` - Smart Recommendations
Get personalized library suggestions based on your use case and experience level.

**Parameters:**
- `use_case` (string): Project type (e.g., "web-api", "frontend", "ai")
- `experience_level` (string): Your skill level ("beginner", "intermediate", "advanced")

#### 3. `compare_libraries` - Technology Comparison
Compare multiple libraries with data-driven analysis.

**Parameters:**
- `library_names` (list): Libraries to compare

#### 4. Additional Tools
- `suggest_libraries` - Auto-complete library names
- `get_trending_libraries` - Find trending technologies
- `get_library_insights` - Deep analysis of specific libraries
- `health_check` - Monitor documentation source availability
- `clear_cache` - Clear cached content

## How It Works

1. **Query Processing** - Takes your search query and target library
2. **Real-Time Enhancement** - Fetches live GitHub data, job market trends (default)
3. **Smart Search** - Uses Serper API for site-specific documentation search
4. **Parallel Fetching** - Concurrently fetches multiple documentation pages
5. **Content Extraction** - Parses clean text using BeautifulSoup
6. **Intelligence Analysis** - Applies real-time scoring and career recommendations
7. **Intelligent Caching** - Stores results for faster future requests

## Environment Variables

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
├── main.py                 # Main MCP server implementation
├── dynamic_enhancer.py     # Optional enhancement module (not used)
├── config.json            # Documentation sources configuration
├── pyproject.toml         # Project dependencies
├── README.md              # This file
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT License
└── .env                   # Environment variables (create this)
```

## Contributing

To add support for new libraries:

1. Add the library and its documentation URL to `config.json`
2. Test that the documentation site returns useful content
3. Submit a pull request

## Troubleshooting

### Common Issues

- **"Library not supported"**: Check that the library name matches an entry in `config.json`
- **"No results found"**: Try a more general search query
- **Timeout errors**: Some documentation sites may be slow; this is handled gracefully

### Integration Issues

- **Tool not appearing**: Ensure paths are correct and dependencies are installed
- **Environment variables**: Verify `SERPER_API_KEY` is set in MCP configuration
- **Virtual environment**: Use the correct Python path from your venv



## 🎯 Ready to Transform Your Development Workflow?

### ⭐ **Star this repository** if you find it valuable!

### 🚀 **Get Started Now**
1. **Clone:** `git clone https://github.com/anton-prosterity/documentation-search-mcp.git`
2. **Setup:** `uv sync && echo "SERPER_API_KEY=your_key" > .env`
3. **Integrate:** Add to Cursor/Claude Desktop (see Setup above)
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
