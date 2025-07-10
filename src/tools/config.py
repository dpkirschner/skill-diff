"""Configuration constants for the scraper package."""

# Network timeouts
NETWORK_TIMEOUT = 120.0  # seconds
STATIC_TIMEOUT = 30.0  # seconds for static HTTP requests

# Playwright settings
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_ARGS = ["--no-sandbox", "--disable-setuid-sandbox"]

# Job URL patterns
JOB_PATTERNS = [
    r"/jobs/",
    r"/careers/",
    r"/openings/",
    r"/positions/",
    r"/opportunities/",
    r"/work-with-us/",
    r"/join-us/",
    r"/job-search/",
    r"/apply/",
    r"/hiring/",
    r"/employment/",
]

# Job board domains
JOB_BOARDS = [
    "ashbyhq.com",
    "lever.co",
    "greenhouse.io",
    "workday.com",
    "jobvite.com",
    "smartrecruiters.com",
    "bamboohr.com",
    "icims.com",
    "taleo.net",
    "successfactors.com",
]

# URL exclusion patterns
EXCLUDES = [
    r"#",  # Fragment links
    r"mailto:",  # Email links
    r"\.(pdf|doc|docx|jpg|jpeg|png|gif|svg|css|js|ico)$",  # File extensions
    r"/(about|contact|privacy|terms|blog|news|press|media)/",  # Non-job pages
    r"/feed/",  # RSS feeds
    r"/search\?",  # Search pages
    r"/login",  # Login pages
]

# Query parameter patterns that indicate job listings
JOB_QUERY_PATTERNS = [
    r"job_id=",
    r"jobid=",
    r"gh_jid=",  # Greenhouse
    r"lever-job=",  # Lever
    r"workday-job=",  # Workday
    r"position=",
    r"req_id=",
    r"posting=",
]
