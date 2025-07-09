from __future__ import annotations

import asyncio
import json
import re
from contextlib import suppress
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from playwright.async_api import Browser, Page, Playwright, Response, async_playwright
from playwright.async_api import TimeoutError as PWTimeout

NETWORK_TIMEOUT = 120_000  # ms


class JobScraper:
    """
    Discover job posting URLs from static or JS-rendered career pages.
    """

    def __init__(self, headless: bool = True) -> None:
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.headless = headless
        self._xhr_links: set[str] = set()

    # ─────────────────────────── setup/teardown ──────────────────────────── #

    async def setup(self) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-dev-shm-usage"],
        )
        self.page = await self.browser.new_page()

        # Attach a response listener to sniff JSON APIs that contain job URLs
        self.page.on("response", self._handle_response)

    async def cleanup(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    # ──────────────────────────── public API ────────────────────────────── #

    async def discover(self, url: str) -> list[str]:
        """
        Main entry point. Tries static fetch first, then falls back to Playwright.

        Returns a list of absolute job posting URLs.
        """
        # 1. Fast static attempt
        static_html = await self._fetch_static(url)
        job_links = self._parse_for_job_links(static_html, url)
        if job_links:  # good enough
            return sorted(job_links)

        # 2. JS path with Playwright
        if not self.page:
            await self.setup()

        assert self.page is not None, "Page should be initialized after setup"

        try:
            await self.page.goto(url, timeout=NETWORK_TIMEOUT)
            # Heuristic: wait until either network idle OR at least 1 anchor appears
            with suppress(PWTimeout):
                await self.page.wait_for_selector("a", timeout=10_000)

            rendered_html = await self.page.content()
        except Exception as exc:
            print(f"[warn] Playwright failed for {url}: {exc}")
            rendered_html = ""

        # combine anchors + xhr-captured links + schema-LD
        links_from_dom = self._parse_for_job_links(rendered_html, url)
        all_links = links_from_dom.union(self._xhr_links)
        return sorted(all_links)

    # ─────────────────────────── helpers ────────────────────────────────── #

    async def _fetch_static(self, url: str) -> str:
        """
        Fast GET with httpx. Returns text or empty string on error.
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                r = await client.get(url, headers={"User-Agent": "JobBot/1.0"})
                r.raise_for_status()
                return r.text
        except httpx.HTTPError as exc:
            print(f"[info] static fetch fallback to Playwright ({exc})")
            return ""

    async def _handle_response(self, resp: Response) -> None:
        """
        Watch XHR / fetch responses for JSON arrays that include job links.
        """
        ct = resp.headers.get("content-type", "")
        if "application/json" not in ct:
            return
        try:
            data = await resp.json()
        except Exception:
            return
        json_str = json.dumps(data)
        # FEATURE: support for other json-based APIs
        # FEATURE: support pagination
        self._xhr_links.update(self._extract_links_from_text(json_str, resp.url))

    # ───────────────────────── link extraction ──────────────────────────── #

    def _parse_for_job_links(self, html: str, base_url: str) -> set[str]:
        soup = BeautifulSoup(html, "html.parser")
        anchors = self._extract_anchor_links(soup, base_url)
        schema_links = self._extract_schema_ld_links(soup, base_url)
        return anchors.union(schema_links)

    def _extract_anchor_links(self, soup: BeautifulSoup, base_url: str) -> set[str]:
        links: set[str] = set()
        for a in soup.find_all("a", href=True):
            if isinstance(a, Tag) and a.get("href"):
                href = a.get("href")
                if isinstance(href, str):
                    abs_url = urljoin(base_url, href)
                    if self._looks_like_job(abs_url):
                        links.add(abs_url)
        return links

    def _extract_schema_ld_links(self, soup: BeautifulSoup, base_url: str) -> set[str]:
        """
        Many pages embed JobPosting objects in <script type=application/ld+json>.
        """
        links: set[str] = set()
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if isinstance(script, Tag) and script.string:
                    payload = json.loads(script.string)
                else:
                    continue
            except Exception:
                continue
            json_str = json.dumps(payload)
            links.update(self._extract_links_from_text(json_str, base_url))
        return links

    # FEATURE: implement something more robust across a few different types of landing pages
    def _extract_links_from_text(self, text: str, base_url: str) -> set[str]:
        """
        Regex any urls inside arbitrary text/JSON, then filter for job-ish paths.
        """
        candidate_urls = set(re.findall(r"https?://[^\s\"'<>]+", text, flags=re.IGNORECASE))
        filtered = {url for url in candidate_urls if self._looks_like_job(url)}
        # also handle relative links occasionally present in JSON
        for frag in re.findall(r"\"(\/[^\"]+)\"", text):
            candidate = urljoin(base_url, frag)
            if self._looks_like_job(candidate):
                filtered.add(candidate)
        return filtered

    # ─────────────────────────── heuristics ─────────────────────────────── #

    # FEATURE: can I utilize an agent call to do this arbitrarily? There must be more patterns
    JOB_PATTERNS = [
        r"/jobs?/",
        r"/careers?/",
        r"/openings?/",
        r"/positions?/",
        r"/opportunities?/",
        r"/vacancies?/",
        r"/employment/",
        r"/hiring/",
        r"job_id=",
        r"jobid=",
        r"gh_jid=",  # Greenhouse
        r"lever.co/.*\?lever",  # Lever tracking links
    ]
    # FEATURE: can I utilize an agent call to do this arbitrarily? There must be more patterns
    JOB_BOARDS = [
        "ashbyhq.com",
        "lever.co",
        "greenhouse.io",
        "workday.com",
        "bamboohr.com",
        "smartrecruiters.com",
        "workable.com",
        "applytojob.com",
        "recruitee.com",
        "teamtailor.com",
    ]
    EXCLUDES = [
        r"#",
        r"javascript:",
        r"mailto:",
        r"\.(png|jpg|jpeg|gif|svg|css|js|pdf)$",
        r"/(about|contact|press|privacy|terms|help|blog)(/|$)",
    ]

    def _looks_like_job(self, url: str) -> bool:
        lower = url.lower()
        if any(re.search(p, lower) for p in self.EXCLUDES):
            return False
        if any(board in lower for board in self.JOB_BOARDS):
            return True
        return any(re.search(p, lower) for p in self.JOB_PATTERNS)


# ─────────────────────────────── demo ──────────────────────────────────── #


async def _demo() -> None:
    scraper = JobScraper()
    try:
        jobs = await scraper.discover("https://sierra.ai/careers")
        print(f"Found {len(jobs)} links:")
        for url in jobs:
            print(" •", url)
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    asyncio.run(_demo())
