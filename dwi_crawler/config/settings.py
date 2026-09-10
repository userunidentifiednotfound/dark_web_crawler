"""Centralized settings and configuration for the DWI Dark Web Crawler."""

import os
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    dwi_database_url: str = Field(
        default="sqlite+aiosqlite:///./dwi_crawler.db",
        alias="DWI_DATABASE_URL",
        description="SQLAlchemy database connection URL"
    )
    sync_database_url: str = Field(
        default="sqlite:///./dwi_crawler.db",
        alias="SYNC_DATABASE_URL"
    )

    @property
    def database_url(self) -> str:
        return self.dwi_database_url

    # Redis Queue
    redis_url: str = Field(
        default="redis://127.0.0.1:6379/0",
        alias="REDIS_URL"
    )

    # Tor / Proxy Configuration
    tor_proxy_host: str = Field(default="127.0.0.1", alias="TOR_PROXY_HOST")
    tor_proxy_port: int = Field(default=9050, alias="TOR_PROXY_PORT")
    tor_proxy_type: str = Field(default="socks5", alias="TOR_PROXY_TYPE")  # socks5 or http
    use_proxy_for_onion: bool = Field(default=True, alias="USE_PROXY_FOR_ONION")
    use_proxy_for_surface: bool = Field(default=False, alias="USE_PROXY_FOR_SURFACE")

    # Concurrency Settings
    max_global_concurrency: int = Field(default=10, alias="MAX_GLOBAL_CONCURRENCY")
    max_per_host_concurrency: int = Field(default=1, alias="MAX_PER_HOST_CONCURRENCY")
    max_browser_workers: int = Field(default=2, alias="MAX_BROWSER_WORKERS")
    search_concurrency: int = Field(default=3, alias="SEARCH_CONCURRENCY")

    # Crawl Depth & Limits
    max_depth: int = Field(default=2, alias="MAX_DEPTH")
    request_timeout: float = Field(default=30.0, alias="REQUEST_TIMEOUT")
    connect_timeout: float = Field(default=15.0, alias="CONNECT_TIMEOUT")
    page_process_timeout: float = Field(default=60.0, alias="PAGE_PROCESS_TIMEOUT")
    max_response_bytes: int = Field(default=10 * 1024 * 1024, alias="MAX_RESPONSE_BYTES")  # 10 MB limit
    max_redirects: int = Field(default=5, alias="MAX_REDIRECTS")

    # Search Limits (3 surface, 7 onion per enhanced keyword)
    search_surface_limit: int = Field(default=3, alias="SEARCH_SURFACE_LIMIT")
    search_onion_limit: int = Field(default=7, alias="SEARCH_ONION_LIMIT")

    # Storage Paths
    storage_path: Path = Field(default=Path("./storage"), alias="STORAGE_PATH")

    # Scope Policy
    scope_policy: Literal["ONION_ONLY", "COMPANY_DOMAINS", "EXPLICIT_ALLOWLIST"] = Field(
        default="ONION_ONLY",
        alias="SCOPE_POLICY"
    )

    # Context radius for keyword match evidence
    context_radius: int = Field(default=150, alias="CONTEXT_RADIUS")

    # Retry Policy
    max_retries: int = Field(default=4, alias="MAX_RETRIES")
    retry_backoff_base: float = Field(default=3.0, alias="RETRY_BACKOFF_BASE")

    # Observability
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # DWI Core API Integration
    dwi_api_url: str = Field(default="http://localhost:8000/api/v1", alias="DWI_API_URL")
    dwi_api_key: str = Field(default="", alias="DWI_API_KEY")

    def get_proxy_url(self) -> str:
        """Returns the full proxy connection URL."""
        return f"{self.tor_proxy_type}://{self.tor_proxy_host}:{self.tor_proxy_port}"


# Lazy singleton to ensure fast import time
_settings_instance: Settings | None = None


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
