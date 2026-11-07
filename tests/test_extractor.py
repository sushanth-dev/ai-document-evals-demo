import pytest
from src.schemas import TriageStatus
from src.extractor import extract_and_score, extract_text_from_file


SAMPLE_MSA = """
MASTER SERVICES AGREEMENT
This Master Services Agreement is entered into on October 15, 2026, by and between
CloudScale Technologies Inc. ("Vendor") and Enterprise Corp ("Customer").

1. Term and Scope.
Vendor shall provide specialized cloud infrastructure integration services.

2. Contract Fees and Payment.
Customer agrees to pay Vendor a total contract sum of $85,000 USD.
Invoices are payable within 30 days of receipt (Net 30).

3. Liability Cap.
EACH PARTY'S MAXIMUM AGGREGATE LIABILITY UNDER THIS AGREEMENT IS LIMITED TO $250,000 USD.

4. Termination.
Either party may terminate this agreement without cause upon forty-five (45) days prior written notice.

5. Governing Law.
This Agreement is governed by the laws of the State of California.
"""

SAMPLE_DEFECTIVE = """
VENDOR SERVICE ORDER
Vendor: Ghost Services LLC.
Effective Date: 2026-11-01.
Cost: $10,000.
(Notice: No liability cap or termination notice period specified in this order).
"""


def test_extract_and_score_clean_contract():
    result = extract_and_score(SAMPLE_MSA)
    assert result.triage_status == TriageStatus.AUTO_APPROVED
    assert result.overall_confidence >= 0.85
    assert result.fields["vendor_name"].value == "CloudScale Technologies Inc."
    assert result.fields["contract_value_usd"].value == 85000.0
    assert result.fields["payment_terms_days"].value == 30
    assert result.fields["liability_cap_usd"].value == 250000.0
    assert result.fields["governing_law"].value == "California"
    assert result.fields["termination_notice_days"].value == 45


def test_extract_and_score_defective_triggers_triage():
    result = extract_and_score(SAMPLE_DEFECTIVE)
    assert result.triage_status == TriageStatus.NEEDS_HUMAN_REVIEW
    assert result.fields["termination_notice_days"].confidence == 0.0
    assert result.fields["liability_cap_usd"].confidence == 0.0
    assert len(result.triage_reasons) > 0


def test_extract_text_from_file_missing():
    with pytest.raises(FileNotFoundError):
        extract_text_from_file("non_existent_file.txt")


def test_extract_text_from_file_invalid_pdf_magic(tmp_path):
    fake_pdf = tmp_path / "corrupt_contract.pdf"
    fake_pdf.write_bytes(b"NOT_A_REAL_PDF_HEADER")
    with pytest.raises(ValueError, match="Invalid PDF header signature"):
        extract_text_from_file(str(fake_pdf))
