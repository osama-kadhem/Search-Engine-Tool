# Generative AI Reflection Log — COMP3011 CW2

**Institution:** University of Leeds  
**Module:** COMP3011 — Web Services and Web Data  
**Assessment:** Coursework 2: Search Engine Tool  
**AI Tool Used:** Claude 3.5 Sonnet (Anthropic)  

## Acknowledgment of Generative AI Use

In accordance with the **University of Leeds Generative AI (Gen AI) Policy**, I acknowledge the use of Claude to assist in the development of this project. This assessment was classified under the **"Green"** traffic light category, meaning Gen AI was intended to have an **integral role** in the development process. 

I have used the tool to demonstrate critical engagement with the technology, including prompt engineering, code generation, and debugging support. I have taken full responsibility for the final output, ensuring that every AI contribution was reviewed, tested, and understood in the context of the assessment requirements.

---

## Declaration of Authorship and Responsibility

1.  **Critical Engagement:** I have critically evaluated all AI outputs for accuracy, efficiency, and compliance with the project brief.
2.  **Verification:** Every function has been manually traced and tested using the included `pytest` suite to ensure correct logic and 100% test coverage.
3.  **Integral Role:** AI was used as an integral part of the development lifecycle, from initial scaffolding to final test coverage, demonstrating effective use of technical assistance tools.

---

## Interaction Log

The following log details specific interactions where AI played an integral role.

### Interaction 1 — Project Planning and Phase 1 (CLI Scaffold)
- **Task:** Initial project structure and CLI argument parser.
- **Prompt:** "Save this plan to the project directory and start Phase 1. Use argparse for build, load, print, and find commands."
- **AI Tool Input:** Coursework brief and Phase-by-Phase plan.
- **AI Contribution:** Generated `main.py` CLI structure, `requirements.txt`, and basic project folder layout.
- **Critical Review & Modification:** 
    - I reviewed the generated CLI to ensure it matched the specific requirements of the COMP3011 brief.
    - I manually adjusted the default values for `--top-n` and the index file path to ensure consistency across the project.
    - I verified that the initial `Crawler` stub already enforced the 6-second politeness delay.

### Interaction 2 — Web Crawler Implementation (Phase 2)
- **Task:** Implementing the core crawling engine.
- **Prompt:** "Implement the Crawler class for quotes.toscrape.com. Must follow only internal links and collect url, title, quotes, authors, and tags."
- **AI Contribution:** Provided a `requests`-based crawler with link normalization.
- **Critical Review & Modification:**
    - I found the AI had initially used the `lxml` parser, which was an unnecessary external dependency. I manually changed this to the built-in `html.parser`.
    - I added logic to handle potential fragments and trailing slashes to ensure the crawler did not visit the same page twice (deduplication).
    - I verified the politeness window logic by tracking the `time.sleep` calls in the logs.

### Interaction 3 — Indexer and Data Storage (Phase 3)
- **Task:** Building the inverted index and JSON serialization.
- **Prompt:** "Create an Indexer class. Use NLTK for tokenisation and Porter Stemmer for stemming. Support JSON save/load."
- **AI Contribution:** Suggested the `Document` dataclass and the implementation of a token-to-document inverted index.
- **Critical Review & Modification:**
    - I manually added `os.makedirs` to the `save` method because the AI-generated code initially failed when the output directory did not exist.
    - I simplified the serialization of the `term_freq` dictionary from a complex nested dict to a flat "doc:token" string key format to ensure better JSON compatibility.
    - I removed unused imports (`math` and `nltk` in the indexer module) that the AI included by default.

### Interaction 4 — TF-IDF Ranking and Search (Phase 4)
- **Task:** Implementing ranked retrieval and result snippets.
- **Prompt:** "Implement TF-IDF ranking in the Searcher class. Include a snippet generator that finds the match in the text."
- **AI Contribution:** Provided the TF-IDF scoring algorithm and a sliding-window snippet generator.
- **Critical Review & Modification:**
    - I modified the TF-IDF calculation to pre-compute document lengths in the `__init__` method for better performance during multi-query searches.
    - I refined the `_snippet` method to ensure it correctly handled cases where the query term appeared in different cases (e.g., lowercase vs uppercase).
    - I manually verified the ranking by testing specific queries (e.g., "life") against expected results on the source website.

### Interaction 5 — Test Suite and Coverage (Phase 5)
- **Task:** Developing a comprehensive test suite to reach 100% coverage.
- **Prompt:** "Generate a pytest suite for the crawler, indexer, and searcher. Use mocks for HTTP calls."
- **AI Contribution:** Provided 78 initial test cases with mocked HTTP responses.
- **Critical Review & Modification:**
    - I independently diagnosed and fixed three failing tests related to Unicode character mismatches and incorrect mocking of the CLI's lazy imports.
    - I added three additional test cases to reach 100% coverage, specifically targeting the "already visited" crawler branch and the searcher's snippet fallback.
    - I configured `pytest.ini` and `.coveragerc` to automate the reporting process.

---

## Final Verification
I have cross checked the final codebase with the coursework marking criteria. The design decisions, such as the 6-second crawl delay, the specific pre-processing pipeline, and the TF-IDF ranking system, were all implemented to satisfy the academic requirements for COMP3011 while demonstrating the effective use of Generative AI.
