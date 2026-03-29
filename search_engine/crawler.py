# Crawls quotes.toscrape.com, follows internal links, and
# collects quotes, authors and tags from each page.
# Waits 6 seconds between requests to stay polite.

import time
import logging
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://quotes.toscrape.com"
CRAWL_DELAY = 6  # seconds — required by the coursework brief


class Crawler:
    """Crawls quotes.toscrape.com and returns a list of page dicts."""

    def __init__(self, base_url=BASE_URL, delay=CRAWL_DELAY, max_pages=None):
        self.base_url = base_url
        self.delay = delay
        self.max_pages = max_pages  # useful during testing to avoid long crawls
        self._visited = set()
        self._session = requests.Session()
        self._session.headers.update(
            {"User-Agent": "COMP3011-SearchEngine/1.0 (educational project)"}
        )

    def crawl(self, start_url=None):
        """
        Crawl from start_url and return all collected pages.
        Each page is a dict: url, title, quotes, authors, tags.
        """
        start_url = start_url or self.base_url
        queue = [start_url]
        pages = []

        while queue:
            if self.max_pages and len(pages) >= self.max_pages:
                logger.info("Reached max_pages limit (%d). Stopping.", self.max_pages)
                break

            url = queue.pop(0)
            normalised = self._normalise(url)

            if normalised in self._visited:
                continue
            self._visited.add(normalised)

            page_data = self._fetch_and_parse(normalised)
            if page_data is None:
                continue

            pages.append(page_data)
            logger.info("Crawled: %s (%d pages so far)", normalised, len(pages))

            # Queue any new links found on this page
            for link in page_data.get("_links", []):
                if self._normalise(link) not in self._visited:
                    queue.append(link)

            # Be polite — wait before the next request
            if queue:
                logger.debug("Waiting %.1f s before next request...", self.delay)
                time.sleep(self.delay)

        # Strip the internal _links field before handing data to the caller
        for page in pages:
            page.pop("_links", None)

        return pages

    def _fetch_and_parse(self, url):
        """Fetch one page and return its data, or None if the request fails."""
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
        # Use a set first to remove duplicate tags, then convert back to list
        return list({t.get_text(strip=True) for t in soup.select("a.tag")})

    def _parse_links(self, soup, current_url):
        """Return all internal links found on the page as absolute URLs."""
        links = []
        for a in soup.find_all("a", href=True):
            abs_url = urljoin(current_url, a["href"])
            if self._is_internal(abs_url):
                links.append(abs_url)
        return links

    def _is_internal(self, url):
        """Return True if the URL belongs to the same domain we started from."""
        target_host = urlparse(self.base_url).netloc
        return urlparse(url).netloc == target_host

    @staticmethod
    def _normalise(url):
        """Remove trailing slashes and fragments so we don't visit the same page twice."""
        parsed = urlparse(url)
        return parsed._replace(fragment="").geturl().rstrip("/")
