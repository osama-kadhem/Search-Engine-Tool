"""
Indexer - builds an inverted index from crawled pages and saves/loads it to disk.

Pipeline for each page:
  1. Combine all text fields (title, quotes, authors, tags) into one string
  2. Tokenise and lowercase
  3. Remove stop words (common words like 'the', 'a', 'is')
  4. Stem each word (e.g. 'running' -> 'run') so similar words match
  5. Map each token to the document IDs that contain it
"""

import json
import os
import math
import logging
from dataclasses import dataclass, asdict
from typing import List

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

logger = logging.getLogger(__name__)

STOP_WORDS = set(stopwords.words("english"))
stemmer = PorterStemmer()


@dataclass
class Document:
    """Represents a single crawled page stored in the index."""
    doc_id: int
    url: str
    title: str
    quotes: List[str]
    authors: List[str]
    tags: List[str]

    def full_text(self):
        """Combine all text fields into one string for indexing."""
        parts = [self.title] + self.quotes + self.authors + self.tags
        return " ".join(parts)


class Indexer:
    """Builds and stores an inverted index from crawled page data."""

    def __init__(self):
        self.documents = {}       # doc_id -> Document
        self.index = {}           # token -> list of doc_ids
        self.term_freq = {}       # (doc_id, token) -> count, used for TF-IDF

    def build(self, pages):
        """
        Build the inverted index from a list of crawled page dicts.
        Each page dict comes directly from the Crawler.
        """
        logger.info("Building index from %d pages...", len(pages))

        for doc_id, page in enumerate(pages):
            doc = Document(
                doc_id=doc_id,
                url=page.get("url", ""),
                title=page.get("title", ""),
                quotes=page.get("quotes", []),
                authors=page.get("authors", []),
                tags=page.get("tags", []),
            )
            self.documents[doc_id] = doc

            # Tokenise and clean the document's text
            tokens = self._preprocess(doc.full_text())

            # Count how often each token appears (for TF-IDF later)
            for token in tokens:
                self.term_freq[(doc_id, token)] = self.term_freq.get((doc_id, token), 0) + 1

            # Add this doc to the posting list for each unique token
            for token in set(tokens):
                if token not in self.index:
                    self.index[token] = []
                self.index[token].append(doc_id)

        logger.info("Index built: %d documents, %d unique tokens.",
                    len(self.documents), len(self.index))

    def save(self, path):
        """Save the index and all documents to a JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Convert term_freq keys from tuples to strings so JSON can store them
        serialisable_tf = {
            f"{doc_id}:{token}": count
            for (doc_id, token), count in self.term_freq.items()
        }

        data = {
            "documents": {str(k): asdict(v) for k, v in self.documents.items()},
            "index": self.index,
            "term_freq": serialisable_tf,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("Index saved to %s", path)

    def load(self, path):
        """Load the index and documents back from a JSON file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"No index file found at '{path}'. Run 'build' first.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Rebuild documents as Document objects
        self.documents = {
            int(k): Document(**v)
            for k, v in data["documents"].items()
        }

        # Restore the inverted index (JSON stores int keys as strings)
        self.index = {
            token: [int(doc_id) for doc_id in doc_ids]
            for token, doc_ids in data["index"].items()
        }

        # Restore term frequencies, converting string keys back to tuples
        self.term_freq = {}
        for key, count in data["term_freq"].items():
            doc_id_str, token = key.split(":", 1)
            self.term_freq[(int(doc_id_str), token)] = count

        logger.info("Index loaded from %s (%d docs, %d tokens).",
                    path, len(self.documents), len(self.index))

    def _preprocess(self, text):
        """
        Clean and normalise text into a list of stemmed tokens.
        Steps: lowercase -> tokenise -> remove stop words and punctuation -> stem
        """
        tokens = word_tokenize(text.lower())

        # Keep only alphabetic words and remove stop words
        cleaned = [
            stemmer.stem(word)
            for word in tokens
            if word.isalpha() and word not in STOP_WORDS
        ]

        return cleaned
