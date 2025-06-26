# 📦 Publishing Guide: AWS-Style Deployment

This guide shows how to publish your MCP server to PyPI to replicate the AWS MCP deployment model.

## 🎯 Goal: Enable `uvx your-package@latest` Usage

After publishing, users can run your MCP server exactly like AWS servers:

```bash
# No local setup needed - just like AWS MCP servers
uvx documentation-search-enhanced@latest
```

## 📋 Prerequisites

1. **PyPI Account**: Create account at [pypi.org](https://pypi.org/account/register/)
2. **API Token**: Generate at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
3. **UV Package Manager**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## 🚀 Publishing Steps

### Step 1: Set Up PyPI Token

```bash
# Set your PyPI token as environment variable
export PYPI_TOKEN="pypi-your-token-here"
```

### Step 2: Verify Package Configuration

Your `pyproject.toml` should have:

```toml
[project.scripts]
documentation-search-enhanced = "documentation_search_enhanced.main:main"
```

✅ **Already configured** - this creates the console command users will run.

### Step 3: Build and Publish

```bash
# Make the script executable and run it
chmod +x publish_to_pypi.sh
./publish_to_pypi.sh
```

Or manually:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Install build dependencies
uv add --dev twine

# Build the package
uv build

# Check the package
uv run twine check dist/*

# Upload to PyPI
uv run twine upload dist/* --username __token__ --password "$PYPI_TOKEN"
```

## 🎉 Success! Your MCP Server is Now AWS-Style

Once published, users can:

```bash
# Install and run directly (no cloning)
uvx documentation-search-enhanced@latest

# Add to their AI assistant configuration
{
  "mcpServers": {
    "documentation-search-enhanced": {
      "command": "uvx",
      "args": ["documentation-search-enhanced@latest"],
      "env": {
        "SERPER_API_KEY": "user_key_here"
      }
    }
  }
}
```

## 🔄 Publishing Updates

When you make changes:

```bash
# 1. Update version in pyproject.toml
[project]
version = "1.0.1"  # Increment version

# 2. Republish
./publish_to_pypi.sh
```

Users automatically get updates when they restart their AI assistant (due to `@latest`).

## 🔍 Key Differences from AWS Pattern

| Aspect | AWS MCP | Your MCP | Status |
|--------|---------|----------|---------|
| Distribution | PyPI | PyPI | ✅ Same |
| Command | `uvx awslabs.service@latest` | `uvx documentation-search-enhanced@latest` | ✅ Same |
| Zero Setup | ✅ | ✅ | ✅ Same |
| Auto Updates | ✅ | ✅ | ✅ Same |
| Isolated Env | ✅ | ✅ | ✅ Same |

## ⚠️ Important Notes

1. **Unique Package Name**: Ensure your package name is unique on PyPI
2. **Version Management**: Always increment version numbers for updates
3. **Testing**: Test locally before publishing with `uv run documentation-search-enhanced`
4. **Documentation**: Update README to show the `uvx` usage pattern

## 🎯 Result: Professional MCP Distribution

Your MCP server now has the same professional deployment pattern as AWS MCP servers:

- ✅ No local cloning required
- ✅ Zero setup complexity for users  
- ✅ Automatic dependency management
- ✅ Universal compatibility
- ✅ Professional presentation 