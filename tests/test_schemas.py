from datetime import date
import pytest
from pydantic import ValidationError

from src.schemas import (
    ContractExtraction,
    FieldScore,
    ScoredExtraction,
    TriageStatus,
)


def test_contract_extraction_valid():
    contract = ContractExtraction(
        vendor_name="Acme Cloud Inc.",
        effective_date="2026-10-01",
        contract_value_usd=120000.0,
        payment_terms_days=30,
        liability_cap_usd=250000.0,
        governing_law="Delaware",
        termination_notice_days=60,
    )
    assert contract.vendor_name == "Acme Cloud Inc."
    assert contract.effective_date == "2026-10-01"
    assert contract.contract_value_usd == 120000.0
    assert contract.payment_terms_days == 30
    assert contract.liability_cap_usd == 250000.0
    assert contract.governing_law == "Delaware"
    assert contract.termination_notice_days == 60


def test_contract_extraction_optional_fields_none():
    contract = ContractExtraction(
        vendor_name="Zero Dollar Mutual NDA",
        effective_date="2026-11-01",
        contract_value_usd=0.0,
        payment_terms_days=None,
        liability_cap_usd=None,
        governing_law=None,
        termination_notice_days=None,
    )
    assert contract.contract_value_usd == 0.0
    assert contract.payment_terms_days is None
    assert contract.liability_cap_usd is None


def test_field_score_confidence_bounds():
    with pytest.raises(ValidationError):
        FieldScore(
            value="Acme",
            verbatim_span="Acme",
            confidence=1.5,  # Exceeds max 1.0
            flags=[],
        )

    with pytest.raises(ValidationError):
        FieldScore(
            value="Acme",
            verbatim_span="Acme",
            confidence=-0.1,  # Below min 0.0
            flags=[],
        )


def test_scored_extraction_structure():
    field_scores = {
        "vendor_name": FieldScore(
            value="Acme Corp",
            verbatim_span="Acme Corp",
            confidence=1.0,
            flags=[],
        ),
        "contract_value_usd": FieldScore(
            value=50000.0,
            verbatim_span="$50,000",
            confidence=0.95,
            flags=["FORMAT_NORMALIZED"],
        ),
    }
    scored = ScoredExtraction(
        fields=field_scores,
        overall_confidence=0.975,
        triage_status=TriageStatus.AUTO_APPROVED,
        triage_reasons=[],
    )
    assert scored.overall_confidence == 0.975
    assert scored.triage_status == TriageStatus.AUTO_APPROVED
    assert len(scored.triage_reasons) == 0
