"""
Indexer - builds an inverted index from crawled pages and saves/loads it.
Full implementation coming in Phase 3.
"""


class Indexer:
    """Builds and stores an inverted index from crawled page data."""

    def build(self, pages):
        """Build the index from a list of page dicts. (Phase 3)"""
        raise NotImplementedError("Phase 3: implement Indexer.build()")

    def save(self, path):
        """Save the index to a JSON file. (Phase 3)"""
        raise NotImplementedError("Phase 3: implement Indexer.save()")

    def load(self, path):
        """Load the index from a JSON file. (Phase 3)"""
        raise NotImplementedError("Phase 3: implement Indexer.load()")
