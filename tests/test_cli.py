# Tests for CLI commands

import json
import os
import sys
import types
from unittest.mock import MagicMock, patch, call
import pytest

# Make sure the project root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main
from main import build_parser, cmd_load, cmd_print, cmd_find


# ---- Parser tests ------------------------------------------------------------

class TestBuildParser:

    def test_build_command_is_registered(self):
        parser = build_parser()
        args = parser.parse_args(["build"])
        assert args.command == "build"

    def test_load_command_is_registered(self):
        parser = build_parser()
        args = parser.parse_args(["load"])
        assert args.command == "load"

    def test_print_command_is_registered(self):
        parser = build_parser()
        args = parser.parse_args(["print"])
        assert args.command == "print"

    def test_find_command_is_registered(self):
        parser = build_parser()
        args = parser.parse_args(["find", "love"])
        assert args.command == "find"
        assert args.query == "love"

    def test_find_default_top_n(self):
        parser = build_parser()
        args = parser.parse_args(["find", "life"])
        assert args.top_n == 10

    def test_find_custom_top_n(self):
        parser = build_parser()
        args = parser.parse_args(["find", "life", "--top-n", "5"])
        assert args.top_n == 5

    def test_build_default_output(self):
        parser = build_parser()
        args = parser.parse_args(["build"])
        assert args.output == "data/index.json"

    def test_build_custom_output(self):
        parser = build_parser()
        args = parser.parse_args(["build", "--output", "/tmp/idx.json"])
        assert args.output == "/tmp/idx.json"

    def test_build_custom_start_url(self):
        parser = build_parser()
        args = parser.parse_args(["build", "--start-url", "https://example.com"])
        assert args.start_url == "https://example.com"

    def test_load_default_index(self):
        parser = build_parser()
        args = parser.parse_args(["load"])
        assert args.index == "data/index.json"

    def test_no_command_raises(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--verbose", "find", "love"])
        assert args.verbose is True

    def test_func_is_set_for_each_command(self):
        parser = build_parser()
        for cmd in ["build", "load", "print"]:
            args = parser.parse_args([cmd])
            assert callable(args.func)
        args = parser.parse_args(["find", "test"])
        assert callable(args.func)


# ---- cmd_build tests ---------------------------------------------------------

class TestCmdBuild:

    def test_build_crawls_and_saves(self):
        args = MagicMock()
        args.start_url = "https://quotes.toscrape.com"
        args.output = "/tmp/test_build_output.json"

        fake_pages = [{"url": "https://quotes.toscrape.com", "title": "Home",
                       "quotes": [], "authors": [], "tags": []}]

        with patch("search_engine.crawler.Crawler") as MockCrawler, \
             patch("search_engine.indexer.Indexer") as MockIndexer:

            mock_crawler = MagicMock()
            mock_crawler.crawl.return_value = fake_pages
            MockCrawler.return_value = mock_crawler

            mock_indexer = MagicMock()
            MockIndexer.return_value = mock_indexer

            from main import cmd_build
            cmd_build(args)

            mock_crawler.crawl.assert_called_once()
            mock_indexer.build.assert_called_once_with(fake_pages)
            mock_indexer.save.assert_called_once_with(args.output)


# ---- cmd_load tests ----------------------------------------------------------

class TestCmdLoad:

    def test_load_calls_indexer_load(self, tmp_path):
        from search_engine.indexer import Indexer
        path = str(tmp_path / "index.json")
        idx = Indexer()
        idx.build([])
        idx.save(path)

        args = MagicMock()
        args.index = path

        # Patch inside the search_engine module since main.py imports lazily
        with patch("search_engine.indexer.Indexer") as MockIdx:
            mock_instance = MagicMock()
            MockIdx.return_value = mock_instance
            cmd_load(args)
            mock_instance.load.assert_called_once_with(path)

    def test_load_prints_confirmation(self, tmp_path, capsys):
        from search_engine.indexer import Indexer
        path = str(tmp_path / "index.json")
        idx = Indexer()
        idx.build([])
        idx.save(path)

        args = MagicMock()
        args.index = path

        with patch("search_engine.indexer.Indexer") as MockIdx:
            MockIdx.return_value = MagicMock()
            cmd_load(args)

        captured = capsys.readouterr()
        assert "loaded" in captured.out.lower()


# ---- cmd_print tests ---------------------------------------------------------

class TestCmdPrint:

    def test_print_calls_print_all(self):
        args = MagicMock()
        args.index = "data/index.json"

        with patch("search_engine.indexer.Indexer") as MockIdx, \
             patch("search_engine.searcher.Searcher") as MockSearch:
            mock_idx = MagicMock()
            mock_search = MagicMock()
            MockIdx.return_value = mock_idx
            MockSearch.return_value = mock_search
            cmd_print(args)
            mock_idx.load.assert_called_once_with("data/index.json")
            mock_search.print_all.assert_called_once()


# ---- cmd_find tests ----------------------------------------------------------

class TestCmdFind:

    def test_find_no_results_prints_message(self, capsys):
        args = MagicMock()
        args.index = "data/index.json"
        args.query = "zzznomatch"
        args.top_n = 10

        with patch("search_engine.indexer.Indexer") as MockIdx, \
             patch("search_engine.searcher.Searcher") as MockSearch:
            mock_search = MagicMock()
            mock_search.find.return_value = []
            MockSearch.return_value = mock_search
            MockIdx.return_value = MagicMock()
            cmd_find(args)

        captured = capsys.readouterr()
        assert "no results" in captured.out.lower()

    def test_find_with_results_prints_ranked_list(self, capsys):
        args = MagicMock()
        args.index = "data/index.json"
        args.query = "life"
        args.top_n = 10

        fake_results = [
            {"title": "Page One", "url": "https://quotes.toscrape.com", "score": 0.9, "snippet": "life is good"},
            {"title": "Page Two", "url": "https://quotes.toscrape.com/page/2", "score": 0.5, "snippet": ""},
        ]

        with patch("search_engine.indexer.Indexer") as MockIdx, \
             patch("search_engine.searcher.Searcher") as MockSearch:
            mock_search = MagicMock()
            mock_search.find.return_value = fake_results
            MockSearch.return_value = mock_search
            MockIdx.return_value = MagicMock()
            cmd_find(args)

        captured = capsys.readouterr()
        assert "Page One" in captured.out
        assert "0.9000" in captured.out

    def test_find_passes_top_n_to_searcher(self):
        args = MagicMock()
        args.index = "data/index.json"
        args.query = "love"
        args.top_n = 3

        with patch("search_engine.indexer.Indexer") as MockIdx, \
             patch("search_engine.searcher.Searcher") as MockSearch:
            mock_search = MagicMock()
            mock_search.find.return_value = []
            MockSearch.return_value = mock_search
            MockIdx.return_value = MagicMock()
            cmd_find(args)
            mock_search.find.assert_called_once_with("love", top_n=3)


# ---- main() integration tests ------------------------------------------------

class TestMain:

    def test_main_verbose_sets_debug_level(self):
        with patch("sys.argv", ["search_tool", "--verbose", "find", "love"]), \
             patch("search_engine.indexer.Indexer") as MockIdx, \
             patch("search_engine.searcher.Searcher") as MockSearch:
            mock_search = MagicMock()
            mock_search.find.return_value = []
            MockSearch.return_value = mock_search
            MockIdx.return_value = MagicMock()

            import logging
            from main import main
            main()
            assert logging.getLogger().level == logging.DEBUG

    def test_main_file_not_found_exits_with_code_1(self):
        with patch("sys.argv", ["search_tool", "load"]), \
             patch("search_engine.indexer.Indexer") as MockIdx:
            mock_instance = MagicMock()
            mock_instance.load.side_effect = FileNotFoundError("no index")
            MockIdx.return_value = mock_instance

            from main import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_keyboard_interrupt_exits_cleanly(self, capsys):
        with patch("sys.argv", ["search_tool", "find", "love"]), \
             patch("search_engine.indexer.Indexer") as MockIdx, \
             patch("search_engine.searcher.Searcher") as MockSearch:
            mock_search = MagicMock()
            mock_search.find.side_effect = KeyboardInterrupt()
            MockSearch.return_value = mock_search
            MockIdx.return_value = MagicMock()

            from main import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            assert "Interrupted" in capsys.readouterr().out

