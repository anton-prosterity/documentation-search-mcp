#!/bin/bash
# Publish to PyPI script
#
# ⚠️ DEPRECATED: This manual script is deprecated in favor of automated GitHub Actions releases.
#
# New Release Process:
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit: git commit -m "chore(release): bump version to X.Y.Z"
# 4. Tag: git tag vX.Y.Z && git push origin vX.Y.Z
# 5. Create GitHub Release (triggers automated PyPI deployment)
#
# See CONTRIBUTING.md for full release process documentation.
#
# This script is kept for emergency manual releases only.

set -e  # Exit on any error

echo "⚠️  WARNING: Using deprecated manual publish script"
echo "   Consider using the automated GitHub Actions release process instead."
echo "   See CONTRIBUTING.md for details."
echo ""
read -p "Continue with manual publish? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

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