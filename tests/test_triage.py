import pytest
from src.schemas import FieldScore, TriageStatus
from src.triage import (
    evaluate_triage,
    CONFIDENCE_THRESHOLD,
    CRITICAL_FIELD_THRESHOLD,
)


def test_triage_auto_approved():
    field_scores = {
        "vendor_name": FieldScore(value="Acme Inc", verbatim_span="Acme Inc", confidence=1.0, flags=["EXACT_SPAN_MATCH"]),
        "effective_date": FieldScore(value="2026-10-01", verbatim_span="2026-10-01", confidence=1.0, flags=["EXACT_SPAN_MATCH"]),
        "liability_cap_usd": FieldScore(value=100000.0, verbatim_span="$100,000", confidence=0.95, flags=["FORMAT_NORMALIZED"]),
        "termination_notice_days": FieldScore(value=30, verbatim_span="30 days", confidence=0.95, flags=["FORMAT_NORMALIZED"]),
    }
    status, reasons = evaluate_triage(field_scores, overall_confidence=0.975)
    assert status == TriageStatus.AUTO_APPROVED
    assert len(reasons) == 0


def test_triage_low_overall_confidence():
    field_scores = {
        "vendor_name": FieldScore(value="Acme Inc", verbatim_span="Acme Inc", confidence=0.80, flags=["PARTIAL_SPAN_ALIGNMENT"]),
        "effective_date": FieldScore(value="2026-10-01", verbatim_span="2026-10-01", confidence=0.80, flags=["PARTIAL_SPAN_ALIGNMENT"]),
    }
    status, reasons = evaluate_triage(field_scores, overall_confidence=0.80)
    assert status == TriageStatus.NEEDS_HUMAN_REVIEW
    assert any("overall confidence" in r.lower() for r in reasons)


def test_triage_critical_field_missing():
    field_scores = {
        "vendor_name": FieldScore(value="Acme Inc", verbatim_span="Acme Inc", confidence=1.0, flags=["EXACT_SPAN_MATCH"]),
        "liability_cap_usd": FieldScore(value=None, verbatim_span=None, confidence=0.0, flags=["FIELD_MISSING"]),
        "termination_notice_days": FieldScore(value=30, verbatim_span="30 days", confidence=1.0, flags=["EXACT_SPAN_MATCH"]),
    }
    # Even if overall confidence is >= 0.85, critical field liability_cap_usd fails
    status, reasons = evaluate_triage(field_scores, overall_confidence=0.88)
    assert status == TriageStatus.NEEDS_HUMAN_REVIEW
    assert any("liability_cap_usd" in r for r in reasons)


def test_triage_hallucinated_span_flag():
    field_scores = {
        "vendor_name": FieldScore(value="Ghost Corp", verbatim_span="Ghost Corp", confidence=0.0, flags=["SPAN_NOT_FOUND"]),
    }
    status, reasons = evaluate_triage(field_scores, overall_confidence=0.50)
    assert status == TriageStatus.NEEDS_HUMAN_REVIEW
    assert any("SPAN_NOT_FOUND" in r or "Ghost Corp" in r for r in reasons)
