"""Base filter class for common functionality."""

import logging
from abc import ABC, abstractmethod

from src.tools.types import URL

logger = logging.getLogger(__name__)


class BaseFilter(ABC):
    """Abstract base class for URL filters."""

    @abstractmethod
    def looks_like_target(self, url: URL) -> bool:
        """Check if a URL looks like a target link.

        Args:
            url: The URL to check

        Returns:
            True if the URL matches target patterns, False otherwise
        """
        ...

    def __repr__(self) -> str:
        """Return string representation of the filter."""
        return f"{self.__class__.__name__}()"

    def filter_urls(self, urls: list[URL]) -> list[URL]:
        """Filter a list of URLs, keeping only those that match the target criteria.

        Args:
            urls: List of URLs to filter

        Returns:
            List of URLs that match the target criteria
        """
        return [url for url in urls if self.looks_like_target(url)]

    def count_matches(self, urls: list[URL]) -> int:
        """Count how many URLs in a list match the target criteria.

        Args:
            urls: List of URLs to check

        Returns:
            Number of URLs that match the target criteria
        """
        return sum(1 for url in urls if self.looks_like_target(url))
