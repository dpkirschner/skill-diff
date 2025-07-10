"""Base fetcher class for common functionality."""

import logging
from abc import ABC, abstractmethod

from src.tools.types import URL

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for fetchers."""

    def __init__(self, timeout: float) -> None:
        """Initialize the base fetcher.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    @abstractmethod
    async def get(self, url: URL) -> str:
        """Fetch content from the given URL.

        Args:
            url: The URL to fetch

        Returns:
            The response content as a string

        Raises:
            FetchError: If the request fails
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources used by the fetcher."""
        ...

    def __repr__(self) -> str:
        """Return string representation of the fetcher."""
        return f"{self.__class__.__name__}(timeout={self.timeout})"
