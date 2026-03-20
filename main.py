"""
COMP3011 Coursework 2 - Search Engine Tool
CLI entry point. Run with --help to see available commands.

Usage:
  python3 main.py build [--start-url URL] [--output data/index.json]
  python3 main.py load  [--index data/index.json]
  python3 main.py print [--index data/index.json]
  python3 main.py find  <query> [--index data/index.json] [--top-n 10]
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("search_tool")

DEFAULT_INDEX = "data/index.json"
DEFAULT_START_URL = "https://quotes.toscrape.com"
DEFAULT_TOP_N = 10


def cmd_build(args):
    """Crawl the site, build the inverted index, and save it to disk."""
    from search_engine.crawler import Crawler
    from search_engine.indexer import Indexer

    logger.info("Starting crawl from: %s", args.start_url)
    crawler = Crawler(base_url=args.start_url)
    pages = crawler.crawl()
    logger.info("Crawl complete - %d pages collected.", len(pages))

    indexer = Indexer()
    indexer.build(pages)
    indexer.save(args.output)
    logger.info("Index saved to: %s", args.output)


def cmd_load(args):
    """Load a previously saved index from disk."""
    from search_engine.indexer import Indexer

    indexer = Indexer()
    indexer.load(args.index)
    print(f"Index loaded from '{args.index}'.")


def cmd_print(args):
    """Print every document stored in the index."""
    from search_engine.indexer import Indexer
    from search_engine.searcher import Searcher

    indexer = Indexer()
    indexer.load(args.index)

    searcher = Searcher()
    searcher.print_all()


def cmd_find(args):
    """Search the index and display ranked results."""
    from search_engine.indexer import Indexer
    from search_engine.searcher import Searcher

    logger.info("Searching for: %r  (top %d)", args.query, args.top_n)
    indexer = Indexer()
    indexer.load(args.index)

    searcher = Searcher()
    results = searcher.find(args.query, top_n=args.top_n)

    if not results:
        print("No results found.")
        return

    for rank, doc in enumerate(results, start=1):
        print(f"\n[{rank}] {doc.get('title', '(no title)')}")
        print(f"    URL   : {doc.get('url', '')}")
        print(f"    Score : {doc.get('score', 0):.4f}")
        snippet = doc.get("snippet", "")
        if snippet:
            print(f"    ...{snippet}...")


def build_parser():
    """Set up the argument parser with all four subcommands."""
    parser = argparse.ArgumentParser(
        prog="search_tool",
        description="COMP3011 CW2 - Search Engine for quotes.toscrape.com",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show debug-level log messages.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # build: crawl and save
    p_build = subparsers.add_parser("build", help="Crawl the site and build the index.")
    p_build.add_argument("--start-url", default=DEFAULT_START_URL, metavar="URL",
                         help=f"Where to start crawling (default: {DEFAULT_START_URL})")
    p_build.add_argument("--output", default=DEFAULT_INDEX, metavar="FILE",
                         help=f"Where to save the index (default: {DEFAULT_INDEX})")
    p_build.set_defaults(func=cmd_build)

    # load: read a saved index
    p_load = subparsers.add_parser("load", help="Load a saved index from disk.")
    p_load.add_argument("--index", default=DEFAULT_INDEX, metavar="FILE",
                        help=f"Path to the index file (default: {DEFAULT_INDEX})")
    p_load.set_defaults(func=cmd_load)

    # print: list all documents
    p_print = subparsers.add_parser("print", help="Print all indexed documents.")
    p_print.add_argument("--index", default=DEFAULT_INDEX, metavar="FILE",
                         help=f"Path to the index file (default: {DEFAULT_INDEX})")
    p_print.set_defaults(func=cmd_print)

    # find: search and rank
    p_find = subparsers.add_parser("find", help="Search the index for a query.")
    p_find.add_argument("query", help="Words to search for, e.g. 'life love'")
    p_find.add_argument("--index", default=DEFAULT_INDEX, metavar="FILE",
                        help=f"Path to the index file (default: {DEFAULT_INDEX})")
    p_find.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, metavar="N",
                        help=f"How many results to show (default: {DEFAULT_TOP_N})")
    p_find.set_defaults(func=cmd_find)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        args.func(args)
    except NotImplementedError as exc:
        logger.error("Not implemented yet: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
