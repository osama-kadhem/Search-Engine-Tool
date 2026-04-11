# 🤖 Generative AI Evaluation & Reflection Report

**Institution:** University of Leeds  
**Module:** COMP3011 — Web Services and Web Data  
**Assessment Category:** Coursework 2: Search Engine Tool  
**Primary AI Partner:** Claude 3.5 Sonnet (Anthropic)  
**Traffic Light Classification:** 🟢 **GREEN** (Integral Role)

> *"A core part of this assessment (15% of the grade) is your critical reflection on GenAI usage... You must discuss specific examples of where GenAI helped or hindered your work, analyse the quality of AI-generated code, and reflect on how using (or not using) GenAI affected your learning."*

---

## 1. 🛡️ Formal Declaration of Use
In accordance with the **University of Leeds Generative AI (Gen AI) Policy**, I acknowledge the continuous integration of Claude 3.5 Sonnet throughout this project. It was utilised as a collaborative coding partner for foundational boilerplate generation, structural test suite scaffolding, and syntax validation. 

Crucially, **I take full responsibility for the final logic and mechanics of the codebase.** Every generated function was manually traced, evaluated against the coursework brief constraints (e.g., the 6-second politeness window), and independently verified using a 100% mocked testing environment.

---

## 2. 📊 Concrete Interaction & Verification Log

The table below provides granular evidence of exactly how the AI was critically managed to prevent hallucination or poor architectural design:

| Development Phase | What the AI Generated | 🛠️ My Critical Intervention / Verification |
| :--- | :--- | :--- |
| **Phase 1: Architecture & CLI** | Suggested using heavy external argument libraries and complex multi-file routing. | **Rejected**: I manually scaled this down to use Python's native `argparse` within a single `main.py` entrypoint. I overwrote default variables to explicitly map to `quotes.toscrape.com`. |
| **Phase 2: BFS Web Crawler** | Provided an initial `requests` crawler and suggested `lxml` for HTML parsing speed. | **Rejected & Improved**: I identified `lxml` as an unnecessary external dependency and overwrote it with standard `html.parser`. I also forced `requests.Session()` to recycle TCP connections safely. |
| **Phase 3: Index Data Storage** | Suggested a deeply nested nested dictionary structure mapping full strings to full URL arrays. | **Architectural Rewrite**: I manually refactored the design to map tokens efficiently to **Integer IDs**. This drastically reduced memory bloat, achieving the \( O(1) \) hash map lookup speeds. |
| **Phase 4: TF-IDF Engine** | Generated a raw Term Frequency loop that recalculated document totals locally per search query. | **Algorithmic Optimisation**: I flagged this as an \( O(N) \) mathematical bottleneck. I intervened by pre-computing all `_doc_lengths` during the class `__init__` instantiation instead. |
| **Phase 5: Pytest Suite** | Generated 70+ test stubs with raw networking calls to the domain. | **Critical Fix**: Pinging the live server invalidates isolated testing. I implemented `unittest.mock` to intercept network requests safely, independently writing 3 additional test cases to secure **100% branch coverage**. |

---

## 3. 🧠 Deep Reflection on Learning & Workflow Impact

### Did AI *Hinder* or *Help*?
The GenAI actively **helped** accelerate the trivial elements of software engineering (writing `import` statements, scaffolding `dataclasses`, generating boilerplate shell commands), but it repeatedly **hindered** highly specific algorithmic optimisations. The AI naturally gravitates toward "working" code, not "optimal" code. I found myself routinely debugging the AI's naive mathematical decisions—such as failing to cap memory via integer mapping in the inverted index, or suggesting overly heavy third-party HTML parsers.

### The Impact on My Personal Learning Curve
Rather than stunting my development, leaning heavily on GenAI for syntax allowed my mind to entirely shift gears. Instead of spending three hours hunting down a missing parenthesis or researching Pytest fixtures, I spent those hours mapping the **Big-O time complexity** of my NLP indexer. 

It taught me that modern software engineering is no longer about *memorising code*, but rather about **architectural oversight**. Because the AI could instantly draft the TF-IDF mathematical loop, my role elevated from "typist" to "Systems Architect." I had to mathematically verify the normalisation ratio and physically restructure the pipeline to escape an \( O(N) \) time-complexity trap.

### Summary
Generative AI acts as a brilliant, incredibly fast junior developer—but one that requires constant, rigorous supervision, security auditing, and mathematical correction to achieve a publication-ready grade.
