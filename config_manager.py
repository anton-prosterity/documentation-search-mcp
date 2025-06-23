#!/usr/bin/env python3
"""
Unified Configuration Manager
Single source of truth for all MCP server configurations
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config = None
        self._docs_urls = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load and cache configuration"""
        if self._config is None:
            with open(self.config_file, "r") as f:
                self._config = json.load(f)
        return self._config
    
    def get_docs_urls(self) -> Dict[str, str]:
        """Get simple URL mapping for documentation search"""
        if self._docs_urls is None:
            config = self.load_config()
            self._docs_urls = {}
            
            for lib_name, lib_data in config["docs_urls"].items():
                if isinstance(lib_data, dict):
                    self._docs_urls[lib_name] = lib_data.get("url", "")
                else:
                    self._docs_urls[lib_name] = lib_data
        
        return self._docs_urls
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get full configuration with popularity data"""
        return self.load_config()
    
    def get_library_data(self, library_name: str) -> Optional[Dict[str, Any]]:
        """Get full data for a specific library"""
        config = self.load_config()
        return config["docs_urls"].get(library_name)
    
    def get_libraries_by_category(self, category: str) -> Dict[str, Any]:
        """Get all libraries in a specific category"""
        config = self.load_config()
        libraries = {}
        
        for lib_name, lib_data in config["docs_urls"].items():
            if isinstance(lib_data, dict) and lib_data.get("category") == category:
                libraries[lib_name] = lib_data
        
        return libraries
    
    def get_popularity_weights(self) -> Dict[str, float]:
        """Get popularity scoring weights"""
        config = self.load_config()
        return config.get("popularity_weights", {
            "github_stars": 0.3,
            "community_size": 0.2,
            "job_market": 0.25,
            "maturity": 0.15,
            "trending": 0.1
        })
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration"""
        config = self.load_config()
        return config.get("cache", {
            "enabled": True,
            "ttl_hours": 24,
            "max_entries": 1000
        })
    
    def reload_config(self):
        """Force reload configuration from disk"""
        self._config = None
        self._docs_urls = None

# Global instance
config_manager = ConfigManager()

# Convenience functions for backward compatibility
def load_config():
    """Load configuration (backward compatibility)"""
    return config_manager.get_full_config()

def get_docs_urls():
    """Get docs URLs (backward compatibility)"""
    return config_manager.get_docs_urls()

def load_enhanced_config():
    """Load enhanced config (backward compatibility)"""
    return config_manager.get_full_config()

if __name__ == "__main__":
    # Test the configuration manager
    cm = ConfigManager()
    
    print("🔧 Configuration Manager Test")
    print(f"📚 Libraries: {len(cm.get_docs_urls())}")
    print(f"🏷️ Categories: {list(cm.get_full_config().get('categories', {}).keys())}")
    print(f"⚙️ Cache enabled: {cm.get_cache_config()['enabled']}")
    print("✅ Configuration manager working perfectly!") 