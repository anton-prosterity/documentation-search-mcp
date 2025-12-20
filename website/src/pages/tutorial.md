# Documentation Search MCP Server - Tutorial

Complete guide to using the documentation-search-enhanced MCP server for documentation search, security scanning, and project generation.

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Installation & Setup](#installation--setup)
3. [Available Tools](#available-tools)
4. [Documentation Search](#documentation-search)
5. [Security Scanning](#security-scanning)
6. [Project Generation](#project-generation)
7. [Learning & Examples](#learning--examples)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)

---

## What is MCP?

**Model Context Protocol (MCP)** is a standard for connecting AI assistants to external tools and data sources. Think of it as a plugin system that lets Claude, Cursor, and other AI assistants use specialized tools.

**How it works:**
1. You install an MCP server (like documentation-search-enhanced)
2. Configure your AI client (Claude Desktop, Codex CLI, Cursor, etc.)
3. The AI can now call tools from the server to answer your questions

**Example workflow:**
```
You: "Search FastAPI docs for authentication examples"
  ↓
Claude Desktop sees you need documentation
  ↓
Claude calls the semantic_search tool from documentation-search-enhanced
  ↓
Tool fetches and searches FastAPI documentation
  ↓
Claude receives results and explains them to you
```

---

## Installation & Setup

### Prerequisites

- Python 3.12+ (3.13 supported for core features)
- uv package manager: https://docs.astral.sh/uv
- One of: Claude Desktop, Codex CLI, Cursor, or another MCP client

### Step 1: Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Verify installation
which uvx
# Expected: /Users/yourusername/.local/bin/uvx
```

### Step 2: Test the Package

```bash
# This will download and cache the package
uvx documentation-search-enhanced@1.6.3
# You'll see JSON-RPC errors - this is normal (server needs a client)
# Press Ctrl+C to exit
```

### Step 3: Configure Your MCP Client

#### Option A: Claude Desktop

1. Find your uvx path:
```bash
which uvx
# Copy this path
```

2. Edit Claude Desktop config:
```bash
# macOS
open ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
nano ~/.config/Claude/claude_desktop_config.json
```

3. Add this configuration (replace paths with your actual paths):
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/Users/yourusername/.local/bin/uvx",
      "args": ["documentation-search-enhanced@1.6.3"],
      "env": {
        "SERPER_API_KEY": "your_api_key_here_or_leave_empty"
      }
    }
  }
}
```

4. Restart Claude Desktop

5. Look for the 🔌 icon in Claude Desktop - it shows connected MCP servers

#### Option B: Codex CLI

```bash
# Get your uvx path
which uvx

# Add the MCP server (with SERPER API key)
codex mcp add documentation-search-enhanced \
  --env SERPER_API_KEY=your_key_here \
  -- /Users/yourusername/.local/bin/uvx documentation-search-enhanced@1.6.3

# Or without SERPER API key (uses prebuilt index)
codex mcp add documentation-search-enhanced \
  -- /Users/yourusername/.local/bin/uvx documentation-search-enhanced@1.6.3

# Verify
codex mcp list

# Start interactive session
codex
```

#### Option C: Cursor

In Cursor settings, add to MCP configuration:
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "/Users/yourusername/.local/bin/uvx",
      "args": ["documentation-search-enhanced@1.6.3"]
    }
  }
}
```

### Optional: Enable Semantic Search

For AI-powered semantic search (adds ~600MB, Python 3.12 only):

```bash
# Create a virtual environment
python3.12 -m venv ~/.venv-doc-search
source ~/.venv-doc-search/bin/activate

# Install with vector search
pip install documentation-search-enhanced[vector]==1.6.3

# Update your MCP config to use this Python instead of uvx
# Replace "command" with: "/Users/yourusername/.venv-doc-search/bin/python"
# Replace "args" with: ["-m", "documentation_search_enhanced.main"]
```

---

## Available Tools

### Core Tools

| Tool | Purpose | Use When |
|------|---------|----------|
| `semantic_search` | Search documentation across 100+ sources | Finding docs, tutorials, API references |
| `get_docs` | Fetch specific documentation URLs | Getting full doc pages |
| `get_learning_path` | Generate learning roadmap | Learning new technology |
| `get_code_examples` | Find code snippets | Need implementation examples |
| `scan_project_dependencies` | Scan for vulnerabilities | Check project security |
| `snyk_scan_project` | Detailed Snyk security analysis | Deep security audit |
| `generate_project_starter` | Create project boilerplate | Starting new project |
| `manage_dev_environment` | Generate docker-compose files | Setting up development environment |
| `compare_library_security` | Compare library vulnerabilities | Choosing between libraries |

---

## Documentation Search

### Basic Search

**Example 1: Simple Documentation Query**

```
You: "How do I set up authentication in FastAPI?"

What happens:
- Claude calls semantic_search(query="FastAPI authentication", libraries=["fastapi"])
- Tool searches FastAPI documentation
- Returns relevant sections about OAuth2, JWT, security
- Claude explains the concepts and provides code examples
```

**Example 2: Multi-Library Search**

```
You: "Compare authentication approaches in FastAPI vs Flask"

What happens:
- Claude calls semantic_search(query="authentication", libraries=["fastapi", "flask"])
- Tool searches both documentation sets
- Returns authentication docs from both frameworks
- Claude provides comparative analysis
```

**Example 3: Specific Topic Search**

```
You: "Show me React hooks documentation for useEffect"

What happens:
- Claude calls semantic_search(query="useEffect hook lifecycle", libraries=["react"])
- Tool finds React docs on useEffect
- Claude explains usage patterns and common pitfalls
```

### Advanced Search Features

**Version-Specific Documentation:**

```
You: "How does async/await work in Python 3.11?"

What happens:
- Claude calls semantic_search(query="async await", libraries=["python"], version="3.11")
- Tool fetches Python 3.11 specific documentation
- Returns version-specific syntax and features
```

**With Vector Search (if installed):**

```
You: "Find documentation about database connection pooling"

What happens:
- Claude calls semantic_search(query="...", use_vector_rerank=True)
- Tool uses semantic embeddings for better relevance
- Results ranked by: 50% semantic similarity + 30% keywords + 20% source authority
- More contextually relevant results than keyword-only search
```

### Supported Documentation Sources

**Web Frameworks:**
- FastAPI, Flask, Django, Express.js, NestJS, Spring Boot

**Frontend:**
- React, Vue, Angular, Svelte, Next.js, Nuxt

**Data Science:**
- NumPy, Pandas, Scikit-learn, TensorFlow, PyTorch

**Cloud & DevOps:**
- AWS, Azure, GCP, Docker, Kubernetes, Terraform

**Languages:**
- Python, JavaScript, TypeScript, Go, Rust, Java

**And 70+ more sources**

---

## Security Scanning

### Scan Local Project

**Example 1: Quick Vulnerability Check**

```
You: "Scan my project for vulnerabilities"
You: "The project is at /Users/me/myapp"

What happens:
- Claude calls scan_project_dependencies(project_path="/Users/me/myapp")
- Tool detects package manager (requirements.txt, package.json, etc.)
- Scans with Safety, pip-audit, and OSV
- Returns list of vulnerabilities with CVSS scores
- Claude summarizes critical issues and suggests fixes
```

**Example output:**
```
Found 3 vulnerabilities:

CRITICAL (CVSS 9.8):
- Package: requests==2.25.1
- CVE-2023-32681: Unintended leak of Proxy-Authorization header
- Fix: Upgrade to requests>=2.31.0

HIGH (CVSS 7.5):
- Package: flask==1.1.2
- CVE-2023-30861: Cookie parsing vulnerability
- Fix: Upgrade to flask>=2.3.2

MEDIUM (CVSS 5.3):
- Package: pyyaml==5.3.1
- CVE-2020-14343: Arbitrary code execution
- Fix: Upgrade to pyyaml>=5.4
```

**Example 2: Detailed Snyk Analysis**

```
You: "Run a detailed security audit on my project"

What happens:
- Claude calls snyk_scan_project(project_path="/Users/me/myapp")
- Snyk performs deep dependency tree analysis
- Checks for outdated packages, licensing issues, and security vulnerabilities
- Returns detailed remediation advice
```

**Example 3: Security Report Generation**

```
You: "Generate a security report for my project and save it to a file"

What happens:
- Claude scans your project
- Formats results as markdown or JSON
- Uses Write tool to save report
- You get a shareable security audit document
```

### Compare Library Security

**Example: Choosing Between Libraries**

```
You: "Should I use requests or httpx? Which is more secure?"

What happens:
- Claude calls compare_library_security(libraries=["requests", "httpx"])
- Tool fetches CVE data for both packages
- Compares vulnerability counts, severity, and patching history
- Claude provides recommendation based on security posture
```

**Example output:**
```
Security Comparison: requests vs httpx

requests:
- 12 known CVEs (5 critical, 4 high, 3 medium)
- Last critical CVE: 6 months ago (patched)
- Active maintenance: Yes
- Security score: 7.5/10

httpx:
- 2 known CVEs (0 critical, 1 high, 1 medium)
- Last critical CVE: Never
- Active maintenance: Yes
- Security score: 9.0/10

Recommendation: httpx has a better security track record
```

---

## Project Generation

### Generate Project Starters

**Example 1: FastAPI Project**

```
You: "Create a new FastAPI project called 'my-api'"

What happens:
- Claude calls generate_project_starter(
    project_type="fastapi",
    project_name="my-api"
  )
- Tool generates:
  - Project structure (app/, tests/, config/)
  - main.py with example endpoints
  - requirements.txt with dependencies
  - .env.example for configuration
  - README.md with setup instructions
  - Dockerfile and docker-compose.yml
```

**Generated structure:**
```
my-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app with example routes
│   ├── models.py         # Pydantic models
│   ├── database.py       # Database connection
│   └── routers/
│       ├── __init__.py
│       └── users.py      # Example user routes
├── tests/
│   ├── __init__.py
│   └── test_main.py      # Example tests
├── requirements.txt      # Dependencies
├── .env.example          # Environment variables template
├── Dockerfile           # Production-ready container
├── docker-compose.yml   # Local development setup
└── README.md            # Setup and usage instructions
```

**Example 2: React Project**

```
You: "Generate a React project with TypeScript"

What happens:
- Claude calls generate_project_starter(
    project_type="react",
    project_name="my-react-app",
    options={"typescript": true}
  )
- Tool generates:
  - Vite-based React setup
  - TypeScript configuration
  - Example components
  - Routing setup (React Router)
  - State management boilerplate
  - Testing setup (Vitest)
```

**Example 3: Full-Stack Project**

```
You: "Create a full-stack app with FastAPI backend and React frontend"

What happens:
- Claude generates both projects
- Creates shared docker-compose.yml
- Sets up API proxy configuration
- Configures CORS
- Provides unified development workflow
```

### Development Environment Setup

**Example: Docker Compose Generation**

```
You: "Set up a development environment with PostgreSQL, Redis, and my FastAPI app"

What happens:
- Claude calls manage_dev_environment(
    services=["postgresql", "redis", "fastapi"],
    project_path="/Users/me/myapp"
  )
- Tool generates docker-compose.yml:

version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/myapp
      REDIS_URL: redis://redis:6379

volumes:
  postgres_data:
```

**To use:**
```bash
docker-compose up -d
```

---

## Learning & Examples

### Get Learning Path

**Example 1: Learning New Framework**

```
You: "I want to learn FastAPI. Create a learning roadmap"

What happens:
- Claude calls get_learning_path(
    technology="fastapi",
    skill_level="beginner",
    goals=["Build REST API", "Deploy to production"]
  )
- Tool generates structured learning path
```

**Example output:**
```
FastAPI Learning Path (Beginner → Intermediate)

Week 1: Fundamentals
✓ Python basics (async/await, type hints)
✓ HTTP protocols and REST APIs
✓ Install FastAPI and Uvicorn
✓ First "Hello World" API
  Resources: FastAPI Tutorial - First Steps

Week 2: Core Concepts
✓ Path parameters and query parameters
✓ Request body with Pydantic models
✓ Response models and status codes
✓ Data validation
  Resources: FastAPI Tutorial - Request Body

Week 3: Database Integration
✓ SQLAlchemy basics
✓ Database models and relationships
✓ CRUD operations
✓ Async database queries
  Resources: FastAPI SQL Databases

Week 4: Authentication & Security
✓ OAuth2 with Password flow
✓ JWT tokens
✓ Password hashing
✓ Dependency injection
  Resources: FastAPI Security

Week 5: Advanced Features
✓ Background tasks
✓ WebSockets
✓ File uploads
✓ Testing with pytest
  Resources: FastAPI Advanced User Guide

Week 6: Deployment
✓ Docker containerization
✓ Environment configuration
✓ Logging and monitoring
✓ Deploy to AWS/Railway/Render
  Resources: FastAPI Deployment
```

**Example 2: Code Examples**

```
You: "Show me examples of JWT authentication in FastAPI"

What happens:
- Claude calls get_code_examples(
    topic="JWT authentication",
    language="python",
    framework="fastapi"
  )
- Tool finds relevant code snippets
- Claude explains and adapts to your needs
```

**Example output:**
```python
# JWT Authentication in FastAPI

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify user credentials (check database)
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}
```

---

## Advanced Usage

### Combining Multiple Tools

**Example: Complete Project Setup Workflow**

```
You: "I'm starting a new FastAPI project with authentication. Set up everything for me."

What happens (multi-step workflow):
1. Claude generates FastAPI starter
2. Searches FastAPI auth docs
3. Adds authentication code
4. Generates docker-compose with PostgreSQL
5. Scans dependencies for vulnerabilities
6. Provides setup instructions
```

**Example: Security-First Development**

```
You: "I need to choose between Flask, FastAPI, and Django for a new API. Consider security."

What happens:
1. Claude compares security records of all three
2. Searches current best practices for each
3. Provides recommendation based on your requirements
4. Generates starter for chosen framework
5. Pre-configures security best practices
```

### Customizing Search

**Disable vector search for faster results:**
```python
# Claude will use: use_vector_rerank=False
# Results in <100ms response time vs ~500ms with vector search
```

**Search specific versions:**
```
You: "Find Python 3.12 specific features for asyncio"

# Claude searches: version="3.12" parameter
```

**Filter by source type:**
```
You: "Search only official documentation, no blog posts"

# Claude filters for official doc sources
```

---

## Troubleshooting

### MCP Server Won't Start

**Error:** `MCP startup failed: No such file or directory (os error 2)`

**Solution:**
```bash
# 1. Find your actual uvx path
which uvx

# 2. Update config with FULL path (not just "uvx")
# Wrong: "command": "uvx"
# Right: "command": "/Users/yourusername/.local/bin/uvx"
```

### JSON-RPC Errors When Testing

**Error:** `Invalid JSON: EOF while parsing a value`

**This is normal!** MCP servers need a client (Claude Desktop, Codex). You can't run them directly. Just test with your MCP client instead.

### Vector Search Not Working

**Symptoms:** Search results seem basic, no semantic ranking

**Causes:**
1. Vector dependencies not installed (Python 3.13 or missing `[vector]` extra)
2. First run is building index (takes a few seconds)

**Solutions:**
```bash
# Check if vector search is available
python3.12 -m pip show sentence-transformers

# If not installed, install with vector extra (Python 3.12 only)
pip install documentation-search-enhanced[vector]==1.6.3
```

### Slow Performance

**If searches take >5 seconds:**

1. **Check SERPER_API_KEY:** Without it, the tool crawls documentation in real-time (slower)
2. **Prebuilt index:** The tool downloads a prebuilt index from GitHub Releases automatically
3. **Vector search:** Adds ~200-500ms. Disable with `use_vector_rerank=False` if not needed

**Speed comparison:**
- With SERPER + prebuilt index: 100-200ms
- With prebuilt index only: 500-1000ms
- Live crawling (no index): 3-10 seconds
- Vector search enabled: +200-500ms

### Package Installation Fails

**Error:** `Could not find a version that satisfies the requirement`

**Solution:**
```bash
# 1. Check Python version
python --version  # Need 3.12+

# 2. Use uvx (recommended) instead of pip
uvx documentation-search-enhanced@1.6.3

# 3. If using pip, upgrade pip first
pip install --upgrade pip
```

### Can't Find Documentation

**If search returns no results:**

1. Check spelling of library name
2. Try broader search terms
3. Check if source is supported (see Available Tools section)
4. Use `get_docs` with direct URL if you know the doc location

---

## Real-World Workflows

### Workflow 1: Secure API Development

```
1. Generate FastAPI starter
   You: "Create a FastAPI project called 'secure-api'"

2. Add authentication
   You: "Add JWT authentication to this project"

3. Security scan
   You: "Scan this project for vulnerabilities"

4. Fix issues
   Claude: "Found 2 vulnerabilities in dependencies"
   You: "Update the requirements.txt with secure versions"

5. Set up development environment
   You: "Add PostgreSQL and Redis to docker-compose"

6. Deploy
   You: "How do I deploy this to AWS?"
```

### Workflow 2: Learning New Technology

```
1. Get learning path
   You: "I want to learn React. Create a learning roadmap"

2. Start with basics
   You: "Explain React hooks with examples"

3. Build project
   You: "Generate a React project with routing and state management"

4. Find specific examples
   You: "Show me examples of useEffect for data fetching"

5. Add features
   You: "How do I add authentication to this React app?"
```

### Workflow 3: Library Selection

```
1. Compare options
   You: "Compare FastAPI, Flask, and Django for building REST APIs"

2. Check security
   You: "Which has the best security track record?"

3. Review documentation
   You: "Search each framework's docs for authentication"

4. Generate starter
   You: "Create a starter project with the recommended framework"

5. Verify setup
   You: "Scan the generated project for vulnerabilities"
```

---

## Tips & Best Practices

### Writing Effective Queries

**Good queries:**
- "Search FastAPI docs for database migrations with Alembic"
- "Find React documentation about performance optimization"
- "Show me examples of async/await in Python"

**Less effective queries:**
- "docs" (too vague)
- "help" (unclear what you need)
- "fix my code" (AI can't access your code without you sharing it)

### Security Scanning Best Practices

1. **Scan regularly:** Before each deployment
2. **Fix critical issues immediately:** CVSS 9.0+ vulnerabilities
3. **Keep dependencies updated:** Use `pip list --outdated`
4. **Document exceptions:** If you can't update, document why

### Project Generation Tips

1. **Customize after generation:** Templates are starting points
2. **Review generated code:** Understand what it does
3. **Update dependencies:** Check for newer versions
4. **Follow the README:** Generated projects include setup instructions

---

## Getting Help

### Check Logs

**Claude Desktop logs:**
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Look for errors from documentation-search-enhanced
```

**Codex CLI:**
```bash
codex --verbose
# Enables detailed logging
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "MCP server failed to start" | Check uvx path is absolute, not relative |
| "No results found" | Try broader search terms, check library name spelling |
| "Timeout error" | First run downloads index (~50MB), wait 30s and retry |
| "Vector search not working" | Only works on Python 3.12, needs `[vector]` extra |
| "Slow searches" | Add SERPER_API_KEY for faster results |

### Report Issues

GitHub Issues: https://github.com/anton-prosterity/documentation-search-mcp/issues

Include:
- Python version (`python --version`)
- Package version (`uvx documentation-search-enhanced@1.6.3 --version`)
- MCP client (Claude Desktop / Codex / Cursor)
- Error messages or logs

---

## What's Next?

**Explore more:**
- Try semantic search with the `[vector]` extra
- Generate different project types (React, Django, NestJS)
- Set up security scanning in CI/CD
- Create custom learning paths
- Compare libraries before choosing dependencies

**Advanced topics:**
- Custom documentation sources (coming soon)
- Private repository scanning
- Team collaboration features
- CI/CD integration examples

---

## Quick Reference

### Most Common Commands

**Search documentation:**
```
"Search [framework] docs for [topic]"
"Find examples of [feature] in [language]"
```

**Security scanning:**
```
"Scan my project for vulnerabilities"
"Compare security of [library1] vs [library2]"
```

**Project generation:**
```
"Create a [framework] project called [name]"
"Generate docker-compose with [services]"
```

**Learning:**
```
"Create a learning path for [technology]"
"Show me examples of [concept]"
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SERPER_API_KEY` | Enable live web search | None (uses prebuilt index) |
| `DOCS_SITE_INDEX_AUTO_DOWNLOAD` | Auto-download doc index | `true` |
| `DOCS_SITE_INDEX_PATH` | Custom index location | `~/.cache/doc-search/` |

### Supported Project Types

- `fastapi` - FastAPI REST API
- `react` - React frontend app
- `django` - Django web application
- `flask` - Flask API
- `nextjs` - Next.js full-stack app
- `vue` - Vue.js frontend app

### Supported Scan Tools

- **Safety:** Python CVE database
- **pip-audit:** PyPI advisory database
- **OSV:** Google's Open Source Vulnerabilities DB
- **Snyk:** Commercial-grade security scanning

---

**Happy coding with documentation-search-enhanced! 🚀**
