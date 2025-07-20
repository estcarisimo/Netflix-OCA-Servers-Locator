"""Pytest configuration and fixtures."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from netflix_oca_locator.config.settings import Settings
from netflix_oca_locator.core.models import (
    ISPInfo,
    OCALocatorResult,
    OCAServer,
    PublicIPInfo,
)


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        debug=True,
        log_level="DEBUG",
        request_timeout=10,
        max_retries=1,
        cache_ttl=60,
    )


@pytest.fixture
def mock_public_ip():
    """Mock public IP info."""
    return PublicIPInfo(ip="203.0.113.1")


@pytest.fixture
def mock_isp_info():
    """Mock ISP information."""
    return ISPInfo(
        asn="64512",
        ip="203.0.113.0/24",
        bgp_prefix="203.0.113.0/24",
        cc="US",
        registry="ARIN",
        allocated="2023-01-01",
        as_name="Test ISP",
    )


@pytest.fixture
def mock_oca_servers():
    """Mock OCA servers."""
    return [
        OCAServer(
            domain="lax1.nflxvideo.net",
            ip_address="198.45.48.1",
            url="https://lax1.nflxvideo.net/speedtest",
            city="Los Angeles, CA",
            iata_code="LAX",
            latitude=34.0522,
            longitude=-118.2437,
        ),
        OCAServer(
            domain="ord1.nflxvideo.net",
            ip_address="198.45.48.2",
            url="https://ord1.nflxvideo.net/speedtest",
            city="Chicago, IL",
            iata_code="ORD",
            latitude=41.9742,
            longitude=-87.9073,
        ),
    ]


@pytest.fixture
def mock_oca_result(mock_public_ip, mock_isp_info, mock_oca_servers):
    """Mock complete OCA result."""
    return OCALocatorResult(
        public_ip=mock_public_ip,
        isp_info=mock_isp_info,
        oca_servers=mock_oca_servers,
        fast_com_token="test_token_123",
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.raise_for_status.return_value = None
    return response


@pytest.fixture
def temp_export_dir(tmp_path):
    """Create temporary export directory."""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return export_dir


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
