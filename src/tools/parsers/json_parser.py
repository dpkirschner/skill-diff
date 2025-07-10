"""Parser implementations for extracting links from content."""

import json
import re
from urllib.parse import urljoin

from src.tools.types import URL, LinkFilter

from .parser import BaseParser


class JsonParser(BaseParser):
    """Parser for extracting links from JSON content."""

    def __init__(self, link_filter: LinkFilter):
        """Initialize the JsonParser.

        Args:
            link_filter: Filter to apply to extracted links
        """
        super().__init__(link_filter)

    def extract_links(self, content: str, base_url: URL) -> set[URL]:
        """Extract links from JSON or arbitrary text content.

        Args:
            content: JSON or text content to parse
            base_url: Base URL for resolving relative links

        Returns:
            Set of absolute URLs that match the filter
        """
        links = set()

        # Try to parse as JSON first
        try:
            data = json.loads(content)
            json_links = self._extract_urls_from_json(data, base_url)
            links.update(json_links)
        except json.JSONDecodeError:
            # If not valid JSON, use regex to find URLs in text
            text_links = self._extract_urls_from_text(content, base_url)
            links.update(text_links)

        # Filter and return links
        return self.filter_links(links)

    def _extract_urls_from_text(self, text: str, base_url: URL) -> set[URL]:
        """Extract URLs from arbitrary text using regex."""
        links = set()

        # Pattern to match URLs
        url_pattern = r"(?:https?://|www\.|/)[\w\-\./_~:/?#[\]@!$&\'()*+,;=]+"

        matches = re.findall(url_pattern, text)
        for match in matches:
            if self._is_url_like(match):
                absolute_url = urljoin(base_url, match)
                links.add(absolute_url)

        return links
