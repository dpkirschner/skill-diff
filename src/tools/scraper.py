"""Main scraper orchestrator that coordinates fetchers and parsers."""

import asyncio
import logging

from src.tools.fetchers.httpx_fetcher import HttpxFetcher
from src.tools.fetchers.playwright_fetcher import PlaywrightFetcher
from src.tools.filters.job_link_filter import JobLinkFilter
from src.tools.parsers.html_parser import HtmlParser
from src.tools.parsers.json_parser import JsonParser
from src.tools.types import URL, Fetcher, FetchError, LinkFilter, Parser

logger = logging.getLogger(__name__)


class Scraper:
    """Main scraper orchestrator that coordinates fetchers and parsers."""

    def __init__(
        self,
        fetchers: list[Fetcher],
        parsers: list[Parser],
        link_filter: LinkFilter,
    ):
        """Initialize the Scraper.

        Args:
            fetchers: List of fetchers to try in order
            parsers: List of parsers to apply to fetched content
            link_filter: Filter to apply to extracted links
        """
        self.fetchers = fetchers
        self.parsers = parsers
        self.link_filter = link_filter

    async def discover(self, url: URL) -> list[str]:
        """Discover job URLs from the given URL.

        Tries each fetcher in order until one succeeds, then applies all parsers
        to the fetched content to extract job URLs.

        Args:
            url: The URL to scrape for job links

        Returns:
            Sorted list of unique job URLs found
        """
        all_links: set[URL] = set()

        for fetcher in self.fetchers:
            try:
                logger.debug(f"Trying fetcher {fetcher.__class__.__name__} for {url}")
                content = await fetcher.get(url)

                # Apply all parsers to the fetched content
                for parser in self.parsers:
                    try:
                        links = parser.extract_links(content, url)
                        all_links.update(links)
                        logger.debug(f"Parser {parser.__class__.__name__} found {len(links)} links")
                    except Exception as e:
                        logger.debug(f"Parser {parser.__class__.__name__} failed: {e}")

                # If we found any links, stop trying other fetchers
                if all_links:
                    break

            except FetchError as e:
                logger.debug(f"Fetcher {fetcher.__class__.__name__} failed: {e}")
                continue
            except Exception as e:
                logger.debug(f"Unexpected error with fetcher {fetcher.__class__.__name__}: {e}")
                continue

        # Return sorted list of unique URLs
        return sorted(all_links)

    async def cleanup(self) -> None:
        """Clean up resources used by fetchers."""
        for fetcher in self.fetchers:
            if hasattr(fetcher, "cleanup"):
                try:
                    await fetcher.cleanup()
                except Exception as e:
                    logger.debug(f"Error cleaning up fetcher {fetcher.__class__.__name__}: {e}")


def create_default_scraper() -> Scraper:
    """Create a scraper with default configuration.

    Returns:
        Scraper instance with HttpxFetcher, PlaywrightFetcher, and default parsers
    """
    # Create link filter
    link_filter = JobLinkFilter()

    # Create fetchers
    fetchers: list[Fetcher] = [HttpxFetcher(), PlaywrightFetcher()]

    # Create parsers
    parsers: list[Parser] = [HtmlParser(link_filter), JsonParser(link_filter)]

    return Scraper(fetchers, parsers, link_filter)


def discover(url: str) -> list[str]:
    """Synchronous convenience function for discovering job URLs.

    Args:
        url: The URL to scrape for job links

    Returns:
        Sorted list of unique job URLs found
    """

    async def _discover() -> list[str]:
        scraper = create_default_scraper()
        try:
            return await scraper.discover(url)
        finally:
            await scraper.cleanup()

    return asyncio.run(_discover())
