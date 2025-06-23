#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import get_docs

async def test_simple():
    """Test with a very simple, short query"""
    
    print("=== Testing simple query ==")
    try:
        result = await get_docs("hello world", "python")
        print(f"Result length: {len(result)}")
        print(f"First 200 chars: {result[:200]}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_simple())
    if result and len(result) < 1000:
        print(f"\n=== SHORT RESULT (can test with MCP) ===")
        print(result)
    else:
        print(f"Result too long or failed: {len(result) if result else 'None'}") 