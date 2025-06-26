# 🤝 Contributing to Enhanced Documentation Search MCP Server

Thank you for your interest in contributing! This project thrives on community contributions, and we welcome developers of all skill levels.

## 🌟 Ways to Contribute

### 📚 **Add New Libraries**
The easiest way to contribute! Add support for new documentation sources:

1. **Add to `src/documentation_search_enhanced/config.json`:**
```json
{
  "docs_urls": {
    "your_library": {
      "url": "https://docs.yourlibrary.com/",
      "category": "web-framework",
      "learning_curve": "moderate",
      "tags": ["python", "web", "api"]
    }
  },
  "categories": {
    "web-framework": ["fastapi", "django", "flask", "your_library"]
  }
}
```

2. **Test it works:**
```bash
python src/documentation_search_enhanced/main.py
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
- Python 3.8+
- UV package manager (recommended)
- Serper API key (free at serper.dev)

### **Setup Steps**
```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/documentation-search-mcp.git
cd documentation-search-mcp

# 2. Install dependencies
uv sync

# 3. Set up environment
echo "SERPER_API_KEY=your_key_here" > .env

# 4. Test the setup
python src/documentation_search_enhanced/main.py
# Press Ctrl+C when you see it waiting for input ✅
```

## 📋 Pull Request Guidelines

### **Before Submitting**
- [ ] Code follows existing style conventions
- [ ] All tests pass (if applicable)
- [ ] Documentation is updated
- [ ] Changes are described in PR description

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

## Checklist
- [ ] Code follows style guidelines
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