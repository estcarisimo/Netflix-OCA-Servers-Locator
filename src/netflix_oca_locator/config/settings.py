"""
Application configuration settings.

This module manages application settings using pydantic-settings,
supporting environment variables and configuration files.
"""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Parameters
    ----------
    app_name : str
        Application name.
    version : str
        Application version.
    debug : bool
        Enable debug mode.
    log_level : str
        Logging level.
    log_file : Optional[str]
        Log file path.
    ipify_api_url : str
        IPify API URL for public IP lookup.
    cymru_whois_host : str
        Cymru WHOIS server hostname.
    fast_com_url : str
        Fast.com website URL.
    fast_com_js_pattern : str
        Pattern to find JS file URL.
    fast_com_api_url : str
        Fast.com API endpoint.
    token_pattern : str
        Regex pattern to extract token.
    request_timeout : int
        HTTP request timeout in seconds.
    max_retries : int
        Maximum retry attempts for API calls.
    cache_ttl : int
        Cache time-to-live in seconds.
    export_path : str
        Default export directory.
    map_zoom : int
        Default map zoom level.
    show_emoji : bool
        Enable emoji in output.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NETFLIX_OCA_",
        case_sensitive=False,
    )

    # Application settings
    app_name: str = Field(default="Netflix OCA Locator", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    log_file: Optional[str] = Field(default=None, description="Log file path")

    # API URLs
    ipify_api_url: str = Field(
        default="https://api.ipify.org?format=json", description="IPify API URL"
    )
    cymru_whois_host: str = Field(
        default="whois.cymru.com", description="Cymru WHOIS server"
    )
    fast_com_url: str = Field(default="https://fast.com", description="Fast.com URL")
    fast_com_js_pattern: str = Field(
        default=r'<script src="(/app-[a-f0-9]+\.js)"', description="JS file pattern"
    )
    fast_com_api_url: str = Field(
        default="https://api.fast.com/netflix/speedtest/v2",
        description="Fast.com API endpoint",
    )
    token_pattern: str = Field(
        default=r'token:\s*"([^"]+)"', description="Token extraction pattern"
    )

    # Request settings
    request_timeout: int = Field(
        default=30, ge=5, le=300, description="Request timeout in seconds"
    )
    max_retries: int = Field(default=3, ge=1, le=10, description="Max retry attempts")

    # Cache settings
    cache_ttl: int = Field(default=3600, ge=60, description="Cache TTL in seconds")

    # Export settings
    export_path: str = Field(default="./exports", description="Export directory")

    # Map settings
    map_zoom: int = Field(default=4, ge=1, le=18, description="Default map zoom")

    # UI settings
    show_emoji: bool = Field(default=True, description="Show emoji in output")

    # Geocoding settings
    geocoding_provider: str = Field(
        default="hybrid", 
        description="Geocoding provider (aleph, geopy, hybrid)",
        pattern="^(aleph|geopy|hybrid)$"
    )
    aleph_api_url: str = Field(
        default="https://thealeph.ai/api/query", 
        description="TheAleph API endpoint"
    )
    aleph_ssl_verify: bool = Field(
        default=False, 
        description="Verify SSL for TheAleph API (disabled due to cert issues)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase."""
        return v.upper()


def get_settings() -> Settings:
    """
    Get application settings instance.

    Returns
    -------
    Settings
        Application settings.
    """
    return Settings()
