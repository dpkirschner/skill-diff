"""Fetcher implementations for retrieving content from URLs."""

import logging

import httpx

from src.tools.config import STATIC_TIMEOUT
from src.tools.types import URL, FetchError

from .fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class HttpxFetcher(BaseFetcher):
    """Fetcher that uses httpx for static HTTP requests."""

    def __init__(self, timeout: float = STATIC_TIMEOUT):
        """Initialize the HttpxFetcher.

        Args:
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get(self, url: URL) -> str:
        """Fetch content from the given URL using httpx.

        Args:
            url: The URL to fetch

        Returns:
            The response content as a string

        Raises:
            FetchError: If the request fails
        """
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            raise FetchError(f"HTTP error fetching {url}: {e}") from e
        except Exception as e:
            raise FetchError(f"Unexpected error fetching {url}: {e}") from e

    async def cleanup(self) -> None:
        """Close the httpx client."""
        if self._client:
            await self._client.aclose()
            self._client = None
