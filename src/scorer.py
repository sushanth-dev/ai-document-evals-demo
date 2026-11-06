"""Calibrated confidence scoring engine based on verbatim text span verification."""

import re
from typing import Any
from src.schemas import FieldScore

CRITICAL_FIELDS = {"liability_cap_usd", "termination_notice_days"}

FIELD_WEIGHTS: dict[str, float] = {
    "vendor_name": 1.5,
    "effective_date": 1.5,
    "liability_cap_usd": 2.0,
    "termination_notice_days": 2.0,
    "contract_value_usd": 1.0,
    "payment_terms_days": 1.0,
    "governing_law": 1.0,
}


def _normalize(text: str) -> str:
    """Normalize whitespace and lowercase for fuzzy comparison."""
    return re.sub(r"\s+", " ", text).strip().lower()


def _clean_numeric(text: str) -> str:
    """Extract digits and decimals from currency/number text."""
    return re.sub(r"[^\d.]", "", text)


def score_field(
    raw_text: str,
    field_name: str,
    value: Any,
    span: str | None,
) -> FieldScore:
    """
    Score the confidence of an extracted field against raw document text.

    Scoring criteria:
    - 1.0: Exact verbatim substring match of both span and value in document.
    - Range 0.90 to 0.95: Normalized equivalence (e.g. formatted numbers, stripped punctuation).
    - Range 0.80 to 0.85: Partial or fuzzy presence in document.
    - 0.0: Hallucinated span, span not present in document, or missing field.
    """
    if value is None:
        return FieldScore(
            value=None,
            verbatim_span=None,
            confidence=0.0,
            flags=["FIELD_MISSING"],
        )

    if not span or not span.strip():
        # Value claimed but no span provided
        val_str = str(value)
        if val_str in raw_text or _normalize(val_str) in _normalize(raw_text):
            return FieldScore(
                value=value,
                verbatim_span=None,
                confidence=0.75,
                flags=["NO_SPAN_GIVEN_VALUE_PRESENT"],
            )
        return FieldScore(
            value=value,
            verbatim_span=None,
            confidence=0.0,
            flags=["NO_SPAN_GIVEN_NOT_FOUND"],
        )

    norm_raw = _normalize(raw_text)
    norm_span = _normalize(span)

    # 1. Exact verbatim span existence check in document
    span_in_raw = (span in raw_text) or (norm_span in norm_raw)

    if not span_in_raw:
        return FieldScore(
            value=value,
            verbatim_span=span,
            confidence=0.0,
            flags=["SPAN_NOT_FOUND"],
        )

    # 2. Verify value matches the verified span
    flags: list[str] = []

    # Exact string inclusion
    val_str = str(value)
    if val_str in span or _normalize(val_str) in norm_span:
        flags.append("EXACT_SPAN_MATCH")
        confidence = 1.0
    elif isinstance(value, (int, float)):
        # Numeric normalization check (e.g. 150000.0 vs "$150,000")
        clean_span_num = _clean_numeric(span)
        clean_val_num = _clean_numeric(str(value))
        if clean_span_num == clean_val_num or (clean_span_num and clean_val_num.startswith(clean_span_num)):
            flags.append("FORMAT_NORMALIZED")
            confidence = 0.95
        else:
            flags.append("NUMERIC_SPAN_MISMATCH")
            confidence = 0.50
    else:
        flags.append("PARTIAL_SPAN_ALIGNMENT")
        confidence = 0.85

    return FieldScore(
        value=value,
        verbatim_span=span,
        confidence=confidence,
        flags=flags,
    )


def compute_overall_confidence(field_scores: dict[str, FieldScore]) -> float:
    """Compute weighted composite confidence across all extracted fields."""
    if not field_scores:
        return 0.0

    total_weight = 0.0
    weighted_score = 0.0

    for name, score in field_scores.items():
        weight = FIELD_WEIGHTS.get(name, 1.0)
        total_weight += weight
        weighted_score += score.confidence * weight

    if total_weight == 0.0:
        return 0.0

    return round(weighted_score / total_weight, 4)
