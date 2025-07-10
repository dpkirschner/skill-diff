"""Tests for json parser implementations."""

from src.tools.parsers.json_parser import JsonParser
from tests.unit.tools.conftest import MockLinkFilter


class TestJsonParser:
    """Tests for JsonParser."""

    def test_extract_from_json(self, json_parser: JsonParser, sample_json: str) -> None:
        """Test extraction from valid JSON."""
        links = json_parser.extract_links(sample_json, "https://example.com")

        assert "https://example.com/jobs/123" in links
        assert "https://example.com/careers/456" in links

    def test_extract_from_text(self, json_parser: JsonParser) -> None:
        """Test extraction from non-JSON text."""
        text_content = """
        Check out our jobs at /jobs/123 and /careers/456
        Visit https://example.com/positions/789 for more info
        """

        links = json_parser.extract_links(text_content, "https://example.com")

        assert "https://example.com/jobs/123" in links
        assert "https://example.com/careers/456" in links
        assert "https://example.com/positions/789" in links

    def test_nested_json_extraction(self, json_parser: JsonParser) -> None:
        """Test extraction from nested JSON structures."""
        json_content = """
        {
            "data": {
                "company": {
                    "careers": {
                        "openings": [
                            {"url": "/jobs/123"},
                            {"url": "/jobs/456"}
                        ]
                    }
                }
            }
        }
        """

        links = json_parser.extract_links(json_content, "https://example.com")

        assert "https://example.com/jobs/123" in links
        assert "https://example.com/jobs/456" in links

    def test_filter_applied(self, mock_rejecting_filter: MockLinkFilter, sample_json: str) -> None:
        """Test that link filter is applied."""
        parser = JsonParser(mock_rejecting_filter)
        links = parser.extract_links(sample_json, "https://example.com")

        assert len(links) == 0

    def test_url_like_detection(self, json_parser: JsonParser) -> None:
        """Test URL-like string detection."""
        # Test various URL-like strings
        assert json_parser._is_url_like("https://example.com/jobs/123")
        assert json_parser._is_url_like("/jobs/123")
        assert json_parser._is_url_like("./jobs/123")
        assert json_parser._is_url_like("../jobs/123")
        assert json_parser._is_url_like("example.com/jobs/123")

        # Test non-URL-like strings
        assert not json_parser._is_url_like("just text")
        assert not json_parser._is_url_like("123")
        assert not json_parser._is_url_like("test")
