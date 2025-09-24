"""
Environment-aware configuration manager for documentation-search-enhanced MCP server.
Supports development, staging, and production environments with different settings.
"""

import json
import os
from typing import Dict, Any, Optional
from importlib import resources
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment"""

    logging_level: str = "INFO"
    cache_ttl_hours: float = 24
    cache_max_entries: int = 1000
    rate_limit_enabled: bool = True
    requests_per_minute: int = 60
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    features: Optional[Dict[str, bool]] = None

    def __post_init__(self):
        if self.features is None:
            self.features = {
                "caching_enabled": True,
                "real_time_search": True,
                "github_integration": True,
                "rate_limiting": self.rate_limit_enabled,
                "analytics": True,
            }


class ConfigManager:
    """Manages environment-specific configurations"""

    def __init__(self):
        self.environment = self._detect_environment()
        self.base_config = self._load_base_config()
        self.env_config = self._get_environment_config()

    def _detect_environment(self) -> str:
        """Detect current environment from environment variables"""
        env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()

        # Common environment name mappings
        env_mappings = {
            "dev": "development",
            "develop": "development",
            "development": "development",
            "stage": "staging",
            "staging": "staging",
            "prod": "production",
            "production": "production",
            "test": "testing",
            "testing": "testing",
        }

        return env_mappings.get(env, "development")

    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration from config.json"""
        try:
            # Try to load from package resources first (for installed package)
            try:
                config_text = resources.read_text(
                    "documentation_search_enhanced", "config.json"
                )
                config = json.loads(config_text)
            except (FileNotFoundError, ModuleNotFoundError):
                # Fallback to relative path (for development)
                config_path = os.path.join(os.path.dirname(__file__), "config.json")
                with open(config_path, "r") as f:
                    config = json.load(f)
        except Exception:
            # Final fallback - return minimal config
            config = {"docs_urls": {}, "cache": {"enabled": True}}

        return config

    def _get_environment_config(self) -> EnvironmentConfig:
        """Get configuration for current environment"""
        environments = {
            "development": EnvironmentConfig(
                logging_level="DEBUG",
                cache_ttl_hours=1,
                cache_max_entries=100,
                rate_limit_enabled=False,
                requests_per_minute=120,
                max_concurrent_requests=20,
                request_timeout_seconds=60,
                features={
                    "caching_enabled": True,
                    "real_time_search": True,
                    "github_integration": True,
                    "rate_limiting": False,
                    "analytics": True,
                },
            ),
            "testing": EnvironmentConfig(
                logging_level="WARN",
                cache_ttl_hours=0.5,
                cache_max_entries=50,
                rate_limit_enabled=True,
                requests_per_minute=30,
                max_concurrent_requests=5,
                request_timeout_seconds=15,
                features={
                    "caching_enabled": False,
                    "real_time_search": True,
                    "github_integration": False,
                    "rate_limiting": True,
                    "analytics": False,
                },
            ),
            "staging": EnvironmentConfig(
                logging_level="INFO",
                cache_ttl_hours=12,
                cache_max_entries=500,
                rate_limit_enabled=True,
                requests_per_minute=60,
                max_concurrent_requests=10,
                request_timeout_seconds=30,
                features={
                    "caching_enabled": True,
                    "real_time_search": True,
                    "github_integration": True,
                    "rate_limiting": True,
                    "analytics": True,
                },
            ),
            "production": EnvironmentConfig(
                logging_level="ERROR",
                cache_ttl_hours=24,
                cache_max_entries=1000,
                rate_limit_enabled=True,
                requests_per_minute=60,
                max_concurrent_requests=10,
                request_timeout_seconds=30,
                features={
                    "caching_enabled": True,
                    "real_time_search": True,
                    "github_integration": True,
                    "rate_limiting": True,
                    "analytics": True,
                },
            ),
        }

        return environments.get(self.environment, environments["development"])

    def get_config(self) -> Dict[str, Any]:
        """Get merged configuration for current environment"""
        # Start with base config
        merged_config = self.base_config.copy()

        # Override with environment-specific settings
        if "server_config" not in merged_config:
            merged_config["server_config"] = {}

        merged_config["server_config"].update(
            {
                "environment": self.environment,
                "logging_level": self.env_config.logging_level,
                "max_concurrent_requests": self.env_config.max_concurrent_requests,
                "request_timeout_seconds": self.env_config.request_timeout_seconds,
                "features": self.env_config.features,
            }
        )

        if "cache" not in merged_config:
            merged_config["cache"] = {}

        features = self.env_config.features or {}
        merged_config["cache"].update(
            {
                "ttl_hours": self.env_config.cache_ttl_hours,
                "max_entries": self.env_config.cache_max_entries,
                "enabled": features.get("caching_enabled", True),
            }
        )

        if "rate_limiting" not in merged_config:
            merged_config["rate_limiting"] = {}

        merged_config["rate_limiting"].update(
            {
                "enabled": self.env_config.rate_limit_enabled,
                "requests_per_minute": self.env_config.requests_per_minute,
            }
        )

        return merged_config

    def get_docs_urls(self) -> Dict[str, str]:
        """Get documentation URLs with environment filtering"""
        docs_urls = {}
        config = self.get_config()

        for lib_name, lib_data in config.get("docs_urls", {}).items():
            if isinstance(lib_data, dict):
                # Check if library is enabled for this environment
                environments = lib_data.get(
                    "environments", ["development", "staging", "production"]
                )
                if self.environment in environments:
                    docs_urls[lib_name] = lib_data.get("url", "")
            else:
                # Legacy format - always include
                docs_urls[lib_name] = lib_data

        return docs_urls

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled in current environment"""
        features = self.env_config.features or {}
        return features.get(feature_name, False)

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration for current environment"""
        features = self.env_config.features or {}
        return {
            "ttl_hours": self.env_config.cache_ttl_hours,
            "max_entries": self.env_config.cache_max_entries,
            "enabled": features.get("caching_enabled", True),
        }


# Global configuration manager
config_manager = ConfigManager()
