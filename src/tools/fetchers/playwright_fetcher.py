import logging

from playwright.async_api import Browser, Response, async_playwright

from src.tools.config import NETWORK_TIMEOUT, PLAYWRIGHT_ARGS, PLAYWRIGHT_HEADLESS
from src.tools.types import URL, FetchError

from .fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class PlaywrightFetcher(BaseFetcher):
    """Fetcher that uses Playwright for JavaScript-rendered content."""

    def __init__(
        self,
        timeout: float = NETWORK_TIMEOUT,
        headless: bool = PLAYWRIGHT_HEADLESS,
        args: list[str] | None = None,
    ):
        """Initialize the PlaywrightFetcher.

        Args:
            timeout: Network timeout in seconds
            headless: Whether to run in headless mode
            args: Additional browser arguments
        """
        super().__init__(timeout)
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.headless = headless
        self.args = args or PLAYWRIGHT_ARGS
        self._browser: Browser | None = None
        self._captured_responses: list[str] = []

    async def _get_browser(self) -> Browser:
        """Get or create the Playwright browser."""
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=self.headless, args=self.args)
        return self._browser

    async def _handle_response(self, response: Response) -> None:
        """Handle network responses and capture relevant content."""
        try:
            if response.status == 200:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    text = await response.text()
                    if text:
                        self._captured_responses.append(text)
        except Exception as e:
            logger.debug(f"Error handling response from {response.url}: {e}")

    async def get(self, url: URL) -> str:
        """Fetch content from the given URL using Playwright.

        Args:
            url: The URL to fetch

        Returns:
            The page content as HTML, with captured JSON responses appended

        Raises:
            FetchError: If the request fails
        """
        try:
            browser = await self._get_browser()
            page = await browser.new_page()

            # Clear previous responses
            self._captured_responses.clear()

            # Set up response monitoring
            page.on("response", self._handle_response)

            # Navigate to the page
            await page.goto(url, timeout=self.timeout)

            # Wait for the page to load
            await page.wait_for_load_state("networkidle", timeout=self.timeout)

            # Get the page content
            content = await page.content()

            # Append captured JSON responses
            if self._captured_responses:
                content += "\n" + "\n".join(self._captured_responses)

            await page.close()
            return content

        except Exception as e:
            raise FetchError(f"Playwright error fetching {url}: {e}") from e

    async def cleanup(self) -> None:
        """Close the Playwright browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
