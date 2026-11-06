# B2B Contract Extraction with Calibrated Confidence Scoring and Regression Evals

**Status:** Approved  
**Date:** 2026-11-06  
**Repository:** `~/Development/projects/ai-document-evals-demo`  

## 1. Intent and Context
Seed-stage AI startup founders and enterprise engineering teams constantly deal with LLMs hallucinating on complex legal/financial PDFs and silently degrading when prompts or models change. This repository serves as a production-grade proof of engineering capability:
- Structured schema extraction for commercial contracts (MSAs, NDAs, Service Agreements).
- Calibrated, field-level confidence scoring (0.0 to 1.0) based on verbatim character span matching in raw text.
- Automated human-in-the-loop triage thresholding (`< 0.85` overall or `< 0.80` critical fields routes to human review).
- Deterministic 10-fixture regression test suite with accuracy and triage metrics reported via CLI.

## 2. Architecture and Directory Structure
```
ai-document-evals-demo/
├── pyproject.toml            # Dependencies: pydantic>=2.0, pdfplumber, pytest, rich
├── README.md                 # 60-second architecture breakdown and benchmark tables
├── src/
│   ├── __init__.py
│   ├── schemas.py            # Pydantic contract extraction and confidence schemas
│   ├── extractor.py          # Document text extraction and structured parsing pipeline
│   ├── scorer.py             # Verbatim span-matching confidence scoring engine
│   └── triage.py             # Human-in-the-loop threshold gate (auto-approve vs triage queue)
├── fixtures/
│   ├── contracts/            # 10 synthetic commercial contracts (.txt and .pdf)
│   │   ├── 01_clean_standard_msa.txt
│   │   ├── 02_missing_termination.txt
│   │   ├── 03_ambiguous_payment_terms.txt
│   │   ├── 04_contradictory_dates.txt
│   │   ├── 05_ocr_typo_vendor.txt
│   │   ├── 06_extreme_liability_cap.txt
│   │   ├── 07_multi_page_spans.txt
│   │   ├── 08_missing_governing_law.txt
│   │   ├── 09_foreign_currency_msa.txt
│   │   └── 10_zero_dollar_nda.txt
│   └── ground_truth.json     # Expected field values and expected triage status per fixture
├── tests/
│   ├── test_schemas.py
│   ├── test_scorer.py
│   ├── test_triage.py
│   └── test_extractor.py
└── evals/
    └── run_evals.py          # Benchmark runner printing terminal table of accuracy and triage metrics
```

## 3. Interfaces and Schemas
### `ContractExtraction` (Pydantic Model)
- `vendor_name: str`
- `effective_date: str` (YYYY-MM-DD or raw string)
- `contract_value_usd: float | None`
- `payment_terms_days: int | None`
- `liability_cap_usd: float | None`
- `governing_law: str | None`
- `termination_notice_days: int | None`

### `FieldScore` (Pydantic Model)
- `value: Any`
- `verbatim_span: str | None`
- `confidence: float` (0.0 to 1.0)
- `flags: list[str]`

### `ScoredExtraction` (Pydantic Model)
- `fields: dict[str, FieldScore]`
- `overall_confidence: float`
- `triage_status: Literal["AUTO_APPROVED", "NEEDS_HUMAN_REVIEW"]`
- `triage_reasons: list[str]`

## 4. Confidence Scoring Rules
1. Exact verbatim substring match in raw document text: `confidence = 1.0`.
2. Fuzzy / normalized match (e.g. `$50,000` vs `50000`, or `October 12, 2026` vs `2026-10-12`): `confidence = 0.85 to 0.95`.
3. Absent, conflicting, or hallucinated span: `confidence = 0.0`.
4. Missing required field: penalty applied to `overall_confidence`.

## 5. Triage Gate Logic
- If `overall_confidence < 0.85`: `triage_status = "NEEDS_HUMAN_REVIEW"`.
- If critical fields (`liability_cap_usd`, `termination_notice_days`) have `confidence < 0.80`: `triage_status = "NEEDS_HUMAN_REVIEW"`.
- Otherwise: `triage_status = "AUTO_APPROVED"`.

## 6. Constraints and Non-Goals
- Zero proprietary TC AI code or document data. 100% synthetic commercial contracts.
- Deterministic offline execution: includes a deterministic mock/rules extractor alongside live LLM client so `pytest` and `run_evals.py` execute instantly without requiring paid API keys.
- Fast runtime: complete evaluation suite executes in under 2 seconds.
