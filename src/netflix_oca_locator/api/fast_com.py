"""
Fast.com API interaction module.

This module handles interactions with Netflix's Fast.com service
to obtain tokens and fetch OCA candidates.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config.settings import Settings
from ..core.models import OCAServer
from .dns_resolver import DNSResolver


class FastComAPI:
    """
    API client for Fast.com interactions with IPv6 support.

    This client provides intelligent DNS resolution for Netflix OCA domains,
    automatically selecting A (IPv4) or AAAA (IPv6) queries based on domain
    naming conventions.

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
    dns_resolver : DNSResolver
        DNS resolver for IPv4/IPv6 domain resolution.
    """

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        """Initialize Fast.com API client."""
        self.settings = settings
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout),
            follow_redirects=True,
        )
        self.dns_resolver = DNSResolver(settings)

    async def __aenter__(self) -> FastComAPI:
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
    async def get_token(self) -> str:
        """
        Retrieve a Netflix token from Fast.com.

        This method:
        1. Fetches the Fast.com homepage
        2. Extracts the JavaScript file URL
        3. Fetches the JavaScript file
        4. Extracts the API token

        Returns
        -------
        str
            The API token for accessing Netflix's OCA data.

        Raises
        ------
        ValueError
            If token extraction fails.
        httpx.RequestError
            If HTTP requests fail.
        """
        logger.debug("Fetching Fast.com homepage")

        try:
            # Step 1: Get Fast.com homepage
            response = await self.client.get(self.settings.fast_com_url)
            response.raise_for_status()
            html_content = response.text

            # Step 2: Extract JS file URL
            js_match = re.search(self.settings.fast_com_js_pattern, html_content)
            if not js_match:
                raise ValueError("Could not find JavaScript file URL in Fast.com HTML")

            js_path = js_match.group(1)
            js_url = f"{self.settings.fast_com_url}{js_path}"
            logger.debug(f"Found JavaScript file: {js_url}")

            # Step 3: Fetch JavaScript file
            js_response = await self.client.get(js_url)
            js_response.raise_for_status()
            js_content = js_response.text

            # Step 4: Extract token
            token_match = re.search(self.settings.token_pattern, js_content)
            if not token_match:
                raise ValueError("Could not find token in JavaScript file")

            token = token_match.group(1)
            logger.debug(f"Successfully extracted token: {token[:8]}...")
            return token

        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get Fast.com token: {e}")
            raise ValueError(f"Token extraction failed: {e}") from e

    @retry(
        retry=retry_if_exception_type(httpx.RequestError),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
    )
    async def fetch_oca_candidates(self, token: str) -> list[OCAServer]:
        """
        Fetch Netflix's OCA candidates using the provided token.

        Parameters
        ----------
        token : str
            The API token obtained from get_token().

        Returns
        -------
        List[OCAServer]
            List of OCA server information.

        Raises
        ------
        ValueError
            If the API response is invalid.
        httpx.RequestError
            If the HTTP request fails.
        """
        logger.debug("Fetching OCA candidates from Fast.com API")

        try:
            # Build request parameters
            params = {
                "https": "true",
                "token": token,
                "urlCount": "5",  # Request multiple URLs
            }

            # Make API request
            response = await self.client.get(self.settings.fast_com_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse OCA servers
            oca_servers = await self._parse_oca_response(data)
            logger.info(f"Retrieved {len(oca_servers)} OCA servers")
            return oca_servers

        except httpx.RequestError as e:
            logger.error(f"Failed to fetch OCA candidates: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing OCA response: {e}")
            raise ValueError(f"Failed to fetch OCA candidates: {e}") from e

    async def _parse_oca_response(self, data: dict[str, Any]) -> list[OCAServer]:
        """
        Parse the Fast.com API response into OCAServer objects.

        Parameters
        ----------
        data : Dict[str, Any]
            Raw API response data.

        Returns
        -------
        List[OCAServer]
            List of parsed OCA servers.
        """
        oca_servers = []

        # Handle both single URL and multiple URLs response formats
        urls = []
        if "targets" in data:
            # New format with multiple targets
            for target in data["targets"]:
                if "url" in target:
                    urls.append(target["url"])
        elif "url" in data:
            # Old format with single URL
            urls.append(data["url"])
        else:
            # Try to find URLs in the response
            for _key, value in data.items():
                if isinstance(value, str) and value.startswith("https://"):
                    urls.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and "url" in item:
                            urls.append(item["url"])
                        elif isinstance(item, str) and item.startswith("https://"):
                            urls.append(item)

        # Process each URL
        for url in urls:
            try:
                # Extract domain
                parsed_url = urlparse(url)
                domain = parsed_url.netloc

                # Resolve IP address using IPv4/IPv6 intelligent resolution
                try:
                    ip_address = await self.dns_resolver.resolve_domain(domain)
                except OSError as e:
                    logger.warning(f"Failed to resolve IP for {domain}: {e}")
                    continue

                # Create OCA server object
                oca = OCAServer(
                    domain=domain,
                    ip_address=ip_address,
                    url=url,
                )
                oca_servers.append(oca)

            except Exception as e:
                logger.warning(f"Failed to parse OCA URL {url}: {e}")
                continue

        # Remove duplicates based on domain
        unique_ocas = {oca.domain: oca for oca in oca_servers}
        return list(unique_ocas.values())
