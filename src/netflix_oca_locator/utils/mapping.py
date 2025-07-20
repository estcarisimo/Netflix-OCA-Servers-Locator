"""
Map generation utilities.

This module provides functionality to create interactive maps
showing OCA server locations.
"""

from __future__ import annotations

from pathlib import Path

import folium
from folium import plugins
from loguru import logger

from ..config.settings import Settings
from ..core.models import OCALocatorResult, OCAServer


class MapGenerator:
    """
    Generate interactive maps showing OCA locations.

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
        """Initialize map generator."""
        self.settings = settings

    def create_oca_map(
        self,
        result: OCALocatorResult,
        output_path: Path | None = None,
    ) -> Path:
        """
        Create an interactive map showing OCA locations.

        Parameters
        ----------
        result : OCALocatorResult
            Complete OCA locator result.
        output_path : Optional[Path]
            Output path for the HTML map file.

        Returns
        -------
        Path
            Path to the generated map file.
        """
        # Determine output path
        if output_path is None:
            output_dir = Path(self.settings.export_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "oca_locations_map.html"

        # Get OCAs with coordinates
        located_ocas = [oca for oca in result.oca_servers if oca.latitude and oca.longitude]

        if not located_ocas:
            logger.warning("No OCAs with location data found, creating empty map")

        # Create base map
        map_center = self._calculate_center(located_ocas)
        oca_map = folium.Map(
            location=map_center,
            zoom_start=self.settings.map_zoom,
            tiles="OpenStreetMap",
        )

        # Add user location marker
        self._add_user_marker(oca_map, result)

        # Add OCA markers
        for oca in located_ocas:
            self._add_oca_marker(oca_map, oca)

        # Add connection lines
        if located_ocas:
            self._add_connection_lines(oca_map, result, located_ocas)

        # Add controls
        self._add_map_controls(oca_map)

        # Save map
        oca_map.save(str(output_path))
        logger.info(f"Map saved to {output_path}")

        return output_path

    def _calculate_center(self, ocas: list[OCAServer]) -> tuple[float, float]:
        """
        Calculate the center point for the map.

        Parameters
        ----------
        ocas : List[OCAServer]
            List of OCA servers with coordinates.

        Returns
        -------
        Tuple[float, float]
            Center coordinates (lat, lon).
        """
        if not ocas:
            # Default to US center if no OCAs
            return (39.8283, -98.5795)

        # Calculate average position
        lats = [oca.latitude for oca in ocas if oca.latitude]
        lons = [oca.longitude for oca in ocas if oca.longitude]

        if lats and lons:
            return (sum(lats) / len(lats), sum(lons) / len(lons))

        return (39.8283, -98.5795)

    def _add_user_marker(self, oca_map: folium.Map, result: OCALocatorResult) -> None:
        """
        Add user location marker to the map.

        Parameters
        ----------
        oca_map : folium.Map
            Map instance.
        result : OCALocatorResult
            OCA locator result with user info.
        """
        # For now, we'll add a marker for the user's ISP
        # In a real implementation, we might geocode the user's IP

        # Add a distinctive marker for user
        # Since we don't have user coordinates, we'll skip this for now
        # In production, we'd geocode the IP or use browser geolocation

    def _add_oca_marker(self, oca_map: folium.Map, oca: OCAServer) -> None:
        """
        Add OCA server marker to the map.

        Parameters
        ----------
        oca_map : folium.Map
            Map instance.
        oca : OCAServer
            OCA server to add.
        """
        if not (oca.latitude and oca.longitude):
            return

        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4>Netflix OCA Server</h4>
            <b>Domain:</b> {oca.domain}<br>
            <b>IP:</b> {oca.ip_address}<br>
            <b>Location:</b> {oca.city or 'Unknown'}<br>
            {f'<b>IATA:</b> {oca.iata_code}<br>' if oca.iata_code else ''}
            <b>Coordinates:</b> {oca.latitude:.4f}, {oca.longitude:.4f}
        </div>
        """

        # Add marker
        folium.Marker(
            location=[oca.latitude, oca.longitude],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{oca.city or oca.domain}",
            icon=folium.Icon(color="red", icon="server", prefix="fa"),
        ).add_to(oca_map)

    def _add_connection_lines(
        self,
        oca_map: folium.Map,
        result: OCALocatorResult,
        ocas: list[OCAServer],
    ) -> None:
        """
        Add connection lines between OCAs.

        Parameters
        ----------
        oca_map : folium.Map
            Map instance.
        result : OCALocatorResult
            OCA locator result.
        ocas : List[OCAServer]
            List of OCA servers with coordinates.
        """
        # Add lines connecting all OCAs (showing the CDN network)
        if len(ocas) > 1:
            coordinates = [
                [oca.latitude, oca.longitude]
                for oca in ocas
                if oca.latitude and oca.longitude
            ]

            # Create a subtle network visualization
            for i, coord1 in enumerate(coordinates):
                for coord2 in coordinates[i + 1 :]:
                    folium.PolyLine(
                        locations=[coord1, coord2],
                        color="#ff0000",
                        weight=1,
                        opacity=0.3,
                    ).add_to(oca_map)

    def _add_map_controls(self, oca_map: folium.Map) -> None:
        """
        Add controls and plugins to the map.

        Parameters
        ----------
        oca_map : folium.Map
            Map instance.
        """
        # Add fullscreen control
        plugins.Fullscreen().add_to(oca_map)

        # Add measurement control
        plugins.MeasureControl().add_to(oca_map)

        # Add minimap
        minimap = plugins.MiniMap(toggle_display=True)
        oca_map.add_child(minimap)

        # Add title
        title_html = """
        <div style="position: fixed;
                    top: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    z-index: 1000;
                    background-color: white;
                    padding: 10px;
                    border: 2px solid #666;
                    border-radius: 5px;
                    font-family: Arial;
                    font-size: 16px;
                    font-weight: bold;">
            Netflix OCA Server Locations
        </div>
        """
        oca_map.get_root().html.add_child(folium.Element(title_html))
