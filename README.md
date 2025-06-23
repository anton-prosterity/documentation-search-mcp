# Documentation Search MCP Server

A Model Context Protocol (MCP) server that provides intelligent documentation search capabilities across multiple programming libraries and frameworks.

## Features

- **Multi-library support**: Search documentation for 30+ popular libraries and frameworks
- **External configuration**: Easily add new documentation sources without code changes
- **Web search integration**: Uses Serper API for targeted documentation searches
- **Content extraction**: Fetches and parses documentation content from official sources

## Supported Libraries

The server currently supports documentation search for:

- **Programming Languages**: Python, JavaScript, SQL
- **Web Frameworks**: React, Node.js, Express, Django, Flask, FastAPI
- **Databases**: MongoDB, SQLAlchemy, PostgreSQL
- **AI/ML**: OpenAI, Anthropic, LangChain, LlamaIndex, LangGraph
- **Cloud & DevOps**: AWS, Kubernetes, Docker, Terraform, Ansible
- **Data Science**: Pandas, NumPy, Matplotlib
- **Development Tools**: Git, Streamlit, Supabase, Firebase, Vercel

And many more! See `config.json` for the complete list.

## Setup

### Prerequisites

- Python 3.8+
- UV package manager (recommended) or pip

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd documentation
```

2. Install dependencies:
```bash
uv sync
```

3. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env and add your SERPER_API_KEY
```

4. Get a Serper API key:
   - Visit [serper.dev](https://serper.dev)
   - Sign up for a free account
   - Copy your API key to the `.env` file

## Configuration

### Adding New Documentation Sources

To add support for new libraries, simply edit the `config.json` file:

```json
{
    "docs_urls": {
        "existing_library": "https://existing-docs.com",
        "new_library": "https://new-library-docs.com/api/"
    }
}
```

The server will automatically pick up changes to this file on restart. No code modifications required!

### Configuration Structure

The `config.json` file contains a single `docs_urls` object where:
- **Key**: Library/framework name (used in search queries)
- **Value**: Base URL of the official documentation

## Usage

### Running the Server

```bash
python main.py
```

The server runs using the stdio transport protocol for MCP communication.

### Integration with AI Tools

#### Adding to Cursor

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Navigate to "Features" → "Model Context Protocol"
3. Add a new MCP server configuration:

```json
{
  "name": "documentation-search",
  "command": "python",
  "args": ["/path/to/your/documentation/main.py"],
  "env": {
    "SERPER_API_KEY": "your_api_key_here"
  }
}
```

4. Replace `/path/to/your/documentation/main.py` with the absolute path to your main.py file
5. Save the configuration and restart Cursor

#### Adding to Claude Desktop

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the MCP server configuration:

```json
{
  "mcpServers": {
    "documentation-search": {
      "command": "python",
      "args": ["/path/to/your/documentation/main.py"],
      "env": {
        "SERPER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. Replace `/path/to/your/documentation/main.py` with the absolute path to your main.py file
4. Restart Claude Desktop

#### Using Virtual Environments

If you're using a virtual environment (recommended), use the full path to the Python executable:

**For UV:**
```json
{
  "command": "/path/to/your/documentation/.venv/bin/python",
  "args": ["/path/to/your/documentation/main.py"]
}
```

**For Conda:**
```json
{
  "command": "/path/to/conda/envs/your-env/bin/python",
  "args": ["/path/to/your/documentation/main.py"]
}
```

### Using the Tool

The server provides a single tool: `get_docs`

**Parameters:**
- `query` (string): Your search query (e.g., "authentication", "database connection")
- `library` (string): The library to search in (e.g., "fastapi", "react", "python")

**Example:**
```python
# Search for authentication info in FastAPI docs
get_docs(query="authentication middleware", library="fastapi")
```

## Project Structure

```
documentation/
├── main.py           # Main MCP server implementation
├── config.json       # External configuration for documentation URLs
├── pyproject.toml    # Project dependencies and metadata
├── uv.lock          # Lock file for reproducible builds
├── .env             # Environment variables (API keys)
├── .gitignore       # Git ignore patterns
└── README.md        # This file
```

## How It Works

1. **Query Processing**: Takes your search query and target library
2. **Site-specific Search**: Uses Serper API to search within the specific documentation site
3. **Content Extraction**: Fetches the actual documentation pages
4. **Text Parsing**: Extracts clean text content using BeautifulSoup
5. **Response**: Returns the relevant documentation content

## API Dependencies

- **Serper API**: For web search functionality
- **FastMCP**: MCP server framework
- **httpx**: Async HTTP client
- **BeautifulSoup4**: HTML parsing and text extraction

## Environment Variables

Create a `.env` file with:

```env
SERPER_API_KEY=your_serper_api_key_here
```

## Contributing

To add support for new libraries:

1. Add the library and its documentation URL to `config.json`
2. Test that the documentation site returns useful content
3. Submit a pull request

## Troubleshooting

### Common Issues

- **"Library not supported"**: Check that the library name matches an entry in `config.json`
- **"No results found"**: The search query might be too specific, or the documentation site might not be indexed well
- **Timeout errors**: Some documentation sites may be slow to respond; this is handled gracefully

### AI Tool Integration Issues

- **Tool not appearing**: Ensure the absolute paths are correct and the Python environment has all dependencies installed
- **Permission errors**: Make sure the Python executable and main.py file have proper permissions
- **Environment variables**: Verify that `SERPER_API_KEY` is correctly set in the MCP configuration, not just your shell environment
- **Virtual environment**: Double-check you're using the correct Python path from your virtual environment

### Debugging

The server includes error handling for:
- Network timeouts
- Invalid library names  
- Empty search results
- Malformed configuration files

## License

This project is open source. See LICENSE file for details.
# documentation-mcp
# documentation-mcp
# documentation-mcp
