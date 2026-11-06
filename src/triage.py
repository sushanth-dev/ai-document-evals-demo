"""Automated human-in-the-loop triage gate based on confidence calibration."""

from src.schemas import FieldScore, TriageStatus
from src.scorer import CRITICAL_FIELDS

CONFIDENCE_THRESHOLD: float = 0.85
CRITICAL_FIELD_THRESHOLD: float = 0.80


def evaluate_triage(
    field_scores: dict[str, FieldScore],
    overall_confidence: float,
) -> tuple[TriageStatus, list[str]]:
    """
    Evaluate whether an extracted document can be auto-approved or routed to human review.

    Rules:
    1. Overall confidence must meet or exceed CONFIDENCE_THRESHOLD (0.85).
    2. Every critical field must meet or exceed CRITICAL_FIELD_THRESHOLD (0.80).
    3. Severe warning flags (SPAN_NOT_FOUND, NUMERIC_SPAN_MISMATCH) trigger human review.
    """
    reasons: list[str] = []

    # 1. Overall confidence check
    if overall_confidence < CONFIDENCE_THRESHOLD:
        reasons.append(
            f"Overall confidence {overall_confidence:.3f} below approval threshold {CONFIDENCE_THRESHOLD:.2f}"
        )

    # 2. Critical field checks
    for crit_field in CRITICAL_FIELDS:
        score = field_scores.get(crit_field)
        if score is None or score.confidence < CRITICAL_FIELD_THRESHOLD:
            conf_val = score.confidence if score else 0.0
            reasons.append(
                f"Critical field '{crit_field}' confidence {conf_val:.2f} below minimum {CRITICAL_FIELD_THRESHOLD:.2f}"
            )

    # 3. Quality flag inspection across all fields
    for field_name, score in field_scores.items():
        if "SPAN_NOT_FOUND" in score.flags:
            reasons.append(
                f"Field '{field_name}' ({score.value}) has unconfirmed span; potential hallucination"
            )
        elif "NUMERIC_SPAN_MISMATCH" in score.flags:
            reasons.append(
                f"Field '{field_name}' numeric value does not align with document span '{score.verbatim_span}'"
            )

    if reasons:
        return TriageStatus.NEEDS_HUMAN_REVIEW, reasons

    return TriageStatus.AUTO_APPROVED, []
