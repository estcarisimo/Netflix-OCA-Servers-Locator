"""
Core business logic for OCA location.

This module orchestrates the process of locating Netflix OCAs
for the user's network.
"""

from __future__ import annotations

import asyncio

from loguru import logger

from ..api.fast_com import FastComAPI
from ..api.ip_services import IPServices
from ..config.settings import Settings
from ..utils.geocoding import GeocodeService
from ..utils.aleph_geocoding import HybridGeocodeService
from .models import OCALocatorResult, OCAServer


class OCALocator:
    """
    Main class for locating Netflix OCAs.

    This class orchestrates the process of:
    1. Getting public IP
    2. Getting ISP information
    3. Getting Netflix token
    4. Fetching OCA candidates
    5. Enriching with geolocation data

    Parameters
    ----------
    settings : Settings
        Application settings.
    ip_service : Optional[IPServices]
        IP services instance.
    fast_com_api : Optional[FastComAPI]
        Fast.com API instance.
    geocode_service : Optional[GeocodeService]
        Geocoding service instance.

    Attributes
    ----------
    settings : Settings
        Application settings.
    ip_service : IPServices
        IP services instance.
    fast_com_api : FastComAPI
        Fast.com API instance.
    geocode_service : GeocodeService
        Geocoding service instance.
    """

    def __init__(
        self,
        settings: Settings,
        ip_service: IPServices | None = None,
        fast_com_api: FastComAPI | None = None,
        geocode_service: GeocodeService | None = None,
    ) -> None:
        """Initialize OCA Locator."""
        self.settings = settings
        self.ip_service = ip_service or IPServices(settings)
        self.fast_com_api = fast_com_api or FastComAPI(settings)
        
        # Choose geocoding service based on configuration
        if geocode_service is not None:
            self.geocode_service = geocode_service
        elif settings.geocoding_provider == "hybrid":
            self.geocode_service = HybridGeocodeService(settings)
        elif settings.geocoding_provider == "aleph":
            from ..utils.aleph_geocoding import AlephGeocodeService
            self.geocode_service = AlephGeocodeService(settings)
        else:
            self.geocode_service = GeocodeService(settings)

    async def locate_ocas(self) -> OCALocatorResult:
        """
        Locate OCAs for the current network.

        This method performs the complete OCA location process:
        1. Fetches public IP address
        2. Gets ISP information via WHOIS
        3. Obtains Fast.com token
        4. Retrieves OCA candidates
        5. Enriches with geolocation data

        Returns
        -------
        OCALocatorResult
            Complete result with all information.

        Raises
        ------
        Exception
            If any step in the process fails.
        """
        logger.info("Starting OCA location process")

        # Step 1: Get public IP
        logger.debug("Fetching public IP address")
        public_ip = await self.ip_service.get_public_ip()
        logger.info(f"Public IP: {public_ip.ip}")

        # Step 2: Get ISP info
        logger.debug("Fetching ISP information")
        isp_info = await self.ip_service.get_isp_info(str(public_ip.ip))
        logger.info(f"ISP: {isp_info.as_name} (AS{isp_info.asn})")

        # Step 3: Get Fast.com token
        logger.debug("Fetching Fast.com token")
        token = await self.fast_com_api.get_token()
        logger.info("Successfully obtained Fast.com token")

        # Step 4: Fetch OCA candidates
        logger.debug("Fetching OCA candidates")
        oca_servers = await self.fast_com_api.fetch_oca_candidates(token)
        logger.info(f"Found {len(oca_servers)} OCA servers")

        # Step 5: Enrich with geolocation
        logger.debug("Enriching OCA data with geolocation")
        oca_servers = await self._enrich_with_geolocation(oca_servers, isp_info.asn)

        # Create result
        result = OCALocatorResult(
            public_ip=public_ip,
            isp_info=isp_info,
            oca_servers=oca_servers,
            fast_com_token=token,
        )

        logger.info("OCA location process completed successfully")
        return result

    async def _enrich_with_geolocation(
        self, oca_servers: list[OCAServer], user_asn: str | None = None
    ) -> list[OCAServer]:
        """
        Enrich OCA servers with geolocation data.

        Parameters
        ----------
        oca_servers : list[OCAServer]
            List of OCA servers to enrich.
        user_asn : str | None
            User's ISP ASN for enhanced geocoding.

        Returns
        -------
        list[OCAServer]
            Enriched OCA servers.
        """
        tasks = [self._enrich_single_oca(oca, user_asn) for oca in oca_servers]
        enriched_servers = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out any exceptions
        result = []
        for server in enriched_servers:
            if isinstance(server, Exception):
                logger.warning(f"Failed to enrich OCA: {server}")
                # Return original server without enrichment
                idx = enriched_servers.index(server)
                result.append(oca_servers[idx])
            else:
                result.append(server)

        return result

    async def _enrich_single_oca(self, oca: OCAServer, user_asn: str | None = None) -> OCAServer:
        """
        Enrich a single OCA server with geolocation.

        Parameters
        ----------
        oca : OCAServer
            OCA server to enrich.
        user_asn : str | None
            User's ISP ASN (kept for backward compatibility, but not used).

        Returns
        -------
        OCAServer
            Enriched OCA server.
        """
        # Step 1: Lookup ASN and AS name for this specific OCA's IP address
        oca_asn, as_name = await self._get_oca_asn_info(str(oca.ip_address))
        
        # Step 2: Try to extract location from domain using OCA's own ASN and IP
        location_info = await self.geocode_service.extract_location_from_domain(
            oca.domain, oca_asn, str(oca.ip_address)
        )

        if location_info:
            oca.iata_code = location_info.get("iata_code")
            oca.city = location_info.get("city")
            oca.latitude = location_info.get("latitude")
            oca.longitude = location_info.get("longitude")
            # Store the geocoding approach (method used)
            oca.geolocation_approach = location_info.get("provider", "unknown")
            
        # Use AS name as provider (network provider)
        oca.geocoding_provider = as_name or "unknown"
        # Store the OCA's individual ASN
        oca.asn = oca_asn

        return oca

    async def _get_oca_asn_info(self, ip_address: str) -> tuple[str | None, str | None]:
        """
        Get ASN and AS name for a specific OCA IP address with Netflix fallback.

        Parameters
        ----------
        ip_address : str
            IP address of the OCA server.

        Returns
        -------
        tuple[str | None, str | None]
            Tuple of (ASN number, AS name) or fallback values.
        """
        try:
            logger.debug(f"Looking up ASN for OCA IP: {ip_address}")
            
            # Try to get ISP info for this specific OCA IP
            isp_info = await self.ip_service.get_isp_info(ip_address)
            if isp_info and isp_info.asn:
                logger.debug(f"Found ASN {isp_info.asn} ({isp_info.as_name}) for OCA IP {ip_address}")
                return isp_info.asn, isp_info.as_name
                
        except Exception as e:
            logger.warning(f"Failed to lookup ASN for OCA IP {ip_address}: {e}")
        
        # Fallback to Netflix's ASN
        logger.debug(f"Using Netflix fallback ASN (2906) for OCA IP {ip_address}")
        return "2906", "AS-SSI"


async def create_locator() -> OCALocator:
    """
    Create an OCA Locator instance with default settings.

    Returns
    -------
    OCALocator
        Configured OCA Locator instance.
    """
    from ..config.settings import get_settings

    settings = get_settings()
    return OCALocator(settings)
