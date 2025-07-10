"""Parser implementations for extracting links from content."""

import json
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.tools.types import URL, LinkFilter

from .parser import BaseParser

logger = logging.getLogger(__name__)


class HtmlParser(BaseParser):
    """Parser for extracting links from HTML content."""

    def __init__(self, link_filter: LinkFilter):
        """Initialize the HtmlParser.

        Args:
            link_filter: Filter to apply to extracted links
        """
        super().__init__(link_filter)

    def extract_links(self, html: str, base_url: URL) -> set[URL]:
        """Extract links from HTML content.

        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links

        Returns:
            Set of absolute URLs that match the filter
        """
        links = set()

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract links from anchor tags
            anchor_links = self._extract_anchor_links(soup, base_url)
            links.update(anchor_links)

            # Extract links from JSON-LD schema
            jsonld_links = self._extract_jsonld_links(soup, base_url)
            links.update(jsonld_links)

        except Exception as e:
            logger.debug(f"Error parsing HTML: {e}")

        # Filter and return links
        return self.filter_links(links)

    def _extract_anchor_links(self, soup: BeautifulSoup, base_url: URL) -> set[URL]:
        """Extract URLs from anchor tags."""
        links = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href:
                absolute_url = urljoin(base_url, href)
                links.add(absolute_url)

        return links

    def _extract_jsonld_links(self, soup: BeautifulSoup, base_url: URL) -> set[URL]:
        """Extract URLs from JSON-LD structured data."""
        links = set()

        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                if script.string:
                    data = json.loads(script.string)
                    script_links = self._extract_urls_from_json(data, base_url)
                    links.update(script_links)
            except json.JSONDecodeError:
                continue

        return links
