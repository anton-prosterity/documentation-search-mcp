# 🤝 Contributing to Enhanced Documentation Search MCP Server

Thank you for your interest in contributing! This project thrives on community contributions, and we welcome developers of all skill levels.

## 🌟 Ways to Contribute

### 📚 **Add New Libraries**
The easiest way to contribute! Add support for new documentation sources:

1. **Add to `src/documentation_search_enhanced/config.json` (or the remote catalog if configured):**
```json
{
  "docs_urls": {
    "your_library": {
      "url": "https://docs.yourlibrary.com/",
      "category": "web-framework",
      "learning_curve": "moderate",
      "tags": ["python", "web", "api"],
      "priority": "medium",
      "auto_approve": true
    }
  }
}
```

2. **Test it works:**
```bash
uv run python -m documentation_search_enhanced.main
# Test search functionality
```

3. **Submit a Pull Request** with the library details

### 🐛 **Bug Reports**
Found an issue? Help us fix it:

- **Search existing issues** first
- **Use the bug report template**
- **Include steps to reproduce**
- **Add system information** (OS, Python version)

### ✨ **Feature Requests**
Have ideas for new features?

- **Check existing feature requests**
- **Describe the use case** clearly
- **Explain the expected behavior**
- **Consider implementation complexity**

### 🔧 **Code Contributions**
Ready to dive into the code?

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** if applicable
5. **Update documentation**
6. **Submit a Pull Request**

## 🛠️ Development Setup

### **Prerequisites**
- Python 3.12+
- UV package manager (recommended)
- Optional: Serper API key (free at serper.dev)

### **Setup Steps**
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/documentation-search-mcp.git
cd documentation-search-mcp

# 2. Install dependencies
uv sync

# 3. Set up environment
# Optional: enable Serper-powered search
# echo "SERPER_API_KEY=your_key_here" > .env

# 4. Test the setup
uv run python -m documentation_search_enhanced.main
# Press Ctrl+C when you see it waiting for input ✅
```

## 📋 Pull Request Guidelines

### **CI/CD Requirements**
All pull requests must pass automated checks before merging:

**Required Status Checks:**
- ✅ **Lint (Ruff)** - Code quality and formatting
- ✅ **Type Check (mypy)** - Static type checking
- ✅ **Tests** - All pytest tests must pass
- ✅ **Build Validation** - Package must build successfully
- ✅ **Security Scan** - No high-severity vulnerabilities

**To Run Checks Locally:**
```bash
# Linting
uv run ruff check src --fix
uv run ruff format src

# Type checking
uv pip install mypy types-PyYAML
uv run mypy src/documentation_search_enhanced --ignore-missing-imports

# Tests with coverage
uv run pytest --ignore=pytest-test-project --cov=src/documentation_search_enhanced -v

# Build validation
uv build
uv run twine check dist/*
```

### **Before Submitting**
- [ ] Code follows existing style conventions
- [ ] All tests pass locally
- [ ] Code is properly formatted (Ruff)
- [ ] Type hints are added where appropriate
- [ ] Documentation is updated
- [ ] Changes are described in PR description
- [ ] No high-severity security issues

### **PR Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Library addition

## Testing
- [ ] Tested locally
- [ ] Added new tests (if applicable)
- [ ] All existing tests pass
- [ ] CI checks pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Linting passes (Ruff)
- [ ] Type checking passes (mypy)
- [ ] Self-review completed
- [ ] Documentation updated
```

## 🎯 Priority Areas

We're especially looking for help with:

### **🔥 High Priority**
- **More documentation sources** (especially trending libraries)
- **Performance optimizations**
- **Error handling improvements**
- **Integration guides** for other IDEs

### **📈 Medium Priority**
- **Advanced caching strategies**
- **Metrics and analytics**
- **Configuration validation**
- **Unit tests**

### **💡 Ideas Welcome**
- **UI/visualization tools**
- **Alternative API integrations**
- **Machine learning features**
- **Developer workflow integrations**

## 🚢 Release Process

Releases are fully automated via GitHub Actions:

### **For Maintainers**
1. **Update Version:**
   ```bash
   # Edit pyproject.toml and update version
   vim pyproject.toml  # Change version = "1.4.1" to "1.5.0"
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [1.5.0] - 2025-01-XX
   ### Added
   - New feature description
   ### Fixed
   - Bug fix description
   ```

3. **Commit and Tag:**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore(release): bump version to 1.5.0"
   git push origin main
   git tag v1.5.0
   git push origin v1.5.0
   ```

4. **Create GitHub Release:**
   - Go to [Releases](https://github.com/antonmishel/documentation-search-mcp/releases)
   - Click "Create a new release"
   - Select the tag (v1.5.0)
   - Generate release notes automatically
   - Publish release

5. **Automated Deployment:**
   - GitHub Actions automatically builds the package
   - Validates version consistency
   - Publishes to PyPI using Trusted Publishing
   - Uploads build artifacts to GitHub Release

### **Version Numbering**
Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.x.x) - Breaking changes
- **MINOR** (x.1.x) - New features, backwards compatible
- **PATCH** (x.x.1) - Bug fixes, backwards compatible

## 🏷️ Issue Labels

- `good first issue` - Perfect for newcomers
- `help wanted` - We'd love community help
- `bug` - Something isn't working
- `enhancement` - New feature or improvement
- `documentation` - Documentation improvements
- `library-request` - New library support request

## 📞 Getting Help

### **Community Support**
- **GitHub Issues** - For bugs and feature requests
- **GitHub Discussions** - For questions and ideas
- **Pull Request Comments** - For code-specific discussions

### **Direct Contact**
- **Maintainer:** [@anton-prosterity](https://github.com/anton-prosterity)
- **Response Time:** Usually within 24-48 hours

## 🏆 Recognition

Contributors are recognized in:
- **README.md** contributor section
- **Release notes** for significant contributions
- **GitHub contributors page**

## 📜 Code of Conduct

### **Our Pledge**
We're committed to providing a welcoming, inclusive environment for everyone.

### **Expected Behavior**
- Be respectful and constructive
- Welcome newcomers and help them learn
- Focus on technical merits in discussions
- Respect different perspectives and experiences

### **Unacceptable Behavior**
- Harassment or discrimination of any kind
- Offensive language or personal attacks
- Spam or irrelevant promotions
- Violation of privacy or confidentiality

## 🚀 Quick Contribution Ideas

### **5-Minute Contributions**
- Fix typos in documentation
- Add missing library tags
- Update broken documentation links
- Improve error messages

### **30-Minute Contributions**
- Add a new library to `config.json`
- Write integration guide for new IDE
- Create example usage scenarios
- Improve existing documentation

### **1-Hour+ Contributions**
- Implement new MCP tools
- Add comprehensive test coverage
- Create performance benchmarks
- Build visualization features

---

## 🎉 Thank You!

Every contribution, no matter how small, makes this project better for the entire developer community. We appreciate your time and effort in helping us build the future of AI-powered development tools!

**Ready to contribute?** Check out our [good first issues](https://github.com/anton-prosterity/documentation-search-mcp/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) and get started today!

---

*This contributing guide is inspired by the best practices from successful open-source projects. Have suggestions for improvement? We'd love to hear them!* 
