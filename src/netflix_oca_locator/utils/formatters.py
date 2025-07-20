"""
Output formatters for various export formats.

This module provides functionality to export OCA location results
in different formats (JSON, CSV, Excel, Markdown).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from loguru import logger

from ..config.settings import Settings
from ..core.models import OCALocatorResult


class ResultFormatter:
    """
    Format and export OCA location results.

    Parameters
    ----------
    settings : Settings
        Application settings.

    Attributes
    ----------
    settings : Settings
        Application settings.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize result formatter."""
        self.settings = settings

    def export_json(self, result: OCALocatorResult, output_path: Path) -> None:
        """
        Export results to JSON format.

        Parameters
        ----------
        result : OCALocatorResult
            Results to export.
        output_path : Path
            Output file path.
        """
        logger.debug(f"Exporting results to JSON: {output_path}")

        # Convert to dictionary
        data = {
            "query_time": result.query_time.isoformat(),
            "public_ip": {
                "ip": str(result.public_ip.ip),
                "timestamp": result.public_ip.timestamp.isoformat(),
            },
            "isp_info": {
                "asn": result.isp_info.asn,
                "as_name": result.isp_info.as_name,
                "ip": result.isp_info.ip,
                "bgp_prefix": result.isp_info.bgp_prefix,
                "country": result.isp_info.cc,
                "registry": result.isp_info.registry,
                "allocated": result.isp_info.allocated,
            },
            "oca_servers": [
                {
                    "domain": oca.domain,
                    "ip_address": str(oca.ip_address),
                    "url": str(oca.url),
                    "city": oca.city,
                    "iata_code": oca.iata_code,
                    "latitude": oca.latitude,
                    "longitude": oca.longitude,
                    "asn": oca.asn,
                    "geocoding_provider": oca.geocoding_provider,
                    "geolocation_approach": oca.geolocation_approach,
                }
                for oca in result.oca_servers
            ],
            "total_ocas": len(result.oca_servers),
        }

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON export completed: {output_path}")

    def export_csv(self, result: OCALocatorResult, output_path: Path) -> None:
        """
        Export OCA servers to CSV format.

        Parameters
        ----------
        result : OCALocatorResult
            Results to export.
        output_path : Path
            Output file path.
        """
        logger.debug(f"Exporting results to CSV: {output_path}")

        # Prepare data for DataFrame
        data = []
        for oca in result.oca_servers:
            data.append({
                "domain": oca.domain,
                "ip_address": str(oca.ip_address),
                "city": oca.city or "",
                "iata_code": oca.iata_code or "",
                "latitude": oca.latitude or "",
                "longitude": oca.longitude or "",
                "asn": oca.asn or "",
                "geocoding_provider": oca.geocoding_provider or "",
                "geolocation_approach": oca.geolocation_approach or "",
                "url": str(oca.url),
                "user_ip": str(result.public_ip.ip),
                "user_isp": result.isp_info.as_name,
                "user_asn": result.isp_info.asn,
                "query_time": result.query_time.isoformat(),
            })

        # Create DataFrame and export
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding="utf-8")

        logger.info(f"CSV export completed: {output_path}")

    def export_excel(self, result: OCALocatorResult, output_path: Path) -> None:
        """
        Export results to Excel format with multiple sheets.

        Parameters
        ----------
        result : OCALocatorResult
            Results to export.
        output_path : Path
            Output file path.
        """
        logger.debug(f"Exporting results to Excel: {output_path}")

        # Create Excel writer
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Sheet 1: Summary
            summary_data = {
                "Property": [
                    "Query Time",
                    "Public IP",
                    "ISP Name",
                    "AS Number",
                    "Country",
                    "BGP Prefix",
                    "Total OCAs Found",
                ],
                "Value": [
                    result.query_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    str(result.public_ip.ip),
                    result.isp_info.as_name,
                    f"AS{result.isp_info.asn}",
                    result.isp_info.cc,
                    result.isp_info.bgp_prefix,
                    len(result.oca_servers),
                ],
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Sheet 2: OCA Servers
            oca_data = []
            for i, oca in enumerate(result.oca_servers, 1):
                oca_data.append({
                    "#": i,
                    "Domain": oca.domain,
                    "IP Address": str(oca.ip_address),
                    "City": oca.city or "",
                    "IATA Code": oca.iata_code or "",
                    "Latitude": oca.latitude or "",
                    "Longitude": oca.longitude or "",
                    "ASN": oca.asn or "",
                    "Geocoding Provider": oca.geocoding_provider or "",
                    "Geolocation Method": oca.geolocation_approach or "",
                    "Speed Test URL": str(oca.url),
                })

            if oca_data:
                oca_df = pd.DataFrame(oca_data)
                oca_df.to_excel(writer, sheet_name="OCA Servers", index=False)

                # Auto-adjust column widths
                worksheet = writer.sheets["OCA Servers"]
                for column in oca_df:
                    column_length = max(
                        oca_df[column].astype(str).map(len).max(),
                        len(str(column))
                    )
                    col_idx = oca_df.columns.get_loc(column)
                    worksheet.column_dimensions[
                        chr(65 + col_idx)
                    ].width = min(column_length + 2, 50)

        logger.info(f"Excel export completed: {output_path}")

    def export_markdown(self, result: OCALocatorResult, output_path: Path) -> None:
        """
        Export results to Markdown format.

        Parameters
        ----------
        result : OCALocatorResult
            Results to export.
        output_path : Path
            Output file path.
        """
        logger.debug(f"Exporting results to Markdown: {output_path}")

        # Build Markdown content
        md_content = [
            "# Netflix OCA Location Results",
            "",
            f"**Query Time:** {result.query_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Network Information",
            "",
            f"- **Public IP:** {result.public_ip.ip}",
            f"- **ISP:** {result.isp_info.as_name}",
            f"- **AS Number:** AS{result.isp_info.asn}",
            f"- **Country:** {result.isp_info.cc}",
            f"- **BGP Prefix:** {result.isp_info.bgp_prefix}",
            "",
            "## OCA Servers",
            "",
            f"Total OCAs found: **{len(result.oca_servers)}**",
            "",
        ]

        if result.oca_servers:
            # Add table header
            md_content.extend([
                "| # | Domain | IP Address | Location | IATA | Coordinates | ASN | Provider | Method |",
                "|---|--------|------------|----------|------|-------------|-----|----------|--------|",
            ])

            # Add table rows
            for i, oca in enumerate(result.oca_servers, 1):
                location = oca.city or "Unknown"
                iata = oca.iata_code or "-"
                coords = (
                    f"{oca.latitude:.4f}, {oca.longitude:.4f}"
                    if oca.latitude and oca.longitude
                    else "-"
                )

                asn_info = oca.asn or "-"
                provider = oca.geocoding_provider or "-"
                method = oca.geolocation_approach or "-"
                
                md_content.append(
                    f"| {i} | {oca.domain} | {oca.ip_address} | {location} | {iata} | {coords} | {asn_info} | {provider} | {method} |"
                )

            # Add detailed information
            md_content.extend([
                "",
                "### Detailed OCA Information",
                "",
            ])

            for i, oca in enumerate(result.oca_servers, 1):
                md_content.extend([
                    f"#### {i}. {oca.domain}",
                    "",
                    f"- **IP Address:** {oca.ip_address}",
                    f"- **Speed Test URL:** {oca.url}",
                ])

                if oca.city:
                    md_content.append(f"- **City:** {oca.city}")
                if oca.iata_code:
                    md_content.append(f"- **IATA Code:** {oca.iata_code}")
                if oca.latitude and oca.longitude:
                    md_content.append(
                        f"- **Coordinates:** {oca.latitude:.6f}, {oca.longitude:.6f}"
                    )

                md_content.append("")

        else:
            md_content.append("*No OCA servers were found for your network.*")

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        logger.info(f"Markdown export completed: {output_path}")

    def format_table_for_terminal(self, result: OCALocatorResult) -> str:
        """
        Format results as a simple text table for terminal output.

        Parameters
        ----------
        result : OCALocatorResult
            Results to format.

        Returns
        -------
        str
            Formatted table string.
        """
        if not result.oca_servers:
            return "No OCA servers found."

        # Create DataFrame for easy formatting
        data = []
        for oca in result.oca_servers:
            data.append({
                "Domain": oca.domain,
                "IP Address": str(oca.ip_address),
                "Location": oca.city or "Unknown",
                "IATA": oca.iata_code or "-",
            })

        df = pd.DataFrame(data)
        return df.to_string(index=False)
