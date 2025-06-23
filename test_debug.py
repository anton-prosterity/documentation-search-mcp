#!/usr/bin/env python3

import asyncio
import os
import sys
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import get_docs, docs_urls

async def test_get_docs():
    """Test the get_docs function directly"""
    
    print("=== Testing get_docs function ===")
    print(f"Available libraries: {list(docs_urls.keys())[:5]}...")  # Show first 5
    print(f"FastAPI URL: {docs_urls.get('fastapi', 'NOT FOUND')}")
    print(f"SERPER_API_KEY set: {'Yes' if os.getenv('SERPER_API_KEY') else 'No'}")
    
    try:
        print("\n=== Testing FastAPI authentication search ===")
        result = await get_docs("authentication examples", "fastapi")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(str(result))}")
        print(f"First 500 chars: {str(result)[:500]}...")
        return result
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_get_docs())
    
    if result:
        print("\n=== SUCCESS: Function returned results ===")
    else:
        print("\n=== FAILURE: No results returned ===") 