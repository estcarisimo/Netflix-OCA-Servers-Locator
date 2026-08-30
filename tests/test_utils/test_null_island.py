"""
Regression tests for coordinates of exactly 0.0.

`latitude` and `longitude` are `float | None`, with `None` meaning "unknown" and
0.0 a perfectly valid coordinate: the equator, and the prime meridian that runs
through Greenwich. Every consumer used to test them for truthiness, which
silently dropped an OCA at 0.0 from maps and wrote an empty cell into exports.

See https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/issues/9.
"""

import csv
import json

import pytest

from netflix_oca_locator.config.settings import Settings
from netflix_oca_locator.core.models import OCALocatorResult, OCAServer
from netflix_oca_locator.utils.formatters import ResultFormatter
from netflix_oca_locator.utils.mapping import MapGenerator


@pytest.fixture
def null_island_oca():
    """An OCA sitting exactly at 0.0, 0.0."""
    return OCAServer(
        domain="zero.nflxvideo.net",
        ip_address="198.45.48.9",
        url="https://zero.nflxvideo.net/speedtest",
        city="Null Island",
        iata_code="NUL",
        latitude=0.0,
        longitude=0.0,
    )


@pytest.fixture
def greenwich_oca():
    """A realistic case: a London OCA on the prime meridian, longitude 0.0."""
    return OCAServer(
        domain="lhr1.nflxvideo.net",
        ip_address="198.45.48.10",
        url="https://lhr1.nflxvideo.net/speedtest",
        city="London, UK",
        iata_code="LHR",
        latitude=51.4779,
        longitude=0.0,
    )


@pytest.fixture
def zero_result(mock_public_ip, mock_isp_info, null_island_oca, greenwich_oca):
    """A result whose OCAs all have at least one zero coordinate."""
    return OCALocatorResult(
        public_ip=mock_public_ip,
        isp_info=mock_isp_info,
        oca_servers=[null_island_oca, greenwich_oca],
        fast_com_token="test_token_zero",
    )


class TestZeroCoordinatesInExports:
    """Zero coordinates must survive every export format."""

    def test_json_keeps_zero(self, zero_result, temp_export_dir, settings):
        out = temp_export_dir / "zero.json"
        ResultFormatter(settings).export_json(zero_result, out)

        data = json.loads(out.read_text())
        ocas = {o["domain"]: o for o in data["oca_servers"]}

        assert ocas["zero.nflxvideo.net"]["latitude"] == 0.0
        assert ocas["zero.nflxvideo.net"]["longitude"] == 0.0
        assert ocas["lhr1.nflxvideo.net"]["longitude"] == 0.0

    def test_csv_writes_zero_not_empty_string(self, zero_result, temp_export_dir, settings):
        out = temp_export_dir / "zero.csv"
        ResultFormatter(settings).export_csv(zero_result, out)

        rows = {r["domain"]: r for r in csv.DictReader(out.open())}

        # The bug wrote "" here because `0.0 or ""` evaluates to "".
        assert rows["zero.nflxvideo.net"]["latitude"] == "0.0"
        assert rows["zero.nflxvideo.net"]["longitude"] == "0.0"
        assert rows["lhr1.nflxvideo.net"]["longitude"] == "0.0"

    def test_markdown_renders_zero_coordinates(self, zero_result, temp_export_dir, settings):
        out = temp_export_dir / "zero.md"
        ResultFormatter(settings).export_markdown(zero_result, out)

        content = out.read_text()
        # Previously rendered as "-" because of the truthiness check.
        assert "0.0000, 0.0000" in content
        assert "51.4779, 0.0000" in content


class TestZeroCoordinatesOnMap:
    """Zero coordinates must not be dropped from the map."""

    def test_map_includes_zero_coordinate_ocas(self, zero_result, temp_export_dir, settings):
        out = temp_export_dir / "zero_map.html"
        MapGenerator(settings).create_oca_map(zero_result, out)

        content = out.read_text()
        # Both OCAs should have produced markers.
        assert "zero.nflxvideo.net" in content
        assert "lhr1.nflxvideo.net" in content


class TestNoneStillMeansUnknown:
    """The fix must not make None look like a real coordinate."""

    def test_none_coordinates_still_omitted(
        self, mock_public_ip, mock_isp_info, temp_export_dir, settings
    ):
        unlocated = OCAServer(
            domain="unknown.nflxvideo.net",
            ip_address="198.45.48.11",
            url="https://unknown.nflxvideo.net/speedtest",
        )
        result = OCALocatorResult(
            public_ip=mock_public_ip,
            isp_info=mock_isp_info,
            oca_servers=[unlocated],
            fast_com_token="test_token_none",
        )

        out = temp_export_dir / "none.csv"
        ResultFormatter(settings).export_csv(result, out)

        row = next(iter(csv.DictReader(out.open())))
        assert row["latitude"] == ""
        assert row["longitude"] == ""


@pytest.fixture
def settings():
    """Settings for export and map generation."""
    return Settings(debug=True)
