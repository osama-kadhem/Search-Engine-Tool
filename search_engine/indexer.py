# Builds an inverted index from crawled pages and saves/loads it to disk.
#
# For each page we:
#   1. Join all text (title, quotes, authors, tags) into one string
#   2. Lowercase and tokenise
#   3. Drop stop words (the, a, is …)
#   4. Stem each word (running → run) so similar words match
#   5. Record which documents contain each token

import json
import os
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

logger = logging.getLogger(__name__)

# Load these once at module level — they don't change between calls
STOP_WORDS = set(stopwords.words("english"))
stemmer = PorterStemmer()


@dataclass
class Document:
    """One crawled page stored in the index."""
    doc_id: int
    url: str
    title: str
    quotes: List[str]
    authors: List[str]
    tags: List[str]

    def full_text(self) -> str:
        """Return all text fields joined into a single string."""
        parts = [self.title] + self.quotes + self.authors + self.tags
        return " ".join(parts)


class Indexer:
    """Builds and stores an inverted index from crawled page data."""

    def __init__(self) -> None:
        self.documents: Dict[int, Document] = {}   # doc_id → Document
        self.index: Dict[str, List[int]] = {}       # token  → list of doc_ids
        self.term_freq: Dict[Tuple[int, str], int] = {}   # (doc_id, token) → count  (used for TF-IDF scoring)

    def build(self, pages: List[Dict[str, Any]]) -> None:
        """Build the index from a list of page dicts returned by the Crawler."""
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

            tokens = self._preprocess(doc.full_text())

            # Count how many times each token appears in this document
            for token in tokens:
                self.term_freq[(doc_id, token)] = self.term_freq.get((doc_id, token), 0) + 1

            # Add this document to each token's posting list (once per token)
            for token in set(tokens):
                self.index.setdefault(token, []).append(doc_id)

        logger.info(
            "Index built: %d documents, %d unique tokens.",
            len(self.documents), len(self.index),
        )

    def save(self, path: str) -> None:
        """Write the index to a JSON file, creating directories if needed."""
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # JSON can't store tuple keys, so we encode (doc_id, token) as "doc_id:token"
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

    def load(self, path: str) -> None:
        """Load a previously saved index from disk."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"No index file at '{path}'. Run 'build' first.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Rebuild Document objects (JSON stores all keys as strings)
        self.documents = {
            int(k): Document(**v)
            for k, v in data["documents"].items()
        }

        # doc_ids in the index were stored as strings — convert back to ints
        self.index = {
            token: [int(doc_id) for doc_id in doc_ids]
            for token, doc_ids in data["index"].items()
        }

        # Decode "doc_id:token" keys back into (int, str) tuples
        self.term_freq = {}
        for key, count in data["term_freq"].items():
            doc_id_str, token = key.split(":", 1)
            self.term_freq[(int(doc_id_str), token)] = count

        logger.info(
            "Index loaded from %s (%d docs, %d tokens).",
            path, len(self.documents), len(self.index),
        )

    def _preprocess(self, text: str) -> List[str]:
        """Lowercase, tokenise, remove stop words, and stem."""
        tokens = word_tokenize(text.lower())
        return [
            stemmer.stem(word)
            for word in tokens
            if word.isalpha() and word not in STOP_WORDS
        ]
