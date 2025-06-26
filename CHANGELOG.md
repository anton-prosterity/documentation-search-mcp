# Changelog

All notable changes to Documentation Search Enhanced MCP Server will be documented in this file.

## [1.3.0] - 2025-06-26

### Added
- **Project-Aware Security Scan**: New `scan_project_dependencies` tool to scan all dependencies in a project (`pyproject.toml`, `requirements.txt`, etc.) for vulnerabilities.
- **Project Boilerplate Generation**: New `generate_project_starter` tool to create starter projects from templates (FastAPI, React+Vite).
- **Multi-Library Search**: Enhanced `get_docs` and `semantic_search` to accept a list of libraries, allowing for comparison and discovery across multiple documentation sources.
- **Local Dev Environment Management**: New `manage_dev_environment` tool to generate `docker-compose.yml` files for services like `postgres`, `redis`, and `rabbitmq`.

### Changed
- Pivoted away from the complex Test Execution feature in favor of the more robust Docker Environment Management.

### Fixed
- Resolved numerous bugs in the multi-library search and project generation features through iterative testing and debugging.
- Corrected a `ModuleNotFoundError` by adding `PyYAML` as a dependency.

## [1.2.0] - 2025-06-26

### Added
- **Production Essential Tools** (5 new libraries):
  - Prometheus - Monitoring and metrics
  - Grafana - Data visualization and dashboards
  - Elasticsearch - Search and analytics engine
  - Celery - Distributed task queue
  - ESLint - JavaScript linting
  
- **Enhanced Learning Paths**:
  - Multi-library learning paths that intelligently use different documentation sources
  - New comprehensive paths: frontend-development, backend-development, fullstack-development, devops
  - Individual library paths now reference multiple related libraries for better learning
  
- **Advanced Search Features**:
  - `semantic_search` - AI-powered search with relevance scoring
  - `filtered_search` - Filter by content type, difficulty level, code examples
  - `get_code_examples` - Extract curated code examples from documentation
  
- **Environment-Aware Configuration**:
  - Support for development, testing, staging, and production environments
  - Environment-specific settings for caching, logging, and rate limiting
  - Auto-detection from ENVIRONMENT/ENV variables
  
- **Enhanced Features**:
  - Smart query expansion for better search results
  - Content difficulty assessment
  - Cross-reference detection
  - Contextual recommendations
  - Structured logging with performance tracking

### Changed
- Learning paths now use multiple libraries for comprehensive education
- Configuration structure enhanced with server_config, features, and priorities
- Cache TTL now environment-aware (1 hour dev, 24 hours production)

### Fixed
- Removed duplicate main.py file that was causing RuntimeWarning
- Fixed linter errors in security tool implementations

## [1.1.0] - 2025-06-26

### Added
- OSINT vulnerability scanning using OSV Database, GitHub Security Advisories, and Safety DB
- Security scoring system (0-100 scale) for libraries
- New security-focused tools:
  - `scan_library_vulnerabilities` - Full vulnerability scan
  - `get_security_summary` - Quick security overview
  - `compare_library_security` - Compare multiple libraries
  - `suggest_secure_libraries` - Enhanced suggestions with security scores
- Support for multiple ecosystems (PyPI, npm, Maven, Go)
- Auto-approve configuration for sensitive libraries

## [1.0.0] - 2025-06-25

### Initial Release
- Support for 99 popular development libraries
- Basic documentation search and retrieval
- Library suggestions with fuzzy matching
- Health check for documentation sources
- Simple caching system
- AWS MCP-style deployment via uvx 