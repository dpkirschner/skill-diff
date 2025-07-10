"""Tests for playwright fetcher implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.fetchers.playwright_fetcher import PlaywrightFetcher
from src.tools.types import FetchError


class TestPlaywrightFetcher:
    """Tests for PlaywrightFetcher."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Test successful Playwright fetch."""
        fetcher = PlaywrightFetcher()

        with patch("src.tools.fetchers.playwright_fetcher.async_playwright") as mock_playwright_func:
            mock_playwright_context = AsyncMock()
            mock_playwright_func.return_value = mock_playwright_context

            mock_playwright_instance = AsyncMock()
            mock_playwright_context.start.return_value = mock_playwright_instance

            mock_browser = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser

            mock_page = AsyncMock()
            mock_browser.new_page.return_value = mock_page
            mock_page.content.return_value = "<html>Test content</html>"
            mock_page.on = MagicMock()

            result = await fetcher.get("https://example.com")

            assert result == "<html>Test content</html>"
            mock_page.goto.assert_called_once()
            mock_page.wait_for_load_state.assert_called_once()

        await fetcher.cleanup()

    @pytest.mark.asyncio
    async def test_response_capture(self) -> None:
        """Test JSON response capture."""
        fetcher = PlaywrightFetcher()

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text.return_value = '{"jobs": [{"id": 1}]}'
        mock_response.url = "https://api.example.com/jobs"

        await fetcher._handle_response(mock_response)

        assert '{"jobs": [{"id": 1}]}' in fetcher._captured_responses

    @pytest.mark.asyncio
    async def test_response_capture_non_json(self) -> None:
        """Test that non-JSON responses are ignored."""
        fetcher = PlaywrightFetcher()

        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com"

        await fetcher._handle_response(mock_response)

        assert len(fetcher._captured_responses) == 0

    @pytest.mark.asyncio
    async def test_fetch_error(self) -> None:
        """Test Playwright fetch error handling."""
        fetcher = PlaywrightFetcher()

        with patch("src.tools.fetchers.playwright_fetcher.async_playwright") as mock_playwright_func:
            mock_playwright_context = AsyncMock()
            mock_playwright_func.return_value = mock_playwright_context

            mock_playwright_instance = AsyncMock()
            mock_playwright_context.start.return_value = mock_playwright_instance

            mock_browser = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser

            mock_page = AsyncMock()
            mock_browser.new_page.return_value = mock_page
            mock_page.goto.side_effect = Exception("Network error")
            mock_page.on = MagicMock()

            with pytest.raises(FetchError) as exc_info:
                await fetcher.get("https://example.com")

            assert "Playwright error" in str(exc_info.value)

        await fetcher.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        """Test cleanup functionality."""
        fetcher = PlaywrightFetcher()

        with patch("src.tools.fetchers.playwright_fetcher.async_playwright") as mock_playwright_func:
            mock_playwright_context = AsyncMock()
            mock_playwright_func.return_value = mock_playwright_context

            mock_playwright_instance = AsyncMock()
            mock_playwright_context.start.return_value = mock_playwright_instance

            mock_browser = AsyncMock()
            mock_playwright_instance.chromium.launch.return_value = mock_browser

            # Force browser creation
            await fetcher._get_browser()

            await fetcher.cleanup()
            mock_browser.close.assert_called_once()
