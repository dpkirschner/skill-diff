"""Unit tests for JobScraper."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from bs4 import BeautifulSoup

from src.agents.scraping.job_scraper import JobScraper


class TestJobScraper:
    """Test cases for JobScraper."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.scraper = JobScraper()
        self.base_url = "https://example.com/careers"

    def test_extract_anchor_links_basic(self) -> None:
        """Test basic anchor link extraction from HTML."""
        html = """
        <html>
            <body>
                <a href="/jobs/engineer">Software Engineer</a>
                <a href="https://jobs.ashbyhq.com/Company/123">External Job</a>
                <a href="/about">About Us</a>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        links = self.scraper._extract_anchor_links(soup, self.base_url)

        expected_links = {"https://example.com/jobs/engineer", "https://jobs.ashbyhq.com/Company/123"}

        assert links == expected_links

    def test_extract_anchor_links_relative_urls(self) -> None:
        """Test that relative URLs are converted to absolute."""
        html = """
        <html>
            <body>
                <a href="jobs/developer">Developer</a>
                <a href="/careers/manager">Manager</a>
                <a href="#section">Section Link</a>
            </body>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        links = self.scraper._extract_anchor_links(soup, self.base_url)

        expected_links = {"https://example.com/jobs/developer", "https://example.com/careers/manager"}

        assert links == expected_links

    def test_extract_schema_ld_links(self) -> None:
        """Test extraction of job links from JSON-LD schema."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "JobPosting",
                    "url": "https://example.com/jobs/software-engineer",
                    "title": "Software Engineer"
                }
                </script>
                <script type="application/ld+json">
                {
                    "jobs": [
                        {"jobUrl": "https://jobs.ashbyhq.com/Company/123"},
                        {"url": "https://example.com/careers/manager"}
                    ]
                }
                </script>
            </head>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        links = self.scraper._extract_schema_ld_links(soup, self.base_url)

        expected_links = {
            "https://example.com/jobs/software-engineer",
            "https://jobs.ashbyhq.com/Company/123",
            "https://example.com/careers/manager",
        }

        assert links == expected_links

    def test_extract_links_from_text(self) -> None:
        """Test extraction of job links from arbitrary text/JSON."""
        text = """
        {
            "jobs": [
                {"url": "https://jobs.ashbyhq.com/Sierra/123"},
                {"jobUrl": "https://lever.co/company/456"},
                {"link": "/careers/developer"}
            ],
            "other": "https://example.com/about"
        }
        """

        links = self.scraper._extract_links_from_text(text, self.base_url)

        expected_links = {
            "https://jobs.ashbyhq.com/Sierra/123",
            "https://lever.co/company/456",
            "https://example.com/careers/developer",
        }

        assert links == expected_links

    def test_looks_like_job_patterns(self) -> None:
        """Test job URL pattern matching."""
        test_cases = [
            ("https://example.com/jobs/engineer", True),
            ("https://example.com/careers/manager", True),
            ("https://example.com/openings/designer", True),
            ("https://example.com/positions/analyst", True),
            ("https://example.com/opportunities/lead", True),
            ("https://example.com/vacancies/intern", True),
            ("https://example.com/employment/specialist", True),
            ("https://example.com/hiring/coordinator", True),
            ("https://example.com/apply?job_id=123", True),
            ("https://example.com/careers?jobid=456", True),
            ("https://example.com/apply?gh_jid=789", True),
            ("https://lever.co/company/123?lever=track", True),
            ("https://example.com/about", False),
            ("https://example.com/blog", False),
            ("https://example.com/contact", False),
        ]

        for url, expected in test_cases:
            result = self.scraper._looks_like_job(url)
            assert result == expected, f"Expected {expected} for {url}, got {result}"

    def test_looks_like_job_board_domains(self) -> None:
        """Test job board domain matching."""
        test_cases = [
            ("https://jobs.ashbyhq.com/Company/123", True),
            ("https://jobs.lever.co/company/456", True),
            ("https://app.greenhouse.io/jobs/789", True),
            ("https://company.workday.com/job/123", True),
            ("https://company.bamboohr.com/jobs/456", True),
            ("https://jobs.smartrecruiters.com/Company/123", True),
            ("https://apply.workable.com/company/j/456", True),
            ("https://company.applytojob.com/apply/123", True),
            ("https://company.recruitee.com/o/position", True),
            ("https://jobs.teamtailor.com/company/123", True),
            ("https://github.com/user/repo", False),
            ("https://stackoverflow.com/jobs/123", True),  # This matches /jobs/ pattern
        ]

        for url, expected in test_cases:
            result = self.scraper._looks_like_job(url)
            assert result == expected, f"Expected {expected} for {url}, got {result}"

    def test_looks_like_job_excludes(self) -> None:
        """Test URL exclusion patterns."""
        excluded_urls = [
            "https://example.com/jobs#section",
            "javascript:void(0)",
            "mailto:jobs@company.com",
            "https://example.com/jobs/contact",
            "https://example.com/careers/about",
            "https://example.com/openings/privacy",
            "https://example.com/job.pdf",
            "https://example.com/careers.css",
            "https://example.com/jobs.js",
            "https://example.com/logo.png",
            "https://example.com/careers/press",
            "https://example.com/jobs/help",
            "https://example.com/careers/blog",
        ]

        for url in excluded_urls:
            assert not self.scraper._looks_like_job(url), f"Should exclude {url}"

    def test_parse_for_job_links_integration(self) -> None:
        """Test complete job link parsing from HTML."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@type": "JobPosting",
                    "url": "https://example.com/jobs/schema-job"
                }
                </script>
            </head>
            <body>
                <a href="/jobs/software-engineer">Software Engineer</a>
                <a href="https://jobs.ashbyhq.com/Company/123">External Job</a>
                <a href="/careers/product-manager">Product Manager</a>
                <a href="/about">About Us</a>
                <a href="/blog/post">Blog Post</a>
                <a href="mailto:jobs@company.com">Email</a>
                <a href="/openings/designer">Designer</a>
                <a href="/contact">Contact</a>
            </body>
        </html>
        """

        job_links = self.scraper._parse_for_job_links(html, self.base_url)

        expected_links = {
            "https://example.com/jobs/software-engineer",
            "https://jobs.ashbyhq.com/Company/123",
            "https://example.com/careers/product-manager",
            "https://example.com/openings/designer",
            "https://example.com/jobs/schema-job",
        }

        assert job_links == expected_links

    # Note: Async tests for _fetch_static would require pytest-asyncio
    # Skipping these for now as they're not critical for static HTML parsing functionality

    def test_sierra_sample_structure(self) -> None:
        """Test job URL extraction with Sierra.ai-like structure."""
        # This mimics the structure found in the sample.html
        html = """
        <script>
        {"jobs": [
            {"jobUrl": "https://jobs.ashbyhq.com/Sierra/123", "title": "Engineer"},
            {"jobUrl": "https://jobs.ashbyhq.com/Sierra/456", "title": "Manager"}
        ]}
        </script>
        <div>
            <a href="https://jobs.ashbyhq.com/Sierra/123">Software Engineer</a>
            <a href="https://jobs.ashbyhq.com/Sierra/456">Product Manager</a>
        </div>
        """

        job_links = self.scraper._parse_for_job_links(html, "https://sierra.ai/careers")

        expected_links = {"https://jobs.ashbyhq.com/Sierra/123", "https://jobs.ashbyhq.com/Sierra/456"}

        assert job_links == expected_links

    def test_handle_malformed_json_ld(self) -> None:
        """Test handling of malformed JSON-LD scripts."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                { malformed json here
                </script>
                <script type="application/ld+json">
                {
                    "valid": "json",
                    "jobUrl": "https://example.com/jobs/valid"
                }
                </script>
            </head>
        </html>
        """

        soup = BeautifulSoup(html, "html.parser")
        links = self.scraper._extract_schema_ld_links(soup, self.base_url)

        # Should only extract from valid JSON
        expected_links = {"https://example.com/jobs/valid"}

        assert links == expected_links

    @pytest.mark.asyncio
    async def test_handle_response_json_content(self) -> None:
        """Test _handle_response with JSON content containing job links."""
        # Mock response with JSON content
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.url = "https://api.example.com/jobs"
        mock_response.json = AsyncMock(
            return_value={
                "jobs": [
                    {"jobUrl": "https://jobs.ashbyhq.com/Company/123"},
                    {"url": "https://example.com/careers/engineer"},
                    {"link": "/jobs/developer"},
                ]
            }
        )

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response
        await self.scraper._handle_response(mock_response)

        # Verify job links were extracted
        expected_links = {
            "https://jobs.ashbyhq.com/Company/123",
            "https://example.com/careers/engineer",
            "https://api.example.com/jobs/developer",
        }
        assert self.scraper._xhr_links == expected_links

    @pytest.mark.asyncio
    async def test_handle_response_non_json_content(self) -> None:
        """Test _handle_response ignores non-JSON content."""
        # Mock response with HTML content
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "text/html"}

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response
        await self.scraper._handle_response(mock_response)

        # Verify no links were extracted
        assert self.scraper._xhr_links == set()

    @pytest.mark.asyncio
    async def test_handle_response_json_parse_error(self) -> None:
        """Test _handle_response handles JSON parsing errors gracefully."""
        # Mock response that fails JSON parsing
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0))

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response - should not raise exception
        await self.scraper._handle_response(mock_response)

        # Verify no links were extracted
        assert self.scraper._xhr_links == set()

    @pytest.mark.asyncio
    async def test_handle_response_network_error(self) -> None:
        """Test _handle_response handles network errors gracefully."""
        # Mock response that fails during JSON call
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(side_effect=Exception("Network error"))

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response - should not raise exception
        await self.scraper._handle_response(mock_response)

        # Verify no links were extracted
        assert self.scraper._xhr_links == set()

    @pytest.mark.asyncio
    async def test_handle_response_empty_json(self) -> None:
        """Test _handle_response with empty JSON response."""
        # Mock response with empty JSON
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.url = "https://api.example.com/jobs"
        mock_response.json = AsyncMock(return_value={})

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response
        await self.scraper._handle_response(mock_response)

        # Verify no links were extracted
        assert self.scraper._xhr_links == set()

    @pytest.mark.asyncio
    async def test_handle_response_nested_json_structure(self) -> None:
        """Test _handle_response with complex nested JSON structure."""
        # Mock response with nested JSON structure
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.url = "https://api.example.com/jobs"
        mock_response.json = AsyncMock(
            return_value={
                "data": {
                    "results": [
                        {"job": {"url": "https://jobs.ashbyhq.com/Company/nested-123"}},
                        {"position": {"link": "https://lever.co/company/nested-456"}},
                    ]
                },
                "metadata": {"nextUrl": "https://api.example.com/jobs?page=2"},
            }
        )

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response
        await self.scraper._handle_response(mock_response)

        # Verify job links were extracted from nested structure
        expected_links = {
            "https://jobs.ashbyhq.com/Company/nested-123",
            "https://lever.co/company/nested-456",
        }
        assert self.scraper._xhr_links == expected_links

    @pytest.mark.asyncio
    async def test_handle_response_accumulates_links(self) -> None:
        """Test _handle_response accumulates links from multiple responses."""
        # Add some initial links
        self.scraper._xhr_links.add("https://jobs.ashbyhq.com/Company/existing-123")

        # Mock first response
        mock_response1 = MagicMock()
        mock_response1.headers = {"content-type": "application/json"}
        mock_response1.url = "https://api.example.com/jobs"
        mock_response1.json = AsyncMock(
            return_value={"jobs": [{"jobUrl": "https://jobs.ashbyhq.com/Company/new-456"}]}
        )

        # Mock second response
        mock_response2 = MagicMock()
        mock_response2.headers = {"content-type": "application/json"}
        mock_response2.url = "https://api.example.com/jobs"
        mock_response2.json = AsyncMock(
            return_value={"positions": [{"url": "https://lever.co/company/new-789"}]}
        )

        # Call _handle_response multiple times
        await self.scraper._handle_response(mock_response1)
        await self.scraper._handle_response(mock_response2)

        # Verify all links were accumulated
        expected_links = {
            "https://jobs.ashbyhq.com/Company/existing-123",
            "https://jobs.ashbyhq.com/Company/new-456",
            "https://lever.co/company/new-789",
        }
        assert self.scraper._xhr_links == expected_links

    @pytest.mark.asyncio
    async def test_handle_response_filters_non_job_links(self) -> None:
        """Test _handle_response filters out non-job links."""
        # Mock response with mixed content
        mock_response = MagicMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.url = "https://api.example.com/mixed"
        mock_response.json = AsyncMock(
            return_value={
                "data": [
                    {"url": "https://jobs.ashbyhq.com/Company/123"},  # Valid job link
                    {"url": "https://example.com/about"},  # Should be filtered out
                    {"url": "https://example.com/careers/engineer"},  # Valid job link
                    {"url": "https://example.com/blog/post"},  # Should be filtered out
                    {"url": "mailto:jobs@company.com"},  # Should be filtered out
                    {"url": "https://example.com/jobs/developer"},  # Valid job link
                ]
            }
        )

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response
        await self.scraper._handle_response(mock_response)

        # Verify only job links were extracted
        expected_links = {
            "https://jobs.ashbyhq.com/Company/123",
            "https://example.com/careers/engineer",
            "https://example.com/jobs/developer",
        }
        assert self.scraper._xhr_links == expected_links

    @pytest.mark.asyncio
    async def test_handle_response_content_type_variations(self) -> None:
        """Test _handle_response handles different JSON content-type variations."""
        test_cases = [
            ("application/json", True),
            ("application/json; charset=utf-8", True),
            ("application/json;charset=utf-8", True),
            ("Application/JSON", False),  # Case sensitive - should be ignored
            ("text/json", False),  # Should be ignored
            ("application/xml", False),  # Should be ignored
        ]

        for content_type, should_process in test_cases:
            # Mock response
            mock_response = MagicMock()
            mock_response.headers = {"content-type": content_type}
            mock_response.url = "https://api.example.com/jobs"
            mock_response.json = AsyncMock(
                return_value={"jobs": [{"jobUrl": "https://jobs.ashbyhq.com/Company/123"}]}
            )

            # Clear any existing XHR links
            self.scraper._xhr_links.clear()

            # Call _handle_response
            await self.scraper._handle_response(mock_response)

            # Check if links were extracted based on content type
            if should_process:
                expected_links = {"https://jobs.ashbyhq.com/Company/123"}
                assert self.scraper._xhr_links == expected_links, f"Failed for content-type: {content_type}"
            else:
                assert self.scraper._xhr_links == set(), f"Should ignore content-type: {content_type}"

    @pytest.mark.asyncio
    async def test_handle_response_missing_content_type(self) -> None:
        """Test _handle_response handles missing content-type header."""
        # Mock response without content-type header
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.url = "https://api.example.com/jobs"

        # Clear any existing XHR links
        self.scraper._xhr_links.clear()

        # Call _handle_response
        await self.scraper._handle_response(mock_response)

        # Verify no links were extracted (no JSON processing)
        assert self.scraper._xhr_links == set()
