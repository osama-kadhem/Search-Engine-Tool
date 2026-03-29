# Ranks documents against a search query using TF-IDF scoring.

import math
import logging

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

logger = logging.getLogger(__name__)

# Same settings as the indexer — must match or scores will be wrong
STOP_WORDS = set(stopwords.words("english"))
stemmer = PorterStemmer()


class Searcher:
    """Searches a built Indexer and returns ranked results."""

    def __init__(self, indexer):
        self.indexer = indexer

        # Sum up how many tokens each document contains.
        # We do this once here so the find() loop doesn't re-scan on every query.
        self._doc_lengths = {}
        for (doc_id, _), count in indexer.term_freq.items():
            self._doc_lengths[doc_id] = self._doc_lengths.get(doc_id, 0) + count

    def find(self, query, top_n=10):
        """Return the top N documents for the query, ranked by TF-IDF score."""
        query_tokens = self._preprocess(query)

        if not query_tokens:
            return []

        scores = {}
        n_docs = len(self.indexer.documents)

        # Score each document that contains at least one query token
        for token in set(query_tokens):  # use set so repeated words don't double-count
            posting = self.indexer.index.get(token, [])
            if not posting:
                continue

            # IDF tells us how rare (and therefore valuable) this term is
            idf = math.log((n_docs + 1) / (len(posting) + 1)) + 1

            for doc_id in posting:
                tf = self.indexer.term_freq.get((doc_id, token), 0)
                # Divide TF by doc length so long documents don't score unfairly
                doc_len = self._doc_lengths.get(doc_id, 1)
                scores[doc_id] = scores.get(doc_id, 0.0) + (tf / doc_len) * idf

        # Sort highest score first and keep only the top N
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
        """Print every document in the index as a simple table."""
        docs = self.indexer.documents

        if not docs:
            print("Index is empty.")
            return

        print(f"{'ID':<5} {'Title':<40} {'URL'}")
        print("-" * 90)
        for doc_id, doc in sorted(docs.items()):
            print(f"{doc_id:<5} {doc.title[:40]:<40} {doc.url}")

    def _preprocess(self, text):
        """Apply the same cleaning pipeline as the indexer."""
        tokens = word_tokenize(text.lower())
        return [
            stemmer.stem(w)
            for w in tokens
            if w.isalpha() and w not in STOP_WORDS
        ]

    def _snippet(self, doc, query_tokens, window=10):
        """
        Find the first query word in the document and return the words around it.
        Falls back to the opening words if nothing matches.
        """
        words = doc.full_text().split()
        stemmed = [stemmer.stem(w.lower()) for w in words]

        for i, stem in enumerate(stemmed):
            if stem in query_tokens:
                start = max(0, i - window // 2)
                end = min(len(words), i + window // 2 + 1)
                return " ".join(words[start:end])

        # No match — just show the start of the document
        return " ".join(words[:window])
