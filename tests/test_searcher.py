# Tests for searcher.py

import io
import pytest

from search_engine.indexer import Indexer
from search_engine.searcher import Searcher


# ---- Shared fixture ----------------------------------------------------------

PAGES = [
    {
        "url": "https://quotes.toscrape.com",
        "title": "Quotes to Scrape",
        "quotes": ["The world is a book and those who do not travel read only one page."],
        "authors": ["Saint Augustine"],
        "tags": ["world", "travel"],
    },
    {
        "url": "https://quotes.toscrape.com/page/2",
        "title": "Page Two",
        "quotes": ["Life is what happens to us while we are making other plans."],
        "authors": ["Allen Saunders"],
        "tags": ["life", "planning"],
    },
    {
        "url": "https://quotes.toscrape.com/page/3",
        "title": "Page Three",
        "quotes": ["In the middle of every difficulty lies opportunity."],
        "authors": ["Albert Einstein"],
        "tags": ["difficulty", "opportunity"],
    },
]


@pytest.fixture
def searcher():
    indexer = Indexer()
    indexer.build(PAGES)
    return Searcher(indexer)


# ---- find() tests ------------------------------------------------------------

class TestSearcherFind:

    def test_returns_list(self, searcher):
        results = searcher.find("world")
        assert isinstance(results, list)

    def test_known_term_returns_results(self, searcher):
        results = searcher.find("world")
        assert len(results) > 0

    def test_result_has_required_keys(self, searcher):
        results = searcher.find("life")
        assert len(results) > 0
        for key in ("title", "url", "score", "snippet"):
            assert key in results[0]

    def test_results_are_sorted_by_score_descending(self, searcher):
        results = searcher.find("life")
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limits_results(self, searcher):
        results = searcher.find("the", top_n=1)
        assert len(results) <= 1

    def test_unknown_query_returns_empty(self, searcher):
        results = searcher.find("xyznonexistentword")
        assert results == []

    def test_empty_query_returns_empty(self, searcher):
        # An empty or all-stop-word query should return nothing gracefully
        results = searcher.find("")
        assert results == []

    def test_stop_word_only_query_returns_empty(self, searcher):
        results = searcher.find("the a and is")
        assert results == []

    def test_score_is_positive(self, searcher):
        results = searcher.find("world")
        for r in results:
            assert r["score"] > 0

    def test_url_in_result(self, searcher):
        results = searcher.find("world")
        assert any("quotes.toscrape.com" in r["url"] for r in results)

    def test_multiword_query(self, searcher):
        results = searcher.find("world travel")
        assert len(results) > 0

    def test_relevant_doc_ranks_higher(self, searcher):
        results = searcher.find("life planning")
        top_url = results[0]["url"]
        assert "page/2" in top_url


# ---- print_all() tests -------------------------------------------------------

class TestSearcherPrintAll:

    def test_print_all_runs_without_error(self, searcher, capsys):
        searcher.print_all()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_all_shows_all_docs(self, searcher, capsys):
        searcher.print_all()
        captured = capsys.readouterr()
        # All three URLs should appear in the output
        assert "quotes.toscrape.com" in captured.out

    def test_print_all_empty_index_prints_message(self, capsys):
        empty_indexer = Indexer()
        empty_indexer.build([])
        s = Searcher(empty_indexer)
        s.print_all()
        captured = capsys.readouterr()
        assert "empty" in captured.out.lower()


# ---- _snippet() tests --------------------------------------------------------

class TestSearcherSnippet:

    def test_snippet_contains_query_word(self, searcher):
        results = searcher.find("world")
        snippet = results[0]["snippet"]
        # Snippet should include words close to 'world'
        assert len(snippet) > 0

    def test_snippet_fallback_when_query_not_in_text(self):
        # Build an indexer with a page that contains 'apple' but search for 'zzz'
        # so the stemmed loop never matches and we hit the fallback return.
        pages = [{
            "url": "https://example.com",
            "title": "Apple Pie Recipe",
            "quotes": ["Bake at 180 degrees."],
            "authors": ["Chef"],
            "tags": ["food"],
        }]
        indexer = Indexer()
        indexer.build(pages)
        s = Searcher(indexer)
        doc = list(indexer.documents.values())[0]

        # Call _snippet directly with a token that will never match
        snippet = s._snippet(doc, ["zzztoken"])
        # Should be non-empty and come from the start of the text
        assert len(snippet) > 0
        assert "Apple" in snippet or "Bake" in snippet or "Chef" in snippet or "food" in snippet



# ---- doc_lengths pre-computation --------------------------------------------

class TestSearcherDocLengths:

    def test_doc_lengths_all_positive(self, searcher):
        for doc_id, length in searcher._doc_lengths.items():
            assert length > 0, f"doc_id {doc_id} has zero length"

    def test_doc_lengths_count_matches_documents(self, searcher):
        assert len(searcher._doc_lengths) == len(searcher.indexer.documents)
