"""
Data models for Netflix OCA Locator.

This module contains Pydantic models representing the various data structures
used throughout the application.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, IPvAnyAddress, field_validator


class PublicIPInfo(BaseModel):
    """
    Public IP information model.

    Parameters
    ----------
    ip : IPvAnyAddress
        The public IP address (IPv4 or IPv6).
    timestamp : datetime
        When the IP was fetched.

    Attributes
    ----------
    ip : IPvAnyAddress
        The public IP address.
    timestamp : datetime
        When the IP was fetched.
    """

    ip: IPvAnyAddress
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ISPInfo(BaseModel):
    """
    ISP information model from WHOIS data.

    Parameters
    ----------
    asn : str
        Autonomous System Number.
    ip : str
        IP address or range.
    bgp_prefix : str
        BGP prefix.
    cc : str
        Country code.
    registry : str
        Regional Internet Registry.
    allocated : Optional[str]
        Allocation date.
    as_name : str
        AS organization name.

    Attributes
    ----------
    asn : str
        Autonomous System Number.
    ip : str
        IP address or range.
    bgp_prefix : str
        BGP prefix.
    cc : str
        Country code.
    registry : str
        Regional Internet Registry.
    allocated : Optional[str]
        Allocation date.
    as_name : str
        AS organization name.
    """

    asn: str = Field(..., description="Autonomous System Number")
    ip: str = Field(..., description="IP address or range")
    bgp_prefix: str = Field(..., description="BGP prefix")
    cc: str = Field(..., description="Country code")
    registry: str = Field(..., description="Regional Internet Registry")
    allocated: str | None = Field(None, description="Allocation date")
    as_name: str = Field(..., description="AS organization name")

    @field_validator("asn")
    @classmethod
    def validate_asn(cls, v: str) -> str:
        """Validate and clean ASN format."""
        # Remove 'AS' prefix if present
        if v.upper().startswith("AS"):
            return v[2:]
        return v


class OCAServer(BaseModel):
    """
    Netflix OCA (Open Connect Appliance) server information.

    Parameters
    ----------
    domain : str
        The OCA server domain name.
    ip_address : IPvAnyAddress
        The resolved IP address of the OCA.
    url : HttpUrl
        The full URL for speed testing.
    city : Optional[str]
        City where the OCA is located (if identifiable).
    iata_code : Optional[str]
        IATA airport code (if identifiable).
    latitude : Optional[float]
        Latitude coordinate.
    longitude : Optional[float]
        Longitude coordinate.
    asn : Optional[str]
        Autonomous System Number for enhanced geocoding.
    geocoding_provider : Optional[str]
        Provider used for geocoding (AS name).
    geolocation_approach : Optional[str]
        Geolocation method used (thealeph, geopy, etc.).

    Attributes
    ----------
    domain : str
        The OCA server domain name.
    ip_address : IPvAnyAddress
        The resolved IP address of the OCA.
    url : HttpUrl
        The full URL for speed testing.
    city : Optional[str]
        City where the OCA is located.
    iata_code : Optional[str]
        IATA airport code.
    latitude : Optional[float]
        Latitude coordinate.
    longitude : Optional[float]
        Longitude coordinate.
    asn : Optional[str]
        Autonomous System Number for enhanced geocoding.
    geocoding_provider : Optional[str]
        Provider used for geocoding (AS name).
    geolocation_approach : Optional[str]
        Geolocation method used.
    """

    domain: str = Field(..., description="OCA server domain")
    ip_address: IPvAnyAddress = Field(..., description="OCA IP address")
    url: HttpUrl = Field(..., description="Speed test URL")
    city: str | None = Field(None, description="City location")
    iata_code: str | None = Field(None, description="IATA airport code")
    latitude: float | None = Field(None, ge=-90, le=90, description="Latitude")
    longitude: float | None = Field(None, ge=-180, le=180, description="Longitude")
    asn: str | None = Field(None, description="Autonomous System Number")
    geocoding_provider: str | None = Field(None, description="Geocoding provider used")
    geolocation_approach: str | None = Field(None, description="Geolocation method used")

    @field_validator("iata_code")
    @classmethod
    def validate_iata_code(cls, v: str | None) -> str | None:
        """Validate IATA code format."""
        if v is not None:
            v = v.upper()
            if len(v) != 3 or not v.isalpha():
                raise ValueError("IATA code must be exactly 3 letters")
        return v


class OCALocatorResult(BaseModel):
    """
    Complete result from OCA location process.

    Parameters
    ----------
    public_ip : PublicIPInfo
        Public IP information.
    isp_info : ISPInfo
        ISP information.
    oca_servers : list[OCAServer]
        List of allocated OCA servers.
    query_time : datetime
        When the query was performed.
    fast_com_token : str
        Token used for the query.

    Attributes
    ----------
    public_ip : PublicIPInfo
        Public IP information.
    isp_info : ISPInfo
        ISP information.
    oca_servers : list[OCAServer]
        List of allocated OCA servers.
    query_time : datetime
        When the query was performed.
    fast_com_token : str
        Token used for the query.
    """

    public_ip: PublicIPInfo
    isp_info: ISPInfo
    oca_servers: list[OCAServer]
    query_time: datetime = Field(default_factory=datetime.utcnow)
    fast_com_token: str = Field(..., description="Fast.com API token")


class ExportFormat(BaseModel):
    """
    Export format configuration.

    Parameters
    ----------
    format : str
        Export format type (json, csv, xlsx).
    include_headers : bool
        Whether to include headers in export.
    prettify : bool
        Whether to prettify the output.

    Attributes
    ----------
    format : str
        Export format type.
    include_headers : bool
        Whether to include headers.
    prettify : bool
        Whether to prettify output.
    """

    format: str = Field(..., pattern="^(json|csv|xlsx|markdown)$")
    include_headers: bool = Field(default=True)
    prettify: bool = Field(default=True)
