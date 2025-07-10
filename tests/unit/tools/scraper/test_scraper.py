"""Tests for scraper orchestrator."""

from typing import Protocol
from unittest.mock import AsyncMock, patch

import pytest

from src.tools.scraper import Scraper, create_default_scraper, discover
from tests.unit.tools.conftest import MockFetcher, MockLinkFilter, MockParser


class MockFetcherFactory(Protocol):
    """Protocol for mock fetcher factory."""

    def __call__(self, *, content: str | None = None, should_fail: bool = False) -> MockFetcher: ...


class MockParserFactory(Protocol):
    """Protocol for mock parser factory."""

    def __call__(self, *, links: list[str] | None = None, should_fail: bool = False) -> MockParser: ...


class TestScraper:
    """Tests for Scraper orchestrator."""

    @pytest.mark.asyncio
    async def test_successful_discovery(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test successful job discovery."""
        fetcher = mock_fetcher_factory(content="<html>Test content</html>")
        parser = mock_parser_factory(
            links=["https://example.com/jobs/123", "https://example.com/careers/456"]
        )

        scraper = Scraper([fetcher], [parser], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert len(result) == 2
        assert "https://example.com/jobs/123" in result
        assert "https://example.com/careers/456" in result
        assert len(parser.extract_calls) == 1
        assert parser.extract_calls[0] == ("<html>Test content</html>", "https://example.com")

    @pytest.mark.asyncio
    async def test_fetcher_fallback(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test fallback to next fetcher on failure."""
        failing_fetcher = mock_fetcher_factory(should_fail=True)
        working_fetcher = mock_fetcher_factory(content="<html>Working content</html>")
        parser = mock_parser_factory(links=["https://example.com/jobs/123"])

        scraper = Scraper([failing_fetcher, working_fetcher], [parser], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert len(result) == 1
        assert "https://example.com/jobs/123" in result
        assert len(parser.extract_calls) == 1
        assert parser.extract_calls[0] == ("<html>Working content</html>", "https://example.com")

    @pytest.mark.asyncio
    async def test_multiple_parsers(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test multiple parsers are applied to same content."""
        fetcher = mock_fetcher_factory(content="<html>Test content</html>")
        parser1 = mock_parser_factory(links=["https://example.com/jobs/123"])
        parser2 = mock_parser_factory(links=["https://example.com/careers/456"])

        scraper = Scraper([fetcher], [parser1, parser2], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert len(result) == 2
        assert "https://example.com/jobs/123" in result
        assert "https://example.com/careers/456" in result
        assert len(parser1.extract_calls) == 1
        assert len(parser2.extract_calls) == 1

    @pytest.mark.asyncio
    async def test_parser_error_handling(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test graceful handling of parser errors."""
        fetcher = mock_fetcher_factory(content="<html>Test content</html>")
        failing_parser = mock_parser_factory(should_fail=True)
        working_parser = mock_parser_factory(links=["https://example.com/jobs/123"])

        scraper = Scraper([fetcher], [failing_parser, working_parser], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert len(result) == 1
        assert "https://example.com/jobs/123" in result

    @pytest.mark.asyncio
    async def test_no_links_found(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test behavior when no links are found."""
        fetcher1 = mock_fetcher_factory(content="<html>No links</html>")
        fetcher2 = mock_fetcher_factory(content="<html>Still no links</html>")
        parser = mock_parser_factory(links=[])

        scraper = Scraper([fetcher1, fetcher2], [parser], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert len(result) == 0
        # Should try both fetchers when no links found
        assert len(parser.extract_calls) == 2

    @pytest.mark.asyncio
    async def test_duplicate_link_removal(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test duplicate link removal."""
        fetcher = mock_fetcher_factory(content="<html>Test content</html>")
        parser1 = mock_parser_factory(
            links=["https://example.com/jobs/123", "https://example.com/careers/456"]
        )
        parser2 = mock_parser_factory(
            links=["https://example.com/jobs/123", "https://example.com/openings/789"]
        )

        scraper = Scraper([fetcher], [parser1, parser2], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert len(result) == 3
        assert "https://example.com/jobs/123" in result
        assert "https://example.com/careers/456" in result
        assert "https://example.com/openings/789" in result

    @pytest.mark.asyncio
    async def test_result_sorting(
        self,
        mock_fetcher_factory: MockFetcherFactory,
        mock_parser_factory: MockParserFactory,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test that results are sorted."""
        fetcher = mock_fetcher_factory(content="<html>Test content</html>")
        parser = mock_parser_factory(
            links=[
                "https://example.com/jobs/zebra",
                "https://example.com/jobs/alpha",
                "https://example.com/jobs/beta",
            ]
        )

        scraper = Scraper([fetcher], [parser], mock_link_filter)

        result = await scraper.discover("https://example.com")

        assert result == [
            "https://example.com/jobs/alpha",
            "https://example.com/jobs/beta",
            "https://example.com/jobs/zebra",
        ]

    @pytest.mark.asyncio
    async def test_cleanup(
        self,
        mock_fetcher: MockFetcher,
        mock_parser: MockParser,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test cleanup functionality."""
        scraper = Scraper([mock_fetcher], [mock_parser], mock_link_filter)

        await scraper.cleanup()

        assert mock_fetcher.cleanup_called

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(
        self,
        mock_fetcher: MockFetcher,
        mock_parser: MockParser,
        mock_link_filter: MockLinkFilter,
    ) -> None:
        """Test cleanup error handling."""
        with patch.object(mock_fetcher, "cleanup", AsyncMock(side_effect=Exception("Cleanup error"))):
            scraper = Scraper([mock_fetcher], [mock_parser], mock_link_filter)

            # Should not raise exception
            await scraper.cleanup()

    def test_create_default_scraper(self) -> None:
        """Test default scraper creation."""
        scraper = create_default_scraper()

        assert len(scraper.fetchers) == 2
        assert len(scraper.parsers) == 2
        assert scraper.link_filter is not None

        # Check fetcher types
        fetcher_types = [type(f).__name__ for f in scraper.fetchers]
        assert "HttpxFetcher" in fetcher_types
        assert "PlaywrightFetcher" in fetcher_types

        # Check parser types
        parser_types = [type(p).__name__ for p in scraper.parsers]
        assert "HtmlParser" in parser_types
        assert "JsonParser" in parser_types

    def test_discover_function(self) -> None:
        """Test synchronous discover function."""
        with patch("src.tools.scraper.create_default_scraper") as mock_create:
            mock_scraper = AsyncMock()
            mock_scraper.discover.return_value = ["https://example.com/jobs/123"]
            mock_create.return_value = mock_scraper

            result = discover("https://example.com")

            assert result == ["https://example.com/jobs/123"]
            mock_scraper.discover.assert_called_once_with("https://example.com")
            mock_scraper.cleanup.assert_called_once()
