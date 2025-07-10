"""Integration tests for the complete scraper system."""

import http.server
import socket
import socketserver
import threading
import time
from contextlib import suppress
from typing import Any
from unittest.mock import patch

import pytest

from src.tools import create_default_scraper, discover


class TestIntegration:
    """Integration tests using a real HTTP server."""

    port: int
    server: socketserver.TCPServer | None
    server_thread: threading.Thread | None
    test_html: str

    @classmethod
    def setup_class(cls) -> None:
        """Set up a test HTTP server."""
        cls.test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Company Careers</title>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "JobPosting",
                "url": "/jobs/software-engineer",
                "title": "Software Engineer",
                "hiringOrganization": {
                    "@type": "Organization",
                    "name": "Test Company"
                }
            }
            </script>
        </head>
        <body>
            <h1>Join Our Team</h1>
            <div id="jobs">
                <a href="/jobs/123">Frontend Developer</a>
                <a href="/careers/456">Backend Engineer</a>
                <a href="/openings/789">DevOps Engineer</a>
                <a href="/about">About Us</a>
                <a href="/contact">Contact</a>
            </div>
        </body>
        </html>
        """

        # Start test server with dynamic port
        cls.port = cls._find_free_port()
        cls.server = None
        cls.server_thread = None
        cls._start_server()

    @classmethod
    def teardown_class(cls) -> None:
        """Tear down the test HTTP server."""
        if cls.server:
            with suppress(Exception):
                cls.server.shutdown()
                cls.server.server_close()
            cls.server = None

        if cls.server_thread:
            with suppress(Exception):
                cls.server_thread.join(timeout=5.0)
            cls.server_thread = None

    @classmethod
    def _find_free_port(cls) -> int:
        """Find a free port to use for the test server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            port: int = s.getsockname()[1]
        return port

    @classmethod
    def _start_server(cls) -> None:
        """Start the test HTTP server."""

        class TestHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(TestIntegration.test_html.encode())

            def log_message(self, format: str, *args: Any) -> None:
                # Suppress server logs
                pass

        # Retry with different ports if needed
        max_retries = 5
        for attempt in range(max_retries):
            try:
                cls.server = socketserver.TCPServer(("", cls.port), TestHandler)
                cls.server.allow_reuse_address = True
                cls.server_thread = threading.Thread(target=cls.server.serve_forever)
                cls.server_thread.daemon = True
                cls.server_thread.start()

                # Wait for server to start
                time.sleep(0.1)
                return
            except OSError:
                # Clean up any partial state
                if cls.server:
                    with suppress(Exception):
                        cls.server.server_close()
                    cls.server = None

                if attempt == max_retries - 1:
                    raise
                # Find a new port and try again
                cls.port = cls._find_free_port()
                time.sleep(0.1)

    @pytest.mark.asyncio
    async def test_end_to_end_scraping(self) -> None:
        """Test complete end-to-end scraping with real HTTP server."""
        scraper = create_default_scraper()

        try:
            # Only test HttpxFetcher to avoid Playwright complexity in tests
            scraper.fetchers = [scraper.fetchers[0]]  # Keep only HttpxFetcher

            url = f"http://localhost:{self.__class__.port}"
            result = await scraper.discover(url)

            # Should find job-related links
            expected_links = [
                f"http://localhost:{self.__class__.port}/careers/456",
                f"http://localhost:{self.__class__.port}/jobs/123",
                f"http://localhost:{self.__class__.port}/jobs/software-engineer",
                f"http://localhost:{self.__class__.port}/openings/789",
            ]

            assert len(result) == len(expected_links)
            for link in expected_links:
                assert link in result

            # Should not find non-job links
            assert f"http://localhost:{self.__class__.port}/about" not in result
            assert f"http://localhost:{self.__class__.port}/contact" not in result

        finally:
            await scraper.cleanup()

    def test_synchronous_discover(self) -> None:
        """Test synchronous discover function."""
        url = f"http://localhost:{self.__class__.port}"

        # Mock to use only HttpxFetcher
        with patch("src.tools.scraper.create_default_scraper") as mock_create:
            scraper = create_default_scraper()
            scraper.fetchers = [scraper.fetchers[0]]  # Keep only HttpxFetcher
            mock_create.return_value = scraper

            result = discover(url)

            # Should find job-related links
            expected_links = [
                f"http://localhost:{self.__class__.port}/careers/456",
                f"http://localhost:{self.__class__.port}/jobs/123",
                f"http://localhost:{self.__class__.port}/jobs/software-engineer",
                f"http://localhost:{self.__class__.port}/openings/789",
            ]

            assert len(result) == len(expected_links)
            for link in expected_links:
                assert link in result

    @pytest.mark.asyncio
    async def test_custom_scraper_configuration(self) -> None:
        """Test scraper with custom configuration."""
        from src.tools.fetchers.httpx_fetcher import HttpxFetcher
        from src.tools.filters.job_link_filter import JobLinkFilter
        from src.tools.parsers.html_parser import HtmlParser
        from src.tools.parsers.json_parser import JsonParser
        from src.tools.types import Fetcher, Parser

        # Custom filter that only matches /jobs/ paths
        custom_filter = JobLinkFilter(
            job_patterns=[r"/jobs/"], job_boards=[], excludes=[r"/about", r"/contact"]
        )

        fetchers: list[Fetcher] = [HttpxFetcher()]
        parsers: list[Parser] = [HtmlParser(custom_filter), JsonParser(custom_filter)]

        from src.tools.scraper import Scraper

        scraper = Scraper(fetchers, parsers, custom_filter)

        try:
            url = f"http://localhost:{TestIntegration.port}"
            result = await scraper.discover(url)

            # Should only find /jobs/ links
            expected_links = [
                f"http://localhost:{self.__class__.port}/jobs/123",
                f"http://localhost:{self.__class__.port}/jobs/software-engineer",
            ]

            assert len(result) == len(expected_links)
            for link in expected_links:
                assert link in result

            # Should not find /careers/ or /openings/ links
            assert f"http://localhost:{self.__class__.port}/careers/456" not in result
            assert f"http://localhost:{self.__class__.port}/openings/789" not in result

        finally:
            await scraper.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling_integration(self) -> None:
        """Test error handling in integration scenario."""
        scraper = create_default_scraper()

        try:
            # Test with non-existent URL
            result = await scraper.discover("http://localhost:99999/nonexistent")

            # Should return empty list, not raise exception
            assert result == []

        finally:
            await scraper.cleanup()
