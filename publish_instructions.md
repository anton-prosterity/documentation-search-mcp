# 📦 Publishing to PyPI - Step by Step

## 1. Get Your PyPI Token

1. Go to https://pypi.org and log in
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Give it a name like "documentation-search-enhanced"
5. Set scope to "Entire account" or just this project
6. Copy the token (starts with `pypi-`)

## 2. Set the Token

### Option A: One-time publish (Recommended)
```bash
PYPI_TOKEN="pypi-your-token-here" ./publish_to_pypi.sh
```

### Option B: Export for session
```bash
export PYPI_TOKEN="pypi-your-token-here"
./publish_to_pypi.sh
```

### Option C: Save in .env file (DO NOT COMMIT!)
```bash
echo 'PYPI_TOKEN="pypi-your-token-here"' >> .env
source .env
./publish_to_pypi.sh
```

## 3. Publish Version 1.2.0

Since the package is already built, you can publish directly:

```bash
# Set token and publish
export PYPI_TOKEN="pypi-your-token-here"
./publish_to_pypi.sh
```

Or manually with twine:
```bash
# Install twine if needed
uv pip install twine

# Upload to PyPI
twine upload dist/* --username __token__ --password $PYPI_TOKEN
```

## 4. Verify Publication

After publishing, verify it worked:
```bash
# Check PyPI page
open https://pypi.org/project/documentation-search-enhanced/1.2.0/

# Test installation
uvx documentation-search-enhanced@1.2.0
```

## 5. What's New in 1.2.0

- 🏭 5 Production Tools: Prometheus, Grafana, Elasticsearch, Celery, ESLint
- 🎓 Enhanced multi-library learning paths
- 🔍 Smart search with relevance scoring
- 🌍 Environment-aware configuration
- 📚 104 total libraries supported!

## Troubleshooting

### "File already exists" error
You're trying to publish a version that already exists. Bump the version in `pyproject.toml`.

### Authentication failed
Make sure your token:
- Starts with `pypi-`
- Has the correct permissions
- Is properly quoted in the command

### Test PyPI First (Optional)
To test on TestPyPI first:
```bash
# Use test token
export PYPI_TEST_TOKEN="pypi-test-token"
twine upload --repository testpypi dist/* --username __token__ --password $PYPI_TEST_TOKEN

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ documentation-search-enhanced==1.2.0
``` 