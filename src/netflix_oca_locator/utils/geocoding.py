"""
Geocoding utilities for location extraction and mapping.

This module provides functionality to extract location information
from OCA domain names and geocode them to coordinates.
"""

from __future__ import annotations

import re

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from loguru import logger

from ..config.settings import Settings


class GeocodeService:
    """
    Service for geocoding and location extraction.

    Parameters
    ----------
    settings : Settings
        Application settings.
    geocoder : Optional[Nominatim]
        Geocoding service instance.

    Attributes
    ----------
    settings : Settings
        Application settings.
    geocoder : Nominatim
        Geocoding service.
    iata_patterns : list[re.Pattern]
        Regex patterns for IATA code extraction.
    """

    # IATA code patterns commonly found in CDN domains
    IATA_PATTERNS = [
        re.compile(r"\.([a-z]{3})\d*\."),  # .lax1. or .ord.
        re.compile(r"-([a-z]{3})-"),  # -lax-
        re.compile(r"^([a-z]{3})\d*\."),  # lax1.domain.com
        re.compile(r"\.([a-z]{3})$"),  # domain.lax
    ]

    # Common IATA to city mappings
    IATA_TO_CITY = {
        "lax": ("Los Angeles, CA, USA", 33.9425, -118.4081),
        "ord": ("Chicago, IL, USA", 41.9742, -87.9073),
        "atl": ("Atlanta, GA, USA", 33.6407, -84.4277),
        "dfw": ("Dallas, TX, USA", 32.8998, -97.0403),
        "den": ("Denver, CO, USA", 39.8561, -104.6737),
        "jfk": ("New York, NY, USA", 40.6413, -73.7781),
        "sfo": ("San Francisco, CA, USA", 37.6213, -122.3790),
        "sea": ("Seattle, WA, USA", 47.4502, -122.3088),
        "mia": ("Miami, FL, USA", 25.7959, -80.2870),
        "bos": ("Boston, MA, USA", 42.3656, -71.0096),
        "phx": ("Phoenix, AZ, USA", 33.4352, -112.0101),
        "las": ("Las Vegas, NV, USA", 36.0840, -115.1537),
        "iad": ("Washington, DC, USA", 38.9531, -77.4565),
        "ams": ("Amsterdam, Netherlands", 52.3105, 4.7683),
        "lhr": ("London, UK", 51.4700, -0.4543),
        "cdg": ("Paris, France", 49.0097, 2.5479),
        "fra": ("Frankfurt, Germany", 50.0379, 8.5622),
        "nrt": ("Tokyo, Japan", 35.7720, 140.3929),
        "sin": ("Singapore", 1.3644, 103.9915),
        "syd": ("Sydney, Australia", -33.9399, 151.1753),
        "gru": ("São Paulo, Brazil", -23.4356, -46.4731),
        "mex": ("Mexico City, Mexico", 19.4363, -99.0721),
        "yyz": ("Toronto, Canada", 43.6777, -79.6248),
    }

    def __init__(self, settings: Settings, geocoder: Nominatim | None = None) -> None:
        """Initialize geocode service."""
        self.settings = settings
        self.geocoder = geocoder or Nominatim(
            user_agent=f"{settings.app_name}/{settings.version}"
        )

    async def extract_location_from_domain(
        self, domain: str, asn: str | None = None, ip_address: str | None = None
    ) -> dict[str, str | float | None] | None:
        """
        Extract location information from a domain name.

        Parameters
        ----------
        domain : str
            Domain name to analyze.
        asn : str | None
            Autonomous System Number (not used in this implementation,
            for interface compatibility).
        ip_address : str | None
            IP address (not used in this implementation,
            for interface compatibility).

        Returns
        -------
        Optional[Dict[str, Optional[str | float]]]
            Dictionary with iata_code, city, latitude, longitude.
            Returns None if no location found.
        """
        # Try to extract IATA code
        iata_code = self._extract_iata_code(domain)

        if iata_code:
            # Look up in our database
            if iata_code in self.IATA_TO_CITY:
                city, lat, lon = self.IATA_TO_CITY[iata_code]
                return {
                    "iata_code": iata_code.upper(),
                    "city": city,
                    "latitude": lat,
                    "longitude": lon,
                }

            # Try geocoding the IATA code
            location = await self._geocode_iata(iata_code)
            if location:
                return location

        # Try extracting city name from domain
        city_name = self._extract_city_name(domain)
        if city_name:
            location = await self._geocode_city(city_name)
            if location:
                return location

        return None

    def _extract_iata_code(self, domain: str) -> str | None:
        """
        Extract IATA code from domain name.

        Parameters
        ----------
        domain : str
            Domain name to analyze.

        Returns
        -------
        Optional[str]
            IATA code if found, None otherwise.
        """
        domain_lower = domain.lower()

        for pattern in self.IATA_PATTERNS:
            match = pattern.search(domain_lower)
            if match:
                potential_code = match.group(1)
                # Validate it looks like an IATA code
                if len(potential_code) == 3 and potential_code.isalpha():
                    logger.debug(f"Found potential IATA code: {potential_code} in {domain}")
                    return potential_code

        return None

    def _extract_city_name(self, domain: str) -> str | None:
        """
        Extract city name from domain.

        Parameters
        ----------
        domain : str
            Domain name to analyze.

        Returns
        -------
        Optional[str]
            City name if found, None otherwise.
        """
        # Common city name patterns in CDN domains
        city_patterns = [
            re.compile(r"\.([a-z]+)-dc\."),  # .seattle-dc.
            re.compile(r"\.([a-z]+)pop\."),  # .seattlepop.
            re.compile(r"-([a-z]+)\d*\."),  # -seattle1.
        ]

        domain_lower = domain.lower()

        for pattern in city_patterns:
            match = pattern.search(domain_lower)
            if match:
                potential_city = match.group(1)
                # Filter out common non-city terms
                if potential_city not in ["cdn", "edge", "cache", "pop", "dc"]:
                    logger.debug(f"Found potential city name: {potential_city} in {domain}")
                    return potential_city

        return None

    async def _geocode_iata(
        self, iata_code: str
    ) -> dict[str, str | float | None] | None:
        """
        Geocode an IATA airport code.

        Parameters
        ----------
        iata_code : str
            IATA airport code.

        Returns
        -------
        Optional[Dict[str, Optional[str | float]]]
            Location information if found.
        """
        try:
            # Search for airport by IATA code
            query = f"{iata_code.upper()} airport"
            location = self.geocoder.geocode(query)

            if location:
                return {
                    "iata_code": iata_code.upper(),
                    "city": self._extract_city_from_address(location.address),
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding failed for IATA {iata_code}: {e}")

        return None

    async def _geocode_city(
        self, city_name: str
    ) -> dict[str, str | float | None] | None:
        """
        Geocode a city name.

        Parameters
        ----------
        city_name : str
            City name to geocode.

        Returns
        -------
        Optional[Dict[str, Optional[str | float]]]
            Location information if found.
        """
        try:
            location = self.geocoder.geocode(city_name)

            if location:
                return {
                    "iata_code": None,
                    "city": self._extract_city_from_address(location.address),
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding failed for city {city_name}: {e}")

        return None

    def _extract_city_from_address(self, address: str) -> str:
        """
        Extract city name from geocoded address.

        Parameters
        ----------
        address : str
            Full address string.

        Returns
        -------
        str
            Extracted city name.
        """
        # Take first few components of the address
        parts = address.split(",")
        if len(parts) >= 2:
            return f"{parts[0].strip()}, {parts[1].strip()}"
        return parts[0].strip() if parts else address
