"""
TheAleph API integration for enhanced geocoding.

This module provides enhanced geocoding capabilities using TheAleph API
with full HTTPS security and SSL certificate validation.
"""

from __future__ import annotations

import asyncio
import re
import socket
from typing import Any

import httpx
from loguru import logger

from ..config.settings import Settings


class AlephGeocodeService:
    """
    Enhanced geocoding service using TheAleph API.

    This service provides superior location resolution for network infrastructure
    by leveraging TheAleph's PTR record and geographic intelligence with full
    HTTPS security and IPv6 support.

    Parameters
    ----------
    settings : Settings
        Application settings.
    client : Optional[httpx.AsyncClient]
        HTTP client instance.

    Attributes
    ----------
    settings : Settings
        Application settings.
    client : httpx.AsyncClient
        HTTP client with full SSL verification enabled.
    """

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        """Initialize TheAleph geocoding service."""
        self.settings = settings
        
        # Create client with full SSL verification enabled
        if client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.request_timeout),
                verify=True,  # Full SSL verification enabled
                follow_redirects=True,
            )
        else:
            self.client = client
            
        logger.info("TheAleph API integration initialized with full HTTPS security")

    def _is_ipv6_domain(self, domain: str) -> bool:
        """
        Detect if a domain is IPv6-related based on naming convention.
        
        Netflix IPv6 OCA domains typically contain 'ipv6' in the hostname.
        Example: ipv6-c001-ord001-ix.1.oca.nflxvideo.net
        
        Parameters
        ----------
        domain : str
            Domain name to check.
            
        Returns
        -------
        bool
            True if domain appears to be IPv6-related, False otherwise.
        """
        return "ipv6" in domain.lower()
    
    def _detect_ip_type(self, ip_address: str) -> str:
        """
        Determine if an IP address is IPv4, IPv6, or unknown.
        
        Parameters
        ----------
        ip_address : str
            IP address to analyze.
            
        Returns
        -------
        str
            "ipv4" - Contains dots but no colons (e.g., "192.168.1.1")
            "ipv6" - Contains colons (e.g., "2001:db8::1")
            "unknown" - Cannot determine type
        """
        if not ip_address:
            return "unknown"
            
        if "." in ip_address and ":" not in ip_address:
            return "ipv4"
        elif ":" in ip_address:
            return "ipv6"
        else:
            return "unknown"
    
    async def _get_ptr_record(self, ip_address: str) -> str | None:
        """
        Get PTR record for an IP address.
        
        Parameters
        ----------
        ip_address : str
            IP address to lookup PTR record for.
            
        Returns
        -------
        str | None
            PTR record if found, None otherwise.
        """
        try:
            logger.debug(f"Looking up PTR record for {ip_address}")
            
            # Use asyncio to run the synchronous socket call
            loop = asyncio.get_event_loop()
            ptr_record = await loop.run_in_executor(
                None, socket.gethostbyaddr, ip_address
            )
            
            # gethostbyaddr returns (hostname, aliaslist, ipaddrlist)
            hostname = ptr_record[0]
            logger.debug(f"PTR record for {ip_address}: {hostname}")
            return hostname
            
        except socket.herror as e:
            logger.debug(f"No PTR record found for {ip_address}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error looking up PTR record for {ip_address}: {e}")
            return None
    
    def _is_valid_ptr_for_thealeph(self, ptr_record: str) -> bool:
        """
        Validate if a PTR record is suitable for TheAleph API.
        
        Invalid conditions:
        - Contains ":" (IPv6 indicator)
        - Is None or empty
        - Contains invalid characters
        
        Parameters
        ----------
        ptr_record : str
            PTR record to validate.
            
        Returns
        -------
        bool
            True if PTR record is valid for TheAleph, False otherwise.
        """
        if not ptr_record:
            return False
        
        if ":" in ptr_record:
            return False
            
        # Additional validation can be added here
        return True

    async def __aenter__(self) -> AlephGeocodeService:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    async def resolve_domain_location(
        self, domain: str, asn: str | None = None, ip_address: str | None = None
    ) -> dict[str, str | float | None] | None:
        """
        Resolve domain location using TheAleph API with IPv6 support.

        This method queries TheAleph's PTR and geolocation intelligence
        to provide enhanced location resolution for CDN domains, including
        intelligent handling of IPv6 domains with NAT64 detection.

        Parameters
        ----------
        domain : str
            Domain (PTR record) to resolve location for.
        asn : str | None
            Autonomous System Number for enhanced location resolution.
        ip_address : str | None
            IP address associated with the domain.

        Returns
        -------
        dict[str, str | float | None] | None
            Dictionary with location information or None if resolution fails.
        """
        try:
            logger.debug(f"Resolving location for domain: {domain} (ASN: {asn}, IP: {ip_address})")
            
            # Check if this is an IPv6 domain
            if self._is_ipv6_domain(domain):
                return await self._handle_ipv6_domain(domain, asn, ip_address)
            
            # Standard IPv4 domain handling
            return await self._handle_standard_domain(domain, asn, ip_address)
            
        except Exception as e:
            logger.debug(f"TheAleph geocoding failed for {domain}: {e}")
            return None

    async def _handle_ipv6_domain(
        self, domain: str, asn: str | None, ip_address: str | None
    ) -> dict[str, str | float | None] | None:
        """
        Handle IPv6 domains with NAT64 support.
        
        Parameters
        ----------
        domain : str
            IPv6 domain name.
        asn : str | None
            Autonomous System Number.
        ip_address : str | None
            IP address associated with the domain.
            
        Returns
        -------
        dict[str, str | float | None] | None
            Location information or None if resolution fails.
        """
        logger.debug(f"Handling IPv6 domain: {domain}")
        
        if ip_address:
            ip_type = self._detect_ip_type(ip_address)
            
            if ip_type == "ipv4":
                # NAT64 detected: IPv6 domain resolved to IPv4 address
                logger.debug(f"NAT64 detected for IPv6 domain {domain} -> IPv4 {ip_address}")
                return await self._handle_nat64_case(domain, asn, ip_address)
                
            elif ip_type == "ipv6":
                # Pure IPv6 case: IPv6 domain resolved to IPv6 address
                logger.debug(f"Pure IPv6 detected for domain {domain} -> IPv6 {ip_address}")
                return await self._handle_pure_ipv6_case(domain, asn, ip_address)
        
        # No IP address or invalid - use geopy fallback
        logger.debug(f"Using geopy fallback for IPv6 domain {domain} (no valid IP)")
        return None  # Will trigger fallback in HybridGeocodeService

    async def _handle_nat64_case(
        self, domain: str, asn: str | None, ipv4_address: str
    ) -> dict[str, str | float | None] | None:
        """
        Handle NAT64 case where IPv6 domain resolves to IPv4 address.
        
        Parameters
        ----------
        domain : str
            Original IPv6 domain.
        asn : str | None
            Autonomous System Number.
        ipv4_address : str
            IPv4 address from NAT64.
            
        Returns
        -------
        dict[str, str | float | None] | None
            Location information or None if resolution fails.
        """
        # Try PTR lookup on the IPv4 address
        ptr_record = await self._get_ptr_record(ipv4_address)
        
        if ptr_record and self._is_valid_ptr_for_thealeph(ptr_record):
            logger.debug(f"Using PTR record {ptr_record} for NAT64 IPv6 domain {domain}")
            
            # Try with original ASN
            result = await self._handle_standard_domain(ptr_record, asn, ipv4_address)
            if result:
                result["original_domain"] = domain
                result["nat64_detected"] = True
                return result
            
            # Try with Netflix ASN fallback
            result = await self._handle_standard_domain(ptr_record, "2906", ipv4_address)
            if result:
                result["original_domain"] = domain
                result["nat64_detected"] = True
                result["fallback_used"] = "netflix_asn"
                return result
        
        # PTR lookup failed - try using domain directly with TheAleph workaround
        logger.debug(f"PTR lookup failed, trying direct domain resolution for NAT64 {domain}")
        
        # Try with original ASN
        result = await self._handle_standard_domain(domain, asn, ipv4_address)
        if result:
            result["nat64_detected"] = True
            return result
            
        # Try with Netflix ASN fallback
        result = await self._handle_standard_domain(domain, "2906", ipv4_address)
        if result:
            result["nat64_detected"] = True
            result["fallback_used"] = "netflix_asn"
            return result
        
        return None

    async def _handle_pure_ipv6_case(
        self, domain: str, asn: str | None, ipv6_address: str
    ) -> dict[str, str | float | None] | None:
        """
        Handle pure IPv6 case where IPv6 domain resolves to IPv6 address.
        
        Since TheAleph doesn't support IPv6 addresses directly, this method
        implements the IPv6 workaround using PTR record analysis.
        
        Parameters
        ----------
        domain : str
            IPv6 domain.
        asn : str | None
            Autonomous System Number.
        ipv6_address : str
            IPv6 address.
            
        Returns
        -------
        dict[str, str | float | None] | None
            Location information or None if resolution fails.
        """
        logger.debug(f"Implementing IPv6 workaround for {domain} -> {ipv6_address}")
        
        # Try PTR lookup on the IPv6 address
        ptr_record = await self._get_ptr_record(ipv6_address)
        
        if ptr_record and self._is_valid_ptr_for_thealeph(ptr_record):
            logger.debug(f"Using PTR record {ptr_record} for IPv6 address {ipv6_address}")
            
            # Try with original ASN using PTR record
            result = await self._handle_standard_domain(ptr_record, asn, "")
            if result:
                result["original_domain"] = domain
                result["original_ip"] = ipv6_address
                result["ipv6_workaround"] = True
                return result
            
            # Try with Netflix ASN fallback using PTR record
            result = await self._handle_standard_domain(ptr_record, "2906", "")
            if result:
                result["original_domain"] = domain
                result["original_ip"] = ipv6_address
                result["ipv6_workaround"] = True
                result["fallback_used"] = "netflix_asn"
                return result
        
        # PTR lookup failed - try using original domain with empty IP
        logger.debug(f"PTR lookup failed, trying domain-based resolution for IPv6 {domain}")
        
        # Try with original ASN
        result = await self._handle_standard_domain(domain, asn, "")
        if result:
            result["original_ip"] = ipv6_address
            result["ipv6_workaround"] = True
            return result
            
        # Try with Netflix ASN fallback
        result = await self._handle_standard_domain(domain, "2906", "")
        if result:
            result["original_ip"] = ipv6_address
            result["ipv6_workaround"] = True
            result["fallback_used"] = "netflix_asn"
            return result
        
        # All IPv6 workarounds failed - return None for geopy fallback
        logger.debug(f"IPv6 workaround failed for {domain}, falling back to geopy")
        return None

    async def _handle_standard_domain(
        self, domain: str, asn: str | None, ip_address: str | None
    ) -> dict[str, str | float | None] | None:
        """
        Handle standard domain resolution using TheAleph API.
        
        Parameters
        ----------
        domain : str
            Domain to resolve.
        asn : str | None
            Autonomous System Number.
        ip_address : str | None
            IP address associated with the domain.
            
        Returns
        -------
        dict[str, str | float | None] | None
            Location information or None if resolution fails.
        """
        try:
            # TheAleph API payload structure - match working curl command exactly
            payload = {
                "ptr_record": domain,
                "ip": ip_address or "",  # Always include ip field, empty string if not provided
            }
            
            # Add ASN if available
            if asn:
                try:
                    payload["asn"] = int(asn)  # Convert to integer as expected by API
                except (ValueError, TypeError):
                    logger.warning(f"Invalid ASN format: {asn}, skipping ASN in payload")
                
            logger.debug(f"TheAleph payload: {payload}")
            
            # Make API request with headers matching working curl command
            response = await self.client.post(
                "https://thealeph.ai/api/query",
                json=payload,
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                }
            )
            
            # Check response status
            response.raise_for_status()
            data = response.json()
            
            # Parse TheAleph response
            return await self._parse_aleph_response(data, domain)
            
        except httpx.TimeoutException:
            logger.debug(f"TheAleph API timeout for domain: {domain}")
            return None
        except httpx.RequestError as e:
            logger.debug(f"TheAleph API request failed for {domain}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                logger.debug(f"TheAleph API server error for {domain} (this is common)")
            else:
                logger.warning(f"TheAleph API HTTP error {e.response.status_code} for {domain}")
            return None
        except Exception as e:
            logger.debug(f"TheAleph standard domain handling failed for {domain}: {e}")
            return None

    async def resolve_ip_location(
        self, ip_address: str
    ) -> dict[str, str | float | None] | None:
        """
        Resolve IP address location using TheAleph API.

        Parameters
        ----------
        ip_address : str
            IP address to resolve.

        Returns
        -------
        dict[str, str | float | None] | None
            Dictionary with location information or None if resolution fails.
        """
        try:
            logger.debug(f"Resolving location for IP: {ip_address}")
            
            payload = {
                "query": ip_address,
                "type": "ip",
                "include_geo": True,
                "include_asn": True,
                "include_infrastructure": True
            }
            
            response = await self.client.post(
                "https://thealeph.ai/api/query",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"{self.settings.app_name}/{self.settings.version}",
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            return await self._parse_aleph_response(data, ip_address)
            
        except Exception as e:
            logger.warning(f"TheAleph IP resolution failed for {ip_address}: {e}")
            return None

    async def _parse_aleph_response(
        self, data: dict[str, Any], query: str
    ) -> dict[str, str | float | None] | None:
        """
        Parse TheAleph API response into standardized location format.

        The actual TheAleph response structure is:
        {
          "ptr_record": "ipv4-c148-ord003-ix.1.oca.nflxvideo.net",
          "asn": 2906,
          "location_info": {
            "city": "Chicago",
            "state": "IL",
            "region": "",
            "country": "US",
            "latitude": 41.978252,
            "longitude": -87.90923
          },
          "regular_expression": "([a-z]{3})(\\d{3})",
          "geo_hint": "ord",
          "ip": "string"
        }

        Parameters
        ----------
        data : dict[str, Any]
            Raw API response from TheAleph.
        query : str
            Original query string for logging.

        Returns
        -------
        dict[str, str | float | None] | None
            Parsed location information or None if parsing fails.
        """
        try:
            logger.debug(f"TheAleph raw response for {query}: {data}")
            
            # Check if we have the expected response structure
            if not data or "location_info" not in data:
                logger.debug(f"No location_info in TheAleph response for: {query}")
                return None
                
            location_data = data["location_info"]
            if not location_data:
                logger.debug(f"Empty location_info in TheAleph response for: {query}")
                return None
            
            # Extract location information from the actual response structure
            location_info = {
                "iata_code": None,
                "city": None,
                "latitude": None,
                "longitude": None,
                "country": None,
                "region": None,
                "provider": "thealeph"
            }
            
            # Extract coordinates from location_info
            location_info["latitude"] = location_data.get("latitude")
            location_info["longitude"] = location_data.get("longitude")
            location_info["country"] = location_data.get("country")
            
            # Build city name from available components
            city_parts = []
            if location_data.get("city"):
                city_parts.append(location_data["city"])
            if location_data.get("state"):
                city_parts.append(location_data["state"])
            elif location_data.get("region"):
                city_parts.append(location_data["region"])
                
            if city_parts:
                location_info["city"] = ", ".join(city_parts)
            
            # Extract IATA code from geo_hint
            geo_hint = data.get("geo_hint", "")
            if geo_hint and len(geo_hint) == 3 and geo_hint.isalpha():
                location_info["iata_code"] = geo_hint.upper()
                
            # If no geo_hint, try to extract from the PTR record using regex
            if not location_info["iata_code"]:
                regex_pattern = data.get("regular_expression", "")
                if regex_pattern:
                    try:
                        match = re.search(regex_pattern, query)
                        if match and len(match.groups()) >= 1:
                            potential_iata = match.group(1)
                            if len(potential_iata) == 3 and potential_iata.isalpha():
                                location_info["iata_code"] = potential_iata.upper()
                    except Exception as e:
                        logger.debug(f"Failed to apply regex {regex_pattern} to {query}: {e}")
                        
            # Return only if we have useful information
            if any(location_info[key] for key in ["latitude", "city", "iata_code"]):
                logger.info(f"TheAleph successfully resolved location for {query}: {location_info}")
                return location_info
            else:
                logger.debug(f"TheAleph response had no useful location data for {query}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to parse TheAleph response for {query}: {e}")
            logger.debug(f"TheAleph response data: {data}")
            return None

    def _extract_iata_from_string(self, text: str) -> str | None:
        """
        Extract IATA code from text string.

        Parameters
        ----------
        text : str
            Text to search for IATA codes.

        Returns
        -------
        str | None
            IATA code if found, None otherwise.
        """
        # Common patterns for IATA codes in hostnames
        patterns = [
            r'\b([a-z]{3})\d*\.',  # lax1., ord2.
            r'-([a-z]{3})-',       # -lax-
            r'\.([a-z]{3})\.',     # .lax.
            r'^([a-z]{3})\d*\.',   # lax1.domain.com
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                candidate = match.group(1)
                if len(candidate) == 3 and candidate.isalpha():
                    return candidate.upper()
                    
        return None


class HybridGeocodeService:
    """
    Hybrid geocoding service that combines TheAleph and Geopy.

    This service tries TheAleph first for enhanced accuracy,
    then falls back to Geopy for standard geocoding.

    Parameters
    ----------
    settings : Settings
        Application settings.
    aleph_service : Optional[AlephGeocodeService]
        TheAleph service instance.
    geopy_service : Optional[GeocodeService]
        Geopy service instance.

    Attributes
    ----------
    settings : Settings
        Application settings.
    aleph_service : AlephGeocodeService
        TheAleph geocoding service.
    geopy_service : GeocodeService
        Fallback geocoding service.
    """

    def __init__(
        self,
        settings: Settings,
        aleph_service: AlephGeocodeService | None = None,
        geopy_service: Any | None = None,
    ) -> None:
        """Initialize hybrid geocoding service."""
        self.settings = settings
        self.aleph_service = aleph_service or AlephGeocodeService(settings)
        
        # Import GeocodeService here to avoid circular imports
        if geopy_service is None:
            from .geocoding import GeocodeService
            self.geopy_service = GeocodeService(settings)
        else:
            self.geopy_service = geopy_service

    async def extract_location_from_domain(
        self, domain: str, asn: str | None = None, ip_address: str | None = None
    ) -> dict[str, str | float | None] | None:
        """
        Extract location from domain using hybrid approach.

        Parameters
        ----------
        domain : str
            Domain to resolve.
        asn : str | None
            Autonomous System Number for enhanced location resolution.
        ip_address : str | None
            IP address associated with the domain.

        Returns
        -------
        dict[str, str | float | None] | None
            Location information or None if resolution fails.
        """
        # Try TheAleph first with original ASN
        try:
            aleph_result = await self.aleph_service.resolve_domain_location(domain, asn, ip_address)
            if aleph_result and self._is_good_result(aleph_result):
                logger.debug(f"TheAleph provided location for {domain} with ASN {asn}")
                return aleph_result
        except Exception as e:
            logger.debug(f"TheAleph geocoding failed for {domain} with ASN {asn}: {e}")

        # If TheAleph returns nothing, try again with Netflix's ASN 2906
        if asn != "2906":
            try:
                logger.debug(f"Trying TheAleph fallback with Netflix ASN 2906 for {domain}")
                aleph_fallback_result = await self.aleph_service.resolve_domain_location(domain, "2906", ip_address)
                if aleph_fallback_result and self._is_good_result(aleph_fallback_result):
                    logger.debug(f"TheAleph provided location for {domain} with Netflix ASN fallback")
                    return aleph_fallback_result
            except Exception as e:
                logger.debug(f"TheAleph geocoding failed for {domain} with Netflix ASN fallback: {e}")

        # Fallback to standard geocoding
        try:
            geopy_result = await self.geopy_service.extract_location_from_domain(domain)
            if geopy_result:
                logger.debug(f"Geopy provided fallback location for {domain}")
                if isinstance(geopy_result, dict):
                    geopy_result["provider"] = "geopy_fallback"
                return geopy_result
        except Exception as e:
            logger.warning(f"Geopy fallback failed for {domain}: {e}")

        return None

    def _is_good_result(self, result: dict[str, str | float | None]) -> bool:
        """
        Check if geocoding result is of good quality.

        Parameters
        ----------
        result : dict[str, str | float | None]
            Geocoding result to evaluate.

        Returns
        -------
        bool
            True if result is good quality, False otherwise.
        """
        # Check for valid coordinates (not None, not -1.0 placeholder values)
        lat = result.get("latitude")
        lon = result.get("longitude")
        has_valid_coords = (
            lat is not None and lon is not None and 
            lat != -1.0 and lon != -1.0 and
            isinstance(lat, (int, float)) and isinstance(lon, (int, float))
        )
        
        # Check for city and IATA code
        has_city_and_iata = result.get("city") is not None and result.get("iata_code") is not None
        
        return has_valid_coords or has_city_and_iata