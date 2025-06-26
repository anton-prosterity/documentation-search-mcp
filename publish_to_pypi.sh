#!/bin/bash
# Publish to PyPI script

set -e  # Exit on any error

echo "🚀 Publishing Documentation Search Enhanced to PyPI..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "📦 Building package..."
uv build

# Check the package
echo "🔍 Checking package..."
uv run twine check dist/*

# Upload to PyPI (requires PYPI_TOKEN environment variable)
echo "⬆️ Uploading to PyPI..."
if [ -z "$PYPI_TOKEN" ]; then
    echo "❌ Error: PYPI_TOKEN environment variable not set"
    echo "   Get your token from https://pypi.org/manage/account/token/"
    echo "   Then export PYPI_TOKEN=your_token_here"
    exit 1
fi

uv run twine upload dist/* --username __token__ --password "$PYPI_TOKEN"

echo "✅ Successfully published to PyPI!"
echo "📝 Users can now install with: uvx documentation-search-enhanced@latest" 