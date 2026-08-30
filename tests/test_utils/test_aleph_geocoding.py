"""Tests for TheAleph geocoding service."""

from unittest.mock import AsyncMock, call

import httpx
import pytest

from netflix_oca_locator.config.settings import Settings
from netflix_oca_locator.utils.aleph_geocoding import AlephGeocodeService, HybridGeocodeService


class TestAlephGeocodeService:
    """Tests for AlephGeocodeService."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            debug=True,
            log_level="DEBUG",
            request_timeout=10,
            geocoding_provider="aleph",
        )

    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        return AsyncMock(spec=httpx.AsyncClient)

    @pytest.fixture
    def aleph_service(self, settings, mock_client):
        """Create AlephGeocodeService instance."""
        return AlephGeocodeService(settings, mock_client)

    def test_init(self, settings):
        """Test service initialization."""
        service = AlephGeocodeService(settings)
        assert service.settings == settings
        assert service.client is not None

    @pytest.mark.asyncio
    async def test_resolve_domain_location_success(
        self, aleph_service, mock_client, mock_httpx_response
    ):
        """Test successful domain location resolution."""
        # httpx.Response.json()/raise_for_status() are synchronous, so the response
        # must be a MagicMock; only the client's post() is awaited.
        mock_response = mock_httpx_response
        # Payload shape matches the real TheAleph API response documented on
        # AlephGeocodeService._parse_aleph_response.
        mock_response.json.return_value = {
            "ptr_record": "lax1.nflxvideo.net",
            "asn": 2906,
            "location_info": {
                "city": "Los Angeles",
                "state": "CA",
                "region": "",
                "country": "US",
                "latitude": 34.0522,
                "longitude": -118.2437,
            },
            "geo_hint": "lax",
            "ip": "198.45.48.1",
        }
        mock_client.post.return_value = mock_response

        # Test resolution
        result = await aleph_service.resolve_domain_location("lax1.nflxvideo.net", "64512")

        # Verify result
        assert result is not None
        assert result["latitude"] == 34.0522
        assert result["longitude"] == -118.2437
        assert result["city"] == "Los Angeles, CA"
        assert result["iata_code"] == "LAX"
        assert result["provider"] == "thealeph"

    @pytest.mark.asyncio
    async def test_resolve_domain_location_timeout(self, aleph_service, mock_client):
        """Test timeout handling."""
        mock_client.post.side_effect = httpx.TimeoutException("Request timeout")

        result = await aleph_service.resolve_domain_location("test.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_domain_location_request_error(self, aleph_service, mock_client):
        """Test request error handling."""
        mock_client.post.side_effect = httpx.RequestError("Connection failed")

        result = await aleph_service.resolve_domain_location("test.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_ip_location(self, aleph_service, mock_client, mock_httpx_response):
        """Test IP location resolution."""
        mock_response = mock_httpx_response
        mock_response.json.return_value = {
            "ptr_record": "dns.google",
            "asn": 15169,
            "location_info": {
                "city": "San Francisco",
                "state": "CA",
                "region": "",
                "country": "US",
                "latitude": 37.7749,
                "longitude": -122.4194,
            },
            "geo_hint": "sfo",
            "ip": "8.8.8.8",
        }
        mock_client.post.return_value = mock_response

        result = await aleph_service.resolve_ip_location("8.8.8.8")

        assert result is not None
        assert result["latitude"] == 37.7749
        assert result["longitude"] == -122.4194
        assert result["city"] == "San Francisco, CA"
        assert result["provider"] == "thealeph"

    def test_extract_iata_from_string(self, aleph_service):
        """Test IATA code extraction from strings."""
        # Test various patterns
        assert aleph_service._extract_iata_from_string("lax1.example.com") == "LAX"
        assert aleph_service._extract_iata_from_string("example-ord-1.com") == "ORD"
        assert aleph_service._extract_iata_from_string("example.iad.com") == "IAD"
        assert aleph_service._extract_iata_from_string("no-iata-here.com") is None
        assert aleph_service._extract_iata_from_string("123.example.com") is None


class TestHybridGeocodeService:
    """Tests for HybridGeocodeService."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            debug=True,
            geocoding_provider="hybrid",
        )

    @pytest.fixture
    def mock_aleph_service(self):
        """Create mock AlephGeocodeService."""
        return AsyncMock()

    @pytest.fixture
    def mock_geopy_service(self):
        """Create mock GeocodeService."""
        return AsyncMock()

    @pytest.fixture
    def hybrid_service(self, settings, mock_aleph_service, mock_geopy_service):
        """Create HybridGeocodeService instance."""
        return HybridGeocodeService(settings, mock_aleph_service, mock_geopy_service)

    @pytest.mark.asyncio
    async def test_extract_location_aleph_success(
        self, hybrid_service, mock_aleph_service, mock_geopy_service
    ):
        """Test successful location extraction using TheAleph."""
        aleph_result = {
            "latitude": 34.0522,
            "longitude": -118.2437,
            "city": "Los Angeles",
            "iata_code": "LAX",
        }
        mock_aleph_service.resolve_domain_location.return_value = aleph_result

        result = await hybrid_service.extract_location_from_domain("lax1.nflxvideo.net", "64512")

        assert result == aleph_result
        mock_aleph_service.resolve_domain_location.assert_called_once()
        mock_geopy_service.extract_location_from_domain.assert_not_called()

    @pytest.mark.asyncio
    async def test_extract_location_geopy_fallback(
        self, hybrid_service, mock_aleph_service, mock_geopy_service
    ):
        """Test fallback to geopy when TheAleph fails."""
        mock_aleph_service.resolve_domain_location.return_value = None
        geopy_result = {
            "latitude": 34.0522,
            "longitude": -118.2437,
            "city": "Los Angeles",
            "iata_code": "LAX",
        }
        mock_geopy_service.extract_location_from_domain.return_value = geopy_result

        result = await hybrid_service.extract_location_from_domain("lax1.nflxvideo.net", "64512")

        assert result["provider"] == "geopy_fallback"
        # TheAleph is tried twice: once with the caller's ASN, then once more with
        # Netflix's own ASN 2906, before geopy is used as the final fallback.
        assert mock_aleph_service.resolve_domain_location.call_args_list == [
            call("lax1.nflxvideo.net", "64512", None),
            call("lax1.nflxvideo.net", "2906", None),
        ]
        mock_geopy_service.extract_location_from_domain.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_location_both_fail(
        self, hybrid_service, mock_aleph_service, mock_geopy_service
    ):
        """Test when both services fail."""
        mock_aleph_service.resolve_domain_location.return_value = None
        mock_geopy_service.extract_location_from_domain.return_value = None

        result = await hybrid_service.extract_location_from_domain("unknown.com")

        assert result is None

    def test_is_good_result(self, hybrid_service):
        """Test result quality evaluation."""
        # Good result with coordinates
        good_coords = {"latitude": 34.0, "longitude": -118.0}
        assert hybrid_service._is_good_result(good_coords) is True

        # Good result with city and IATA
        good_city_iata = {"city": "Los Angeles", "iata_code": "LAX"}
        assert hybrid_service._is_good_result(good_city_iata) is True

        # Poor result
        poor_result = {"city": "Unknown"}
        assert hybrid_service._is_good_result(poor_result) is False

        # Empty result
        empty_result = {}
        assert hybrid_service._is_good_result(empty_result) is False
