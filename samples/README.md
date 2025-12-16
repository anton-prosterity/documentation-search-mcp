# 🚀 Documentation Search Enhanced - Samples

This directory contains ready-to-use examples showing how to integrate and use the documentation-search-enhanced MCP server with different AI assistants and workflows.

## 📁 Sample Configurations

### 🎯 **Basic Setup Examples**

#### For Cursor
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_key_here",
        "FASTMCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### For Claude Desktop
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_key_here",
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["suggest_libraries", "health_check"]
    }
  }
}
```

#### For Codex CLI
```bash
codex mcp add documentation-search-enhanced \
  --env SERPER_API_KEY=your_key_here \
  --env FASTMCP_LOG_LEVEL=ERROR \
  -- uvx documentation-search-enhanced@latest
```

### 🔧 **Advanced Configuration Examples**

#### Production Configuration
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_production_key",
        "FASTMCP_LOG_LEVEL": "ERROR",
        "GITHUB_TOKEN": "your_github_token_optional"
      },
      "disabled": false,
      "autoApprove": [
        "suggest_libraries",
        "health_check", 
        "get_cache_stats"
      ]
    }
  }
}
```

#### Development Configuration
```json
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "your_dev_key",
        "FASTMCP_LOG_LEVEL": "DEBUG"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## 🎬 **Usage Scenarios**

### Scenario 1: Learning FastAPI
```
👤 User: "I'm new to FastAPI. Show me how to create a simple API with authentication."

🤖 Claude: I'll help you get started with FastAPI! Let me search for authentication examples.

[Using documentation-search-enhanced MCP server...]

📚 **FastAPI Authentication - Complete Guide**

**1. Basic Setup:**
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

@app.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"message": "This is a protected route"}
```

**2. JWT Implementation:**
[Detailed code examples...]
```

### Scenario 2: Comparing Technologies
```
👤 User: "Should I use Django or FastAPI for my new API project?"

🤖 Claude: Great question! Let me analyze both frameworks for you.

[Using documentation-search-enhanced MCP server...]

📊 **Django vs FastAPI Comparison**

**FastAPI** (Recommended for APIs)
✅ **Pros:**
- Native async support
- Automatic API documentation (OpenAPI/Swagger)
- Type hints integration
- 3x faster performance
- Modern Python features

**Django** (Better for full-stack)
✅ **Pros:**
- Mature ecosystem (15+ years)
- Built-in admin interface
- Comprehensive ORM
- Better for complex web applications

**🎯 Recommendation:** FastAPI for pure APIs, Django for full-stack applications.
```

### Scenario 3: Debugging Help
```
👤 User: "I'm getting a CORS error in my React app calling FastAPI. How do I fix it?"

🤖 Claude: CORS errors are common when React and FastAPI are on different ports. Let me show you the solution.

[Using documentation-search-enhanced MCP server...]

🔧 **FastAPI CORS Configuration**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security Note:** Never use `allow_origins=["*"]` with `allow_credentials=True` in production.
```

## 🚀 **Integration Examples**

### With GitHub Codespaces
```json
// .devcontainer/devcontainer.json
{
  "name": "Development Environment",
  "postCreateCommand": "uvx documentation-search-enhanced@latest",
  "customizations": {
    "vscode": {
      "settings": {
        "mcp.servers": {
          "documentation-search-enhanced": {
            "command": "uvx",
            "args": ["documentation-search-enhanced@latest"],
            "env": {
              "SERPER_API_KEY": "${env:SERPER_API_KEY}"
            }
          }
        }
      }
    }
  }
}
```

### With Docker
```dockerfile
FROM python:3.12-slim

# Install UV
RUN pip install uv

# Install MCP server
RUN uvx documentation-search-enhanced@latest

ENV SERPER_API_KEY=""
ENV FASTMCP_LOG_LEVEL="INFO"

CMD ["uvx", "documentation-search-enhanced@latest"]
```

## 🎯 **Best Practices**

### 1. **API Key Management**
```bash
# Use environment variables
export SERPER_API_KEY="your_key_here"

# Or use .env files for local development
echo "SERPER_API_KEY=your_key_here" > .env
```

### 2. **Logging Configuration**
```bash
# Production (minimal logging)
export FASTMCP_LOG_LEVEL="ERROR"

# Development (detailed logging)
export FASTMCP_LOG_LEVEL="DEBUG"

# Default (balanced logging)
export FASTMCP_LOG_LEVEL="INFO"
```

### 3. **Auto-Approve Settings**
```json
{
  "autoApprove": [
    "suggest_libraries",     // Safe: just returns library names
    "health_check",          // Safe: just checks service status
    "get_cache_stats"        // Safe: just returns cache info
  ]
  // Don't auto-approve:
  // - "get_docs" (may fetch external content)
  // - "clear_cache" (modifies system state)
}
```

## 🔒 **Security Considerations**

### 1. **API Key Security**
- Never commit API keys to version control
- Use environment variables or secure vaults
- Rotate keys regularly

### 2. **Auto-Approve Guidelines**
- Only auto-approve read-only operations
- Never auto-approve operations that modify state
- Review auto-approve settings regularly

### 3. **Network Security**
- Monitor outbound requests
- Use HTTPS endpoints only
- Implement rate limiting

## 📚 **Additional Resources**

- [Main Documentation](../README.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Publishing Guide](../PUBLISHING_GUIDE.md) 
