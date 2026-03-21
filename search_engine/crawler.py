"""
Crawler for quotes.toscrape.com.
Follows internal links and collects quotes, authors, and tags from each page.
Waits at least 6 seconds between requests to be polite to the server.
"""

import time
import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://quotes.toscrape.com"
CRAWL_DELAY = 6  # seconds - required by the coursework brief


class Crawler:
    """Crawls quotes.toscrape.com and returns a list of page data dicts."""

    def __init__(self, base_url=BASE_URL, delay=CRAWL_DELAY, max_pages=None):
        self.base_url = base_url
        self.delay = delay
        self.max_pages = max_pages  # set a limit during testing to avoid long crawls
        self._visited = set()
        self._session = requests.Session()
        self._session.headers.update(
            {"User-Agent": "COMP3011-SearchEngine/1.0 (educational project)"}
        )

    def crawl(self, start_url=None):
        """
        Start crawling from start_url and return all collected pages.
        Each page is a dict with: url, title, quotes, authors, tags.
        """
        start_url = start_url or self.base_url
        queue = [start_url]
        pages = []

        while queue:
            # Stop early if we have reached the page limit
            if self.max_pages and len(pages) >= self.max_pages:
                logger.info("Reached max_pages limit (%d). Stopping.", self.max_pages)
                break

            url = queue.pop(0)
            normalised = self._normalise(url)

            # Skip pages we have already visited
            if normalised in self._visited:
                continue
            self._visited.add(normalised)

            page_data = self._fetch_and_parse(normalised)
            if page_data is None:
                continue

            pages.append(page_data)
            logger.info("Crawled: %s (%d pages so far)", normalised, len(pages))

            # Add any new links we found on this page to the queue
            for link in page_data.get("_links", []):
                if self._normalise(link) not in self._visited:
                    queue.append(link)

            # Wait before the next request to be polite to the server
            if queue:
                logger.debug("Waiting %.1f s before next request...", self.delay)
                time.sleep(self.delay)

        # Remove the internal _links field before returning to the caller
        for page in pages:
            page.pop("_links", None)

        return pages

    def _fetch_and_parse(self, url):
        """Fetch a single URL and return its parsed data, or None if it fails."""
        try:
            response = self._session.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Could not fetch %s: %s", url, exc)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        return {
            "url": url,
            "title": self._parse_title(soup),
            "quotes": self._parse_quotes(soup),
            "authors": self._parse_authors(soup),
            "tags": self._parse_tags(soup),
            "_links": self._parse_links(soup, url),
        }

    def _parse_title(self, soup):
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    def _parse_quotes(self, soup):
        return [q.get_text(strip=True) for q in soup.select("span.text")]

    def _parse_authors(self, soup):
        return [a.get_text(strip=True) for a in soup.select("small.author")]

    def _parse_tags(self, soup):
        # Use a set to avoid duplicates, then convert back to a list
        return list({t.get_text(strip=True) for t in soup.select("a.tag")})

    def _parse_links(self, soup, current_url):
        """Return all absolute links on the page that stay within our domain."""
        links = []
        for a in soup.find_all("a", href=True):
            abs_url = urljoin(current_url, a["href"])
            if self._is_internal(abs_url):
                links.append(abs_url)
        return links

    def _is_internal(self, url):
        """Check whether a URL belongs to the same domain we are crawling."""
        target_host = urlparse(self.base_url).netloc
        return urlparse(url).netloc == target_host

    @staticmethod
    def _normalise(url):
        """Strip trailing slashes and fragments so we don't visit the same page twice."""
        parsed = urlparse(url)
        return parsed._replace(fragment="").geturl().rstrip("/")
