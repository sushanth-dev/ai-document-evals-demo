import pytest
from src.schemas import FieldScore
from src.scorer import (
    score_field,
    compute_overall_confidence,
    CRITICAL_FIELDS,
)


DOCUMENT_TEXT = """
MASTER SERVICES AGREEMENT
This Master Services Agreement is entered into on October 12, 2026, by and between
Apex Systems LLC ("Vendor") and Client Corp ("Customer").

1. Fees and Payment.
Total contract compensation shall be $150,000. Customer shall pay all undisputed
invoices within thirty (30) days of receipt (Net 30).

2. Limitation of Liability.
IN NO EVENT SHALL EITHER PARTY'S AGGREGATE LIABILITY EXCEED $500,000.

3. Termination.
Either party may terminate this Agreement upon sixty (60) days prior written notice.

4. Governing Law.
This Agreement shall be governed by and construed in accordance with the laws of Delaware.
"""


def test_score_field_exact_match():
    score = score_field(
        raw_text=DOCUMENT_TEXT,
        field_name="vendor_name",
        value="Apex Systems LLC",
        span="Apex Systems LLC",
    )
    assert score.confidence == 1.0
    assert "EXACT_SPAN_MATCH" in score.flags
    assert score.value == "Apex Systems LLC"


def test_score_field_normalized_number():
    score = score_field(
        raw_text=DOCUMENT_TEXT,
        field_name="contract_value_usd",
        value=150000.0,
        span="$150,000",
    )
    assert score.confidence >= 0.90
    assert "FORMAT_NORMALIZED" in score.flags or "EXACT_SPAN_MATCH" in score.flags


def test_score_field_hallucinated_span():
    score = score_field(
        raw_text=DOCUMENT_TEXT,
        field_name="vendor_name",
        value="Fake Vendor Inc.",
        span="Fake Vendor Inc.",
    )
    assert score.confidence == 0.0
    assert "SPAN_NOT_FOUND" in score.flags


def test_score_field_none_value():
    score = score_field(
        raw_text=DOCUMENT_TEXT,
        field_name="liability_cap_usd",
        value=None,
        span=None,
    )
    assert score.confidence == 0.0
    assert "FIELD_MISSING" in score.flags


def test_compute_overall_confidence_weighted():
    scores = {
        "vendor_name": FieldScore(value="Apex", verbatim_span="Apex", confidence=1.0, flags=[]),
        "effective_date": FieldScore(value="2026-10-12", verbatim_span="October 12, 2026", confidence=0.95, flags=[]),
        "contract_value_usd": FieldScore(value=150000.0, verbatim_span="$150,000", confidence=0.95, flags=[]),
        "payment_terms_days": FieldScore(value=30, verbatim_span="Net 30", confidence=0.95, flags=[]),
        "liability_cap_usd": FieldScore(value=500000.0, verbatim_span="$500,000", confidence=1.0, flags=[]),
        "governing_law": FieldScore(value="Delaware", verbatim_span="Delaware", confidence=1.0, flags=[]),
        "termination_notice_days": FieldScore(value=60, verbatim_span="60 days", confidence=0.95, flags=[]),
    }
    overall = compute_overall_confidence(scores)
    assert 0.90 <= overall <= 1.0
