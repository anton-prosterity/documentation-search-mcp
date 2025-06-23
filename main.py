import json
import os
import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
#Load the environment variables
load_dotenv()

#Initialize the MCP server
mcp = FastMCP("docs")
USER_AGENT = "docs-app/1.0"
SERPER_URL = "https://google.serper.dev/search"


# TO DO: Add the API key to the .env file
#SERPER_API_KEY = "58faeeabd62e9f1c27503de7e47fea14767775e3"

SERPER_API_KEY = os.getenv("SERPER_API_KEY")



# Load configuration from external file
def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    return config["docs_urls"]

# Load docs URLs from configuration
docs_urls = load_config()






async def search_web(query: str) -> dict | None:
    payload = json.dumps({"q": query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}
        
        
        
    
async def fetch_url(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            return text
        except httpx.TimeoutException:
            return "Timeout error"
    
        

@mcp.tool()
async def get_docs(query: str, library: str):
    f"""
    Search the latest docs for a given query and library.
    Supports: {', '.join(sorted(docs_urls.keys()))}

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs
    """
    
    if library not in docs_urls:
        raise ValueError(f"Library {library} not supported by this tool")
    query = f"site:{docs_urls[library]} {query}"
    results = await search_web(query)
    if len(results["organic"]) == 0:
        return "No results found"
    
    text = ""
    for result in results["organic"]:
        text += await fetch_url(result["link"])
    return text
    



if __name__ == "__main__":
    mcp.run(transport="stdio")
    
