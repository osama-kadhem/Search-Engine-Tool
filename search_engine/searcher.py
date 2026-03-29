"""
Searcher - runs TF-IDF ranked search over the inverted index.
"""

import math
import logging

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

logger = logging.getLogger(__name__)

STOP_WORDS = set(stopwords.words("english"))
stemmer = PorterStemmer()


class Searcher:
    """Performs ranked search over a built Indexer."""

    def __init__(self, indexer):
        self.indexer = indexer
        # Pre-compute each document's total term count once to avoid repeating
        # the scan inside the scoring loop for every query token.
        self._doc_lengths = {}
        for (doc_id, _), count in indexer.term_freq.items():
            self._doc_lengths[doc_id] = self._doc_lengths.get(doc_id, 0) + count

    def find(self, query, top_n=10):
        """Return the top N documents ranked by TF-IDF score for the given query."""
        query_tokens = self._preprocess(query)

        if not query_tokens:
            return []

        scores = {}
        n_docs = len(self.indexer.documents)

        for token in set(query_tokens):  # deduplicate so repeated words don't inflate scores
            posting = self.indexer.index.get(token, [])
            if not posting:
                continue

            # IDF: how rare the term is across all documents
            idf = math.log((n_docs + 1) / (len(posting) + 1)) + 1

            for doc_id in posting:
                tf = self.indexer.term_freq.get((doc_id, token), 0)
                # Normalise TF by document length to avoid bias toward long docs
                doc_len = self._doc_lengths.get(doc_id, 1)
                tf_normalised = tf / doc_len
                scores[doc_id] = scores.get(doc_id, 0.0) + tf_normalised * idf

        # Sort by score descending and take top N
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

        results = []
        for doc_id, score in ranked:
            doc = self.indexer.documents[doc_id]
            results.append({
                "title": doc.title,
                "url": doc.url,
                "score": score,
                "snippet": self._snippet(doc, query_tokens),
            })

        return results

    def print_all(self):
        """Print every document in the index with its metadata."""
        docs = self.indexer.documents

        if not docs:
            print("Index is empty.")
            return

        print(f"{'ID':<5} {'Title':<40} {'URL'}")
        print("-" * 90)
        for doc_id, doc in sorted(docs.items()):
            print(f"{doc_id:<5} {doc.title[:40]:<40} {doc.url}")

    def _preprocess(self, text):
        """Apply the same pipeline as the indexer: lowercase, stop words, stemming."""
        tokens = word_tokenize(text.lower())
        return [
            stemmer.stem(w)
            for w in tokens
            if w.isalpha() and w not in STOP_WORDS
        ]

    def _snippet(self, doc, query_tokens, window=10):
        """
        Extract a short snippet from the document text around the first query match.
        Falls back to the first few words if no match is found.
        """
        words = doc.full_text().split()
        stemmed_words = [stemmer.stem(w.lower()) for w in words]

        # Find the first position where a query token appears
        for i, stem in enumerate(stemmed_words):
            if stem in query_tokens:
                start = max(0, i - window // 2)
                end = min(len(words), i + window // 2 + 1)
                return " ".join(words[start:end])

        # No match found — return the beginning of the text
        return " ".join(words[:window])
