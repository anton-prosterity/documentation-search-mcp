#!/usr/bin/env python3
"""
Pydantic models for validating the config.json file.
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Dict, List, Optional


class AutoApproveConfig(BaseModel):
    get_docs: bool = True
    suggest_libraries: bool = True
    health_check: bool = True
    get_cache_stats: bool = True
    clear_cache: bool = False


class FeatureConfig(BaseModel):
    caching_enabled: bool = True
    real_time_search: bool = True
    github_integration: bool = True
    rate_limiting: bool = True
    analytics: bool = True


class ServerConfig(BaseModel):
    name: str = "documentation-search-enhanced"
    version: Optional[str] = None
    logging_level: str = "INFO"
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 30
    auto_approve: AutoApproveConfig = Field(default_factory=AutoApproveConfig)
    features: FeatureConfig = Field(default_factory=FeatureConfig)


class CacheConfig(BaseModel):
    ttl_hours: int = 24
    max_entries: int = 1000
    enabled: bool = True
    persistence_enabled: bool = False
    cleanup_interval_minutes: int = 60
    persist_path: Optional[str] = None


class RateLimitingConfig(BaseModel):
    enabled: bool = True
    requests_per_minute: int = 60
    burst_requests: int = 10


class DocsURL(BaseModel):
    url: HttpUrl
    category: str
    learning_curve: str
    tags: List[str]
    priority: str
    auto_approve: bool


class Config(BaseModel):
    version: str
    server_config: ServerConfig = Field(default_factory=ServerConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limiting: RateLimitingConfig = Field(default_factory=RateLimitingConfig)
    docs_urls: Dict[str, DocsURL]
    categories: Dict[str, List[str]]

    @field_validator("server_config", "cache", "rate_limiting", mode="before")
    @classmethod
    def check_nested_dicts(cls, v):
        return v or {}


def validate_config(data: Dict) -> Config:
    """
    Validates the configuration dictionary against the Pydantic model.
    Raises a ValidationError if the data is invalid.
    """
    return Config.model_validate(data)
