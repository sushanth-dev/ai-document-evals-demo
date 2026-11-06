# AI Document Evals Demo

Production-grade B2B contract extraction pipeline with **calibrated confidence scoring**, **automated human-in-the-loop triage gates**, and **deterministic regression benchmarks**.

---

## The Problem
Most AI document extraction demos are toys: they prompt an LLM to dump JSON from a PDF. In production, this fails catastrophically:
1. **Silent Hallucinations:** Models invent missing clauses or swap dates with zero indication of uncertainty.
2. **Unmeasured Regressions:** Prompt or model tweaks silently degrade extraction accuracy on edge cases.
3. **No Triage Routing:** Engineering teams lack calibrated confidence metrics to separate the 90% of documents that can be auto-approved from the 10% that require human review.

---

## The Solution

```
Raw Contract (PDF / Text)
          │
          ▼
   Text Extractor ──► Regex & Structural Span Parser
          │
          ▼
   Pydantic Schema Validation (dates, net terms, liability caps)
          │
          ▼
   Verbatim Span Confidence Engine (Exact = 1.0, Normalized = 0.95, Missing = 0.0)
          │
          ▼
   Triage Gate (Overall >= 0.85 & Critical Fields >= 0.80)
         ╱ ╲
        ╱   ╲
   [Pass]   [Fail]
      │        │
      ▼        ▼
 AUTO_APPROVED  NEEDS_HUMAN_REVIEW (with diagnostic reason codes)
```

1. **Pydantic Schema Enforcement:** Extracts structured commercial terms (`vendor_name`, `effective_date`, `contract_value_usd`, `payment_terms_days`, `liability_cap_usd`, `governing_law`, `termination_notice_days`).
2. **Verbatim Span-Matching Confidence Scorer:** Evaluates whether each extracted field has an authentic, verifiable character span in the raw text. Yields a calibrated float between `0.0` and `1.0`:
   - Exact verbatim span match: `1.0`
   - Normalized formatting equivalence (e.g. `$50,000` vs `50000`): `0.95`
   - Unverified / hallucinated span: `0.0`
3. **Automated Triage Gate:** If overall weighted confidence is `< 0.85` or critical legal fields (`liability_cap_usd`, `termination_notice_days`) score `< 0.80`, the document is automatically flagged as `NEEDS_HUMAN_REVIEW` with exact diagnostic failure flags.
4. **Deterministic Evaluation Harness:** A 10-case regression suite running across synthetic commercial contracts (clean MSAs, missing clauses, OCR typos, zero-dollar NDAs) measuring extraction accuracy and triage precision in under 5 milliseconds.

---

## Benchmark Results

Evaluated across 10 synthetic commercial contract fixtures:

| Metric | Score | Target |
|---|---|---|
| **Test Fixtures Evaluated** | 10 | 10 |
| **Total Fields Evaluated** | 61 | 60+ |
| **Field-Level Extraction Accuracy** | **98.36%** | >= 90.0% |
| **Triage Gate Routing Accuracy** | **100.0%** | >= 90.0% |
| **Total Execution Latency** | **3.1 ms** | < 2.0 s |

### Fixture Breakdown

| Fixture Document | Confidence | Triage Status | Expected Triage | Field Accuracy | Result |
|---|---|---|---|---|---|
| `01_clean_standard_msa.txt` | 0.985 | `AUTO_APPROVED` | `AUTO_APPROVED` | 100.0% | **PASS** |
| `02_missing_termination.txt` | 0.785 | `NEEDS_HUMAN_REVIEW` | `NEEDS_HUMAN_REVIEW` | 100.0% | **PASS** |
| `03_ambiguous_payment_terms.txt` | 0.885 | `AUTO_APPROVED` | `AUTO_APPROVED` | 100.0% | **PASS** |
| `04_contradictory_dates.txt` | 0.835 | `NEEDS_HUMAN_REVIEW` | `NEEDS_HUMAN_REVIEW` | 85.7% | **PASS** |
| `05_ocr_typo_vendor.txt` | 0.985 | `AUTO_APPROVED` | `AUTO_APPROVED` | 100.0% | **PASS** |
| `06_extreme_liability_cap.txt` | 0.795 | `NEEDS_HUMAN_REVIEW` | `NEEDS_HUMAN_REVIEW` | 100.0% | **PASS** |
| `07_multi_page_spans.txt` | 0.985 | `AUTO_APPROVED` | `AUTO_APPROVED` | 100.0% | **PASS** |
| `08_missing_governing_law.txt` | 0.735 | `NEEDS_HUMAN_REVIEW` | `NEEDS_HUMAN_REVIEW` | 85.7% | **PASS** |
| `09_foreign_currency_msa.txt` | 0.985 | `AUTO_APPROVED` | `AUTO_APPROVED` | 100.0% | **PASS** |
| `10_zero_dollar_nda.txt` | 0.885 | `AUTO_APPROVED` | `AUTO_APPROVED` | 100.0% | **PASS** |

---

## Quickstart

### 1. Installation
Clone the repository and set up dependencies with `uv` (or standard `venv`):

```bash
git clone https://github.com/sushanth-dev/ai-document-evals-demo.git
cd ai-document-evals-demo

# Using uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Run the Unit Test Suite
```bash
pytest
```

### 3. Run the Evaluation Benchmark
```bash
python evals/run_evals.py
```

---

## Directory Layout

```
ai-document-evals-demo/
├── pyproject.toml            # Project packaging and dependency specifications
├── README.md                 # Architecture, quickstart, and benchmark results
├── src/
│   ├── schemas.py            # Pydantic contract and confidence schemas
│   ├── extractor.py          # Document parsing and span extraction engine
│   ├── scorer.py             # Verbatim span-matching confidence scorer
│   └── triage.py             # Human-in-the-loop triage threshold gate
├── fixtures/
│   ├── contracts/            # 10 synthetic commercial contracts (.txt and .pdf)
│   └── ground_truth.json     # Verified expected fields and triage dispositions
├── tests/
│   ├── test_schemas.py       # Pydantic validation and boundary assertions
│   ├── test_scorer.py        # Exact, normalized, and hallucinated span tests
│   ├── test_triage.py        # Automated triage decision tests
│   ├── test_extractor.py     # End-to-end extraction and parsing tests
│   ├── test_fixtures.py      # Fixture loading and parsing tests
│   └── test_eval_runner.py   # Benchmark metrics and latency tests
└── evals/
    └── run_evals.py          # Terminal CLI benchmark runner using Rich tables
```

---

## License
MIT
