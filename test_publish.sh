#!/bin/bash
# Test publish to TestPyPI (safe testing environment)

set -e

echo "🧪 Test Publishing to TestPyPI..."

if [ -z "$PYPI_TOKEN" ]; then
    echo "❌ Error: PYPI_TOKEN environment variable not set"
    echo "   Get your token from https://pypi.org/manage/account/token/"
    echo "   Then export PYPI_TOKEN=your_token_here"
    exit 1
fi

# Upload to TestPyPI (safe testing)
echo "⬆️ Uploading to TestPyPI (test environment)..."
uv run twine upload --repository testpypi dist/* --username __token__ --password "$PYPI_TOKEN"

echo "✅ Successfully uploaded to TestPyPI!"
echo "🧪 Test install with: pip install -i https://test.pypi.org/simple/ documentation-search-enhanced"
echo "🚀 If everything works, run ./publish_to_pypi.sh for real PyPI" 