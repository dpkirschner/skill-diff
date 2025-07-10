"""Shared fixtures for tools tests."""

from collections.abc import Callable

import pytest

from src.tools.types import FetchError


class MockFetcher:
    """Mock fetcher for testing."""

    def __init__(self, content: str | None = None, should_fail: bool = False) -> None:
        self.content = content
        self.should_fail = should_fail
        self.cleanup_called = False

    async def get(self, url: str) -> str:
        if self.should_fail:
            raise FetchError("Mock fetch error")
        return self.content or "<html>Mock content</html>"

    async def cleanup(self) -> None:
        self.cleanup_called = True


class MockParser:
    """Mock parser for testing."""

    def __init__(self, links: list[str] | None = None, should_fail: bool = False) -> None:
        self.links = set(links or [])
        self.should_fail = should_fail
        self.extract_calls: list[tuple[str, str]] = []

    def extract_links(self, content: str, base_url: str) -> set[str]:
        self.extract_calls.append((content, base_url))
        if self.should_fail:
            raise Exception("Mock parser error")
        return self.links


class MockLinkFilter:
    """Mock link filter for testing."""

    def __init__(self, should_match: bool = True) -> None:
        self.should_match = should_match

    def looks_like_target(self, url: str) -> bool:
        return self.should_match


# Fixtures for common mock objects
@pytest.fixture
def mock_fetcher() -> MockFetcher:
    """Fixture providing a basic mock fetcher."""
    return MockFetcher()


@pytest.fixture
def mock_fetcher_with_content() -> MockFetcher:
    """Fixture providing a mock fetcher with test content."""
    return MockFetcher(content="<html>Test content</html>")


@pytest.fixture
def mock_failing_fetcher() -> MockFetcher:
    """Fixture providing a mock fetcher that fails."""
    return MockFetcher(should_fail=True)


@pytest.fixture
def mock_parser() -> MockParser:
    """Fixture providing a basic mock parser."""
    return MockParser()


@pytest.fixture
def mock_parser_with_links() -> MockParser:
    """Fixture providing a mock parser with test links."""
    return MockParser(links=["https://example.com/jobs/123", "https://example.com/careers/456"])


@pytest.fixture
def mock_failing_parser() -> MockParser:
    """Fixture providing a mock parser that fails."""
    return MockParser(should_fail=True)


@pytest.fixture
def mock_link_filter() -> MockLinkFilter:
    """Fixture providing a mock link filter that matches all."""
    return MockLinkFilter(should_match=True)


@pytest.fixture
def mock_rejecting_filter() -> MockLinkFilter:
    """Fixture providing a mock link filter that rejects all."""
    return MockLinkFilter(should_match=False)


@pytest.fixture
def mock_fetcher_factory() -> Callable[[str | None, bool], MockFetcher]:
    """Fixture providing a factory function for creating mock fetchers."""

    def _create_fetcher(content: str | None = None, should_fail: bool = False) -> MockFetcher:
        return MockFetcher(content=content, should_fail=should_fail)

    return _create_fetcher


@pytest.fixture
def mock_parser_factory() -> Callable[[list[str] | None, bool], MockParser]:
    """Fixture providing a factory function for creating mock parsers."""

    def _create_parser(links: list[str] | None = None, should_fail: bool = False) -> MockParser:
        return MockParser(links=links, should_fail=should_fail)

    return _create_parser
