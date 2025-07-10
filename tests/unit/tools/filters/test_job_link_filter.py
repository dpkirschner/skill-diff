"""Tests for filter implementations."""

from src.tools.filters.job_link_filter import JobLinkFilter


class TestJobLinkFilter:
    """Tests for JobLinkFilter."""

    def test_job_path_patterns(self) -> None:
        """Test job path pattern matching."""
        filter_obj = JobLinkFilter()

        # Test job path patterns
        assert filter_obj.looks_like_target("https://example.com/jobs/123")
        assert filter_obj.looks_like_target("https://example.com/careers/software-engineer")
        assert filter_obj.looks_like_target("https://example.com/openings/456")
        assert filter_obj.looks_like_target("https://example.com/positions/data-scientist")
        assert filter_obj.looks_like_target("https://example.com/opportunities/789")

        # Test non-job paths
        assert not filter_obj.looks_like_target("https://example.com/about")
        assert not filter_obj.looks_like_target("https://example.com/contact")
        assert not filter_obj.looks_like_target("https://example.com/blog/post")

    def test_job_board_domains(self) -> None:
        """Test job board domain recognition."""
        filter_obj = JobLinkFilter()

        # Test job board domains
        assert filter_obj.looks_like_target("https://company.lever.co/123")
        assert filter_obj.looks_like_target("https://boards.greenhouse.io/company/jobs/123")
        assert filter_obj.looks_like_target("https://company.ashbyhq.com/jobs/123")
        assert filter_obj.looks_like_target("https://company.workday.com/jobs/123")

        # Test with www prefix
        assert filter_obj.looks_like_target("https://www.lever.co/company/123")

        # Test non-job board domains
        assert not filter_obj.looks_like_target("https://example.com/random")

    def test_query_parameter_patterns(self) -> None:
        """Test job query parameter pattern matching."""
        filter_obj = JobLinkFilter()

        # Test job query parameters
        assert filter_obj.looks_like_target("https://example.com/apply?job_id=123")
        assert filter_obj.looks_like_target("https://example.com/careers?jobid=456")
        assert filter_obj.looks_like_target("https://example.com/hiring?gh_jid=789")
        assert filter_obj.looks_like_target("https://example.com/work?position=engineer")

        # Test non-job query parameters
        assert not filter_obj.looks_like_target("https://example.com/search?q=software")

    def test_exclusion_patterns(self) -> None:
        """Test URL exclusion patterns."""
        filter_obj = JobLinkFilter()

        # Test fragment links
        assert not filter_obj.looks_like_target("https://example.com/jobs#section")

        # Test mailto links
        assert not filter_obj.looks_like_target("mailto:hr@example.com")

        # Test file extensions
        assert not filter_obj.looks_like_target("https://example.com/resume.pdf")
        assert not filter_obj.looks_like_target("https://example.com/logo.png")
        assert not filter_obj.looks_like_target("https://example.com/style.css")

        # Test excluded paths
        assert not filter_obj.looks_like_target("https://example.com/about/team")
        assert not filter_obj.looks_like_target("https://example.com/contact/support")
        assert not filter_obj.looks_like_target("https://example.com/blog/posts")
        assert not filter_obj.looks_like_target("https://example.com/privacy/policy")

        # Test search pages
        assert not filter_obj.looks_like_target("https://example.com/search?q=test")

        # Test login pages
        assert not filter_obj.looks_like_target("https://example.com/login")

    def test_custom_patterns(self) -> None:
        """Test custom pattern configuration."""
        custom_filter = JobLinkFilter(
            job_patterns=[r"/custom-jobs/"],
            job_boards=["custom-board.com"],
            excludes=[r"/custom-exclude/"],
            query_patterns=[r"custom_job="],
        )

        # Test custom job pattern
        assert custom_filter.looks_like_target("https://example.com/custom-jobs/123")
        assert not custom_filter.looks_like_target("https://example.com/jobs/123")  # Default pattern

        # Test custom job board
        assert custom_filter.looks_like_target("https://custom-board.com/anything")
        assert not custom_filter.looks_like_target("https://lever.co/job/123")  # Default board

        # Test custom exclusion
        assert not custom_filter.looks_like_target("https://example.com/custom-exclude/page")

        # Test custom query pattern
        assert custom_filter.looks_like_target("https://example.com/apply?custom_job=123")

    def test_invalid_urls(self) -> None:
        """Test handling of invalid URLs."""
        filter_obj = JobLinkFilter()

        # Test invalid URLs
        assert not filter_obj.looks_like_target("not-a-url")
        assert not filter_obj.looks_like_target("://missing-scheme")
        assert not filter_obj.looks_like_target("https://")
        assert not filter_obj.looks_like_target("")

    def test_case_insensitive_matching(self) -> None:
        """Test case-insensitive pattern matching."""
        filter_obj = JobLinkFilter()

        # Test case variations
        assert filter_obj.looks_like_target("https://example.com/JOBS/123")
        assert filter_obj.looks_like_target("https://example.com/Jobs/123")
        assert filter_obj.looks_like_target("https://example.com/Careers/456")
        assert filter_obj.looks_like_target("https://LEVER.CO/company/123")
        assert filter_obj.looks_like_target("https://example.com/apply?JOB_ID=123")

    def test_domain_normalization(self) -> None:
        """Test domain normalization (www prefix removal)."""
        filter_obj = JobLinkFilter()

        # Test www prefix removal
        assert filter_obj._is_job_board("www.lever.co")
        assert filter_obj._is_job_board("lever.co")
        assert filter_obj._is_job_board("WWW.LEVER.CO")

        # Test non-job boards
        assert not filter_obj._is_job_board("www.example.com")
        assert not filter_obj._is_job_board("example.com")
