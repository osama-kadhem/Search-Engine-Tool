"""
Tests for search_engine/crawler.py.
All HTTP calls are mocked so no real network requests are made.
"""

from unittest.mock import MagicMock, patch
import pytest

from search_engine.crawler import Crawler


# Minimal HTML pages used across multiple tests
HOME_HTML = """
<html>
  <head><title>Home Page</title></head>
  <body>
    <span class="text">"The world is a book."</span>
    <small class="author">Saint Augustine</small>
    <a class="tag" href="/tag/world">world</a>
    <a href="/page/2/">Next</a>
  </body>
</html>
"""

PAGE2_HTML = """
<html>
  <head><title>Page 2</title></head>
  <body>
    <span class="text">"Life is what happens."</span>
    <small class="author">John Lennon</small>
    <a class="tag" href="/tag/life">life</a>
  </body>
</html>
"""


def _make_response(html, url="https://quotes.toscrape.com"):
    """Helper: build a mock requests.Response."""
    resp = MagicMock()
    resp.text = html
    resp.url = url
    resp.raise_for_status = MagicMock()
    return resp


@patch("search_engine.crawler.time.sleep")  # stop real sleeps in tests
class TestCrawlerBasics:

    def test_crawl_returns_list(self, mock_sleep):
        """crawl() should return a list of page dicts."""
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        assert isinstance(pages, list)
        assert len(pages) == 1

    def test_page_has_required_fields(self, mock_sleep):
        """Each page dict must contain url, title, quotes, authors, tags."""
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        page = pages[0]
        for field in ("url", "title", "quotes", "authors", "tags"):
            assert field in page, f"Missing field: {field}"

    def test_private_links_field_is_removed(self, mock_sleep):
        """The internal _links field must be stripped from returned pages."""
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        assert "_links" not in pages[0]

    def test_title_is_parsed(self, mock_sleep):
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        assert pages[0]["title"] == "Home Page"

    def test_quotes_are_parsed(self, mock_sleep):
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        # BeautifulSoup returns the text verbatim; the HTML uses plain ASCII quotes
        assert '"The world is a book."' in pages[0]["quotes"]

    def test_authors_are_parsed(self, mock_sleep):
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        assert "Saint Augustine" in pages[0]["authors"]

    def test_tags_are_parsed(self, mock_sleep):
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            return_value=_make_response(HOME_HTML)
        )
        pages = crawler.crawl()
        assert "world" in pages[0]["tags"]


@patch("search_engine.crawler.time.sleep")
class TestCrawlerLimits:

    def test_max_pages_is_respected(self, mock_sleep):
        """Crawler must stop once max_pages is reached."""
        responses = [
            _make_response(HOME_HTML, "https://quotes.toscrape.com"),
            _make_response(PAGE2_HTML, "https://quotes.toscrape.com/page/2"),
        ]
        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(side_effect=responses)
        pages = crawler.crawl()
        assert len(pages) == 1

    def test_already_visited_urls_are_skipped(self, mock_sleep):
        """The same URL should only be crawled once even if queued twice."""
        # Page A links to B and C; Page B also links to C, so C enters the queue twice.
        # When the crawler pops C the second time it should hit `continue`.
        page_a = """
        <html><head><title>A</title></head><body>
          <a href="/b/">B</a>
          <a href="/c/">C</a>
        </body></html>
        """
        page_b = """
        <html><head><title>B</title></head><body>
          <a href="/c/">C again</a>
        </body></html>
        """
        page_c = """
        <html><head><title>C</title></head><body>No links here.</body></html>
        """

        def side_effect(url, timeout=10):
            if url.endswith("/b"):
                return _make_response(page_b, url)
            if url.endswith("/c"):
                return _make_response(page_c, url)
            return _make_response(page_a, url)

        crawler = Crawler(delay=0, max_pages=10)
        crawler._session.get = MagicMock(side_effect=side_effect)
        pages = crawler.crawl()

        # C must appear exactly once despite being queued from both A and B
        titles = [p["title"] for p in pages]
        assert titles.count("C") == 1


    def test_sleep_is_called_between_pages(self, mock_sleep):
        """time.sleep must be called at least once when more than one page is crawled."""
        responses = [
            _make_response(HOME_HTML, "https://quotes.toscrape.com"),
            _make_response(PAGE2_HTML, "https://quotes.toscrape.com/page/2"),
        ]
        crawler = Crawler(delay=6, max_pages=2)
        crawler._session.get = MagicMock(side_effect=responses)
        crawler.crawl()
        mock_sleep.assert_called()


@patch("search_engine.crawler.time.sleep")
class TestCrawlerErrorHandling:

    def test_failed_request_is_skipped(self, mock_sleep):
        """A page that raises RequestException should be skipped gracefully."""
        import requests as req_lib

        crawler = Crawler(delay=0, max_pages=1)
        crawler._session.get = MagicMock(
            side_effect=req_lib.RequestException("timeout")
        )
        pages = crawler.crawl()
        assert pages == []

    def test_external_links_are_not_followed(self, mock_sleep):
        """Links pointing to other domains must not be queued."""
        html_with_external = """
        <html><head><title>X</title></head><body>
          <a href="https://example.com/page">external</a>
        </body></html>
        """
        crawler = Crawler(delay=0, max_pages=5)
        crawler._session.get = MagicMock(
            return_value=_make_response(html_with_external)
        )
        pages = crawler.crawl()
        # Only the start URL should have been fetched
        assert crawler._session.get.call_count == 1


class TestCrawlerNormalise:

    def test_trailing_slash_stripped(self):
        crawler = Crawler()
        assert crawler._normalise("https://quotes.toscrape.com/") == \
               "https://quotes.toscrape.com"

    def test_fragment_stripped(self):
        crawler = Crawler()
        assert crawler._normalise("https://quotes.toscrape.com/page/#top") == \
               "https://quotes.toscrape.com/page"

    def test_is_internal_same_domain(self):
        crawler = Crawler()
        assert crawler._is_internal("https://quotes.toscrape.com/page/2/")

    def test_is_internal_different_domain(self):
        crawler = Crawler()
        assert not crawler._is_internal("https://example.com/page")
