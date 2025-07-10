"""Fixtures specific to parser tests."""

import pytest

from src.tools.parsers.html_parser import HtmlParser
from src.tools.parsers.json_parser import JsonParser
from tests.unit.tools.conftest import MockLinkFilter


@pytest.fixture
def html_parser(mock_link_filter: MockLinkFilter) -> HtmlParser:
    """Fixture providing an HtmlParser with mock filter."""
    return HtmlParser(mock_link_filter)


@pytest.fixture
def json_parser(mock_link_filter: MockLinkFilter) -> JsonParser:
    """Fixture providing a JsonParser with mock filter."""
    return JsonParser(mock_link_filter)


@pytest.fixture
def sample_html() -> str:
    """Fixture providing sample HTML content for testing."""
    return """
    <html>
        <body>
            <a href="/jobs/123">Software Engineer</a>
            <a href="/careers/456">Data Scientist</a>
            <a href="https://example.com/positions/789">Product Manager</a>
        </body>
    </html>
    """


@pytest.fixture
def sample_json() -> str:
    """Fixture providing sample JSON content for testing."""
    return """
    {
        "jobs": [
            {
                "id": 1,
                "url": "/jobs/123",
                "title": "Software Engineer"
            },
            {
                "id": 2,
                "url": "/careers/456",
                "title": "Data Scientist"
            }
        ]
    }
    """


@pytest.fixture
def sample_jsonld_html() -> str:
    """Fixture providing HTML with JSON-LD structured data."""
    return """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "JobPosting",
                "url": "/jobs/software-engineer",
                "hiringOrganization": {
                    "url": "https://example.com"
                }
            }
            </script>
        </head>
    </html>
    """
