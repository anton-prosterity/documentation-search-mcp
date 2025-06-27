#!/usr/bin/env python3
"""
A simple and efficient rate limiter for the MCP server.
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Deque

class RateLimiter:
    """
    A sliding window rate limiter to control the frequency of requests.
    This implementation is for a single-process server. For multi-process
    or distributed systems, a solution like Redis would be required.
    """
    def __init__(self, requests: int, per_seconds: int):
        if requests <= 0 or per_seconds <= 0:
            raise ValueError("Requests and per_seconds must be positive.")
        self.requests = requests
        self.window = timedelta(seconds=per_seconds)
        self.history: Dict[str, Deque[datetime]] = {}

    def is_allowed(self, identifier: str = "default") -> bool:
        """
        Checks if a request from the given identifier is allowed.

        Args:
            identifier: A unique identifier for the user/client.

        Returns:
            True if the request is allowed, False otherwise.
        """
        now = datetime.now()
        
        # Get or create the request history for this identifier
        if identifier not in self.history:
            self.history[identifier] = deque()
            
        request_times = self.history[identifier]

        # Remove timestamps that are outside the current window
        while request_times and request_times[0] < now - self.window:
            request_times.popleft()

        # Check if the number of requests exceeds the limit
        if len(request_times) < self.requests:
            request_times.append(now)
            return True
        else:
            return False

# --- Global Rate Limiter Instance ---
# This can be configured and instantiated from main.py based on config.json
# For now, we define a placeholder.
# Example: limiter = RateLimiter(requests=60, per_seconds=60)
limiter = None 