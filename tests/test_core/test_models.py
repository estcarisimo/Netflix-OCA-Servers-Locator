"""Tests for core models."""

from datetime import datetime
from ipaddress import IPv4Address

import pytest
from pydantic import ValidationError

from netflix_oca_locator.core.models import (
    ExportFormat,
    ISPInfo,
    OCAServer,
    PublicIPInfo,
)


class TestPublicIPInfo:
    """Tests for PublicIPInfo model."""

    def test_valid_ipv4(self):
        """Test valid IPv4 address."""
        ip_info = PublicIPInfo(ip="192.168.1.1")
        assert isinstance(ip_info.ip, IPv4Address)
        assert str(ip_info.ip) == "192.168.1.1"

    def test_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated."""
        ip_info = PublicIPInfo(ip="192.168.1.1")
        assert isinstance(ip_info.timestamp, datetime)

    def test_invalid_ip(self):
        """Test invalid IP address."""
        with pytest.raises(ValidationError):
            PublicIPInfo(ip="invalid_ip")


class TestISPInfo:
    """Tests for ISPInfo model."""

    def test_valid_isp_info(self):
        """Test valid ISP information."""
        isp = ISPInfo(
            asn="1234",
            ip="192.168.1.0/24",
            bgp_prefix="192.168.0.0/16",
            cc="US",
            registry="ARIN",
            as_name="Test ISP",
        )
        assert isp.asn == "1234"
        assert isp.as_name == "Test ISP"

    def test_asn_with_prefix(self):
        """Test ASN with AS prefix gets cleaned."""
        isp = ISPInfo(
            asn="AS1234",
            ip="192.168.1.0/24",
            bgp_prefix="192.168.0.0/16",
            cc="US",
            registry="ARIN",
            as_name="Test ISP",
        )
        assert isp.asn == "1234"


class TestOCAServer:
    """Tests for OCAServer model."""

    def test_valid_oca_server(self):
        """Test valid OCA server."""
        oca = OCAServer(
            domain="lax1.nflxvideo.net",
            ip_address="192.168.1.100",
            url="https://lax1.nflxvideo.net/speedtest",
        )
        assert oca.domain == "lax1.nflxvideo.net"
        assert str(oca.ip_address) == "192.168.1.100"

    def test_with_geolocation(self):
        """Test OCA server with geolocation data."""
        oca = OCAServer(
            domain="lax1.nflxvideo.net",
            ip_address="192.168.1.100",
            url="https://lax1.nflxvideo.net/speedtest",
            city="Los Angeles, CA",
            iata_code="LAX",
            latitude=34.0522,
            longitude=-118.2437,
        )
        assert oca.city == "Los Angeles, CA"
        assert oca.iata_code == "LAX"
        assert oca.latitude == 34.0522

    def test_invalid_iata_code(self):
        """Test invalid IATA code."""
        with pytest.raises(ValidationError):
            OCAServer(
                domain="test.com",
                ip_address="192.168.1.1",
                url="https://test.com",
                iata_code="INVALID",  # Too long
            )

    def test_invalid_coordinates(self):
        """Test invalid coordinates."""
        with pytest.raises(ValidationError):
            OCAServer(
                domain="test.com",
                ip_address="192.168.1.1",
                url="https://test.com",
                latitude=91.0,  # Invalid latitude
            )


class TestExportFormat:
    """Tests for ExportFormat model."""

    def test_valid_formats(self):
        """Test valid export formats."""
        for fmt in ["json", "csv", "xlsx", "markdown"]:
            export = ExportFormat(format=fmt)
            assert export.format == fmt

    def test_invalid_format(self):
        """Test invalid export format."""
        with pytest.raises(ValidationError):
            ExportFormat(format="invalid")

    def test_default_values(self):
        """Test default values."""
        export = ExportFormat(format="json")
        assert export.include_headers is True
        assert export.prettify is True
