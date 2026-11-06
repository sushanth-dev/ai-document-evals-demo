# AI Document Evals Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade Python library and evaluation benchmark for B2B contract extraction with calibrated confidence scoring, human-in-the-loop triage, and 10 deterministic regression fixtures.

**Architecture:** A modular pipeline where raw document text is extracted and parsed into Pydantic models with verbatim text spans, evaluated by a confidence scoring engine checking span validity, filtered through an automated triage threshold gate, and benchmarked against ground truth via a CLI evaluation runner.

**Tech Stack:** Python 3.11+, Pydantic V2, pytest, rich, pdfplumber.

**Spec:** `docs/superpowers/specs/2026-11-06-ai-document-evals-design.md`

## Global Constraints
- Python 3.11+ using standard library and minimal dependencies (Pydantic V2, pytest, rich, pdfplumber).
- Zero paid API key requirements to run `pytest` and benchmark runner (deterministic local extraction engine included).
- Zero proprietary data from TC Agent: all 10 fixtures are synthetic commercial agreements.
- Sub-2-second total execution time for all tests and evaluation benchmarks.

## Review Focus
1. **Missing critical fields:** When a contract has no termination clause or liability cap, confidence must drop to 0.0 for that field and trigger `NEEDS_HUMAN_REVIEW` without throwing an exception.
2. **Ambiguous or conflicting spans:** When multiple conflicting dates appear (e.g. preamble date vs signature date), the scorer must flag the date ambiguity rather than silently picking one with 1.0 confidence.
3. **Fuzzy formatting equivalence:** Normalized numbers (`$50,000` vs `50000`) and dates (`October 12, 2026` vs `2026-10-12`) must achieve high confidence (`>= 0.85`) through normalization without failing exact substring matching.
4. **Hallucinated values:** If an extraction yields a value with no matching span in the document text, confidence must strictly evaluate to `0.0` and flag `SPAN_NOT_FOUND`.
5. **Zero-dollar contracts:** Contracts with `contract_value_usd = 0.0` (such as mutual NDAs) must not be treated as missing or falsy values; they must maintain valid numeric scoring.

---

### Task 1: Environment & Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: Project root configuration, packaging, and dependency definitions for Pydantic V2, pytest, and rich.

- [ ] **Step 1: Create `pyproject.toml` with build configuration and dependencies**
- [ ] **Step 2: Create `.gitignore` for Python, virtual environments, and test caches**
- [ ] **Step 3: Create `src/__init__.py`**
- [ ] **Step 4: Verify environment by running `python3 -m pytest`**
- [ ] **Step 5: Commit scaffolding**
```bash
git add pyproject.toml .gitignore src/__init__.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: Pydantic Data Contracts & Schemas

**Files:**
- Create: `src/schemas.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces:
  - `ContractExtraction` (Pydantic model of parsed contract terms)
  - `FieldScore` (Pydantic model containing value, verbatim span, confidence float, and warning flags)
  - `ScoredExtraction` (Pydantic model containing dictionary of field scores, overall confidence, triage status, and triage reasons)
  - `TriageStatus` (Enum: `AUTO_APPROVED`, `NEEDS_HUMAN_REVIEW`)

- [ ] **Step 1: Write failing test in `tests/test_schemas.py`**
Verify `ContractExtraction`, `FieldScore`, and `ScoredExtraction` validate types, bounds, and defaults correctly.
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_schemas.py -v` (FAIL: module not found)
- [ ] **Step 3: Implement schemas in `src/schemas.py`**
Define Pydantic V2 models with field constraints and serialization helpers.
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_schemas.py -v` (PASS)
- [ ] **Step 5: Commit**
```bash
git add src/schemas.py tests/test_schemas.py
git commit -m "feat: define contract extraction and scoring schemas"
```

---

### Task 3: Verbatim Span-Matching Confidence Scorer

**Files:**
- Create: `src/scorer.py`
- Test: `tests/test_scorer.py`

**Interfaces:**
- Consumes: `ContractExtraction`, `FieldScore` from `src/schemas.py`
- Produces: `score_field(raw_text: str, field_name: str, value: Any, span: str | None) -> FieldScore`
- Produces: `compute_overall_confidence(field_scores: dict[str, FieldScore]) -> float`

- [ ] **Step 1: Write failing tests in `tests/test_scorer.py`**
Test exact span match (1.0), normalized match (0.9), missing span (0.0), and empty/None values.
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_scorer.py -v` (FAIL)
- [ ] **Step 3: Implement `src/scorer.py`**
Implement text normalization, substring presence check, fuzzy numeric/date equivalence, and weighted confidence aggregation.
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_scorer.py -v` (PASS)
- [ ] **Step 5: Commit**
```bash
git add src/scorer.py tests/test_scorer.py
git commit -m "feat: implement verbatim span confidence scoring engine"
```

---

### Task 4: Human-in-the-Loop Triage Gate

**Files:**
- Create: `src/triage.py`
- Test: `tests/test_triage.py`

**Interfaces:**
- Consumes: `FieldScore`, `ScoredExtraction`, `TriageStatus` from `src/schemas.py`
- Produces: `evaluate_triage(field_scores: dict[str, FieldScore], overall_confidence: float) -> tuple[TriageStatus, list[str]]`

- [ ] **Step 1: Write failing tests in `tests/test_triage.py`**
Test auto-approval when confidence >= 0.85 and critical fields pass; test triage routing when overall confidence < 0.85 or liability cap < 0.80.
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_triage.py -v` (FAIL)
- [ ] **Step 3: Implement `src/triage.py`**
Define triage threshold constants (`CONFIDENCE_THRESHOLD = 0.85`, `CRITICAL_FIELD_THRESHOLD = 0.80`) and reason generator.
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_triage.py -v` (PASS)
- [ ] **Step 5: Commit**
```bash
git add src/triage.py tests/test_triage.py
git commit -m "feat: implement automated human-in-the-loop triage gate"
```

---

### Task 5: Document Extractor with Deterministic Engine

**Files:**
- Create: `src/extractor.py`
- Test: `tests/test_extractor.py`

**Interfaces:**
- Consumes: `ContractExtraction`, `ScoredExtraction`, `src/scorer.py`, `src/triage.py`
- Produces: `extract_and_score(document_text: str) -> ScoredExtraction`

- [ ] **Step 1: Write failing tests in `tests/test_extractor.py`**
Test end-to-end extraction and scoring on a sample contract string.
- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_extractor.py -v` (FAIL)
- [ ] **Step 3: Implement `src/extractor.py`**
Build rule-based and regex extraction engine with verbatim span location, followed by confidence scoring and triage evaluation.
- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_extractor.py -v` (PASS)
- [ ] **Step 5: Commit**
```bash
git add src/extractor.py tests/test_extractor.py
git commit -m "feat: build contract extraction and scoring pipeline"
```

---

### Task 6: 10 Synthetic Contract Fixtures and Ground Truth

**Files:**
- Create: `fixtures/contracts/01_clean_standard_msa.txt` through `10_zero_dollar_nda.txt`
- Create: `fixtures/ground_truth.json`
- Test: `tests/test_fixtures.py`

**Interfaces:**
- Produces: 10 synthetic test contracts representing edge cases (OCR typos, missing clauses, extreme liability, ambiguous dates) and verified expected values in JSON.

- [ ] **Step 1: Author 10 synthetic contract text files in `fixtures/contracts/`**
- [ ] **Step 2: Create `fixtures/ground_truth.json` mapping each contract to expected fields and expected triage status**
- [ ] **Step 3: Write test in `tests/test_fixtures.py` verifying all 10 fixtures load and parse without error**
- [ ] **Step 4: Run test to verify fixtures pass**
Run: `pytest tests/test_fixtures.py -v` (PASS)
- [ ] **Step 5: Commit**
```bash
git add fixtures/ tests/test_fixtures.py
git commit -m "test: add 10 synthetic contract fixtures and ground truth labels"
```

---

### Task 7: Benchmark CLI Evaluation Harness & Terminal Reporter

**Files:**
- Create: `evals/run_evals.py`
- Test: `tests/test_eval_runner.py`

**Interfaces:**
- Consumes: All 10 fixtures, `fixtures/ground_truth.json`, and `src/extractor.py`
- Produces: CLI benchmark runner printing execution metrics, accuracy percentages, and triage confusion matrix using `rich`.

- [ ] **Step 1: Write test verifying eval calculation logic**
- [ ] **Step 2: Implement `evals/run_evals.py` with CLI arguments and rich table output**
- [ ] **Step 3: Run benchmark via CLI**
Run: `python3 evals/run_evals.py`
Expected: Formatted terminal table showing 10/10 test cases evaluated, accuracy breakdown, and pass/fail summary.
- [ ] **Step 4: Commit**
```bash
git add evals/ tests/test_eval_runner.py
git commit -m "feat: build CLI evaluation harness and benchmark reporter"
```

---

### Task 8: Production README & Architecture Documentation

**Files:**
- Create: `README.md`

**Interfaces:**
- Produces: Concise 60-second technical breakdown, installation steps, architecture diagram, sample benchmark output, and design trade-offs.

- [ ] **Step 1: Write `README.md` following terse engineer conventions**
- [ ] **Step 2: Run complete test suite and CLI eval to capture real output for README**
Run: `pytest && python3 evals/run_evals.py`
- [ ] **Step 3: Commit**
```bash
git add README.md
git commit -m "docs: add architecture documentation and benchmark results"
```
