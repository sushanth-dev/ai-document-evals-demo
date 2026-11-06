"""Pydantic V2 schemas for contract extraction, field-level confidence scoring, and triage."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class TriageStatus(str, Enum):
    """Triage gate disposition."""
    AUTO_APPROVED = "AUTO_APPROVED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class ContractExtraction(BaseModel):
    """Raw structured output extracted from commercial contract."""
    vendor_name: str = Field(description="Name of the external vendor or counterparty")
    effective_date: str = Field(description="Date the agreement enters into force (YYYY-MM-DD or raw)")
    contract_value_usd: float | None = Field(default=None, description="Total contract value in USD if specified")
    payment_terms_days: int | None = Field(default=None, description="Net payment term in days (e.g. 30 for Net 30)")
    liability_cap_usd: float | None = Field(default=None, description="Maximum liability limitation in USD")
    governing_law: str | None = Field(default=None, description="Jurisdiction or state governing agreement")
    termination_notice_days: int | None = Field(default=None, description="Required written notice period for termination in days")


class FieldScore(BaseModel):
    """Calibrated confidence score and verification evidence for an extracted field."""
    value: Any = Field(description="Extracted value")
    verbatim_span: str | None = Field(default=None, description="Exact or normalized snippet from source text")
    confidence: float = Field(ge=0.0, le=1.0, description="Calibrated confidence score between 0.0 and 1.0")
    flags: list[str] = Field(default_factory=list, description="Quality or risk warning flags")


class ScoredExtraction(BaseModel):
    """Full extraction envelope with field-level confidence and automated triage disposition."""
    fields: dict[str, FieldScore] = Field(description="Field-by-field scores and evidence")
    overall_confidence: float = Field(ge=0.0, le=1.0, description="Weighted composite confidence score")
    triage_status: TriageStatus = Field(description="Automated triage decision")
    triage_reasons: list[str] = Field(default_factory=list, description="Explanations if routed to review")
