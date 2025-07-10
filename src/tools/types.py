"""Shared types and protocols for the scraper package."""

from typing import Protocol, runtime_checkable

URL = str


class FetchError(Exception):
    """Raised when a fetcher fails to retrieve content."""

    pass


@runtime_checkable
class Fetcher(Protocol):
    """Protocol for fetching content from URLs."""

    async def get(self, url: URL) -> str:
        """Fetch content from the given URL.

        Args:
            url: The URL to fetch content from

        Returns:
            The content as a string

        Raises:
            FetchError: If the fetch operation fails
        """
        ...


@runtime_checkable
class Parser(Protocol):
    """Protocol for extracting links from content."""

    def extract_links(self, content: str, base_url: URL) -> set[URL]:
        """Extract links from the given content.

        Args:
            content: HTML, JSON, or other content to parse
            base_url: Base URL for resolving relative links

        Returns:
            Set of absolute URLs found in the content
        """
        ...


@runtime_checkable
class LinkFilter(Protocol):
    """Protocol for filtering URLs based on patterns."""

    def looks_like_target(self, url: URL) -> bool:
        """Check if a URL looks like a target link.

        Args:
            url: The URL to check

        Returns:
            True if the URL matches target patterns, False otherwise
        """
        ...
