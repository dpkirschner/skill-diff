"""Filter implementations for identifying target URLs."""

import re
from urllib.parse import urlparse

from src.tools.config import EXCLUDES, JOB_BOARDS, JOB_PATTERNS, JOB_QUERY_PATTERNS
from src.tools.types import URL

from .filter import BaseFilter


class JobLinkFilter(BaseFilter):
    """Filter for identifying job-related URLs."""

    def __init__(
        self,
        job_patterns: list[str] | None = None,
        job_boards: list[str] | None = None,
        excludes: list[str] | None = None,
        query_patterns: list[str] | None = None,
    ):
        """Initialize the JobLinkFilter.

        Args:
            job_patterns: URL path patterns that indicate job listings
            job_boards: Domain names of known job boards
            excludes: URL patterns to exclude
            query_patterns: Query parameter patterns that indicate job listings
        """
        self.job_patterns = job_patterns or JOB_PATTERNS
        self.job_boards = job_boards or JOB_BOARDS
        self.excludes = excludes or EXCLUDES
        self.query_patterns = query_patterns or JOB_QUERY_PATTERNS

        # Compile regex patterns for better performance
        self._job_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.job_patterns]
        self._exclude_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.excludes]
        self._query_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.query_patterns]

    def looks_like_target(self, url: URL) -> bool:
        """Check if a URL looks like a job listing.

        Args:
            url: The URL to check

        Returns:
            True if the URL appears to be a job listing, False otherwise
        """
        try:
            parsed = urlparse(url)

            # Skip invalid URLs
            if not parsed.scheme or not parsed.netloc:
                return False

            # Check exclusion patterns first
            if self._matches_exclude_patterns(url):
                return False

            # Check if it's a known job board
            if self._is_job_board(parsed.netloc):
                return True

            # Check job-related path patterns
            if self._matches_job_patterns(parsed.path):
                return True

            # Check query parameters
            return self._matches_query_patterns(parsed.query)

        except Exception:
            return False

    def _matches_exclude_patterns(self, url: URL) -> bool:
        """Check if URL matches any exclusion pattern."""
        return any(regex.search(url) for regex in self._exclude_regex)

    def _is_job_board(self, domain: str) -> bool:
        """Check if domain is a known job board."""
        # Remove 'www.' prefix if present
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Check for exact match first
        if domain in self.job_boards:
            return True

        # Check for subdomain matches (e.g., company.lever.co matches lever.co)
        return any(domain.endswith("." + job_board) for job_board in self.job_boards)

        return False

    def _matches_job_patterns(self, path: str) -> bool:
        """Check if path matches any job pattern."""
        return any(regex.search(path) for regex in self._job_regex)

    def _matches_query_patterns(self, query: str) -> bool:
        """Check if query string matches any job query pattern."""
        return any(regex.search(query) for regex in self._query_regex)
