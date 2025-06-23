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
🎯 LANGCHAIN - Leading Agentic Framework (Score: 90/100)

📊 Market Analysis:
• GitHub Stars: 85,000+ (explosive growth)
• Job Market: HOT (400% increase in postings)  
• Salary Impact: $40k-$100k+ increase potential
• Companies: Google, Microsoft, OpenAI hiring

💡 Career Intelligence:
"LangChain skills can increase salary by $40k-$100k+. 
400% growth in job postings makes it the #1 AI skill for 2024."
```

## 🚀 Quick Start (2 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/anton-prosterity/documentation-search-mcp.git
cd documentation-search-mcp
uv sync

# 2. Get your free API key from serper.dev
echo "SERPER_API_KEY=your_key_here" > .env

# 3. Test the server
python main.py
# Press Ctrl+C when you see it waiting for input ✅

# 4. Add to Cursor (Settings → Features → MCP):
```

```json
{
  "name": "documentation-search-enhanced",
  "command": "/path/to/.venv/bin/python",
  "args": ["/path/to/main.py"],
  "env": {"SERPER_API_KEY": "your_key_here"}
}
```

**That's it!** 🎉 Claude now has intelligent development superpowers.

## 🛠️ 7 Specialized AI Tools

Transform Claude from a generic assistant into a **data-driven development expert**:

| Tool | What It Does | Example Output |
|------|-------------|----------------|
| 🔍 **`get_docs`** | Smart documentation search | *Returns targeted FastAPI auth docs in 3 seconds* |
| 🎯 **`recommend_libraries`** | Personalized suggestions with career impact | *"FastAPI (88/100): $40k salary boost, 1-2 week learning"* |
| ⚖️ **`compare_libraries`** | Multi-dimensional analysis with winners | *"Winner: Django (63.8/100) vs FastAPI vs Flask"* |
| 📈 **`get_trending_libraries`** | Trend analysis with growth metrics | *"LangChain: Explosive growth, 400% job increase"* |
| 💡 **`get_library_insights`** | Deep market analysis with ROI data | *"React: $30k-$80k salary increase, 2-month ROI"* |
| 🔤 **`suggest_libraries`** | Smart autocomplete with popularity | *"lang" → LangChain (90/100, explosive growth)* |
| ⚡ **`health_check`** | Performance tracking of 30+ sources | *"5/5 sources healthy, avg 207ms response"* |

## 📚 30+ Supported Technologies

**🔥 Hot & Trending:** FastAPI, LangChain, Supabase, Anthropic, OpenAI  
**⚡ Frontend:** React, Vue, Angular, Svelte, TypeScript  
**🛠️ Backend:** Django, Flask, Express, Node.js, PostgreSQL  
**☁️ Cloud & DevOps:** AWS, Docker, Kubernetes, Terraform  
**🤖 AI/ML:** LangChain, LlamaIndex, OpenAI, Anthropic  
**📊 Data Science:** Pandas, NumPy, Streamlit  

*See `config.json` for the complete list.*

## 🌟 Core Intelligence Features

### 🧠 **Multi-Dimensional Scoring**
- **Popularity Metrics** - GitHub stars, community size, enterprise adoption
- **Career Intelligence** - Salary data, job market trends, hiring insights  
- **Experience Matching** - Beginner/Intermediate/Advanced optimization
- **Trend Analysis** - Growth velocity and market timing advice

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

To add support for new libraries, simply edit the `config.json` file:

```json
{
    "docs_urls": {
        "new_library": "https://new-library-docs.com/api/"
    }
}
```

The server will automatically pick up changes on restart. No code modifications required!

## Usage

### Running the Server

```bash
python main.py
```

### Integration with AI Tools

#### Adding to Cursor

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Navigate to "Features" → "Model Context Protocol"
3. Add a new MCP server configuration:

```json
{
  "name": "documentation-search",
  "command": "/path/to/.venv/bin/python",
  "args": ["/path/to/main.py"],
  "env": {
    "SERPER_API_KEY": "your_api_key_here"
  }
}
```

4. Replace paths with your actual file locations
5. Save and restart Cursor

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
2. **Smart Search** - Uses Serper API for site-specific documentation search
3. **Parallel Fetching** - Concurrently fetches multiple pages
4. **Content Extraction** - Parses clean text using BeautifulSoup
5. **Intelligence Analysis** - Applies multi-dimensional scoring and recommendations
6. **Intelligent Caching** - Stores results for faster future requests

## Environment Variables

Create a `.env` file with:

```env
SERPER_API_KEY=your_serper_api_key_here
```

## Hybrid System (Advanced)

For real-time GitHub data and dynamic enhancement:

```bash
# Enable dynamic mode for real-time API data
export ENABLE_DYNAMIC_ENHANCEMENT=true
export GITHUB_TOKEN=your_github_token  # Optional, for higher rate limits
```

This fetches live GitHub stars, job market data, and calculates real-time popularity scores.

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
