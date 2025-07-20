"""
IP and ISP information services.

This module handles fetching public IP addresses and ISP information
using external services.
"""

from __future__ import annotations

import asyncio
import socket
import subprocess
from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config.settings import Settings
from ..core.models import ISPInfo, PublicIPInfo


class IPServices:
    """
    Service for IP and ISP information lookup.

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
        HTTP client for API requests.
    """

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        """Initialize IP Services."""
        self.settings = settings
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout),
            follow_redirects=True,
        )

    async def __aenter__(self) -> IPServices:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.client.aclose()

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
    )
    async def get_public_ip(self) -> PublicIPInfo:
        """
        Fetch the public IP address of the host.

        Uses the ipify.org API to get the public IP address.

        Returns
        -------
        PublicIPInfo
            Public IP information.

        Raises
        ------
        httpx.RequestError
            If the request fails.
        ValueError
            If the response is invalid.
        """
        logger.debug(f"Fetching public IP from {self.settings.ipify_api_url}")

        try:
            response = await self.client.get(self.settings.ipify_api_url)
            response.raise_for_status()
            data = response.json()

            if "ip" not in data:
                raise ValueError("Invalid response from IP service")

            ip_info = PublicIPInfo(ip=data["ip"])
            logger.debug(f"Retrieved public IP: {ip_info.ip}")
            return ip_info

        except httpx.RequestError as e:
            logger.error(f"Failed to fetch public IP: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching public IP: {e}")
            raise ValueError(f"Failed to get public IP: {e}") from e

    async def get_isp_info(self, ip_address: str) -> ISPInfo:
        """
        Fetch ISP information for a given IP address.

        Uses Team Cymru's WHOIS service to get ISP information.

        Parameters
        ----------
        ip_address : str
            The IP address to lookup.

        Returns
        -------
        ISPInfo
            ISP information.

        Raises
        ------
        ValueError
            If WHOIS lookup fails.
        """
        logger.debug(f"Fetching ISP info for {ip_address}")

        try:
            # Run whois command
            result = await self._run_whois_command(ip_address)

            # Parse the result
            isp_info = self._parse_whois_response(result)
            logger.debug(f"Retrieved ISP info: {isp_info.as_name} (AS{isp_info.asn})")
            return isp_info

        except Exception as e:
            logger.error(f"Failed to get ISP info: {e}")
            raise ValueError(f"Failed to get ISP information: {e}") from e

    async def _run_whois_command(self, ip_address: str) -> str:
        """
        Run WHOIS command asynchronously.

        Parameters
        ----------
        ip_address : str
            IP address to lookup.

        Returns
        -------
        str
            WHOIS command output.

        Raises
        ------
        subprocess.CalledProcessError
            If the command fails.
        """
        cmd = ["whois", "-h", self.settings.cymru_whois_host, f" -v {ip_address}"]

        # Run command asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            stderr.decode("utf-8", errors="ignore")
            raise subprocess.CalledProcessError(
                process.returncode, cmd, output=stdout, stderr=stderr
            )

        return stdout.decode("utf-8")

    def _parse_whois_response(self, response: str) -> ISPInfo:
        """
        Parse WHOIS response into ISPInfo.

        Parameters
        ----------
        response : str
            Raw WHOIS response.

        Returns
        -------
        ISPInfo
            Parsed ISP information.

        Raises
        ------
        ValueError
            If parsing fails.
        """
        lines = response.strip().split("\n")

        if len(lines) < 2:
            raise ValueError("Invalid WHOIS response format")

        # First line contains column headers
        headers = [h.strip() for h in lines[0].split("|")]

        # Second line contains the data
        data_line = lines[1] if len(lines) > 1 else ""
        values = [v.strip() for v in data_line.split("|")]

        if len(headers) != len(values):
            raise ValueError("Mismatched headers and values in WHOIS response")

        # Create a dictionary mapping headers to values
        data_dict: dict[str, str] = dict(zip(headers, values))

        # Map to our ISPInfo model fields
        try:
            isp_info = ISPInfo(
                asn=data_dict.get("AS", ""),
                ip=data_dict.get("IP", ""),
                bgp_prefix=data_dict.get("BGP Prefix", ""),
                cc=data_dict.get("CC", ""),
                registry=data_dict.get("Registry", ""),
                allocated=data_dict.get("Allocated"),
                as_name=data_dict.get("AS Name", ""),
            )
            return isp_info
        except Exception as e:
            logger.error(f"Failed to parse WHOIS data: {e}")
            logger.debug(f"WHOIS response: {response}")
            raise ValueError(f"Failed to parse WHOIS response: {e}") from e

    async def get_ptr_record(self, ip_address: str) -> str | None:
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

    async def resolve_oca_details(self, domain: str, ip_address: str) -> dict[str, Any]:
        """
        Resolve comprehensive details for an OCA server.

        This method combines IP information, ISP details, and PTR records
        to provide complete network intelligence for TheAleph API.

        Parameters
        ----------
        domain : str
            OCA domain name.
        ip_address : str
            OCA IP address.

        Returns
        -------
        dict[str, Any]
            Comprehensive OCA network details.
        """
        logger.debug(f"Resolving comprehensive details for {domain} ({ip_address})")
        
        details = {
            "domain": domain,
            "ip_address": ip_address,
            "ptr_record": None,
            "isp_info": None,
            "asn": None,
        }
        
        try:
            # Get PTR record
            ptr_record = await self.get_ptr_record(ip_address)
            if ptr_record:
                details["ptr_record"] = ptr_record
                logger.debug(f"Found PTR record: {ptr_record}")
            
            # Get ISP information including ASN
            try:
                isp_info = await self.get_isp_info(ip_address)
                details["isp_info"] = {
                    "asn": isp_info.asn,
                    "as_name": isp_info.as_name,
                    "country": isp_info.cc,
                    "registry": isp_info.registry,
                    "bgp_prefix": isp_info.bgp_prefix,
                }
                details["asn"] = isp_info.asn
                logger.debug(f"Found ASN: AS{isp_info.asn} ({isp_info.as_name})")
            except Exception as e:
                logger.warning(f"Could not get ISP info for {ip_address}: {e}")
            
            return details
            
        except Exception as e:
            logger.error(f"Error resolving OCA details for {domain}: {e}")
            return details
