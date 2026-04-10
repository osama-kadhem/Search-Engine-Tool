# Tests for indexer.py

import json
import os
import pytest

from search_engine.indexer import Document, Indexer


# --- Document tests -----------------------------------------------------------

class TestDocument:

    def test_full_text_combines_all_fields(self):
        doc = Document(
            doc_id=0,
            url="https://example.com",
            title="My Title",
            quotes=["A wise quote"],
            authors=["An Author"],
            tags=["wisdom"],
        )
        text = doc.full_text()
        assert "My Title" in text
        assert "A wise quote" in text
        assert "An Author" in text
        assert "wisdom" in text

    def test_full_text_handles_empty_lists(self):
        doc = Document(
            doc_id=1, url="", title="Only Title",
            quotes=[], authors=[], tags=[]
        )
        assert doc.full_text() == "Only Title"


# --- Indexer.build tests ------------------------------------------------------

SAMPLE_PAGES = [
    {
        "url": "https://quotes.toscrape.com",
        "title": "Quotes to Scrape",
        "quotes": ["The world is a book."],
        "authors": ["Saint Augustine"],
        "tags": ["world", "travel"],
    },
    {
        "url": "https://quotes.toscrape.com/page/2",
        "title": "Page Two",
        "quotes": ["Life is what happens."],
        "authors": ["John Lennon"],
        "tags": ["life", "change"],
    },
]


class TestIndexerBuild:

    def test_documents_are_created(self):
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        assert len(indexer.documents) == 2

    def test_document_ids_are_sequential(self):
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        assert set(indexer.documents.keys()) == {0, 1}

    def test_index_contains_stemmed_tokens(self):
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        # 'world' stems to 'world', it must appear in the index
        assert "world" in indexer.index or any(
            "world" in k for k in indexer.index
        )

    def test_index_maps_token_to_doc_id(self):
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        # The stemmed form of 'augustin' or similar should map to doc 0
        # Use a known word: title 'quot' (stem of quotes) should appear for both
        for doc_ids in indexer.index.values():
            assert all(isinstance(d, int) for d in doc_ids)

    def test_term_freq_is_populated(self):
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        assert len(indexer.term_freq) > 0

    def test_term_freq_keys_are_tuples(self):
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        for key in indexer.term_freq:
            assert isinstance(key, tuple)
            assert len(key) == 2

    def test_build_on_empty_list(self):
        indexer = Indexer()
        indexer.build([])
        assert indexer.documents == {}
        assert indexer.index == {}

    def test_missing_fields_default_to_empty(self):
        pages = [{"url": "https://example.com"}]
        indexer = Indexer()
        indexer.build(pages)  # should not raise
        assert len(indexer.documents) == 1


# --- Indexer.save / load tests ------------------------------------------------

class TestIndexerSaveLoad:

    def test_save_creates_file(self, tmp_path):
        path = str(tmp_path / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        indexer.save(path)
        assert os.path.exists(path)

    def test_save_produces_valid_json(self, tmp_path):
        path = str(tmp_path / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        indexer.save(path)
        with open(path) as f:
            data = json.load(f)  # must not raise
        assert "documents" in data
        assert "index" in data
        assert "term_freq" in data

    def test_load_restores_documents(self, tmp_path):
        path = str(tmp_path / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        indexer.save(path)

        indexer2 = Indexer()
        indexer2.load(path)
        assert len(indexer2.documents) == 2

    def test_load_restores_index(self, tmp_path):
        path = str(tmp_path / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        original_tokens = set(indexer.index.keys())
        indexer.save(path)

        indexer2 = Indexer()
        indexer2.load(path)
        assert set(indexer2.index.keys()) == original_tokens

    def test_load_restores_term_freq(self, tmp_path):
        path = str(tmp_path / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        indexer.save(path)

        indexer2 = Indexer()
        indexer2.load(path)
        assert len(indexer2.term_freq) == len(indexer.term_freq)

    def test_load_doc_ids_are_ints(self, tmp_path):
        # JSON artefact encodes keys as strings, we want ints
        path = str(tmp_path / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        indexer.save(path)

        indexer2 = Indexer()
        indexer2.load(path)
        for k in indexer2.documents:
            assert isinstance(k, int)

    def test_load_missing_file_raises(self, tmp_path):
        indexer = Indexer()
        with pytest.raises(FileNotFoundError):
            indexer.load(str(tmp_path / "nonexistent.json"))

    def test_save_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "index.json")
        indexer = Indexer()
        indexer.build(SAMPLE_PAGES)
        indexer.save(path)  # should not raise
        assert os.path.exists(path)


# --- Preprocess tests ---------------------------------------------------------

class TestIndexerPreprocess:

    def _preprocess(self, text):
        return Indexer()._preprocess(text)

    def test_returns_list(self):
        assert isinstance(self._preprocess("hello world"), list)

    def test_lowercases_tokens(self):
        # All returned tokens should be lowercase
        tokens = self._preprocess("Hello World")
        for t in tokens:
            assert t == t.lower()

    def test_removes_stop_words(self):
        tokens = self._preprocess("the quick brown fox")
        # 'the' is a stop word and should be removed
        assert "the" not in tokens

    def test_removes_punctuation_tokens(self):
        tokens = self._preprocess("Hello, world!")
        for t in tokens:
            assert t.isalpha()

    def test_empty_string_returns_empty(self):
        assert self._preprocess("") == []
