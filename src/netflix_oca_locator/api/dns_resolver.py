"""
DNS resolution service for IPv4 and IPv6 support.

This module provides intelligent DNS resolution with automatic query type
selection based on domain naming conventions for Netflix OCA domains.
"""

from __future__ import annotations

import asyncio
import socket
from typing import Any

from loguru import logger

from ..config.settings import Settings


class DNSResolver:
    """
    DNS resolution service with IPv4/IPv6 support.

    This service provides domain name resolution with automatic query type
    selection based on Netflix OCA domain naming conventions:
    - Domains containing "ipv6" → AAAA queries (IPv6)
    - Domains containing "ipv4" → A queries (IPv4)
    - Default → A queries (IPv4) for backward compatibility

    Parameters
    ----------
    settings : Settings
        Application settings for timeout configuration.

    Attributes
    ----------
    settings : Settings
        Application settings.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize DNS resolver."""
        self.settings = settings

    async def resolve_domain(self, domain: str) -> str:
        """
        Resolve domain to IP address using automatic query type selection.

        Automatically selects DNS query type based on domain naming:
        - If domain contains "ipv6" → issue AAAA query
        - If domain contains "ipv4" → issue A query
        - Default → A query for backward compatibility

        Parameters
        ----------
        domain : str
            Domain name to resolve.

        Returns
        -------
        str
            Resolved IP address (IPv4 or IPv6).

        Raises
        ------
        OSError
            If DNS resolution fails.
        """
        domain_lower = domain.lower()
        
        if "ipv6" in domain_lower:
            logger.debug(f"Detected IPv6 domain, using AAAA query for: {domain}")
            return await self.resolve_ipv6(domain)
        elif "ipv4" in domain_lower:
            logger.debug(f"Detected IPv4 domain, using A query for: {domain}")
            return await self.resolve_ipv4(domain)
        else:
            logger.debug(f"Using default A query for: {domain}")
            return await self.resolve_ipv4(domain)

    async def resolve_ipv4(self, domain: str) -> str:
        """
        Resolve domain to IPv4 address using A record query.

        Parameters
        ----------
        domain : str
            Domain name to resolve.

        Returns
        -------
        str
            IPv4 address.

        Raises
        ------
        OSError
            If DNS resolution fails or no IPv4 address found.
        """
        try:
            logger.debug(f"Resolving IPv4 (A record) for: {domain}")
            
            # Use asyncio to run the synchronous socket call
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                socket.getaddrinfo,
                domain,
                None,
                socket.AF_INET,  # IPv4 only
                socket.SOCK_STREAM
            )
            
            if not result:
                raise OSError(f"No IPv4 address found for {domain}")
            
            # Extract IP address from the first result
            ip_address = result[0][4][0]
            logger.debug(f"Resolved {domain} to IPv4: {ip_address}")
            return ip_address
            
        except Exception as e:
            logger.warning(f"Failed to resolve IPv4 for {domain}: {e}")
            raise OSError(f"DNS resolution failed for {domain}: {e}") from e

    async def resolve_ipv6(self, domain: str) -> str:
        """
        Resolve domain to IPv6 address using AAAA record query.

        Parameters
        ----------
        domain : str
            Domain name to resolve.

        Returns
        -------
        str
            IPv6 address.

        Raises
        ------
        OSError
            If DNS resolution fails or no IPv6 address found.
        """
        try:
            logger.debug(f"Resolving IPv6 (AAAA record) for: {domain}")
            
            # Use asyncio to run the synchronous socket call
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                socket.getaddrinfo,
                domain,
                None,
                socket.AF_INET6,  # IPv6 only
                socket.SOCK_STREAM
            )
            
            if not result:
                raise OSError(f"No IPv6 address found for {domain}")
            
            # Extract IP address from the first result
            ip_address = result[0][4][0]
            logger.debug(f"Resolved {domain} to IPv6: {ip_address}")
            return ip_address
            
        except Exception as e:
            logger.warning(f"Failed to resolve IPv6 for {domain}: {e}")
            raise OSError(f"DNS resolution failed for {domain}: {e}") from e

    async def resolve_any(self, domain: str) -> str:
        """
        Resolve domain to any available IP address (IPv4 or IPv6).

        This method tries both IPv4 and IPv6 resolution and returns
        the first successful result.

        Parameters
        ----------
        domain : str
            Domain name to resolve.

        Returns
        -------
        str
            IP address (IPv4 or IPv6).

        Raises
        ------
        OSError
            If DNS resolution fails for both IPv4 and IPv6.
        """
        try:
            logger.debug(f"Resolving any IP (A or AAAA record) for: {domain}")
            
            # Use asyncio to run the synchronous socket call
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                socket.getaddrinfo,
                domain,
                None,
                socket.AF_UNSPEC,  # Any address family
                socket.SOCK_STREAM
            )
            
            if not result:
                raise OSError(f"No IP address found for {domain}")
            
            # Extract IP address from the first result
            ip_address = result[0][4][0]
            
            # Determine IP version for logging
            ip_version = "IPv6" if ":" in ip_address else "IPv4"
            logger.debug(f"Resolved {domain} to {ip_version}: {ip_address}")
            return ip_address
            
        except Exception as e:
            logger.warning(f"Failed to resolve any IP for {domain}: {e}")
            raise OSError(f"DNS resolution failed for {domain}: {e}") from e

    def is_ipv6_address(self, ip_address: str) -> bool:
        """
        Check if an IP address string is IPv6.

        Parameters
        ----------
        ip_address : str
            IP address string to check.

        Returns
        -------
        bool
            True if IPv6, False if IPv4 or invalid.
        """
        try:
            # Try to parse as IPv6
            socket.inet_pton(socket.AF_INET6, ip_address)
            return True
        except socket.error:
            return False

    def is_ipv4_address(self, ip_address: str) -> bool:
        """
        Check if an IP address string is IPv4.

        Parameters
        ----------
        ip_address : str
            IP address string to check.

        Returns
        -------
        bool
            True if IPv4, False if IPv6 or invalid.
        """
        try:
            # Try to parse as IPv4
            socket.inet_pton(socket.AF_INET, ip_address)
            return True
        except socket.error:
            return False