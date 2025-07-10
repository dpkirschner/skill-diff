"""Base parser class for common functionality."""

import logging
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urljoin

from src.tools.types import URL, LinkFilter

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for parsers."""

    def __init__(self, link_filter: LinkFilter) -> None:
        """Initialize the base parser.

        Args:
            link_filter: Filter to apply to extracted links
        """
        self.link_filter = link_filter

    @abstractmethod
    def extract_links(self, content: str, base_url: URL) -> set[URL]:
        """Extract links from the given content.

        Args:
            content: Content to parse (HTML, JSON, or other formats)
            base_url: Base URL for resolving relative links

        Returns:
            Set of absolute URLs found in the content
        """
        ...

    def __repr__(self) -> str:
        """Return string representation of the parser."""
        return f"{self.__class__.__name__}(filter={self.link_filter.__class__.__name__})"

    def _is_url_like(self, text: str) -> bool:
        """Check if a string looks like a URL.

        Common implementation that can be used by concrete parsers.

        Args:
            text: String to check

        Returns:
            True if the string looks like a URL, False otherwise
        """
        return text.startswith(("http://", "https://", "/", "./", "../")) or (
            "." in text and "/" in text and len(text) > 5
        )

    def _extract_urls_from_json(self, data: Any, base_url: URL) -> set[URL]:
        """Recursively extract URLs from JSON data.

        Common implementation that can be used by concrete parsers.

        Args:
            data: JSON data to extract URLs from
            base_url: Base URL for resolving relative links

        Returns:
            Set of absolute URLs found in the JSON data
        """
        links = set()

        if isinstance(data, dict):
            for value in data.values():
                links.update(self._extract_urls_from_json(value, base_url))
        elif isinstance(data, list):
            for item in data:
                links.update(self._extract_urls_from_json(item, base_url))
        elif isinstance(data, str) and self._is_url_like(data):
            absolute_url = urljoin(base_url, data)
            links.add(absolute_url)

        return links

    def filter_links(self, links: set[URL]) -> set[URL]:
        """Apply the filter to a set of links.

        Args:
            links: Set of URLs to filter

        Returns:
            Set of URLs that match the filter criteria
        """
        return {link for link in links if self.link_filter.looks_like_target(link)}

    def count_links(self, content: str, base_url: URL) -> int:
        """Count the number of links that would be extracted from content.

        Args:
            content: Content to parse
            base_url: Base URL for resolving relative links

        Returns:
            Number of links that would be extracted
        """
        return len(self.extract_links(content, base_url))
