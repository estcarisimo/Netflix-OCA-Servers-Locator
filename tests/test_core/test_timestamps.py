"""
Regression tests for timezone-aware timestamps.

The models used to default to `datetime.utcnow()`, which is deprecated, scheduled
for removal, and returned a *naive* datetime that was UTC only by convention.
They now use `datetime.now(timezone.utc)`, which is explicit.

That changes serialised output: `isoformat()` gains a `+00:00` offset. These
tests pin that format so it cannot drift again unnoticed.

See https://github.com/estcarisimo/Netflix-OCA-Servers-Locator/issues/22.
"""

import json
from datetime import datetime, timezone

import pytest

from netflix_oca_locator.config.settings import Settings
from netflix_oca_locator.core.models import OCALocatorResult, PublicIPInfo
from netflix_oca_locator.utils.formatters import ResultFormatter


class TestTimestampsAreAware:
    """Default timestamps must carry explicit UTC tzinfo."""

    def test_public_ip_timestamp_is_aware(self):
        info = PublicIPInfo(ip="203.0.113.1")
        assert info.timestamp.tzinfo is not None
        assert info.timestamp.utcoffset() == timezone.utc.utcoffset(None)

    def test_query_time_is_aware(self, mock_public_ip, mock_isp_info, mock_oca_servers):
        result = OCALocatorResult(
            public_ip=mock_public_ip,
            isp_info=mock_isp_info,
            oca_servers=mock_oca_servers,
            fast_com_token="tz_token",
        )
        assert result.query_time.tzinfo is not None
        assert result.query_time.utcoffset() == timezone.utc.utcoffset(None)

    def test_no_deprecation_warning_on_construction(self, recwarn):
        """`datetime.utcnow()` raises a DeprecationWarning on modern Pythons."""
        PublicIPInfo(ip="203.0.113.2")

        offenders = [w for w in recwarn.list if "utcnow" in str(w.message)]
        assert not offenders, f"utcnow deprecation warning raised: {offenders}"


class TestSerialisedFormat:
    """The exported string format is a contract; pin it."""

    def test_isoformat_carries_utc_offset(self):
        info = PublicIPInfo(ip="203.0.113.3")
        rendered = info.timestamp.isoformat()
        assert rendered.endswith("+00:00"), rendered

    def test_json_export_timestamps_are_offset_qualified(
        self, mock_oca_result, temp_export_dir, tz_settings
    ):
        out = temp_export_dir / "tz.json"
        ResultFormatter(tz_settings).export_json(mock_oca_result, out)

        data = json.loads(out.read_text())
        assert data["query_time"].endswith("+00:00")
        assert data["public_ip"]["timestamp"].endswith("+00:00")

        # Round-trips back to an aware datetime.
        parsed = datetime.fromisoformat(data["query_time"])
        assert parsed.tzinfo is not None

    def test_markdown_still_labels_utc_explicitly(
        self, mock_oca_result, temp_export_dir, tz_settings
    ):
        """
        The Markdown and XLSX exports format with `strftime('... UTC')`, which
        ignores tzinfo. Those must stay byte-identical to before the change.
        """
        out = temp_export_dir / "tz.md"
        ResultFormatter(tz_settings).export_markdown(mock_oca_result, out)

        content = out.read_text()
        expected = mock_oca_result.query_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        assert expected in content
        assert "+00:00" not in content


@pytest.fixture
def tz_settings():
    """Settings for export."""
    return Settings(debug=True)
