"""
Searcher - runs TF-IDF ranked search over the inverted index.
Full implementation coming in Phase 4.
"""


class Searcher:
    """Performs ranked search over a built Indexer."""

    def find(self, query, top_n=10):
        """Return the top N documents ranked by relevance to query. (Phase 4)"""
        raise NotImplementedError("Phase 4: implement Searcher.find()")

    def print_all(self):
        """Print every document in the index. (Phase 4)"""
        raise NotImplementedError("Phase 4: implement Searcher.print_all()")
