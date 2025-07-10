"""Tests for httpx fetcher implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.tools.fetchers.httpx_fetcher import HttpxFetcher
from src.tools.types import FetchError


class TestHttpxFetcher:
    """Tests for HttpxFetcher."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Test successful HTTP fetch."""
        fetcher = HttpxFetcher()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.text = "<html>Test content</html>"
            mock_client.get.return_value = mock_response

            result = await fetcher.get("https://example.com")

            assert result == "<html>Test content</html>"
            mock_client.get.assert_called_once_with("https://example.com")

        await fetcher.cleanup()

    @pytest.mark.asyncio
    async def test_http_error(self) -> None:
        """Test HTTP error handling."""
        fetcher = HttpxFetcher()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_client.get.side_effect = httpx.HTTPError("404 Not Found")

            with pytest.raises(FetchError) as exc_info:
                await fetcher.get("https://example.com/notfound")

            assert "HTTP error" in str(exc_info.value)

        await fetcher.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        """Test cleanup functionality."""
        fetcher = HttpxFetcher()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Force client creation
            await fetcher._get_client()

            await fetcher.cleanup()
            mock_client.aclose.assert_called_once()
